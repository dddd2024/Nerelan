"""Pure per-task routing. Priors are bootstrap estimates, never measured claims.

Three completed attempts in a kind/difficulty bucket establish evidence. A bucket
with >=80% success and <=20% timeouts demonstrates that difficulty; otherwise
its tier is one lower. Exploration uses an injected draw (no hidden randomness).
"""
from __future__ import annotations

from typing import Any, Collection, Mapping, Sequence
import math
from types import SimpleNamespace

from . import model_review_transport
from .run_store import TaskStoreError

from .quota_guard import CONFIRMED_EXHAUSTION_REASONS
from .routing_inputs import pool_key_for_upstream, requirements, reset_decision, routing_group_id, upstream_namespace
from .resource_allowances import urgency
import re
import time

KINDS = frozenset({"code", "analysis", "writing", "research_design", "review"})
LEGACY_DIFFICULTY = {"simple": 2, "coder": 3, "complex": 4, "planner": 4, "reviewer": 4}
MIN_SAMPLES = 3
RELIABILITY_PRIOR_WEIGHT = 4.0


def measured_reliability_penalty(bucket: Mapping[str, Any]) -> float:
    """Bayesian-shrunk reliability penalty prioritizing recency-weighted outcomes."""
    if not isinstance(bucket, Mapping):
        return 0.0
    ra = bucket.get("recent_attempts")
    ro = bucket.get("recent_ok")
    if type(ra) in (int, float) and math.isfinite(ra) and ra >= 0:
        eff_attempts = float(ra)
        if type(ro) in (int, float) and math.isfinite(ro):
            eff_ok = float(ro)
        else:
            sr = bucket.get("recent_success_rate", bucket.get("success_rate"))
            eff_ok = eff_attempts * float(sr) if type(sr) in (int, float) and math.isfinite(sr) else eff_attempts
    else:
        att = bucket.get("attempts")
        if type(att) is not int or att <= 0:
            return 0.0
        eff_attempts = float(att)
        ok = bucket.get("ok")
        if type(ok) in (int, float) and math.isfinite(ok):
            eff_ok = float(ok)
        else:
            sr = bucket.get("success_rate")
            if type(sr) not in (int, float) or not math.isfinite(sr):
                return 0.0
            eff_ok = eff_attempts * float(sr)
    if eff_attempts < MIN_SAMPLES:
        return 0.0
    eff_ok = max(0.0, min(eff_attempts, eff_ok))
    eff_failed = max(0.0, eff_attempts - eff_ok)
    shrunk_failure = eff_failed / (eff_attempts + RELIABILITY_PRIOR_WEIGHT)
    return round(2.5 * shrunk_failure, 4)


def task_traits(raw: Mapping[str, Any]) -> tuple[int, str]:
    role = raw.get("agent_role") or ""
    if isinstance(role, str):
        role = role.strip()
    if not isinstance(role, str) or (role and role not in LEGACY_DIFFICULTY):
        raise ValueError(f"unsupported_agent_role:{role}" if isinstance(role, str) else "unsupported_agent_role")
    difficulty = raw.get("difficulty", LEGACY_DIFFICULTY.get(role, 3))
    kind = raw.get("kind", "review" if role == "reviewer" else "code")
    if type(difficulty) is not int or not 1 <= difficulty <= 5:
        raise ValueError("invalid_task_difficulty")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError("invalid_task_kind")
    return difficulty, kind


def prior_tier(model: str) -> tuple[int, bool]:
    """Exact-id fallback carries no measured capability claim."""
    return 2, True


def capability(model: str, profile: Mapping[str, Any], kind: str, difficulty: int) -> tuple[int, bool]:
    from .routing_capabilities import tier_evidence
    tier, unproven, _ = tier_evidence(model, profile, kind, difficulty)
    return tier, unproven


# A dot between two digits is a version separator: "glm-5.3" and "glm-5-3" are one model.
_VERSION_DOT = re.compile(r"(?<=\d)\.(?=\d)")
_CLAUDE_ALIASES = frozenset({"sonnet", "opus", "haiku"})
_CLAUDE_ALIAS_RE = re.compile(r"^claude-(sonnet|opus|haiku)(?:-[0-9a-z.-]+)?$")


def _base_identity(model: str) -> str:
    identity = model.strip().lower().rsplit("/", 1)[-1]
    while identity.endswith((":free", "-free")):
        identity = identity.removesuffix(":free").removesuffix("-free")
    return _VERSION_DOT.sub("-", identity)


def same_model_identity(left: str, right: str, groups: Mapping[str, Any] | None = None) -> bool:
    """Whether ``left`` and ``right`` name the same model identity, or bare/pinned Claude aliases."""
    a, b = model_identity(left, groups), model_identity(right, groups)
    if not a or not b:
        return False
    if a == b:
        return True
    for bare, concrete in ((a, b), (b, a)):
        if bare in _CLAUDE_ALIASES:
            match = _CLAUDE_ALIAS_RE.fullmatch(concrete)
            if match and match.group(1) == bare:
                return True
    return False


def model_identity(model: str, groups: Mapping[str, Any] | None = None) -> str:
    """Provider namespaces and free gateway suffixes do not make a new author.

    A Magpie routing group (``group/<id>``, Owner decision 2026-11-17) is the model
    its members serve, as the Owner declares it in the overrides ``groups`` section.
    An undeclared ``group/`` id has no identity (""), so it can never be proven
    independent of anything; an undeclared ``auto/<model>`` falls back to ``<model>``.
    """
    group = routing_group_id(model)
    if not group:
        return _base_identity(model)
    entry = (groups or {}).get(group)
    if entry is None:
        entry = next((value for key, value in (groups or {}).items()
                      if isinstance(key, str) and key.strip().lower() == group), None)
    declared = entry.get("identity") if isinstance(entry, Mapping) else None
    if isinstance(declared, str) and declared.strip() and not routing_group_id(declared):
        return _base_identity(declared)
    head, _, rest = group.partition("/")
    return _base_identity(rest) if head == "auto" and not routing_group_id(rest) else ""


def served_model(model: str, groups: Mapping[str, Any] | None = None) -> str:
    """The model id capability lookups use: a declared group's served model, else ``model``.

    Only an Owner-declared ``group/``/``auto/`` id resolves; an undeclared one keeps
    its own id, so its tier stays what it was before.
    """
    group = routing_group_id(model)
    if not group:
        return model
    entry = (groups or {}).get(group)
    if entry is None:
        entry = next((value for key, value in (groups or {}).items()
                      if isinstance(key, str) and key.strip().lower() == group), None)
    declared = entry.get("identity") if isinstance(entry, Mapping) else None
    if isinstance(declared, str) and declared.strip() and not routing_group_id(declared):
        return declared.strip()
    return model


def store_groups(store: Any) -> Mapping[str, Any]:
    """The Owner's declared routing groups the host attached to a task store, or {}."""
    provider = getattr(store, "routing_groups", None)
    try:
        groups = provider() if callable(provider) else {}
    except Exception:  # noqa: BLE001 - unreadable declarations leave every group undeclared
        return {}
    return groups if isinstance(groups, Mapping) else {}


WEEK_SECONDS = 7 * 86400
# Weekly need assumed for a task whose account has no calibrated units-per-percent
# yet: the uncalibrated median in quota_reservation (3 percentage points).
UNKNOWN_WEEKLY_NEED = .03


# With ``require_fresh``, an account with no fresh weekly reading is re-checked this often.
UNKNOWN_PACE_RETRY_SECONDS = 900


def upstream_key(candidate: Mapping[str, Any]) -> str:
    """The upstream account a candidate spends: its account plus a gateway namespace (#1596).

    ``magpie/minimax/m3`` and ``magpie/minimax/m3-fast`` on one gateway account share the
    ``minimax`` upstream; a model id without a namespace is its account alone. A Magpie
    routing group is keyed by its own id (``group:<id>``), never by the shared ``group``.
    """
    namespace = upstream_namespace(candidate.get("model_id"))
    return f"{candidate.get('account_ref') or candidate.get('connection_id') or ''}|{namespace}"


# Liveness preference (#1596), best first: another upstream, the same upstream, a
# binding cooling down after a stall elsewhere, the binding this step just stalled on.
LIVENESS_CLEAN, LIVENESS_SAME_UPSTREAM, LIVENESS_COOLING, LIVENESS_AVOIDED = range(4)


def weekly_pace_hold(candidate: Mapping[str, Any], *, now: float,
                     pace: Mapping[str, Any] | None) -> float | None:
    """When a paced subscription account may take this task again, or None if it may now.

    A weekly allowance spent ahead of the calendar leaves nothing for the rest of
    the week. Use may run ahead of elapsed time by ``slack`` and never past
    ``1 - reserve``. Unknown usage or reset time makes no claim, so the existing
    quota rules alone decide, unless ``require_fresh`` is set: then the account
    is held until a fresh reading shows where it stands. In the last
    ``reserve_release_hours`` before the reset the reserve is released: what is
    still unused then would only expire.
    """
    return weekly_pace_decision(candidate, now=now, pace=pace)[0]


def active_reserve(pace: Mapping[str, Any], *, resets: float, now: float) -> float:
    """The weekly share kept for the Owner now; 0 in the release hours before the reset."""
    release = float(pace.get("reserve_release_hours", 0)) * 3600
    return 0. if 0 < resets - now <= release else float(pace.get("reserve", .10))


def reserve_released(candidate: Mapping[str, Any], *, now: float, pace: Mapping[str, Any] | None) -> bool:
    """Whether this paced account is in its release hours, so nothing of its week is held back."""
    resets = candidate.get("weekly_resets_at")
    return bool(pace and pace.get("enabled", False) and candidate.get("cost_class") == "subscription"
                and (candidate.get("executor_id") in pace.get("executors", ())
                     or candidate.get("paced_provider") in pace.get("providers", ()))
                and type(resets) in (int, float) and math.isfinite(resets)
                and active_reserve({**pace, "reserve": 1}, resets=resets, now=now) == 0)


def weekly_pace_decision(candidate: Mapping[str, Any], *, now: float,
                         pace: Mapping[str, Any] | None) -> tuple[float | None, str]:
    """``weekly_pace_hold`` plus the cause of a hold, so an exclusion can name it.

    Causes: ``no_fresh_gateway_quota`` / ``no_fresh_account_quota`` (``require_fresh``
    with no usable reading; the host may name a narrower input cause such as
    ``no_gateway_account`` or ``gateway_account_ambiguous``), ``weekly_reserve``
    (only the reset frees it) and ``ahead_of_pace`` (free again at ``retry_at``).
    """
    if not pace or not pace.get("enabled", False):
        return None, ""
    paced = (candidate.get("executor_id") in pace.get("executors", ())
             or candidate.get("paced_provider") in pace.get("providers", ()))
    if not paced or candidate.get("cost_class") != "subscription":
        return None, ""
    headroom, resets = candidate.get("weekly_headroom"), candidate.get("weekly_resets_at")
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (headroom, resets)):
        if pace.get("require_fresh") is not True:
            return None, ""
        named = candidate.get("weekly_pace_input")
        cause = (named if isinstance(named, str) and named.startswith(("no_", "gateway_account_", "gateway_quota_"))
                 else "no_fresh_gateway_quota" if candidate.get("paced_provider") else "no_fresh_account_quota")
        return float(now + UNKNOWN_PACE_RETRY_SECONDS), cause
    need = candidate.get("task_weekly_fraction")
    need = need if type(need) in (int, float) and math.isfinite(need) and need >= 0 else UNKNOWN_WEEKLY_NEED
    slack, reserve = float(pace.get("slack", .10)), active_reserve(pace, resets=resets, now=now)
    start = resets - WEEK_SECONDS
    elapsed = min(1., max(0., (now - start) / WEEK_SECONDS))
    demand = (1 - headroom) + need
    if demand <= min(1 - reserve, elapsed + slack):
        return None, ""
    if demand > 1 - reserve:
        # The reset frees it, or the release hours if the task fits the whole allowance.
        release = float(pace.get("reserve_release_hours", 0)) * 3600
        return float(max(now, resets - release) if reserve and demand <= 1 else resets), "weekly_reserve"
    return float(max(now, min(resets, start + WEEK_SECONDS * (demand - slack)))), "ahead_of_pace"


def weekly_pace_penalty(candidate: Mapping[str, Any], *, now: float,
                        pace: Mapping[str, Any] | None) -> float:
    """Soft scoring penalty when a paced account is ahead of elapsed week without hitting reserve."""
    _, cause = weekly_pace_decision(candidate, now=now, pace=pace)
    if cause != "ahead_of_pace":
        return 0.0
    headroom = candidate.get("weekly_headroom")
    resets = candidate.get("weekly_resets_at")
    need = candidate.get("task_weekly_fraction")
    need = need if type(need) in (int, float) and math.isfinite(need) and need >= 0 else UNKNOWN_WEEKLY_NEED
    slack = float((pace or {}).get("slack", .10))
    elapsed = min(1., max(0., (now - (resets - WEEK_SECONDS)) / WEEK_SECONDS))
    demand = (1 - headroom) + need
    overshoot = max(0., min(1., demand - (elapsed + slack)))
    return round(min(1.5, overshoot * 3.0), 4)


# Most mirror reset events confirm a reset that already landed ("the reset has been
# processed"), posted minutes to hours after it. A week that began this long before
# the announcement is that reset, not an older one (#1400 review at 241f19e9).
RENEWAL_MARGIN_SECONDS = 24 * 3600


def _window_renewed_since(candidate: Mapping[str, Any], announced_at: Any) -> bool:
    """Whether this account's weekly window began after, or shortly before, the announcement.

    Then the reset has already happened for this account: draining further would
    spend the new week, so pacing applies again whatever the announcement said.
    "Shortly before" covers confirmations posted after the reset landed. A natural
    renewal in that margin only skips a drain on an almost untouched week.
    """
    resets = candidate.get("weekly_resets_at")
    if not isinstance(announced_at, str) or type(resets) not in (int, float) or not math.isfinite(resets):
        return False
    try:
        from datetime import datetime
        announced = datetime.fromisoformat(announced_at.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return False
    return resets - WEEK_SECONDS > announced - RENEWAL_MARGIN_SECONDS


class ModelSelectionError(ValueError):
    def __init__(self, reason: str, *, excluded: list[dict[str, Any]], refusals: Sequence[str] = (), pin: str = ""):
        super().__init__(reason)
        # The pinned binding's own refusal leads the list so the 10-row cap cannot hide it (#1521).
        shown = [row for row in excluded if pin and row.get("binding_id") == pin] + [
            row for row in excluded if not pin or row.get("binding_id") != pin]
        self.decision = {"reason": reason, "excluded_candidates": shown[:10], "refusals": list(refusals)}
        summary: dict[str, int] = {}
        for row in excluded:
            summary[str(row.get("filter"))] = summary.get(str(row.get("filter")), 0) + 1
        if summary:
            self.decision["excluded_summary"] = summary
        if pin:
            pin_row = next((row for row in excluded if row.get("binding_id") == pin), None)
            self.decision["pin"] = pin
            self.decision["pin_filter"] = pin_row.get("filter") if pin_row else "pin_not_candidate"
        resources = [row for row in excluded if row.get("filter") in {
            "account_quarantined", "quota_exhausted", "weekly_pace",
            "pool_concurrency_limit", "pool_rpm_limit", "pool_tpm_limit"}
                     and (not pin or row.get("binding_id") == pin)]
        if resources:
            due = [row["retry_at"] for row in resources if type(row.get("retry_at")) in (int, float)
                   and math.isfinite(row["retry_at"])]
            self.decision.update(temporary_resource_blocked=True, retry_at=min(due) if due else None)


def select_model(candidates: Sequence[Mapping[str, Any]], *, difficulty: int, kind: str,
                 profiles: Mapping[str, Any] | None = None, role: str = "",
                 author_model: str = "", author_models: Sequence[str] = (), author_executors: Sequence[str] = (), pin: str = "", failed_model: str = "",
                 failed_tier: int = 0, exploration_draw: float = 1.0,
                 exploration_budget: float = .1, context_need: int = 0,
                 needs: Sequence[str] = (), overrides: Mapping[str, Any] | None = None,
                 reset_signal: Mapping[str, Any] | None = None, now: float | None = None,
                 reset_buffer: float = .03, refused_models: Sequence[str] = (),
                 refusal_tier: int = 0, capability_table: Mapping[str, Any] | None = None,
                 allow_paid: bool = False, quota_buffer: float = .10,
                 account_feedback: Mapping[str, Any] | None = None,
                 weekly_pace: Mapping[str, Any] | None = None,
                 avoid_bindings: Sequence[str] = (), avoid_upstreams: Sequence[str] = (),
                 stall_tier: int = 0, groups: Mapping[str, Any] | None = None,
                 window_pool: Collection[str] | None = None,
                 in_flight_by_upstream: Mapping[str, int] | None = None,
                 pool_limits: Mapping[str, Mapping[str, Any]] | None = None,
                 rpm_by_pool: Mapping[str, int] | None = None,
                 tpm_by_pool: Mapping[str, int] | None = None) -> dict[str, Any]:
    """Pick from public binding metadata and precomputed quota observations.

    Scores prefer known availability/readiness, then quota, cost, success and speed.
    Subscription cost ranges from 1 to 2 as headroom falls; paid API cost is 3.
    Pins override price/tier, while readiness, quota and review fitness still apply.
    The injected uniform draw gives easy tasks a default 10% exploration rate.
    Liveness (#1596) is a preference, not a filter: a binding in a stall cool-down, or
    one this step stalled on (``avoid_bindings``), is chosen only when no qualifying
    alternative exists, and then the decision says so. ``stall_tier`` is the stalled
    attempt's tier: a stall retry never goes below it.
    ``groups`` are the Owner's declared Magpie routing groups: every author, reviewer,
    refusal and escalation comparison uses the model a group serves, and a declared
    group's capability tier and priors are its served model's; the measured
    profile stays keyed by binding.
    ``window_pool``, when given, is the set of bindings the Goal's Owner window lets
    it run on (#1667); any other candidate is excluded as ``outside_window_pool``.
    """
    def identity(model: str) -> str:
        return model_identity(model, groups)

    if type(quota_buffer) not in (int, float) or not 0 <= quota_buffer <= 1:
        raise ValueError("invalid_quota_buffer")
    task_traits({"difficulty": difficulty, "kind": kind})
    context_need, needs = requirements({"context_need": context_need, "needs": needs})
    content = "security_simulation" if "security_simulation" in needs else kind
    now = time.time() if now is None else now
    ranked, excluded, reset_observations = [], [], []
    # A binding this step stalled on also marks its upstream: siblings there likely hang too.
    avoid_upstreams = {*avoid_upstreams, *(upstream_key(c) for c in candidates if c["binding_id"] in avoid_bindings)}
    artifact_review = (kind == "review" or role == "reviewer") and bool(author_models)
    if artifact_review and any(not isinstance(m, str) or not identity(m) for m in author_models):
        raise ModelSelectionError("review_not_independent", excluded=[])
    authors = {identity(m) for m in (*author_models, author_model) if m}
    reviewing = kind == "review" or role == "reviewer"
    if reviewing and "" in authors:
        # An undeclared routing group authored: nothing can be proven independent of it.
        raise ModelSelectionError("review_not_independent", excluded=[])
    codex_authored = artifact_review and ("codex" in author_executors or any(
        c.get("executor_id") == "codex" and isinstance(c.get("model_id"), str)
        and identity(c["model_id"]) in authors for c in candidates))
    excluded_tiers: dict[str, int] = {}
    for candidate in candidates:
        if candidate.get("dispatch_block"):
            # A paid subscription behind a gateway (#1743): above every pin and preference.
            excluded.append({"binding_id": candidate["binding_id"], "model_id": candidate.get("model_id"),
                             "filter": "paid_subscription_gateway", "cause": candidate["dispatch_block"]})
            continue
        if window_pool is not None and candidate["binding_id"] not in window_pool:
            excluded.append({"binding_id": candidate["binding_id"], "model_id": candidate.get("model_id"),
                             "filter": "outside_window_pool"})
            continue
        if artifact_review and (not isinstance(candidate.get("model_id"), str)
                                or not identity(candidate["model_id"])):
            excluded.append({"binding_id": candidate["binding_id"], "model_id": candidate.get("model_id"),
                             "filter": "review_identity_unknown"})
            continue
        profile = (profiles or {}).get(candidate["binding_id"], {})
        override = (overrides or {}).get(candidate["binding_id"], {})
        # Public metadata < measured evidence < explicit Owner values.
        # A declared routing group is judged as the model its members serve.
        capability_model = served_model(candidate["model_id"], groups)
        metadata = {**prior_characteristics(capability_model),
                    **{k: v for k, v in (candidate.get("metadata") or {}).items() if v is not None},
                    **{k: v for k, v in profile.items() if v is not None}, **override}
        window = metadata["context_window"]
        if type(window) not in (int, float) or isinstance(window, float) and not math.isfinite(window) or window <= 0:
            window = prior_characteristics(capability_model)["context_window"]
        refusal = metadata.get("refusal_rates", {}).get(content)
        refusal_risk = .25 if refusal is None else max(0., min(1., refusal))
        quota = candidate.get("quota") or {}
        from .routing_capabilities import tier_detail
        detail = tier_detail(capability_model, profile, kind, difficulty, capability_table, override)
        tier, unproven, tier_source = detail["tier"], detail["unproven"], detail["source"]
        # The decision record cites benchmark sources and confidence (issue 1264).
        tier_basis = {key: detail[key] for key in ("benchmark", "prior_gap") if key in detail}
        reset = reset_decision(reset_signal, now=now, buffer=reset_buffer,
                               weekly_remaining=candidate.get("weekly_headroom"), short_resets_at=candidate.get("short_resets_at"))
        if reset["drain"] and _window_renewed_since(candidate, reset.get("announced_at")):
            # This account's week began after the announcement: its reset has
            # happened. Every drain effect ends here (pacing, the reserve bypass,
            # the quota penalty and the cost discount), so the new week is kept.
            reset = {**reset, "drain": False, "drain_target": None, "drain_ended": "window_renewed"}
        if candidate["executor_id"] == "codex" and candidate.get("cost_class") == "subscription":
            reset_observations.append({"binding_id": candidate["binding_id"], **reset})
        # A validated announced Codex reset already drains to reset_buffer (Owner rule,
        # #1248/#1281): allowance that the reset will void is not saved for later.
        pace_hold, pace_cause = (None, "") if candidate["executor_id"] == "codex" and reset["drain"] else (
            weekly_pace_decision(candidate, now=now, pace=weekly_pace))
        soft_pace = bool((weekly_pace or {}).get("soft_pacing", True))
        pace_penalty = 0.0
        if pace_cause == "ahead_of_pace" and soft_pace:
            pace_penalty = weekly_pace_penalty(candidate, now=now, pace=weekly_pace)
            pace_hold = None
        reason = ""
        review_transport = ""
        if artifact_review:
            if candidate["executor_id"] == "codex":
                review_transport = "codex"
            elif candidate["executor_id"] == "claude_code" and not (
                    candidate.get("review_connection") or {}).get("relay_required"):
                review_transport = "claude_code"
            else:
                try:
                    connection = candidate.get("review_connection") or {}
                    model_review_transport.validate_connection(SimpleNamespace(executor_id=candidate["executor_id"],
                        auth_method=connection.get("auth_method"),
                        relay_required=connection.get("relay_required"),
                        native_endpoint=connection.get("native_endpoint"),
                        base_url=connection.get("base_url")), candidate.get("review_lease_provider"))
                    review_transport = "toolless"
                except TaskStoreError:
                    reason = "review_transport_unsupported"
        endpoints = metadata.get("native_endpoints", ())
        responses_only = endpoints and all(endpoint in {"/responses", "/v1/responses", "responses"} for endpoint in endpoints)
        if candidate.get("executor_available") is False:
            reason = "executor_unavailable"
        elif reason:
            pass
        elif (not candidate.get("enabled", True) or not candidate.get("runnable", True)
                or role == "planner" and candidate["executor_id"] not in {"codex", "claude_code", "opencode"}
                or responses_only and candidate["executor_id"] == "claude_code"):
            reason = "executor_fitness"
        elif (override.get("exclude") or difficulty > override.get("max_difficulty", 5)
              or content in override.get("denied_content", ())
              or ("allowed_content" in override and content not in override["allowed_content"])):
            reason = "owner_override"
        elif window * .7 < context_need:
            reason = "context_window"
        elif ("vision" in needs and "image" not in metadata.get("input_modalities", ())
              or "tool_use" in needs and metadata.get("tool_use") is False
              or "chinese" in needs and metadata.get("chinese") is False):
            reason = "modality"
        elif candidate.get("availability", {}).get("reason") == "no_credits":
            # A billing hold is not a quota window: it lasts until credits are
            # bought, so it is reported as itself rather than as the generic
            # quota exhaustion that the same failure also triggers (#1525).
            reason = "availability:no_credits"
        elif quota.get("reason") == "account_quarantined":
            reason = "account_quarantined"
        elif quota.get("reason") in CONFIRMED_EXHAUSTION_REASONS | {"predicted_insufficient", "quota_capacity"}:
            reason = "quota_exhausted"
        elif (candidate.get("cost_class") == "subscription"
              # An announced Codex reset drains to reset_buffer instead (Owner rule, #1248/#1281).
              and not (candidate["executor_id"] == "codex" and reset["drain"]) and any(
                candidate.get(need) is not None and candidate.get(headroom) is not None
                and candidate[need] > candidate[headroom] - (
                    0 if headroom == "weekly_headroom" and reserve_released(candidate, now=now, pace=weekly_pace)
                    else quota_buffer)
                for need, headroom in (("task_weekly_fraction", "weekly_headroom"),
                                       ("task_short_fraction", "short_headroom")))):
            reason = "quota_capacity"
        elif pace_hold is not None:
            reason = "weekly_pace"
        elif (candidate["executor_id"] == "codex" and candidate.get("cost_class") == "subscription"
              and reset["drain_target"] is not None and candidate.get("weekly_headroom") is not None
              and candidate["weekly_headroom"] <= reset_buffer):
            reason = "reset_buffer"
        elif (candidate["executor_id"] == "codex" and reset["drain"]
              and candidate.get("task_weekly_fraction") is not None
              and candidate["weekly_headroom"] - candidate["task_weekly_fraction"] < reset_buffer):
            reason = "reset_buffer"
        elif (candidate["executor_id"] == "codex" and reset["drain"]
              and candidate.get("task_short_fraction") is not None and candidate.get("short_headroom") is not None
              and candidate["task_short_fraction"] > candidate["short_headroom"] - reset_buffer):
            reason = "short_window_capacity"
        elif "security_simulation" in needs and refusal is not None and refusal >= .5:
            reason = "refusal_rate"
        elif reviewing and not identity(candidate["model_id"]):
            reason = "review_identity_unknown"  # an undeclared routing group is never independent
        elif reviewing and any(same_model_identity(candidate["model_id"], author, groups) for author in authors):
            reason = "reviewer_is_author"
        elif candidate.get("cost_class", "paid_api") == "paid_api" and not allow_paid:
            reason = "paid_spend_disabled"
        elif candidate.get("availability", {}).get("state") == "UNAVAILABLE":
            reason = "availability:" + candidate.get("availability", {}).get("reason", "unverified")
        elif identity(candidate["model_id"]) in {identity(m) for m in refused_models}:
            reason = "model_refused"
        elif refused_models and tier < refusal_tier:
            reason = "refusal_retry_tier"
        elif pool_limits and (in_flight_by_upstream or rpm_by_pool or tpm_by_pool):
            raw_key = upstream_namespace(candidate.get("model_id")) or str(
                candidate.get("account_ref") or candidate.get("connection_id") or ""
            ).lower()
            counter_key = pool_key_for_upstream(raw_key, pool_limits) if raw_key else ""
            pool_cfg = (pool_limits.get(raw_key) or pool_limits.get(counter_key) or {}) if counter_key else {}
            cap = pool_cfg.get("max_in_flight")
            rpm_cap = pool_cfg.get("rpm_limit")
            tpm_cap = pool_cfg.get("tpm_limit")
            in_flight = int((in_flight_by_upstream or {}).get(counter_key) or 0) if counter_key else 0
            rpm_used = int((rpm_by_pool or {}).get(counter_key) or 0) if counter_key else 0
            tpm_used = int((tpm_by_pool or {}).get(counter_key) or 0) if counter_key else 0
            if type(cap) is int and cap > 0 and in_flight >= cap:
                reason = "pool_concurrency_limit"
            elif type(rpm_cap) is int and rpm_cap > 0 and rpm_used >= rpm_cap:
                reason = "pool_rpm_limit"
            elif type(tpm_cap) is int and tpm_cap > 0 and tpm_used >= tpm_cap:
                reason = "pool_tpm_limit"
        if reason:
            exclusion = {"binding_id": candidate["binding_id"], "model_id": candidate["model_id"], "filter": reason}
            if reason == "executor_unavailable":
                exclusion["executor_id"] = candidate["executor_id"]  # name the missing CLI
            elif reason == "account_quarantined":
                exclusion["retry_at"] = quota.get("retry_at")
            elif reason == "weekly_pace":
                exclusion["retry_at"] = pace_hold
                exclusion["cause"] = pace_cause
                if candidate.get("weekly_pace_input") == "gateway_reading_aged":
                    exclusion["weekly_pace_input"] = "gateway_reading_aged"
            elif reason == "quota_exhausted":
                from .quota_guard import parse_time
                exclusion["retry_at"] = parse_time(quota.get("until"))
            elif reason in {"pool_concurrency_limit", "pool_rpm_limit", "pool_tpm_limit"}:
                exclusion["retry_at"] = float(now + 30.0)
            excluded.append(exclusion)
            excluded_tiers[candidate["binding_id"]] = tier
            continue
        quota_penalty = int(quota.get("decision") in {"switch", "warn"})
        if (candidate["executor_id"] == "codex" and reset["drain"]
                and quota.get("window") in {"weekly", "7d", "week"}):
            quota_penalty = 0  # announced draining replaces the weekly pacing reserve
        bucket = profile.get("task_buckets", {}).get(f"{kind}:{difficulty}", profile)
        cost_class = candidate.get("cost_class", "paid_api")
        observed_headroom = candidate.get("quota_headroom")
        headroom = max(.01, min(1., observed_headroom)) if observed_headroom is not None else 1.
        cost = {"free": 0., "subscription": 1. + (1. - headroom), "paid_api": 3.}[cost_class]
        base_cost = cost
        if candidate["executor_id"] == "codex" and cost_class == "subscription" and reset["drain"]:
            cost = 1.
        reset["cost_adjustment"] = cost - base_cost
        for entry in reset_observations:
            if entry["binding_id"] == candidate["binding_id"]:
                entry["cost_adjustment"] = reset["cost_adjustment"]
        tool_penalty = 2 * (1 - metadata.get("tool_reliability", 1.)) if "tool_use" in needs else 0.
        refusal_penalty = 2 * refusal_risk
        context_bonus = min(.5, window / 2_000_000) if "long_context" in needs else 0.
        latency_penalty = min(2., (override.get("median_ok_seconds", bucket.get("median_ok_seconds")) or 0) / 60) if "low_latency" in needs else 0.
        availability_penalty = candidate.get("availability", {}).get("penalty", 0.)
        # Use a time-limited allowance or expiring credits before they lapse (#1471).
        resource_urgency = urgency(candidate.get("resources"), now=now)
        mult_info = candidate.get("credit_multiplier_info") if isinstance(candidate.get("credit_multiplier_info"), Mapping) else None
        if mult_info is not None:
            mult_source = str(mult_info.get("source") or "unknown")
            raw_mult = mult_info.get("effective")
        else:
            raw_mult = candidate.get("credit_multiplier", override.get("credit_multiplier", 1.0))
            mult_source = "configured" if ("credit_multiplier" in candidate or "credit_multiplier" in override) else "default"
        credit_cost_penalty = (
            round(min(1.5, max(0.0, math.log2(float(raw_mult)) * 0.4)), 4)
            if type(raw_mult) in (int, float) and math.isfinite(raw_mult) and float(raw_mult) > 1.0
            else 0.0
        )
        credit_cost_uncertainty_penalty = (
            0.15
            if (mult_source == "unknown" and cost_class == "subscription" and not candidate.get("paced_provider"))
            else 0.0
        )
        lightweight_task = (
            not artifact_review
            and not failed_model
            and not refused_models
            and (difficulty <= 2 or (kind in {"writing", "analysis"} and context_need <= 64_000))
        )
        avail_rank_val = int(candidate.get("availability", {}).get("state") not in {"AVAILABLE", "READY"})
        free_channel_fit_bonus = (
            0.25
            if (lightweight_task and (cost_class == "free" or resource_urgency > 0)
                and avail_rank_val == 0 and quota_penalty == 0
                and quota.get("reason") != "liveness_cooldown"
                and candidate["binding_id"] not in avoid_bindings)
            else 0.0
        )
        success = bucket.get("success_rate")
        reliability_penalty = measured_reliability_penalty(bucket)
        adjusted = (cost + tool_penalty + refusal_penalty + latency_penalty + availability_penalty
                    + pace_penalty + reliability_penalty + credit_cost_penalty + credit_cost_uncertainty_penalty
                    - context_bonus - resource_urgency - free_channel_fit_bonus)
        breakdown = {"availability_rank": avail_rank_val,
                     "base_cost": base_cost, "tool_penalty": tool_penalty, "availability_penalty": availability_penalty,
                     "resource_urgency": resource_urgency, "credit_cost_penalty": credit_cost_penalty,
                     "credit_cost_uncertainty_penalty": credit_cost_uncertainty_penalty,
                     "credit_multiplier_source": mult_source,
                     "free_channel_fit_bonus": free_channel_fit_bonus,
                     "pace_penalty": pace_penalty, "reliability_penalty": reliability_penalty,
                     "refusal_penalty": refusal_penalty, "context_bonus": context_bonus,
                     "latency_penalty": latency_penalty, "reset_adjustment": cost - base_cost,
                     "quota_pressure": 1. - headroom if observed_headroom is not None else None, "quota_penalty": quota_penalty}
        if pace_penalty > 0:
            breakdown["pace_cause"] = "ahead_of_pace"
            pace_retry, _ = weekly_pace_decision(candidate, now=now, pace=weekly_pace)
            if pace_retry is not None:
                breakdown["pace_retry_at"] = pace_retry
        speed = override.get("median_ok_seconds", bucket.get("median_ok_seconds"))
        characteristics = {key: metadata.get(key) for key in
                           ("context_window", "max_output_tokens", "input_modalities", "reasoning", "tool_reliability", "chinese")}
        characteristics["context_window"] = window
        ranked.append(dict(candidate, review_transport=review_transport, availability=dict(candidate.get("availability") or {"state": "UNKNOWN"}), context_window=window, tier=tier, tier_source=tier_source, tier_basis=tier_basis, unproven=unproven, cost_class=cost_class,
                           cost=cost, quota_penalty=quota_penalty, success_rate=success, speed=speed,
                           reset=reset, characteristics=characteristics, quota_headroom=observed_headroom,
                           score_breakdown=breakdown, refusal_risk=refusal_risk,
                           liveness_rank=(LIVENESS_AVOIDED if candidate["binding_id"] in avoid_bindings
                                          else LIVENESS_COOLING if quota.get("reason") == "liveness_cooldown"
                                          else LIVENESS_SAME_UPSTREAM if upstream_key(candidate) in avoid_upstreams
                                          else LIVENESS_CLEAN),
                           availability_rank=int(candidate.get("availability", {}).get("state") not in {"AVAILABLE", "READY"}),
                           score=[quota_penalty, adjusted, -(success if success is not None else -1),
                                  speed if speed is not None else float("inf")]))
    if account_feedback is not None:
        try:
            from .multi_account.feedback_policy import apply_routing_feedback
            apply_routing_feedback(ranked, account_feedback, now=now)
        except Exception:  # noqa: BLE001 - measured advice cannot replace hard admission
            pass
    ranked.sort(key=lambda c: (c["availability_rank"], *c["score"], c["binding_id"]))
    if not ranked:
        error = ModelSelectionError("review_not_independent" if artifact_review else "no_willing_model" if refused_models or "security_simulation" in needs else "no_runnable_model",
                                    excluded=excluded, refusals=refused_models, pin=pin)
        error.decision["reset"] = reset_decision(reset_signal, now=now, buffer=reset_buffer, demand=False)
        raise error
    liveness_fallback = False
    if stall_tier or any(c["liveness_rank"] for c in ranked):
        # Tier rules first: liveness only orders candidates at or above the floor (the
        # task's difficulty and, for a stall retry, the stalled attempt's tier). When none
        # reaches it, only the strongest tier present competes, so a stall never moves a
        # step to a weaker model than the one that stalled.
        floor = max(difficulty, stall_tier)
        top = max(c["tier"] for c in ranked)
        eligible = set()
        if failed_model and not refused_models:
            # A capability retry must still reach the models escalation needs: a higher
            # tier first, then a distinct model at the failed tier. A cooling one among
            # them is ranked lower, never removed in favour of the model that just failed.
            eligible = {c["binding_id"] for c in ranked if c["tier"] > failed_tier} or {
                c["binding_id"] for c in ranked if c["tier"] == failed_tier
                and identity(c["model_id"]) != identity(failed_model)}
            floor = max(floor, failed_tier)
        eligible = eligible or {c["binding_id"] for c in ranked if c["tier"] >= floor} or {
            c["binding_id"] for c in ranked if c["tier"] == top}
        best = min(c["liveness_rank"] for c in ranked if c["binding_id"] in eligible)
        kept = []
        for item in ranked:
            below_floor = bool(stall_tier) and item["binding_id"] not in eligible
            if item["binding_id"] == pin or (item["liveness_rank"] <= best and not below_floor):
                kept.append(item)
                continue
            exclusion = {"binding_id": item["binding_id"], "model_id": item["model_id"],
                         "filter": "stall_tier_floor" if below_floor else
                         ("liveness_step_avoided", "liveness_cooldown", "liveness_same_upstream")[
                             (LIVENESS_AVOIDED, LIVENESS_COOLING, LIVENESS_SAME_UPSTREAM).index(item["liveness_rank"])]}
            if exclusion["filter"] == "liveness_cooldown":
                from .quota_guard import parse_time
                exclusion["retry_at"] = parse_time((item.get("quota") or {}).get("until"))
            excluded.append(exclusion)
            excluded_tiers[item["binding_id"]] = item["tier"]
        ranked = kept
        liveness_fallback = best >= LIVENESS_COOLING
    pinned = next((c for c in ranked if c["binding_id"] == pin), None)
    if pin and pinned is None and not refused_models:
        raise ModelSelectionError("review_not_independent" if artifact_review else "pinned_model_unavailable", excluded=excluded, pin=pin)
    # Review fitness is a hard boundary before retry preferences. A weaker
    # different model must not displace the only qualifying independent model.
    pool = [c for c in ranked if c["tier"] >= difficulty] if artifact_review else ranked
    if not pool:
        raise ModelSelectionError("review_not_independent", excluded=excluded)
    if refused_models:
        pool = sorted(pool, key=lambda c: (c["availability_rank"], c["refusal_risk"], *c["score"], c["binding_id"]))
        pinned = None  # a refusal never sends the task back to its pinned author
    downgrade_fallback = False
    if failed_model and not pinned and not refused_models:
        # Compare tiers before preferring a different model: a weaker distinct
        # model must never displace an eligible equal-or-higher one (#1280).
        def distinct(items):
            return [c for c in items if identity(c["model_id"]) != identity(failed_model)]
        higher = [c for c in pool if c["tier"] > failed_tier]
        same = [c for c in pool if c["tier"] == failed_tier]
        if higher:
            pool = distinct(higher) or higher
        elif same:
            pool = distinct(same) or same
        else:
            downgrade_fallback = True  # nothing eligible at or above the failed tier
            pool = [c for c in pool if c["tier"] == max(item["tier"] for item in pool)]
    if artifact_review and codex_authored and not pinned:
        best_availability = min(c["availability_rank"] for c in pool)
        independent_toolless = [c for c in pool if c["review_transport"] in {"toolless", "claude_code"}
                                and c["availability_rank"] == best_availability]
        pool = independent_toolless or pool
    exploratory = [c for c in pool if c["unproven"] and c["cost_class"] == "free"]
    # Evidence always outranks an unmeasured fallback outside bounded exploration,
    # unless every proven qualifying candidate is degraded (cooling/shortfall/unready)
    # while a clean, ready unmeasured candidate exists.
    proven_pool = [c for c in pool if not c["unproven"] and c["tier"] >= difficulty]
    has_healthy_proven = any(
        c["availability_rank"] == 0 and c["liveness_rank"] == 0 and c["quota_penalty"] == 0
        for c in proven_pool
    )
    clean_unproven = [
        c for c in pool
        if c["unproven"] and c["availability_rank"] == 0 and c["liveness_rank"] == 0 and c["quota_penalty"] == 0
    ]
    if proven_pool and (has_healthy_proven or not clean_unproven or artifact_review or bool(failed_model)):
        pool = proven_pool
    qualifying = [c for c in pool if c["tier"] >= difficulty]
    has_healthy_qualifying = any(
        c["availability_rank"] == 0 and c["liveness_rank"] == 0 and c["quota_penalty"] == 0
        for c in qualifying
    )
    # Exploration must not turn unknown availability into a prerequisite probe
    # or displace an otherwise qualifying ready/available connection.
    if any(c["availability_rank"] == 0 for c in qualifying):
        exploratory = [c for c in exploratory if c["availability_rank"] == 0]
    if clean_unproven:
        exploratory = [c for c in exploratory if c["liveness_rank"] == 0] or exploratory
    reason = "cheapest_qualifying"
    if pinned:
        chosen, reason = pinned, "pin"
    elif (not failed_model and not artifact_review and difficulty <= 4
          and exploration_draw < exploration_budget and exploratory):
        chosen, reason = exploratory[0], "exploration"
    elif qualifying and (has_healthy_qualifying or not clean_unproven or artifact_review or bool(failed_model) or difficulty > 4):
        chosen = qualifying[0]
    elif clean_unproven and not artifact_review and not failed_model and difficulty <= 4:
        chosen, reason = clean_unproven[0], "prior_only_unproven"
    elif qualifying:
        chosen = qualifying[0]
    else:
        chosen, reason = max(pool, key=lambda c: c["tier"]), "underpowered"
    if refused_models:
        reason = "refusal_redispatch"
    if failed_model and not pinned and reason != "underpowered" and not refused_models:
        reason = ("retry_lower_tier_fallback" if downgrade_fallback else
                  "escalation_higher_tier" if chosen["tier"] > failed_tier else
                  "retry_different_model" if identity(chosen["model_id"]) != identity(failed_model) else "retry_only_model")
    if artifact_review and chosen["tier"] < difficulty:
        raise ModelSelectionError("review_not_independent", excluded=excluded)
    if liveness_fallback and not pinned and not (failed_model and not refused_models):
        # A capability retry keeps its escalation reason; the liveness block records the fallback.
        reason = ("liveness_same_binding_fallback" if chosen["liveness_rank"] == LIVENESS_AVOIDED
                  else "liveness_cooling_fallback")
    if chosen["unproven"] and difficulty >= 3 and reason != "exploration":
        reason = "prior_only_unproven"
    # JSON-safe evidence: unknown speed is null, never Infinity.
    for item in ranked:
        if item["score"][3] == float("inf"):
            item["score"][3] = None
    top = ranked[:5]
    if chosen not in top:
        top = [*top[:4], chosen]
    shown = {item["binding_id"] for item in top}
    hidden_tiers: dict[str, int] = {}
    for item in ranked:
        if item["binding_id"] not in shown:
            hidden_tiers[str(item["tier"])] = hidden_tiers.get(str(item["tier"]), 0) + 1
    excluded_summary: dict[str, int] = {}
    for row in excluded:
        excluded_summary[str(row.get("filter"))] = excluded_summary.get(str(row.get("filter")), 0) + 1
    # Stronger excluded bindings first, so the 10-row cap keeps the ones worth explaining.
    excluded = sorted(excluded, key=lambda row: -excluded_tiers.get(row.get("binding_id"), 0))
    evidence = [{key: item[key] for key in ("binding_id", "model_id", "executor_id", "availability", "tier", "tier_source", "tier_basis", "unproven",
                                            "cost_class", "cost", "quota_penalty", "success_rate", "speed", "score", "score_breakdown", "refusal_risk", "characteristics", "quota_headroom", "reset")}
                | ({"resources": item["resources"]} if item.get("resources") else {})
                for item in top]
    return {"difficulty": difficulty, "kind": kind, "binding_ref": chosen["binding_id"],
            "model_id": chosen["model_id"], "executor_kind": chosen["executor_id"], "tier": chosen["tier"], "reason": reason,
            "underpowered": chosen["tier"] < difficulty, "candidates": evidence,
            "context_need": context_need, "needs": list(needs), "content_class": content,
            "excluded_candidates": excluded[:10], "excluded_summary": excluded_summary,
            "ranked_summary": {"count": len(ranked), "shown": len(top),
                               "hidden_tiers": dict(sorted(hidden_tiers.items(), reverse=True))},
            "reset": chosen["reset"],
            "score_breakdown": chosen["score_breakdown"], "context_window": chosen["context_window"],
            "tier_source": chosen["tier_source"], "tier_basis": chosen["tier_basis"], "reset_observations": reset_observations,
            "characteristics": chosen["characteristics"],
            **({"downgrade_fallback": True} if downgrade_fallback else {}),
            **({"liveness": {"avoided_bindings": list(avoid_bindings), "avoided_upstreams": sorted(avoid_upstreams),
                             "rank": chosen["liveness_rank"], "fallback": liveness_fallback,
                             "stall_tier": stall_tier}}
               if avoid_bindings or avoid_upstreams or liveness_fallback or stall_tier else {})}


def prior_characteristics(model: str) -> dict[str, Any]:
    """Conservative bootstrap windows, replaced by metadata/evidence/Owner values.

    Unknown ids use 128k. The versioned exact-id table supplies other
    conservative estimates, not guarantees. Vision is unknown by default.
    """
    from .routing_capabilities import PRIOR_MODELS
    return {"context_window": 128_000, "input_modalities": ["text"],
            **PRIOR_MODELS.get(model.lower().rsplit("/", 1)[-1], {})}

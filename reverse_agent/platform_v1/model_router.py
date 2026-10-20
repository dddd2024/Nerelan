"""Pure per-task routing. Priors are bootstrap estimates, never measured claims.

Three completed attempts in a kind/difficulty bucket establish evidence. A bucket
with >=80% success and <=20% timeouts demonstrates that difficulty; otherwise
its tier is one lower. Exploration uses an injected draw (no hidden randomness).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence
import math

from .quota_guard import CONFIRMED_EXHAUSTION_REASONS
from .routing_inputs import requirements, reset_decision
import time

KINDS = frozenset({"code", "analysis", "writing", "research_design", "review"})
LEGACY_DIFFICULTY = {"simple": 2, "coder": 3, "complex": 4, "planner": 4, "reviewer": 4}
MIN_SAMPLES = 3


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


def model_identity(model: str) -> str:
    """Provider namespaces and free gateway suffixes do not make a new author."""
    identity = model.strip().lower().rsplit("/", 1)[-1]
    while identity.endswith((":free", "-free")):
        identity = identity.removesuffix(":free").removesuffix("-free")
    return identity


class ModelSelectionError(ValueError):
    def __init__(self, reason: str, *, excluded: list[dict[str, Any]], refusals: Sequence[str] = ()):
        super().__init__(reason)
        self.decision = {"reason": reason, "excluded_candidates": excluded[:10], "refusals": list(refusals)}


def select_model(candidates: Sequence[Mapping[str, Any]], *, difficulty: int, kind: str,
                 profiles: Mapping[str, Any] | None = None, role: str = "",
                 author_model: str = "", author_models: Sequence[str] = (), pin: str = "", failed_model: str = "",
                 failed_tier: int = 0, exploration_draw: float = 1.0,
                 exploration_budget: float = .1, context_need: int = 0,
                 needs: Sequence[str] = (), overrides: Mapping[str, Any] | None = None,
                 reset_signal: Mapping[str, Any] | None = None, now: float | None = None,
                 reset_buffer: float = .03, refused_models: Sequence[str] = (),
                 refusal_tier: int = 0, capability_table: Mapping[str, Any] | None = None,
                 allow_paid: bool = False) -> dict[str, Any]:
    """Pick from public binding metadata and precomputed quota observations.

    Scores prefer known availability/readiness, then quota, cost, success and speed.
    Subscription cost ranges from 1 to 2 as headroom falls; paid API cost is 3.
    Pins override price/tier, while readiness, quota and review fitness still apply.
    The injected uniform draw gives easy tasks a default 10% exploration rate.
    """
    task_traits({"difficulty": difficulty, "kind": kind})
    context_need, needs = requirements({"context_need": context_need, "needs": needs})
    content = "security_simulation" if "security_simulation" in needs else kind
    now = time.time() if now is None else now
    ranked, excluded, reset_observations = [], [], []
    authors = {model_identity(m) for m in (*author_models, author_model) if m}
    artifact_review = (kind == "review" or role == "reviewer") and bool(author_models)
    for candidate in candidates:
        profile = (profiles or {}).get(candidate["binding_id"], {})
        override = (overrides or {}).get(candidate["binding_id"], {})
        # Public metadata < measured evidence < explicit Owner values.
        metadata = {**prior_characteristics(candidate["model_id"]),
                    **{k: v for k, v in (candidate.get("metadata") or {}).items() if v is not None},
                    **{k: v for k, v in profile.items() if v is not None}, **override}
        window = metadata["context_window"]
        if type(window) not in (int, float) or isinstance(window, float) and not math.isfinite(window) or window <= 0:
            window = prior_characteristics(candidate["model_id"])["context_window"]
        refusal = metadata.get("refusal_rates", {}).get(content)
        refusal_risk = .25 if refusal is None else max(0., min(1., refusal))
        quota = candidate.get("quota") or {}
        from .routing_capabilities import tier_evidence
        tier, unproven, tier_source = tier_evidence(candidate["model_id"], profile, kind, difficulty, capability_table, override)
        reset = reset_decision(reset_signal, now=now, buffer=reset_buffer,
                               weekly_remaining=candidate.get("weekly_headroom"), short_resets_at=candidate.get("short_resets_at"))
        if candidate["executor_id"] == "codex" and candidate.get("cost_class") == "subscription":
            reset_observations.append({"binding_id": candidate["binding_id"], **reset})
        reason = ""
        endpoints = metadata.get("native_endpoints", ())
        responses_only = endpoints and all(endpoint in {"/responses", "/v1/responses", "responses"} for endpoint in endpoints)
        if (not candidate.get("enabled", True) or not candidate.get("runnable", True)
                or role == "planner" and candidate["executor_id"] not in {"codex", "claude_code"}
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
        elif quota.get("reason") in CONFIRMED_EXHAUSTION_REASONS:
            reason = "quota_exhausted"
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
              and candidate["task_short_fraction"] > candidate["short_headroom"]):
            reason = "short_window_capacity"
        elif "security_simulation" in needs and refusal is not None and refusal >= .5:
            reason = "refusal_rate"
        elif (kind == "review" or role == "reviewer") and model_identity(candidate["model_id"]) in authors:
            reason = "reviewer_is_author"
        elif candidate.get("cost_class", "paid_api") == "paid_api" and not allow_paid:
            reason = "paid_spend_disabled"
        elif candidate.get("availability", {}).get("state") == "UNAVAILABLE":
            reason = "availability:" + candidate.get("availability", {}).get("reason", "unverified")
        elif model_identity(candidate["model_id"]) in {model_identity(m) for m in refused_models}:
            reason = "model_refused"
        elif refused_models and tier < refusal_tier:
            reason = "refusal_retry_tier"
        if reason:
            excluded.append({"binding_id": candidate["binding_id"], "model_id": candidate["model_id"], "filter": reason})
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
        adjusted = cost + tool_penalty + refusal_penalty + latency_penalty + availability_penalty - context_bonus
        breakdown = {"availability_rank": int(candidate.get("availability", {}).get("state") not in {"AVAILABLE", "READY"}),
                     "base_cost": base_cost, "tool_penalty": tool_penalty, "availability_penalty": availability_penalty,
                     "refusal_penalty": refusal_penalty, "context_bonus": context_bonus,
                     "latency_penalty": latency_penalty, "reset_adjustment": cost - base_cost,
                     "quota_pressure": 1. - headroom if observed_headroom is not None else None, "quota_penalty": quota_penalty}
        success = bucket.get("success_rate")
        speed = override.get("median_ok_seconds", bucket.get("median_ok_seconds"))
        characteristics = {key: metadata.get(key) for key in
                           ("context_window", "max_output_tokens", "input_modalities", "reasoning", "tool_reliability", "chinese")}
        characteristics["context_window"] = window
        ranked.append(dict(candidate, availability=dict(candidate.get("availability") or {"state": "UNKNOWN"}), context_window=window, tier=tier, tier_source=tier_source, unproven=unproven, cost_class=cost_class,
                           cost=cost, quota_penalty=quota_penalty, success_rate=success, speed=speed,
                           reset=reset, characteristics=characteristics, quota_headroom=observed_headroom,
                           score_breakdown=breakdown, refusal_risk=refusal_risk,
                           availability_rank=int(candidate.get("availability", {}).get("state") not in {"AVAILABLE", "READY"}),
                           score=[quota_penalty, adjusted, -(success if success is not None else -1),
                                  speed if speed is not None else float("inf")]))
    ranked.sort(key=lambda c: (c["availability_rank"], *c["score"], c["binding_id"]))
    if not ranked:
        error = ModelSelectionError("review_not_independent" if artifact_review else "no_willing_model" if refused_models or "security_simulation" in needs else "no_runnable_model",
                                    excluded=excluded, refusals=refused_models)
        error.decision["reset"] = reset_decision(reset_signal, now=now, buffer=reset_buffer, demand=False)
        raise error
    pinned = next((c for c in ranked if c["binding_id"] == pin), None)
    if pin and pinned is None and not refused_models:
        raise ModelSelectionError("review_not_independent" if artifact_review else "pinned_model_unavailable", excluded=excluded)
    # Review fitness is a hard boundary before retry preferences. A weaker
    # different model must not displace the only qualifying independent model.
    pool = [c for c in ranked if c["tier"] >= difficulty] if artifact_review else ranked
    if not pool:
        raise ModelSelectionError("review_not_independent", excluded=excluded)
    if refused_models:
        pool = sorted(pool, key=lambda c: (c["availability_rank"], c["refusal_risk"], *c["score"], c["binding_id"]))
        pinned = None  # a refusal never sends the task back to its pinned author
    if failed_model and not pinned and not refused_models:
        distinct = [c for c in pool if model_identity(c["model_id"]) != model_identity(failed_model)]
        pool = distinct or pool
        higher = [c for c in pool if c["tier"] > failed_tier]
        if higher:
            pool = higher
        else:
            same = [c for c in pool if c["tier"] == failed_tier]
            pool = same or [c for c in pool if c["tier"] == max(item["tier"] for item in pool)]
    exploratory = [c for c in pool if c["unproven"] and c["cost_class"] == "free"]
    # Evidence always outranks an unmeasured fallback outside bounded exploration.
    proven_pool = [c for c in pool if not c["unproven"] and c["tier"] >= difficulty]
    if proven_pool:
        pool = proven_pool
    qualifying = [c for c in pool if c["tier"] >= difficulty]
    # Exploration must not turn unknown availability into a prerequisite probe
    # or displace an otherwise qualifying ready/available connection.
    if any(c["availability_rank"] == 0 for c in qualifying):
        exploratory = [c for c in exploratory if c["availability_rank"] == 0]
    reason = "cheapest_qualifying"
    if pinned:
        chosen, reason = pinned, "pin"
    elif not failed_model and difficulty <= 2 and exploration_draw < exploration_budget and exploratory:
        chosen, reason = exploratory[0], "exploration"
    elif qualifying:
        chosen = qualifying[0]
    else:
        chosen, reason = max(pool, key=lambda c: c["tier"]), "underpowered"
    if refused_models:
        reason = "refusal_redispatch"
    if failed_model and not pinned and reason != "underpowered" and not refused_models:
        reason = ("escalation_higher_tier" if chosen["tier"] > failed_tier else
                  "retry_different_model" if model_identity(chosen["model_id"]) != model_identity(failed_model) else "retry_only_model")
    if artifact_review and chosen["tier"] < difficulty:
        raise ModelSelectionError("review_not_independent", excluded=excluded)
    if chosen["unproven"] and difficulty >= 3:
        reason = "prior_only_unproven"
    # JSON-safe evidence: unknown speed is null, never Infinity.
    for item in ranked:
        if item["score"][3] == float("inf"):
            item["score"][3] = None
    top = ranked[:5]
    if chosen not in top:
        top = [*top[:4], chosen]
    evidence = [{key: item[key] for key in ("binding_id", "model_id", "executor_id", "availability", "tier", "tier_source", "unproven",
                                            "cost_class", "cost", "quota_penalty", "success_rate", "speed", "score", "score_breakdown", "refusal_risk", "characteristics", "quota_headroom", "reset")}
                for item in top]
    return {"difficulty": difficulty, "kind": kind, "binding_ref": chosen["binding_id"],
            "model_id": chosen["model_id"], "executor_kind": chosen["executor_id"], "tier": chosen["tier"], "reason": reason,
            "underpowered": chosen["tier"] < difficulty, "candidates": evidence,
            "context_need": context_need, "needs": list(needs), "content_class": content,
            "excluded_candidates": excluded[:10], "reset": chosen["reset"],
            "score_breakdown": chosen["score_breakdown"], "context_window": chosen["context_window"],
            "tier_source": chosen["tier_source"], "reset_observations": reset_observations,
            "characteristics": chosen["characteristics"]}


def prior_characteristics(model: str) -> dict[str, Any]:
    """Conservative bootstrap windows, replaced by metadata/evidence/Owner values.

    Unknown ids use 128k. The versioned exact-id table supplies other
    conservative estimates, not guarantees. Vision is unknown by default.
    """
    from .routing_capabilities import PRIOR_MODELS
    return {"context_window": 128_000, "input_modalities": ["text"],
            **PRIOR_MODELS.get(model.lower().rsplit("/", 1)[-1], {})}

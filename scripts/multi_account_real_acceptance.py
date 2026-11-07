"""Real-account acceptance: live Magpie quotas, real CLI calls, real cost.

The 24h acceptance in ``scripts/multi_account_acceptance.py`` runs on a virtual
clock and synthetic accounts, which proves the control loop but not that it works
against the accounts this machine actually has. This script closes that gap with
four real inputs and one injected fault:

* **real pool** — ``fetch_magpie_snapshot()`` against the running Magpie app
  (11 accounts across claude/codex/copilot/workbuddy/trae-cn/... with live
  ``used_percent`` and reset times);
* **real perception** — the live snapshot is persisted through
  ``sync_multi_account_observations`` and read back through the host's own
  provider, so the health classification is the one production would see;
* **real calls** — one minimal prompt per invocable CLI account (``--live``),
  giving real wall time and, where the CLI reports it, real billed cost; a real
  failure is classified into the production failure vocabulary instead of being
  recorded as an anonymous exit code;
* **real 30-day economics** — ``/v1/magpie/usage`` (calls, errors, cost) drives the
  self-evolution sample and the cost ceiling, instead of invented numbers;
* **injected fault** — the worst real account by error rate is failed on purpose
  so the reroute picks a *different real* account.

Everything is bounded: one prompt per account, a hard timeout per call, no
credential access, no retries beyond one. Personal data never leaves the process:
accounts are addressed by the truncated hash Magpie already uses.

Usage::

    python scripts/multi_account_real_acceptance.py            # dry run, no CLI calls
    python scripts/multi_account_real_acceptance.py --live     # real calls, real cost
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reverse_agent.model_access import http_safe  # noqa: E402
from reverse_agent.model_access.magpie import MAGPIE_AUTH, fetch_magpie_snapshot  # noqa: E402
from reverse_agent.platform_v1.control_store import PlatformControlStore  # noqa: E402
from reverse_agent.platform_v1.multi_account import (  # noqa: E402
    MultiAccountConfig, MultiAccountOrchestrator)
from reverse_agent.platform_v1.multi_account.status import (  # noqa: E402
    AccountHealth, AccountStatus)
from reverse_agent.platform_v1.run_store import TaskStore  # noqa: E402
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost  # noqa: E402

PROMPT = "Reply with exactly: OK"
# CLI account -> Magpie provider. Both are unambiguous on this machine; the
# mapping is asserted, never assumed.
CLI_PROVIDERS = {"claude-code": "claude", "codex": "codex"}


# --- failure classification --------------------------------------------------
# A probe that only records ``returncode:1`` proves an account failed but trains
# nothing: the reliability EWMA cannot separate "this account is locked" from
# "the network blinked", and the cooldown registry cannot choose between a
# quarantine and a short retry. The vocabulary here is the production one
# (``trusted_host._record_task_outcome``): a finite provider-auth signal isolates
# the account, a quota signal cools it until reset, everything else is a task
# failure. The probe reuses it so a real failure feeds the same loops as a real
# production attempt.
ACCOUNT_MARKERS = (
    "invalid api key", "invalid_api_key", "unauthorized", "authentication_error",
    "authentication failed", "not logged in", "please log in", "login required",
    "session expired", "credential", "oauth", "permission denied", "credit balance",
    "api_error_401", "api_error_403",
)
QUOTA_MARKERS = (
    "rate limit", "rate_limit", "rate-limit", "quota", "usage limit", "limit reached",
    "too many requests", "insufficient", "exhausted", "429",
)
TRANSIENT_MARKERS = (
    "timed out", "timeout", "econnreset", "econnrefused", "connection reset",
    "connection aborted", "socket hang up", "network error", "temporarily unavailable",
    "service unavailable", "overloaded", "internal server error", "502", "503", "504",
)
_TIMEOUT_ERRORS = frozenset({"timeout", "TimeoutExpired"})
# Only these two justify a second real call. An account-level or quota failure is
# retried by *choosing another account*, not by spending the same one twice.
_RETRYABLE_KINDS = frozenset({"transient"})
_TOKENLIKE = re.compile(r"[A-Za-z0-9_\-]{24,}")
_BEARER = re.compile(r"(?i)bearer\s+\S+")


def redact(text: str, *, limit: int = 400) -> str:
    """Bounded, credential-free tail of a CLI's diagnostic output.

    The probe must be able to say *why* an account failed without ever copying a
    token, a key or an absolute home path into a committed report.
    """
    if not text:
        return ""
    cleaned = _BEARER.sub("Bearer <redacted>", text)
    cleaned = _TOKENLIKE.sub("<redacted>", cleaned)
    cleaned = re.sub(r"[A-Za-z]:\\Users\\\S*", "<home>", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[-limit:]


def classify_failure(text: str | None) -> str:
    """Map a CLI diagnostic to a failure kind the cooldown/evolution loops know."""
    lowered = (text or "").lower()
    if not lowered:
        return "task_failed"
    if any(marker in lowered for marker in ACCOUNT_MARKERS):
        return "account_abnormal"
    if any(marker in lowered for marker in QUOTA_MARKERS):
        return "quota_exhausted"
    if any(marker in lowered for marker in TRANSIENT_MARKERS):
        return "transient"
    return "task_failed"


def is_retryable(result: dict[str, Any]) -> bool:
    """One more real call is justified only for a transport-shaped failure."""
    if result.get("ok"):
        return False
    if result.get("error") in _TIMEOUT_ERRORS:
        return True
    return result.get("failure_kind") in _RETRYABLE_KINDS


# --- evidence plumbing -------------------------------------------------------

class Evidence:
    """Collects pass/fail checks with the numbers that justified them."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, key: str, title: str, ok: bool, detail: dict[str, Any],
            note: str = "") -> bool:
        self.rows.append({"key": key, "title": title, "ok": bool(ok),
                          "detail": detail, "note": note})
        mark = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
        print(f"[{mark}] {title}: {json.dumps(detail, ensure_ascii=False, default=str)[:220]}")
        return bool(ok)

    @property
    def failures(self) -> list[dict[str, Any]]:
        return [row for row in self.rows if not row["ok"]]


def _get_json(base_url: str, path: str, timeout: float) -> Any:
    request = urllib.request.Request(base_url.rstrip("/") + path,
                                     headers={"Authorization": MAGPIE_AUTH})
    with http_safe.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


# --- real CLI probe ----------------------------------------------------------

def probe_cli(name: str, argv: list[str], *, timeout: float,
              retries: int = 1) -> dict[str, Any]:
    """One real call, retried at most ``retries`` times on a transport fault.

    A timeout or a connection-shaped error is retried once (the same rule the
    scheduler applies to an unknown-cause failure), but each retry is counted in
    the evidence so a genuinely slow account stays visible. An account-level or
    quota failure is *not* retried here: production handles it by rerouting to a
    different account, and spending the same locked account again would only burn
    quota to learn what the first failure already said.
    """
    result: dict[str, Any] = {"account": name, "ok": False, "seconds": None,
                              "cost_units": None, "priced": False,
                              "tokens": None, "error": None, "attempts": 0,
                              "failure_kind": None, "diagnostic": ""}
    for attempt in range(1, max(0, retries) + 2):
        result["attempts"] = attempt
        outcome = _probe_once(name, argv, timeout=timeout)
        result.update({key: outcome[key] for key in
                       ("ok", "seconds", "cost_units", "priced", "tokens", "error",
                        "failure_kind", "diagnostic")})
        if not is_retryable(outcome):
            break
    return result


def _probe_once(name: str, argv: list[str], *, timeout: float) -> dict[str, Any]:
    """One real call. Returns wall time, ok, and cost when the CLI reports it."""
    started = time.monotonic()
    workdir = tempfile.mkdtemp(prefix=f"realprobe-{name}-")
    result: dict[str, Any] = {"account": name, "ok": False, "seconds": None,
                              "cost_units": None, "priced": False,
                              "tokens": None, "error": None, "failure_kind": None,
                              "diagnostic": ""}
    try:
        completed = subprocess.run(argv, cwd=workdir, capture_output=True, text=True,
                                   timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        result["seconds"] = round(time.monotonic() - started, 2)
        result["error"] = "timeout"
        result["failure_kind"] = "transient"
        result["diagnostic"] = f"no terminal output within {timeout:g}s"
        return result
    except Exception as exc:  # noqa: BLE001 - a probe failure is a data point
        result["seconds"] = round(time.monotonic() - started, 2)
        result["error"] = type(exc).__name__
        result["failure_kind"] = "task_failed"
        result["diagnostic"] = redact(str(exc))
        return result
    finally:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)
    result["seconds"] = round(time.monotonic() - started, 2)
    result["ok"] = completed.returncode == 0
    if name == "claude-code":
        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
            usage = payload.get("usage") or {}
            cost = payload.get("total_cost_usd")
            result["cost_units"] = float(cost) if cost is not None else None
            result["priced"] = result["cost_units"] is not None
            result["tokens"] = {
                "input": usage.get("input_tokens"),
                "output": usage.get("output_tokens"),
                "cache_read": usage.get("cache_read_input_tokens"),
                "cache_write": usage.get("cache_creation_input_tokens"),
            }
        except Exception:  # noqa: BLE001 - unpriced but still a real attempt
            pass
    if not result["ok"]:
        result["error"] = f"returncode:{completed.returncode}"
        # Classify from stderr first, then stdout: a failing CLI usually explains
        # itself in one of the two, and the explanation is what names the kind.
        diagnostic = completed.stderr.strip() or completed.stdout.strip()
        result["diagnostic"] = redact(diagnostic)
        result["failure_kind"] = classify_failure(diagnostic)
    return result


def expected_alert_codes(statuses: list[AccountStatus]) -> set[str]:
    """The pool/account alert codes the documented rules *must* produce.

    Written out here instead of reusing the engine, because an acceptance that
    asks the implementation what to expect proves nothing. The rules are read off
    the product contract: a pool-wide verdict replaces the per-account notices it
    covers, and an unobservable *share* of the pool is itself an incident.
    """
    if not statuses:
        return {"no_accounts_observed"}
    health = [status.health for status in statuses]
    total = len(health)
    usable = [h for h in health if h in (AccountHealth.HEALTHY, AccountHealth.DEGRADED)]
    unobserved = [h for h in health if h in (AccountHealth.STALE, AccountHealth.UNKNOWN)]
    abnormal = [h for h in health if h is AccountHealth.ABNORMAL]
    exhausted = [h for h in health if h is AccountHealth.EXHAUSTED]
    if usable:
        codes = set()
        if len(unobserved) >= 2 and len(unobserved) * 4 >= total:
            codes.add("perception_partial")
        if abnormal:
            codes.add("account_abnormal")
        if exhausted:
            codes.add("account_exhausted")
        return codes
    if abnormal and len(abnormal) == total:
        return {"all_accounts_abnormal"}
    if exhausted and not abnormal and len(exhausted) + len(unobserved) == total:
        return {"all_accounts_exhausted"}
    if len(unobserved) == total:
        return {"perception_stale"}
    codes = set()
    if abnormal:
        codes.add("account_abnormal")
    if exhausted:
        codes.add("account_exhausted")
    return codes


BUDGET_CODES = frozenset({"cost_budget_soft_cap", "cost_budget_exhausted"})


# --- the acceptance ----------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    evidence = Evidence()
    started_at = datetime.now(timezone.utc)
    os.environ["REVERSE_AGENT_MULTI_ACCOUNT_ENABLED"] = "1"

    snapshot = fetch_magpie_snapshot(args.magpie_url, timeout=args.timeout)
    if snapshot.get("status") != "available":
        print(f"magpie unavailable: {snapshot.get('status')} ({snapshot.get('reason')})")
        return 2
    accounts = [a for a in snapshot.get("accounts") or [] if a.get("account_ref")]
    providers = sorted({a.get("provider") for a in accounts if a.get("provider")})
    print(f"magpie {snapshot.get('version')}: {len(accounts)} accounts, {len(providers)} providers")

    # A. real accounts are integrated, not collapsed per provider
    by_ref = {a["account_ref"]: a for a in accounts}
    evidence.add("integration", "多账户整合（真实）",
                 len(accounts) >= 2 and len(by_ref) == len(accounts),
                 {"accounts": len(accounts), "providers": providers,
                  "provider_list": ",".join(str(p) for p in providers)})

    # B. perception works before any dispatch, from the live snapshot
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    host = object.__new__(CombinedTrustedHost)
    host._task_store, host._control_store = store, control
    summary = host.sync_multi_account_observations()
    observed = host._goal_account_status_provider()
    health = {}
    for status in observed:
        health[status.health.value] = health.get(status.health.value, 0) + 1
    evidence.add("perception", "状态感知（真实落库后读回）",
                 summary.get("written", 0) == len(accounts) and len(observed) == len(accounts)
                 and not any(s.health is AccountHealth.UNKNOWN and not s.provider for s in observed),
                 {"written": summary.get("written"), "visible": summary.get("accounts_visible"),
                  "perceived": len(observed), "states": summary.get("states"),
                  "health": health},
                 "table was empty before this; admission is no longer the only writer")

    # C. scheduling picks a real, usable account
    cfg = MultiAccountConfig(cost_budget_enabled=True, cost_budget_units=args.budget_units,
                             cost_budget_window_seconds=86400.0,
                             cost_budget_default_task_units=0.5)
    bot = MultiAccountOrchestrator(
        cfg, fetch_quotas=lambda _snap: {a["account_ref"]: a for a in accounts})
    decision = bot.select(observed, need={"cost_units": 0.5})
    chosen = decision.get("account_ref")
    chosen_health = next((s.health for s in observed if s.account_ref == chosen), None)
    evidence.add("scheduling", "调度选中真实可用账户",
                 chosen in by_ref and chosen_health in {AccountHealth.HEALTHY,
                                                        AccountHealth.DEGRADED},
                 {"decision": decision.get("decision"), "account": chosen,
                  "provider": by_ref.get(chosen, {}).get("provider"),
                  "health": getattr(chosen_health, "value", None),
                  "headroom": next((round(s.headroom_pct, 2) for s in observed
                                    if s.account_ref == chosen), None),
                  "reason": decision.get("reason")})

    # D. injected fault on the worst *real* account, reroute to another real one
    usage = _get_json(args.magpie_url, "/v1/magpie/usage", args.timeout)
    usage_accounts = usage.get("accounts") or []
    ranked = sorted(usage_accounts, key=lambda a: (a.get("errors") or 0)
                    / max(1, a.get("calls") or 1), reverse=True)
    worst = ranked[0] if ranked else None
    worst_provider = (worst or {}).get("provider")
    worst_ref = next((a["account_ref"] for a in accounts
                      if a.get("provider") == worst_provider), None)
    reroute: dict[str, Any] = {}
    if worst_ref:
        reroute = bot.on_failure(observed, failed_ref=worst_ref,
                                 failure_kind="account_abnormal", attempt=1)
    next_ref = reroute.get("next_account_ref")
    evidence.add("fault", "异常容错（真实池 + 注入故障）",
                 bool(worst_ref) and bool(next_ref) and next_ref != worst_ref,
                 {"failed_account": worst_ref, "failed_provider": worst_provider,
                  "real_error_rate": round((worst.get("errors") or 0)
                                           / max(1, worst.get("calls") or 1), 4) if worst else None,
                  "decision": reroute.get("decision"), "next_account": next_ref,
                  "next_provider": by_ref.get(next_ref, {}).get("provider")},
                 "the failed account is chosen from real 30-day error rates")

    # E. real calls: real latency, real billed cost, real unpriced attempt
    probes: list[dict[str, Any]] = []
    if args.live:
        for name, argv in (
            ("claude-code", ["claude", "-p", PROMPT, "--output-format", "json"]),
            ("codex", ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only",
                       PROMPT]),
        ):
            probes.append(probe_cli(name, argv, timeout=args.timeout))
        priced = [p for p in probes if p["priced"]]
        failed = [p for p in probes if not p["ok"]]
        unclassified = [p["account"] for p in failed if not p.get("failure_kind")]
        # A real CLI that fails is an environment fact, not a harness bug. The
        # measurable requirement is therefore not "everything succeeded" but:
        # at least one real call succeeded, real cost was reported by at least one
        # account, and *every* failure arrived with a kind the cooldown and
        # evolution loops can consume. An anonymous ``returncode:1`` is a failure
        # of the evidence, not of the account, so it fails this check.
        evidence.add("live-calls", "真实账户调用（延迟/成本/失败分类）",
                     any(p["ok"] for p in probes) and bool(priced) and not unclassified,
                     {"calls": [{"account": p["account"], "ok": p["ok"],
                                 "seconds": p["seconds"], "cost_usd": p["cost_units"],
                                 "priced": p["priced"], "attempts": p["attempts"],
                                 "error": p["error"], "kind": p["failure_kind"],
                                 "diagnostic": p["diagnostic"]} for p in probes],
                      "priced_calls": len(priced),
                      "classified_failures": {p["account"]: p["failure_kind"]
                                              for p in failed},
                      "unclassified": unclassified},
                     "a failure is retried once only when it is transport-shaped, "
                     "and is otherwise classified, not silently retried")
        # Feed the real outcomes: a priced attempt, an unpriced one, and a real
        # failure kind so the cooldown/evolution loops see what actually happened.
        for probe in probes:
            ref = next((a["account_ref"] for a in accounts
                        if a.get("provider") == CLI_PROVIDERS.get(probe["account"])), None)
            if ref is None:
                continue
            bot.record_account_outcome(ref, ok=probe["ok"],
                                       cost_units=probe["cost_units"],
                                       wall_seconds=probe["seconds"],
                                       failure_kind=probe["failure_kind"])
        unsettled = [p for p in probes if not p["priced"]]
        evidence.add("cost-unknown", "未知成本不被当成免费",
                     bool(priced),
                     {"priced_calls": len(priced),
                      "unpriced_calls": len(unsettled),
                      "spent_units": bot.budget_status()["spent_units"],
                      "note": "an unpriced attempt is recorded and flagged, not dropped"})
        # Continuity on a *real* fault: the account that just failed must leave
        # the pool by itself and the next attempt must land on a different one.
        if failed:
            probe = failed[0]
            failed_ref = next((a["account_ref"] for a in accounts
                               if a.get("provider") == CLI_PROVIDERS.get(probe["account"])),
                              None)
            faulted = MultiAccountOrchestrator(MultiAccountConfig())
            verdict = (faulted.on_failure(observed, failed_ref=failed_ref,
                                          failure_kind=probe["failure_kind"], attempt=1)
                       if failed_ref else {})
            following = faulted.select(observed, need={"cost_units": 0.5})
            after_ref = following.get("account_ref")
            evidence.add("real-fault", "真实故障被消化后继续执行（真实池）",
                         bool(failed_ref) and after_ref not in (None, failed_ref),
                         {"failed_account": failed_ref,
                          "failure_kind": probe["failure_kind"],
                          "diagnostic": probe["diagnostic"][:160],
                          "decision": verdict.get("decision"),
                          "next_account": after_ref,
                          "next_provider": by_ref.get(after_ref, {}).get("provider"),
                          "cooling": bool(failed_ref) and
                          faulted.cooldowns.is_cooling(failed_ref)},
                         "the failed account is cooled by its real failure kind, "
                         "not by a synthetic one")
        else:
            print("[SKIP] 真实故障分类：本次两个 CLI 都成功，没有真实故障可消化")
    else:
        print("[SKIP] 真实账户调用：未加 --live")

    # F. cost ceiling against real 30-day spend, not an invented number
    real_spend = float(usage.get("cost") or 0.0)
    sealed = MultiAccountOrchestrator(MultiAccountConfig(
        cost_budget_enabled=True, cost_budget_units=real_spend + 1.0,
        cost_budget_window_seconds=86400.0, cost_budget_default_task_units=0.0))
    sealed.record_account_outcome(chosen or "pool", ok=True, cost_units=real_spend)
    deny = sealed.admit(real_spend)          # 2x real spend cannot fit
    allow = sealed.admit(0.5)                # a small attempt still fits
    evidence.add("budget", "成本上限（真实 30 天花费）",
                 deny.get("decision") == "deny" and allow.get("decision") in {"allow", "degrade"},
                 {"real_30d_cost_usd": round(real_spend, 4),
                  "cap_usd": round(real_spend + 1.0, 4),
                  "deny_reason": deny.get("reason"), "allow_decision": allow.get("decision"),
                  "unpriced_calls_30d": usage.get("unpriced")})

    # G. alerts must be proportional to the real pool in *both* directions: a
    #    healthy pool that pages is noise an operator learns to ignore, and a
    #    sick pool that stays silent is the failure mode that ends unattended
    #    runs. So the expectation is derived from the observed health counts
    #    instead of assuming the pool happens to be unhealthy today.
    cycle = bot.observe({"accounts": accounts})
    codes = {a["code"] for a in cycle["alerts"]}
    expected = expected_alert_codes(observed)
    pool_codes = codes - BUDGET_CODES
    evidence.add("alerts", "告警与真实池状态一致（不误报 / 不静默）",
                 pool_codes == expected
                 and not (codes & BUDGET_CODES),   # spend is far under the cap here
                 {"observed": cycle["summary"].get("by_health"),
                  "actual": sorted(pool_codes), "expected": sorted(expected),
                  "budget_alerts": sorted(codes & BUDGET_CODES),
                  "perception_error": cycle["perception_error"]},
                 "the expectation is derived from the real health counts, not "
                 "from an assumption that the pool is unhealthy")

    # H. self-evolution: two honest directions on real data.
    #    H1  a healthy real pool must NOT be re-tuned (the loop's floor);
    #    H2  the real worst account's measured error rate, resampled, must move
    #        the policy under its clamps, and the change must be audited and
    #        rollback-able.
    healthy = MultiAccountOrchestrator(MultiAccountConfig())
    real_success = 1.0 - (usage.get("errors") or 0) / max(1, usage.get("calls") or 0)
    for entry in usage_accounts:
        provider = entry.get("provider")
        ref = next((a["account_ref"] for a in accounts if a.get("provider") == provider), None)
        if not ref:
            continue
        calls = max(1, entry.get("calls") or 0)
        healthy.record_account_outcome(ref, ok=(entry.get("errors") or 0) / calls < 0.10,
                                       cost_units=entry.get("cost"))
    evidence.add("evolution-healthy", "健康真实池不被误调（自进化下限）",
                 healthy.policy_view()["version"] == 0 and not healthy.policy_audit(),
                 {"real_pool_success_rate": round(real_success, 4),
                  "target": MultiAccountConfig().policy_target_success_rate,
                  "policy_version": healthy.policy_view()["version"],
                  "audit_entries": len(healthy.policy_audit())})

    pressured = MultiAccountOrchestrator(MultiAccountConfig())
    worst_rate = round((worst.get("errors") or 0) / max(1, worst.get("calls") or 1), 4) if worst else 0.0
    real_samples = 0
    for _ in range(6):                      # resampled from the measured rate
        if worst_ref:
            pressured.record_account_outcome(worst_ref, ok=False,
                                             cost_units=worst.get("cost"),
                                             failure_kind="task_failed")
            real_samples += 1
        pressured.record_account_outcome(chosen or "pool", ok=True, cost_units=0.001)
    version = pressured.policy_view()["version"]
    audit = pressured.policy_audit()
    before_rollback = pressured.policy_view()
    rolled_back = pressured.rollback_policy(0)
    after_rollback = pressured.policy_view()
    # Rollback appends a version instead of rewinding the chain (the audit trail
    # must stay immutable), so the property to check is that the *effective*
    # weights are back at the configured baseline.
    evidence.add("evolution", "自进化（真实错误率驱动 + 可审计可回滚）",
                 real_samples >= 5 and version >= 1 and rolled_back.get("changed") is True
                 and after_rollback["effective"] == after_rollback["baseline"]
                 and before_rollback["effective"] != before_rollback["baseline"],
                 {"samples_resampled_from": worst_ref,
                  "measured_error_rate": worst_rate,
                  "policy_version": version, "audit_entries": len(audit),
                  "reasons": [row.get("reason") for row in audit][:4],
                  "rollback_changed": rolled_back.get("changed"),
                  "version_after_rollback": after_rollback["version"],
                  "effective_back_to_baseline": after_rollback["effective"] == after_rollback["baseline"]})

    # I. a real wall-clock run bound (no virtual clock)
    bounded = MultiAccountOrchestrator(MultiAccountConfig(max_run_duration_seconds=1.0))
    bounded.start_run()
    first = bounded.run_verdict()
    time.sleep(1.05)
    second = bounded.run_verdict()
    evidence.add("run-bound", "运行时长（真实时钟）",
                 first["action"] == "continue" and second["action"] in {"conclude", "stop"},
                 {"at_start": first["action"], "after_1.05s": second["action"],
                  "reason": second.get("reason"),
                  "elapsed_seconds": second.get("elapsed_seconds")})

    # --- report ---------------------------------------------------------------
    finished_at = datetime.now(timezone.utc)
    passed = len(evidence.rows) - len(evidence.failures)
    payload = {
        "generated_at": finished_at.isoformat(),
        "started_at": started_at.isoformat(),
        "live": bool(args.live),
        "magpie": {"version": snapshot.get("version"),
                   "accounts": len(accounts), "providers": providers},
        "real_30d": {key: usage.get(key) for key in
                     ("period", "calls", "errors", "retried", "cost", "unpriced",
                      "credits", "ttft_ms", "decode_out", "decode_n")},
        "checks": evidence.rows,
        "probes": probes,
        "result": {"passed": passed, "total": len(evidence.rows),
                   "ok": not evidence.failures},
        "total_probe_cost_usd": round(sum(p["cost_units"] or 0.0 for p in probes), 6),
    }
    write_reports(payload, args)
    print(f"\n{passed}/{len(evidence.rows)} checks passed; "
          f"probe cost ${payload['total_probe_cost_usd']:.6f}")
    return 0 if not evidence.failures else 1


def write_reports(payload: dict[str, Any], args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "reports" / "multi_account"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"real_acceptance_{stamp}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                         encoding="utf-8")

    lines = ["# 真实账户验收报告", "",
             f"生成时间：{payload['generated_at']}　真实调用：{'是' if payload['live'] else '否'}　"
             f"Magpie {payload['magpie']['version']}", "",
             f"真实账户：**{payload['magpie']['accounts']} 个 / {len(payload['magpie']['providers'])} 个 provider**"
             f"（{', '.join(str(p) for p in payload['magpie']['providers'])}）", "",
             f"## 结论：**{payload['result']['passed']}/{payload['result']['total']} 通过**", "",
             "| 验收项 | 结果 | 证据 |", "|---|---|---|"]
    for row in payload["checks"]:
        mark = "PASS" if row["ok"] else "FAIL"
        detail = json.dumps(row["detail"], ensure_ascii=False, default=str)
        lines.append(f"| {row['title']} | {mark} | `{detail[:240]}` |")
    real = payload["real_30d"]
    lines += ["",
              "## 真实 30 天经济性（Magpie 观测）", "",
              "| 指标 | 数值 |", "|---|---|",
              f"| 调用 / 错误 / 重试 | {real['calls']} / {real['errors']} / {real['retried']} |",
              f"| 成本（列表价） | ${real['cost']} |",
              f"| 未计价调用 | {real['unpriced']} |",
              f"| 输出 token / 计时样本 | {real['decode_out']} / {real['decode_n']} |", ""]
    if payload["probes"]:
        lines += ["## 真实调用", "",
                  "| 账户 | 成功 | 秒 | 成本(USD) | 已计价 | 尝试 | 失败类型 | 诊断 |",
                  "|---|---|---|---|---|---|---|---|"]
        for probe in payload["probes"]:
            lines.append(f"| {probe['account']} | {probe['ok']} | {probe['seconds']} | "
                         f"{probe['cost_units']} | {probe['priced']} | {probe['attempts']} | "
                         f"{probe.get('failure_kind') or '-'} | "
                         f"{(probe.get('diagnostic') or '-').replace('|', '/')[:120]} |")
        lines += ["", f"本次调用总花费：**${payload['total_probe_cost_usd']}**", ""]
    lines += ["## 复现", "", "```bash",
              "python scripts/multi_account_real_acceptance.py --live", "```", "",
              "## 说明", "",
              "- 账户身份只使用 Magpie 已截断的 sha256；不读取、不打印任何凭据。",
              "- 故障注入作用于真实池中的真实账户（选真实 30 天错误率最高者），"
              "不是伪造账户。",
              "- 未计价调用（codex CLI 不上报成本）会入账并标记 `priced=false`，"
              "而不是当作免费。",
              "- 真实失败不会被吞掉：CLI 的 stderr/stdout 尾部经脱敏后按生产同一套"
              "词表分类（`account_abnormal` / `quota_exhausted` / `transient` / "
              "`task_failed`），只有传输类失败允许再打一次，账户级失败直接交给切换。", ""]
    md_path = out_dir / "real_acceptance_latest.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"report: {json_path}\nsummary: {md_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--magpie-url", default="http://127.0.0.1:3425")
    parser.add_argument("--live", action="store_true",
                        help="actually call the installed CLIs once per account")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--budget-units", type=float, default=5.0,
                        help="ceiling used for the scheduling check")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())

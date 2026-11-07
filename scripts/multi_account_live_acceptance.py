"""Acceptance against the real account pool, through a real host.

Starts ``CombinedTrustedHost`` on isolated ports and an isolated runtime directory,
reads the pool over the authenticated Task API, makes real low-cost model calls
through the local Magpie gateway, and checks that the production feedback, cooldown,
alert and policy paths react.

What each check proves is stated in its name. In particular:

* ``real_*`` used a real account or a real network call.
* ``injected_*`` fed a synthetic outcome into the production path, because a real
  account cannot be made to fail on demand. The reaction is real, the cause is not.
* The failover loop lives in this script. It calls the production scheduler for
  each decision, but it is not the coordinator running a task.

It proves nothing about billing, about a run lasting hours or days, or about
surviving sleep or a hard kill. Output carries provider names, never account refs.

    python scripts/multi_account_live_acceptance.py --evidence out.json
    python scripts/multi_account_live_acceptance.py --soak-minutes 1440 --soak-interval 300 \\
        --runtime-dir .platform_v1_runtime/soak --evidence .platform_v1_runtime/soak/evidence.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TASK_PORT = 18766
MODEL_PORT = 18765
ORIGIN = "http://127.0.0.1:4274"
COOLDOWN_SECONDS = 6
INTERVAL_SECONDS = 5
POLICY_ATTEMPTS = 3
MAX_FAILOVER_ATTEMPTS = 3
SOAK_INTERVAL_SECONDS = 60
# Low-cost models, cheapest first. Each maps to the Magpie provider that serves it.
CANDIDATES = (
    ("workbuddy-ai", "workbuddy-ai/hy4free"),
    ("workbuddy", "workbuddy/hy4free"),
    ("trae-cn", "trae-cn/Doubao-Seed-2.1-Turbo"),
)


class Report:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, name: str, passed: bool, **detail: Any) -> bool:
        self.checks.append({"name": name, "passed": bool(passed), **detail})
        print(f"[{'PASS' if passed else 'FAIL'}] {name} {json.dumps(detail, ensure_ascii=False)}")
        return bool(passed)


def configure_environment(runtime: Path) -> None:
    os.environ.update({
        "REVERSE_AGENT_MAGPIE": "1",
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED": "1",
        "REVERSE_AGENT_MULTI_ACCOUNT_STORE": str(runtime / "multi_account.json"),
        "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_LOG_PATH": str(runtime / "alerts.jsonl"),
        "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_INTERVAL_SECONDS": str(INTERVAL_SECONDS),
        "REVERSE_AGENT_MULTI_ACCOUNT_ABNORMAL_ACCOUNT_COOLDOWN_SECONDS": str(COOLDOWN_SECONDS),
        "REVERSE_AGENT_MULTI_ACCOUNT_FAILURE_BACKOFF_BASE_SECONDS": str(COOLDOWN_SECONDS),
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_ACCOUNT_SCORING": "1",
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_FEEDBACK_ROUTING": "1",
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLE_POLICY_EVOLUTION": "1",
        "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_MIN_NEW_ATTEMPTS": str(POLICY_ATTEMPTS),
    })


def get_accounts(capability: str) -> dict[str, Any]:
    request = Request(f"http://127.0.0.1:{TASK_PORT}/api/platform/accounts", headers={
        "X-Nerelan-Client-Capability": capability, "Origin": ORIGIN})
    with urlopen(request, timeout=20) as response:  # noqa: S310 - loopback constant
        return json.loads(response.read())


def real_call(model: str, auth: str) -> dict[str, Any]:
    """One tiny completion through Magpie; returns outcome without response text."""
    body = json.dumps({"model": model, "max_tokens": 16,
                       "messages": [{"role": "user", "content": "Reply with the single word: ok"}]}).encode()
    request = Request("http://127.0.0.1:3425/v1/chat/completions", data=body, method="POST",
                      headers={"Authorization": auth, "Content-Type": "application/json"})
    started = time.monotonic()
    try:
        with urlopen(request, timeout=90) as response:  # noqa: S310 - loopback constant
            payload = json.loads(response.read())
        usage = payload.get("usage") or {}
        return {"ok": bool(payload.get("choices")), "status": 200, "seconds": time.monotonic() - started,
                "total_tokens": usage.get("total_tokens")}
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "seconds": time.monotonic() - started}
    except (URLError, OSError, ValueError) as exc:
        return {"ok": False, "status": type(exc).__name__, "seconds": time.monotonic() - started}


def wait_until(predicate: Any, *, timeout: float) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(1)
    return predicate()


def hold_system_awake() -> None:
    """Per-process idle-sleep request on Windows; ends with the process."""
    if sys.platform == "win32":
        import ctypes
        es_continuous, es_system_required = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | es_system_required)


def soak(report: Report, capability: str, models: dict[str, str], minutes: float, auth: str,
         *, interval: float, progress: Path | None) -> None:
    """Bounded continuous run: real calls chosen by the production scheduler.

    Each round is appended to ``progress`` as it finishes, so a run that dies
    still leaves its evidence. A round that raises is counted, not fatal. A gap
    well over the interval means the process was paused, usually by host sleep.
    """
    from reverse_agent.model_access.magpie import fetch_magpie_snapshot
    from reverse_agent.platform_v1.multi_account.dispatch import (
        get_orchestrator,
        record_account_outcome,
        reroute_failed_account,
    )
    from reverse_agent.platform_v1.multi_account.status import MultiAccountStatusMonitor

    hold_system_awake()
    started = time.monotonic()
    served: dict[str, int] = {}
    latencies: list[float] = []
    rounds = failures = failovers = held = view_errors = stale_views = round_errors = 0
    tokens = 0
    longest_gap = 0.0
    last_round = time.time()

    def one_round() -> dict[str, Any]:
        nonlocal failures, failovers, held, tokens
        snapshot = fetch_magpie_snapshot()
        monitor = MultiAccountStatusMonitor(get_orchestrator().config)
        statuses = [s for s in monitor.diagnose(snapshot) if s.provider in models]
        names = {s.account_ref: s.provider for s in statuses}
        chosen = get_orchestrator().select(statuses, small_task=True, reset_task=True).get("account_ref")
        attempt = 0
        entry: dict[str, Any] = {"snapshot": snapshot.get("status"), "served": None, "attempts": 0}
        while chosen in names and attempt < MAX_FAILOVER_ATTEMPTS:
            attempt += 1
            provider = names[chosen]
            outcome = real_call(models[provider], auth)
            entry["attempts"] = attempt
            record_account_outcome(chosen, ok=outcome["ok"], wall_seconds=outcome["seconds"],
                                   outcome_id=f"soak-{rounds}-{attempt}",
                                   failure_kind=None if outcome["ok"] else "task_failed")
            if outcome["ok"]:
                served[provider] = served.get(provider, 0) + 1
                latencies.append(outcome["seconds"])
                tokens += outcome.get("total_tokens") or 0
                entry.update(served=provider, seconds=round(outcome["seconds"], 2))
                break
            failures += 1
            failovers += 1
            entry.setdefault("failed", []).append({"provider": provider, "status": outcome["status"]})
            chosen = reroute_failed_account(statuses, failed_ref=chosen, failure_kind="task_failed",
                                            attempt=attempt, small_task=True).get("next_account_ref")
        if entry["served"] is None:
            held += 1
        return entry

    while time.monotonic() - started < minutes * 60:
        rounds += 1
        now = time.time()
        gap = now - last_round
        last_round = now
        longest_gap = max(longest_gap, gap)
        try:
            entry = one_round()
        except Exception as exc:  # noqa: BLE001 - one bad round must not end a long run
            round_errors += 1
            entry = {"error": type(exc).__name__}
        try:
            view = get_accounts(capability)
            if time.time() - view["observed_at"] > INTERVAL_SECONDS * 4:
                stale_views += 1
            entry.update(dispatchable=view["summary"]["dispatchable_accounts"],
                         alerts=sorted(alert["code"] for alert in view["alerts"]["active"]),
                         monitoring=view["monitoring"])
        except (URLError, OSError, ValueError, KeyError, TypeError) as exc:
            view_errors += 1
            entry["view_error"] = type(exc).__name__
        if progress is not None:
            entry.update(round=rounds, at=round(now), gap_seconds=round(gap, 1), threads=threading.active_count())
            with progress.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        time.sleep(interval)
    completed = sum(served.values())
    latencies.sort()
    report.check("real_soak_every_round_served_or_held_without_crashing",
                 completed + held + round_errors == rounds and round_errors == 0
                 and view_errors == 0 and stale_views == 0,
                 minutes=minutes, interval_seconds=interval, rounds=rounds, served=served, failures=failures,
                 failovers=failovers, held=held, round_errors=round_errors, view_errors=view_errors,
                 stale_views=stale_views, total_tokens=tokens, longest_gap_seconds=round(longest_gap, 1),
                 p50_seconds=round(latencies[len(latencies) // 2], 2) if latencies else None,
                 max_seconds=round(latencies[-1], 2) if latencies else None)


def run(report: Report, runtime: Path, soak_minutes: float = 0, *,
        soak_interval: float = SOAK_INTERVAL_SECONDS, progress: Path | None = None) -> None:
    from reverse_agent.model_access.magpie import MAGPIE_AUTH, fetch_magpie_snapshot
    from reverse_agent.platform_v1.multi_account.dispatch import (
        account_quarantine_guard,
        get_orchestrator,
        record_account_outcome,
        reroute_failed_account,
        routing_feedback_snapshot,
    )
    from reverse_agent.platform_v1.multi_account.status import MultiAccountStatusMonitor
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost

    snapshot = fetch_magpie_snapshot()
    if not report.check("real_magpie_reachable", snapshot["status"] == "available",
                        accounts=len(snapshot["accounts"])):
        return

    host = CombinedTrustedHost(
        model_control_port=MODEL_PORT, task_api_port=TASK_PORT, allowed_origin=ORIGIN,
        task_db_path=str(runtime / "tasks.sqlite3"), vault=None,
    )
    host.start()
    try:
        held: dict[str, str] = {}
        # The documented in-process seam; the capability is never logged.
        host._local_client_session.deliver(lambda token: held.update(token=token))
        capability = held["token"]

        try:
            urlopen(Request(f"http://127.0.0.1:{TASK_PORT}/api/platform/accounts",  # noqa: S310
                            headers={"Origin": ORIGIN}), timeout=10)
            refused = False
        except HTTPError as exc:
            refused = exc.code == 401
        report.check("real_api_refuses_without_capability", refused)

        view = get_accounts(capability)
        providers = [row["provider"] for row in view["accounts"]]
        report.check("real_pool_lists_every_magpie_account",
                     len(view["accounts"]) == len(snapshot["accounts"]) and view["source"] == "magpie",
                     accounts=len(view["accounts"]), by_health=view["summary"]["by_health"],
                     dispatchable=view["summary"]["dispatchable_accounts"], providers=providers)
        report.check("real_monitor_thread_running", view["monitoring"] is True)
        report.check("real_no_secret_in_view", "raw" not in json.dumps(view["accounts"][0]))

        rows = {row["provider"]: row for row in view["accounts"]}
        usable = [(provider, model) for provider, model in CANDIDATES
                  if rows.get(provider, {}).get("dispatchable")]
        if not report.check("real_low_cost_candidates_available", len(usable) >= 2,
                            candidates=[provider for provider, _ in usable]):
            return

        primary_provider, primary_model = usable[0]
        primary_ref = rows[primary_provider]["account_ref"]
        result = real_call(primary_model, MAGPIE_AUTH)
        report.check("real_model_call_succeeds", result["ok"], provider=primary_provider, **result)
        record_account_outcome(primary_ref, ok=result["ok"], wall_seconds=result["seconds"], outcome_id="live-1",
                               failure_kind=None if result["ok"] else "task_failed")
        scored = wait_until(lambda: next((r for r in get_accounts(capability)["accounts"]
                                          if r["provider"] == primary_provider and r["score"]), None),
                            timeout=INTERVAL_SECONDS * 3)
        report.check("real_feedback_reaches_the_pool_view", bool(scored),
                     attempts=(scored or {}).get("score", {}).get("attempts"),
                     mean_wall_seconds=(scored or {}).get("score", {}).get("mean_wall_seconds"))

        record_account_outcome(primary_ref, ok=False, failure_kind="account_abnormal", outcome_id="live-2")
        guard = account_quarantine_guard(primary_ref)
        report.check("injected_fault_quarantines_the_account", guard.get("skip") is True,
                     reason=guard.get("reason"))
        isolated = wait_until(lambda: next((a for a in get_accounts(capability)["alerts"]["active"]
                                            if a["code"] == "account_quarantined"), None),
                              timeout=INTERVAL_SECONDS * 3)
        report.check("injected_fault_raises_an_alert_from_the_monitor_thread", bool(isolated))

        statuses = MultiAccountStatusMonitor(get_orchestrator().config).diagnose(fetch_magpie_snapshot())
        failed_ref, attempts, served = primary_ref, 0, None
        tried: list[dict[str, Any]] = []
        models = dict(usable)
        by_ref = {row["account_ref"]: row["provider"] for row in view["accounts"]}
        while attempts < MAX_FAILOVER_ATTEMPTS and served is None:
            attempts += 1
            decision = reroute_failed_account(
                [s for s in statuses if s.provider in models], failed_ref=failed_ref,
                failure_kind="account_abnormal", attempt=attempts)
            next_ref = decision.get("next_account_ref")
            provider = by_ref.get(next_ref)
            tried.append({"decision": decision.get("decision"), "provider": provider})
            if not provider:
                break
            outcome = real_call(models[provider], MAGPIE_AUTH)
            tried[-1].update(status=outcome["status"], seconds=round(outcome["seconds"], 2))
            record_account_outcome(next_ref, ok=outcome["ok"], wall_seconds=outcome["seconds"],
                                   outcome_id=f"live-failover-{attempts}",
                                   failure_kind=None if outcome["ok"] else "task_failed")
            if outcome["ok"]:
                served = provider
            failed_ref = next_ref
        report.check("real_failover_serves_on_another_account", served not in (None, primary_provider),
                     served=served, tried=tried)

        recovered = wait_until(lambda: not any(a["code"] == "account_quarantined"
                                               for a in get_accounts(capability)["alerts"]["active"]),
                               timeout=COOLDOWN_SECONDS + INTERVAL_SECONDS * 3)
        report.check("real_quarantine_expires_and_the_alert_resolves", bool(recovered))
        log = runtime / "alerts.jsonl"
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        transitions = [(e["event"], e["code"]) for e in events]
        report.check("real_alert_log_records_both_transitions",
                     ("raised", "account_quarantined") in transitions
                     and ("resolved", "account_quarantined") in transitions,
                     events=len(events), codes=sorted({code for _, code in transitions}))

        brain = get_orchestrator()
        before = brain.account_policy_view()
        for index in range(POLICY_ATTEMPTS * 2):
            record_account_outcome(primary_ref, ok=False, failure_kind="account_abnormal",
                                   wall_seconds=1.0, cost_units=1.0, outcome_id=f"policy-{index}")
        evolved = brain.account_policy_view()
        report.check("injected_outcomes_evolve_the_policy_within_bounds",
                     evolved["revision"] > before["revision"]
                     and evolved["effective"] != before["effective"],
                     revision=evolved["revision"], weights=evolved["effective"])
        snapshot_after = routing_feedback_snapshot() or {}
        report.check("evolved_policy_reaches_the_production_router_snapshot",
                     snapshot_after.get("evolution_revision") == evolved["revision"]
                     or snapshot_after.get("policy", {}).get("evolution_revision") == evolved["revision"],
                     keys=sorted(snapshot_after))
        rolled = brain.rollback_account_policy(0, expected_revision=evolved["revision"])
        after = brain.account_policy_view()
        report.check("policy_rollback_restores_the_baseline_as_a_new_version",
                     after["revision"] == evolved["revision"] + 1
                     and after["effective"]["reliability_weight"] == brain.config.reliability_weight
                     and after["effective"]["cost_weight"] == brain.config.cost_weight,
                     revision=after["revision"], rolled=sorted(rolled))
        if soak_minutes > 0:
            soak(report, capability, dict(usable), soak_minutes, MAGPIE_AUTH,
                 interval=soak_interval, progress=progress)
    finally:
        host.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, help="write the check results here as JSON")
    parser.add_argument("--soak-minutes", type=float, default=0,
                        help="after the checks, keep making real scheduled calls for this long")
    parser.add_argument("--soak-interval", type=float, default=SOAK_INTERVAL_SECONDS,
                        help="seconds between soak rounds; each round spends one real call")
    parser.add_argument("--runtime-dir", type=Path,
                        help="keep the host data, alert log and soak_progress.jsonl here")
    args = parser.parse_args()
    report = Report()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        with ExitStack() as stack:
            runtime = args.runtime_dir or Path(stack.enter_context(
                tempfile.TemporaryDirectory(prefix="nerelan-live-", ignore_cleanup_errors=True)))
            runtime.mkdir(parents=True, exist_ok=True)
            configure_environment(runtime)
            run(report, runtime, args.soak_minutes, soak_interval=args.soak_interval,
                progress=runtime / "soak_progress.jsonl" if args.runtime_dir else None)
    finally:
        passed = sum(1 for item in report.checks if item["passed"])
        print(f"{passed}/{len(report.checks)} checks passed", flush=True)
        if args.evidence:
            args.evidence.write_text(json.dumps(report.checks, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report.checks and passed == len(report.checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

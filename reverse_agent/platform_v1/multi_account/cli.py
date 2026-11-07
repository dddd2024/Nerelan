"""Operator CLI for the multi-account orchestration brain.

Why a CLI and not another endpoint: during an unattended run the questions that
actually get asked are local — "how much of the ceiling is gone", "is the run
about to conclude", "what did the policy change and can I undo it". Answering
them from the same ledger the loop writes avoids depending on the HTTP service
being up (which is often what broke).

Every command is read-only except ``rollback``. No command reads, prints or
touches a provider credential: account identity here is the truncated hash the
brain already stores.

Usage::

    python -m reverse_agent.platform_v1.multi_account.cli status
    python -m reverse_agent.platform_v1.multi_account.cli accounts --live
    python -m reverse_agent.platform_v1.multi_account.cli budget
    python -m reverse_agent.platform_v1.multi_account.cli policy
    python -m reverse_agent.platform_v1.multi_account.cli audit
    python -m reverse_agent.platform_v1.multi_account.cli alerts
    python -m reverse_agent.platform_v1.multi_account.cli rollback --version 2
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional, Sequence

_EXIT_OK = 0
_EXIT_CONFIG = 2
_EXIT_REFUSED = 3


def _build(store_path: Optional[str] = None):
    from . import MultiAccountConfig, MultiAccountOrchestrator
    from pathlib import Path

    config = MultiAccountConfig.from_env()
    return MultiAccountOrchestrator(
        config, store_path=Path(store_path) if store_path else None)


def _status(brain: Any) -> dict[str, Any]:
    return {
        "routing": brain.routing(),
        "budget": brain.budget_status(),
        "run": brain.run_verdict(),
        "policy": brain.policy_view(),
        "cooldowns": brain.cooldowns.active_streaks(),
        "accounts_tracked": len(brain.account_scores()),
        "alerts": {"pending": brain.alerts.pending_count(),
                   "recent": brain.alert_history()[-5:]},
        "config": {
            "cost_budget_enabled": brain.config.cost_budget_enabled,
            "reserve_inflight": brain.config.cost_budget_reserve_inflight,
            "max_run_duration_seconds": brain.config.max_run_duration_seconds,
            "max_idle_seconds": brain.config.max_idle_seconds,
            "watchdog_enabled": brain.config.watchdog_enabled,
            "alerts_enabled": brain.config.alerts_enabled,
            "policy_enabled": brain.config.policy_enabled,
        },
    }


def _accounts(brain: Any, *, live: bool) -> dict[str, Any]:
    if not live:
        return {
            "note": "pass --live to read the provider snapshot (read-only, no credentials)",
            "scores": brain.account_scores(),
        }
    from ...model_access.magpie import fetch_magpie_snapshot

    snapshot = fetch_magpie_snapshot()
    if not isinstance(snapshot, dict) or snapshot.get("status") != "available":
        return {"status": (snapshot or {}).get("status", "unavailable"),
                "reason": (snapshot or {}).get("reason")}
    payload = brain.observe(snapshot)
    return {"summary": payload["summary"], "accounts": payload["accounts"],
            "perception_error": payload.get("perception_error")}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m reverse_agent.platform_v1.multi_account.cli",
        description="Inspect (or roll back) the multi-account scheduling brain.")
    parser.add_argument("--store", default=None,
                        help="ledger path; defaults to REVERSE_AGENT_MULTI_ACCOUNT_STORE")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="routing, budget, run verdict, policy, alerts")
    accounts = sub.add_parser("accounts", help="per-account scores (or live perception)")
    accounts.add_argument("--live", action="store_true",
                          help="also read the provider snapshot (read-only)")
    sub.add_parser("budget", help="rolling-window cost ceiling")
    sub.add_parser("policy", help="effective weights, drift, version")
    sub.add_parser("audit", help="bounded policy audit trail")
    sub.add_parser("alerts", help="pending and recent alerts")
    sub.add_parser("scores", help="per-account reliability/cost/latency")
    rollback = sub.add_parser("rollback", help="restore an earlier policy version")
    rollback.add_argument("--version", type=int, default=0,
                          help="0 = configured baseline")
    rollback.add_argument("--reason", default="operator_rollback")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    command = args.command or "status"
    try:
        brain = _build(args.store)
    except Exception as exc:  # noqa: BLE001 - a bad deployment must say why, not traceback
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return _EXIT_CONFIG

    if command == "status":
        payload = _status(brain)
    elif command == "accounts":
        payload = _accounts(brain, live=args.live)
    elif command == "budget":
        payload = brain.budget_status()
    elif command == "policy":
        payload = brain.policy_view()
    elif command == "audit":
        payload = {"entries": brain.policy_audit()}
    elif command == "alerts":
        payload = {"pending": [alert.to_dict() for alert in brain.alerts.pending()],
                   "history": brain.alert_history()}
    elif command == "scores":
        payload = brain.account_scores()
    elif command == "rollback":
        payload = brain.rollback_policy(args.version, reason=args.reason)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return _EXIT_OK if payload.get("changed") or payload.get("reason") == "already_at_version" \
            else _EXIT_REFUSED
    else:  # pragma: no cover - argparse rejects unknown commands first
        return _EXIT_CONFIG
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return _EXIT_OK


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())

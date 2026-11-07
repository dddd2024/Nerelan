"""Operator entry for the account policy: read it, and roll it back.

``python -m reverse_agent.platform_v1.multi_account.cli policy``
``python -m reverse_agent.platform_v1.multi_account.cli rollback --target 3 --expected-revision 7``
``python -m reverse_agent.platform_v1.multi_account.cli alerts --limit 20``

Rollback is deliberately not an HTTP route: policy authority does not belong to
the browser. The feedback store serializes writers inside one process only, so
rollback refuses while a host answers on the task API and asks for it to stop.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque
from typing import Any, Optional, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

from . import MultiAccountConfig, MultiAccountOrchestrator

DEFAULT_TASK_API = "http://127.0.0.1:8766"


def _host_running(base_url: str) -> bool:
    request = Request(base_url.rstrip("/") + "/api/health", method="GET")
    try:
        with urlopen(request, timeout=2) as response:  # noqa: S310 - loopback constant or operator value
            return 200 <= response.getcode() < 300
    except (URLError, OSError, ValueError):
        return False


def _orchestrator(config: MultiAccountConfig) -> MultiAccountOrchestrator:
    return MultiAccountOrchestrator(config, store_path=config.break_even_store_path)


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _alerts(config: MultiAccountConfig, limit: int) -> list[Any]:
    try:
        with open(config.alert_log_path, encoding="utf-8") as handle:
            lines = deque(handle, maxlen=limit)
    except FileNotFoundError:
        return []
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("policy", help="show the effective weights and version history")
    alerts = commands.add_parser("alerts", help="show recent alert transitions")
    alerts.add_argument("--limit", type=int, default=50)
    rollback = commands.add_parser("rollback", help="create a new policy version from an earlier one")
    rollback.add_argument("--target", type=int, required=True, help="revision to restore; 0 is the Owner baseline")
    rollback.add_argument("--expected-revision", type=int, required=True)
    rollback.add_argument("--task-api", default=os.environ.get("REVERSE_AGENT_TASK_API", DEFAULT_TASK_API))
    args = parser.parse_args(argv)

    config = MultiAccountConfig.from_env()
    if args.command == "alerts":
        _print(_alerts(config, max(1, args.limit)))
        return 0
    if args.command == "policy":
        _print(_orchestrator(config).account_policy_view())
        return 0
    if _host_running(args.task_api):
        print("host_running: stop the host before rolling back the account policy", file=sys.stderr)
        return 2
    try:
        _print(_orchestrator(config).rollback_account_policy(
            args.target, expected_revision=args.expected_revision))
    except ValueError as exc:
        print(f"rollback_refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

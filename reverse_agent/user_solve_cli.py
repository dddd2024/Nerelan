from __future__ import annotations

import argparse
import json
from typing import Sequence

from .user_solve_controller import UserSolveController
from .user_solve_fixtures import FIXTURE_NAMES
from .user_solve_request import demo_request
from .orchestrator_api import available_actions, handle_orchestrator_request
from .orchestrator_console_schema import build_console_fixture_bundle
from .user_solve_workbench import UserSolveWorkbench


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixture-only user solve preview.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", choices=FIXTURE_NAMES)
    group.add_argument("--workbench-demo", choices=("route-plan", "capability", "workbench"))
    group.add_argument(
        "--manual-console-demo",
        choices=(
            "dashboard",
            "create-demo-task",
            "create-demo-job",
            "export-handoff",
            "import-result-preview",
            "available-actions",
            "console-fixture-bundle",
        ),
    )
    parser.add_argument("--developer", action="store_true", help="Include developer audit fields.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.manual_console_demo:
        payload = _manual_console_payload(args.manual_console_demo)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
        return 0
    if args.workbench_demo:
        workbench = UserSolveWorkbench()
        if args.workbench_demo == "route-plan":
            payload = workbench.route_plan_preview("missing-evidence")
        elif args.workbench_demo == "capability":
            payload = workbench.capability_preview()
        else:
            payload = workbench.render_all(developer=args.developer)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
        return 0
    envelope = UserSolveController().solve(demo_request(args.demo))
    payload = envelope.to_developer_dict() if args.developer else envelope.to_user_dict()
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


def _manual_console_payload(name: str) -> dict:
    if name == "dashboard":
        return handle_orchestrator_request("GET", "/api/manual/dashboard")["body"]
    if name == "create-demo-task":
        return handle_orchestrator_request("GET", "/api/manual/tasks")["body"]
    if name == "create-demo-job":
        return handle_orchestrator_request("GET", "/api/manual/jobs")["body"]
    if name == "export-handoff":
        return handle_orchestrator_request("GET", "/api/manual/handoff")["body"]
    if name == "import-result-preview":
        return handle_orchestrator_request("GET", "/api/manual/import-preview")["body"]
    if name == "available-actions":
        return {"actions": available_actions()}
    return build_console_fixture_bundle()


if __name__ == "__main__":
    raise SystemExit(main())

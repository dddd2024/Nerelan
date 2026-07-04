from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tool_capabilities import capability_snapshot, capability_from_profiles
from .tool_profiles import tool_profile_snapshot
from .user_solve_controller import UserSolveController
from .user_solve_fixtures import FIXTURE_NAMES, fixture_catalog, fixture_request
from .user_solve_route_plan import build_route_plan
from .user_solve_task_trace import build_workbench_task_trace
from .user_solve_ui_state import map_response_to_ui_state


@dataclass
class UserSolveWorkbench:
    controller: UserSolveController = field(default_factory=UserSolveController)

    def preview_fixture(self, name: str, *, developer: bool = False) -> dict[str, Any]:
        request = fixture_request(name)
        envelope = self.controller.solve(request)
        response = envelope.to_developer_dict() if developer else envelope.to_user_dict()
        capability = capability_from_profiles()
        missing = []
        fallback = response.get("fallback_summary") if isinstance(response.get("fallback_summary"), dict) else {}
        if fallback:
            missing = list(fallback.get("missing_evidence") or [])
        route_plan = build_route_plan(
            response,
            fixture_name=request.fixture_name,
            capability=capability,
            missing_evidence=missing,
        ).to_dict()
        trace = build_workbench_task_trace(
            fixture_name=request.fixture_name,
            response=response,
            route_plan=route_plan,
        )
        return {
            "schema_version": 1,
            "fixture_name": request.fixture_name,
            "fixture_only": True,
            "persistent_task_created": False,
            "external_tool_invocation": False,
            "response": response,
            "ui_state": map_response_to_ui_state(response),
            "capability": capability.to_dict(),
            "route_plan": route_plan,
            "task_trace": trace.to_developer_dict() if developer else trace.to_user_dict(),
        }

    def render_all(self, *, developer: bool = False) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "fixture_only": True,
            "workbench": "UserSolveWorkbench",
            "catalog": fixture_catalog(),
            "tool_profiles": tool_profile_snapshot(),
            "capability_snapshot": capability_snapshot(),
            "fixtures": [self.preview_fixture(name, developer=developer) for name in FIXTURE_NAMES],
        }

    def route_plan_preview(self, name: str) -> dict[str, Any]:
        return self.preview_fixture(name)["route_plan"]

    def capability_preview(self) -> dict[str, Any]:
        return capability_snapshot()


def build_workbench_demo_payloads(*, developer: bool = False) -> dict[str, Any]:
    return UserSolveWorkbench().render_all(developer=developer)

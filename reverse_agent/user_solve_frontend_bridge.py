from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve_controller import UserSolveController
from .user_solve_fixtures import FIXTURE_NAMES, fixture_catalog, fixture_request
from .user_solve_ui_state import map_response_to_ui_state


@dataclass
class UserSolveFrontendBridge:
    controller: UserSolveController = field(default_factory=UserSolveController)

    def render_fixture(self, name: str, *, developer: bool = False) -> dict[str, Any]:
        request = fixture_request(name)
        envelope = self.controller.solve(request)
        response = envelope.to_developer_dict() if developer else envelope.to_user_dict()
        return {
            "fixture_name": request.fixture_name,
            "response": response,
            "ui_state": map_response_to_ui_state(response),
            "developer_mode": developer,
        }

    def render_all(self, *, developer: bool = False) -> dict[str, Any]:
        fixtures = [self.render_fixture(name, developer=developer) for name in FIXTURE_NAMES]
        return {
            "schema_version": 1,
            "fixture_only": True,
            "bridge": "UserSolveFrontendBridge",
            "catalog": fixture_catalog(),
            "fixtures": fixtures,
        }


def build_frontend_demo_payloads(*, developer: bool = False) -> dict[str, Any]:
    return UserSolveFrontendBridge().render_all(developer=developer)

from __future__ import annotations

from pathlib import Path
from typing import Any

from .orchestrator_api import handle_orchestrator_request


CONSOLE_PANELS = (
    "Dashboard",
    "Decision",
    "Command-plan",
    "Jobs",
    "Tasks",
    "Handoff",
    "Import",
    "Gate",
    "Audit",
    "Settings",
)


def build_console_fixture_bundle(*, state_dir: str | Path = "project_state") -> dict[str, Any]:
    routes = {
        "dashboard": "/api/manual/dashboard",
        "decision": "/api/manual/decision",
        "command_plan": "/api/manual/command-plan",
        "jobs": "/api/manual/jobs",
        "tasks": "/api/manual/tasks",
        "handoff": "/api/manual/handoff",
        "import_preview": "/api/manual/import-preview",
        "gates": "/api/manual/gates",
        "audit": "/api/manual/audit",
        "actions": "/api/manual/actions",
    }
    fixtures = {
        key: handle_orchestrator_request("GET", path, state_dir=state_dir)["body"]
        for key, path in routes.items()
    }
    return {
        "schema_version": 1,
        "console": "manual_mode_console",
        "panels": list(CONSOLE_PANELS),
        "routes": routes,
        "fixtures": fixtures,
        "static_only": True,
        "network_calls": False,
        "build_step_required": False,
        "direct_project_state_mutation": False,
    }

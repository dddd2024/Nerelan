from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .user_solve_errors import error_payload
from .user_solve_task_lifecycle import build_demo_task_payload
from .user_solve_task_store import list_demo_tasks, read_demo_task, write_demo_task


def handle_task_request(
    method: str,
    path: str,
    body: Mapping[str, Any] | None = None,
    *,
    state_dir: str | Path = "project_state",
    decision_id: str = "",
    round_id: str = "",
    report_id: str = "",
) -> dict[str, Any]:
    route_method = str(method or "GET").upper()
    route_path = "/" + str(path or "").strip("/")
    payload = dict(body or {})
    if route_method == "GET" and route_path == "/api/manual/tasks":
        return _response(200, {"tasks": list_demo_tasks(state_dir)})
    if route_method == "GET" and route_path.startswith("/api/manual/tasks/"):
        task_id = route_path.removeprefix("/api/manual/tasks/")
        try:
            return _response(200, {"task": read_demo_task(state_dir, task_id)})
        except (OSError, ValueError):
            return _response(404, {"error": error_payload("fixture_not_found")})
    if route_method == "POST" and route_path == "/api/manual/tasks/demo":
        task_id = str(payload.get("task_id") or "demo_manual_mode_task")
        task = build_demo_task_payload(
            task_id=task_id,
            decision_id=decision_id,
            round_id=round_id,
            report_id=report_id,
            status=str(payload.get("status") or "DRAFT"),
        )
        try:
            write_info = write_demo_task(state_dir, task)
        except ValueError as exc:
            return _response(400, {"error": {"code": "invalid_demo_task", "public_message": str(exc)}})
        return _response(200, {"task": task, "write": write_info})
    return _response(404, {"error": error_payload("route_not_found")})


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "headers": {"content_type": "application/json"},
        "body": body,
        "production_service": False,
        "direct_project_state_mutation": False,
    }

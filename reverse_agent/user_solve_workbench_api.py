from __future__ import annotations

from typing import Any, Mapping

from .user_solve_api_schema import schema_snapshot
from .user_solve_errors import error_payload
from .user_solve_fixtures import fixture_catalog, normalize_fixture_name
from .user_solve_workbench import UserSolveWorkbench


def handle_workbench_request(
    method: str,
    path: str,
    body: Mapping[str, Any] | None = None,
    *,
    developer: bool = False,
) -> dict[str, Any]:
    route_method = str(method or "GET").upper()
    route_path = "/" + str(path or "").strip("/")
    payload = dict(body or {})
    workbench = UserSolveWorkbench()

    if route_method == "GET" and route_path in {"/api/workbench/fixtures", "/workbench/fixtures"}:
        return _response(200, {"catalog": fixture_catalog(), "workbench": workbench.render_all(developer=developer)})
    if route_method == "GET" and route_path in {"/api/workbench/capabilities", "/workbench/capabilities"}:
        return _response(200, workbench.capability_preview())
    if route_method == "GET" and route_path in {"/api/workbench/schema", "/workbench/schema"}:
        return _response(200, schema_snapshot())
    if route_method == "GET" and route_path.startswith("/api/workbench/route-plan/"):
        return _fixture_response(workbench, route_path.removeprefix("/api/workbench/route-plan/"), "route_plan")
    if route_method == "GET" and route_path.startswith("/api/workbench/trace/"):
        return _fixture_response(workbench, route_path.removeprefix("/api/workbench/trace/"), "task_trace")
    if route_method == "POST" and route_path in {"/api/workbench/preview", "/workbench/preview"}:
        fixture_name = str(payload.get("fixture_name") or payload.get("demo") or "candidate")
        return _fixture_response(workbench, fixture_name, "preview", developer=developer)
    if route_path.startswith("/api/workbench") or route_path.startswith("/workbench"):
        return _response(405 if route_method != "GET" else 404, {"error": error_payload("route_not_found")})
    return _response(404, {"error": error_payload("route_not_found")})


def _fixture_response(
    workbench: UserSolveWorkbench,
    fixture_name: str,
    section: str,
    *,
    developer: bool = False,
) -> dict[str, Any]:
    try:
        name = normalize_fixture_name(fixture_name)
        preview = workbench.preview_fixture(name, developer=developer)
    except ValueError:
        return _response(404, {"error": error_payload("fixture_not_found")})
    if section == "route_plan":
        return _response(200, {"route_plan": preview["route_plan"]})
    if section == "task_trace":
        return _response(200, {"task_trace": preview["task_trace"]})
    return _response(200, preview)


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_code": int(status_code),
        "headers": {"content_type": "application/json"},
        "body": body,
        "fixture_only": True,
        "production_service": False,
        "persistent_tasks": False,
        "external_tool_invocation": False,
    }

from __future__ import annotations

from typing import Any, Mapping

from .user_solve_errors import error_payload
from .user_solve_fixtures import fixture_catalog, normalize_fixture_name
from .user_solve_frontend_bridge import UserSolveFrontendBridge


def handle_local_fixture_request(
    method: str,
    path: str,
    body: Mapping[str, Any] | None = None,
    *,
    developer: bool = False,
) -> dict[str, Any]:
    route_method = str(method or "GET").upper()
    route_path = "/" + str(path or "").strip("/")
    payload = dict(body or {})
    bridge = UserSolveFrontendBridge()

    if route_method == "GET" and route_path in {"/fixtures", "/api/fixtures"}:
        return _response(200, {"catalog": fixture_catalog()})

    if route_method == "GET" and route_path.startswith("/fixtures/"):
        return _fixture_response(bridge, route_path.removeprefix("/fixtures/"), developer=developer)

    if route_method == "GET" and route_path.startswith("/api/fixtures/"):
        return _fixture_response(bridge, route_path.removeprefix("/api/fixtures/"), developer=developer)

    if route_method == "POST" and route_path in {"/solve", "/api/solve"}:
        fixture_name = str(payload.get("fixture_name") or payload.get("demo") or "candidate")
        return _fixture_response(bridge, fixture_name, developer=developer)

    if route_path in {"/fixtures", "/api/fixtures", "/solve", "/api/solve"}:
        return _response(405, {"error": error_payload("method_not_allowed")})
    return _response(404, {"error": error_payload("route_not_found")})


def _fixture_response(
    bridge: UserSolveFrontendBridge,
    fixture_name: str,
    *,
    developer: bool,
) -> dict[str, Any]:
    try:
        name = normalize_fixture_name(fixture_name)
        payload = bridge.render_fixture(name, developer=developer)
    except ValueError:
        return _response(404, {"error": error_payload("fixture_not_found")})
    return _response(200, payload)


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "status_code": int(status_code),
        "headers": {"content_type": "application/json"},
        "body": body,
        "fixture_only": True,
        "production_service": False,
    }

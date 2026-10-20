"""Real HTTP admission rejects local callers before any task side effect."""
import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from reverse_agent.platform_v1.local_client_session import LocalClientSession
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory

TOKEN = "a" * 64
ORIGIN = "http://127.0.0.1:4173"


@pytest.fixture
def authenticated_server(tmp_path, monkeypatch):
    clock = [10.0]
    values = iter((TOKEN, "c" * 64))
    session = LocalClientSession(ttl_seconds=2, clock=lambda: clock[0], token_factory=lambda: next(values))
    session.rotate()
    store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    router = ExecutorRouter()
    handler = _handler_factory(store, router, allowed_origin=ORIGIN, local_client_session=session)
    actions = []
    def forbidden(*args, **kwargs):
        actions.append("forbidden-dispatch")
        raise AssertionError("unauthenticated side effect")
    monkeypatch.setattr(store, "get_task", forbidden)
    monkeypatch.setattr(router, "dispatch_execute", forbidden)
    monkeypatch.setattr(handler.autonomy_service, "activate", forbidden)
    monkeypatch.setattr(handler.autonomy_service, "activate_policy", forbidden)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], session, clock, actions, store
    finally:
        session.revoke()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(port, method, path, *, capability=None, origin=None, duplicate=False, body=b"{invalid-json"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.putrequest(method, path)
        if origin is not None:
            connection.putheader("Origin", origin)
        if capability is not None:
            connection.putheader("X-Nerelan-Client-Capability", capability)
            if duplicate:
                connection.putheader("X-Nerelan-Client-Capability", capability)
        if method == "POST":
            connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body if method == "POST" else None)
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw) if raw else None, dict(response.getheaders())
    finally:
        connection.close()


@pytest.mark.parametrize("method,path", [
    ("POST", "/api/tasks/unknown/execute"), ("POST", "/api/tasks/unknown/publish"),
    ("POST", "/api/tasks"), ("POST", "/api/windows/activate"),
    ("POST", "/api/goals/unknown/launch"), ("POST", "/api/goals/unknown/rebind"), ("POST", "/api/inbox"),
    ("GET", "/api/tasks"), ("GET", "/api/platform/status"), ("GET", "/api/goals"),
    ("GET", "/api/windows/policy"),
])
def test_missing_capability_rejected_before_body_lookup_or_dispatch(authenticated_server, method, path):
    port, _, _, actions, store = authenticated_server
    before = store._conn.total_changes
    status, result, _ = request(port, method, path)
    assert status == 401
    assert result["code"] == "local_client_session_required"
    assert not actions and store._conn.total_changes == before


@pytest.mark.parametrize("kind", ["wrong", "expired", "stale", "duplicate", "non-ascii", "oversized", "query-only"])
def test_invalid_client_identity_rejected_fail_closed(authenticated_server, kind):
    port, session, clock, actions, _ = authenticated_server
    value = TOKEN
    path = "/api/tasks/unknown/execute"
    if kind == "wrong": value = "b" * 64
    if kind == "expired": clock[0] = 12.0
    if kind == "stale": session.rotate()
    if kind == "non-ascii": value = "é" * 64
    if kind == "oversized": value = "a" * 1024
    if kind == "query-only": value = None; path += "?capability=" + TOKEN
    status, result, _ = request(port, "POST", path, capability=value, duplicate=kind == "duplicate")
    assert status == 401 and result["code"] == "local_client_session_required"
    assert not actions


def test_authenticated_read_semantics_and_origin_are_independent(authenticated_server):
    port, _, _, _, _ = authenticated_server
    status, data, headers = request(port, "GET", "/api/tasks", capability=TOKEN, origin=ORIGIN)
    assert status == 200 and data["tasks"] == []
    assert headers["Access-Control-Allow-Origin"] == ORIGIN
    # A trusted native in-process bootstrap may make a no-Origin request.
    assert request(port, "GET", "/api/tasks", capability=TOKEN)[0] == 200
    assert request(port, "GET", "/api/tasks", capability=TOKEN, origin="http://evil.example")[0] == 403
    assert request(port, "OPTIONS", "/api/tasks", origin="http://evil.example")[0] == 403
    assert request(port, "OPTIONS", "/api/tasks", origin=ORIGIN)[0] == 204


def test_public_health_is_only_explicit_readiness_boolean(authenticated_server):
    port, _, _, actions, store = authenticated_server
    before = store._conn.total_changes
    status, data, _ = request(port, "GET", "/api/health")
    assert status == 200 and data == {"ready": True}
    assert not actions and store._conn.total_changes == before


def test_unconfigured_handler_has_no_unauthenticated_compatibility_mode(tmp_path):
    handler = _handler_factory(TaskStore(db_path=str(tmp_path / "tasks.sqlite3")), ExecutorRouter(), allowed_origin=ORIGIN)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert request(server.server_address[1], "GET", "/api/tasks", capability=TOKEN)[0] == 401
        assert request(server.server_address[1], "GET", "/api/health")[1] == {"ready": True}
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


@pytest.mark.parametrize("assertions", [
    {},  # An arbitrary first Goal is not a human selection.
    {"selected_goal_id": "first-goal"},
    {"selected_goal_id": "other-goal"},
    {"selected_goal_id": "first-goal", "expected_revision": 2},
    {"executor_kind": "codex"},
    {"executor_kind": "claude_code", "binding_ref": "other-account"},
    {"human_confirmed": True, "confirmation_mode": "OWNER"},
    {"client_nonce": TOKEN, "receipt": {"approved": True}},
    {"policy_revision": 0, "policy_digest": "stale"},
    {"window_id": "other-window", "receipt_window_id": "first-window"},
    {"confirmation_mode": "DELEGATED_CONTROLLER"},
])
def test_authenticated_client_assertions_cannot_activate_owner_window(authenticated_server, assertions):
    from datetime import datetime, timedelta, timezone
    port, _, _, actions, store = authenticated_server
    now = datetime.now(timezone.utc)
    payload = {
        "policy_id": "untrusted-owner-selection", "policy_revision": 1,
        "owner_identity": "human-owner", "confirmation": "ACTIVATE",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 1, "max_retries": 0,
        "selected_goal_id": "first-goal", "expected_revision": 1,
        "executor_kind": "deterministic_fixture", "binding_ref": "fixture",
        **assertions,
    }
    before = store._conn.total_changes
    # Identical replay and a second window must both fail without reservations.
    for candidate in (payload, payload, {**payload, "policy_id": "second-window"}):
        status, result, _ = request(port, "POST", "/api/windows/activate",
                                    capability=TOKEN, origin=ORIGIN,
                                    body=json.dumps(candidate).encode())
        assert status == 409
        assert result == {"error": "owner_selection_confirmation_unavailable"}
    assert not actions  # Neither activation path nor model dispatch was reached.
    assert store._conn.total_changes == before

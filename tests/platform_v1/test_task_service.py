"""HTTP Task API tests: loopback-only, Origin fail-closed, bounded body, no secrets."""

import http.client
import json
import os
import tempfile
import threading

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import (
    TaskService,
    _handler_factory,
    validate_bind_host,
)


@pytest.fixture()
def task_server(tmp_path):
    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    handler_cls = _handler_factory(store, router, allowed_origin="http://localhost:5173")
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:%d" % port, server
    server.shutdown()
    server.server_close()


def _req(base_url: str, method: str, path: str, body=None, origin=None):
    host, port = base_url.replace("http://", "").split(":", 1)
    conn = http.client.HTTPConnection(host, int(port), timeout=10)
    headers = {
        "Accept": "application/json",
        "Origin": origin or "http://localhost:5173",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, json.loads(data.decode()) if data else None


def test_create_and_read_task(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"title": "t1", "executor_kind": "deterministic_fixture"})
    assert status == 201
    assert body["status"] == "QUEUED"
    assert body["executor_kind"] == "deterministic_fixture"
    assert body["frontend_task"]["executor"] == "fixture/provider-free"
    tid = body["id"]

    status, got = _req(base, "GET", f"/api/tasks/{tid}")
    assert status == 200
    assert got["id"] == tid
    assert got["events"][0]["type"] == "DISCOVERED"


def test_task_api_round_trips_explicit_binding_ref(task_server) -> None:
    base, _store = task_server
    status, created = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "bound task",
            "executor_kind": "opencode",
            "binding_ref": "coding-fast",
            "model_profile_ref": "legacy-profile",
        },
    )

    assert status == 201
    assert created["binding_ref"] == "coding-fast"
    assert created["model_profile_ref"] == "legacy-profile"
    status, fetched = _req(base, "GET", f"/api/tasks/{created['id']}")
    assert status == 200
    assert fetched["binding_ref"] == "coding-fast"


def test_task_api_keeps_legacy_empty_binding_compatible(task_server) -> None:
    base, _store = task_server
    status, created = _req(
        base,
        "POST",
        "/api/tasks",
        {
            "title": "legacy opencode",
            "executor_kind": "opencode",
            "model_profile_ref": "provider/model",
        },
    )

    assert status == 201
    assert created["binding_ref"] == ""
    assert created["model_profile_ref"] == "provider/model"


def test_list_tasks_and_events(task_server) -> None:
    base, _ = task_server
    _, created = _req(base, "POST", "/api/tasks", {"title": "t", "executor_kind": "deterministic_fixture"})
    tid = created["id"]
    status, listed = _req(base, "GET", "/api/tasks")
    assert status == 200
    assert any(t["id"] == tid for t in listed["tasks"])

    status, events = _req(base, "GET", f"/api/tasks/{tid}/events")
    assert status == 200
    assert events["task_id"] == tid
    assert events["events"][0]["type"] == "DISCOVERED"


def test_execute_endpoint_runs_fixture_and_persists(task_server) -> None:
    base, _ = task_server
    _, created = _req(base, "POST", "/api/tasks", {"title": "exec", "executor_kind": "deterministic_fixture"})
    tid = created["id"]
    status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
    assert status == 200
    assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert executed["validation_exit_code"] == 0
    assert executed["validation_command_id"] == "git_diff_check"
    assert executed["changed_files"]
    assert any(e["category"] == "Validation" for e in executed["evidence"])


def test_idempotency_key_across_http_creates_once(task_server) -> None:
    base, _ = task_server
    payload = {"title": "id", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-1"}
    _, first = _req(base, "POST", "/api/tasks", payload)
    _, second = _req(base, "POST", "/api/tasks", payload)
    assert first["id"] == second["id"]
    _, listed = _req(base, "GET", "/api/tasks")
    assert sum(1 for t in listed["tasks"] if t["id"] == first["id"]) == 1


def test_idempotency_conflict_across_http(task_server) -> None:
    base, _ = task_server
    payload = {"title": "idem", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-conflict"}
    _req(base, "POST", "/api/tasks", payload)
    status, body = _req(base, "POST", "/api/tasks", {"title": "DIFFERENT", "executor_kind": "deterministic_fixture", "idempotency_key": "http-k-conflict"})
    assert status == 409
    assert "idempotency" in body["error"].lower()


def test_origin_fail_closed(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "GET", "/api/tasks", origin="https://evil.example")
    assert status == 403
    assert body == {"error": "forbidden"}


def test_missing_title_rejected(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"executor_kind": "deterministic_fixture"})
    assert status == 409
    assert "title_required" in body["error"]


def test_unsupported_executor_kind_rejected(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "POST", "/api/tasks", {"title": "t", "executor_kind": "codex"})
    assert status == 409
    assert "unsupported_executor_kind" in body["error"]


def test_unknown_task_returns_404(task_server) -> None:
    base, _ = task_server
    status, _ = _req(base, "GET", "/api/tasks/task-nonexistent")
    assert status == 404


def test_validate_bind_host_loopback_only() -> None:
    assert validate_bind_host("127.0.0.1") == "127.0.0.1"
    assert validate_bind_host("localhost") == "localhost"
    assert validate_bind_host("::1") == "::1"
    with pytest.raises(ValueError):
        validate_bind_host("0.0.0.0")
    with pytest.raises(ValueError):
        validate_bind_host("192.168.1.1")


def test_task_service_wrapper_starts_and_serves(task_server) -> None:
    base, _ = task_server
    status, body = _req(base, "GET", "/api/tasks")
    assert status == 200
    assert "tasks" in body


def test_router_injection_http_execute(task_server) -> None:
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    base, _ = task_server

    dispatched_kinds: list[str] = []

    class _TracingRouter(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            dispatched_kinds.append(kwargs.get("executor_kind", ""))
            return super().dispatch_execute(**kwargs)

    store = TaskStore(":memory:")
    tracing_router = _TracingRouter()
    from http.server import ThreadingHTTPServer

    handler_cls = _handler_factory(store, tracing_router, allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        trace_base = "http://127.0.0.1:%d" % port
        _, created = _req(trace_base, "POST", "/api/tasks", {"title": "inj", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        before = len(dispatched_kinds)
        status, executed = _req(trace_base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert len(dispatched_kinds) > before
        assert dispatched_kinds[-1] == "deterministic_fixture"
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------------------
# Timeline regression (v4-F1): executor runs while state == RUNNING, not VALIDATING
# ---------------------------------------------------------------------------

def test_task_service_executor_runs_while_state_is_running_not_validating(tmp_path) -> None:
    from reverse_agent.platform_v1.task_runtime import (
        ExecutorRuntimeError,
        ExecutorResult,
    )

    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)

    class _TimelineRouter(ExecutorRouter):
        def __init__(self):
            super().__init__()
            self.states_at_dispatch: list[str] = []
            self.tasks_at_dispatch: list[str] = []

        def dispatch_execute(self, *, task_id: str, store, **kwargs):
            self.states_at_dispatch.append(store.get_task(task_id).status)
            self.tasks_at_dispatch.append(task_id)
            return super().dispatch_execute(
                task_id=task_id,
                store=store,
                executor_kind=kwargs.get("executor_kind", "deterministic_fixture"),
                workspace_root=kwargs.get("workspace_root", ""),
            )

    router = _TimelineRouter()
    handler_cls = _handler_factory(store, router, allowed_origin="http://localhost:5173")
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(base, "POST", "/api/tasks", {"title": "timeline", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert router.states_at_dispatch, "executor must be dispatched"
        for s in router.states_at_dispatch:
            assert s == "RUNNING_FIXTURE", s
            assert s != "VALIDATING", s
            assert s != "READY_FOR_REVIEW_FIXTURE", s
    finally:
        server.shutdown()
        server.server_close()


def test_task_service_validator_runs_after_executor(tmp_path) -> None:
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()

    class _StateObserver(ExecutorRouter):
        def __init__(self):
            super().__init__()
            self.states: list[str] = []

        def dispatch_execute(self, *, task_id: str, store, **kwargs):
            before = store.get_task(task_id).status
            result = super().dispatch_execute(
                task_id=task_id,
                store=store,
                executor_kind=kwargs.get("executor_kind", "deterministic_fixture"),
                workspace_root=kwargs.get("workspace_root", ""),
            )
            after = store.get_task(task_id).status
            self.states.append((before, after))
            return result

    obs = _StateObserver()
    handler_cls = _handler_factory(store, obs, allowed_origin="http://localhost:5173")
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = "http://127.0.0.1:%d" % port
        _, created = _req(base, "POST", "/api/tasks", {"title": "timeline2", "executor_kind": "deterministic_fixture"})
        tid = created["id"]
        status, executed = _req(base, "POST", f"/api/tasks/{tid}/execute")
        assert status == 200
        assert executed["status"] == "READY_FOR_REVIEW_FIXTURE"
        assert obs.states, "executor must run"
        for before, after in obs.states:
            assert before == "RUNNING_FIXTURE"
            assert after == "RUNNING_FIXTURE"
        task = store.get_task(tid)
        assert task.validation_exit_code == 0
        assert task.validation_command_id == "git_diff_check"
    finally:
        server.shutdown()
        server.server_close()


def test_frontend_task_test_status_uses_validation_exit_code() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    ok = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "READY_FOR_REVIEW",
        "executor_kind": "opencode", "validation_exit_code": 0,
        "failure_classification": "",
    })
    assert ok["testStatus"] == "PASS"

    fail = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "FAILED",
        "executor_kind": "opencode", "validation_exit_code": 1,
        "failure_classification": "",
    })
    assert fail["testStatus"] == "FAIL"


def test_frontend_task_test_status_is_running_while_validating() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    val = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "VALIDATING",
        "executor_kind": "opencode",
    })
    assert val["testStatus"] == "RUNNING"

    running = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "RUNNING",
        "executor_kind": "opencode",
    })
    assert running["testStatus"] == "PENDING"


def test_ready_for_human_next_action_is_executor_neutral() -> None:
    from reverse_agent.platform_v1.task_service import _map_task_to_frontend

    ok = _map_task_to_frontend({
        "id": "t", "title": "t", "status": "READY_FOR_REVIEW",
        "executor_kind": "opencode", "validation_exit_code": 0,
        "failure_classification": "",
    })
    assert ok["state"] == "READY_FOR_HUMAN"
    assert ok["testStatus"] == "PASS"
    assert "fixture" not in ok["nextAction"].lower()

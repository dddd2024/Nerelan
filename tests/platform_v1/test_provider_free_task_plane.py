"""End-to-end provider-free task plane tests.

These tests exercise the full chain without Codex, OpenHands, or any model API:
TaskStore -> ExecutorRouter -> DeterministicFixtureExecutor -> validation ->
evidence -> persistence -> TaskService HTTP round-trip.
"""

import json
import os
import socket
import tempfile
import threading

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _full_chain(tmp_path) -> dict:
    workspace_root = str(tmp_path / "workspace")
    os.makedirs(workspace_root, exist_ok=True)
    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()

    task = store.create_task(
        title="provider-free task plane",
        repository="dddd2024/reverse-agent",
        executor_kind="deterministic_fixture",
        idempotency_key="pf-test-1",
    )
    assert task.status == "QUEUED"
    assert task.id.startswith("task-")

    worktree_root = os.path.join(workspace_root, task.id)
    os.makedirs(worktree_root, exist_ok=True)
    events_received: list[dict] = []

    def cb(task_id: str, event: dict) -> None:
        events_received.append(event)

    result = router.dispatch_execute(
        task_id=task.id,
        store=store,
        executor_kind="deterministic_fixture",
        workspace_root=worktree_root,
        event_callback=cb,
    )
    assert result.success
    assert result.validation_exit_code == 0
    assert result.validation_command_id == "git_diff_check"
    assert result.changed_files
    assert result.validation_output_digest

    store.set_changed_files(task.id, result.changed_files)
    store.add_evidence(
        task.id,
        category="Validation",
        label=result.validation_command_id,
        value="0",
        status="pass",
        detail="fixture validation passed",
        raw_json_digest=result.validation_output_digest,
    )
    store.add_evidence(
        task.id,
        category="Executor",
        label="executor_kind",
        value="deterministic_fixture",
        status="pass",
        detail="fixture/provider-free executor",
    )

    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING_FIXTURE")
    store.transition_to(task.id, "VALIDATING")
    store.transition_to(task.id, "READY_FOR_REVIEW_FIXTURE")
    store._conn.close()

    persisted_store = TaskStore(db_path=db_path)
    try:
        persisted = persisted_store.get_task(task.id)
        assert persisted.status == "READY_FOR_REVIEW_FIXTURE"
        assert len(persisted.changed_files) == len(result.changed_files)
        assert len(persisted.evidence_refs) >= 2
    finally:
        persisted_store._conn.close()

    from http.server import ThreadingHTTPServer

    bind_port = _find_free_port()
    service_store = TaskStore(db_path=db_path)
    server = ThreadingHTTPServer(
        ("127.0.0.1", bind_port),
        _handler_factory(
            service_store,
            router,
            allowed_origin="http://localhost:5173",
        ),
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def do_request(method, path, body=None):
        import urllib.request as _urllib
        url = "http://127.0.0.1:%d%s" % (port, path)
        headers = {"Accept": "application/json", "Origin": "http://localhost:5173"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        req = _urllib.Request(url, data=data, headers=headers, method=method)
        with _urllib.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode()) if raw else None

    s, created = do_request("POST", "/api/tasks", {
        "title": "http fixture task",
        "executor_kind": "deterministic_fixture",
        "idempotency_key": "pf-http-1",
    })
    assert s == 201
    assert created["frontend_task"]["executor"] == "fixture/provider-free"
    http_tid = created["id"]

    s, events = do_request("GET", f"/api/tasks/{http_tid}/events")
    assert s == 200
    assert events["events"][0]["type"] == "DISCOVERED"

    server.shutdown()
    server.server_close()
    service_store._conn.close()

    return {
        "task_id": task.id,
        "http_task_id": http_tid,
        "model_calls": 0,
        "codex_calls": 0,
        "openhands_calls": 0,
        "fixture_success": result.success,
        "validation_exit_code": result.validation_exit_code,
        "changed_file_count": len(result.changed_files),
        "evidence_count": len(persisted.evidence_refs),
        "event_count": len(events_received),
        "db_path": db_path,
    }


def test_provider_free_full_chain(tmp_path) -> None:
    result = _full_chain(tmp_path)
    assert result["model_calls"] == 0
    assert result["codex_calls"] == 0
    assert result["openhands_calls"] == 0
    assert result["fixture_success"] is True
    assert result["validation_exit_code"] == 0
    assert result["changed_file_count"] >= 1
    assert result["evidence_count"] >= 2
    assert os.path.exists(result["db_path"])


def test_provider_free_chain_rejects_external_origin(tmp_path) -> None:
    db_path = str(tmp_path / "t.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(
        ("127.0.0.1", _find_free_port()),
        _handler_factory(store, router, allowed_origin="http://localhost:5173"),
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    import urllib.request as _urllib
    req = _urllib.Request(
        "http://127.0.0.1:%d/api/tasks" % port,
        headers={"Accept": "application/json", "Origin": "https://evil.example"},
        method="GET",
    )
    try:
        with _urllib.urlopen(req, timeout=10) as resp:
            assert False, "expected 403"
    except _urllib.HTTPError as exc:
        assert exc.code == 403
    finally:
        server.shutdown()
        server.server_close()
        store._conn.close()

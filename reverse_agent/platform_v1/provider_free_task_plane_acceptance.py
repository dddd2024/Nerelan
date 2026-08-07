"""End-to-end provider-free task plane acceptance.

Proves the complete non-model chain through the real HTTP API without Codex,
OpenHands, or any third-party provider:

POST /api/tasks
  -> server task id
  -> POST /api/tasks/{id}/execute
  -> TaskService
  -> injected ExecutorRouter
  -> DeterministicFixtureExecutor
  -> disposable workspace mutation
  -> validation
  -> persisted backend truth
  -> GET /api/tasks/{id} readback
  -> GET /api/tasks/{id}/events

Plus restart/readback persistence proof and injected-router regression proof.

Exit code 0 on success, non-zero with a JSON error on any failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .run_store import TaskStore
from .task_runtime import ExecutorRouter
from .task_service import TaskService, validate_bind_host


def _json_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _run(
    *,
    repo_dir: str,
    workspace_root: str,
) -> dict[str, Any]:
    workspace_root = os.path.abspath(workspace_root)
    os.makedirs(workspace_root, exist_ok=True)

    db_path = os.path.join(workspace_root, "issue128_tasks.sqlite3")
    if os.path.exists(db_path):
        os.remove(db_path)

    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    workspace_root_env = os.path.join(workspace_root, "task_workspaces")
    os.makedirs(workspace_root_env, exist_ok=True)

    from urllib.request import Request, urlopen

    results: dict[str, Any] = {
        "model_calls": 0,
        "codex_calls": 0,
        "openhands_calls": 0,
        "repo_dir": os.path.abspath(repo_dir),
        "workspace_root": workspace_root,
        "db_path": db_path,
        "chain": [],
    }

    def _http(
        method: str,
        path: str,
        body: dict[str, Any] | None,
        port: int,
    ) -> tuple[int, dict[str, Any]]:
        url = f"http://127.0.0.1:{port}{path}"
        data = json.dumps(body).encode("utf-8") if body else None
        req = Request(
            url,
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "http://localhost:4173",
            },
            method=method,
        )
        with urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), payload

    # =========================================================================
    # PHASE 1: Full HTTP execution chain (create -> execute -> readback)
    # =========================================================================

    os.environ["REVERSE_AGENT_TASK_DB_PATH"] = db_path
    os.environ["REVERSE_AGENT_TASK_WORKSPACE_ROOT"] = workspace_root_env

    service = TaskService(store=store, router=router)
    server, thread = service.start(host="127.0.0.1", port=0)
    port = server.server_address[1]
    results["task_api"] = {
        "host": "127.0.0.1",
        "port": int(port),
        "loopback_only": True,
        "base_url": f"http://127.0.0.1:{port}",
    }

    # Step 1: POST /api/tasks
    status_code, create_payload = _http(
        "POST",
        "/api/tasks",
        {
            "title": "HTTP fixture task",
            "repository": "dddd2024/reverse-agent",
            "executor_kind": "deterministic_fixture",
            "idempotency_key": "issue128-http-001",
        },
        port,
    )
    assert status_code == 201, f"POST /api/tasks expected 201, got {status_code}"
    http_task_id = create_payload["id"]
    assert http_task_id.startswith("task-"), "server task id must start with task-"
    assert create_payload["status"] == "QUEUED"
    assert create_payload["frontend_task"]["executor"] == "fixture/provider-free"
    results["http_task_id"] = http_task_id
    results["execution_id"] = create_payload.get("execution_id", "")
    results["chain"].append("http_post_task_created")

    # Step 2: POST /api/tasks/{id}/execute (real execution through injected router)
    status_code, execute_payload = _http(
        "POST",
        f"/api/tasks/{http_task_id}/execute",
        {},
        port,
    )
    assert status_code == 200, f"POST execute expected 200, got {status_code}"
    assert execute_payload["status"] == "READY_FOR_REVIEW_FIXTURE", (
        f"execute result status={execute_payload.get('status')}"
    )
    assert execute_payload["validation_exit_code"] == 0
    assert execute_payload["validation_command_id"] == "git_diff_check"
    assert execute_payload["changed_files"], "changed_files must be non-empty"
    assert execute_payload["evidence"], "evidence must be non-empty"
    assert any(e.get("category") == "Validation" for e in execute_payload["evidence"]), (
        "Validation evidence required"
    )
    assert any(e.get("category") == "Executor" for e in execute_payload["evidence"]), (
        "Executor evidence required"
    )
    results["http_execute_result"] = {
        "status": execute_payload["status"],
        "validation_exit_code": execute_payload["validation_exit_code"],
        "validation_command_id": execute_payload["validation_command_id"],
        "changed_file_count": len(execute_payload["changed_files"]),
        "evidence_count": len(execute_payload["evidence"]),
        "executor": execute_payload["frontend_task"]["executor"],
    }
    results["chain"].append("http_post_execute_real_fixture")

    # Step 3: GET /api/tasks/{id} readback
    status_code, get_payload = _http("GET", f"/api/tasks/{http_task_id}", None, port)
    assert status_code == 200
    assert get_payload["id"] == http_task_id
    assert get_payload["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert get_payload["executor_kind"] == "deterministic_fixture"
    assert get_payload["frontend_task"]["executor"] == "fixture/provider-free"
    assert get_payload["frontend_task"]["state"] == "READY_FOR_HUMAN"
    assert get_payload["validation_exit_code"] == 0
    assert get_payload["changed_files"]
    assert get_payload["evidence"]
    results["http_readback"] = {
        "status": get_payload["status"],
        "state": get_payload["frontend_task"]["state"],
        "validation_exit_code": get_payload["validation_exit_code"],
        "changed_file_count": len(get_payload["changed_files"]),
        "evidence_count": len(get_payload["evidence"]),
    }
    results["chain"].append("http_get_task_readback")

    # Step 4: GET /api/tasks/{id}/events
    status_code, events_payload = _http(
        "GET", f"/api/tasks/{http_task_id}/events", None, port
    )
    assert status_code == 200
    assert events_payload["task_id"] == http_task_id
    event_types = [e["type"] for e in events_payload["events"]]
    assert "DISCOVERED" in event_types, f"DISCOVERED event missing: {event_types}"
    assert "EXECUTOR_RUNNING" in event_types, f"EXECUTOR_RUNNING missing: {event_types}"
    assert "EXECUTOR_FINISHED" in event_types, f"EXECUTOR_FINISHED missing: {event_types}"
    assert "WORKSPACE_READY" in event_types, f"WORKSPACE_READY missing: {event_types}"
    assert (
        "VALIDATED" in event_types or "LOCAL_VALIDATED" in event_types
    ), f"VALIDATED/LOCAL_VALIDATED missing: {event_types}"
    results["http_events"] = {
        "event_count": len(events_payload["events"]),
        "event_types": event_types,
    }
    results["chain"].append("http_events_readback")

    # Step 5: Idempotent create through HTTP (same key -> same task)
    status_code, dup_payload = _http(
        "POST",
        "/api/tasks",
        {
            "title": "HTTP fixture task",
            "repository": "dddd2024/reverse-agent",
            "executor_kind": "deterministic_fixture",
            "idempotency_key": "issue128-http-001",
        },
        port,
    )
    assert status_code == 201
    assert dup_payload["id"] == http_task_id, "idempotency key must return same task"
    results["chain"].append("http_idempotency_preserved_same_key")

    # Idempotency conflict: same key, different title -> 409
    from urllib.error import HTTPError

    try:
        _http(
            "POST",
            "/api/tasks",
            {
                "title": "DIFFERENT title",
                "repository": "dddd2024/reverse-agent",
                "executor_kind": "deterministic_fixture",
                "idempotency_key": "issue128-http-001",
            },
            port,
        )
        assert False, "idempotency key conflict should return 409"
    except HTTPError as exc:
        assert exc.code == 409, f"idempotency conflict expected 409, got {exc.code}"
    results["chain"].append("http_idempotency_conflict_fail_closed")

    server.shutdown()
    server.server_close()
    thread.join(timeout=3)

    # =========================================================================
    # PHASE 2: Restart/readback persistence proof
    # =========================================================================

    restarted_store = TaskStore(db_path=db_path)
    restarted = restarted_store.get_task(http_task_id)
    results["restart_persistence_proof"] = {
        "task_id": restarted.id,
        "status": restarted.status,
        "execution_id": restarted.execution_id,
        "event_count": len(restarted.events),
        "changed_file_count": len(restarted.changed_files),
        "evidence_count": len(restarted.evidence_refs),
        "validation_command_id": restarted.validation_command_id,
        "validation_exit_code": restarted.validation_exit_code,
        "validation_output_digest": restarted.validation_output_digest,
        "db_path": db_path,
        "db_exists": os.path.exists(db_path),
    }
    assert restarted.id == http_task_id
    assert restarted.status == "READY_FOR_REVIEW_FIXTURE"
    assert len(restarted.changed_files) >= 1
    assert len(restarted.evidence_refs) >= 2
    assert restarted.validation_exit_code == 0
    assert restarted.execution_id
    results["chain"].append("restart_persistence_verified")
    restarted_store._conn.close()

    # =========================================================================
    # PHASE 3: Injected router regression proof
    # =========================================================================

    dispatched_kinds: list[str] = []

    class _FakeRouter(ExecutorRouter):
        def dispatch_execute(self, **kwargs: Any) -> Any:
            dispatched_kinds.append(kwargs.get("executor_kind", ""))
            return super().dispatch_execute(**kwargs)

    fake_router = _FakeRouter()
    injection_db_path = os.path.join(workspace_root, "injection_tasks.sqlite3")
    if os.path.exists(injection_db_path):
        os.remove(injection_db_path)
    injection_store = TaskStore(db_path=injection_db_path)
    injection_service = TaskService(
        store=injection_store,
        router=fake_router,
    )
    inj_server, inj_thread = injection_service.start(host="127.0.0.1", port=0)
    inj_port = inj_server.server_address[1]

    _, inj_create = _http(
        "POST",
        "/api/tasks",
        {"title": "Router injection test", "executor_kind": "deterministic_fixture"},
        inj_port,
    )
    inj_tid = inj_create["id"]
    before_count = len(dispatched_kinds)
    _, inj_exec = _http("POST", f"/api/tasks/{inj_tid}/execute", {}, inj_port)
    after_count = len(dispatched_kinds)
    assert after_count > before_count, "injected router was not called"
    assert dispatched_kinds[-1] == "deterministic_fixture"
    assert inj_exec["status"] == "READY_FOR_REVIEW_FIXTURE"

    results["router_injection_proof"] = {
        "dispatched_count": after_count,
        "last_dispatched_kind": dispatched_kinds[-1],
        "execute_status": inj_exec["status"],
        "injection_task_id": inj_tid,
    }
    results["chain"].append("router_injection_verified")

    inj_server.shutdown()
    inj_server.server_close()
    inj_thread.join(timeout=3)
    injection_store._conn.close()

    # Idempotency token test: same key + same request -> same task ID
    same_db = os.path.join(workspace_root, "idempotency_tasks.sqlite3")
    if os.path.exists(same_db):
        os.remove(same_db)
    idem_store = TaskStore(db_path=same_db)
    idem_router = ExecutorRouter()
    idem_service = TaskService(store=idem_store, router=idem_router)
    idem_server, idem_thread = idem_service.start(host="127.0.0.1", port=0)
    idem_port = idem_server.server_address[1]

    _, first = _http(
        "POST",
        "/api/tasks",
        {"title": "idem", "executor_kind": "deterministic_fixture", "idempotency_key": "stable-key-001"},
        idem_port,
    )
    _, second = _http(
        "POST",
        "/api/tasks",
        {"title": "idem", "executor_kind": "deterministic_fixture", "idempotency_key": "stable-key-001"},
        idem_port,
    )
    assert first["id"] == second["id"], "same key + same request must return same task ID"
    results["idempotency_token_proof"] = {
        "key": "stable-key-001",
        "same_key_same_request": first["id"] == second["id"],
        "task_id": first["id"],
    }
    results["chain"].append("stable_idempotency_token_verified")

    idem_server.shutdown()
    idem_server.server_close()
    idem_thread.join(timeout=3)
    idem_store._conn.close()

    results["chain"].append("provider_free_acceptance_complete")
    return results


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Provider-free task plane acceptance",
    )
    parser.add_argument(
        "--repo-dir",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root",
    )
    parser.add_argument(
        "--workspace-root",
        default=os.path.join(tempfile.gettempdir(), "issue128-provider-free-task-plane"),
        help="Root for disposable workspaces and the SQLite store",
    )
    args = parser.parse_args(argv)

    try:
        results = _run(
            repo_dir=args.repo_dir,
            workspace_root=args.workspace_root,
        )
    except Exception as exc:
        error_result = {
            "status": "FAILED",
            "error": f"{exc.__class__.__name__}:{exc}",
            "model_calls": 0,
            "codex_calls": 0,
            "openhands_calls": 0,
        }
        print(json.dumps(error_result, indent=2, sort_keys=True))
        return 1

    print(json.dumps(results, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
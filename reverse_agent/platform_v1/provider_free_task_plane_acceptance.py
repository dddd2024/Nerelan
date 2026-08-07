"""End-to-end provider-free task plane acceptance.

Proves the complete non-model chain without Codex, OpenHands, or any third-party
provider:

Frontend-compatible task request
  -> real Task API
  -> server task id
  -> SQLite persistence
  -> ExecutorRouter
  -> DeterministicFixtureExecutor
  -> disposable workspace mutation
  -> validation
  -> events
  -> changed paths
  -> evidence
  -> readback

Exit code 0 on success, non-zero with a JSON error on any failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .run_store import TaskStore
from .task_runtime import DeterministicFixtureExecutor, ExecutorRouter
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
    executor = DeterministicFixtureExecutor()

    results: dict[str, Any] = {
        "model_calls": 0,
        "codex_calls": 0,
        "openhands_calls": 0,
        "repo_dir": os.path.abspath(repo_dir),
        "workspace_root": workspace_root,
        "db_path": db_path,
        "task_id": None,
        "execution_id": None,
        "fixture_executor_result": {},
        "changed_files": [],
        "sqlite_persistence_proof": {},
        "chain": [],
    }

    # 1. Create task (server-owned id).
    task = store.create_task(
        title="Provider-free fixture task",
        repository="dddd2024/reverse-agent",
        executor_kind="deterministic_fixture",
        idempotency_key="issue128-acceptance-001",
    )
    results["task_id"] = task.id
    results["execution_id"] = task.execution_id
    results["chain"].append("task_created_server_owned")
    assert task.id.startswith("task-"), "server task id must be generated"
    assert task.status == "QUEUED"

    # 2. Idempotency key prevents duplicate.
    existing = store.find_by_idempotency_key("issue128-acceptance-001")
    assert existing is not None and existing.id == task.id
    dup = store.create_task(
        title="Provider-free fixture task",
        repository="dddd2024/reverse-agent",
        executor_kind="deterministic_fixture",
        idempotency_key="issue128-acceptance-001",
    )
    assert dup.id == task.id, "idempotency key must not create duplicate"
    results["chain"].append("idempotency_prevented_duplicate")

    # 3. ExecutorRouter dispatches the deterministic fixture executor.
    worktree_root = os.path.join(workspace_root, task.id)
    os.makedirs(worktree_root, exist_ok=True)

    def _event_cb(tid: str, event: dict[str, Any]) -> None:
        store.add_event(
            tid,
            event_type=event.get("type", "EXECUTOR_FINISHED"),
            title=event.get("title", "Executor event"),
            description=event.get("description", ""),
            raw_log=event.get("raw_log", ""),
            metadata=event.get("metadata"),
        )

    result = router.dispatch_execute(
        task_id=task.id,
        store=store,
        executor_kind="deterministic_fixture",
        workspace_root=worktree_root,
        event_callback=_event_cb,
    )
    results["fixture_executor_result"] = {
        "success": result.success,
        "validation_exit_code": result.validation_exit_code,
        "validation_command_id": result.validation_command_id,
        "validation_output_digest": result.validation_output_digest,
        "workspace": result.workspace,
        "execution_id": result.execution_id,
        "error": result.error,
        "changed_files": result.changed_files,
    }
    results["chain"].append("executor_router_dispatched")
    results["chain"].append("deterministic_fixture_executed")
    assert result.success, f"fixture executor must succeed: {result.error}"
    assert result.validation_exit_code == 0
    assert result.validation_command_id == "git_diff_check"
    assert result.validation_output_digest, "validation output digest required"
    assert result.changed_files, "at least one changed file required"
    results["chain"].append("validation_passed")

    # 4. Persist changed files and evidence.
    task = store.set_changed_files(task.id, result.changed_files)
    store.add_evidence(
        task.id,
        category="Validation",
        label=result.validation_command_id,
        value="0",
        status="pass",
        detail="deterministic fixture validation passed",
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
    results["chain"].append("evidence_recorded")

    # 5. Transition to terminal ready-for-review state.
    task = store.transition_to(task.id, "PREPARING_WORKSPACE")
    task = store.transition_to(task.id, "RUNNING_FIXTURE")
    task = store.transition_to(task.id, "VALIDATING")
    task = store.transition_to(task.id, "READY_FOR_REVIEW_FIXTURE")
    results["chain"].append("state_transitions_complete")

    # 6. Persistence proof: close and reopen the store.
    closed_store = TaskStore(db_path=db_path)
    persisted = closed_store.get_task(task.id)
    results["sqlite_persistence_proof"] = {
        "task_id": persisted.id,
        "status": persisted.status,
        "execution_id": persisted.execution_id,
        "event_count": len(persisted.events),
        "changed_file_count": len(persisted.changed_files),
        "evidence_count": len(persisted.evidence_refs),
        "validation_command_id": persisted.validation_command_id,
        "validation_exit_code": persisted.validation_exit_code,
        "validation_output_digest": persisted.validation_output_digest,
        "db_path": db_path,
        "db_exists": os.path.exists(db_path),
        "db_size_bytes": os.path.getsize(db_path) if os.path.exists(db_path) else 0,
    }
    assert persisted.id == task.id
    assert persisted.status == "READY_FOR_REVIEW_FIXTURE"
    assert len(persisted.events) >= 5
    assert len(persisted.changed_files) >= 1
    assert len(persisted.evidence_refs) >= 2
    results["chain"].append("sqlite_persistence_verified")
    results["chain"].append("readback_verified")

    # 7. HTTP Task API loopback round-trip.
    service = TaskService(store=TaskStore(db_path=db_path), router=router)
    server, thread = service.start(
        host="127.0.0.1",
        port=0,
    )
    port = server.server_address[1]
    results["task_api"] = {
        "host": "127.0.0.1",
        "port": int(port),
        "loopback_only": True,
        "base_url": f"http://127.0.0.1:{port}",
    }

    from urllib.request import Request, urlopen

    def _http(method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
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
        with urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), payload

    status_code, create_payload = _http(
        "POST",
        "/api/tasks",
        {
            "title": "HTTP fixture task",
            "repository": "dddd2024/reverse-agent",
            "executor_kind": "deterministic_fixture",
            "idempotency_key": "issue128-http-001",
        },
    )
    assert status_code == 201, f"POST /api/tasks expected 201, got {status_code}"
    http_task_id = create_payload["id"]
    assert http_task_id.startswith("task-")
    results["http_task_id"] = http_task_id
    results["chain"].append("http_post_task_created")

    status_code, get_payload = _http("GET", f"/api/tasks/{http_task_id}")
    assert status_code == 200
    assert get_payload["id"] == http_task_id
    assert get_payload["status"] == "QUEUED"
    assert get_payload["executor_kind"] == "deterministic_fixture"
    assert get_payload["frontend_task"]["executor"] == "fixture/provider-free"
    results["chain"].append("http_get_task_readback")

    status_code, events_payload = _http("GET", f"/api/tasks/{http_task_id}/events")
    assert status_code == 200
    assert events_payload["task_id"] == http_task_id
    assert len(events_payload["events"]) >= 1
    assert events_payload["events"][0]["type"] == "DISCOVERED"
    results["chain"].append("http_events_readback")

    status_code, list_payload = _http("GET", "/api/tasks")
    assert status_code == 200
    ids = [t["id"] for t in list_payload["tasks"]]
    assert http_task_id in ids
    results["http_task_list_count"] = len(ids)
    results["chain"].append("http_list_tasks_readback")

    # Idempotent create through HTTP.
    status_code, dup_payload = _http(
        "POST",
        "/api/tasks",
        {
            "title": "HTTP fixture task",
            "repository": "dddd2024/reverse-agent",
            "executor_kind": "deterministic_fixture",
            "idempotency_key": "issue128-http-001",
        },
    )
    assert status_code == 201
    assert dup_payload["id"] == http_task_id
    results["chain"].append("http_idempotency_preserved")

    server.shutdown()
    server.server_close()
    thread.join(timeout=3)

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

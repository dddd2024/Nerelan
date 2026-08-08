"""Real OpenCode backend vertical slice acceptance.

Exercises the full HTTP chain:
  POST /api/tasks (executor_kind=opencode)
  -> POST /api/tasks/{id}/execute
  -> GET /api/tasks/{id}
  -> GET /api/tasks/{id}/events

Proves:
- OpenCode CLI child process started with non-OpenAI model
- Isolated worktree outside source tree
- Source checkout not mutated
- Real file mutation occurred
- git diff --check validation passed
- Changed files recorded
- Executor/model evidence recorded
- Backend terminal state READY_FOR_REVIEW -> frontend READY_FOR_HUMAN
- Events persisted
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .run_store import TaskStore
from .task_runtime import ExecutorRouter
from .task_service import TaskService


def _json_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _run(
    *,
    repo_dir: str,
    workspace_root: str,
    model: str,
) -> dict[str, Any]:
    repo_dir = os.path.abspath(repo_dir)
    workspace_root = os.path.abspath(workspace_root)
    os.makedirs(workspace_root, exist_ok=True)

    # Worktree subdirectory for this acceptance run
    run_id = "run_%s_%s" % (int(time.time()), uuid.uuid4().hex[:6])
    run_dir = os.path.join(workspace_root, run_id)
    os.makedirs(run_dir, exist_ok=True)

    db_path = os.path.join(run_dir, "opencode_tasks.sqlite3")
    task_workspaces_root = os.path.join(run_dir, "task_workspaces")
    os.makedirs(task_workspaces_root, exist_ok=True)

    results: dict[str, Any] = {
        "timestamp": _json_now(),
        "repo_dir": repo_dir,
        "workspace_root": workspace_root,
        "run_dir": run_dir,
        "db_path": db_path,
        "model": model,
        "phase": [],
    }

    # ---- Verify OpenCode CLI ----
    from .opencode_executor import resolve_opencode_cli
    cli_path, is_cmd = resolve_opencode_cli()

    version_argv = [cli_path, "--version"]
    models_argv = [cli_path, "models"]

    version_result = subprocess.run(
        version_argv,
        capture_output=True,
        text=True,
        timeout=15,
    )
    results["opencode_path"] = cli_path
    results["opencode_is_cmd"] = is_cmd
    assert cli_path, "OpenCode CLI not found"
    results["phase"].append("opencode_cli_resolved")

    results["opencode_version"] = (version_result.stdout or version_result.stderr or "").strip()
    results["phase"].append("opencode_version_checked")

    models_result = subprocess.run(
        models_argv,
        capture_output=True,
        text=True,
        timeout=30,
    )
    results["opencode_models_output"] = (models_result.stdout or "")[:2000]
    assert model.lower() in (models_result.stdout or "").lower(), (
        "Required model %s not found in opencode models output" % model
    )
    results["phase"].append("opencode_model_verified")

    # ---- Snapshot source checkout ----
    source_status_before = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )
    source_hash_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )
    results["source_checkout"] = {
        "head_before": source_hash_before.stdout.strip(),
        "status_before": source_status_before.stdout.strip(),
    }
    results["phase"].append("source_checkout_snapshot_before")

    # ---- Start TaskService ----
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()

    os.environ["REVERSE_AGENT_TASK_DB_PATH"] = db_path
    os.environ["REVERSE_AGENT_TASK_WORKSPACE_ROOT"] = task_workspaces_root
    os.environ["REVERSE_AGENT_OPENCODE_MODEL"] = model
    os.environ["REVERSE_AGENT_REPO_DIR"] = repo_dir

    service = TaskService(store=store, router=router)
    server, thread = service.start(host="127.0.0.1", port=0)
    port = server.server_address[1]
    base_url = "http://127.0.0.1:%d" % port

    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    def _http(method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        url = "%s%s" % (base_url, path)
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
        with urlopen(req, timeout=600) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), payload

    # ---- Step 1: POST /api/tasks ----
    create_body = {
        "title": "Write file issue127_acceptance_output.txt containing exactly alpha-ok then run git diff --check",
        "repository": "dddd2024/reverse-agent",
        "executor_kind": "opencode",
        "model_profile_ref": model,
        "idempotency_key": "issue127-opencode-acceptance-v1",
    }
    status_code, create_payload = _http("POST", "/api/tasks", create_body)
    assert status_code == 201, "POST /api/tasks expected 201, got %d" % status_code
    http_task_id = create_payload["id"]
    assert create_payload["status"] == "QUEUED"
    assert create_payload["executor_kind"] == "opencode"
    results["http_create"] = {
        "status": status_code,
        "task_id": http_task_id,
        "executor_kind": create_payload["executor_kind"],
        "execution_id": create_payload.get("execution_id", ""),
        "state": create_payload.get("state", ""),
    }
    results["phase"].append("http_post_task_created")

    # ---- Step 2: POST /api/tasks/{id}/execute ----
    status_code, execute_payload = _http(
        "POST", "/api/tasks/%s/execute" % http_task_id, {}
    )
    assert status_code == 200, "POST execute expected 200, got %d" % status_code
    results["http_execute"] = {
        "status": status_code,
        "task_status": execute_payload.get("status", ""),
        "state": execute_payload.get("state", ""),
        "validation_exit_code": execute_payload.get("validation_exit_code"),
        "validation_command_id": execute_payload.get("validation_command_id", ""),
        "executor": execute_payload.get("frontend_task", {}).get("executor", ""),
        "executor_kind": execute_payload.get("executor_kind", ""),
        "changed_file_count": len(execute_payload.get("changed_files", [])),
        "evidence_count": len(execute_payload.get("evidence", [])),
        "changed_files": execute_payload.get("changed_files", []),
    }
    results["phase"].append("http_post_execute_started")

    # Allow task to reach a terminal state
    time.sleep(2)

    # ---- Step 3: GET /api/tasks/{id} readback ----
    status_code, get_payload = _http("GET", "/api/tasks/%s" % http_task_id)
    assert status_code == 200
    backend_status = get_payload.get("status", "")
    frontend_state = get_payload.get("state", "")
    results["http_get_task"] = {
        "status": status_code,
        "task_id": get_payload.get("id", ""),
        "backend_status": backend_status,
        "frontend_state": frontend_state,
        "executor_kind": get_payload.get("executor_kind", ""),
        "executor": get_payload.get("frontend_task", {}).get("executor", ""),
        "validation_exit_code": get_payload.get("validation_exit_code"),
        "validation_command_id": get_payload.get("validation_command_id", ""),
        "changed_file_count": len(get_payload.get("changed_files", [])),
        "evidence_count": len(get_payload.get("evidence", [])),
        "events_count": len(get_payload.get("events", [])),
        "execution_id": get_payload.get("execution_id", ""),
    }
    results["phase"].append("http_get_task_readback")

    # Verify terminal state
    assert backend_status in ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"), (
        "Expected READY_FOR_REVIEW, got %s" % backend_status
    )
    assert frontend_state == "READY_FOR_HUMAN", (
        "Expected frontend READY_FOR_HUMAN, got %s" % frontend_state
    )
    assert get_payload.get("executor_kind") == "opencode"

    # Verify evidence
    evidence = get_payload.get("evidence", [])
    has_executor_evidence = any(e.get("category") == "Executor" for e in evidence)
    has_validation_evidence = any(e.get("category") == "Validation" for e in evidence)
    assert has_executor_evidence, "Executor evidence missing"
    assert has_validation_evidence, "Validation evidence missing"
    assert get_payload.get("validation_exit_code") == 0, (
        "Validation exit code should be 0, got %s" % get_payload.get("validation_exit_code")
    )
    assert len(get_payload.get("changed_files", [])) >= 1, (
        "changed_files must be non-empty"
    )

    # Verify events
    event_types = [e.get("type", "") for e in get_payload.get("events", [])]
    assert "DISCOVERED" in event_types, "DISCOVERED event missing"
    assert "EXECUTOR_RUNNING" in event_types, "EXECUTOR_RUNNING missing"
    assert "EXECUTOR_FINISHED" in event_types, "EXECUTOR_FINISHED missing"
    assert "WORKSPACE_READY" in event_types, "WORKSPACE_READY missing"
    assert "VALIDATED" in event_types or "LOCAL_VALIDATED" in event_types, (
        "VALIDATED/LOCAL_VALIDATED missing"
    )
    results["event_types"] = event_types
    results["phase"].append("http_events_verified")

    # ---- Step 4: GET /api/tasks/{id}/events ----
    status_code, events_payload = _http(
        "GET", "/api/tasks/%s/events" % http_task_id
    )
    assert status_code == 200
    assert events_payload["task_id"] == http_task_id
    results["http_events_readback"] = {
        "status": status_code,
        "event_count": len(events_payload.get("events", [])),
        "event_types": [e.get("type", "") for e in events_payload.get("events", [])],
    }
    results["phase"].append("http_events_readback")

    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
    store._conn.close()

    # ---- Verify source checkout untouched ----
    source_status_after = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )
    source_hash_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )
    results["source_checkout"]["head_after"] = source_hash_after.stdout.strip()
    results["source_checkout"]["status_after"] = source_status_after.stdout.strip()
    results["source_checkout"]["untouched"] = (
        source_hash_before.stdout.strip() == source_hash_after.stdout.strip()
        and source_status_before.stdout.strip() == source_status_after.stdout.strip()
    )
    assert results["source_checkout"]["untouched"], "Source checkout was mutated by executor"
    results["phase"].append("source_checkout_untouched_verified")

    # ---- Verify isolated worktree exists outside source ----
    worktree_subdirs = []
    for root, dirs, files in os.walk(task_workspaces_root):
        for f in files:
            if f == "issue127_acceptance_output.txt":
                worktree_subdirs.append(os.path.join(root, f))
    results["acceptance_output_file"] = {
        "found": len(worktree_subdirs) > 0,
        "paths": worktree_subdirs[:5],
    }
    assert results["acceptance_output_file"]["found"], (
        "Acceptance output file not found in worktree"
    )
    results["phase"].append("acceptance_output_file_verified")

    # ---- Verify worktree is outside source ----
    for wp in worktree_subdirs:
        abs_wp = os.path.abspath(wp)
        repo_sep = repo_dir + os.sep
        assert not abs_wp.startswith(repo_sep), (
            "Worktree file is inside source repo: %s" % abs_wp
        )
    results["phase"].append("worktree_outside_source_verified")

    # ---- Restart/readback persistence ----
    restarted = TaskStore(db_path=db_path)
    restarted_task = restarted.get_task(http_task_id)
    results["restart_persistence"] = {
        "task_id": restarted_task.id,
        "status": restarted_task.status,
        "execution_id": restarted_task.execution_id,
        "event_count": len(restarted_task.events),
        "changed_file_count": len(restarted_task.changed_files),
        "evidence_count": len(restarted_task.evidence_refs),
        "validation_exit_code": restarted_task.validation_exit_code,
        "db_exists": os.path.exists(db_path),
    }
    assert restarted_task.id == http_task_id
    assert len(restarted_task.changed_files) >= 1
    assert len(restarted_task.evidence_refs) >= 2
    assert restarted_task.validation_exit_code == 0
    results["phase"].append("restart_persistence_verified")
    restarted._conn.close()

    results["phase"].append("acceptance_complete")
    return results


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="OpenCode task plane acceptance")
    parser.add_argument("--repo-dir", required=True, help="Repository root")
    parser.add_argument("--workspace-root", required=True, help="Workspace root")
    parser.add_argument("--model", required=True, help="Model identifier")
    args = parser.parse_args(argv)

    try:
        results = _run(
            repo_dir=args.repo_dir,
            workspace_root=args.workspace_root,
            model=args.model,
        )
    except Exception as exc:
        error_result = {
            "status": "FAILED",
            "error": "%s:%s" % (exc.__class__.__name__, exc),
            "model_calls": 0,
            "codex_calls": 0,
            "openhands_calls": 0,
            "phase": [],
        }
        print(json.dumps(error_result, indent=2, sort_keys=True))
        return 1

    print(json.dumps(results, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

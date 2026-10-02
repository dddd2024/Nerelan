"""Provider-free validation of an owner-approved exact candidate commit.

This route prepares an isolated checkout and runs existing fixed host checks.
It does not implement code, retain/export producer artifacts, or provide an OS
sandbox: approved repository tests are still executable code.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from typing import Any

from .functional_validation import git_output, load_contract, normalize_checks
from .repository_workspace import resolve_repository_workspace
from .run_store import TaskStoreError


def candidate_snapshot(store: Any, task: Any) -> dict[str, Any]:
    """Check the frozen Goal/task binding without authorizing new execution."""
    from .control_store import PlatformControlStore
    contract = load_contract(task)
    if task.executor_kind != "candidate_validation" or contract is None:
        raise TaskStoreError("candidate_contract_required")
    control = PlatformControlStore(store)
    goal = control.get_goal(contract["goal_id"])
    linked = control.list_goal_tasks(goal.id)
    planned = [item for item in goal.tasks if item.get("id") == contract["plan_task_id"]]
    if (goal.revision != contract["goal_revision"]
            or goal.artifact_digest != contract["goal_artifact_digest"]
            or goal.repository != task.repository or goal.executor_kind != task.executor_kind
            or goal.orchestration_mode != "single" or goal.binding_ref or len(planned) != 1
            or planned[0].get("expected_candidate_sha") != contract["expected_candidate_sha"]
            or planned[0].get("capability") != "validate_task"
            or list(normalize_checks(planned[0].get("validation_checks", ()))) != contract["checks"]
            or planned[0].get("artifact_input") is not None
            or not any(item["task_id"] == task.id and item["goal_revision"] == goal.revision
                       and item["plan_task_id"] == contract["plan_task_id"] for item in linked)):
        raise TaskStoreError("candidate_goal_snapshot_stale")
    return contract


def admit_candidate(store: Any, task: Any) -> dict[str, Any]:
    """Authorize new executor work against the current Goal and live window."""
    from .control_store import PlatformControlStore
    contract = candidate_snapshot(store, task)
    control = PlatformControlStore(store)
    goal = control.get_goal(contract["goal_id"])
    if goal.status != "RUNNING":
        raise TaskStoreError("candidate_goal_snapshot_stale")
    window = control.get_window(goal.window_id)
    now = datetime.now(timezone.utc)
    if (window.status != "ACTIVE" or goal.repository not in window.repositories
            or not {"execute_task", "validate_task"}.issubset(window.capabilities)
            or not datetime.fromisoformat(window.starts_at.replace("Z", "+00:00")) <= now
            < datetime.fromisoformat(window.expires_at.replace("Z", "+00:00"))):
        raise TaskStoreError("candidate_requires_active_window")
    resolve_repository_workspace(task.repository)
    return contract


class CandidateValidationExecutor:
    """Truthful native preparation identity, with no model or network call."""

    def __init__(self, *, approved_contract: dict[str, Any]) -> None:
        self._contract = approved_contract

    def execute(self, task_id: str, store: Any, *, workspace_root: str = "",
                event_callback: Any = None) -> Any:
        from .task_runtime import ExecutorResult
        task = store.get_task(task_id)
        contract = load_contract(task)
        if contract != self._contract or contract is None:
            raise TaskStoreError("candidate_contract_changed")
        if not workspace_root or not Path(workspace_root).is_absolute():
            raise TaskStoreError("candidate_workspace_root_required")
        source = resolve_repository_workspace(task.repository).repo_dir
        root = Path(workspace_root).resolve()
        target = root / task_id
        if target.exists() or root == source or root.is_relative_to(source):
            raise TaskStoreError("candidate_workspace_not_disposable")
        root.mkdir(parents=True, exist_ok=True)
        env = {key: os.environ[key] for key in (
            "PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"
        ) if key in os.environ}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
        origin = git_output(source, "remote", "get-url", "origin")
        for argv in (
            ["git", "clone", "--no-checkout", "--shared", "--", str(source), str(target)],
            ["git", "-C", str(target), "config", "--local", "core.autocrlf", "false"],
            # Owned disposable checkout only; do not change global/OS settings.
            ["git", "-C", str(target), "config", "--local", "core.longpaths", "true"],
            ["git", "-C", str(target), "remote", "set-url", "origin", origin],
            # A source may hold the approved commit only through FETCH_HEAD.
            # Explicit local transfer keeps it available even when clone does
            # not retain unreferenced/shared objects. This is not a network URL.
            ["git", "-C", str(target), "fetch", "--no-tags", "--", str(source), contract["expected_candidate_sha"]],
            ["git", "-C", str(target), "checkout", "--detach", contract["expected_candidate_sha"]],
        ):
            result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                    env=env, timeout=30, check=False)
            if result.returncode:
                raise TaskStoreError("candidate_checkout_failed")
        resolve_repository_workspace(task.repository, source_dir=target)
        if git_output(target, "rev-parse", "HEAD") != contract["expected_candidate_sha"]:
            raise TaskStoreError("candidate_checkout_head_mismatch")
        if event_callback is not None:
            event_callback(task_id, {"type": "WORKSPACE_READY", "title": "Exact candidate prepared",
                "metadata": {"workspace": str(target), "base_sha": contract["base_commit"],
                             "expected_candidate_sha": contract["expected_candidate_sha"],
                             "execution_id": task.execution_id, "executor_kind": "candidate_validation"}})
        return ExecutorResult(success=True, validation_exit_code=-1, validation_command_id="",
            validation_output_digest="", validation_output_summary="Host checks pending",
            workspace=str(target), execution_id=task.execution_id)

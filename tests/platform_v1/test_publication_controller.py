import json
from pathlib import Path

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.publication_controller import CommandResult, PublicationController
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _validated_task(store: TaskStore):
    task = store.create_task(title="Publish me", executor_kind="deterministic_fixture")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING_FIXTURE")
    store.transition_to(task.id, "VALIDATING")
    store.transition_to(task.id, "READY_FOR_REVIEW_FIXTURE")
    return store.get_task(task.id)


def _window(autonomy):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    return autonomy.activate({
        "policy_id": "publish-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": ["open_draft_pr"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })


def test_publication_is_allowlisted_draft_only_and_idempotent(tmp_path, monkeypatch):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    task = _validated_task(store)
    window = _window(autonomy)
    state = {"committed": False, "pr": False, "pushes": 0, "creates": 0}

    def runner(argv, cwd):
        args = tuple(argv)
        if args[:3] == ("git", "rev-parse", "--show-toplevel"):
            return CommandResult(0, str(tmp_path) + "\n")
        if args[:3] == ("git", "rev-parse", "HEAD"):
            return CommandResult(0, ("commit123" if state["committed"] else "base123") + "\n")
        if args[:3] == ("git", "status", "--porcelain=v1"):
            return CommandResult(0, " M allowed/file.py\n")
        if args[:3] == ("git", "branch", "--show-current"):
            return CommandResult(0, "main\n")
        if args[:3] == ("git", "diff", "--cached"):
            return CommandResult(0, "allowed/file.py\n")
        if args[:2] == ("git", "commit"):
            state["committed"] = True
            return CommandResult(0)
        if args[:2] == ("git", "push"):
            state["pushes"] += 1
            return CommandResult(0)
        if args[:3] == ("gh", "pr", "list"):
            value = [{
                "number": 88, "url": "https://example/pr/88", "isDraft": True,
                "headRefOid": "commit123", "baseRefName": "main",
            }] if state["pr"] else []
            return CommandResult(0, json.dumps(value))
        if args[:3] == ("gh", "pr", "create"):
            state["pr"] = True
            state["creates"] += 1
            return CommandResult(0, "https://example/pr/88\n")
        return CommandResult(0)

    monkeypatch.setattr(control, "durable_workspace", lambda task_id: {
        "worktree_path": str(tmp_path), "worktree_head_sha": "base123",
        "repository_base_sha": "base123", "accepted_checkpoint": "COMPLETE",
    })
    controller = PublicationController(
        store=store, control_store=control, autonomy=autonomy, runner=runner
    )
    first = controller.publish(
        task.id, window_id=window.id, base_branch="main", allowed_paths=["allowed"]
    )
    second = controller.publish(
        task.id, window_id=window.id, base_branch="main", allowed_paths=["allowed"]
    )
    assert first.status == second.status == "COMPLETE"
    assert first.pr_number == 88
    assert state["pushes"] == 1
    assert state["creates"] == 1


def test_publication_fails_closed_on_path_outside_allowlist(tmp_path, monkeypatch):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    task = _validated_task(store)
    window = _window(autonomy)

    def runner(argv, cwd):
        args = tuple(argv)
        if args[:3] == ("git", "rev-parse", "--show-toplevel"):
            return CommandResult(0, str(tmp_path) + "\n")
        if args[:3] == ("git", "rev-parse", "HEAD"):
            return CommandResult(0, "base123\n")
        if args[:3] == ("git", "status", "--porcelain=v1"):
            return CommandResult(0, "?? forbidden.txt\n")
        return CommandResult(0)

    monkeypatch.setattr(control, "durable_workspace", lambda task_id: {
        "worktree_path": str(tmp_path), "worktree_head_sha": "base123",
    })
    controller = PublicationController(
        store=store, control_store=control, autonomy=autonomy, runner=runner
    )
    with pytest.raises(TaskStoreError, match="outside_allowlist"):
        controller.publish(
            task.id, window_id=window.id, base_branch="main", allowed_paths=["allowed"]
        )

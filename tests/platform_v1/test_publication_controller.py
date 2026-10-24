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
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["open_draft_pr"],
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


from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup
from reverse_agent.platform_v1 import artifact_handoff
from test_model_review_feedback import rejected, repair_and_review


def artifact_publisher(setup):
    store = setup[0]
    control = PlatformControlStore(store)
    goal = control.get_goal(control.goal_id_for_task(setup[2]))
    store._conn.execute("UPDATE platform_autonomous_windows SET capabilities_json = ?",
        (json.dumps(["execute_task", "validate_only", "open_draft_pr", "land_reviewed_pr"]),))
    remote = {"head": "", "creates": 0, "pushes": [], "pr": False}
    def runner(argv, cwd):
        if argv[:2] == ("git", "push"):
            remote["head"] = argv[3].split(":")[0]
            remote["pushes"].append(argv[3])
            return CommandResult(0)
        if argv[:2] in {("git", "rev-parse"), ("git", "rev-list")}:
            artifact = next(artifact_handoff._load_evidence(store.get_task(row["task_id"]),
                artifact_handoff.ACCEPTED_CATEGORY, store.get_task(row["task_id"]).execution_id)
                for row in control.list_goal_tasks(goal.id) if row["plan_task_id"] == "A")
            if argv[1] == "rev-list":
                return CommandResult(0, artifact["commit"] + " " + artifact["source_head"])
            return CommandResult(0, artifact["tree"] if argv[2].endswith("^{tree}") else artifact["commit"])
        if argv[:3] == ("gh", "pr", "create"):
            remote["creates"] += 1
            remote["pr"] = True
            return CommandResult(0)
        if argv[:3] == ("gh", "pr", "list"):
            return CommandResult(0, json.dumps([{"number": 1266, "url": "https://example/pr/1266",
                "isDraft": True, "headRefOid": remote["head"], "baseRefName": "main"}] if remote["pr"] else []))
        pytest.fail(f"unexpected command {argv}")
    publication = PublicationController(store=store, control_store=control,
        autonomy=AutonomyService(control_store=control, capabilities=CapabilityRegistry()), runner=runner)
    return publication, control, goal, remote


def test_retained_publication_reuses_goal_branch_and_draft_across_repairs(review_setup):
    publication, control, goal, remote = artifact_publisher(review_setup)
    first = publication.publish_artifact(review_setup[2], window_id=goal.window_id, goal_id=goal.id)
    store, control, service, goal_id = rejected(review_setup)
    repair, _, result = repair_and_review(review_setup, service, goal_id, '{"verdict":"ACCEPT","findings":[]}')
    assert result.success
    second = publication.publish_artifact(repair, window_id=goal.window_id, goal_id=goal.id)
    replay = publication.publish_artifact(repair, window_id=goal.window_id, goal_id=goal.id)
    assert first.pr_number == second.pr_number == replay.pr_number == 1266
    assert first.branch == second.branch == "nerelan/" + goal.id
    assert first.commit_sha != second.commit_sha
    assert remote["creates"] == 1
    assert all(push.endswith(":refs/heads/" + first.branch) for push in remote["pushes"])


def test_artifact_publication_refuses_unverified_output(review_setup, monkeypatch):
    publication, control, goal, remote = artifact_publisher(review_setup)
    from reverse_agent.platform_v1 import functional_validation
    monkeypatch.setattr(functional_validation, "functional_evidence", lambda task: {"verified": False})
    with pytest.raises(TaskStoreError, match="unverified"):
        publication.publish_artifact(review_setup[2], window_id=goal.window_id, goal_id=goal.id)
    assert not remote["pushes"] and remote["creates"] == 0

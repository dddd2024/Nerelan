from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _services():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    return store, control, autonomy, GoalService(store=store, control_store=control)


def _window_payload():
    now = datetime.now(timezone.utc)
    return {
        "policy_id": "owner-window-1",
        "policy_revision": 1,
        "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "validate_task"],
        "max_concurrent_tasks": 2,
        "max_tasks": 10,
        "max_retries": 1,
        "confirmation": "ACTIVATE",
    }


def test_goal_plan_approval_and_launch_are_persistent_and_idempotent():
    store, control, autonomy, goals = _services()
    goal = goals.create({
        "objective": "Add a durable status endpoint",
        "repository": "dddd2024/reverse-agent",
        "idempotency_key": "goal-http-status-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    planned = goals.plan(goal.id, expected_revision=1)
    assert planned.goal.status == "PLANNED"
    assert planned.goal.spec_markdown.startswith("# Specification")
    assert [task["id"] for task in planned.goal.tasks] == ["T001", "T002", "T003"]
    approved = goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    assert approved.status == "APPROVED"
    window = autonomy.activate(_window_payload())
    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert running.status == "RUNNING"
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 3
    assert links[1]["dependencies"] == ("T001",)
    assert store.count_tasks() == 3


def test_goal_amendment_invalidates_old_plan_and_requires_replanning():
    _, _, _, goals = _services()
    goal = goals.create({
        "objective": "Original objective",
        "idempotency_key": "goal-amend-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1)
    amended = goals.amend(goal.id, expected_revision=1, objective="Revised objective")
    assert amended.revision == 2
    assert amended.status == "DRAFT"
    assert amended.artifact_digest == ""
    with pytest.raises(TaskStoreError, match="goal_not_approvable"):
        goals.approve(goal.id, expected_revision=2)


def test_goal_rejects_secret_shaped_planning_fields():
    _, _, _, goals = _services()
    goal = goals.create({
        "objective": "Do safe work",
        "idempotency_key": "goal-secret-reject-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    with pytest.raises(TaskStoreError, match="sensitive_control_field_rejected"):
        goals.plan(
            goal.id,
            expected_revision=1,
            tasks=[{"id": "T001", "title": "bad", "instruction": "x", "api_token": "sentinel"}],
        )


def _complete_goal_chain():
    store, control, autonomy, goals = _services()
    goal = goals.create({
        "objective": "Converge goal state",
        "repository": "dddd2024/reverse-agent",
        "idempotency_key": "goal-converge-v1",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1)
    approved = goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    assert approved.status == "APPROVED"
    window = autonomy.activate(_window_payload())
    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert running.status == "RUNNING"
    return store, control, autonomy, goals, goal


def test_list_provides_authoritative_goal_state_with_task_links():
    store, control, _, goals, goal = _complete_goal_chain()
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 3
    for link in links:
        store.set_state(link["task_id"], "READY_FOR_REVIEW")

    listed = goals.list()
    listed_goal = next((g for g in listed if g["id"] == goal.id), None)
    assert listed_goal is not None
    assert listed_goal["status"] == "COMPLETED"
    assert len(listed_goal["task_links"]) == 3
    assert {link["status"] for link in listed_goal["task_links"]} == {"READY_FOR_REVIEW"}

    detail = goals.detail(goal.id)
    assert detail["status"] == listed_goal["status"]
    assert [link["task_id"] for link in detail["task_links"]] == [
        link["task_id"] for link in listed_goal["task_links"]
    ]


def test_list_and_detail_converge_when_linked_task_fails():
    store, control, _, goals, goal = _complete_goal_chain()
    links = control.list_goal_tasks(goal.id)
    task_id = links[0]["task_id"]
    store.set_state(task_id, "FAILED")

    listed = goals.list()
    listed_goal = next(g for g in listed if g["id"] == goal.id)
    detail = goals.detail(goal.id)

    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    assert listed_goal["status"] == detail["status"]
    assert any(link["task_id"] == task_id and link["status"] == "FAILED" for link in listed_goal["task_links"])


def test_list_and_detail_converge_when_linked_task_is_blocked():
    store, control, _, goals, goal = _complete_goal_chain()
    links = control.list_goal_tasks(goal.id)
    store.set_state(links[0]["task_id"], "BLOCKED")

    listed = goals.list()
    listed_goal = next(g for g in listed if g["id"] == goal.id)
    detail = goals.detail(goal.id)

    assert listed_goal["status"] == "BLOCKED"
    assert detail["status"] == "BLOCKED"
    assert listed_goal["status"] == detail["status"]
    assert any(link["task_id"] == links[0]["task_id"] and link["status"] == "BLOCKED" for link in listed_goal["task_links"])

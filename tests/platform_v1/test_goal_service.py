from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
import reverse_agent.platform_v1.control_store as control_store_module
import reverse_agent.platform_v1.goal_service as goal_service_module
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


def _running_timestamp_goal():
    store, control, autonomy, goals = _services()
    goal = goals.create({
        "objective": "Preserve business timestamps on reads",
        "idempotency_key": "timestamp-goal",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1)
    goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    window = autonomy.activate(_window_payload())
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    return store, control, goals, goal.id, control.list_goal_tasks(goal.id)[0]["task_id"]


@pytest.mark.parametrize("read_response", ["list", "detail"])
@pytest.mark.parametrize("task_status,goal_status", [
    ("QUEUED", "RUNNING"),
    ("RUNNING", "RUNNING"),
    ("INTERRUPTED", "RUNNING"),
    ("BLOCKED", "BLOCKED"),
    ("FAILED", "BLOCKED"),
    ("CANCELLED", "BLOCKED"),
    ("READY_FOR_REVIEW", "COMPLETED"),
    ("READY_FOR_REVIEW_FIXTURE", "COMPLETED"),
])
def test_unchanged_goal_reads_preserve_timestamp_without_row_writes(
    monkeypatch, read_response, task_status, goal_status
):
    store, control, goals, goal_id, task_id = _running_timestamp_goal()
    store.set_state(task_id, task_status)
    control.refresh_goal_status(goal_id)
    before = control.get_goal(goal_id)
    changes = store._conn.total_changes
    try:
        for observed_at in ("2099-01-01T00:00:00Z", "2099-01-02T00:00:00Z"):
            monkeypatch.setattr(
                control_store_module, "_utc_now", lambda: observed_at
            )
            response = goals.list()[0] if read_response == "list" else goals.detail(goal_id)
            assert response["id"] == goal_id
            assert response["status"] == goal_status
            assert response["updated_at"] == before.updated_at
        assert store._conn.total_changes == changes
        assert control.get_goal(goal_id) == before
    finally:
        store._conn.close()


@pytest.mark.parametrize("before_task,after_task,expected_status,changed", [
    ("QUEUED", "READY_FOR_REVIEW", "COMPLETED", True),
    ("READY_FOR_REVIEW", "FAILED", "BLOCKED", True),
    ("FAILED", "QUEUED", "RUNNING", True),
    ("QUEUED", "RUNNING", "RUNNING", False),
    ("FAILED", "CANCELLED", "BLOCKED", False),
    ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "COMPLETED", False),
])
def test_goal_timestamp_advances_once_only_for_derived_status_change(
    monkeypatch, before_task, after_task, expected_status, changed
):
    store, control, goals, goal_id, task_id = _running_timestamp_goal()
    store.set_state(task_id, before_task)
    control.refresh_goal_status(goal_id)
    before = control.get_goal(goal_id)
    store.set_state(task_id, after_task)
    changes = store._conn.total_changes
    try:
        monkeypatch.setattr(
            control_store_module, "_utc_now", lambda: "2099-01-01T00:00:00Z"
        )
        first = goals.detail(goal_id)
        expected_time = "2099-01-01T00:00:00Z" if changed else before.updated_at
        assert first["status"] == expected_status
        assert first["updated_at"] == expected_time
        assert store._conn.total_changes == changes + int(changed)
        monkeypatch.setattr(
            control_store_module, "_utc_now", lambda: "2099-01-02T00:00:00Z"
        )
        assert goals.list()[0]["updated_at"] == expected_time
        assert goals.detail(goal_id)["updated_at"] == expected_time
        assert store._conn.total_changes == changes + int(changed)
    finally:
        store._conn.close()


@pytest.mark.parametrize("stage", ["DRAFT", "PLANNED", "APPROVED"])
def test_unlaunched_goal_reads_preserve_status_and_timestamp(monkeypatch, stage):
    store, control, _, goals = _services()
    goal = goals.create({
        "objective": "No current execution links",
        "idempotency_key": "unlaunched-timestamp-goal",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    if stage in {"PLANNED", "APPROVED"}:
        goals.plan(goal.id, expected_revision=1)
    if stage == "APPROVED":
        goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    before = control.get_goal(goal.id)
    changes = store._conn.total_changes
    try:
        monkeypatch.setattr(
            control_store_module, "_utc_now", lambda: "2099-01-01T00:00:00Z"
        )
        for response in (goals.list()[0], goals.detail(goal.id)):
            assert response["status"] == stage
            assert response["updated_at"] == before.updated_at
        assert store._conn.total_changes == changes
    finally:
        store._conn.close()


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
    assert [task["id"] for task in planned.goal.tasks] == ["T001"]
    default_task = planned.goal.tasks[0]
    assert default_task["dependencies"] == []
    assert default_task["capability"] == "execute_task"
    instruction = default_task["instruction"]
    lowered = instruction.lower()
    assert "analyze" in lowered
    assert "implement" in lowered
    assert "verify" in lowered
    assert "same runtime task" in lowered
    assert "prepared worktree" in lowered
    assert "independent repository baseline" in lowered
    for criterion in planned.goal.acceptance_criteria:
        assert criterion in instruction

    approved = goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    assert approved.status == "APPROVED"
    window = autonomy.activate(_window_payload())
    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert running.status == "RUNNING"
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 1
    assert links[0]["plan_task_id"] == "T001"
    assert links[0]["dependencies"] == ()
    assert store.count_tasks() == 1
    runtime_task = store.get_task(links[0]["task_id"])
    assert runtime_task.orchestration_mode == "single"


def test_default_opencode_goal_launch_materializes_one_sequential_team_task(monkeypatch):
    store, control, autonomy, goals = _services()
    monkeypatch.setattr(
        goal_service_module,
        "resolve_repository_workspace",
        lambda repository: object(),
    )
    goal = goals.create({
        "objective": "Implement and verify one bounded product change",
        "repository": "dddd2024/Nerelan",
        "idempotency_key": "goal-opencode-single-team-v1",
        "executor_kind": "opencode",
        "orchestration_mode": "sequential_team",
        "binding_ref": "coding-default",
    })

    planned = goals.plan(goal.id, expected_revision=1)
    assert [task["id"] for task in planned.goal.tasks] == ["T001"]
    goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    window_payload = _window_payload()
    window_payload["repositories"] = ["dddd2024/Nerelan"]
    window = autonomy.activate(window_payload)
    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)

    assert running.status == "RUNNING"
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 1
    runtime_task = store.get_task(links[0]["task_id"])
    assert runtime_task.executor_kind == "opencode"
    assert runtime_task.orchestration_mode == "sequential_team"
    assert runtime_task.binding_ref == "coding-default"


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


@pytest.mark.parametrize("read_response", ["list", "detail"])
def test_goal_response_status_uses_the_returned_link_snapshot(
    monkeypatch, read_response
):
    store, control, autonomy, goals = _services()
    goal = goals.create({
        "objective": "Keep goal response truth coherent",
        "idempotency_key": "goal-response-snapshot-v1-" + read_response,
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(
        goal.id,
        expected_revision=1,
        tasks=[{"id": "T001", "title": "step", "instruction": "run"}],
    )
    goals.approve(goal.id, expected_revision=1, policy_ref="owner-window-1")
    window = autonomy.activate(_window_payload())
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    original_refresh = control.refresh_goal_status

    def refresh_then_change_task(goal_id):
        refreshed = original_refresh(goal_id)
        # Force the task transition into the gap between durable refresh and
        # the links snapshot used to build this response.
        store.set_state(task_id, "READY_FOR_REVIEW")
        return refreshed

    monkeypatch.setattr(control, "refresh_goal_status", refresh_then_change_task)
    response = goals.list()[0] if read_response == "list" else goals.detail(goal.id)

    assert response["status"] == "COMPLETED"
    assert response["task_links"][0]["status"] == "READY_FOR_REVIEW"


def _launched_dependency_pair():
    store, control, autonomy, goals = _services()
    goal = goals.create({
        "objective": "Execute dependencies regardless of plan input order",
        "idempotency_key": "dependency-pair",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "B", "title": "second", "instruction": "second", "dependencies": ["A"]},
        {"id": "A", "title": "first", "instruction": "first"},
    ])
    goals.approve(goal.id, expected_revision=1)
    window = autonomy.activate(_window_payload())
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    tasks = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}
    return store, control, goals, goal, window, tasks


@pytest.mark.parametrize("status", [
    "QUEUED", "RUNNING", "VALIDATING", "INTERRUPTED", "FAILED", "BLOCKED", "CANCELLED",
    "READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE",
])
def test_runnable_dependencies_require_successful_predecessor(status):
    store, control, _, _, window, tasks = _launched_dependency_pair()
    store.set_state(tasks["A"], status)
    runnable = control.runnable_tasks(window.id, limit=1)
    if status in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}:
        assert runnable == (tasks["B"],)
    elif status in {"QUEUED", "INTERRUPTED"}:
        assert runnable == (tasks["A"],)
    else:
        assert runnable == ()


@pytest.mark.parametrize("boundary", ["missing", "other_revision", "other_goal"])
def test_runnable_dependency_cannot_resolve_outside_its_goal_revision(boundary):
    store, control, goals, goal, window, tasks = _launched_dependency_pair()
    store.set_state(tasks["A"], "READY_FOR_REVIEW")
    # Model unavailable or historical links without deleting accepted task data.
    if boundary == "missing":
        control._conn.execute(
            "UPDATE platform_goal_task_links SET dependencies_json = ? WHERE task_id = ?",
            ('["missing"]', tasks["B"]),
        )
    elif boundary == "other_revision":
        control._conn.execute("UPDATE platform_goals SET revision = 2 WHERE id = ?", (goal.id,))
        control._conn.execute(
            "UPDATE platform_goal_task_links SET goal_revision = 2 WHERE task_id = ?",
            (tasks["B"],),
        )
    else:
        other = goals.create({
            "objective": "Different goal", "idempotency_key": "different-goal",
            "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
        })
        control._conn.execute(
            "UPDATE platform_goal_task_links SET goal_id = ? WHERE task_id = ?",
            (other.id, tasks["A"]),
        )
    assert control.runnable_tasks(window.id, limit=1) == ()


@pytest.mark.parametrize("status", ["QUEUED", "INTERRUPTED"])
def test_runnable_limit_applies_after_waiting_tasks_within_one_goal(status):
    store, control, _, _, window, tasks = _launched_dependency_pair()
    store.set_state(tasks["A"], status)
    assert control.runnable_tasks(window.id, limit=1) == (tasks["A"],)
    assert control.runnable_tasks("another-window", limit=1) == ()


def test_dependency_selection_does_not_accept_cyclic_plans():
    _, _, _, goals = _services()
    goal = goals.create({
        "objective": "Reject cyclic plan", "idempotency_key": "cyclic-plan",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    with pytest.raises(TaskStoreError, match="cyclic_plan_task_dependencies"):
        goals.plan(goal.id, expected_revision=1, tasks=[
            {"id": "B", "title": "second", "instruction": "second", "dependencies": ["A"]},
            {"id": "A", "title": "first", "instruction": "first", "dependencies": ["B"]},
        ])

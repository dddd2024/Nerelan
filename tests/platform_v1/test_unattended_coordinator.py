from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _ready_fixture(store: TaskStore, task_id: str):
    store.transition_to(task_id, "PREPARING_WORKSPACE")
    store.transition_to(task_id, "RUNNING_FIXTURE")
    store.transition_to(task_id, "VALIDATING")
    store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
    return SimpleNamespace(success=True)


def test_coordinator_respects_dependencies_and_restart_does_not_duplicate(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "unattended-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = goals.create({
        "objective": "Run two dependent tasks", "idempotency_key": "coord-goal-1",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "first", "instruction": "do first"},
        {"id": "T002", "title": "second", "instruction": "do second", "dependencies": ["T001"]},
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    calls = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert len(calls) == 1
    assert coordinator.tick() == 1
    assert len(calls) == 2
    assert control.get_goal(goal.id).status == "COMPLETED"

    restarted = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert restarted.tick() == 0
    assert len(calls) == 2
    summary = autonomy.summary(window.id)
    assert summary["window"]["tasks_started"] == 2
    assert summary["window"]["tasks_completed"] == 2


def test_coordinator_is_inert_without_active_window(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=lambda task_id: None,
    )
    assert coordinator.tick() == 0
    assert coordinator.status()["active_window_id"] == ""

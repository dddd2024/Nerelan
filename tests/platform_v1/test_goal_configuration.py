"""Same-Goal configuration and atomic launch over the existing SQLite store."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Event

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.inbox_service import InboxService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
import reverse_agent.platform_v1.goal_service as goal_service_module


def setup(store):
    control = PlatformControlStore(store)
    service = GoalService(store=store, control_store=control)
    return control, service


@pytest.fixture
def services():
    store = TaskStore(":memory:")
    control, service = setup(store)
    goal = service.create({"objective": "Original objective", "repository": "owner/original",
                           "idempotency_key": "configuration", "executor_kind": "deterministic_fixture",
                           "orchestration_mode": "single"})
    yield store, control, service, goal
    store._conn.close()


def window(control, repository="owner/original"):
    now = datetime.now(timezone.utc)
    return AutonomyService(control_store=control, capabilities=CapabilityRegistry()).activate({
        "policy_id": "test-policy", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(), "repositories": [repository],
        "capabilities": ["execute_task", "validate_task"], "max_concurrent_tasks": 2,
        "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE",
    })


def configure(service, goal, **changes):
    return service.amend(goal.id, expected_revision=goal.revision, objective="Edited objective",
                         repository="owner/selected", executor_kind="opencode",
                         orchestration_mode="sequential_team", binding_ref="coding-selected", **changes)


def test_inbox_configuration_plan_edit_and_launch_preserve_exact_identity(services, monkeypatch):
    store, control, service, _ = services
    inbox = InboxService(control_store=control, goal_service=service)
    item = inbox.capture({"objective": "Captured idea", "repository": "owner/original"})
    promoted = inbox.promote(item.id)["goal"]
    goal = control.get_goal(promoted["id"])
    configured = configure(service, goal)
    assert configured.id == goal.id and configured.revision == 2
    plan = service.plan(goal.id, expected_revision=2).goal
    tasks = [dict(task, instruction="Implement the edited instruction") for task in plan.tasks]
    edited = service.plan(goal.id, expected_revision=2, tasks=tasks, acceptance_criteria=["Edited acceptance"]).goal
    assert edited.revision == 3
    with pytest.raises(TaskStoreError):
        service.approve(goal.id, expected_revision=2)
    service.approve(goal.id, expected_revision=3)
    monkeypatch.setattr(goal_service_module, "resolve_repository_workspace", lambda repository: None)
    active = window(control, "owner/selected")
    launched = service.launch(goal.id, expected_revision=3, window_id=active.id)
    assert launched.status == "RUNNING" and launched.id == promoted["id"]
    assert inbox.get_item(item.id).promoted_goal_id == launched.id
    task = store.get_task(control.list_goal_tasks(goal.id)[0]["task_id"])
    assert task.repository == "owner/selected" and task.executor_kind == "opencode"
    assert task.binding_ref == "coding-selected" and task.orchestration_mode == "sequential_team"
    assert "Implement the edited instruction" in task.title
    assert task.status == "QUEUED"
    assert service.launch(goal.id, expected_revision=3, window_id=active.id).id == goal.id
    assert store.count_tasks() == 1


@pytest.mark.parametrize("stage", ["DRAFT", "PLANNED", "APPROVED"])
def test_configuration_invalidates_plan_and_approval(services, stage):
    _, control, service, goal = services
    if stage != "DRAFT":
        service.plan(goal.id, expected_revision=1)
    if stage == "APPROVED":
        service.approve(goal.id, expected_revision=1, policy_ref="old-policy")
    configured = configure(service, goal)
    assert configured.status == "DRAFT" and configured.revision == 2
    assert not configured.tasks and not configured.artifact_digest
    assert configured.spec_markdown == configured.plan_markdown == configured.policy_ref == configured.window_id == ""
    with pytest.raises(TaskStoreError):
        service.approve(goal.id, expected_revision=1)
    assert control.get_goal(goal.id) == configured
    legacy = service.amend(goal.id, expected_revision=2, objective="Legacy objective edit")
    assert legacy.revision == 3 and legacy.repository == "owner/selected"
    assert legacy.binding_ref == "coding-selected" and legacy.executor_kind == "opencode"


def test_identical_configuration_is_idempotent_and_normalizes_existing_origin(services):
    store, _, service, goal = services
    updated = service.amend(goal.id, expected_revision=1, objective=goal.objective,
                            repository="https://github.com/owner/original.git")
    assert updated == goal
    changes = store._conn.total_changes
    assert service.amend(goal.id, expected_revision=1, objective=goal.objective, repository=goal.repository) == goal
    assert store._conn.total_changes == changes


@pytest.mark.parametrize("changes", [
    {"repository": "invalid"}, {"repository": "https://example.com/owner/repo"},
    {"executor_kind": "unknown"}, {"orchestration_mode": "unknown"},
    {"orchestration_mode": "sequential_team"}, {"binding_ref": "coding"},
    {"executor_kind": "opencode"}, {"executor_kind": "opencode", "binding_ref": "bad ref"},
    {"repository": 123},
])
def test_invalid_configuration_preserves_snapshot(services, changes):
    _, control, service, goal = services
    with pytest.raises(TaskStoreError):
        service.amend(goal.id, expected_revision=1, objective=goal.objective, **changes)
    assert control.get_goal(goal.id) == goal


@pytest.mark.parametrize("status", ["RUNNING", "COMPLETED", "BLOCKED", "INVALIDATED"])
def test_configuration_of_launched_or_terminal_goal_is_rejected(services, status):
    store, control, service, goal = services
    store._conn.execute("UPDATE platform_goals SET status = ? WHERE id = ?", (status, goal.id))
    before = control.get_goal(goal.id)
    with pytest.raises(TaskStoreError, match="goal_configuration_not_editable"):
        configure(service, before)
    assert control.get_goal(goal.id) == before


def test_partial_launch_records_block_configuration_mutation(services):
    store, control, service, goal = services
    task = store.create_task(title="Existing partial materialization")
    control.link_goal_task(goal.id, goal_revision=1, plan_task_id="T001", task_id=task.id, dependencies=(), seq=0)
    with pytest.raises(TaskStoreError, match="goal_configuration_not_editable"):
        configure(service, goal)
    assert control.get_goal(goal.id) == goal


def test_failed_launch_rolls_back_all_materialization_and_retry_is_idempotent(services, monkeypatch):
    store, control, service, goal = services
    service.plan(goal.id, expected_revision=1, tasks=[
        {"id": "A", "title": "Implement A", "instruction": "A"},
        {"id": "B", "title": "Verify B", "instruction": "B", "dependencies": ["A"]},
    ])
    approved = service.approve(goal.id, expected_revision=1)
    active = window(control)
    create = store.create_task
    count = [0]
    def fail_second(**kwargs):
        count[0] += 1
        if count[0] == 2:
            raise RuntimeError("injected materialization failure")
        return create(**kwargs)
    monkeypatch.setattr(store, "create_task", fail_second)
    with pytest.raises(RuntimeError, match="injected"):
        service.launch(goal.id, expected_revision=1, window_id=active.id)
    assert control.get_goal(goal.id) == approved
    for table in ["tasks", "idempotency_keys", "task_events", "platform_goal_task_links"]:
        assert store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    monkeypatch.setattr(store, "create_task", create)
    assert service.launch(goal.id, expected_revision=1, window_id=active.id).status == "RUNNING"
    assert service.launch(goal.id, expected_revision=1, window_id=active.id).status == "RUNNING"
    assert store.count_tasks() == 2 and len(control.list_goal_tasks(goal.id)) == 2


def test_concurrent_configuration_cannot_change_snapshot_during_launch(tmp_path, monkeypatch):
    path = str(tmp_path / "tasks.sqlite3")
    stores = [TaskStore(path), TaskStore(path)]
    control, service = setup(stores[0])
    other_control, other_service = setup(stores[1])
    goal = service.create({"objective": "Original", "repository": "owner/original", "idempotency_key": "race",
                           "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    service.plan(goal.id, expected_revision=1)
    service.approve(goal.id, expected_revision=1)
    active = window(control)
    materializing, amendment_started = Event(), Event()
    create = stores[0].create_task
    def gated_create(**kwargs):
        materializing.set()
        assert amendment_started.wait(10)
        return create(**kwargs)
    monkeypatch.setattr(stores[0], "create_task", gated_create)
    def amend():
        assert materializing.wait(10)
        amendment_started.set()
        with pytest.raises(TaskStoreError):
            configure(other_service, goal)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(amend)
            launched = service.launch(goal.id, expected_revision=1, window_id=active.id)
            future.result(timeout=10)
        assert launched.revision == 1 and launched.status == "RUNNING"
        task = stores[0].get_task(control.list_goal_tasks(goal.id)[0]["task_id"])
        assert task.repository == "owner/original" and task.executor_kind == "deterministic_fixture"
        assert other_control.get_goal(goal.id).repository == "owner/original"
    finally:
        for store in stores:
            store._conn.close()

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


@pytest.mark.parametrize("command,capability", [
    ("shell echo hello", "validate_task"),
    ("git_diff_check", "execute_task"),
    ("git_diff_check", "validate_task"),
])
def test_goal_rejects_retired_host_validation_command(command, capability):
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Check", "idempotency_key": "invalid-command"})
    with pytest.raises(TaskStoreError, match="unsupported_standalone_validation_command"):
        goals.plan(goal.id, expected_revision=1, tasks=[{
            "id": "CHECK001", "title": "Check", "instruction": "Check", "capability": capability,
            "validation_command_id": command}])


def test_retired_host_validation_contract_api_is_gone():
    from reverse_agent.platform_v1 import task_runtime, task_service
    from reverse_agent.platform_v1.task_execution import TaskExecutionService

    assert not hasattr(task_runtime, "HOST_VALIDATION_CONTRACT")
    assert not hasattr(task_runtime, "load_host_validation_contract")
    assert not hasattr(task_runtime, "task_operation")
    assert not hasattr(TaskExecutionService, "execute_host_validation")
    assert not hasattr(task_service._TaskHandler, "_dispatch_host_check")


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


def _strict_running_goal():
    store, control, autonomy, goals = _services()
    payload = _window_payload()
    payload.update(capabilities=["execute_task"], max_tasks=1,
                   max_concurrent_tasks=1, max_retries=0)
    window = autonomy.activate(payload)
    goal = _approve_strict_fixture(goals, "first")
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    return store, control, autonomy, goals, window, goal, task_id


def _approve_strict_fixture(goals, key):
    goal = goals.create({"objective": "Fixture", "idempotency_key": key,
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    goals.approve(goal.id, expected_revision=1)
    return goal


def test_strict_window_rejects_second_goal_without_materialization():
    store, control, _, goals, window, first, task_id = _strict_running_goal()
    second = _approve_strict_fixture(goals, "second")
    with pytest.raises(TaskStoreError, match="strict_window_requires_one_single_task_goal"):
        goals.launch(second.id, expected_revision=1, window_id=window.id)
    assert control.list_goal_tasks(second.id) == ()
    assert control.runnable_tasks(window.id) == (task_id,)
    control.claim_task(window_id=window.id, task_id=task_id, owner="fixture", lease_ms=1000)
    assert control.get_window(window.id).tasks_started == 1


def test_strict_window_preassociated_goal_launches_once_without_denied_writes():
    # Synthetic SQLite authority only; no production store or provider execution.
    store, control, autonomy, goals = _services()
    payload = _window_payload()
    payload.update(capabilities=["execute_task"], max_tasks=1,
                   max_concurrent_tasks=1, max_retries=0)
    window = autonomy.activate(payload)
    goal = goals.create({"objective": "Fixture", "idempotency_key": "preassociated",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
                         "window_id": window.id})
    goals.plan(goal.id, expected_revision=1)
    goals.approve(goal.id, expected_revision=1)
    assert control.get_goal(goal.id).window_id == window.id
    assert control.list_goal_tasks(goal.id) == ()

    running = goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert running.status == "RUNNING"
    links = control.list_goal_tasks(goal.id)
    assert len(links) == 1
    task_id = links[0]["task_id"]

    def execution_state():
        return tuple(tuple(tuple(row) for row in store._conn.execute(query).fetchall()) for query in (
            "SELECT * FROM tasks ORDER BY id",
            "SELECT * FROM platform_goal_task_links ORDER BY task_id",
            "SELECT * FROM platform_coordinator_claims ORDER BY task_id",
            "SELECT * FROM platform_budget_reservations ORDER BY task_id",
            "SELECT * FROM platform_usage_charges",
            "SELECT * FROM platform_autonomous_windows ORDER BY id",
        ))

    before = execution_state()
    assert goals.launch(goal.id, expected_revision=1, window_id=window.id) == running
    assert execution_state() == before
    second = _approve_strict_fixture(goals, "unrelated")
    for claimed in (False, True):
        if claimed:
            control.claim_task(window_id=window.id, task_id=task_id, owner="fixture", lease_ms=1000)
        before = execution_state()
        with pytest.raises(TaskStoreError, match="strict_window_requires_one_single_task_goal"):
            goals.launch(second.id, expected_revision=1, window_id=window.id)
        assert execution_state() == before
        assert control.list_goal_tasks(second.id) == ()
        assert control.get_goal(second.id).status == "APPROVED"
    with pytest.raises(TaskStoreError):
        control.claim_task(window_id=window.id, task_id=task_id, owner="again", lease_ms=1000)
    assert execution_state() == before
    assert control.get_window(window.id).tasks_started == 1
    assert control.get_window(window.id).retries_used == 0


@pytest.mark.parametrize("mutation", ["revision", "executor", "repository", "binding", "unknown"])
def test_strict_claim_rejects_unbound_task_without_spending(mutation):
    store, control, _, _, window, goal, task_id = _strict_running_goal()
    if mutation == "revision":
        store._conn.execute("UPDATE platform_goal_task_links SET goal_revision = 2 WHERE task_id = ?", (task_id,))
    elif mutation == "unknown":
        task_id = store.create_task(title="Legacy", repository=goal.repository,
                                    executor_kind="deterministic_fixture").id
    else:
        column, value = {"executor": ("executor_kind", "opencode"),
                         "repository": ("repository", "other/repo"),
                         "binding": ("binding_ref", "wrong-binding")}[mutation]
        store._conn.execute(f"UPDATE tasks SET {column} = ? WHERE id = ?", (value, task_id))
    with pytest.raises(TaskStoreError, match="strict_window_task_binding_mismatch"):
        control.claim_task(window_id=window.id, task_id=task_id, owner="fixture", lease_ms=1000)
    assert control.get_window(window.id).tasks_started == 0
    if mutation != "unknown":
        assert control.runnable_tasks(window.id) == ()
    assert store._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations").fetchone()[0] == 0


def test_strict_binding_does_not_spill_to_next_window():
    _, control, autonomy, goals, first_window, _, first_task = _strict_running_goal()
    control.stop_window(first_window.id)
    payload = _window_payload()
    payload.update(policy_id="owner-window-2", capabilities=["execute_task"],
                   max_tasks=1, max_concurrent_tasks=1, max_retries=0)
    window = autonomy.activate(payload)
    goal = _approve_strict_fixture(goals, "next-window")
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    with pytest.raises(TaskStoreError, match="strict_window_task_binding_mismatch"):
        control.claim_task(window_id=window.id, task_id=first_task, owner="fixture", lease_ms=1000)
    assert control.runnable_tasks(window.id) == (task_id,)
    control.claim_task(window_id=window.id, task_id=task_id, owner="fixture", lease_ms=1000)


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


def test_goal_fit_plan_detail_use_host_account_estimator_without_reservations(monkeypatch):
    import json
    import time
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import quota_reservation
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    from tests.platform_v1.test_quota_reservation import quota_evidence
    store, control, _, goals = _services()
    host = object.__new__(CombinedTrustedHost)
    host._task_store = store
    host._control_store = control
    host._goal_service = goals
    host._store = SimpleNamespace(
        list_bindings_public=lambda: [{"binding_id": "b", "connection_id": "c", "model_id": "fixture"}],
        get_connection_public=lambda _: {"connection_id": "c", "account_ref": "a", "auth_method": "external_cli_session"})
    monkeypatch.setattr(host, "_runnable_bindings", lambda: {"b"})
    goals.quota_forecaster = host._goal_quota_fit
    monkeypatch.setattr(quota_reservation.pricing, "equivalent_cost", lambda *args: {"usd": 30})
    now = time.time()
    observed = quota_evidence(weekly=40, now=now)
    for w in observed["windows"]:
        w["capacity_units"] = {"low": 100}
    store._conn.execute("INSERT INTO platform_quota_observations VALUES (?, ?, ?)",
                        ("a", str(now), json.dumps(observed)))
    goal = goals.create({"objective": "Forecast two tasks", "idempotency_key": "fit",
                         "orchestration_mode": "single", "binding_ref": "b"})
    tables = ("platform_quota_admissions", "platform_quota_observations", "platform_budget_reservations", "platform_quota_calibrations")
    before = {t: [tuple(r) for r in store._conn.execute("SELECT * FROM " + t)] for t in tables}
    planned = goals.plan(goal.id, expected_revision=goal.revision, tasks=[
        {"id": "T1", "title": "First", "instruction": "First"},
        {"id": "T2", "title": "Second", "instruction": "Second"}])
    fit = planned.quota_fit
    assert fit["status"] == "needs_a_reset"
    assert fit["accounts"]["a"]["blocking_windows"] == ["weekly"]
    assert fit["tasks"][0]["need"]["estimate"]["cold_start"]
    assert fit["tasks"][0]["need"]["estimate"]["uncertain"]
    assert '"status": "needs_a_reset"' in planned.goal.plan_markdown
    detail = goals.detail(goal.id)
    assert detail["quota_fit"]["status"] == "needs_a_reset"
    assert detail["account_accounting"] == {}
    assert before == {t: [tuple(r) for r in store._conn.execute("SELECT * FROM " + t)] for t in tables}
    store._conn.execute("DELETE FROM platform_quota_observations")
    assert goals.detail(goal.id)["quota_fit"]["status"] == "UNKNOWN"


def test_goal_fit_default_unknown_is_explicit():
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Unobserved", "idempotency_key": "unknown-fit"})
    planned = goals.plan(goal.id, expected_revision=goal.revision)
    assert planned.quota_fit["status"] == "UNKNOWN"
    assert goals.detail(goal.id)["quota_fit"]["status"] == "UNKNOWN"


def test_goal_forecast_router_does_not_discover_refresh_or_probe(monkeypatch, tmp_path):
    from tests.platform_v1.test_model_router import fixture_host
    from reverse_agent.platform_v1.goal_service import PlannedTask
    host = fixture_host(monkeypatch, tmp_path)
    store, control, _, goals = _services()
    host._task_store = store
    host._control_store = control
    host._goal_service = goals
    def forbidden(*args, **kwargs):
        pytest.fail("forecast attempted a refresh, discovery, quota read or availability probe")
    for name in ("_routing_bind_discovered", "_routing_refresh_quota_for_signal", "_subscription_quotas",
                 "_quota_check", "_probe_routing_binding"):
        monkeypatch.setattr(host, name, forbidden)
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    monkeypatch.setattr(host, "_routing_availability",
                        CombinedTrustedHost._routing_availability.__get__(host))
    decision = host._resolve_task_model(PlannedTask("T1", "Forecast", "Implement", difficulty=3), forecast=True)
    assert decision["binding_ref"] in {"cheap", "mid", "strong"}
    assert not hasattr(host, "_availability_cache")
    assert store._conn.execute("SELECT COUNT(*) FROM platform_quota_admissions").fetchone()[0] == 0


def test_goal_detail_surfaces_existing_account_accounting(monkeypatch):
    _, control, _, goals = _services()
    goal = goals.create({"objective": "Accounting projection", "idempotency_key": "account-projection",
                         "window_id": "fixture-window"})
    expected = {"a": {"reserved": {"weekly": 5}, "actual": {"weekly": None}, "unknown_count": 1}}
    calls = []
    def summary(window_id):
        calls.append(window_id)
        return expected
    monkeypatch.setattr(control, "account_budget_summary", summary)
    assert goals.detail(goal.id)["account_accounting"] == expected
    assert calls == ["fixture-window"]


def test_forecast_replays_availability_without_changing_persisted_cache(tmp_path):
    import time
    from types import SimpleNamespace
    from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
    from reverse_agent.platform_v1 import model_availability
    host = object.__new__(CombinedTrustedHost)
    host._store = SimpleNamespace(_state_path=None)
    cache = model_availability.AvailabilityCache(tmp_path / "availability.json")
    host._availability_cache = cache
    binding = {"binding_id": "b", "model_id": "m", "executor_id": "opencode"}
    connection = {"connection_id": "c", "auth_method": "api_key"}
    now = time.time()
    cache.remember(binding, connection, model_availability.observation(now=now - 100, success=True))
    before = cache.path.read_bytes()
    result = host._routing_availability(binding, connection, allow_paid=False, cost_class="free",
        readonly=True, runnable=True, history=[{"updated_at": datetime.fromtimestamp(now - 10, timezone.utc).isoformat(),
            "status": "FAILED", "failure_classification": "MODEL_UNAVAILABLE", "failure_detail": "model_not_found"}])
    assert result["state"] == "UNAVAILABLE"
    assert cache.path.read_bytes() == before
    assert cache.check(binding, connection)["state"] == "AVAILABLE"


def test_goal_lists_skip_the_forecast_and_detail_runs_it_outside_the_store_lock():
    """A polled list must not route every task of every goal (run host, 2026-11-11)."""
    store, _, _, goals = _services()
    seen = []

    def forecaster(goal, tasks):
        # RLock._is_owned() is true only for the thread holding the lock.
        seen.append(store._lock._is_owned())
        return {"status": "ok"}

    goal = goals.create({"objective": "Listed", "idempotency_key": "listed"})
    goals.plan(goal.id, expected_revision=goal.revision)
    goals.quota_forecaster = forecaster

    assert [item["quota_fit"] for item in goals.list()] == [None]
    assert [item["quota_fit"] for item in goals.list_page()["goals"]] == [None]
    assert seen == []
    assert goals.detail(goal.id)["quota_fit"] == {"status": "ok"}
    assert seen == [False]

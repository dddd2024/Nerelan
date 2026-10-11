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


@pytest.mark.parametrize("durable", [False, True])
def test_explicit_host_check_goal_freezes_intent_and_never_dispatches_model(tmp_path, monkeypatch, durable):
    """Synthetic authority fixture; the checker itself operates on a real Git repository."""
    import subprocess
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter, load_host_validation_contract
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin",
                    "https://github.com/dddd2024/reverse-agent.git"], check=True)
    (tmp_path / "source.txt").write_bytes(b"baseline\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "source.txt"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "fixture"], check=True, capture_output=True)
    head = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(tmp_path))
    store, control, autonomy, goals = _services()
    payload = _window_payload()
    payload["capabilities"] = ["validate_task"]
    window = autonomy.activate(payload)
    monkeypatch.setattr(control, "window_policy_binding", lambda unused: {
        "canonical_policy": {"fixture_only": True}, "authority": {
            "workspace_path": str(tmp_path), "head_sha": head, "validation_paths": ["source.txt"],
            "validation_command_ids": ["git_diff_check"], "plan_task_id": "CHECK001",
            "goal_idempotency_key": "host-check-fixture"}}, raising=False)
    goal = goals.create({"objective": "Check patch hygiene", "idempotency_key": "host-check-fixture",
                         "orchestration_mode": "single", "executor_kind": "opencode"})
    planned = goals.plan(goal.id, expected_revision=1, tasks=[{
        "id": "CHECK001", "title": "Host checker", "instruction": "Check pinned source only",
        "capability": "validate_task", "validation_command_id": "git_diff_check"}]).goal
    assert planned.tasks[0]["validation_command_id"] == "git_diff_check"
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    frozen = load_host_validation_contract(store.get_task(task_id))
    assert frozen["allowed_paths"] == ["source.txt"] and frozen["base_sha"] == head
    router = ExecutorRouter()
    monkeypatch.setattr(router, "dispatch_execute", lambda **unused: pytest.fail("model executor reached"))
    monkeypatch.setattr(router, "create_executor", lambda **unused: pytest.fail("model binding reached"))
    service = TaskExecutionService(store=store, router=router)
    if durable:
        task = store.get_task(task_id)
        lease = store._acquire_durable_lease(task_id=task_id, execution_id=task.execution_id,
            lease_owner="fixture-owner", execution_authority_sha=head, planning_sha=head, task_status="QUEUED")
        outcome = service.execute_host_validation(task_id, lease=lease)
        observed = store.get_latest_durable_run_observation(task_id)
        assert observed.accepted_checkpoint == "POST_VALIDATION"
        store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
    else:
        outcome = service.execute(task_id, workspace_root=str(tmp_path))
    assert outcome.success and outcome.validation_command_id == "git_diff_check"
    final = store.get_task(task_id)
    assert final.status == "READY_FOR_REVIEW"
    assert any(row["value"] == "host_validation" for row in final.evidence_refs)
    assert any(event.metadata.get("model_execution_skipped") for event in store.get_events(task_id))
    assert goals.detail(goal.id)["completion_scope"] == "EXECUTION_ONLY"


@pytest.mark.parametrize("command,capability", [("shell echo hello", "validate_task"), ("git_diff_check", "execute_task")])
def test_goal_rejects_caller_selected_non_fixed_host_command(command, capability):
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Check", "idempotency_key": "invalid-command"})
    with pytest.raises(TaskStoreError, match="unsupported_standalone_validation_command"):
        goals.plan(goal.id, expected_revision=1, tasks=[{
            "id": "CHECK001", "title": "Check", "instruction": "Check", "capability": capability,
            "validation_command_id": command}])


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

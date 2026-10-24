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
    _persisted_host_result(tmp_path, monkeypatch, durable=durable)


def _persisted_host_result(tmp_path, monkeypatch, *, durable=True, strict=False, failed=False):
    """Synthetic SQLite authority; the checker uses a disposable Git repository."""
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
    if strict:
        # Synthetic authority only: exercise recovery under the strict admission shape.
        store._conn.execute(
            "UPDATE platform_autonomous_windows SET capabilities_json = ?, max_tasks = 1, "
            "max_concurrent_tasks = 1, max_retries = 0 WHERE id = ?",
            ('["execute_task"]', window.id))
        assert control.is_strict_owner_window(control.get_window(window.id))
        control.claim_task(window_id=window.id, task_id=task_id, owner="original", lease_ms=1000)
    if failed:
        (tmp_path / "source.txt").write_bytes(b"baseline trailing whitespace   \n")
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
    assert outcome.success is (not failed)
    assert outcome.validation_command_id == "git_diff_check"
    final = store.get_task(task_id)
    assert final.status == ("FAILED" if failed else "READY_FOR_REVIEW")
    assert any(row["value"] == "host_validation" for row in final.evidence_refs)
    assert any(event.metadata.get("model_execution_skipped") for event in store.get_events(task_id))
    if not failed:
        assert goals.detail(goal.id)["completion_scope"] == "EXECUTION_ONLY"
    control.refresh_goal_status(goal.id)
    monkeypatch.setattr(control, "window_policy_binding",
                        PlatformControlStore.window_policy_binding.__get__(control))
    return store, control, window, goal, task_id


@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("mutation", [None, "task", "revision", "executor", "missing_result", "new_work"])
def test_strict_terminal_goal_recovers_only_original_persisted_result(tmp_path, monkeypatch, failed, mutation):
    store, control, window, goal, task_id = _persisted_host_result(
        tmp_path, monkeypatch, strict=True, failed=failed)
    assert control.get_goal(goal.id).status == ("BLOCKED" if failed else "COMPLETED")
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms = 0 WHERE task_id = ?", (task_id,))
    task = store.get_task(task_id)
    store.append_usage_observation(task_id, observation_id="original-unknown", execution_id=task.execution_id,
        role="executor", model_id="fixture", provider_id="", source_kind="fixture", source_id="original", status="UNKNOWN")
    if mutation == "task":
        task_id = store.create_task(title="Unrelated", repository=goal.repository, executor_kind=goal.executor_kind).id
    elif mutation == "revision":
        store._conn.execute("UPDATE platform_goal_task_links SET goal_revision = 2 WHERE task_id = ?", (task_id,))
    elif mutation == "executor":
        store._conn.execute("UPDATE tasks SET executor_kind = 'codex' WHERE id = ?", (task_id,))
    elif mutation == "missing_result":
        store._conn.execute("UPDATE tasks SET validation_exit_code = NULL WHERE id = ?", (task_id,))
    elif mutation == "new_work":
        store.set_state(task_id, "QUEUED")
    if mutation:
        assert task_id not in control.runnable_tasks(window.id)
        with pytest.raises(TaskStoreError, match="strict_window_task_binding_mismatch"):
            control.claim_task(window_id=window.id, task_id=task_id, owner="recovery", lease_ms=1000)
        reservation = store._conn.execute("SELECT * FROM platform_budget_reservations").fetchone()
        assert reservation["state"] == "ACTIVE" and reservation["claim_epoch"] == 1
    else:
        assert control.can_complete_host_claim(window_id=window.id, task_id=task_id)
        assert control.runnable_tasks(window.id) == (task_id,)
        epoch, _ = control.claim_task(window_id=window.id, task_id=task_id, owner="recovery", lease_ms=1000)
        assert epoch == 2
        assert store.get_task(task_id) == task
        control.complete_task_claim(window_id=window.id, task_id=task_id, owner="recovery", epoch=epoch, result="persisted")
        with pytest.raises(TaskStoreError, match="coordinator_claim_fenced"):
            control.complete_task_claim(window_id=window.id, task_id=task_id, owner="recovery", epoch=epoch, result="persisted")
        reservation = store._conn.execute("SELECT * FROM platform_budget_reservations").fetchone()
        assert reservation["state"] == "UNKNOWN" and reservation["claim_epoch"] == epoch
        assert store._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == 1
        assert control.get_window(window.id).tasks_completed == 1
        assert control.get_window(window.id).unknown_observation_count == 1
        assert control.runnable_tasks(window.id) == ()
        with pytest.raises(TaskStoreError):
            control.claim_task(window_id=window.id, task_id=task_id, owner="again", lease_ms=1000)
    assert store._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations").fetchone()[0] == 1
    assert control.get_window(window.id).tasks_started == 1
    assert control.get_window(window.id).retries_used == 0


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

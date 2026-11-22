from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
import reverse_agent.platform_v1.control_store as control_store_module
import reverse_agent.platform_v1.goal_service as goal_service_module
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)
from test_contract_miss_fixup import case  # noqa: F401 (fixture)


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


# --- #1596: a stalled attempt retries on another binding; host termination resumes ------

from test_contract_miss_fixup import case, destination, git, wrong_tree  # noqa: E402,F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: E402,F401 (fixture)
import reverse_agent.platform_v1.contract_recovery as recovery  # noqa: E402

STALLED = "executor_stalled"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail_stalled(store, task, root, *, classification=STALLED, age=None):
    store.add_event(task.id, event_type="WORKSPACE_READY", title="Workspace ready",
                    metadata={"execution_id": task.execution_id, "workspace": str(root)})
    store.add_event(task.id, event_type="MODEL_SELECTED", title="Model selected", description="fixture",
                    metadata={"binding_ref": task.binding_ref, "reason": "fixture", "context_window": 128000})
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification=?, failure_detail=?, "
                        "updated_at=? WHERE id=?", (classification, "opencode_stalled:900", age or _now(), task.id))
    store._conn.commit()


def _stall_resolver(calls, choice):
    def resolve(plan_task, *, goal, failed_binding="", failed_tier=None, avoid_bindings=(), **kwargs):
        calls.append({"failed_binding": failed_binding, "avoid_bindings": tuple(avoid_bindings)})
        if isinstance(choice, Exception):
            raise choice
        return dict(choice)
    return resolve


OTHER_BINDING = {"binding_ref": "other-upstream", "executor_kind": "opencode", "model_id": "zai/glm-5.3",
                 "tier": 3, "reason": "cheapest_qualifying", "context_window": 128000,
                 "liveness": {"avoided_bindings": ["local-test-binding"], "fallback": False}}


def test_stalled_step_retries_at_once_on_another_binding_with_the_retained_tree(case, tmp_path):
    root, base, store, control, service, goal, _, task = case
    wrong_tree(root)
    _fail_stalled(store, task, root)  # just failed: a same-binding retry would still be backing off
    calls = []
    service.task_resolver = _stall_resolver(calls, OTHER_BINDING)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == f"{goal_service_module.HOST_RETRY_REASON}:{STALLED}:rerouted"
    assert calls == [{"failed_binding": "", "avoid_bindings": (task.binding_ref,)}]
    retry = store.get_task(step["to_task_id"])
    assert (retry.binding_ref, retry.executor_kind) == ("other-upstream", "opencode")
    # Still a free, not-the-model's-fault retry inside the shared per-step cap.
    history = control.list_task_escalations(goal.id)
    assert goal_service_module._free_retries_used(history, "T001") == 1
    assert goal_service_module._routing_retries_spent(history) == 0
    events = store.get_events(retry.id)
    note = next(e for e in events if e.title == "Retry on another binding after a stall")
    assert note.metadata["liveness_retry"] == "rerouted" and note.metadata["from_binding"] == task.binding_ref
    assert any(e.type == "MODEL_SELECTED" and e.metadata.get("binding_ref") == "other-upstream" for e in events)
    # The retained tree moves with the step, although the binding changed.
    assert recovery.recovery_input(retry)["source_task_id"] == task.id
    dest = destination(case, tmp_path)
    recovery.restore_failed_tree(store, retry.id, worktree=dest)
    assert (dest / "wrong_name.py").exists()
    assert git(dest, "rev-parse", "HEAD") == base


def test_a_second_stall_avoids_every_binding_the_step_stalled_on(case, monkeypatch):
    root, _, store, control, service, goal, _, task = case
    _fail_stalled(store, task, root)
    calls = []
    service.task_resolver = _stall_resolver(calls, OTHER_BINDING)
    [step] = service.escalate_failed_tasks(goal.id)
    _fail_stalled(store, store.get_task(step["to_task_id"]), root)
    service.task_resolver = _stall_resolver(calls, dict(OTHER_BINDING, binding_ref="third"))
    [step2] = service.escalate_failed_tasks(goal.id)
    assert calls[-1]["avoid_bindings"] == ("other-upstream", task.binding_ref)
    assert store.get_task(step2["to_task_id"]).binding_ref == "third"


@pytest.mark.parametrize("choice,note", [
    (dict(OTHER_BINDING, binding_ref="local-test-binding"), "no_eligible_binding"),
    (dict(OTHER_BINDING, binding_ref="cooling", liveness={"fallback": True}), "only_cooling_bindings"),
    (TaskStoreError("no_runnable_model"), "selection_failed:no_runnable_model"),
    (None, "no_router"),
])
def test_no_alternative_retries_the_same_binding_after_backoff_and_says_why(case, monkeypatch, choice, note):
    root, _, store, _, service, goal, _, task = case
    _fail_stalled(store, task, root)
    calls = []
    service.task_resolver = None if choice is None else _stall_resolver(calls, choice)
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()  # backing off
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    assert len(calls) == (0 if choice is None else 1)  # looked once, not on every tick
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == f"{goal_service_module.HOST_RETRY_REASON}:{STALLED}:no_alternative"
    retry = store.get_task(step["to_task_id"])
    assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)
    status = next(e for e in store.get_events(retry.id) if e.title == "Retry on the same binding after a stall")
    assert status.metadata["liveness_retry"] == "no_alternative" and status.metadata["liveness_detail"] == note
    assert note in status.description


def test_host_termination_still_resumes_the_same_model_without_routing(case):
    root, _, store, _, service, goal, _, task = case
    _fail_stalled(store, task, root, classification=goal_service_module.EXECUTOR_TERMINATED,
                  age="2000-01-01T00:00:00Z")

    def forbidden(*args, **kwargs):
        raise AssertionError("a stopped agent resumes on its own binding")
    service.task_resolver = forbidden
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == f"{goal_service_module.HOST_RETRY_REASON}:{goal_service_module.EXECUTOR_TERMINATED}"
    retry = store.get_task(step["to_task_id"])
    assert (retry.binding_ref, retry.executor_kind) == (task.binding_ref, task.executor_kind)
    assert not any("stall" in e.title for e in store.get_events(retry.id))


def test_stall_reroute_floor_is_the_strongest_tier_the_step_was_routed_at(case):
    root, _, store, _, service, goal, _, task = case
    _fail_stalled(store, task, root)
    store.add_event(task.id, event_type="MODEL_SELECTED", title="Escalated", description="fixture",
                    metadata={"binding_ref": task.binding_ref, "tier": 5, "reason": "escalation_higher_tier"})
    seen = []

    def resolve(plan_task, *, goal, avoid_bindings=(), stall_tier=None, **kwargs):
        seen.append(stall_tier)
        return dict(OTHER_BINDING, tier=5)
    service.task_resolver = resolve
    [step] = service.escalate_failed_tasks(goal.id)
    assert seen == [5] and step["reason"].endswith(":rerouted")


def test_stall_reroute_never_accepts_a_model_below_the_stall_tier(case, monkeypatch):
    # #1601 review (Codex P2): the stalled binding itself unavailable, only a weaker model left.
    root, _, store, _, service, goal, _, task = case
    _fail_stalled(store, task, root)
    store.add_event(task.id, event_type="MODEL_SELECTED", title="Escalated", description="fixture",
                    metadata={"binding_ref": task.binding_ref, "tier": 5, "reason": "escalation_higher_tier"})
    service.task_resolver = lambda plan_task, *, goal, **kwargs: dict(OTHER_BINDING, tier=2)
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"].endswith(":no_alternative")
    assert store.get_task(step["to_task_id"]).binding_ref == task.binding_ref


def test_backoff_memory_is_dropped_once_the_step_moves_on(case, monkeypatch):
    root, _, store, _, service, goal, _, task = case
    _fail_stalled(store, task, root)
    calls = []
    service.task_resolver = _stall_resolver(calls, dict(OTHER_BINDING, binding_ref=task.binding_ref))
    assert service.escalate_failed_tasks(goal.id) == ()
    assert service._stall_routes_checked == {task.id: goal.id}
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"].endswith(":no_alternative")
    service.escalate_failed_tasks(goal.id)  # the stalled attempt is no longer the step's failed link
    assert service._stall_routes_checked == {}
    # The memory is bounded even if goals never come back to prune it.
    monkeypatch.setattr(goal_service_module, "STALL_ROUTES_CHECKED_LIMIT", 2)
    service._stall_routes_checked.update({"a": "g1", "b": "g1", "c": "g1"})
    service._prune_stall_routes(goal.id)
    assert list(service._stall_routes_checked) == ["b", "c"]


def test_server_session_error_escalates_while_local_session_missing_stays_blocked(case):
    """#1718: server_session_error is an OpenCode turn error and must retry, unlike review_session_missing."""
    _, _, store, control, service, goal, _, task = case
    store.add_event(
        task.id,
        event_type="MODEL_SELECTED",
        title="Model selected",
        description="fixture",
        metadata={"binding_ref": task.binding_ref, "tier": 2, "context_window": 128000},
    )
    store._conn.execute(
        "UPDATE tasks SET status='FAILED', failure_classification='server_session_error', "
        "failure_detail='opencode_server:server_session_error' WHERE id=?",
        (task.id,),
    )
    store._conn.commit()
    calls = []
    service.task_resolver = _stall_resolver(calls, OTHER_BINDING)

    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "failed:server_session_error"
    assert calls == [{"failed_binding": task.binding_ref, "avoid_bindings": ()}]
    retry = store.get_task(step["to_task_id"])
    assert retry.binding_ref == "other-upstream"
    assert control.get_goal(goal.id).status == "RUNNING"

    store._conn.execute(
        "UPDATE tasks SET status='FAILED', failure_classification='review_session_missing', "
        "failure_detail='review_session_missing' WHERE id=?",
        (retry.id,),
    )
    store._conn.commit()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert control.get_goal(goal.id).status == "BLOCKED"


def _strand(store, task, *, status="INTERRUPTED", classification="", lease_ms=1, operation_state=None,
            operation_key="opencode_dispatch", external_id="", recovery="orphan_stale_lease"):
    """A redeploy-stranded attempt: its durable run, lease and (optionally) an external call (#1515)."""
    now = "2026-11-14T06:00:00Z"
    store._conn.execute(
        "INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_owner, lease_epoch, "
        "lease_expiry_ms, recovery_classification, created_at, updated_at) "
        "VALUES (?, ?, ?, '', 'old-host', 1, ?, ?, ?, ?)",
        (f"run-{task.id}", task.id, task.execution_id, lease_ms, recovery, now, now))
    if operation_state is not None:
        store._conn.execute(
            "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
            "idempotency_key, request_digest, state, external_operation_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'digest', ?, ?, ?, ?)",
            (f"op-{task.id}", f"run-{task.id}", task.id, operation_key, f"idem-{task.id}", operation_state,
             external_id, now, now))
    store._conn.execute("UPDATE tasks SET status=?, failure_classification=?, updated_at=? WHERE id=?",
                        (status, classification, "2000-01-01T00:00:00Z", task.id))
    store._conn.commit()


def test_owner_retry_recovers_an_interrupted_step_after_a_redeploy_strand(case):
    """#1515: an INTERRUPTED step with no live lease, claim or unresolved call is Owner-retryable,
    and the stranded attempt is closed in the same transaction so it never runs beside the retry."""
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, operation_state="SUCCESS")
    result = service.owner_retry(goal.id, "T001", expected_revision=control.get_goal(goal.id).revision)
    assert result["reason"] == goal_service_module.OWNER_RETRY_REASON
    assert result["from_task_id"] == task.id
    retry = store.get_task(result["to_task_id"])
    assert retry.status == "QUEUED"
    [link] = control.list_goal_tasks(goal.id)
    assert link["task_id"] == retry.id
    source = store.get_task(task.id)
    assert source.status == "FAILED"
    assert source.failure_classification == goal_service_module.OWNER_RETRY_SUPERSEDED


def test_owner_retry_refuses_an_interrupted_step_with_a_live_lease(case):
    """#1515: with a live lease the old run may still be executing, so the Owner retry is refused."""
    import time as _time
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, lease_ms=int(_time.time() * 1000) + 600000)
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_lease_live"):
        service.owner_retry(goal.id, "T001", expected_revision=control.get_goal(goal.id).revision)
    assert store.count_tasks() == count and store.get_task(task.id).status == "INTERRUPTED"


@pytest.mark.parametrize("state", ["PENDING", "UNKNOWN"])
@pytest.mark.parametrize("status,classification", [("INTERRUPTED", ""), ("FAILED", "host_version_changed")])
def test_owner_retry_holds_a_stranded_step_whose_external_call_is_unresolved(case, state, status, classification):
    """Review blocker on 952b366f: after the old lease expired, an unresolved call must not be
    bypassed by a fresh QUEUED task under a new id; the plan link stays and nothing is replayed."""
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, status=status, classification=classification, operation_state=state)
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_external_operation_unresolved"):
        service.owner_retry(goal.id, "T001", expected_revision=control.get_goal(goal.id).revision)
    assert store.count_tasks() == count
    [link] = control.list_goal_tasks(goal.id)
    assert link["task_id"] == task.id
    assert store.get_task(task.id).status == status
    assert not control.list_task_escalations(goal.id)
    [operation] = store._conn.execute("SELECT state FROM durable_external_operations WHERE task_id=?",
                                      (task.id,)).fetchall()
    assert operation["state"] == state


def test_owner_retry_recheck_inside_the_transaction_holds_a_call_recorded_while_routing(case, monkeypatch):
    """The unresolved-call check is repeated under the write lock: a call recorded after the first
    check (while the model was being routed) still refuses the retry."""
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task)
    resolver = service.roster_resolver

    def routing_while_a_call_lands(role):
        store._conn.execute(
            "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
            "idempotency_key, request_digest, state, created_at, updated_at) VALUES "
            "('late-op', ?, ?, 'opencode_dispatch', 'late-idem', 'digest', 'PENDING', 'x', 'x')",
            (f"run-{task.id}", task.id))
        return resolver(role)
    monkeypatch.setattr(service, "roster_resolver", routing_while_a_call_lands)
    count = store.count_tasks()
    with pytest.raises(TaskStoreError, match="owner_retry_external_operation_unresolved"):
        service.owner_retry(goal.id, "T001", expected_revision=control.get_goal(goal.id).revision)
    assert store.count_tasks() == count and store.get_task(task.id).status == "INTERRUPTED"


def test_owner_retry_still_refuses_a_running_step(case):
    """#1515 does not widen Owner retry to non-stopped steps: RUNNING is refused."""
    _, _, _store, _control, service, goal, _window, _task = case
    with pytest.raises(TaskStoreError, match="owner_retry_step_not_stopped"):
        service.owner_retry(
            goal.id, "T001",
            expected_revision=service.control_store.get_goal(goal.id).revision)


def test_host_version_changed_retries_without_spending_max_retries(case, monkeypatch):
    """#1515: a redeploy-closed attempt is a host fault: the same model retries (decision B)
    with no routing retries left, and it is not capability evidence."""
    from reverse_agent.platform_v1 import model_profiles
    _, _, store, control, service, goal, window, task = case
    store._conn.execute("UPDATE platform_autonomous_windows SET max_retries=0 WHERE id=?", (window.id,))
    _strand(store, task, status="FAILED", classification="host_version_changed")
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    profile = model_profiles.compute_agent_profiles(store).get(task.binding_ref, {"attempts": 0, "failed": 0})
    assert profile["attempts"] == 0 and profile["failed"] == 0
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "host_retry:host_version_changed"
    retry = store.get_task(step["to_task_id"])
    assert retry.binding_ref == task.binding_ref and retry.status == "QUEUED"
    assert goal_service_module._routing_retries_spent(control.list_task_escalations(goal.id)) == 0


@pytest.mark.parametrize("state", ["PENDING", "UNKNOWN"])
def test_host_version_changed_with_an_unresolved_call_stays_parked(case, monkeypatch, state):
    """No automatic replacement while the redeploy-closed attempt's call is unresolved:
    one typed hold event, no new task, the plan link unchanged."""
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, status="FAILED", classification="host_version_changed", operation_state=state)
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    [link] = control.list_goal_tasks(goal.id)
    assert link["task_id"] == task.id
    holds = [e for e in store.get_events(task.id)
             if e.type == "MODEL_SELECTION_FAILED" and e.metadata.get("reason") == "external_operation_unresolved"]
    assert len(holds) == 1 and holds[0].metadata["hold"] == f"op-{task.id}:{state}"


def _local_call(task):
    return f"single-exec-{task.id}"


def _settled_events(store, task):
    return [e for e in store.get_events(task.id)
            if e.type == "MODEL_SELECTION_FAILED" and e.metadata.get("reason") == "abandoned_host_restart"]


def test_host_version_changed_settles_its_dead_local_call_and_retries(case, monkeypatch):
    """#1515/#1528: a redeploy-closed OpenCode attempt whose only unresolved call is its own local
    execution, on a run a later host reconciled, is settled as a failure and retries as a host fault."""
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, status="FAILED", classification="host_version_changed", operation_state="PENDING",
            operation_key=_local_call(task))
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    [step] = service.escalate_failed_tasks(goal.id)
    assert step["reason"] == "host_retry:host_version_changed"
    assert store.get_task(step["to_task_id"]).status == "QUEUED"
    [operation] = store._conn.execute(
        "SELECT state, result_state FROM durable_external_operations WHERE task_id=?", (task.id,)).fetchall()
    assert (operation["state"], operation["result_state"]) == ("RECONCILED", "failure")
    [event] = _settled_events(store, task)
    assert event.metadata["operation_id"] == f"op-{task.id}"
    assert not [e for e in store.get_events(task.id) if e.metadata.get("reason") == "external_operation_unresolved"]
    service.escalate_failed_tasks(goal.id)
    assert len(_settled_events(store, task)) == 1


def test_owner_retry_settles_a_dead_local_call_of_a_redeploy_closed_step(case):
    _, _, store, control, service, goal, _window, task = case
    _strand(store, task, status="FAILED", classification="host_version_changed", operation_state="PENDING",
            operation_key=_local_call(task))
    result = service.owner_retry(goal.id, "T001", expected_revision=control.get_goal(goal.id).revision)
    assert result["from_task_id"] == task.id
    assert store.get_task(result["to_task_id"]).status == "QUEUED"
    assert len(_settled_events(store, task)) == 1


@pytest.mark.parametrize("variant", ["remote_id", "unknown_state", "interrupted", "not_orphaned",
                                     "native_executor", "live_lease", "second_call"])
def test_host_version_changed_keeps_the_hold_unless_the_call_is_surely_dead(case, monkeypatch, variant):
    """Only a PENDING local call with no external id, on an orphaned run of a FAILED host_version_changed
    OpenCode attempt with nothing live, is settled; every other unresolved call keeps the step parked."""
    import time as _time
    _, _, store, control, service, goal, _window, task = case
    kwargs = dict(status="FAILED", classification="host_version_changed", operation_state="PENDING",
                  operation_key=_local_call(task))
    if variant == "remote_id":
        kwargs["external_id"] = "remote-123"
    elif variant == "unknown_state":
        kwargs["operation_state"] = "UNKNOWN"
    elif variant == "interrupted":
        kwargs.update(status="INTERRUPTED", classification="")
    elif variant == "not_orphaned":
        kwargs["recovery"] = "normal"
    elif variant == "live_lease":
        kwargs["lease_ms"] = int(_time.time() * 1000) + 600000
    _strand(store, task, **kwargs)
    if variant == "native_executor":
        store._conn.execute("UPDATE tasks SET executor_kind='codex' WHERE id=?", (task.id,))
    if variant == "second_call":
        store._conn.execute(
            "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
            "idempotency_key, request_digest, state, created_at, updated_at) VALUES "
            "('other-op', ?, ?, 'opencode_dispatch', 'other-idem', 'digest', 'PENDING', 'x', 'x')",
            (f"run-{task.id}", task.id))
    store._conn.commit()
    monkeypatch.setattr(goal_service_module, "TRANSIENT_BACKOFF_SECONDS", 0)
    count = store.count_tasks()
    assert service.escalate_failed_tasks(goal.id) == ()
    assert store.count_tasks() == count
    assert not _settled_events(store, task)
    states = {row["state"] for row in store._conn.execute(
        "SELECT state FROM durable_external_operations WHERE task_id=?", (task.id,)).fetchall()}
    assert "RECONCILED" not in states


def test_detail_response_includes_generated_at_timestamp():
    """#1555: goal detail carries generated_at so the frontend can detect stale content."""
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Timestamp", "idempotency_key": "generated-at-detail",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    detail = goals.detail(goal.id)
    assert "generated_at" in detail
    assert detail["generated_at"].endswith("Z")
    # Re-read: timestamp should not be empty and should be a plausible ISO date.
    assert detail["generated_at"][:4] == "2099" or detail["generated_at"][:4] >= "2020"


def test_list_response_includes_generated_at_timestamp():
    """#1555: goal list responses carry generated_at for stale-state tracking."""
    _, _, _, goals = _services()
    goal = goals.create({"objective": "List timestamp", "idempotency_key": "generated-at-list",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    items = goals.list()
    assert len(items) == 1
    assert "generated_at" in items[0]
    assert items[0]["generated_at"].endswith("Z")


def test_list_page_response_includes_generated_at_timestamp():
    """#1555: paginated goal list responses carry generated_at."""
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Page timestamp", "idempotency_key": "generated-at-page",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    page = goals.list_page()
    assert page["total"] == 1
    assert "generated_at" in page["goals"][0]
    assert page["goals"][0]["generated_at"].endswith("Z")


def test_timeline_snapshot_includes_generated_at_timestamp():
    """#1555: timeline snapshot carries generated_at so polled timeline views can mark stale."""
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Timeline timestamp", "idempotency_key": "generated-at-timeline",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    snapshot = goals.timeline_snapshot(goal.id)
    assert "generated_at" in snapshot
    assert snapshot["generated_at"].endswith("Z")


def test_detail_and_timeline_generated_at_are_fresh_per_call(monkeypatch):
    """#1555: generated_at is computed per call, not cached, so a re-read reflects a new time."""
    from datetime import datetime, timezone
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Fresh timestamp", "idempotency_key": "fresh-generated-at",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1)
    first = goals.detail(goal.id)["generated_at"]
    import time as _time
    _time.sleep(1.1)
    second = goals.detail(goal.id)["generated_at"]
    assert first != second


def test_goal_detail_preserves_existing_fields_besides_generated_at():
    """#1555: adding generated_at must not remove or alter existing response fields."""
    _, _, _, goals = _services()
    goal = goals.create({"objective": "Field preservation", "idempotency_key": "field-preservation",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    planned = goals.plan(goal.id, expected_revision=1)
    detail = goals.detail(goal.id)
    assert detail["id"] == goal.id
    assert detail["status"] == "PLANNED"
    assert detail["title"] == planned.goal.title
    assert detail["completion_scope"] == "EXECUTION_ONLY"
    assert detail["remote_acceptance"] == "NOT_OBSERVED"
    assert "generated_at" in detail


def test_plan_markdown_compacts_bulky_nested_quota_fit_while_preserving_api_fit():
    import json
    _, _, _, goals = _services()
    bulky_fit = {
        "status": "needs_a_reset",
        "uncertain": True,
        "forecast_only": True,
        "availability_guaranteed": False,
        "estimated_at": "2026-11-20T00:00:00Z",
        "safety_buffer_percent": 15,
        "accounts": {
            "acct-a": {
                "state": "EXHAUSTED",
                "decision": "wait",
                "reason": "weekly_cap",
                "blocking_windows": ["weekly"],
                "uncertain": True,
                "until": "2026-11-21T00:00:00Z",
                "need": {"tokens": 50000, "padding": "z" * 2000},
                "observation": {"raw": "y" * 2000},
                "resets": {"weekly": "2026-11-21T00:00:00Z"},
            }
        },
        "tasks": [
            {
                "task_id": "t1",
                "account_ref": "acct-a",
                "binding_ref": "b1",
                "need": {"estimate": {"tokens": 12345}, "blob": "n" * 2000},
                "routing": {"candidates": ["b" * 1000]},
            },
            {
                "task_id": "t2",
                "account_ref": None,
                "reason": "no_capacity",
                "need": {"blob": "m" * 2000},
            },
        ],
        "alternative": {
            "status": "needs_another_model",
            "uncertain": False,
            "accounts": {
                "acct-b": {
                    "state": "READY",
                    "decision": "proceed",
                    "observation": {"huge": "x" * 2000},
                    "need": {"tokens": 999, "blob": "k" * 1500},
                }
            },
            "tasks": [
                {"task_id": "t1", "account_ref": "acct-b", "binding_ref": "b2", "need": {"blob": "j" * 1500}},
            ],
            "alternative": {
                "status": "fits_other",
                "accounts": {"acct-c": {"state": "READY", "observation": {"huge": "q" * 2000}}},
            },
        },
    }
    goals.quota_forecaster = lambda _goal, _tasks: bulky_fit
    goal = goals.create({
        "objective": "Preserve compact plan forecast",
        "idempotency_key": "compact-quota-fit-plan",
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    planned = goals.plan(goal.id, expected_revision=1)
    assert planned.quota_fit["accounts"]["acct-a"]["need"]["padding"] == "z" * 2000
    assert planned.quota_fit["tasks"][0]["routing"]["candidates"] == ["b" * 1000]
    detail_fit = goals.detail(goal.id)["quota_fit"]
    assert detail_fit["accounts"]["acct-a"]["observation"]["raw"] == "y" * 2000
    section = planned.goal.plan_markdown.split("## Quota fit forecast", 1)[1]
    compact_json = section.split("```json\n", 1)[1].split("\n```", 1)[0]
    assert len(compact_json.encode("utf-8")) < 2048
    parsed = json.loads(compact_json)
    assert parsed["status"] == "needs_a_reset"
    assert set(parsed["accounts"]["acct-a"]) == {
        "state", "decision", "reason", "blocking_windows", "uncertain", "until",
    }
    assert parsed["tasks"] == [
        {"task_id": "t1", "account_ref": "acct-a", "binding_ref": "b1"},
        {"task_id": "t2", "account_ref": None, "reason": "no_capacity"},
    ]
    assert parsed["alternative"]["status"] == "needs_another_model"
    assert "observation" not in parsed["alternative"]["accounts"]["acct-b"]
    assert "need" not in parsed["alternative"]["accounts"]["acct-b"]
    assert parsed["alternative"]["alternative"] == {"status": "fits_other"}


def test_compact_quota_fit_for_plan_omits_absent_status_in_deep_alternative():
    from reverse_agent.platform_v1.goal_service import GoalService
    compact = GoalService._compact_quota_fit_for_plan({
        "status": "needs_another_model",
        "alternative": {
            "status": "inner",
            "alternative": {"accounts": {"acct-c": {"state": "READY"}}},
        },
    })
    assert compact["alternative"]["alternative"] == {}

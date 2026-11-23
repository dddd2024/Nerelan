"""Fail-closed startup contract for autonomous coordinator recovery."""
import time

import pytest

from datetime import datetime, timedelta, timezone

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from test_native_host_socket_smoke import _isolated_host
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)


def _owner_fixture(tmp_path, *, fail_dispatch=False):
    """Owner window, one provider-free fixture Task and a durable coordinator."""
    store = TaskStore(str(tmp_path / "coordinator.sqlite3"))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "startup-reconcile", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 5, "max_retries": 0, "confirmation": "ACTIVATE",
    })
    goal = goals.create({"objective": "Startup reconcile fixture", "idempotency_key": "startup-reconcile-goal",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "only", "instruction": "do it"}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    dispatches = []

    class CountingExecutor:
        def execute(self, task_id, task_store, *, workspace_root="", event_callback=None):
            dispatches.append(task_id)
            if fail_dispatch:
                pytest.fail("fixture executor dispatched after failed startup reconciliation")
            return ExecutorResult(success=True, validation_exit_code=0, validation_command_id="git_diff_check",
                                  validation_output_digest="startup-fixture", validation_output_summary="ok",
                                  changed_files=[], execution_id=f"exec-{task_id}")

    router = ExecutorRouter()
    router.replace("deterministic_fixture", lambda **_: CountingExecutor())
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy, router=router,
                                        workspace_root=tmp_path / "workspaces",
                                        execution_authority_sha="a" * 64, planning_sha="b" * 64)
    return store, control, window, task_id, coordinator, dispatches


def _deny_startup_reconcile(patcher):
    """Persisted durable-run state becomes unreadable at activation time."""
    def unavailable(self, *args, **kwargs):
        raise OSError("fixture_recovery_unavailable")

    patcher.setattr(DurableExecutionService, "reconcile_expired_runs", unavailable)


def test_paused_host_cannot_activate_autonomous_dispatch_after_failed_reconcile(
    tmp_path, monkeypatch,
):
    """Cover native-goal bootstrap's paused-host -> coordinator.start path."""
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    calls = []

    def unavailable(self, *args, **kwargs):
        calls.append(True)
        raise OSError("fixture_recovery_unavailable")

    monkeypatch.setattr(DurableExecutionService, "reconcile_expired_runs", unavailable)
    store, host = _isolated_host(tmp_path)
    try:
        host.start(coordinator_paused=True)
        assert host._coordinator is not None
        assert host._coordinator._thread is None
        with pytest.raises(RuntimeError, match="coordinator_startup_reconciliation_failed") as exc:
            host._coordinator.start()
        assert isinstance(exc.value.__cause__, OSError)
        assert len(calls) == 1
        assert host._coordinator._thread is None
        assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
        assert store._conn.execute(
            "SELECT COUNT(*) FROM platform_operation_receipts"
        ).fetchone()[0] == 0
    finally:
        host.stop()
        store._conn.close()


def test_explicit_read_only_reconcile_preserves_diagnostic_behavior(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")

    def unavailable(self, *args, **kwargs):
        raise OSError("fixture_recovery_unavailable")

    monkeypatch.setattr(DurableExecutionService, "reconcile_expired_runs", unavailable)
    store, host = _isolated_host(tmp_path)
    try:
        host.start(coordinator_paused=True)
        coordinator = host._coordinator
        assert coordinator is not None
        assert coordinator.reconcile() == ()
        assert coordinator._last_error == "reconcile_failed:OSError"
        assert coordinator._thread is None
    finally:
        host.stop()
        store._conn.close()


def test_failed_startup_reconcile_keeps_manual_ticks_inert(tmp_path, monkeypatch):
    """A failed startup reconcile must block every manual dispatch mode (#1347)."""
    store, control, window, task_id, coordinator, dispatches = _owner_fixture(tmp_path, fail_dispatch=True)
    try:
        with monkeypatch.context() as denied:
            _deny_startup_reconcile(denied)
            with pytest.raises(
                RuntimeError, match="coordinator_startup_reconciliation_failed"
            ) as exc:
                coordinator.start()
        assert isinstance(exc.value.__cause__, OSError)
        assert coordinator._thread is None
        assert coordinator._last_error == "reconcile_failed:OSError"
        status = coordinator.status()
        assert status["lifecycle"] == "STOPPED"
        assert status["enabled"] is False
        assert status["accepting_work"] is False
        assert coordinator.tick() == 0
        assert coordinator.tick(background=True) == 0
        assert dispatches == []
        # No task admission, no claim, no budget reservation and no receipt.
        assert store.get_task(task_id).status == "QUEUED"
        assert store.get_latest_durable_run_observation(task_id) is None
        assert store.list_usage_observations(task_id) == ()
        assert store._conn.execute(
            "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?", (task_id,)
        ).fetchone()[0] == 0
        assert store._conn.execute(
            "SELECT COUNT(*) FROM platform_coordinator_claims"
        ).fetchone()[0] == 0
        assert store._conn.execute(
            "SELECT COUNT(*) FROM platform_operation_receipts"
        ).fetchone()[0] == 0
        budget = control.get_window(window.id)
        assert (budget.tasks_started, budget.tasks_completed, budget.retries_used) == (0, 0, 0)
        assert control.window_budget_summary(window.id)["active_reservation_count"] == 0
    finally:
        coordinator.stop(timeout=2.0)
        store._conn.close()


def test_failed_startup_reconcile_recovers_on_a_later_successful_start(tmp_path, monkeypatch):
    """The denial is scoped to the failed activation, not permanent (#1347)."""
    store, control, window, task_id, coordinator, dispatches = _owner_fixture(tmp_path)
    try:
        with monkeypatch.context() as denied:
            _deny_startup_reconcile(denied)
            with pytest.raises(
                RuntimeError, match="coordinator_startup_reconciliation_failed"
            ):
                coordinator.start()
            assert coordinator._thread is None
            assert coordinator.tick() == 0
            assert dispatches == []
            assert store.get_task(task_id).status == "QUEUED"

        # Recovery truth is available again: a later start dispatches normally.
        coordinator.start()
        assert coordinator._thread is not None and coordinator._thread.is_alive()
        assert coordinator.status()["lifecycle"] == "RUNNING"
        deadline = time.monotonic() + 15.0
        while (store.get_task(task_id).status
               not in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "FAILED", "BLOCKED"}
               and time.monotonic() < deadline):
            time.sleep(0.05)
        # The worker completes its claim, and the window counter, just after the task settles.
        while control.get_window(window.id).tasks_completed == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        final = store.get_task(task_id)
        assert final.status in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"} and final.validation_exit_code == 0
        assert dispatches == [task_id]
        assert (
            control.get_window(window.id).tasks_started,
            control.get_window(window.id).tasks_completed,
        ) == (1, 1)
        coordinator.stop(timeout=5.0)
        status = coordinator.status()
        assert status["lifecycle"] == "STOPPED"
        assert status["accepting_work"] is False
        assert coordinator._thread is None
        assert coordinator.tick() == 0
        assert dispatches == [task_id]
    finally:
        coordinator.stop(timeout=2.0)
        store._conn.close()


def test_restart_during_preparation_does_not_strand_continuous_run_goals(tmp_path, goal_checks):
    """Incident 2026-11-17: a host restart hit two tasks in PREPARING_WORKSPACE. Each had a
    dead owner's 15-minute coordinator claim and a 5-minute durable lease, nothing
    dispatched, and the continuous window was at max_retries. Reconcile and the escalation
    sweep must give both goals a replacement task and settle the dead claims."""
    from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
    _root, _base, store, control, _service, first_goal, window = goal_checks
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control,
                        roster_resolver=lambda role: ("opencode", "local-test-binding"))
    goal_ids, task_ids = [], []
    for index in range(2):
        goal = goals.create({"objective": f"Incident goal {index}", "idempotency_key": f"incident-{index}",
                             "repository": first_goal.repository, "executor_kind": "opencode",
                             "binding_ref": "local-test-binding", "orchestration_mode": "agent_team"})
        goals.plan(goal.id, expected_revision=1,
                   tasks=[{"id": "T001", "title": "Work", "instruction": "Do it", "agent_role": "coder"}])
        goals.approve(goal.id, expected_revision=1)
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
        goal_ids.append(goal.id)
        task_ids.append(control.list_goal_tasks(goal.id)[0]["task_id"])
        control.append_receipt(window_id=window.id, operation_type=OWNER_WINDOW_RECEIPT,
                               capability="execute_task", repository=first_goal.repository,
                               subject_id=goal.id, decision="allowed", reason="test",
                               input_payload={}, result="ok")
    store._conn.execute("UPDATE platform_operation_receipts SET confirmation_mode = ? WHERE operation_type = ?",
                        (OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT))
    # A continuous window whose retries are all used.
    store._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode = ?, expires_at = '', "
                        "retries_used = max_retries WHERE id = ?", (OWNER_WINDOW_MODE, window.id))
    store._conn.commit()
    assert control.get_window(window.id).continuous
    now_ms = int(time.time() * 1000)
    epochs = {}
    for task_id in task_ids:
        epochs[task_id], _ = control.claim_task(window_id=window.id, task_id=task_id, owner="dead-host",
                                                lease_ms=15 * 60_000)
        task = store.get_task(task_id)
        store._acquire_durable_lease(task_id=task_id, execution_id=task.execution_id, lease_owner="dead-host",
                                     execution_authority_sha="a" * 64, planning_sha="b" * 64,
                                     task_status="QUEUED")
        store.set_state(task_id, "PREPARING_WORKSPACE")
        # The 5-minute durable lease ran out; the 15-minute claim has not yet.
        store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now_ms - 1000, task_id))
    store._conn.commit()
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
                                        router=ExecutorRouter(), workspace_root=tmp_path / "workspaces",
                                        execution_authority_sha="a" * 64, planning_sha="b" * 64,
                                        owner="new-host", goal_escalator=goals.escalate_failed_tasks)

    # Restart: the claims are still live, so the runs are only interrupted (as before).
    coordinator.reconcile()
    assert [store.get_task(task_id).status for task_id in task_ids] == ["INTERRUPTED"] * 2
    assert [control.list_goal_tasks(goal_id)[0]["task_id"] for goal_id in goal_ids] == task_ids

    # The dead owner's claims expire; the next reconcile closes, settles and escalates.
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms = ? WHERE owner = 'dead-host'",
                        (now_ms - 1,))
    store._conn.commit()
    coordinator.reconcile()
    for goal_id, task_id in zip(goal_ids, task_ids):
        old = store.get_task(task_id)
        assert (old.status, old.failure_classification) == ("FAILED", "orphaned_preparation")
        claim = store._conn.execute("SELECT owner, epoch, status FROM platform_coordinator_claims WHERE task_id = ?",
                                    (task_id,)).fetchone()
        assert dict(claim) == {"owner": "dead-host", "epoch": epochs[task_id], "status": "FAILED"}
        assert store._conn.execute("SELECT state FROM platform_budget_reservations WHERE task_id = ?",
                                   (task_id,)).fetchone()["state"] == "UNKNOWN"
        link = control.list_goal_tasks(goal_id)[0]
        assert link["task_id"] != task_id
        replacement = store.get_task(link["task_id"])
        assert (replacement.status, replacement.binding_ref) == ("QUEUED", old.binding_ref)
        assert control.get_goal(goal_id).status == "RUNNING"
        [step] = control.list_task_escalations(goal_id)
        assert step["reason"] == "host_retry:interrupted"
    # No max_retries were spent and the replacements are runnable at 2/2.
    budget = control.get_window(window.id)
    assert budget.retries_used == budget.max_retries > 0
    runnable = control.runnable_tasks(window.id, respect_attempt_limits=True)
    assert {control.list_goal_tasks(goal_id)[0]["task_id"] for goal_id in goal_ids} <= set(runnable)


def test_pre_start_manual_tick_before_any_start_still_dispatches(tmp_path, monkeypatch):
    """Provider-free direct ticks keep working; gating is armed by a failed start."""
    store, control, window, task_id, coordinator, dispatches = _owner_fixture(tmp_path)
    try:
        assert coordinator.tick() == 1
        assert dispatches == [task_id]
        assert store.get_task(task_id).status in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}
        assert control.get_window(window.id).tasks_started == 1
        # A coordinator that never started stays inert on its own.
        assert coordinator._thread is None
        status = coordinator.status()
        assert status["lifecycle"] == "STOPPED"
        assert status["accepting_work"] is False
        assert coordinator.tick() == 0
    finally:
        coordinator.stop(timeout=2.0)
        store._conn.close()

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

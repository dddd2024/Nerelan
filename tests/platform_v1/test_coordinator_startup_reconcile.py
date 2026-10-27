"""Fail-closed startup contract for autonomous coordinator recovery."""
import time

import pytest

from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from reverse_agent.platform_v1.task_runtime import LocalValidationRunner
from test_native_host_socket_smoke import _isolated_host
from test_unattended_coordinator import _real_checker_fixture


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
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(
        tmp_path, monkeypatch
    )
    dispatches = []

    def observed_run(self, **kwargs):
        dispatches.append(kwargs["task_id"])
        pytest.fail("actual checker dispatched after failed startup reconciliation")

    monkeypatch.setattr(LocalValidationRunner, "run", observed_run)
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
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(
        tmp_path, monkeypatch
    )
    dispatches = []
    original_run = LocalValidationRunner.run

    def observed_run(self, **kwargs):
        dispatches.append(kwargs["task_id"])
        return original_run(self, **kwargs)

    monkeypatch.setattr(LocalValidationRunner, "run", observed_run)
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
        assert final.status == "READY_FOR_REVIEW" and final.validation_exit_code == 0
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
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(
        tmp_path, monkeypatch
    )
    dispatches = []
    original_run = LocalValidationRunner.run

    def observed_run(self, **kwargs):
        dispatches.append(kwargs["task_id"])
        return original_run(self, **kwargs)

    monkeypatch.setattr(LocalValidationRunner, "run", observed_run)
    try:
        assert coordinator.tick() == 1
        assert dispatches == [task_id]
        assert store.get_task(task_id).status == "READY_FOR_REVIEW"
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

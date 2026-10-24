"""Fail-closed startup contract for autonomous coordinator recovery."""
import pytest

from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from test_native_host_socket_smoke import _isolated_host


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

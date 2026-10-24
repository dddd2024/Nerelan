"""Startup reconciliation must fail visibly, without starting a falsely healthy host."""
import pytest

from reverse_agent.platform_v1.durable_execution import DurableExecutionService
from _local_client_fixture import client_session
from test_native_host_socket_smoke import _isolated_host


def test_reconciliation_exception_refuses_unpaused_host_start(tmp_path, monkeypatch):
    calls = []

    def broken_reconcile(self, *args, **kwargs):
        calls.append(True)
        raise OSError("fixture_db_unavailable")

    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    monkeypatch.setattr(DurableExecutionService, "reconcile_expired_runs", broken_reconcile)
    store, host = _isolated_host(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="trusted_host_startup_reconciliation_failed") as exc:
            host.start(coordinator_paused=False)
        assert isinstance(exc.value.__cause__, OSError)
        assert len(calls) == 1
        assert host._started_servers == []
        assert host._coordinator is None
        assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
        assert store._conn.execute("SELECT COUNT(*) FROM platform_operation_receipts").fetchone()[0] == 0
    finally:
        host.stop()
        store._conn.close()


def test_paused_host_is_explicitly_usable_without_reconciliation(tmp_path, monkeypatch):
    def forbidden_reconcile(self, *args, **kwargs):
        raise AssertionError("paused host must skip reconciliation")

    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    monkeypatch.setattr(DurableExecutionService, "reconcile_expired_runs", forbidden_reconcile)
    store, host = _isolated_host(tmp_path)
    try:
        host.start(coordinator_paused=True)
        assert len(host._started_servers) == 3
        assert host._coordinator is not None
        assert host._coordinator._thread is None
        assert host._control_store.active_window() is None
        assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
    finally:
        host.stop()
        store._conn.close()

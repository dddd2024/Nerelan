"""Disposable storage and real loopback host restart regression."""
import socket
from urllib.parse import urlsplit
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
from _local_client_fixture import client_session
from test_native_host_socket_smoke import _get


def test_clean_host_restart_rebinds_fresh_ports_without_reviving_coordinator(tmp_path, monkeypatch):
    """A normal stop/start with the same disposable TaskStore must not resurrect work."""
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    db = tmp_path / "restart-tasks.sqlite3"
    observed = []
    for _ in range(2):
        store = TaskStore(db_path=str(db))
        host = CombinedTrustedHost(
            task_store=store, vault=None, auth_list_probe=lambda: {},
            local_client_session=client_session(activate=False),
            model_control_host="127.0.0.1", model_control_port=0,
            task_api_host="127.0.0.1", task_api_port=0,
        )
        try:
            host.start(coordinator_paused=True)
            assert host._coordinator is not None and host._coordinator._thread is None
            ports = tuple(urlsplit(url).port for url in (
                host.model_control_url, host.task_api_url, host.relay_url))
            assert len(set(ports)) == 3
            observed.append(ports)
            status, policy = _get(host.task_api_url, "/api/windows/policy")
            assert status == 200 and policy["available"] is False
            assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
            assert store._conn.execute("SELECT COUNT(*) FROM platform_operation_receipts").fetchone()[0] == 0
        finally:
            host.stop()
            store._conn.close()
        for port in ports:
            with socket.socket() as probe:
                probe.settimeout(0.5)
                assert probe.connect_ex(("127.0.0.1", port)) != 0
    assert len(observed) == 2


def test_synthetic_stale_lease_reconciles_once_across_host_reopenings(tmp_path, monkeypatch):
    """A synthetic stale lease is reconciled once; no real model crash is simulated."""
    import time

    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    db = tmp_path / "interrupted-tasks.sqlite3"
    store = TaskStore(db_path=str(db))
    task = store.create_task(title="interrupted-fixture", executor_kind="deterministic_fixture")
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="disconnected-worker", repository_base_sha="", worktree_path="",
    )
    store.transition_to(task.id, "RUNNING")
    expired_at_ms = int(time.time() * 1000) - 10000
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (expired_at_ms, lease.run_id),
    )
    store._conn.commit()
    store._conn.close()

    for paused, expected_status in ((True, "RUNNING"), (False, "INTERRUPTED"), (False, "INTERRUPTED")):
        reopened = TaskStore(db_path=str(db))
        host = CombinedTrustedHost(
            task_store=reopened, vault=None, auth_list_probe=lambda: {},
            local_client_session=client_session(activate=False),
            model_control_host="127.0.0.1", model_control_port=0,
            task_api_host="127.0.0.1", task_api_port=0,
        )
        try:
            host.start(coordinator_paused=paused)
            assert host._coordinator is not None and host._coordinator._thread is None
            assert reopened.get_task(task.id).status == expected_status
            durable = reopened._get_durable_run(lease.run_id)
            assert durable.run_id == lease.run_id
            assert durable.lease_expiry_ms == expired_at_ms
            if not paused:
                assert durable.recovery_classification == "orphan_stale_lease"
            events = reopened._conn.execute(
                "SELECT COUNT(*) FROM task_events WHERE task_id = ? AND description = ?",
                (task.id, "lease expired, reconciled to INTERRUPTED"),
            ).fetchone()[0]
            assert events == (0 if paused else 1)
            assert reopened._conn.execute(
                "SELECT COUNT(*) FROM platform_operation_receipts"
            ).fetchone()[0] == 0
        finally:
            host.stop()
            reopened._conn.close()

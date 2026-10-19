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
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe.bind(("127.0.0.1", port))
    assert len(observed) == 2

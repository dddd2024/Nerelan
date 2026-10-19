"""Provider-free real socket smoke for the merged native host lifecycle.

Uses a fresh SQLite database and ephemeral loopback ports. This suite cannot
approve an Owner dialog, start a coordinator, dispatch an Agent, or touch live
task/claim/account state.
"""
import json
import socket
from http.client import HTTPConnection
from urllib.parse import urlsplit

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
from _local_client_fixture import client_headers, client_session


def _isolated_host(tmp_path):
    store = TaskStore(db_path=str(tmp_path / "scratch-tasks.sqlite3"))
    host = CombinedTrustedHost(
        task_store=store,
        vault=None,
        auth_list_probe=lambda: {},
        local_client_session=client_session(activate=False),
        model_control_host="127.0.0.1",
        model_control_port=0,
        task_api_host="127.0.0.1",
        task_api_port=0,
    )
    return store, host


def _get(url, path):
    target = urlsplit(url)
    client = HTTPConnection(target.hostname, target.port, timeout=3)
    try:
        client.request("GET", path, headers=client_headers())
        response = client.getresponse()
        return response.status, json.loads(response.read())
    finally:
        client.close()


def test_paused_real_host_starts_on_isolated_ports_and_releases_all(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    monkeypatch.delenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", raising=False)
    store, host = _isolated_host(tmp_path)
    ports = []
    try:
        host.start(coordinator_paused=True)
        assert len(host._started_servers) == 3
        assert host._coordinator is not None
        assert host._coordinator._thread is None
        for url in (host.model_control_url, host.task_api_url, host.relay_url):
            parsed = urlsplit(url)
            assert parsed.hostname == "127.0.0.1"
            assert parsed.port > 0
            ports.append(parsed.port)
        assert len(set(ports)) == 3
        code, policy = _get(host.task_api_url, "/api/windows/policy")
        assert code == 200
        assert policy["available"] is False
        assert host._control_store.active_window() is None
        assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
        assert store._conn.execute("SELECT COUNT(*) FROM platform_operation_receipts").fetchone()[0] == 0
    finally:
        host.stop()
        store._conn.close()

    assert not host._started_servers
    for port in ports:
        with socket.socket() as probe:
            probe.settimeout(0.5)
            # Rebinding with SO_REUSEADDR can succeed while a listener remains
            # active on Windows; connection refusal checks the actual listener.
            assert probe.connect_ex(("127.0.0.1", port)) != 0


def test_occupied_port_refuses_without_start_or_durable_write(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    store, host = _isolated_host(tmp_path)
    try:
        with socket.socket() as owner:
            owner.bind(("127.0.0.1", 0))
            owner.listen()
            port = owner.getsockname()[1]
            with pytest.raises(OSError):
                host.start(model_control_port=port, coordinator_paused=True)
            assert owner.getsockname()[1] == port
        assert host._started_servers == []
        assert store._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
        assert store._conn.execute("SELECT COUNT(*) FROM platform_operation_receipts").fetchone()[0] == 0
        assert host._control_store.active_window() is None
    finally:
        host.stop()
        store._conn.close()

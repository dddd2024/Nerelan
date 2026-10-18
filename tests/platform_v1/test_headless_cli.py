"""CLI-0 accepts no owner tokens, mutation requests, or live model calls."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time

import pytest

from reverse_agent.platform_v1 import headless_cli


@pytest.fixture
def health_peer():
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(0.1)
    stop = threading.Event()
    requests = []
    threads = []

    def start(prefix, body, drip):
        def serve():
            while not stop.is_set():
                try:
                    conn, _ = listener.accept()
                    break
                except socket.timeout:
                    continue
            else:
                return
            with conn:
                conn.settimeout(1)
                try:
                    request = b""
                    while b"\r\n\r\n" not in request:
                        part = conn.recv(4096)
                        if not part:
                            return
                        request += part
                    requests.append(request)
                    conn.sendall(prefix)
                    if drip:
                        for byte in body:
                            conn.sendall(bytes([byte]))
                            if stop.wait(0.15):
                                break
                    else:
                        conn.sendall(body)
                except OSError:
                    pass
        thread = threading.Thread(target=serve, daemon=True)
        threads.append(thread)
        thread.start()
        return listener.getsockname()[1], requests

    yield start
    stop.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    listener.close()


@pytest.mark.parametrize("response, expected", [
    (b'HTTP/1.1 200 OK\r\nContent-Length: 14\r\n\r\n{"ready":true}', 0),
    (b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{"ready":true}', 50),
    (b'HTTP/1.1 200 OK\r\nContent-Length: 40\r\n\r\n{"ready":true,"ready":true}', 50),
    (b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{"ready":true,"a":NaN}', 50),
    (b'HTTP/1.1 302 Found\r\nLocation: http://external.invalid/\r\n\r\n', 50),
    (b'HTTP/1.1 307 Redirect\r\nLocation: /api/health\r\n\r\n', 50),
    (b'HTTP/1.1 200 OK\r\n\r\n{"ready":true}' + b' ' * 4096, 50),
])
def test_fixed_probe_no_proxy_auth_redirect_or_oversize(monkeypatch, health_peer, response, expected):
    port, requests = health_peer(b"", response, False)
    connect = headless_cli._DeadlineSocket.connect

    def test_connect(sock, address):
        assert address == ("127.0.0.1", 8766)
        return connect(sock, ("127.0.0.1", port))

    monkeypatch.setattr(headless_cli._DeadlineSocket, "connect", test_connect)
    monkeypatch.setenv("HTTP_PROXY", "http://external.invalid:1")
    monkeypatch.setenv("http_proxy", "http://external.invalid:1")
    monkeypatch.setenv("NO_PROXY", "")
    code, body = headless_cli.evaluate(["doctor"])
    assert code == expected
    assert body["dispatch_permitted"] is False
    assert requests == [b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1:8766\r\nConnection: close\r\n\r\n"]


@pytest.mark.parametrize("slow_stage", ["headers", "body"])
def test_slow_peer_process_deadline(health_peer, slow_stage):
    if slow_stage == "headers":
        prefix = b"HTTP/1.1 200 OK\r\nX-Slow: "
        body = b"private-secret" * 10
    else:
        prefix = b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n"
        body = b" " * 100
    port, requests = health_peer(prefix, body, True)
    script = """
import json, sys
from reverse_agent.platform_v1 import headless_cli as cli
connect = cli._DeadlineSocket.connect
def test_connect(sock, address):
    assert address == ('127.0.0.1', 8766)
    return connect(sock, ('127.0.0.1', int(sys.argv[1])))
cli._DeadlineSocket.connect = test_connect
results = [cli.evaluate(['doctor'])]
results += [cli.evaluate(args) for args in
            [['status'], ['goal', 'create'], ['goal', 'approve'], ['goal', 'launch']]]
print(json.dumps(results))
"""
    start = time.monotonic()
    result = subprocess.run([sys.executable, "-c", script, str(port)],
                            capture_output=True, text=True, timeout=3.8)
    elapsed = time.monotonic() - start
    assert 1.8 <= elapsed < 4
    assert result.returncode == 0, result.stderr
    results = json.loads(result.stdout)
    assert results[0][1]["status"] == "PUBLIC_HEALTH_UNAVAILABLE"
    assert results[1][1]["status"] == "WAITING"
    assert all(code == 50 and not body["dispatch_permitted"] for code, body in results)
    assert all(body["status"] == "NOT_SUPPORTED" for _, body in results[2:])
    assert "private-secret" not in result.stdout
    assert len(requests) == 1


def test_public_health_is_explicitly_not_execution_authority():
    code, body = headless_cli.evaluate(["doctor", "--json"], probe=lambda: b'{"ready":true}')
    assert code == 0
    assert body["status"] == "PUBLIC_HEALTH_OBSERVED"
    assert body["authenticated"] is False
    assert body["dispatch_permitted"] is False
    assert body["control_plane"] == "NOT_CONNECTED"


@pytest.mark.parametrize("payload", [
    b'{"ready":false}', b'{"ready":"true"}', b'[]', b'invalid',
    b'{"ready":false,"ready":true}', b'{"ready":true,"ready":false}',
    b'{"ready":true,"unexpected":NaN}', b'{"ready":true,"infinite":Infinity}',
    b'{"ready":true}' + b" " * 4096, b'{"ready":true,"private_key":"x"}' * 1000,
])
def test_bad_health_payload_is_not_auth_or_success(payload):
    code, body = headless_cli.evaluate(["doctor"], probe=lambda: payload)
    assert code == 50
    assert body["status"] == "PUBLIC_HEALTH_UNAVAILABLE"
    assert body["dispatch_permitted"] is False


@pytest.mark.parametrize("args", [
    ["goal", "create", "--file", "goal.json", "--json"],
    ["goal", "approve", "goal-123"],
    ["goal", "launch", "goal-123", "--window", "window-123"],
    ["task", "list", "--json"], ["run", "stop", "run-123"],
    ["window", "activate", "window-123"], ["run", "resume"],
    ["doctor", "--url", "http://evil.example"],
    ["doctor", "--capability", "private-value"],
    ["doctor", "--json", "extra"], [],
])
def test_unsupported_verbs_fail_closed_before_network(args, monkeypatch):
    def unreachable(*_args, **_kwargs):
        raise AssertionError("unsupported action must not attempt network")

    monkeypatch.setattr(headless_cli, "_public_health", unreachable)
    code, body = headless_cli.evaluate(args)
    assert code == 50
    assert body["status"] == "NOT_SUPPORTED"
    assert "private-value" not in json.dumps(body)
    assert body["dispatch_permitted"] is False


def test_private_status_never_reads_public_health(monkeypatch):
    def unreachable():
        raise AssertionError("status may not substitute public health for auth")
    monkeypatch.setattr(headless_cli, "_public_health", unreachable)
    code, body = headless_cli.evaluate(["status", "--json"])
    assert code == 50
    assert body["status"] == "WAITING"
    assert body["reason"] == "authenticated_control_transport_not_implemented"


def test_main_is_structured_with_nonzero_mutation_exit(capsys):
    result = headless_cli.main(["goal", "launch", "goal-1", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == 50
    assert output["status"] == "NOT_SUPPORTED"
    assert "goal-1" not in json.dumps(output)

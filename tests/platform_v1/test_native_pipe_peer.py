"""Windows kernel peer-PID binding for the test-only CLI-2 pipe probe."""
from __future__ import annotations

import json
import multiprocessing
import os
import threading
from multiprocessing.connection import Client

import pytest

from reverse_agent.platform_v1 import native_pipe_peer
from reverse_agent.platform_v1.native_pipe_probe import NativePipeProbe, PROTOCOL


def _foreign_client_with_valid_key(address: str, key: bytes, output) -> None:
    """Test child proves correct HMAC key alone cannot impersonate host PID."""
    try:
        with Client(address, family="AF_PIPE", authkey=key) as conn:
            conn.send_bytes(json.dumps({"protocol": PROTOCOL, "operation": "doctor"}).encode())
            conn.recv_bytes(4096)
        output.put("UNEXPECTED_AUTHORIZATION")
    except (EOFError, OSError, ValueError):
        output.put("REJECTED")


@pytest.mark.parametrize("pid", [0, -1, True, "123", None, 2**34])
def test_expected_client_pid_cannot_be_spoofed_by_type_or_range(pid):
    assert native_pipe_peer.matches_expected_client_pid(12, pid) is False
    if os.name == "nt":
        with pytest.raises(RuntimeError, match="native_pipe_expected_client_unavailable"):
            NativePipeProbe(expected_client_pid=pid)


@pytest.mark.parametrize("handle", [-1, 0, True, "handle", None])
def test_invalid_kernel_pipe_handle_is_not_a_client_identity(handle):
    assert native_pipe_peer.get_named_pipe_client_pid(handle) is None


@pytest.mark.skipif(os.name != "nt", reason="Windows named pipe identity API")
def test_unattested_pipe_handle_never_satisfies_expected_pid():
    assert native_pipe_peer.matches_expected_client_pid(0, os.getpid()) is False


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_correct_host_key_from_foreign_pid_is_still_denied():
    host = NativePipeProbe(expected_client_pid=os.getpid())
    values: list[tuple[str, bytes]] = []
    host.deliver_to_trusted_bootstrap(lambda address, key: values.append((address, key)))
    address, key = values[0]
    bound = threading.Event()
    server_outcome = []
    server = threading.Thread(
        target=lambda: server_outcome.append(host.serve_one(bound=bound)), daemon=True
    )
    server.start()
    assert bound.wait(5)

    ctx = multiprocessing.get_context("spawn")
    output = ctx.Queue()
    process = ctx.Process(target=_foreign_client_with_valid_key, args=(address, key, output))
    process.start()
    process.join(12)
    if process.is_alive():
        process.terminate()
        process.join(5)
        pytest.fail("IPC fixture client exceeded bounded test deadline")
    assert process.exitcode == 0
    assert output.get(timeout=3) == "REJECTED"
    server.join(5)
    assert not server.is_alive()
    assert server_outcome == ["CLIENT_IDENTITY_REJECTED"]
    assert "host-private" in repr(host)
    assert key.hex() not in repr(host)


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_failed_kernel_pid_attestation_never_read_or_dispatch(monkeypatch):
    host = NativePipeProbe(expected_client_pid=os.getpid())
    values = []
    host.deliver_to_trusted_bootstrap(lambda address, key: values.append((address, key)))
    monkeypatch.setattr(
        "reverse_agent.platform_v1.native_pipe_probe.matches_expected_client_pid",
        lambda handle, expected: False,
    )
    bound = threading.Event()
    result = []
    server = threading.Thread(
        target=lambda: result.append(host.serve_one(bound=bound)), daemon=True
    )
    server.start()
    assert bound.wait(5)
    with Client(values[0][0], family="AF_PIPE", authkey=values[0][1]) as connection:
        connection.send_bytes(b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor"}')
        with pytest.raises((OSError, EOFError)):
            connection.recv_bytes(4096)
    server.join(5)
    assert not server.is_alive()
    assert result == ["CLIENT_IDENTITY_REJECTED"]

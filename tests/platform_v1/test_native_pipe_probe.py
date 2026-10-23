"""Provider-free Windows named-pipe authentication proof, NOT an Agent."""
from __future__ import annotations

import json
import multiprocessing
import os
import threading
from multiprocessing.connection import AuthenticationError, Client

import pytest

from reverse_agent.platform_v1.native_pipe_probe import (
    MAX_REQUEST_BYTES,
    NativePipeProbe,
    PIPE_PREFIX,
    PROTOCOL,
    _parse_probe,
    _reply,
)


def _isolated_stall_host(channel, bound):
    """Spawn transfers fixture credentials over an anonymous pipe, never argv/env."""
    host = NativePipeProbe(expected_client_pid=os.getpid())
    host.deliver_to_trusted_bootstrap(lambda address, key: channel.send((address, key)))
    channel.send(host.serve_one(bound=bound))
    channel.close()


@pytest.mark.skipif(os.name != "nt", reason="real Windows AF_PIPE negative proof")
def test_unauthenticated_foreign_client_blocks_before_pid_check_until_disconnect():
    """Known blocker: a wrong-PID peer can stall before sending ANY auth reply.

    Contain the deliberately blocking server in a joined, killable process.
    This documents a missing deadline; it is not a timeout implementation.
    """
    ctx = multiprocessing.get_context("spawn")
    parent, child = ctx.Pipe()
    bound = ctx.Event()
    process = ctx.Process(target=_isolated_stall_host, args=(child, bound))
    connection = None
    process.start()
    child.close()
    try:
        assert parent.poll(10), "isolated host did not bootstrap"
        address, _key = parent.recv()
        assert bound.wait(5)
        connection = Client(address, family="AF_PIPE", authkey=None)
        assert connection.poll(5), "server never began authentication"
        challenge = connection.recv_bytes(256)
        assert challenge.startswith(b"#CHALLENGE#")
        # The server expects its own PID, whereas this connection is from the
        # parent. It nevertheless waits for auth rather than rejecting the PID.
        assert not parent.poll(0.3)
        assert process.is_alive()
        connection.close()
        connection = None
        assert parent.poll(5), "disconnect did not release authentication"
        assert parent.recv() == "AUTHENTICATION_FAILED"
        process.join(5)
        assert process.exitcode == 0
    finally:
        if connection is not None:
            connection.close()
        if process.is_alive():
            process.terminate()
        process.join(5)
        parent.close()
        assert not process.is_alive(), "negative-test host was not reaped"


@pytest.mark.parametrize("packet,valid", [
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor"}', True),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"status"}', False),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"goal.launch"}', False),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor","principal":"owner"}', False),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor","token":"abc"}', False),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor","operation":"doctor"}', False),
    (b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"doctor","extra":NaN}', False),
    (b'[]', False),
    (b'x' * (MAX_REQUEST_BYTES + 1), False),
    (b'\xff', False),
])
def test_only_exact_doctor_probe_is_understood(packet, valid):
    assert _parse_probe(packet) is valid


def test_probe_response_does_not_assert_user_or_scheduler_authority():
    for valid in (True, False):
        payload = json.loads(_reply(valid))
        assert payload["status"] == ("TRANSPORT_PROOF_ONLY" if valid else "NOT_SUPPORTED")
        assert payload["transport_authenticated"] is True
        assert payload["principal_authenticated"] is False
        assert payload["dispatch_permitted"] is False
        assert payload["execution_started"] is False
        assert not any(key in payload for key in ("token", "principal", "goal_id", "capability"))


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_real_named_pipe_accepts_only_host_delivered_key():
    server = NativePipeProbe(expected_client_pid=os.getpid())
    bootstrap = []
    server.deliver_to_trusted_bootstrap(lambda address, secret: bootstrap.append((address, secret)))
    assert len(bootstrap) == 1
    address, key = bootstrap[0]
    assert address.startswith(PIPE_PREFIX)
    assert len(key) == 32
    assert "host-private" in repr(server)
    assert key.hex() not in repr(server)
    ready = threading.Event()
    results = []
    worker = threading.Thread(target=lambda: results.append(server.serve_one(bound=ready)), daemon=True)
    worker.start()
    assert ready.wait(5), "test-only server never bound"
    with Client(address, family="AF_PIPE", authkey=key) as conn:
        conn.send_bytes(json.dumps({"protocol": PROTOCOL, "operation": "doctor"}).encode("utf-8"))
        response = json.loads(conn.recv_bytes(MAX_REQUEST_BYTES))
    worker.join(5)
    assert not worker.is_alive(), "test-only server failed to finish"
    assert results == ["PROBE_COMPLETED"]
    assert response["status"] == "TRANSPORT_PROOF_ONLY"
    assert response["transport_authenticated"] is True
    assert response["principal_authenticated"] is False
    assert response["dispatch_permitted"] is False
    with pytest.raises(RuntimeError, match="native_pipe_not_available"):
        server.deliver_to_trusted_bootstrap(lambda *_args: None)


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_real_named_pipe_wrong_authentication_never_reaches_handler():
    server = NativePipeProbe(expected_client_pid=os.getpid())
    bootstrap = []
    server.deliver_to_trusted_bootstrap(lambda address, secret: bootstrap.append((address, secret)))
    address, key = bootstrap[0]
    ready = threading.Event()
    outcomes = []
    worker = threading.Thread(target=lambda: outcomes.append(server.serve_one(bound=ready)), daemon=True)
    worker.start()
    assert ready.wait(5)
    with pytest.raises((AuthenticationError, EOFError, OSError)):
        with Client(address, family="AF_PIPE", authkey=b"wrong-auth-key-32-byte-test-0000") as conn:
            conn.send_bytes(json.dumps({"protocol": PROTOCOL, "operation": "goal.launch"}).encode())
    worker.join(5)
    assert not worker.is_alive()
    assert outcomes == ["AUTHENTICATION_FAILED"]
    assert key.hex() not in repr(server)


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_authenticated_pipe_still_denies_goal_mutation():
    server = NativePipeProbe(expected_client_pid=os.getpid())
    bootstrap = []
    server.deliver_to_trusted_bootstrap(lambda address, key: bootstrap.append((address, key)))
    ready = threading.Event()
    outcomes = []
    worker = threading.Thread(target=lambda: outcomes.append(server.serve_one(bound=ready)), daemon=True)
    worker.start()
    assert ready.wait(5)
    with Client(bootstrap[0][0], family="AF_PIPE", authkey=bootstrap[0][1]) as conn:
        conn.send_bytes(b'{"protocol":"nerelan-native-pipe-probe/v1","operation":"goal.launch"}')
        result = json.loads(conn.recv_bytes(MAX_REQUEST_BYTES))
    worker.join(5)
    assert outcomes == ["PROBE_COMPLETED"]
    assert result["status"] == "NOT_SUPPORTED"
    assert result["dispatch_permitted"] is False


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_delivery_failure_revokes_session_without_echoing_secret():
    server = NativePipeProbe(expected_client_pid=os.getpid())
    def receiver(_address, _secret):
        raise ValueError("credential-shaped sensitive information")
    with pytest.raises(RuntimeError, match="^native_pipe_delivery_failed$") as exc:
        server.deliver_to_trusted_bootstrap(receiver)
    assert "sensitive" not in str(exc.value)
    assert exc.value.__cause__ is None
    with pytest.raises(RuntimeError, match="native_pipe_not_available"):
        server.deliver_to_trusted_bootstrap(lambda *_: None)


@pytest.mark.skipif(os.name != "nt", reason="AF_PIPE requires Windows")
def test_probe_rejects_zero_secret_and_untrusted_pipe_suffix():
    with pytest.raises(RuntimeError, match="native_pipe_key_unavailable"):
        NativePipeProbe(expected_client_pid=os.getpid(), key_factory=lambda _: bytes(32))
    with pytest.raises(RuntimeError, match="native_pipe_name_unavailable"):
        NativePipeProbe(expected_client_pid=os.getpid(), nonce_factory=lambda _: "../../evil")

"""Provider-free Windows named-pipe authentication proof, NOT an Agent."""
from __future__ import annotations

import json
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
    server = NativePipeProbe()
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
    server = NativePipeProbe()
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
    server = NativePipeProbe()
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
    server = NativePipeProbe()
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
        NativePipeProbe(key_factory=lambda _: bytes(32))
    with pytest.raises(RuntimeError, match="native_pipe_name_unavailable"):
        NativePipeProbe(nonce_factory=lambda _: "../../evil")

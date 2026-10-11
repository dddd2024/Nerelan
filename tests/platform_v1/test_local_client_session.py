"""Native host identity foundations; no HTTP authentication claim or providers."""

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.local_client_session import LocalClientSession
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


def session_fixture():
    clock = [10.0]
    tokens = iter(("a" * 64, "b" * 64, "c" * 64))
    session = LocalClientSession(ttl_seconds=10, clock=lambda: clock[0], token_factory=lambda: next(tokens))
    session.rotate()
    return session, clock


@pytest.mark.parametrize("value", [None, "", "a" * 63, "a" * 65, "é" * 64, "A" * 64, "b" * 64, "a" * 100000, [], b"a" * 64], ids=["missing", "empty", "short", "long", "non-ascii", "upper", "wrong", "oversized", "list", "bytes"])
def test_missing_wrong_and_malformed_values_are_rejected(value):
    session, _ = session_fixture()
    assert session.accepts(value) is False
    assert session.accepts("a" * 64) is True


def test_expiry_is_inclusive_and_cannot_be_resurrected_by_clock_rollback():
    session, clock = session_fixture()
    clock[0] = 19.99
    assert session.accepts("a" * 64)
    clock[0] = 20.0
    assert not session.accepts("a" * 64)
    clock[0] = 10.0
    assert not session.accepts("a" * 64)
    with pytest.raises(RuntimeError, match="^client_session_clock_unavailable$"):
        session.rotate()


def test_rotation_revocation_and_independent_host_sessions():
    first, _ = session_fixture()
    other = LocalClientSession(token_factory=lambda: "d" * 64)
    other.rotate()
    assert not other.accepts("a" * 64)
    first.rotate()
    assert not first.accepts("a" * 64)
    assert first.accepts("b" * 64)
    first.revoke()
    assert not first.accepts("b" * 64)
    first.rotate()
    assert first.accepts("c" * 64)


@pytest.mark.parametrize("value", [True, 0, -1, 604801, float("nan"), float("inf"), "secret-invalid-lifetime", None])
def test_invalid_lifetimes_have_fixed_errors(value):
    with pytest.raises(ValueError) as error:
        LocalClientSession(ttl_seconds=value)
    assert str(error.value) == "invalid_client_session_lifetime"
    assert error.value.__context__ is None


@pytest.mark.parametrize("bad_clock", [float("nan"), float("inf"), True, "bad-clock", 9.0])
def test_clock_failure_revokes_even_if_clock_recovers(bad_clock):
    session, clock = session_fixture()
    clock[0] = bad_clock
    assert not session.accepts("a" * 64)
    clock[0] = 11.0
    assert not session.accepts("a" * 64)


def test_clock_exception_does_not_escape_or_leak_private_context():
    clock = [10.0]
    def read_clock():
        if clock[0] is None:
            raise RuntimeError("private-clock-context")
        return clock[0]
    session = LocalClientSession(clock=read_clock, token_factory=lambda: "a" * 64)
    session.rotate()
    clock[0] = None
    assert not session.accepts("a" * 64)
    with pytest.raises(RuntimeError) as error:
        session.rotate()
    assert str(error.value) == "client_session_clock_unavailable"
    assert error.value.__context__ is None


@pytest.mark.parametrize("failure", ["malformed", "exception", "repeated"])
def test_entropy_failure_rejects_old_identity_and_sanitizes_errors(failure):
    def mint():
        if failure == "exception":
            raise ValueError("a" * 64)
        return "not-an-identity" if failure == "malformed" else "a" * 64
    session, _ = session_fixture()
    session._token_factory = mint
    session.revoke()
    with pytest.raises(RuntimeError) as error:
        session.rotate()
    assert str(error.value) == "client_session_entropy_unavailable"
    assert error.value.__context__ is None
    assert not session.accepts("a" * 64)


def test_private_delivery_is_explicit_and_failure_revokes_without_error_context():
    session, _ = session_fixture()
    delivered = []
    session.deliver(delivered.append)
    assert delivered == ["a" * 64]
    assert "a" * 64 not in repr(session)
    def failed_receiver(value):
        raise RuntimeError(value)
    with pytest.raises(RuntimeError) as error:
        session.deliver(failed_receiver)
    assert str(error.value) == "client_session_bootstrap_failed"
    assert error.value.__context__ is None
    assert not session.accepts(delivered[0])
    with pytest.raises(RuntimeError, match="^client_session_unavailable$"):
        session.deliver(delivered.append)
    assert len(delivered) == 1


def test_concurrent_revoke_prevents_all_subsequent_admissions():
    session, _ = session_fixture()
    barrier = threading.Barrier(5)
    revoked = threading.Event()
    def check_after_revoke():
        barrier.wait(timeout=3)
        assert revoked.wait(timeout=3)
        return [session.accepts("a" * 64) for _ in range(100)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        workers = [pool.submit(check_after_revoke) for _ in range(4)]
        barrier.wait(timeout=3)
        session.revoke()
        revoked.set()
        assert all(not any(worker.result(timeout=5)) for worker in workers)


def host_fixture(tmp_path):
    return CombinedTrustedHost(store=ModelProfileStore(), task_store=TaskStore(db_path=str(tmp_path / "tasks.sqlite3")), model_control_port=0, task_api_port=0, vault=None)


def test_real_provider_free_host_restart_rotates_private_session(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", "0")
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    host = host_fixture(tmp_path)
    assert not host._local_client_session.accepts("a" * 64)
    captured = []
    try:
        host.start()
        host._local_client_session.deliver(captured.append)
        assert host._local_client_session.accepts(captured[0])
        host.stop()
        assert not host._local_client_session.accepts(captured[0])
        host.start()
        host._local_client_session.deliver(captured.append)
        assert captured[0] != captured[1]
        assert not host._local_client_session.accepts(captured[0])
        assert host._local_client_session.accepts(captured[1])
        # No persistence seam: known test identity is absent from SQLite,
        # sidecar files and public host URLs; do not print the actual token.
        assert all(value not in host.task_api_url + host.model_control_url + host.relay_url for value in captured)
    finally:
        host.stop()
    assert not host._local_client_session.accepts(captured[-1])
    for path in tmp_path.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert all(value.encode("ascii") not in data for value in captured)


def test_partial_startup_entropy_failure_cleans_host_without_valid_session(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", "0")
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "0")
    host = host_fixture(tmp_path)
    host._local_client_session._token_factory = lambda: "invalid"
    with pytest.raises(RuntimeError, match="^client_session_entropy_unavailable$"):
        host.start()
    assert host._model_server is None
    assert host._task_server is None
    assert host._relay_server_inner is None
    assert not host._threads
    assert not host._local_client_session.accepts("a" * 64)

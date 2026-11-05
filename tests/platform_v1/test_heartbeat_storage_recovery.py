"""C3 F3: real SQLite contention must not silently abandon a valid lease."""

import logging
import sqlite3
import threading

import pytest

from reverse_agent.platform_v1 import durable_execution as runtime
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from tests.platform_v1.test_lease_invariants import _queued_task, _acquire


@pytest.fixture
def leased(tmp_path):
    path = tmp_path / "tasks.sqlite3"
    store = TaskStore(str(path))
    task = _queued_task(store)
    lease = _acquire(store, task, expiry_ms=10_000)
    store._conn.execute("PRAGMA busy_timeout = 5")
    other = sqlite3.connect(str(path))
    try:
        yield store, lease, other
    finally:
        other.rollback()
        other.close()
        store._conn.close()


def context(store, lease):
    return runtime._HeartbeatContext(store=store, run_id=lease.run_id,
        owner=lease.owner, epoch=lease.epoch, expiry_ms=10_000, heartbeat_window_ms=100)


def row(store, lease):
    return dict(store._conn.execute("SELECT lease_owner,lease_epoch,lease_expiry_ms,heartbeat_at_ms "
        "FROM durable_runs WHERE run_id=?", (lease.run_id,)).fetchone())


def observe_calls(store, monkeypatch):
    original = store._heartbeat_durable_lease
    failed, renewed, rejected = threading.Event(), threading.Event(), threading.Event()
    calls = []
    def heartbeat(*args):
        calls.append(args)
        try:
            original(*args)
        except TaskStoreError as exc:
            failed.set()
            if str(exc).startswith(("lease_fenced:", "lease_expired:")):
                rejected.set()
            raise
        else:
            renewed.set()
    monkeypatch.setattr(store, "_heartbeat_durable_lease", heartbeat)
    return calls, failed, renewed, rejected


def test_short_real_writer_lock_recovers_and_persists_a_new_heartbeat(leased, monkeypatch):
    store, lease, other = leased
    before = row(store, lease)
    calls, failed, renewed, rejected = observe_calls(store, monkeypatch)
    other.execute("BEGIN IMMEDIATE")
    heartbeat = context(store, lease)
    def body():
        assert failed.wait(2), "the real SQLite lock was not exercised"
        other.rollback()
        assert renewed.wait(2), "heartbeat did not resume after the writer lock cleared"
    heartbeat.heartbeat_during(body)
    after = row(store, lease)
    assert len(calls) >= 2
    assert after["heartbeat_at_ms"] > before["heartbeat_at_ms"]
    assert after["lease_expiry_ms"] > before["lease_expiry_ms"]
    assert after["lease_owner"] == before["lease_owner"]
    assert after["lease_epoch"] == before["lease_epoch"]
    assert heartbeat.stop_reason is None


def test_persistent_sqlite_lock_exhausts_a_finite_retry_budget(leased, monkeypatch, caplog):
    store, lease, other = leased
    before = row(store, lease)
    calls, failed, renewed, rejected = observe_calls(store, monkeypatch)
    other.execute("BEGIN IMMEDIATE")
    heartbeat = context(store, lease)
    def body():
        heartbeat._thread.join(2)
        assert not heartbeat._thread.is_alive()
    with caplog.at_level(logging.WARNING, logger=runtime.__name__):
        heartbeat.heartbeat_during(body)
    other.rollback()
    assert len(calls) == 3
    assert not renewed.is_set()
    assert row(store, lease) == before
    assert heartbeat.stop_reason == "storage_retry_exhausted"
    assert "storage_retry_exhausted" in caplog.text
    assert "database is locked" not in caplog.text


@pytest.mark.parametrize("takeover", [False, True])
def test_retry_cannot_revive_a_lease_expired_or_superseded_behind_the_writer_lock(leased, monkeypatch, takeover):
    store, lease, other = leased
    before = row(store, lease)
    calls, failed, renewed, rejected = observe_calls(store, monkeypatch)
    other.execute("BEGIN IMMEDIATE")
    heartbeat = context(store, lease)
    expected = {}
    def body():
        assert failed.wait(2)
        if takeover:
            other.execute("UPDATE durable_runs SET lease_owner='successor',lease_epoch=lease_epoch+1 "
                          "WHERE run_id=?", (lease.run_id,))
        else:
            other.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE run_id=?", (lease.run_id,))
        other.commit()
        expected.update(row(store, lease))
        assert rejected.wait(2), "retry did not validate the committed lease state"
        heartbeat._thread.join(2)
    heartbeat.heartbeat_during(body)
    assert len(calls) == 2
    assert not renewed.is_set()
    assert row(store, lease) == expected
    assert row(store, lease)["heartbeat_at_ms"] == before["heartbeat_at_ms"]
    assert heartbeat.stop_reason == ("lease_fenced" if takeover else "lease_expired")


def test_store_rejects_an_expired_lease_even_without_a_successor(leased):
    store, lease, other = leased
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE run_id=?", (lease.run_id,))
    store._conn.commit()
    before = row(store, lease)
    with pytest.raises(TaskStoreError, match="lease_expired"):
        store._heartbeat_durable_lease(lease.run_id, lease.owner, lease.epoch, 10_000)
    assert row(store, lease) == before


def test_expiry_is_sampled_after_a_blocking_begin_immediate(leased, monkeypatch):
    from reverse_agent.platform_v1 import run_store
    store, lease, other = leased
    clock = [1000]
    monkeypatch.setattr(run_store, "_utc_now_ms", lambda: clock[0])
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=2000 WHERE run_id=?", (lease.run_id,))
    store._conn.commit()
    before = row(store, lease)
    store._conn.execute("PRAGMA busy_timeout = 1000")
    entered = threading.Event()
    store._conn.set_trace_callback(lambda sql: entered.set() if sql == "BEGIN IMMEDIATE" else None)
    calls, failed, renewed, rejected = observe_calls(store, monkeypatch)
    other.execute("BEGIN IMMEDIATE")
    heartbeat = context(store, lease)
    def body():
        assert entered.wait(2)
        clock[0] = 3000
        other.rollback()
        assert rejected.wait(2)
        heartbeat._thread.join(2)
    heartbeat.heartbeat_during(body)
    assert len(calls) == 1
    assert not renewed.is_set()
    assert row(store, lease) == before
    assert heartbeat.stop_reason == "lease_expired"


class StopAfterWait:
    """Deterministic cancellation at an inter-attempt wait, not inside SQL."""
    def __init__(self):
        self.stopped = False
    def is_set(self):
        return self.stopped
    def wait(self, timeout):
        self.stopped = True
        return True


def busy_error():
    cause = sqlite3.OperationalError("fixture private driver message")
    cause.sqlite_errorcode = sqlite3.SQLITE_BUSY
    error = TaskStoreError("heartbeat_durable_lease_failed:fixture private driver message")
    error.__cause__ = cause
    return error


def test_cancel_during_retry_wait_does_not_start_another_database_call():
    calls = []
    class Store:
        def _heartbeat_durable_lease(self, *args):
            calls.append(args)
            raise busy_error()
    heartbeat = runtime._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
        expiry_ms=1000, heartbeat_window_ms=100)
    heartbeat._stop_event = StopAfterWait()
    heartbeat._heartbeat_loop()
    assert len(calls) == 1
    assert heartbeat.stop_reason is None


@pytest.mark.parametrize("code", ["lease_fenced", "lease_expired", "durable_run_not_found", "other_error"])
def test_fencing_and_non_storage_errors_are_never_retried(code):
    calls = []
    class Store:
        def _heartbeat_durable_lease(self, *args):
            calls.append(args)
            # A causal BUSY must not turn a finite fencing error into a retry.
            error = TaskStoreError(f"{code}:fixture")
            error.__cause__ = busy_error().__cause__
            raise error
    heartbeat = runtime._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
        expiry_ms=1000, heartbeat_window_ms=100)
    heartbeat._stop_event = threading.Event()
    heartbeat._heartbeat_loop()
    assert len(calls) == 1
    assert heartbeat.stop_reason is not None


@pytest.mark.parametrize("error_code", [None, sqlite3.SQLITE_IOERR, sqlite3.SQLITE_FULL])
def test_error_message_alone_or_non_transient_sqlite_code_does_not_authorize_retry(error_code):
    calls = []
    class Store:
        def _heartbeat_durable_lease(self, *args):
            calls.append(args)
            cause = sqlite3.OperationalError("database is locked")
            cause.sqlite_errorcode = error_code
            error = TaskStoreError("heartbeat_durable_lease_failed:database is locked")
            error.__cause__ = cause
            raise error
    heartbeat = runtime._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
        expiry_ms=1000, heartbeat_window_ms=100)
    heartbeat._stop_event = threading.Event()
    heartbeat._heartbeat_loop()
    assert len(calls) == 1
    assert heartbeat.stop_reason == "heartbeat_error"


@pytest.mark.parametrize("error_code", [sqlite3.SQLITE_BUSY | (2 << 8), sqlite3.SQLITE_LOCKED | (1 << 8)])
def test_extended_transient_codes_recover_and_success_resets_the_failure_budget(error_code):
    calls = []
    class Store:
        def _heartbeat_durable_lease(self, *args):
            calls.append(args)
            if len(calls) in (1, 2, 4, 5):
                error = busy_error()
                error.__cause__.sqlite_errorcode = error_code
                raise error
            if len(calls) == 6:
                heartbeat._stop_event.set()
    heartbeat = runtime._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
        expiry_ms=5000, heartbeat_window_ms=10)
    heartbeat._stop_event = threading.Event()
    heartbeat._heartbeat_loop()
    assert len(calls) == 6
    assert heartbeat.stop_reason is None


def test_elapsed_monotonic_lease_budget_prevents_another_attempt(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(runtime.time, "monotonic", lambda: clock[0])
    calls = []
    class Store:
        def _heartbeat_durable_lease(self, *args):
            calls.append(args)
            raise busy_error()
    class PauseAtWait(StopAfterWait):
        def wait(self, timeout):
            clock[0] += 2.0
            return False
    heartbeat = runtime._HeartbeatContext(store=Store(), run_id="r", owner="o", epoch=1,
        expiry_ms=1000, heartbeat_window_ms=100)
    heartbeat._stop_event = PauseAtWait()
    heartbeat._heartbeat_loop()
    assert len(calls) == 1
    assert heartbeat.stop_reason == "lease_expired"

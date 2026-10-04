"""Durable window fences across independent hosts; no providers or side effects."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def payload(policy_id="window-policy", **changes):
    now = datetime.now(timezone.utc)
    result = {
        "policy_id": policy_id, "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 4, "max_retries": 1,
        "confirmation": "ACTIVATE",
    }
    result.update(changes)
    return result


def host(db_path):
    store = TaskStore(str(db_path))
    control = PlatformControlStore(store)
    return store, control, AutonomyService(control_store=control, capabilities=CapabilityRegistry())


def test_independent_hosts_cannot_both_activate_after_stale_preflight(tmp_path, monkeypatch):
    hosts = [host(tmp_path / "race.sqlite3") for _ in range(2)]
    barrier = Barrier(2)
    for _, control, _ in hosts:
        # Both hosts may have observed no active window before either INSERT.
        # The durable transaction must still arbitrate the competing requests.
        monkeypatch.setattr(control, "active_window", lambda: None)
    def activate(index):
        barrier.wait(timeout=5)
        try:
            return hosts[index][2].activate(payload(f"policy-{index}"))
        except TaskStoreError as exc:
            return exc
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(activate, range(2)))
    assert sum(not isinstance(item, Exception) for item in results) == 1
    assert sum(isinstance(item, TaskStoreError) and "active_window_already_exists" in str(item) for item in results) == 1
    rows = hosts[0][1].list_windows()
    assert len(rows) == 1 and rows[0].status == "ACTIVE"


def test_future_start_reserves_the_single_active_window(tmp_path):
    _, control, service = host(tmp_path / "scheduled.sqlite3")
    future = service.activate(payload(starts_at=(datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()))
    assert control.active_window() is None
    with pytest.raises(TaskStoreError, match="active_window_already_exists"):
        service.activate(payload("competing-policy"))
    assert control.list_windows() == (future,)
    assert not service.authorize(window_id=future.id, operation="execute_task",
        repository="dddd2024/Nerelan", subject_id="scheduled-task", input_payload={})


def test_concurrent_identical_activation_is_one_durable_revision(tmp_path):
    hosts = [host(tmp_path / "replay-race.sqlite3") for _ in range(2)]
    barrier = Barrier(2)
    data = payload()
    def activate(index):
        barrier.wait(timeout=5)
        return hosts[index][2].activate(data)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(activate, range(2)))
    assert results[0] == results[1]
    assert results[0].tasks_started == 0 and results[0].retries_used == 0
    assert hosts[0][1].list_windows() == (results[0],)


def test_replay_after_actual_expiry_returns_expired_history(tmp_path, monkeypatch):
    import reverse_agent.platform_v1.control_store as module
    store, control, service = host(tmp_path / "expired-replay.sqlite3")
    data = payload()
    original = service.activate(data)
    store._conn.execute("UPDATE platform_autonomous_windows SET tasks_started=2 WHERE id=?", (original.id,))
    after_expiry = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    monkeypatch.setattr(module, "_utc_now", lambda: after_expiry)
    # Advance the trusted store clock past the original policy's real expiry;
    # do not create an EXPIRED row with a future expiry as the only evidence.
    normalized = service._validate_policy(data)
    replay = control.activate_window(normalized, confirmation="ACTIVATE")
    assert replay.id == original.id and replay.policy_digest == original.policy_digest
    assert replay.status == "EXPIRED" and replay.tasks_started == 2
    assert replay.stop_reason == "window_expired" and control.active_window() is None


def test_restart_replay_preserves_identity_and_spent_budgets(tmp_path):
    db = tmp_path / "restart.sqlite3"
    store, control, service = host(db)
    original_payload = payload()
    original = service.activate(original_payload)
    store._conn.execute("UPDATE platform_autonomous_windows SET tasks_started=3, tasks_completed=2, "
        "retries_used=1, observed_token_units=123, observed_cost_micro_units=456 WHERE id=?", (original.id,))
    store._conn.close()
    _, restarted, second_service = host(db)
    repeated = second_service.activate(original_payload)
    assert repeated.id == original.id and repeated.policy_digest == original.policy_digest
    assert (repeated.tasks_started, repeated.tasks_completed, repeated.retries_used,
        repeated.observed_token_units, repeated.observed_cost_micro_units) == (3, 2, 1, 123, 456)
    assert restarted.list_windows() == (repeated,)


@pytest.mark.parametrize("changed", [{"max_tasks": 5}, {"owner_identity": "other"}, {"capabilities": ["validate_task"]}])
def test_revision_digest_conflict_cannot_mutate_window(tmp_path, changed):
    _, control, service = host(tmp_path / "immutable.sqlite3")
    data = payload()
    original = service.activate(data)
    with pytest.raises(TaskStoreError, match="policy_revision_conflict"):
        service.activate({**data, **changed})
    assert control.get_window(original.id) == original
    assert len(control.list_windows()) == 1


@pytest.mark.parametrize("terminal", ["STOPPED", "BLOCKED", "COMPLETED", "EXPIRED"])
def test_historical_revision_replay_never_reactivates_or_resets(tmp_path, terminal):
    store, control, service = host(tmp_path / "terminal.sqlite3")
    data = payload()
    original = service.activate(data)
    store._conn.execute("UPDATE platform_autonomous_windows SET status=?, tasks_started=2, "
        "retries_used=1 WHERE id=?", (terminal, original.id))
    current = service.activate(payload("new-policy"))
    historical = service.activate(data)
    assert historical.id == original.id and historical.status == terminal
    assert historical.tasks_started == 2 and historical.retries_used == 1
    assert control.active_window().id == current.id
    assert not service.authorize(window_id=historical.id, operation="execute_task",
        repository="dddd2024/Nerelan", subject_id="old-task", input_payload={})


def test_authorization_denies_stale_active_snapshot_when_another_window_is_current(tmp_path):
    store, control, service = host(tmp_path / "legacy-state.sqlite3")
    first = service.activate(payload())
    control.stop_window(first.id)
    second = service.activate(payload("second-policy"))
    # Emulate a legacy/crash state: an expired row still says ACTIVE until the
    # active-window observation expires it. An unrelated active row is present.
    store._conn.execute("UPDATE platform_autonomous_windows SET status='ACTIVE', expires_at=? WHERE id=?",
        ((datetime.now(timezone.utc) - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), first.id))
    assert not service.authorize(window_id=first.id, operation="execute_task",
        repository="dddd2024/Nerelan", subject_id="old-task", input_payload={"task_id": "old-task"})
    assert control.get_window(first.id).status == "EXPIRED"
    assert control.active_window().id == second.id
    receipt = control.list_receipts(window_id=first.id)[0]
    assert receipt.decision == "denied" and receipt.reason == "window_not_active"
    assert receipt.subject_id == "old-task" and receipt.input_digest


def test_expired_row_is_retired_atomically_before_new_activation(tmp_path):
    store, control, service = host(tmp_path / "expiry.sqlite3")
    first = service.activate(payload())
    store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?",
        ((datetime.now(timezone.utc) - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), first.id))
    second = service.activate(payload("next-policy"))
    assert control.get_window(first.id).status == "EXPIRED"
    assert control.get_window(first.id).stop_reason == "window_expired"
    assert control.active_window().id == second.id


def test_activation_insert_failure_rolls_back_the_transaction(tmp_path):
    store, control, service = host(tmp_path / "persistence.sqlite3")
    store._conn.execute("CREATE TRIGGER reject_window BEFORE INSERT ON platform_autonomous_windows "
        "BEGIN SELECT RAISE(ABORT, 'fixture_storage_failure'); END")
    with pytest.raises(TaskStoreError, match="window_activation_failed"):
        service.activate(payload())
    assert not store._conn.in_transaction and not control.list_windows()
    store._conn.execute("DROP TRIGGER reject_window")
    assert service.activate(payload()).status == "ACTIVE"

"""External operation journal invariants (#1191 / GPT Round17).

Key integrity: an idempotency key binds exactly one (digest, operation,
run, task) scope; conflicting or historically duplicated keys fail closed
without mutating evidence.  Monotonic receipts: only PENDING may become
terminal; terminal receipts accept only an exact replay.
"""

from __future__ import annotations

import dataclasses
import threading
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _make_store(tmp_path: Path) -> TaskStore:
    return TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))


def _leased_task(store: TaskStore, owner: str = "w1") -> tuple[Any, Any]:
    task = store.create_task(
        title="extop-invariants",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id, lease_owner=owner,
    )
    return task, lease


def _record(store: TaskStore, task: Any, lease: Any, **overrides: Any) -> Any:
    kwargs: dict[str, Any] = {
        "operation_key": f"single-exec-{task.id}",
        "idempotency_key": "idem-1",
        "request_digest": "digest-1",
        "run_id": lease.run_id,
        "task_id": task.id,
        "owner": lease.owner,
        "epoch": lease.epoch,
    }
    kwargs.update(overrides)
    return store._record_external_operation(**kwargs)


def _reconcile(store: TaskStore, lease: Any, op: Any, result: str, ext_id: str) -> Any:
    return store._reconcile_external_operation(
        operation_id=op.operation_id,
        external_operation_id=ext_id,
        result_state=result,
        run_id=lease.run_id,
        owner=lease.owner,
        epoch=lease.epoch,
    )


def _rows(store: TaskStore, idempotency_key: str) -> list[dict[str, Any]]:
    return [
        dict(r) for r in store._conn.execute(
            "SELECT * FROM durable_external_operations WHERE idempotency_key = ? "
            "ORDER BY operation_id",
            (idempotency_key,),
        ).fetchall()
    ]


def _prevents(store: TaskStore, lease: Any, key: str, digest: str) -> bool:
    return store._external_operation_prevents_dispatch(
        key, digest, run_id=lease.run_id, owner=lease.owner, epoch=lease.epoch,
    )


def _assert_next_intent_works(store: TaskStore, task: Any, lease: Any) -> None:
    assert not store._conn.in_transaction
    op = _record(store, task, lease, idempotency_key="idem-next", request_digest="d-next")
    assert op.state == "PENDING"
    assert len(_rows(store, "idem-next")) == 1


def test_same_key_same_digest_replays_pending(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op1 = _record(store, task, lease)
    op2 = _record(store, task, lease)
    assert dataclasses.asdict(op2) == dataclasses.asdict(op1)
    assert op1.state == "PENDING"
    assert len(_rows(store, "idem-1")) == 1


def test_same_key_different_digest_conflicts_and_blocks_dispatch(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op1 = _record(store, task, lease)
    before = _rows(store, "idem-1")

    assert _prevents(store, lease, "idem-1", "digest-other") is True
    with pytest.raises(TaskStoreError, match="external_operation_idempotency_conflict"):
        _record(store, task, lease, request_digest="digest-other")

    assert _rows(store, "idem-1") == before
    assert before[0]["operation_id"] == op1.operation_id
    _assert_next_intent_works(store, task, lease)


@pytest.mark.parametrize("field", ["operation_key", "task_id", "run_id"])
def test_same_key_changed_scope_conflicts(tmp_path, field: str) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    _record(store, task, lease)
    before = _rows(store, "idem-1")

    overrides: dict[str, Any] = {field: "other-scope"}
    if field == "run_id":
        # Record against a different, validly leased run on the same key.
        _task2, lease2 = _leased_task(store, owner="w2")
        overrides = {
            "run_id": lease2.run_id, "task_id": task.id,
            "owner": lease2.owner, "epoch": lease2.epoch,
        }
    with pytest.raises(TaskStoreError, match="external_operation_idempotency_conflict"):
        _record(store, task, lease, **overrides)

    assert _rows(store, "idem-1") == before
    _assert_next_intent_works(store, task, lease)


def test_success_is_immutable_against_contradictory_failure(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op = _record(store, task, lease)
    done = _reconcile(store, lease, op, "success", "ext-1")
    assert done.state == "SUCCESS"
    before = _rows(store, "idem-1")

    with pytest.raises(TaskStoreError, match="external_operation_terminal_conflict"):
        _reconcile(store, lease, op, "failure", "ext-1")

    assert _rows(store, "idem-1") == before
    assert before[0]["state"] == "SUCCESS"
    assert before[0]["external_operation_id"] == "ext-1"
    _assert_next_intent_works(store, task, lease)


def test_exact_terminal_replay_is_idempotent_and_changed_provider_id_rejects(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op = _record(store, task, lease)
    done = _reconcile(store, lease, op, "success", "ext-1")
    before = _rows(store, "idem-1")

    replay = _reconcile(store, lease, op, "success", "ext-1")
    assert dataclasses.asdict(replay) == dataclasses.asdict(done)
    assert _rows(store, "idem-1") == before

    with pytest.raises(TaskStoreError, match="external_operation_terminal_conflict"):
        _reconcile(store, lease, op, "success", "ext-2")
    assert _rows(store, "idem-1") == before
    _assert_next_intent_works(store, task, lease)


def test_reconciled_failure_cannot_become_success(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op = _record(store, task, lease)
    done = _reconcile(store, lease, op, "failure", op.operation_id)
    assert done.state == "RECONCILED"
    assert done.result_state == "failure"
    before = _rows(store, "idem-1")

    with pytest.raises(TaskStoreError, match="external_operation_terminal_conflict"):
        _reconcile(store, lease, op, "success", op.operation_id)
    assert _rows(store, "idem-1") == before

    replay = _reconcile(store, lease, op, "failure", op.operation_id)
    assert dataclasses.asdict(replay) == dataclasses.asdict(done)


@pytest.mark.parametrize("bad", ["", "SUCCESS", "ok", "reconciled"])
def test_invalid_result_enum_rejected_without_mutation(tmp_path, bad: str) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op = _record(store, task, lease)
    before = _rows(store, "idem-1")

    with pytest.raises(TaskStoreError, match="invalid_external_operation_result_state"):
        _reconcile(store, lease, op, bad, "ext-1")

    assert _rows(store, "idem-1") == before
    assert before[0]["state"] == "PENDING"
    # The PENDING receipt can still be legitimately resolved afterwards.
    assert _reconcile(store, lease, op, "success", "ext-1").state == "SUCCESS"


def test_legacy_duplicate_key_rows_fail_closed_and_are_preserved(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    # Inject historical duplicate rows into this disposable temp DB only.
    for op_id, digest, ts in (
        ("op-legacy-a", "digest-a", "2026-01-01T00:00:00Z"),
        ("op-legacy-b", "digest-b", "2026-01-02T00:00:00Z"),
    ):
        store._conn.execute(
            "INSERT INTO durable_external_operations "
            "(operation_id, run_id, task_id, operation_key, idempotency_key, "
            "request_digest, state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'idem-dup', ?, 'PENDING', ?, ?)",
            (op_id, lease.run_id, task.id, f"single-exec-{task.id}", digest, ts, ts),
        )
    before = _rows(store, "idem-dup")
    assert len(before) == 2

    for digest in ("digest-a", "digest-b", "digest-new"):
        assert _prevents(store, lease, "idem-dup", digest) is True
        with pytest.raises(TaskStoreError, match="external_operation_idempotency_ambiguous"):
            _record(store, task, lease, idempotency_key="idem-dup", request_digest=digest)

    assert _rows(store, "idem-dup") == before
    _assert_next_intent_works(store, task, lease)


def test_stale_epoch_remains_fenced(tmp_path) -> None:
    store = _make_store(tmp_path)
    task, lease = _leased_task(store)
    op = _record(store, task, lease)
    lease2 = store._recover_durable_lease(lease.run_id, "w2")
    assert lease2.epoch == lease.epoch + 1

    with pytest.raises(TaskStoreError, match="lease_fenced_external_op"):
        _record(store, task, lease)
    with pytest.raises(TaskStoreError, match="lease_fenced_external_op_reconcile"):
        _reconcile(store, lease, op, "success", "ext-1")
    # Existing stale-epoch dispatch helper contract: returns False.
    assert _prevents(store, lease, "idem-1", "digest-1") is False
    assert _rows(store, "idem-1")[0]["state"] == "PENDING"


def _race(stores: list[TaskStore], fn) -> list[Any]:
    barrier = threading.Barrier(len(stores))
    results: list[Any] = [None] * len(stores)

    def worker(i: int) -> None:
        barrier.wait()
        try:
            results[i] = fn(i, stores[i])
        except Exception as exc:  # noqa: BLE001 - collected for assertion
            results[i] = exc

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(stores))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return results


def test_two_connections_same_intent_yield_single_row(tmp_path) -> None:
    store_a = _make_store(tmp_path)
    task, lease = _leased_task(store_a)
    store_b = _make_store(tmp_path)

    results = _race([store_a, store_b], lambda _i, s: _record(s, task, lease))

    assert all(not isinstance(r, Exception) for r in results), results
    assert results[0].operation_id == results[1].operation_id
    assert len(_rows(store_a, "idem-1")) == 1


def test_two_connections_conflicting_digests_admit_exactly_one(tmp_path) -> None:
    store_a = _make_store(tmp_path)
    task, lease = _leased_task(store_a)
    store_b = _make_store(tmp_path)

    results = _race(
        [store_a, store_b],
        lambda i, s: _record(s, task, lease, request_digest=f"digest-{i}"),
    )

    errors = [r for r in results if isinstance(r, Exception)]
    ops = [r for r in results if not isinstance(r, Exception)]
    assert len(ops) == 1 and len(errors) == 1, results
    assert isinstance(errors[0], TaskStoreError)
    assert "external_operation_idempotency_conflict" in str(errors[0])
    rows = _rows(store_a, "idem-1")
    assert len(rows) == 1 and rows[0]["operation_id"] == ops[0].operation_id
    assert not store_b._conn.in_transaction
    _assert_next_intent_works(store_a, task, lease)

from __future__ import annotations

import json
import threading

import pytest

from reverse_agent.platform_v1.active_cancel import (
    ACTIVE_STATUSES,
    CONFIRM_EVENT_TYPE,
    REQUEST_EVENT_TYPE,
    ActiveCancelController,
    generation_digest,
)
from reverse_agent.platform_v1.run_store import TaskStore


def _active_store(path: str = ":memory:", *, status: str = "RUNNING"):
    store = TaskStore(path)
    task = store.create_task(
        title="active cancel target",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="worker-a",
        expiry_ms=600_000,
    )
    store._accept_checkpoint(
        lease.run_id,
        "PRE_PLANNER",
        "",
        1,
        lease.owner,
        lease.epoch,
    )
    store.set_state(task.id, status)
    return store, task.id, lease


def _event_count(store: TaskStore, task_id: str, event_type: str) -> int:
    return int(
        store._conn.execute(
            "SELECT COUNT(*) FROM task_events WHERE task_id = ? AND type = ?",
            (task_id, event_type),
        ).fetchone()[0]
    )


def _run_row(store: TaskStore, run_id: str) -> dict:
    return dict(
        store._conn.execute(
            "SELECT * FROM durable_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    )


def _task_row(store: TaskStore, task_id: str) -> dict:
    return dict(
        store._conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    )


def test_request_binds_exact_current_durable_generation() -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)

    outcome = controller.request_active_cancel(task_id)

    assert outcome.status == "REQUESTED"
    assert outcome.reason_code == "ACTIVE_CANCEL_REQUESTED"
    assert outcome.state is not None
    assert outcome.state.current is True
    assert outcome.state.phase == "REQUESTED"
    assert outcome.state.task_id == task_id
    assert outcome.state.run_id == lease.run_id
    assert outcome.state.lease_epoch == lease.epoch
    assert outcome.state.generation_digest == generation_digest(
        task_id=task_id,
        run_id=lease.run_id,
        lease_epoch=lease.epoch,
    )
    assert outcome.state.request_id.startswith("active-cancel-")
    assert _event_count(store, task_id, REQUEST_EVENT_TYPE) == 1


@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        ("queued", "STATUS_NOT_ACTIVE"),
        ("terminal", "STATUS_NOT_ACTIVE"),
        ("no_run", "NO_DURABLE_RUN"),
        ("no_lease", "NO_LIVE_DURABLE_LEASE"),
    ],
)
def test_request_fails_closed_without_active_live_generation(
    setup: str, reason: str
) -> None:
    if setup == "queued":
        store = TaskStore(":memory:")
        task_id = store.create_task(title="queued").id
    elif setup == "no_run":
        store = TaskStore(":memory:")
        task = store.create_task(title="no run")
        store.set_state(task.id, "RUNNING")
        task_id = task.id
    else:
        store, task_id, lease = _active_store()
        if setup == "terminal":
            store.set_state(task_id, "READY_FOR_REVIEW")
        else:
            store._conn.execute(
                "UPDATE durable_runs SET lease_owner = '' WHERE run_id = ?",
                (lease.run_id,),
            )

    before = store._conn.total_changes
    outcome = ActiveCancelController(store).request_active_cancel(task_id)

    assert outcome.status == "UNAVAILABLE"
    assert outcome.reason_code == reason
    assert outcome.state is None
    assert _event_count(store, task_id, REQUEST_EVENT_TYPE) == 0
    assert store._conn.total_changes == before


def test_same_generation_request_is_idempotent() -> None:
    store, task_id, _ = _active_store()
    controller = ActiveCancelController(store)

    first = controller.request_active_cancel(task_id)
    second = controller.request_active_cancel(task_id)

    assert first.status == "REQUESTED"
    assert second.status == "ALREADY_REQUESTED"
    assert first.state is not None and second.state is not None
    assert second.state.request_id == first.state.request_id
    assert second.state.generation_digest == first.state.generation_digest
    assert _event_count(store, task_id, REQUEST_EVENT_TYPE) == 1


def test_two_connections_racing_create_one_request(tmp_path) -> None:
    db_path = str(tmp_path / "active-cancel.sqlite3")
    first_store, task_id, _ = _active_store(db_path)
    second_store = TaskStore(db_path)
    first = ActiveCancelController(first_store)
    second = ActiveCancelController(second_store)

    barrier = threading.Barrier(2)
    results = []
    errors = []
    result_lock = threading.Lock()

    def run(controller: ActiveCancelController) -> None:
        try:
            barrier.wait(timeout=5)
            result = controller.request_active_cancel(task_id)
            with result_lock:
                results.append(result)
        except BaseException as exc:  # pragma: no cover - diagnostic path
            with result_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=run, args=(first,)),
        threading.Thread(target=run, args=(second,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not errors
    assert sorted(result.status for result in results) == [
        "ALREADY_REQUESTED",
        "REQUESTED",
    ]
    assert len({result.state.request_id for result in results if result.state}) == 1
    assert _event_count(first_store, task_id, REQUEST_EVENT_TYPE) == 1
    second_store._conn.close()
    first_store._conn.close()


def test_newer_lease_epoch_makes_old_request_stale() -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)
    first = controller.request_active_cancel(task_id)

    store._conn.execute(
        "UPDATE durable_runs SET lease_owner = ?, lease_epoch = lease_epoch + 1 "
        "WHERE run_id = ?",
        ("worker-b", lease.run_id),
    )

    stale = controller.current_state(task_id)
    assert stale is not None
    assert stale.phase == "STALE"
    assert stale.current is False
    assert controller.auto_resume_allowed(task_id) is True

    second = controller.request_active_cancel(task_id)
    assert second.status == "REQUESTED"
    assert second.state is not None and first.state is not None
    assert second.state.lease_epoch == lease.epoch + 1
    assert second.state.request_id != first.state.request_id
    assert _event_count(store, task_id, REQUEST_EVENT_TYPE) == 2


def test_read_methods_are_side_effect_free() -> None:
    store, task_id, _ = _active_store()
    controller = ActiveCancelController(store)
    assert controller.auto_resume_allowed(task_id) is True
    controller.request_active_cancel(task_id)

    before = store._conn.total_changes
    state = controller.current_state(task_id)
    allowed = controller.auto_resume_allowed(task_id)
    after = store._conn.total_changes

    assert state is not None and state.current is True
    assert allowed is False
    assert after == before


def test_exact_fenced_checkpoint_confirms_once() -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)
    requested = controller.request_active_cancel(task_id)

    first = controller.confirm_safe_boundary(
        task_id,
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )
    second = controller.confirm_safe_boundary(
        task_id,
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )

    assert requested.state is not None
    assert first.status == "CONFIRMED"
    assert first.reason_code == "ACTIVE_CANCEL_SAFE_BOUNDARY_CONFIRMED"
    assert first.state is not None
    assert first.state.phase == "CONFIRMED"
    assert first.state.current is True
    assert first.state.checkpoint == "PRE_PLANNER"
    assert first.state.request_id == requested.state.request_id
    assert second.status == "ALREADY_CONFIRMED"
    assert _event_count(store, task_id, CONFIRM_EVENT_TYPE) == 1
    assert controller.auto_resume_allowed(task_id) is False


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"lease_owner": "wrong-owner"}, "LEASE_FENCED"),
        ({"lease_epoch": 99}, "LEASE_FENCED"),
        ({"run_id": "wrong-run"}, "LEASE_FENCED"),
        ({"checkpoint": "NOT_A_CHECKPOINT"}, "CHECKPOINT_UNSAFE"),
        ({"checkpoint": "POST_PLANNER"}, "CHECKPOINT_MISMATCH"),
    ],
)
def test_confirmation_fails_closed_on_wrong_fence_or_boundary(
    overrides: dict, reason: str
) -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)
    controller.request_active_cancel(task_id)

    arguments = {
        "run_id": lease.run_id,
        "lease_owner": lease.owner,
        "lease_epoch": lease.epoch,
        "checkpoint": "PRE_PLANNER",
    }
    arguments.update(overrides)
    before = store._conn.total_changes

    outcome = controller.confirm_safe_boundary(task_id, **arguments)

    assert outcome.status == "UNAVAILABLE"
    assert outcome.reason_code == reason
    assert _event_count(store, task_id, CONFIRM_EVENT_TYPE) == 0
    assert store._conn.total_changes == before


def test_confirmation_requires_current_request() -> None:
    store, task_id, lease = _active_store()
    before = store._conn.total_changes

    outcome = ActiveCancelController(store).confirm_safe_boundary(
        task_id,
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )

    assert outcome.status == "UNAVAILABLE"
    assert outcome.reason_code == "NO_CANCEL_REQUEST"
    assert _event_count(store, task_id, CONFIRM_EVENT_TYPE) == 0
    assert store._conn.total_changes == before


def test_request_and_confirmation_metadata_is_fixed_and_sanitized() -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)
    controller.request_active_cancel(task_id)
    controller.confirm_safe_boundary(
        task_id,
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )

    rows = store._conn.execute(
        "SELECT type, title, description, raw_log, metadata FROM task_events "
        "WHERE task_id = ? AND type IN (?, ?) ORDER BY seq",
        (task_id, REQUEST_EVENT_TYPE, CONFIRM_EVENT_TYPE),
    ).fetchall()
    assert [row["type"] for row in rows] == [
        REQUEST_EVENT_TYPE,
        CONFIRM_EVENT_TYPE,
    ]
    request_meta = json.loads(rows[0]["metadata"])
    confirm_meta = json.loads(rows[1]["metadata"])
    assert set(request_meta) == {
        "request_id",
        "run_id",
        "lease_epoch",
        "generation_digest",
        "phase",
    }
    assert set(confirm_meta) == {
        "request_id",
        "run_id",
        "lease_epoch",
        "generation_digest",
        "phase",
        "checkpoint",
    }
    assert all(row["raw_log"] == "" for row in rows)
    serialized = "\n".join(
        [
            rows[0]["title"],
            rows[0]["description"],
            rows[0]["metadata"],
            rows[1]["title"],
            rows[1]["description"],
            rows[1]["metadata"],
        ]
    ).lower()
    for forbidden in (
        "worker-a",
        "worktree",
        "password",
        "secret",
        "authorization",
        "prompt",
        "response",
        "command",
    ):
        assert forbidden not in serialized


def test_protocol_does_not_mutate_runtime_truth() -> None:
    store, task_id, lease = _active_store()
    controller = ActiveCancelController(store)
    before_run = _run_row(store, lease.run_id)
    before_task = _task_row(store, task_id)
    before_task_without_time = {
        key: value for key, value in before_task.items() if key != "updated_at"
    }

    controller.request_active_cancel(task_id)
    controller.confirm_safe_boundary(
        task_id,
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )

    after_run = _run_row(store, lease.run_id)
    after_task = _task_row(store, task_id)
    after_task_without_time = {
        key: value for key, value in after_task.items() if key != "updated_at"
    }
    assert after_run == before_run
    assert after_task_without_time == before_task_without_time
    assert _event_count(store, task_id, REQUEST_EVENT_TYPE) == 1
    assert _event_count(store, task_id, CONFIRM_EVENT_TYPE) == 1


def test_all_active_statuses_admit_requests() -> None:
    for status in sorted(ACTIVE_STATUSES):
        store, task_id, _ = _active_store(status=status)
        outcome = ActiveCancelController(store).request_active_cancel(task_id)
        assert outcome.status == "REQUESTED", status

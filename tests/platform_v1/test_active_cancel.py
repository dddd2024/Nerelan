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
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def active_store(path: str = ":memory:", status: str = "RUNNING"):
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
    store._accept_checkpoint(lease.run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)
    store.set_state(task.id, status)
    return store, task.id, lease


def count_event(store, task_id, event_type):
    return int(store._conn.execute(
        "SELECT COUNT(*) FROM task_events WHERE task_id=? AND type=?",
        (task_id, event_type),
    ).fetchone()[0])


def row(store, table, key, value):
    return dict(store._conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (value,)).fetchone())


def request_event(store, task_id):
    return store._conn.execute(
        "SELECT * FROM task_events WHERE task_id=? AND type=? ORDER BY seq DESC LIMIT 1",
        (task_id, REQUEST_EVENT_TYPE),
    ).fetchone()


def confirm(controller, task_id, lease, **overrides):
    args = dict(
        run_id=lease.run_id,
        lease_owner=lease.owner,
        lease_epoch=lease.epoch,
        checkpoint="PRE_PLANNER",
    )
    args.update(overrides)
    return controller.confirm_safe_boundary(task_id, **args)


def test_request_binds_exact_live_generation_without_projecting_raw_values():
    store, task_id, lease = active_store()
    out = ActiveCancelController(store).request_active_cancel(task_id)
    assert out.status == "REQUESTED"
    assert out.state and out.state.current
    assert not hasattr(out.state, "run_id") and not hasattr(out.state, "lease_epoch")
    assert out.state.generation_digest == generation_digest(
        task_id=task_id, run_id=lease.run_id, lease_epoch=lease.epoch
    )
    assert count_event(store, task_id, REQUEST_EVENT_TYPE) == 1


@pytest.mark.parametrize("case,reason", [
    ("queued", "STATUS_NOT_ACTIVE"),
    ("terminal", "STATUS_NOT_ACTIVE"),
    ("no_run", "NO_DURABLE_RUN"),
    ("no_owner", "NO_LIVE_DURABLE_LEASE"),
    ("no_epoch", "NO_LIVE_DURABLE_LEASE"),
    ("expired", "NO_LIVE_DURABLE_LEASE"),
])
def test_request_unavailable_without_live_generation(case, reason):
    if case == "queued":
        store = TaskStore(":memory:"); task_id = store.create_task(title="queued").id
    elif case == "no_run":
        store = TaskStore(":memory:"); task_id = store.create_task(title="no run").id; store.set_state(task_id, "RUNNING")
    else:
        store, task_id, lease = active_store()
        if case == "terminal":
            store.set_state(task_id, "READY_FOR_REVIEW")
        elif case == "no_owner":
            store._conn.execute("UPDATE durable_runs SET lease_owner='' WHERE run_id=?", (lease.run_id,))
        elif case == "no_epoch":
            store._conn.execute("UPDATE durable_runs SET lease_epoch=0 WHERE run_id=?", (lease.run_id,))
        else:
            store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE run_id=?", (lease.run_id,))
    before = store._conn.total_changes
    out = ActiveCancelController(store).request_active_cancel(task_id)
    assert out.status == "UNAVAILABLE" and out.reason_code == reason
    assert count_event(store, task_id, REQUEST_EVENT_TYPE) == 0
    assert store._conn.total_changes == before


def test_same_generation_request_is_idempotent():
    store, task_id, _ = active_store(); ctl = ActiveCancelController(store)
    first, second = ctl.request_active_cancel(task_id), ctl.request_active_cancel(task_id)
    assert first.status == "REQUESTED" and second.status == "ALREADY_REQUESTED"
    assert first.state and second.state and first.state.request_id == second.state.request_id
    assert count_event(store, task_id, REQUEST_EVENT_TYPE) == 1


def test_two_connections_race_to_one_request(tmp_path):
    path = str(tmp_path / "cancel.sqlite3")
    s1, task_id, _ = active_store(path); s2 = TaskStore(path)
    controllers = [ActiveCancelController(s1), ActiveCancelController(s2)]
    barrier = threading.Barrier(2); results = []; errors = []; lock = threading.Lock()
    def run(ctl):
        try:
            barrier.wait(timeout=5); value = ctl.request_active_cancel(task_id)
            with lock: results.append(value.status)
        except BaseException as exc:
            with lock: errors.append(exc)
    threads = [threading.Thread(target=run, args=(ctl,)) for ctl in controllers]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)
    assert not errors
    assert sorted(results) == ["ALREADY_REQUESTED", "REQUESTED"]
    assert count_event(s1, task_id, REQUEST_EVENT_TYPE) == 1
    s2._conn.close(); s1._conn.close()


def test_new_epoch_makes_old_request_stale_and_allows_resume():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store)
    first = ctl.request_active_cancel(task_id)
    store._conn.execute(
        "UPDATE durable_runs SET lease_owner='worker-b',lease_epoch=lease_epoch+1,lease_expiry_ms=lease_expiry_ms+600000 WHERE run_id=?",
        (lease.run_id,),
    )
    state = ctl.current_state(task_id)
    assert state and state.phase == "STALE" and not state.current and ctl.auto_resume_allowed(task_id)
    second = ctl.request_active_cancel(task_id)
    assert first.state and second.state and first.state.request_id != second.state.request_id


def test_valid_request_remains_hold_after_expiry_but_confirmation_requires_live_lease():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store)
    ctl.request_active_cancel(task_id)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE run_id=?", (lease.run_id,))
    state = ctl.current_state(task_id)
    assert state and state.current and ctl.auto_resume_allowed(task_id) is False
    before = store._conn.total_changes
    out = confirm(ctl, task_id, lease)
    assert out.status == "UNAVAILABLE" and out.reason_code == "NO_LIVE_DURABLE_LEASE"
    assert count_event(store, task_id, CONFIRM_EVENT_TYPE) == 0 and store._conn.total_changes == before


def test_read_methods_are_zero_write():
    store, task_id, _ = active_store(); ctl = ActiveCancelController(store)
    ctl.request_active_cancel(task_id); before = store._conn.total_changes
    assert ctl.current_state(task_id) and ctl.auto_resume_allowed(task_id) is False
    assert store._conn.total_changes == before


def test_exact_fenced_checkpoint_confirms_once():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store)
    requested = ctl.request_active_cancel(task_id)
    first, second = confirm(ctl, task_id, lease), confirm(ctl, task_id, lease)
    assert requested.state and first.state
    assert first.status == "CONFIRMED" and first.state.request_id == requested.state.request_id
    assert second.status == "ALREADY_CONFIRMED"
    assert count_event(store, task_id, CONFIRM_EVENT_TYPE) == 1


@pytest.mark.parametrize("overrides,reason", [
    ({"lease_owner": "wrong"}, "LEASE_FENCED"),
    ({"lease_epoch": 999}, "LEASE_FENCED"),
    ({"run_id": "wrong"}, "LEASE_FENCED"),
    ({"checkpoint": "NOPE"}, "CHECKPOINT_UNSAFE"),
    ({"checkpoint": "POST_PLANNER"}, "CHECKPOINT_MISMATCH"),
])
def test_confirmation_fences_wrong_generation_or_boundary(overrides, reason):
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    before = store._conn.total_changes; out = confirm(ctl, task_id, lease, **overrides)
    assert out.status == "UNAVAILABLE" and out.reason_code == reason
    assert count_event(store, task_id, CONFIRM_EVENT_TYPE) == 0 and store._conn.total_changes == before


def test_confirmation_requires_request():
    store, task_id, lease = active_store(); out = confirm(ActiveCancelController(store), task_id, lease)
    assert out.reason_code == "NO_CANCEL_REQUEST" and count_event(store, task_id, CONFIRM_EVENT_TYPE) == 0


def test_missing_checkpoint_history_fails_closed():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    store._conn.execute("DELETE FROM durable_checkpoint_history WHERE run_id=?", (lease.run_id,))
    before = store._conn.total_changes; out = confirm(ctl, task_id, lease)
    assert out.reason_code == "CHECKPOINT_EVIDENCE_MISSING"
    assert count_event(store, task_id, CONFIRM_EVENT_TYPE) == 0 and store._conn.total_changes == before


def test_duplicate_checkpoint_history_is_ambiguous():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    store._conn.execute(
        "INSERT INTO durable_checkpoint_history(checkpoint_id,run_id,checkpoint_name,artifact_digest,role_attempt,created_at) VALUES(?,?,?,?,?,?)",
        ("cp-duplicate", lease.run_id, "PRE_PLANNER", "", 1, "2026-09-13T00:00:00Z"),
    )
    before = store._conn.total_changes; out = confirm(ctl, task_id, lease)
    assert out.reason_code == "CHECKPOINT_EVIDENCE_AMBIGUOUS"
    assert count_event(store, task_id, CONFIRM_EVENT_TYPE) == 0 and store._conn.total_changes == before


@pytest.mark.parametrize("field,value", [
    ("generation_digest", "0" * 64),
    ("request_id", "active-cancel-wrong"),
])
def test_corrupt_request_metadata_identity_fails_closed(field, value):
    store, task_id, _ = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    event = request_event(store, task_id); meta = json.loads(event["metadata"]); meta[field] = value
    store._conn.execute("UPDATE task_events SET metadata=? WHERE seq=?", (json.dumps(meta, sort_keys=True, separators=(",", ":")), event["seq"]))
    with pytest.raises(TaskStoreError, match="active_cancel_request_identity_mismatch"):
        ctl.current_state(task_id)


@pytest.mark.parametrize("field,value", [("run_id", "raw-run"), ("lease_epoch", 7)])
def test_raw_generation_fields_are_rejected_from_persisted_request_metadata(field, value):
    store, task_id, _ = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    event = request_event(store, task_id); meta = json.loads(event["metadata"]); meta[field] = value
    store._conn.execute("UPDATE task_events SET metadata=? WHERE seq=?", (json.dumps(meta, sort_keys=True, separators=(",", ":")), event["seq"]))
    with pytest.raises(TaskStoreError, match="active_cancel_request_metadata_invalid"):
        ctl.current_state(task_id)


def test_corrupt_request_event_id_fails_closed():
    store, task_id, _ = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id)
    event = request_event(store, task_id); store._conn.execute("UPDATE task_events SET id='bad' WHERE seq=?", (event["seq"],))
    with pytest.raises(TaskStoreError, match="active_cancel_request_identity_mismatch"):
        ctl.current_state(task_id)


def test_corrupt_confirmation_identity_fails_closed():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id); confirm(ctl, task_id, lease)
    event = store._conn.execute(
        "SELECT * FROM task_events WHERE task_id=? AND type=? ORDER BY seq DESC LIMIT 1",
        (task_id, CONFIRM_EVENT_TYPE),
    ).fetchone()
    meta = json.loads(event["metadata"]); meta["request_id"] = "wrong"
    store._conn.execute("UPDATE task_events SET metadata=? WHERE seq=?", (json.dumps(meta, sort_keys=True, separators=(",", ":")), event["seq"]))
    with pytest.raises(TaskStoreError, match="active_cancel_confirmation_identity_mismatch"):
        ctl.current_state(task_id)


def test_event_metadata_is_fixed_and_sanitized():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store); ctl.request_active_cancel(task_id); confirm(ctl, task_id, lease)
    rows = store._conn.execute(
        "SELECT type,title,description,raw_log,metadata FROM task_events WHERE task_id=? AND type IN (?,?) ORDER BY seq",
        (task_id, REQUEST_EVENT_TYPE, CONFIRM_EVENT_TYPE),
    ).fetchall()
    request_meta = json.loads(rows[0]["metadata"])
    confirm_meta = json.loads(rows[1]["metadata"])
    assert set(request_meta) == {"request_id", "generation_digest", "phase"}
    assert set(confirm_meta) == {"request_id", "generation_digest", "phase", "checkpoint"}
    assert "run_id" not in request_meta and "lease_epoch" not in request_meta
    assert "run_id" not in confirm_meta and "lease_epoch" not in confirm_meta
    rendered = "\n".join(str(x) for r in rows for x in r).lower()
    assert all(r["raw_log"] == "" for r in rows)
    for secret in ("worker-a", "password", "secret", "prompt", "response", "command", "worktree"):
        assert secret not in rendered


def test_protocol_preserves_runtime_and_checkpoint_truth():
    store, task_id, lease = active_store(); ctl = ActiveCancelController(store)
    before_run = row(store, "durable_runs", "run_id", lease.run_id)
    before_cp = [dict(r) for r in store._conn.execute("SELECT * FROM durable_checkpoint_history WHERE run_id=? ORDER BY seq", (lease.run_id,))]
    before_task = row(store, "tasks", "id", task_id); before_task.pop("updated_at")
    ctl.request_active_cancel(task_id); confirm(ctl, task_id, lease)
    after_task = row(store, "tasks", "id", task_id); after_task.pop("updated_at")
    assert row(store, "durable_runs", "run_id", lease.run_id) == before_run
    assert [dict(r) for r in store._conn.execute("SELECT * FROM durable_checkpoint_history WHERE run_id=? ORDER BY seq", (lease.run_id,))] == before_cp
    assert after_task == before_task


def test_all_active_statuses_admit_live_request():
    for status in sorted(ACTIVE_STATUSES):
        store, task_id, _ = active_store(status=status)
        assert ActiveCancelController(store).request_active_cancel(task_id).status == "REQUESTED", status

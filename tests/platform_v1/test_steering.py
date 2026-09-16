from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from threading import Barrier

import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.steering import (
    ADVISORY_GUIDANCE,
    APPLIED,
    CORRECTION_REQUEST,
    NEW_AUTHORITY_REQUIRED,
    OWNER_DECISION,
    PAUSE_AND_REPLAN_REQUIRED,
    PRIORITY_HINT,
    QUEUED_FOR_SAFE_POINT,
    REQUIREMENT_CHANGE_REQUEST,
    SteeringService,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _active_bundle(path: str = ":memory:", *, checkpoint: str = "PRE_PLANNER"):
    store = TaskStore(path)
    control = PlatformControlStore(store)
    goal = control.create_goal(
        title="Steerable goal",
        objective="Produce a reviewable bounded result.",
        repository="dddd2024/Nerelan",
        idempotency_key="steering-goal-v2",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )
    task = store.create_task(
        title="Steerable task",
        repository=goal.repository,
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )
    with store._lock:
        store._conn.execute(
            "INSERT INTO platform_goal_task_links "
            "(goal_id, goal_revision, plan_task_id, task_id, dependencies_json, seq) "
            "VALUES (?, ?, ?, ?, '[]', 1)",
            (goal.id, goal.revision, "T001", task.id),
        )
    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="steering-v2-test-worker",
        expiry_ms=600_000,
    )
    store._accept_checkpoint(
        lease.run_id,
        checkpoint,
        "",
        1,
        lease.owner,
        lease.epoch,
    )
    store.set_state(task.id, "RUNNING")
    service = SteeringService(store)
    return store, control, goal, store.get_task(task.id, event_limit=0), lease, service


def _payload(goal, task, lease, **updates):
    payload = {
        "steering_id": "steer-v2-1",
        "goal_id": goal.id,
        "goal_revision": goal.revision,
        "task_id": task.id,
        "run_id": lease.run_id,
        "execution_id": task.execution_id,
        "observed_checkpoint": "PRE_PLANNER",
        "kind": ADVISORY_GUIDANCE,
        "content_digest": _digest("please prioritize the validation path"),
    }
    payload.update(updates)
    return payload


def _count(store: TaskStore) -> int:
    return int(
        store._conn.execute(
            "SELECT COUNT(*) FROM platform_run_steering"
        ).fetchone()[0]
    )


def _durable_row(store: TaskStore, run_id: str) -> dict:
    return dict(
        store._conn.execute(
            "SELECT * FROM durable_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
    )


def test_advisory_steering_binds_exact_active_run_and_derives_content_ref():
    store, control, goal, task, lease, service = _active_bundle()
    before_task = store.get_task(task.id, event_limit=0)
    before_goal = control.get_goal(goal.id)
    payload = _payload(goal, task, lease)

    record = service.submit(payload)

    assert record.status == QUEUED_FOR_SAFE_POINT
    assert record.reason_code == "IN_SCOPE_GUIDANCE_QUEUED"
    assert record.sequence == 1
    assert record.goal_id == goal.id and record.goal_revision == goal.revision
    assert record.task_id == task.id and record.run_id == lease.run_id
    assert record.execution_id == task.execution_id
    assert record.observed_checkpoint == "PRE_PLANNER"
    assert record.content_digest == payload["content_digest"]
    assert record.content_ref == f"sha256:{payload['content_digest']}"
    assert store.get_task(task.id, event_limit=0).status == before_task.status
    assert control.get_goal(goal.id).status == before_goal.status
    assert _count(store) == 1


def test_same_identity_same_semantics_is_zero_write_idempotent():
    store, _, goal, task, lease, service = _active_bundle()
    first = service.submit(_payload(goal, task, lease))
    before = store._conn.total_changes

    second = service.submit(_payload(goal, task, lease))

    assert second == first
    assert store._conn.total_changes == before
    assert _count(store) == 1


def test_same_identity_different_semantics_fails_closed_zero_write():
    store, _, goal, task, lease, service = _active_bundle()
    service.submit(_payload(goal, task, lease))
    before = store._conn.total_changes

    with pytest.raises(
        TaskStoreError, match="steering_id_reused_with_different_request"
    ):
        service.submit(
            _payload(
                goal,
                task,
                lease,
                content_digest=_digest("different guidance"),
            )
        )

    assert store._conn.total_changes == before
    assert _count(store) == 1


@pytest.mark.parametrize(
    "field,bad_value,error",
    [
        ("steering_id", " steer-v2-1", "steering_id_invalid"),
        ("steering_id", "steer-v2-1 ", "steering_id_invalid"),
        ("steering_id", "steer\u0085v2", "steering_id_invalid"),
        ("steering_id", "steer\u200bv2", "steering_id_invalid"),
        ("steering_id", "steer-指导", "steering_id_invalid"),
        ("steering_id", "steer/path", "steering_id_invalid"),
        ("goal_id", "goal\\path", "steering_goal_id_invalid"),
        ("observed_checkpoint", "PRE PLANNER", "steering_observed_checkpoint_invalid"),
    ],
)
def test_machine_tokens_are_exact_ascii_and_never_normalized(
    field, bad_value, error
):
    store, _, goal, task, lease, service = _active_bundle()
    payload = _payload(goal, task, lease, **{field: bad_value})
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match=error):
        service.submit(payload)

    assert store._conn.total_changes == before
    assert _count(store) == 0


@pytest.mark.parametrize(
    "digest",
    [
        "A" * 64,
        "0" * 63,
        " " + ("0" * 64),
        ("0" * 64) + " ",
        "g" * 64,
    ],
)
def test_content_digest_must_be_exact_lowercase_sha256(digest):
    store, _, goal, task, lease, service = _active_bundle()
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_content_digest_invalid"):
        service.submit(_payload(goal, task, lease, content_digest=digest))

    assert store._conn.total_changes == before
    assert _count(store) == 0


def test_caller_cannot_supply_arbitrary_content_ref():
    store, _, goal, task, lease, service = _active_bundle()
    payload = _payload(goal, task, lease)
    payload["content_ref"] = "password:hunter2"
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_unknown_field"):
        service.submit(payload)

    assert store._conn.total_changes == before
    assert _count(store) == 0


def test_raw_secret_shaped_content_is_never_persisted():
    store, _, goal, task, lease, service = _active_bundle()
    raw_secret = "password:hunter2"
    digest = _digest(raw_secret)

    record = service.submit(
        _payload(goal, task, lease, content_digest=digest)
    )
    row = store._conn.execute(
        "SELECT * FROM platform_run_steering WHERE steering_id = ?",
        (record.steering_id,),
    ).fetchone()

    persisted = "\n".join(str(row[key]) for key in row.keys())
    assert raw_secret not in persisted
    assert record.content_ref == f"sha256:{digest}"
    assert record.content_ref in persisted


def test_payload_requires_exact_closed_field_set():
    store, _, goal, task, lease, service = _active_bundle()
    missing = _payload(goal, task, lease)
    del missing["content_digest"]

    with pytest.raises(TaskStoreError, match="steering_missing_field"):
        service.submit(missing)
    assert _count(store) == 0

    unknown = _payload(goal, task, lease)
    unknown["metadata"] = "not-allowed"
    with pytest.raises(TaskStoreError, match="steering_unknown_field"):
        service.submit(unknown)
    assert _count(store) == 0


@pytest.mark.parametrize(
    "case,error",
    [
        ("missing_goal", "steering_goal_not_found"),
        ("goal_revision", "steering_goal_revision_stale"),
        ("task_link", "steering_task_goal_binding_mismatch"),
        ("execution", "steering_task_execution_mismatch"),
        ("missing_run", "steering_run_not_found"),
        ("checkpoint", "steering_checkpoint_stale"),
        ("terminal", "steering_task_not_active"),
    ],
)
def test_stale_or_mismatched_target_fails_before_write(case, error):
    store, _, goal, task, lease, service = _active_bundle()
    payload = _payload(goal, task, lease)
    if case == "missing_goal":
        payload["goal_id"] = "goal-missing"
    elif case == "goal_revision":
        payload["goal_revision"] = goal.revision + 1
    elif case == "task_link":
        other = store.create_task(
            title="other", repository="dddd2024/Nerelan"
        )
        payload["task_id"] = other.id
        payload["execution_id"] = other.execution_id
    elif case == "execution":
        payload["execution_id"] = "exec-stale"
    elif case == "missing_run":
        payload["run_id"] = "run-missing"
    elif case == "checkpoint":
        payload["observed_checkpoint"] = "POST_PLANNER"
    elif case == "terminal":
        store.set_state(task.id, "READY_FOR_REVIEW")
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match=error):
        service.submit(payload)

    assert store._conn.total_changes == before
    assert _count(store) == 0


def test_bool_goal_revision_is_rejected_without_coercion():
    store, _, goal, task, lease, service = _active_bundle()
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_goal_revision_invalid"):
        service.submit(_payload(goal, task, lease, goal_revision=True))

    assert store._conn.total_changes == before


@pytest.mark.parametrize(
    "kind,status",
    [
        (CORRECTION_REQUEST, PAUSE_AND_REPLAN_REQUIRED),
        (REQUIREMENT_CHANGE_REQUEST, NEW_AUTHORITY_REQUIRED),
        (OWNER_DECISION, NEW_AUTHORITY_REQUIRED),
    ],
)
def test_material_guidance_is_classified_without_task_or_goal_transition(
    kind, status
):
    store, control, goal, task, lease, service = _active_bundle()
    task_before = store.get_task(task.id, event_limit=0)
    goal_before = control.get_goal(goal.id)

    record = service.submit(_payload(goal, task, lease, kind=kind))

    assert record.status == status
    assert store.get_task(task.id, event_limit=0).status == task_before.status
    assert control.get_goal(goal.id).status == goal_before.status


@pytest.mark.parametrize("kind", ["advisory_guidance", " ADVISORY_GUIDANCE"])
def test_kind_is_exact_and_not_case_or_whitespace_normalized(kind):
    store, _, goal, task, lease, service = _active_bundle()
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_kind_unsupported"):
        service.submit(_payload(goal, task, lease, kind=kind))

    assert store._conn.total_changes == before


def test_two_items_retain_deterministic_per_run_order():
    _, _, goal, task, lease, service = _active_bundle()
    first = service.submit(_payload(goal, task, lease))
    second = service.submit(
        _payload(
            goal,
            task,
            lease,
            steering_id="steer-v2-2",
            kind=PRIORITY_HINT,
            content_digest=_digest("second guidance"),
        )
    )

    assert (first.sequence, second.sequence) == (1, 2)
    assert service.list_for_run(lease.run_id) == (first, second)


def test_restart_reopens_unapplied_steering_exactly_once(tmp_path):
    path = str(tmp_path / "steering-v2.sqlite3")
    store, _, goal, task, lease, service = _active_bundle(path)
    first = service.submit(_payload(goal, task, lease))
    store._conn.close()

    reopened = TaskStore(path)
    reopened_service = SteeringService(reopened)
    record = reopened_service.get(first.steering_id)

    assert record == first
    assert record.status == QUEUED_FOR_SAFE_POINT
    assert len(reopened_service.list_for_run(lease.run_id)) == 1


def test_safe_point_application_updates_only_steering_and_is_idempotent():
    store, control, goal, task, lease, service = _active_bundle()
    queued = service.submit(_payload(goal, task, lease))
    task_before = store.get_task(task.id, event_limit=0)
    goal_before = control.get_goal(goal.id)
    run_before = _durable_row(store, lease.run_id)

    applied = service.mark_applied(
        queued.steering_id,
        run_id=lease.run_id,
        execution_id=task.execution_id,
        expected_current_checkpoint="PRE_PLANNER",
        applied_at_checkpoint="PRE_PLANNER",
    )

    assert applied.status == APPLIED
    assert applied.reason_code == "APPLIED_AT_SAFE_POINT"
    assert applied.applied_at_checkpoint == "PRE_PLANNER"
    assert store.get_task(task.id, event_limit=0) == task_before
    assert control.get_goal(goal.id) == goal_before
    assert _durable_row(store, lease.run_id) == run_before

    before = store._conn.total_changes
    repeated = service.mark_applied(
        queued.steering_id,
        run_id=lease.run_id,
        execution_id=task.execution_id,
        expected_current_checkpoint="PRE_PLANNER",
        applied_at_checkpoint="PRE_PLANNER",
    )
    assert repeated == applied
    assert store._conn.total_changes == before


def test_checkpoint_drift_rejects_application_zero_write():
    store, _, goal, task, lease, service = _active_bundle()
    queued = service.submit(_payload(goal, task, lease))
    with store._lock:
        store._conn.execute(
            "UPDATE durable_runs SET accepted_checkpoint = ? WHERE run_id = ?",
            ("POST_PLANNER", lease.run_id),
        )
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_checkpoint_stale"):
        service.mark_applied(
            queued.steering_id,
            run_id=lease.run_id,
            execution_id=task.execution_id,
            expected_current_checkpoint="PRE_PLANNER",
            applied_at_checkpoint="PRE_PLANNER",
        )

    assert store._conn.total_changes == before
    assert service.get(queued.steering_id).status == QUEUED_FOR_SAFE_POINT


def test_application_arguments_are_exact_machine_tokens():
    store, _, goal, task, lease, service = _active_bundle()
    queued = service.submit(_payload(goal, task, lease))
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_expected_checkpoint_invalid"):
        service.mark_applied(
            queued.steering_id,
            run_id=lease.run_id,
            execution_id=task.execution_id,
            expected_current_checkpoint="PRE_PLANNER ",
            applied_at_checkpoint="PRE_PLANNER ",
        )

    assert store._conn.total_changes == before


def test_nonqueued_disposition_cannot_be_marked_applied():
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(
        _payload(goal, task, lease, kind=CORRECTION_REQUEST)
    )
    before = store._conn.total_changes

    with pytest.raises(
        TaskStoreError, match="steering_disposition_not_applicable"
    ):
        service.mark_applied(
            record.steering_id,
            run_id=lease.run_id,
            execution_id=task.execution_id,
            expected_current_checkpoint="PRE_PLANNER",
            applied_at_checkpoint="PRE_PLANNER",
        )

    assert store._conn.total_changes == before
    assert service.get(record.steering_id).status == PAUSE_AND_REPLAN_REQUIRED


def test_reads_are_bounded_and_zero_write():
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(_payload(goal, task, lease))
    before = store._conn.total_changes

    assert service.get(record.steering_id) == record
    assert service.list_for_run(lease.run_id, limit=1) == (record,)
    assert store._conn.total_changes == before
    with pytest.raises(TaskStoreError, match="steering_limit_out_of_range"):
        service.list_for_run(lease.run_id, limit=0)
    with pytest.raises(TaskStoreError, match="steering_limit_out_of_range"):
        service.list_for_run(lease.run_id, limit=201)


@pytest.mark.parametrize(
    "mutation",
    [
        "content_ref",
        "sequence",
        "revision",
        "queued_applied_checkpoint",
        "applied_without_checkpoint",
        "reason",
        "created_at",
    ],
)
def test_corrupted_persisted_rows_fail_closed_on_read(mutation):
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(_payload(goal, task, lease))

    if mutation == "content_ref":
        store._conn.execute(
            "UPDATE platform_run_steering SET content_ref = ? WHERE steering_id = ?",
            ("sha256:" + ("0" * 64), record.steering_id),
        )
    elif mutation == "sequence":
        store._conn.execute(
            "UPDATE platform_run_steering SET sequence = 0 WHERE steering_id = ?",
            (record.steering_id,),
        )
    elif mutation == "revision":
        store._conn.execute(
            "UPDATE platform_run_steering SET goal_revision = 0 WHERE steering_id = ?",
            (record.steering_id,),
        )
    elif mutation == "queued_applied_checkpoint":
        store._conn.execute(
            "UPDATE platform_run_steering SET applied_at_checkpoint = ? "
            "WHERE steering_id = ?",
            ("PRE_PLANNER", record.steering_id),
        )
    elif mutation == "applied_without_checkpoint":
        store._conn.execute(
            "UPDATE platform_run_steering SET status = ?, reason_code = ? "
            "WHERE steering_id = ?",
            (APPLIED, "APPLIED_AT_SAFE_POINT", record.steering_id),
        )
    elif mutation == "reason":
        store._conn.execute(
            "UPDATE platform_run_steering SET reason_code = ? WHERE steering_id = ?",
            ("WRONG_REASON", record.steering_id),
        )
    else:
        store._conn.execute(
            "UPDATE platform_run_steering SET created_at = ? WHERE steering_id = ?",
            ("not-a-time", record.steering_id),
        )

    before = store._conn.total_changes
    with pytest.raises(TaskStoreError, match="steering_corrupt_record"):
        service.get(record.steering_id)
    assert store._conn.total_changes == before


@pytest.mark.parametrize(
    "created_at",
    [
        "2026-99-99T99:99:99Z",
        "2026-02-30T12:00:00Z",
        "2025-02-29T12:00:00Z",
        "2026-12-01T25:00:00Z",
        "2026-12-01T12:60:00Z",
        "2026-12-01T12:00:60Z",
        "2026-12-01T12:00:00.000000Z",
        "2026-12-01T12:00:00+00:00",
        " 2026-12-01T12:00:00Z",
        "2026-12-01T12:00:00z",
    ],
)
def test_corrupted_or_noncanonical_persisted_created_at_fails_closed(created_at):
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(_payload(goal, task, lease))
    store._conn.execute(
        "UPDATE platform_run_steering SET created_at = ? WHERE steering_id = ?",
        (created_at, record.steering_id),
    )
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_corrupt_record"):
        service.get(record.steering_id)

    assert store._conn.total_changes == before


def test_valid_leap_day_persisted_created_at_round_trips_exactly():
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(_payload(goal, task, lease))
    valid = "2024-02-29T12:00:00Z"
    store._conn.execute(
        "UPDATE platform_run_steering SET created_at = ? WHERE steering_id = ?",
        (valid, record.steering_id),
    )
    before = store._conn.total_changes

    decoded = service.get(record.steering_id)

    assert decoded.created_at == valid
    assert store._conn.total_changes == before


def test_two_connections_racing_same_identity_converge_to_one_record(tmp_path):
    path = str(tmp_path / "steering-v2-race.sqlite3")
    store1, _, goal, task, lease, service1 = _active_bundle(path)
    store2 = TaskStore(path)
    service2 = SteeringService(store2)
    payload = _payload(goal, task, lease)
    barrier = Barrier(3)

    def submit(service):
        barrier.wait()
        return service.submit(payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        future1 = pool.submit(submit, service1)
        future2 = pool.submit(submit, service2)
        barrier.wait()
        first = future1.result(timeout=10)
        second = future2.result(timeout=10)

    assert first == second
    assert _count(store1) == 1
    assert service1.list_for_run(lease.run_id) == (first,)


def test_schema_initialization_is_idempotent_and_uses_existing_database():
    store, _, _, _, _, service = _active_bundle()
    before = store._conn.total_changes
    again = SteeringService(store)

    assert again.list_for_run("run-none") == ()
    assert store._conn.total_changes == before
    tables = {
        row[0]
        for row in store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "platform_run_steering" in tables

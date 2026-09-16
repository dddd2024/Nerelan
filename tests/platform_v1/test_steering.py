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
        idempotency_key="steering-goal-1",
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
        lease_owner="steering-test-worker",
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
        "steering_id": "steer-1",
        "goal_id": goal.id,
        "goal_revision": goal.revision,
        "task_id": task.id,
        "run_id": lease.run_id,
        "execution_id": task.execution_id,
        "observed_checkpoint": "PRE_PLANNER",
        "kind": ADVISORY_GUIDANCE,
        "content_ref": "ref:steering-1",
        "content_digest": _digest("please prioritize the validation path"),
    }
    payload.update(updates)
    return payload


def _count(store: TaskStore) -> int:
    return int(
        store._conn.execute("SELECT COUNT(*) FROM platform_run_steering").fetchone()[0]
    )


def test_advisory_steering_binds_exact_active_run_and_queues_without_authority():
    store, control, goal, task, lease, service = _active_bundle()
    before_task = store.get_task(task.id, event_limit=0)
    before_goal = control.get_goal(goal.id)

    record = service.submit(_payload(goal, task, lease))

    assert record.status == QUEUED_FOR_SAFE_POINT
    assert record.reason_code == "IN_SCOPE_GUIDANCE_QUEUED"
    assert record.sequence == 1
    assert record.goal_id == goal.id and record.goal_revision == goal.revision
    assert record.task_id == task.id and record.run_id == lease.run_id
    assert record.execution_id == task.execution_id
    assert record.observed_checkpoint == "PRE_PLANNER"
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

    with pytest.raises(TaskStoreError, match="steering_id_reused_with_different_request"):
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
        other = store.create_task(title="other", repository="dddd2024/Nerelan")
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


@pytest.mark.parametrize(
    "kind,status",
    [
        (CORRECTION_REQUEST, PAUSE_AND_REPLAN_REQUIRED),
        (REQUIREMENT_CHANGE_REQUEST, NEW_AUTHORITY_REQUIRED),
        (OWNER_DECISION, NEW_AUTHORITY_REQUIRED),
    ],
)
def test_material_guidance_is_classified_without_task_or_goal_transition(kind, status):
    store, control, goal, task, lease, service = _active_bundle()
    task_before = store.get_task(task.id, event_limit=0)
    goal_before = control.get_goal(goal.id)

    record = service.submit(_payload(goal, task, lease, kind=kind))

    assert record.status == status
    assert store.get_task(task.id, event_limit=0).status == task_before.status
    assert control.get_goal(goal.id).status == goal_before.status


def test_two_items_retain_deterministic_per_run_order():
    _, _, goal, task, lease, service = _active_bundle()
    first = service.submit(_payload(goal, task, lease))
    second = service.submit(
        _payload(
            goal,
            task,
            lease,
            steering_id="steer-2",
            content_ref="ref:steering-2",
            content_digest=_digest("second guidance"),
        )
    )

    assert (first.sequence, second.sequence) == (1, 2)
    assert service.list_for_run(lease.run_id) == (first, second)


def test_restart_reopens_unapplied_steering_exactly_once(tmp_path):
    path = str(tmp_path / "steering.sqlite3")
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
    assert store.get_task(task.id, event_limit=0).status == task_before.status
    assert control.get_goal(goal.id).status == goal_before.status

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


def test_nonqueued_disposition_cannot_be_marked_applied():
    store, _, goal, task, lease, service = _active_bundle()
    record = service.submit(
        _payload(goal, task, lease, kind=CORRECTION_REQUEST)
    )
    before = store._conn.total_changes

    with pytest.raises(TaskStoreError, match="steering_disposition_not_applicable"):
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


def test_persistence_contains_fixed_machine_fields_not_raw_guidance():
    store, _, goal, task, lease, service = _active_bundle()
    raw_guidance = "secret-looking raw guidance must never be stored"
    service.submit(
        _payload(
            goal,
            task,
            lease,
            content_ref="ref:opaque-123",
            content_digest=_digest(raw_guidance),
        )
    )
    row = store._conn.execute("SELECT * FROM platform_run_steering").fetchone()

    assert set(row.keys()) == {
        "steering_id",
        "goal_id",
        "goal_revision",
        "task_id",
        "run_id",
        "execution_id",
        "observed_checkpoint",
        "kind",
        "content_ref",
        "content_digest",
        "status",
        "reason_code",
        "sequence",
        "created_at",
        "applied_at_checkpoint",
    }
    persisted = " ".join(str(row[key]) for key in row.keys()).lower()
    for forbidden in (
        raw_guidance.lower(),
        "password=",
        "authorization:",
        "prompt text",
        "workspace path",
        "model output",
        "metadata_json",
    ):
        assert forbidden not in persisted


def test_content_reference_is_opaque_not_free_form_path_or_text():
    _, _, goal, task, lease, service = _active_bundle()
    for bad_ref in ("/home/user/secret.txt", r"C:\\Users\\secret.txt", "free form text"):
        with pytest.raises(TaskStoreError, match="steering_content_ref_invalid"):
            service.submit(_payload(goal, task, lease, content_ref=bad_ref))


def test_two_connections_racing_same_identity_converge_to_one_record(tmp_path):
    path = str(tmp_path / "steering-race.sqlite3")
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

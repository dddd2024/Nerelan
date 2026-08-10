"""Task contract and store tests for the server-owned TaskStore."""

import os
import tempfile

import pytest

from reverse_agent.platform_v1.run_store import (
    DuplicateTaskError,
    InvalidTransitionError,
    TaskStore,
    TaskStoreError,
)


def test_create_task_generates_server_id_and_queues() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="provider-free fixture", repository="dddd2024/reverse-agent")
    assert task.id.startswith("task-")
    assert task.status == "QUEUED"
    assert task.executor_kind == "deterministic_fixture"
    assert task.execution_id == f"exec-{task.id}"
    assert len(task.events) == 1
    assert task.events[0]["type"] == "DISCOVERED"


def test_idempotency_key_prevents_duplicate() -> None:
    store = TaskStore(":memory:")
    t1 = store.create_task(title="t", idempotency_key="k-1")
    t2 = store.create_task(title="t", idempotency_key="k-1")
    assert t2.id == t1.id
    assert store.count_tasks() == 1


def test_idempotency_key_collision_different_request_raises() -> None:
    store = TaskStore(":memory:")
    store.create_task(title="first", idempotency_key="k-x")
    with pytest.raises(DuplicateTaskError):
        store.create_task(title="second", idempotency_key="k-x")


def test_find_by_idempotency_key_returns_existing() -> None:
    store = TaskStore(":memory:")
    t = store.create_task(title="t", idempotency_key="k-y")
    found = store.find_by_idempotency_key("k-y")
    assert found is not None and found.id == t.id
    assert store.find_by_idempotency_key("missing") is None
    assert store.find_by_idempotency_key("") is None


def test_valid_transitions_proceed() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    assert store.transition_to(task.id, "PREPARING_WORKSPACE").status == "PREPARING_WORKSPACE"
    assert store.transition_to(task.id, "RUNNING_FIXTURE").status == "RUNNING_FIXTURE"
    assert store.transition_to(task.id, "VALIDATING").status == "VALIDATING"
    assert store.transition_to(task.id, "READY_FOR_REVIEW_FIXTURE").status == "READY_FOR_REVIEW_FIXTURE"


def test_invalid_transition_raises() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    with pytest.raises(InvalidTransitionError):
        store.transition_to(task.id, "VALIDATING")


def test_set_state_allows_any_status() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    assert store.set_state(task.id, "BLOCKED").status == "BLOCKED"
    with pytest.raises(TaskStoreError):
        store.set_state(task.id, "NOT_A_STATUS")


def test_terminal_status_blocks_further_transition() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    store.transition_to(task.id, "FAILED")
    with pytest.raises(InvalidTransitionError):
        store.transition_to(task.id, "PREPARING_WORKSPACE")


def test_classify_failure_records_and_moves_to_terminal() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING_FIXTURE")
    updated = store.classify_failure(task.id, classification="failed", detail="boom")
    assert updated.status == "FAILED"
    assert updated.failure_classification == "failed"
    assert updated.failure_detail == "boom"


def test_changed_files_and_evidence_persist() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    store.set_changed_files(
        task.id,
        [
            {"path": "fixture.txt", "status": "added", "additions": 1, "deletions": 0, "diff_digest": "d"},
        ],
    )
    store.add_evidence(
        task.id,
        category="Validation",
        label="git_diff_check",
        value="0",
        status="pass",
        detail="ok",
        raw_json_digest="abc",
    )
    store.set_validation_result(task.id, command_id="git_diff_check", exit_code=0, output_digest="d")
    read = store.get_task(task.id)
    assert len(read.changed_files) == 1
    assert read.changed_files[0]["path"] == "fixture.txt"
    assert read.validation_exit_code == 0
    assert read.validation_output_digest == "d"
    assert len(read.evidence_refs) == 1
    assert read.evidence_refs[0]["label"] == "git_diff_check"


def test_events_are_append_only() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    store.add_event(task.id, event_type="VALIDATED", title="validated", description="ok")
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="finished")
    read = store.get_task(task.id)
    types = [e["type"] for e in read.events]
    assert types == ["DISCOVERED", "VALIDATED", "EXECUTOR_FINISHED"]


def test_list_tasks_orders_by_created_desc() -> None:
    store = TaskStore(":memory:")
    t1 = store.create_task(title="older", idempotency_key="o")
    t2 = store.create_task(title="newer", idempotency_key="n")
    tasks = store.list_tasks()
    assert len(tasks) == 2
    timestamps = [t.updated_at for t in tasks]
    assert timestamps == sorted(timestamps, reverse=True)


def test_persistence_across_store_instances() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "t.sqlite3")
        store = TaskStore(db_path=db_path)
        try:
            task = store.create_task(title="persist", idempotency_key="p")
            store.set_changed_files(task.id, [{"path": "a.txt", "status": "modified", "additions": 1, "deletions": 0, "diff_digest": ""}])
            closed = TaskStore(db_path=db_path)
            try:
                read = closed.get_task(task.id)
                assert read.title == "persist"
                assert read.status == "QUEUED"
                assert len(read.changed_files) == 1
                assert closed.count_tasks() == 1
            finally:
                closed._conn.close()
        finally:
            store._conn.close()


def test_invalid_event_type_rejected() -> None:
    store = TaskStore(":memory:")
    task = store.create_task(title="t")
    with pytest.raises(TaskStoreError):
        store.add_event(task.id, event_type="NOT_VALID", title="x")


# ---------------------------------------------------------------------------
# Concurrency probe: two threads, one shared TaskStore, two distinct tasks
# ---------------------------------------------------------------------------

def test_taskstore_concurrent_writes_two_threads(tmp_path) -> None:
    """One shared TaskStore must tolerate two worker threads that each append
    one event and one evidence row to their own task, synchronized only by
    a ``threading.Barrier(2)``. No production lock may be required merely for
    style if this probe stays stable.
    """
    import threading

    db_path = str(tmp_path / "probe.sqlite3")
    store = TaskStore(db_path=db_path)
    task_a = store.create_task(title="probe-a", idempotency_key="probe-a")
    task_b = store.create_task(title="probe-b", idempotency_key="probe-b")
    assert task_a.id != task_b.id

    barrier = threading.Barrier(2, timeout=10)
    exceptions: list[Exception] = []

    def worker(task, *, task_label: str) -> None:
        try:
            barrier.wait(10)
            store.add_event(
                task.id,
                event_type="EXECUTOR_RUNNING",
                title=f"Probe {task_label} running",
                description="concurrent probe event",
                metadata={"worker": task_label},
            )
            store.add_evidence(
                task.id,
                category="Probe",
                label=task_label,
                value="concurrent",
                status="info",
                detail="concurrent-write-probe",
                raw_json_digest="probe",
            )
            read = store.get_task(task.id)
            assert read.id == task.id
            assert any(e["type"] == "DISCOVERED" for e in read.events)
            assert any(e["type"] == "EXECUTOR_RUNNING" for e in read.events)
            assert any(ev["label"] == task_label for ev in read.evidence_refs)
        except Exception as exc:
            exceptions.append(exc)

    t1 = threading.Thread(target=worker, args=(task_a,), kwargs={"task_label": "A"})
    t2 = threading.Thread(target=worker, args=(task_b,), kwargs={"task_label": "B"})
    t1.start()
    t2.start()
    t1.join(15)
    t2.join(15)
    assert not exceptions, [str(e) for e in exceptions]

    ta = store.get_task(task_a.id)
    tb = store.get_task(task_b.id)
    assert any(e["type"] == "DISCOVERED" for e in ta.events)
    assert any(e["type"] == "EXECUTOR_RUNNING" for e in ta.events)
    assert len(ta.evidence_refs) >= 1
    assert any(e["type"] == "DISCOVERED" for e in tb.events)
    assert any(e["type"] == "EXECUTOR_RUNNING" for e in tb.events)
    assert len(tb.evidence_refs) >= 1


def test_create_task_and_execute_does_not_hold_store_lock_across_runner() -> None:
    """A blocked external runner must not prevent independent store reads."""
    import threading

    store = TaskStore(":memory:")
    runner_entered = threading.Event()
    release_runner = threading.Event()
    read_completed = threading.Event()
    execution_errors: list[Exception] = []

    def runner(task_id: str, runner_store: TaskStore) -> dict[str, object]:
        assert runner_store is store
        assert store.get_task(task_id).status == "RUNNING_FIXTURE"
        runner_entered.set()
        assert release_runner.wait(5), "runner release timed out"
        return {"success": True}

    def execute() -> None:
        try:
            store.create_task_and_execute(
                create_kwargs={"title": "lock-boundary"},
                executor_runner=runner,
            )
        except Exception as exc:
            execution_errors.append(exc)

    execution_thread = threading.Thread(target=execute)
    execution_thread.start()
    assert runner_entered.wait(5), "executor runner did not start"

    read_thread = threading.Thread(
        target=lambda: (store.count_tasks(), read_completed.set())
    )
    read_thread.start()
    read_thread.join(1)
    completed_before_release = read_completed.is_set()

    release_runner.set()
    execution_thread.join(5)
    read_thread.join(5)

    assert completed_before_release, "TaskStore read blocked behind executor runtime"
    assert not execution_errors

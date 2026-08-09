"""TaskExecutionService: single programmatic execution path tests."""

from __future__ import annotations

import os
import tempfile

import pytest

from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_execution import (
    TaskExecutionError,
    TaskExecutionOutcome,
    TaskExecutionService,
)
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


def _service(
    tmp_path,
) -> tuple[TaskStore, ExecutorRouter, TaskExecutionService]:
    db_path = str(tmp_path / "tasks.sqlite3")
    store = TaskStore(db_path=db_path)
    router = ExecutorRouter()
    return store, router, TaskExecutionService(store=store, router=router)


def test_execute_deterministic_fixture_reaches_ready_for_review_fixture(tmp_path) -> None:
    store, router, service = _service(tmp_path)
    task = store.create_task(title="exec-test", executor_kind="deterministic_fixture")

    outcome = service.execute(task.id, workspace_root=str(tmp_path / "ws"))

    assert isinstance(outcome, TaskExecutionOutcome)
    assert outcome.task_id == task.id
    assert outcome.execution_id == task.execution_id
    assert outcome.success is True
    assert outcome.validation_command_id == "git_diff_check"
    assert outcome.validation_exit_code == 0
    assert outcome.changed_files
    assert outcome.evidence_ids
    assert outcome.failure_classification == ""

    stored = store.get_task(task.id)
    assert stored.status == "READY_FOR_REVIEW_FIXTURE"
    assert stored.validation_exit_code == 0
    assert stored.validation_command_id == "git_diff_check"
    assert stored.changed_files
    assert any(e["category"] == "Validation" for e in stored.evidence_refs)
    assert any(e["category"] == "Executor" for e in stored.evidence_refs)


def test_execute_non_queued_task_raises(tmp_path) -> None:
    store, router, service = _service(tmp_path)
    task = store.create_task(title="non-queued")
    store.transition_to(task.id, "PREPARING_WORKSPACE")

    with pytest.raises(TaskExecutionError) as excinfo:
        service.execute(task.id, workspace_root=str(tmp_path / "ws"))
    assert "task_not_queued" in str(excinfo.value)


def test_execute_unknown_task_raises(tmp_path) -> None:
    store, router, service = _service(tmp_path)
    with pytest.raises(TaskExecutionError) as excinfo:
        service.execute("task-nonexistent", workspace_root=str(tmp_path / "ws"))
    assert "task_not_found" in str(excinfo.value)


def test_outcome_evidence_ids_reflect_persisted_records(tmp_path) -> None:
    store, router, service = _service(tmp_path)
    task = store.create_task(title="ev-test")
    assert list(task.evidence_refs) == []

    outcome = service.execute(task.id, workspace_root=str(tmp_path / "ws"))

    stored = store.get_task(task.id)
    persisted_ids = [ev["id"] for ev in stored.evidence_refs]
    for ev_id in outcome.evidence_ids:
        assert ev_id in persisted_ids


def test_execute_runs_state_sequence_running_then_validating(tmp_path) -> None:
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter

    store, _, service = _service(tmp_path)
    task = store.create_task(title="seq-test")

    observed_states: list[str] = []

    class _TracingRouter(ExecutorRouter):
        def dispatch_execute(self, *, task_id: str, store, **kwargs):
            observed_states.append(store.get_task(task_id).status)
            return super().dispatch_execute(
                task_id=task_id,
                store=store,
                executor_kind=kwargs.get("executor_kind", "deterministic_fixture"),
                workspace_root=kwargs.get("workspace_root", ""),
            )

    traced_router = _TracingRouter()
    service = TaskExecutionService(store=store, router=traced_router)
    service.execute(task.id, workspace_root=str(tmp_path / "ws"))

    assert observed_states, "executor must be dispatched"
    assert all(s == "RUNNING_FIXTURE" for s in observed_states)

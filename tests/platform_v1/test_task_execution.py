"""TaskExecutionService: single programmatic execution path tests."""

from __future__ import annotations

import os
import tempfile

import pytest

from reverse_agent.platform_v1.binding_resolver import (
    BindingResolutionError,
    OpenCodeBindingResolution,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_execution import (
    TaskExecutionError,
    TaskExecutionOutcome,
    TaskExecutionService,
)
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter


def test_task_service_has_no_duplicate_execution_helpers() -> None:
    import reverse_agent.platform_v1.task_service as task_service

    assert not hasattr(task_service, "_build_executor_kwargs")
    assert not hasattr(task_service._TaskHandler, "_run_executor")


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


def test_failed_executor_outcome_uses_persisted_failure_truth(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "failed.sqlite3"))

    class _FailingRouter(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            return ExecutorResult(
                success=False,
                validation_exit_code=7,
                validation_command_id="deterministic_failure",
                validation_output_digest="failure-digest",
                validation_output_summary="deterministic validator failed",
                error="validator returned exit code 7",
                failure_classification="deterministic_validation_failure",
            )

    service = TaskExecutionService(store=store, router=_FailingRouter())
    task = store.create_task(title="failing-executor")

    outcome = service.execute(task.id, workspace_root=str(tmp_path / "ws"))
    persisted = store.get_task(task.id)

    assert persisted.failure_classification == "deterministic_validation_failure"
    assert persisted.failure_detail == "validator returned exit code 7"
    assert outcome.failure_classification == persisted.failure_classification
    assert outcome.failure_detail == persisted.failure_detail


def _resolved_binding() -> OpenCodeBindingResolution:
    return OpenCodeBindingResolution(
        binding_ref="coding-fast",
        connection_id="sense-api",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/sense-coding-fast",
        base_url="https://models.example.test/v1",
        auth_method="none",
        external_session_status="not_applicable",
    )


def test_binding_is_resolved_before_state_or_workspace_side_effects(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "bound.sqlite3"))
    workspace_root = tmp_path / "bound-workspace"
    task = store.create_task(
        title="bound execution",
        executor_kind="opencode",
        binding_ref="coding-fast",
    )
    captured: list[dict[str, object]] = []

    class _Resolver:
        def resolve(self, binding_ref: str, *, task_executor: str):
            assert binding_ref == "coding-fast"
            assert task_executor == "opencode"
            assert store.get_task(task.id).status == "QUEUED"
            assert not workspace_root.exists()
            return _resolved_binding()

    class _Router(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            captured.append(kwargs)
            return ExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="git_diff_check",
                validation_output_digest="digest",
                validation_output_summary="",
            )

    outcome = TaskExecutionService(
        store=store,
        router=_Router(),
        binding_resolver=_Resolver(),
    ).execute(task.id, workspace_root=str(workspace_root))

    assert outcome.success is True
    assert len(captured) == 1
    assert captured[0]["binding_resolution"] == _resolved_binding()
    assert "model_id" not in captured[0]


def test_binding_resolution_failure_blocks_before_executor_or_workspace(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "blocked.sqlite3"))
    workspace_root = tmp_path / "blocked-workspace"
    task = store.create_task(
        title="blocked binding",
        executor_kind="opencode",
        binding_ref="api-key-binding",
    )

    class _Resolver:
        def resolve(self, binding_ref: str, *, task_executor: str):
            raise BindingResolutionError("binding_resolution_blocked")

    class _Router(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            raise AssertionError("executor must not run")

    outcome = TaskExecutionService(
        store=store,
        router=_Router(),
        binding_resolver=_Resolver(),
    ).execute(task.id, workspace_root=str(workspace_root))

    assert outcome.success is False
    assert outcome.failure_classification == "blocked"
    assert outcome.failure_detail == "binding_resolution_blocked"
    assert store.get_task(task.id).status == "BLOCKED"
    assert not workspace_root.exists()


def test_legacy_opencode_task_still_passes_model_profile_to_executor(tmp_path) -> None:
    store = TaskStore(db_path=str(tmp_path / "legacy-open.sqlite3"))
    task = store.create_task(
        title="legacy execution",
        executor_kind="opencode",
        model_profile_ref="legacy-provider/legacy-model",
    )
    captured: list[dict[str, object]] = []

    class _Router(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            captured.append(kwargs)
            return ExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="git_diff_check",
                validation_output_digest="digest",
                validation_output_summary="",
            )

    outcome = TaskExecutionService(store=store, router=_Router()).execute(
        task.id, workspace_root=str(tmp_path / "legacy-workspace")
    )

    assert outcome.success is True
    assert captured[0]["model_id"] == "legacy-provider/legacy-model"
    assert "binding_resolution" not in captured[0]


def test_legacy_opencode_task_keeps_environment_model_fallback(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("REVERSE_AGENT_OPENCODE_MODEL", "legacy-env/model")
    store = TaskStore(db_path=str(tmp_path / "legacy-env.sqlite3"))
    task = store.create_task(
        title="legacy environment execution",
        executor_kind="opencode",
    )
    captured: list[dict[str, object]] = []

    class _Router(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            captured.append(kwargs)
            return ExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="git_diff_check",
                validation_output_digest="digest",
                validation_output_summary="",
            )

    outcome = TaskExecutionService(store=store, router=_Router()).execute(
        task.id, workspace_root=str(tmp_path / "legacy-env-workspace")
    )

    assert outcome.success is True
    assert captured[0]["model_id"] == "legacy-env/model"
    assert "binding_resolution" not in captured[0]


def test_execute_sequential_team_rejects_non_opencode_executor_kind(tmp_path) -> None:
    store, router, service = _service(tmp_path)
    task = store.create_task(
        title="not-opencode",
        executor_kind="deterministic_fixture",
        idempotency_key="not-opencode",
    )
    with pytest.raises(TaskExecutionError, match="task_not_opencode"):
        service.execute_sequential_team(
            task.id, workspace_root=str(tmp_path / "root")
        )

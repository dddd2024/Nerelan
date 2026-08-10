"""Single trusted programmatic execution path for an already-created TaskStore task.

Both the HTTP Task API and LangGraph worker adapter call
:class:`TaskExecutionService.execute`. The service owns the entire lifecycle
from ``QUEUED`` through executor dispatch, validation persistence, evidence
recording, and terminal status. It never synthesizes a new executor kind.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Any, Mapping

from .binding_resolver import BindingResolver
from .run_store import (
    InvalidTransitionError,
    TaskStore,
    TaskStoreError,
)
from .task_runtime import (
    ExecutorCallback,
    ExecutorRouter,
    ExecutorRuntimeError,
)


@dataclass(frozen=True)
class TaskExecutionOutcome:
    task_id: str
    execution_id: str
    success: bool
    validation_command_id: str
    validation_exit_code: int
    changed_files: tuple[Mapping[str, Any], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    failure_classification: str = ""
    failure_detail: str = ""


def _build_executor_kwargs(
    task: Mapping[str, Any],
    *,
    binding_resolver: Any | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    executor_kind = str(_map_task_field(task, "executor_kind", ""))
    if executor_kind == "opencode":
        binding_ref = str(_map_task_field(task, "binding_ref", ""))
        if binding_ref:
            resolver = binding_resolver or BindingResolver()
            kwargs["binding_resolution"] = resolver.resolve(
                binding_ref, task_executor=executor_kind
            )
        else:
            model_id = str(
                _map_task_field(task, "model_profile_ref", "")
            ) or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
            kwargs["model_id"] = model_id
        kwargs["repo_dir"] = os.environ.get("REVERSE_AGENT_REPO_DIR", "")
        kwargs["base_ref"] = str(_map_task_field(task, "branch", ""))
    return kwargs


def _map_task_field(task: Mapping[str, Any], key: str, default: Any) -> Any:
    if isinstance(task, Mapping):
        return task.get(key, default)
    return getattr(task, key, default)


class TaskExecutionService:
    """Execute one already-QUEUED TaskStore task through the shared executor
    router and persist the full lifecycle (status transitions, events,
    changed files, validation result, evidence).
    """

    def __init__(
        self,
        *,
        store: TaskStore,
        router: ExecutorRouter,
        binding_resolver: Any | None = None,
    ) -> None:
        self.store = store
        self.router = router
        self.binding_resolver = binding_resolver

    def execute(
        self,
        task_id: str,
        *,
        workspace_root: str,
        validation_command_id: str = "git_diff_check",
    ) -> TaskExecutionOutcome:
        try:
            task = self.store.get_task(task_id)
        except TaskStoreError:
            raise TaskExecutionError(f"task_not_found:{task_id}")

        if task.status != "QUEUED":
            raise TaskExecutionError(
                f"task_not_queued:{task_id}:{task.status}"
            )

        executor_kind = task.executor_kind
        running_status = (
            "RUNNING_FIXTURE"
            if executor_kind == "deterministic_fixture"
            else "RUNNING"
        )
        review_status = (
            "READY_FOR_REVIEW_FIXTURE"
            if executor_kind == "deterministic_fixture"
            else "READY_FOR_REVIEW"
        )

        before_evidence = tuple(ev.get("id", "") for ev in task.evidence_refs)

        try:
            executor_kwargs = _build_executor_kwargs(
                task,
                binding_resolver=self.binding_resolver,
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=str(exc),
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(
                ev.get("id", "") for ev in final.evidence_refs
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id=validation_command_id,
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        self.store.transition_to(task_id, "PREPARING_WORKSPACE")
        self.store.transition_to(task_id, running_status)
        self.store.add_event(
            task_id,
            event_type="EXECUTOR_RUNNING",
            title="Executor running",
            description=f"Executor {executor_kind} started",
            metadata={"executor_kind": executor_kind},
        )

        try:
            exec_result = self._dispatch_executor(
                task=task,
                workspace_root=workspace_root,
                validation_command_id=validation_command_id,
                executor_kwargs=executor_kwargs,
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id,
                classification="blocked",
                detail=str(exc),
            )
            final = self.store.get_task(task_id)
            after_evidence = tuple(
                ev.get("id", "")
                for ev in final.evidence_refs
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id=validation_command_id,
                validation_exit_code=-1,
                evidence_ids=tuple(after_evidence[len(before_evidence):]),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        if exec_result["success"]:
            self.store.transition_to(task_id, "VALIDATING")
            self.store.transition_to(task_id, review_status)
            self.store.add_event(
                task_id,
                event_type="VALIDATED",
                title="Validation passed",
                description=f"{exec_result['validation_command_id']} passed",
                metadata={
                    "validation_exit_code": exec_result["validation_exit_code"],
                },
            )
        else:
            classification = (
                "blocked"
                if "unapproved" in exec_result.get("error", "")
                else exec_result.get("failure_classification", "failed")
            )
            if classification == "":
                classification = "failed"
            self.store.classify_failure(
                task_id,
                classification=classification,
                detail=exec_result.get("error", "execution failed"),
            )
            self.store.add_event(
                task_id,
                event_type="EXECUTOR_FINISHED",
                title="Executor finished",
                description=exec_result.get("error", "execution failed"),
                metadata={
                    "validation_exit_code": exec_result["validation_exit_code"],
                },
            )

        final = self.store.get_task(task_id)
        after_evidence = tuple(ev.get("id", "") for ev in final.evidence_refs)

        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=final.execution_id,
            success=exec_result["success"],
            validation_command_id=exec_result["validation_command_id"],
            validation_exit_code=exec_result["validation_exit_code"],
            changed_files=tuple(final.changed_files),
            evidence_ids=tuple(after_evidence[len(before_evidence):]),
            failure_classification=final.failure_classification,
            failure_detail=final.failure_detail,
        )

    def _dispatch_executor(
        self,
        *,
        task: Any,
        workspace_root: str,
        validation_command_id: str,
        executor_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.router.dispatch_execute(
            task_id=task.id,
            store=self.store,
            executor_kind=task.executor_kind,
            workspace_root=workspace_root,
            event_callback=self._store_event_callback,
            **executor_kwargs,
        )
        self.store.set_changed_files(task.id, result.changed_files)
        self.store.set_validation_result(
            task.id,
            command_id=result.validation_command_id,
            exit_code=result.validation_exit_code,
            output_digest=result.validation_output_digest,
        )
        self.store.add_evidence(
            task.id,
            category="Validation",
            label=result.validation_command_id,
            value=str(result.validation_exit_code),
            status="pass" if result.validation_exit_code == 0 else "fail",
            detail=result.validation_output_summary,
            raw_json_digest=result.validation_output_digest,
        )
        executor_detail = (
            "fixture/provider-free executor"
            if task.executor_kind == "deterministic_fixture"
            else task.executor_kind
        )
        self.store.add_evidence(
            task.id,
            category="Executor",
            label="executor_kind",
            value=task.executor_kind,
            status="pass",
            detail=executor_detail,
        )
        return {
            "success": result.success,
            "validation_command_id": result.validation_command_id,
            "validation_exit_code": result.validation_exit_code,
            "validation_output_digest": result.validation_output_digest,
            "changed_files": result.changed_files,
            "error": result.error,
            "failure_classification": getattr(result, "failure_classification", ""),
        }

    def _store_event_callback(self, task_id: str, event: dict[str, Any]) -> None:
        try:
            self.store.add_event(
                task_id,
                event_type=event.get("type", "EXECUTOR_FINISHED"),
                title=event.get("title", "Executor event"),
                description=event.get("description", ""),
                raw_log=event.get("raw_log", ""),
                metadata=event.get("metadata"),
            )
        except Exception:
            pass


class TaskExecutionError(Exception):
    """Raised when the execution service cannot honor a request."""


def _resolve_workspace_root(store: TaskStore) -> str:
    try:
        db_path = store.db_path
        db_dir = os.path.dirname(db_path) or "."
        workspace_root = os.path.join(db_dir, "task_workspaces")
    except Exception:
        workspace_root = os.path.join(
            tempfile.gettempdir(), "issue151_task_workspaces"
        )
    os.makedirs(workspace_root, exist_ok=True)
    return workspace_root

"""Level-1 durable execution for sequential-team orchestration.

Provides checkpoint, resume, lease/fencing, and interrupted-task recovery
for ``orchestration_mode == "sequential_team"``. TaskStore remains the
single authoritative business/run truth; LangGraph checkpoints store only
the orchestration cursor.

Key invariants:
- TaskStore-accepted roles are NEVER re-invoked on recovery.
- LangGraph cursor alone NEVER promotes an unaccepted role.
- Lease epochs are monotonic fencing tokens.
- Stale epoch/owner mutations fail closed.
- Completed accepted checkpoints are append-only and never overwritten.
- Interrupted Coder preserves the linked worktree and partial diff.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .run_store import (
    InvalidTransitionError,
    TaskStore,
    TaskStoreError,
    _row_to_durable_run,
)
from .task_execution import TaskExecutionError, TaskExecutionService
from .task_runtime import ExecutorRuntimeError, ExecutorRouter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACCEPTED_CHECKPOINTS = frozenset({
    "PRE_PLANNER",
    "POST_PLANNER",
    "POST_CODER",
    "POST_REVIEWER",
    "POST_VALIDATION",
})

CHECKPOINT_ORDER: tuple[str, ...] = (
    "PRE_PLANNER",
    "POST_PLANNER",
    "POST_CODER",
    "POST_REVIEWER",
    "POST_VALIDATION",
)

CHECKPOINT_INDEX: dict[str, int] = {c: i for i, c in enumerate(CHECKPOINT_ORDER)}

RECOVERY_CLASSIFICATIONS = frozenset({
    "orphan_stale_lease",
    "interrupted",
    "recovering",
    "normal",
})

EXTERNAL_OP_STATES = frozenset({
    "PENDING",
    "DISPATCHED",
    "SUCCESS",
    "FAILED",
    "RECONCILED",
})

LEASE_DEFAULT_EXPIRY_MS = 300_000
LEASE_HEARTBEAT_WINDOW_MS = 60_000


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class DurableError(Exception):
    """Base exception for durable execution errors."""


class LeaseFencingError(DurableError):
    """Raised when a stale owner/epoch attempts to mutate durable state."""


class DurableResumeError(DurableError):
    """Raised when a resume precondition fails closed."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DurableRun:
    run_id: str
    task_id: str
    execution_id: str
    repository_base_sha: str
    worktree_path: str
    current_role: str
    role_attempt: int
    accepted_checkpoint: str
    planner_handoff_digest: str
    coder_product_diff_digest: str
    reviewer_handoff_digest: str
    validation_command_id: str
    validation_exit_code: int | None
    validation_output_digest: str
    lease_owner: str
    lease_epoch: int
    heartbeat_at_ms: int
    lease_expiry_ms: int
    recovery_classification: str
    interrupted_at: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DurableCheckpoint:
    checkpoint_id: str
    run_id: str
    checkpoint_name: str
    artifact_digest: str
    role_attempt: int
    created_at: str


@dataclass(frozen=True)
class ExternalOperation:
    operation_id: str
    operation_key: str
    idempotency_key: str
    request_digest: str
    state: str
    external_operation_id: str
    result_state: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class LeaseHandle:
    run_id: str
    task_id: str
    execution_id: str
    owner: str
    epoch: int
    expiry_ms: int
    worktree_path: str
    repository_base_sha: str


@dataclass(frozen=True)
class ResumeContext:
    run: DurableRun
    lease: LeaseHandle
    accepted_checkpoint: str
    current_role: str
    role_attempt: int
    checkpoints: tuple[DurableCheckpoint, ...]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


def _short_uuid() -> str:
    return uuid.uuid4().hex[:12]


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checkpoint_rank(name: str) -> int:
    return CHECKPOINT_INDEX.get(name, -1)


def _json_payload(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Durable Execution Service
# ---------------------------------------------------------------------------

class DurableExecutionService:
    """Level-1 durable sequential-team execution with lease fencing.

    Wraps TaskExecutionService and TaskStore to provide:
    - durable run creation and lease acquisition;
    - epoch-based lease fencing;
    - append-only checkpoint acceptance;
    - TaskStore-wins resume semantics;
    - external operation journal;
    - startup stale-run reconciliation.
    """

    def __init__(
        self,
        *,
        store: TaskStore,
        router: ExecutorRouter,
        binding_resolver: Any | None = None,
        lease_provider: Any | None = None,
        expiry_ms: int = LEASE_DEFAULT_EXPIRY_MS,
        heartbeat_window_ms: int = LEASE_HEARTBEAT_WINDOW_MS,
    ) -> None:
        self.store = store
        self.router = router
        self.binding_resolver = binding_resolver
        self.lease_provider = lease_provider
        self.expiry_ms = expiry_ms
        self.heartbeat_window_ms = heartbeat_window_ms
        self._execution_service = TaskExecutionService(
            store=store,
            router=router,
            binding_resolver=binding_resolver,
            lease_provider=lease_provider,
        )

    # ---------------------------------------------------------------
    # First execution (non-resume)
    # ---------------------------------------------------------------

    def execute_durable_sequential_team(
        self,
        task_id: str,
        *,
        workspace_root: str,
        lease_owner: str = "local",
        repository_base_sha: str = "",
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        """Execute a new durable sequential-team run with lease acquisition.

        This is the first-execution path: the task must be QUEUED, and
        a fresh durable run + lease are created. On success the task
        reaches READY_FOR_REVIEW with POST_VALIDATION accepted.
        """
        lease = self._acquire_or_find_lease(
            task_id, lease_owner, repository_base_sha, workspace_root
        )
        try:
            return self._execute_with_lease(
                task_id,
                workspace_root,
                lease,
                checkpointer=checkpointer,
            )
        except Exception:
            self.store._release_durable_lease(lease.run_id)
            raise

    def _acquire_or_find_lease(
        self,
        task_id: str,
        lease_owner: str,
        repository_base_sha: str,
        workspace_root: str,
    ) -> LeaseHandle:
        existing = self.store._find_active_durable_run(task_id)
        if existing is not None:
            current = self.store.get_task(task_id)
            if current.status in ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"):
                raise TaskExecutionError(
                    f"durable_run_already_completed:{task_id}"
                )
            lease = self.store._recover_durable_lease(
                existing.run_id, lease_owner
            )
            return lease
        return self.store._acquire_durable_lease(
            task_id=task_id,
            execution_id=self.store.get_task(task_id).execution_id,
            lease_owner=lease_owner,
            repository_base_sha=repository_base_sha,
            worktree_path=workspace_root,
        )

    def _execute_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        lease: LeaseHandle,
        *,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        run = self.store._get_durable_run(lease.run_id)

        if run.accepted_checkpoint == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            if stored.status == "READY_FOR_REVIEW":
                from .task_execution import TaskExecutionOutcome
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=True,
                    validation_command_id=run.validation_command_id or "git_diff_check",
                    validation_exit_code=run.validation_exit_code or 0,
                )
            raise TaskExecutionError(
                f"durable_post_validation_without_ready:{task_id}"
            )

        self.store._accept_checkpoint(
            lease.run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch
        )

        outcome = self._execution_service.execute_sequential_team(
            task_id=task_id,
            workspace_root=workspace_root,
        )

        if not outcome.success:
            return outcome

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        run = self.store._get_durable_run(lease.run_id)

        if run.accepted_checkpoint in ("POST_PLANNER",):
            self.store._accept_checkpoint(
                lease.run_id, "POST_PLANNER",
                run.planner_handoff_digest, run.role_attempt,
                lease.owner, lease.epoch,
            )
        elif run.accepted_checkpoint in ("POST_CODER",):
            self.store._accept_checkpoint(
                lease.run_id, "POST_CODER",
                run.coder_product_diff_digest, run.role_attempt,
                lease.owner, lease.epoch,
            )
        elif run.accepted_checkpoint in ("POST_REVIEWER",):
            self.store._accept_checkpoint(
                lease.run_id, "POST_REVIEWER",
                run.reviewer_handoff_digest, run.role_attempt,
                lease.owner, lease.epoch,
            )

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        self.store._set_validation_result(
            lease.run_id,
            command_id=outcome.validation_command_id or "git_diff_check",
            exit_code=outcome.validation_exit_code,
            output_digest="",
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_VALIDATION", "", run.role_attempt,
            lease.owner, lease.epoch,
        )
        return outcome

    # ---------------------------------------------------------------
    # Resume
    # ---------------------------------------------------------------

    def resume_sequential_team(
        self,
        task_id: str,
        *,
        workspace_root: str,
        lease_owner: str = "local",
        repository_base_sha: str = "",
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        """Resume a durable sequential-team run from the last accepted checkpoint.

        Validates all identity invariants fail-closed. TaskStore-accepted
        roles are never re-invoked.
        """
        run = self.store._find_active_durable_run(task_id)
        if run is None:
            raise DurableResumeError(f"no_active_durable_run:{task_id}")

        stored_task = self.store.get_task(task_id)
        if stored_task.status in ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"):
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=run.validation_command_id or "git_diff_check",
                validation_exit_code=run.validation_exit_code or 0,
            )

        if stored_task.orchestration_mode != "sequential_team":
            raise DurableResumeError(
                f"invalid_orchestration_mode:{stored_task.orchestration_mode}"
            )
        if stored_task.executor_kind != "opencode":
            raise DurableResumeError(
                f"invalid_executor_kind:{stored_task.executor_kind}"
            )

        if repository_base_sha and run.repository_base_sha != repository_base_sha:
            raise DurableResumeError(
                f"base_sha_mismatch:{run.repository_base_sha}!={repository_base_sha}"
            )
        if workspace_root and run.worktree_path != workspace_root:
            raise DurableResumeError(
                f"workspace_mismatch:{run.worktree_path}!={workspace_root}"
            )

        if not Path(run.worktree_path).exists():
            raise DurableResumeError(f"worktree_not_found:{run.worktree_path}")

        lease = self.store._recover_durable_lease(run.run_id, lease_owner)

        return self._resume_with_lease(
            task_id, workspace_root, run, lease, checkpointer=checkpointer
        )

    def _resume_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        run: DurableRun,
        lease: LeaseHandle,
        *,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        accepted = run.accepted_checkpoint
        current_role = run.current_role
        role_attempt = run.role_attempt

        if accepted == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            if stored.status == "READY_FOR_REVIEW":
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=True,
                    validation_command_id=run.validation_command_id or "git_diff_check",
                    validation_exit_code=run.validation_exit_code or 0,
                )

        from .task_execution import TaskExecutionOutcome
        from reverse_agent.workflows.team_graph import (
            TeamGraphError,
            WorkerAssignment,
            WorkerExecutionResult,
            build_sequential_team_graph,
        )
        from .opencode_executor import (
            RoleContext,
            _collect_product_diff,
            _collect_final_product_files,
            _handoff_digest,
            _remove_handoff,
            _validate_plan_handoff,
            _validate_review_handoff,
            handoff_dir,
        )
        from .task_runtime import LocalValidationRunner

        executor_kwargs = _build_resume_executor_kwargs(
            stored_task=self.store.get_task(task_id),
            binding_resolver=self.binding_resolver,
            lease_provider=self.lease_provider,
        )
        try:
            executor = self.router.create_executor(
                executor_kind="opencode", **executor_kwargs
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id, classification="blocked", detail=str(exc)
            )
            final = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id="",
                validation_exit_code=-1,
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        return self._resume_roles(
            task_id=task_id,
            workspace_root=workspace_root,
            run=run,
            lease=lease,
            executor=executor,
            accepted=accepted,
            current_role=current_role,
            role_attempt=role_attempt,
            checkpointer=checkpointer,
        )

    def _resume_roles(
        self,
        *,
        task_id: str,
        workspace_root: str,
        run: DurableRun,
        lease: LeaseHandle,
        executor: Any,
        accepted: str,
        current_role: str,
        role_attempt: int,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        from reverse_agent.workflows.team_graph import (
            TeamGraphError,
            WorkerAssignment,
            WorkerExecutionResult,
            build_sequential_team_graph,
        )
        from .opencode_executor import (
            RoleContext,
            _collect_product_diff,
            _collect_final_product_files,
            _handoff_digest,
            _remove_handoff,
            _validate_plan_handoff,
            _validate_review_handoff,
            handoff_dir,
        )
        from .task_execution import TaskExecutionOutcome
        from .task_runtime import LocalValidationRunner

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)

        if accepted == "POST_REVIEWER":
            return self._resume_from_post_reviewer(
                task_id, run, lease, role_attempt
            )
        if accepted == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=run.validation_command_id or "git_diff_check",
                validation_exit_code=run.validation_exit_code or 0,
            )

        new_role_attempt = role_attempt + 1 if current_role == "coder" and accepted in (
            "PRE_PLANNER", "POST_PLANNER"
        ) else role_attempt

        baseline_product = _collect_product_diff(Path(workspace_root))
        self.store.set_changed_files(task_id, baseline_product)

        seq_worker_calls: list[str] = []
        plan_digest = run.planner_handoff_digest
        review_digest = run.reviewer_handoff_digest
        coder_product_snapshot: tuple[dict[str, Any], ...] = ()
        _seq_worker_results: list[dict[str, Any]] = []
        _seq_roles_executed: list[str] = []

        def _make_resume_role_worker(prepared_ctx: Any, handoff_dir_path: Path):
            def _role_worker(wa: "WorkerAssignment") -> "WorkerExecutionResult":
                nonlocal plan_digest, review_digest, coder_product_snapshot
                role = wa.role
                seq_worker_calls.append(role)
                role_context = RoleContext(
                    role=role,
                    task_id=wa.task_id,
                    workspace=Path(workspace_root),
                    plan_path=handoff_dir_path / "plan.md",
                    plan_digest=plan_digest,
                )
                if role == "planner":
                    handoff_dir_path.mkdir(parents=True, exist_ok=True)
                try:
                    result = executor.execute_role_prepared(
                        prepared_ctx,
                        self.store,
                        role_context=role_context,
                        event_callback=self._execution_service._store_event_callback,
                    )
                except Exception as exc:
                    _seq_roles_executed.append(role)
                    _seq_worker_results.append({
                        "role": role, "worker_id": wa.worker_id,
                        "task_id": wa.task_id, "execution_id": "",
                        "success": False, "validation_exit_code": -1,
                        "failure_classification": "executor_error",
                        "failure_detail": f"{exc.__class__.__name__}:{exc}",
                        "reasons": [f"executor_exception:{exc.__class__.__name__}"],
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id="", success=False,
                        validation_exit_code=-1,
                        failure_classification="executor_error",
                        failure_detail=f"{exc.__class__.__name__}:{exc}",
                        reasons=(f"executor_exception:{exc.__class__.__name__}",),
                    )

                if not result.success:
                    _seq_roles_executed.append(role)
                    _seq_worker_results.append({
                        "role": role, "worker_id": wa.worker_id,
                        "task_id": wa.task_id,
                        "execution_id": getattr(result, "execution_id", ""),
                        "success": False,
                        "validation_exit_code": result.validation_exit_code,
                        "failure_classification": result.failure_classification,
                        "failure_detail": result.error,
                        "reasons": [result.failure_classification or "role_failed"],
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id,
                        task_id=wa.task_id,
                        execution_id=getattr(result, "execution_id", ""),
                        success=False,
                        validation_exit_code=result.validation_exit_code,
                        failure_classification=result.failure_classification,
                        failure_detail=result.error,
                        reasons=(result.failure_classification or "role_failed",),
                    )

                if role == "planner":
                    invalid = _validate_plan_handoff(handoff_dir_path / "plan.md")
                    if invalid:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "invalid_plan_handoff",
                            "failure_detail": invalid,
                            "reasons": ["invalid_plan_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="invalid_plan_handoff",
                            failure_detail=invalid,
                            reasons=("invalid_plan_handoff",),
                        )
                    plan_digest = _handoff_digest(handoff_dir_path / "plan.md")
                    planner_post = _collect_product_diff(Path(workspace_root))
                    if planner_post != baseline_product:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "planner_product_mutation",
                            "failure_detail": "planner mutated product files",
                            "reasons": ["planner_product_mutation"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="planner_product_mutation",
                            failure_detail="planner mutated product files",
                            reasons=("planner_product_mutation",),
                        )
                elif role == "coder":
                    if not (handoff_dir_path / "plan.md").is_file():
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "missing_plan_handoff",
                            "failure_detail": "plan handoff missing when coder started",
                            "reasons": ["missing_plan_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="missing_plan_handoff",
                            failure_detail="plan handoff missing when coder started",
                            reasons=("missing_plan_handoff",),
                        )
                    coder_product_snapshot = _collect_product_diff(
                        Path(workspace_root)
                    )
                    if not coder_product_snapshot:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "no_coder_product_diff",
                            "failure_detail": "coder did not produce a product diff",
                            "reasons": ["no_coder_product_diff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="no_coder_product_diff",
                            failure_detail="coder did not produce a product diff",
                            reasons=("no_coder_product_diff",),
                        )
                elif role == "reviewer":
                    invalid_review = _validate_review_handoff(
                        handoff_dir_path / "review.md"
                    )
                    if invalid_review:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "invalid_review_handoff",
                            "failure_detail": invalid_review,
                            "reasons": ["invalid_review_handoff"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="invalid_review_handoff",
                            failure_detail=invalid_review,
                            reasons=("invalid_review_handoff",),
                        )
                    review_digest = _handoff_digest(handoff_dir_path / "review.md")
                    reviewer_post = _collect_product_diff(Path(workspace_root))
                    if reviewer_post != coder_product_snapshot:
                        _seq_roles_executed.append(role)
                        _seq_worker_results.append({
                            "role": role, "worker_id": wa.worker_id,
                            "task_id": wa.task_id,
                            "execution_id": result.execution_id,
                            "success": False, "validation_exit_code": -1,
                            "failure_classification": "reviewer_product_mutation",
                            "failure_detail": "reviewer mutated coder product diff",
                            "reasons": ["reviewer_product_mutation"],
                        })
                        return WorkerExecutionResult(
                            worker_id=wa.worker_id,
                            task_id=wa.task_id,
                            execution_id=result.execution_id,
                            success=False, validation_exit_code=-1,
                            failure_classification="reviewer_product_mutation",
                            failure_detail="reviewer mutated coder product diff",
                            reasons=("reviewer_product_mutation",),
                        )

                _seq_roles_executed.append(role)
                _seq_worker_results.append({
                    "role": role, "worker_id": wa.worker_id,
                    "task_id": wa.task_id,
                    "execution_id": result.execution_id,
                    "success": True, "validation_exit_code": result.validation_exit_code,
                    "failure_classification": "", "failure_detail": "", "reasons": [],
                })
                return WorkerExecutionResult(
                    worker_id=wa.worker_id,
                    task_id=wa.task_id,
                    execution_id=result.execution_id,
                    success=True,
                    validation_exit_code=result.validation_exit_code,
                    failure_classification="", failure_detail="",
                )

            return _role_worker

        try:
            prepared = executor.prepare_worktree_once(
                task_id, Path(workspace_root),
                self._execution_service._store_event_callback
            )
        except ExecutorRuntimeError as exc:
            self.store.classify_failure(
                task_id, classification="blocked",
                detail=f"worktree_preparation_failed:{exc}"
            )
            final = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False, validation_command_id="",
                validation_exit_code=-1,
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        handoff = handoff_dir(prepared.worktree)

        if current_role == "coder" and accepted in ("PRE_PLANNER", "POST_PLANNER"):
            self.store._set_role_attempt(
                lease.run_id, "coder", new_role_attempt, lease.owner, lease.epoch
            )
            self.store._set_recovery_classification(
                lease.run_id, "interrupted", lease.owner, lease.epoch
            )

        skip_roles: set[str] = set()
        if accepted == "POST_PLANNER":
            skip_roles.add("planner")
        if accepted == "POST_CODER":
            skip_roles.add("planner")
            skip_roles.add("coder")

        start_role = None
        if accepted == "PRE_PLANNER" or accepted == "":
            start_role = "planner"
        elif accepted == "POST_PLANNER":
            start_role = "coder"
        elif accepted == "POST_CODER":
            start_role = "reviewer"
        elif accepted == "POST_REVIEWER":
            return self._resume_from_post_reviewer(
                task_id, run, lease, new_role_attempt
            )

        base_assignment = WorkerAssignment(
            worker_id="sequential",
            role=start_role or "planner",
            task_id=task_id,
            workspace_root=workspace_root,
        )

        role_worker = _make_resume_role_worker(prepared, handoff)
        seq_graph = build_sequential_team_graph(
            worker=role_worker,
            checkpointer=checkpointer,
            skip_roles=skip_roles,
        )

        try:
            graph_result = seq_graph.invoke({
                "assignments": [base_assignment.to_dict()],
            })
        except TeamGraphError as exc:
            self._complete_sequential_team_failure(
                task_id, run, lease, _seq_roles_executed,
                _seq_worker_results, baseline_product, plan_digest,
                classification="executor_error",
                failure_detail=str(exc),
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=False,
                validation_command_id="",
                validation_exit_code=-1,
                failure_classification="executor_error",
                failure_detail=str(exc),
            )

        _remove_handoff(handoff)
        final_changed = _collect_final_product_files(prepared.worktree)
        self.store.set_changed_files(task_id, final_changed)

        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=workspace_root,
            )
        except ExecutorRuntimeError:
            val_exit, val_output, val_digest = -1, "", ""

        self.store.transition_to(task_id, "VALIDATING")
        if val_exit == 0:
            self.store.transition_to(task_id, "READY_FOR_REVIEW")
            self.store.add_event(
                task_id, event_type="VALIDATED",
                title="Sequential team validated (resume)",
                description="resume completed validation",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": "git_diff_check",
                    "plan_digest": plan_digest,
                    "review_digest": review_digest,
                },
            )
            success = True
        else:
            self.store.set_validation_result(
                task_id, command_id="git_diff_check",
                exit_code=val_exit, output_digest=val_digest,
            )
            self.store.transition_to(task_id, "FAILED")
            success = False

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        if success:
            if "planner" not in skip_roles and plan_digest:
                self.store._accept_checkpoint(
                    lease.run_id, "POST_PLANNER", plan_digest,
                    new_role_attempt, lease.owner, lease.epoch,
                )
            if "coder" not in skip_roles and coder_product_snapshot:
                coder_digest = _digest(_json_payload(list(coder_product_snapshot)))
                self.store._set_coder_product_diff_digest(
                    lease.run_id, coder_digest, lease.owner, lease.epoch
                )
                self.store._accept_checkpoint(
                    lease.run_id, "POST_CODER", coder_digest,
                    new_role_attempt, lease.owner, lease.epoch,
                )
            if "reviewer" not in skip_roles and review_digest:
                self.store._set_reviewer_handoff_digest(
                    lease.run_id, review_digest, lease.owner, lease.epoch
                )
                self.store._accept_checkpoint(
                    lease.run_id, "POST_REVIEWER", review_digest,
                    new_role_attempt, lease.owner, lease.epoch,
                )
            self.store._set_validation_result(
                lease.run_id,
                command_id="git_diff_check",
                exit_code=val_exit,
                output_digest=val_digest,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_VALIDATION", "",
                new_role_attempt, lease.owner, lease.epoch,
            )

        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=success,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="" if success else "deterministic_validation_failure",
            failure_detail="" if success else f"git_diff_check exit={val_exit}",
        )

    def _resume_from_post_reviewer(
        self, task_id: str, run: DurableRun, lease: LeaseHandle,
        role_attempt: int,
    ) -> TaskExecutionOutcome:
        from .task_execution import TaskExecutionOutcome
        stored = self.store.get_task(task_id)
        if stored.status == "READY_FOR_REVIEW":
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=run.validation_command_id or "git_diff_check",
                validation_exit_code=run.validation_exit_code or 0,
            )
        workspace = run.worktree_path
        from .task_runtime import LocalValidationRunner
        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=workspace,
            )
        except ExecutorRuntimeError:
            val_exit, val_output, val_digest = -1, "", ""

        self.store.transition_to(task_id, "VALIDATING")
        if val_exit == 0:
            self.store.transition_to(task_id, "READY_FOR_REVIEW")
            self.store.add_event(
                task_id, event_type="VALIDATED",
                title="Sequential team validated (resume from POST_REVIEWER)",
                description="post-reviewer validation passed",
                metadata={"validation_exit_code": val_exit},
            )
            self.store._set_validation_result(
                lease.run_id,
                command_id="git_diff_check",
                exit_code=val_exit,
                output_digest=val_digest,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_VALIDATION", "",
                role_attempt, lease.owner, lease.epoch,
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id="git_diff_check",
                validation_exit_code=val_exit,
            )
        self.store.set_validation_result(
            task_id, command_id="git_diff_check",
            exit_code=val_exit, output_digest=val_digest,
        )
        self.store.transition_to(task_id, "FAILED")
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
        )

    def _complete_sequential_team_failure(
        self, task_id: str, run: DurableRun, lease: LeaseHandle,
        roles_executed: list[str], role_results: list[dict[str, Any]],
        baseline_product: tuple[dict[str, Any], ...], plan_digest: str,
        *, classification: str, failure_detail: str,
    ) -> None:
        self.store.set_changed_files(task_id, baseline_product)
        try:
            self.store.classify_failure(
                task_id, classification=classification,
                detail=f"sequential team resume failed:{failure_detail}"
            )
        except TaskStoreError:
            pass
        self.store.add_event(
            task_id, event_type="EXECUTOR_FINISHED",
            title="Sequential team resume failed",
            description=failure_detail,
            metadata={"classification": classification, "roles": roles_executed},
        )

    # ---------------------------------------------------------------
    # Lease management
    # ---------------------------------------------------------------

    def acquire_lease(
        self,
        *,
        task_id: str,
        lease_owner: str,
        repository_base_sha: str = "",
        worktree_path: str = "",
    ) -> LeaseHandle:
        task = self.store.get_task(task_id)
        return self.store._acquire_durable_lease(
            task_id=task_id,
            execution_id=task.execution_id,
            lease_owner=lease_owner,
            repository_base_sha=repository_base_sha,
            worktree_path=worktree_path,
        )

    def heartbeat_lease(self, run_id: str, owner: str, epoch: int) -> None:
        self.store._heartbeat_durable_lease(run_id, owner, epoch)

    def recover_lease(
        self, task_id: str, lease_owner: str
    ) -> LeaseHandle:
        run_raw = self.store._find_active_durable_run(task_id)
        if run_raw is None:
            raise DurableError(f"no_active_durable_run:{task_id}")
        if isinstance(run_raw, dict):
            run_id = run_raw["run_id"]
        else:
            run_id = run_raw.run_id
        return self.store._recover_durable_lease(run_id, lease_owner)

    # ---------------------------------------------------------------
    # Checkpoint
    # ---------------------------------------------------------------

    def accept_checkpoint(
        self,
        run_id: str,
        checkpoint_name: str,
        *,
        artifact_digest: str = "",
        owner: str,
        epoch: int,
        role_attempt: int = 1,
    ) -> DurableCheckpoint:
        if checkpoint_name not in ACCEPTED_CHECKPOINTS:
            raise DurableError(f"invalid_checkpoint_name:{checkpoint_name}")
        return self.store._accept_checkpoint(
            run_id, checkpoint_name, artifact_digest,
            role_attempt, owner, epoch
        )

    def get_checkpoints(self, run_id: str) -> tuple[DurableCheckpoint, ...]:
        return self.store._get_durable_checkpoints(run_id)

    # ---------------------------------------------------------------
    # External operations
    # ---------------------------------------------------------------

    def record_external_operation(
        self,
        *,
        operation_key: str,
        idempotency_key: str,
        request_digest: str,
    ) -> ExternalOperation:
        """Record an external operation BEFORE dispatch.

        Returns the operation record. If an existing operation with the
        same idempotency key is found, it is returned (idempotency).
        """
        return self.store._record_external_operation(
            operation_key=operation_key,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )

    def reconcile_external_operation(
        self,
        operation_id: str,
        *,
        external_operation_id: str,
        result_state: str,
    ) -> ExternalOperation:
        """Reconcile the original operation first on ambiguous interruption.

        A second dispatch for the same durable operation is prevented
        when reconciliation proves the first operation already succeeded.
        """
        return self.store._reconcile_external_operation(
            operation_id=operation_id,
            external_operation_id=external_operation_id,
            result_state=result_state,
        )

    def prevent_duplicate_dispatch(
        self,
        *,
        idempotency_key: str,
        request_digest: str,
    ) -> bool:
        """Return True if dispatch should be prevented (operation already exists/succeeded).

        This implements at-least-once + idempotency semantics, NOT exactly-once.
        """
        return self.store._external_operation_prevents_dispatch(
            idempotency_key, request_digest
        )

    # ---------------------------------------------------------------
    # Stale-run reconciliation
    # ---------------------------------------------------------------

    def reconcile_expired_runs(
        self,
        *,
        now_ms: int | None = None,
        max_age_ms: int | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Find expired active run leases, mark stale tasks INTERRUPTED,
        record orphan/stale-lease classification.

        Does NOT automatically launch models. Returns list of reconciliation records.
        """
        return self.store._reconcile_expired_runs(
            now_ms=now_ms or _utc_now_ms(),
            max_age_ms=max_age_ms or self.expiry_ms,
        )

    # ---------------------------------------------------------------
    # Recovery info
    # ---------------------------------------------------------------

    def get_resume_context(self, task_id: str) -> ResumeContext:
        run_raw = self.store._find_active_durable_run(task_id)
        if run_raw is None:
            raise DurableError(f"no_active_durable_run:{task_id}")
        if isinstance(run_raw, dict):
            run = _row_to_durable_run(dict(run_raw))
        else:
            run = run_raw
        checkpoints = self.store._get_durable_checkpoints(run.run_id)
        return ResumeContext(
            run=run,
            lease=LeaseHandle(
                run_id=run.run_id,
                task_id=run.task_id,
                execution_id=run.execution_id,
                owner=run.lease_owner,
                epoch=run.lease_epoch,
                expiry_ms=run.lease_expiry_ms,
                worktree_path=run.worktree_path,
                repository_base_sha=run.repository_base_sha,
            ),
            accepted_checkpoint=run.accepted_checkpoint,
            current_role=run.current_role,
            role_attempt=run.role_attempt,
            checkpoints=checkpoints,
        )

    # ---------------------------------------------------------------
    # Digest helpers
    # ---------------------------------------------------------------

    def plan_handoff_digest(self, run_id: str) -> str:
        run = self.store._get_durable_run(run_id)
        return run.planner_handoff_digest

    def coder_product_diff_digest(self, run_id: str) -> str:
        run = self.store._get_durable_run(run_id)
        return run.coder_product_diff_digest

    def review_handoff_digest(self, run_id: str) -> str:
        run = self.store._get_durable_run(run_id)
        return run.reviewer_handoff_digest

    def checkpoint_sequence(self, run_id: str) -> tuple[str, ...]:
        cps = self.store._get_durable_checkpoints(run_id)
        return tuple(c.checkpoint_name for c in cps)


# ---------------------------------------------------------------------------
# Executor kwargs helper
# ---------------------------------------------------------------------------

def _build_resume_executor_kwargs(
    *,
    stored_task: Any,
    binding_resolver: Any | None = None,
    lease_provider: Any | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if stored_task.executor_kind == "opencode":
        binding_ref = getattr(stored_task, "binding_ref", "") or ""
        if binding_ref:
            resolver = binding_resolver or __import__(
                "reverse_agent.platform_v1.binding_resolver",
                fromlist=["BindingResolver"],
            ).BindingResolver()
            kwargs["binding_resolution"] = resolver.resolve(
                binding_ref, task_executor="opencode"
            )
        else:
            model_id = (
                getattr(stored_task, "model_profile_ref", "") or ""
            ) or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
            kwargs["model_id"] = model_id
        kwargs["repo_dir"] = os.environ.get("REVERSE_AGENT_REPO_DIR", "")
        kwargs["base_ref"] = getattr(stored_task, "branch", "") or ""
        if lease_provider is not None:
            kwargs["lease_provider"] = lease_provider
    return kwargs

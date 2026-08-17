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
import subprocess
import time
import threading
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
    execution_authority_sha: str
    planning_sha: str
    repository_base_sha: str
    worktree_path: str
    worktree_head_sha: str
    worktree_prepared_at: str
    current_role: str
    role_attempt: int
    accepted_checkpoint: str
    planner_handoff_digest: str
    coder_product_diff_digest: str
    reviewer_handoff_digest: str
    partial_coder_diff_digest: str
    validation_command_id: str
    validation_exit_code: int | None
    validation_output_digest: str
    lease_owner: str
    lease_epoch: int
    heartbeat_at_ms: int
    lease_expiry_ms: int
    checkpoint_db_path: str
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
    checkpoint_db_path: str = ""


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
# Test-only fault injection seam (NOT user-controllable HTTP input)
# ---------------------------------------------------------------------------
# Set to a checkpoint name to raise _CrashSimulated immediately AFTER
# that checkpoint is accepted and BEFORE the next role starts.
_CRASH_SEAM: str | None = None


class _CrashSimulated(BaseException):
    """Simulated abrupt process death for deterministic test-only fault injection.

    Inherits from BaseException (not Exception) so that generic except Exception
    handlers -- including graceful lease release -- DO NOT catch it. This models
    a real OS-level process kill: no chance for cleanup, lease persistence, or
    resource release. The persisted durable run retains the old owner/epoch/expiry
    exactly as it was at the moment of death, requiring stale-lease reconciliation.
    """


def reset_crash_seam() -> None:
    """Clear the crash injection seam. Call between tests."""
    global _CRASH_SEAM
    _CRASH_SEAM = None


def set_crash_after_checkpoint(checkpoint_name: str) -> None:
    """Arm a crash seam after a given checkpoint acceptance. Test-only."""
    global _CRASH_SEAM
    _CRASH_SEAM = checkpoint_name


def _check_crash_seam(checkpoint_name: str = "") -> None:
    global _CRASH_SEAM
    if _CRASH_SEAM is not None and checkpoint_name == _CRASH_SEAM:
        raise _CrashSimulated(f"simulated_crash_after:{_CRASH_SEAM}")


def _checkpoint_name_for_role(role: str) -> str:
    return {
        "planner": "POST_PLANNER",
        "coder": "POST_CODER",
        "reviewer": "POST_REVIEWER",
    }.get(role, "")


class _FakePreparedCtx:
    """Minimal prepared context for resume path where only a Path is available."""
    def __init__(self, worktree: Any) -> None:
        self.worktree = Path(worktree) if not isinstance(worktree, Path) else worktree
        self.execution_id = ""


# ---------------------------------------------------------------------------
# Strict checkpoint serialization helper
# ---------------------------------------------------------------------------

def _make_strict_saver(conn: Any) -> Any:
    """Create a SqliteSaver with explicit restricted serialization.

    Uses JsonPlusSerializer with allowed_msgpack_modules=None so that only
    the built-in safe msgpack types are accepted. Any attempt to revive an
    arbitrary Python object via msgpack extension types is refused.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    serde = JsonPlusSerializer(allowed_msgpack_modules=None)
    return SqliteSaver(conn=conn, serde=serde)


def _check_strict_serde_active(saver: Any) -> bool:
    """Verify the saver has strict serialization configured.

    Strict means _allowed_msgpack_modules is None (only safe built-in types
    allowed) or an empty tuple/set (no additional user modules allowed).
    """
    serde = getattr(saver, "serde", None)
    if serde is None:
        return False
    allowed = getattr(serde, "_allowed_msgpack_modules", True)
    if allowed is None:
        return True
    if isinstance(allowed, (tuple, set, frozenset)) and len(allowed) == 0:
        return True
    return False


# ---------------------------------------------------------------------------
# Heartbeat lifecycle
# ---------------------------------------------------------------------------

class _HeartbeatContext:
    """Bounded background heartbeat thread for a durable lease.

    Runs heartbeat updates at the configured interval while a role is
    executing. Stops automatically when the wrapped callable returns.
    Does NOT stop on _CrashSimulated (BaseException), modeling abrupt
    process death where the heartbeat disappears and the lease expires.
    """

    def __init__(
        self,
        *,
        store: TaskStore,
        run_id: str,
        owner: str,
        epoch: int,
        expiry_ms: int,
        heartbeat_window_ms: int,
    ) -> None:
        self.store = store
        self.run_id = run_id
        self.owner = owner
        self.epoch = epoch
        self.expiry_ms = expiry_ms
        self.heartbeat_window_ms = heartbeat_window_ms
        self._stop_event: Any = None
        self._thread: Any = None
        self._active = False

    def heartbeat_during(self, fn: Callable[[], Any]) -> Any:
        self._stop_event = threading.Event()
        self._active = True
        self._thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="durable-hb"
        )
        self._thread.start()
        try:
            return fn()
        finally:
            self._stop()

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.store._heartbeat_durable_lease(
                    self.run_id, self.owner, self.epoch, self.expiry_ms,
                )
            except TaskStoreError:
                break
            self._stop_event.wait(
                timeout=self.heartbeat_window_ms / 1000.0 * 0.6
            )
        self._active = False

    def _stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._active = False

    @property
    def active(self) -> bool:
        return self._active


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
        execution_authority_sha: str | None = None,
        planning_sha: str | None = None,
    ) -> None:
        self.store = store
        self.router = router
        self.binding_resolver = binding_resolver
        self.lease_provider = lease_provider
        self.expiry_ms = expiry_ms
        self.heartbeat_window_ms = heartbeat_window_ms
        self._execution_authority_sha = execution_authority_sha
        self._planning_sha = planning_sha
        self._validate_trusted_lease_config()
        self._execution_service = TaskExecutionService(
            store=store,
            router=router,
            binding_resolver=binding_resolver,
            lease_provider=lease_provider,
        )

    def _validate_trusted_lease_config(self) -> None:
        if self.expiry_ms <= 0:
            raise TaskExecutionError(
                f"durable_trusted_expiry_ms_non_positive:{self.expiry_ms}"
            )
        if self.heartbeat_window_ms <= 0:
            raise TaskExecutionError(
                f"durable_trusted_heartbeat_window_ms_non_positive:"
                f"{self.heartbeat_window_ms}"
            )
        if self.heartbeat_window_ms >= self.expiry_ms:
            raise TaskExecutionError(
                f"durable_trusted_heartbeat_cannot_renew_before_expiry:"
                f"heartbeat_window_ms={self.heartbeat_window_ms}:"
                f"expiry_ms={self.expiry_ms}"
            )

    @staticmethod
    def _normalize_identity(value: str | None) -> str:
        if value is None:
            return ""
        return value.strip()

    def _trusted_authority_sha(self) -> str:
        return self._normalize_identity(self._execution_authority_sha)

    def _trusted_planning_sha(self) -> str:
        return self._normalize_identity(self._planning_sha)

    def _assert_trusted_identity_for_execute(self) -> None:
        auth = self._trusted_authority_sha()
        plan = self._trusted_planning_sha()
        if not auth:
            raise TaskExecutionError(
                "durable_trusted_identity_missing:"
                "execution_authority_sha is empty/whitespace/None"
            )
        if not plan:
            raise TaskExecutionError(
                "durable_trusted_identity_missing:"
                "planning_sha is empty/whitespace/None"
            )

    def _assert_trusted_identity_for_resume(
        self,
        *,
        execution_authority_sha: str | None = None,
        planning_sha: str | None = None,
    ) -> tuple[str, str]:
        auth = execution_authority_sha
        if auth is None:
            auth = self._execution_authority_sha
        plan = planning_sha
        if plan is None:
            plan = self._planning_sha
        auth_norm = self._normalize_identity(auth)
        plan_norm = self._normalize_identity(plan)
        if not auth_norm:
            raise DurableResumeError(
                "trusted_authority_sha_missing:"
                "execution_authority_sha is empty/whitespace/None"
            )
        if not plan_norm:
            raise DurableResumeError(
                "trusted_planning_sha_missing:"
                "planning_sha is empty/whitespace/None"
            )
        return auth_norm, plan_norm

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
        """Execute a new durable sequential-team run with atomic lease acquisition.

        Trusted identity (execution_authority_sha, planning_sha) MUST be
        non-empty. None, empty, or whitespace-only values all fail closed
        BEFORE durable run creation.
        """
        self._assert_trusted_identity_for_execute()
        lease = self._acquire_or_find_lease(
            task_id, lease_owner, "", workspace_root
        )
        _hb = _HeartbeatContext(
            store=self.store,
            run_id=lease.run_id,
            owner=lease.owner,
            epoch=lease.epoch,
            expiry_ms=self.expiry_ms,
            heartbeat_window_ms=self.heartbeat_window_ms,
        )
        try:
            return _hb.heartbeat_during(
                lambda: self._execute_with_lease(
                    task_id,
                    workspace_root,
                    lease,
                    checkpointer=checkpointer,
                )
            )
        except _CrashSimulated:
            raise
        except Exception:
            self.store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
            raise

    # ---------------------------------------------------------------
    # Single-mode durable execution
    # ---------------------------------------------------------------

    def execute_durable_single(
        self,
        task_id: str,
        *,
        workspace_root: str,
        lease_owner: str = "task-api",
    ) -> Any:
        """Execute a new durable single-mode run with atomic lease acquisition.

        Mirrors the sequential-team durable path: one /execute yields
        exactly one durable run with owner+epoch fencing, heartbeat,
        worktree/authority identity persistence, checkpoint acceptance,
        external-operation journaling, and resume-capable terminal state.
        """
        from .task_execution import TaskExecutionOutcome
        self._assert_trusted_identity_for_execute()
        task = self.store.get_task(task_id)
        if task.orchestration_mode != "single":
            raise TaskExecutionError(
                f"durable_single_wrong_mode:{task_id}:actual={task.orchestration_mode}"
            )
        lease = self._acquire_or_find_lease(
            task_id, lease_owner, "", workspace_root
        )
        _hb = _HeartbeatContext(
            store=self.store,
            run_id=lease.run_id,
            owner=lease.owner,
            epoch=lease.epoch,
            expiry_ms=self.expiry_ms,
            heartbeat_window_ms=self.heartbeat_window_ms,
        )
        try:
            return _hb.heartbeat_during(
                lambda: self._execute_single_with_lease(
                    task_id, workspace_root, lease,
                )
            )
        except _CrashSimulated:
            raise
        except Exception:
            self.store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
            raise

    def _execute_single_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        lease: LeaseHandle,
    ) -> Any:
        """Execute a durable single-mode run: one executor dispatch,
        fenced checkpoints, validation, terminalization.

        Checkpoint sequence:
          PRE_PLANNER -> POST_PLANNER -> POST_CODER ->
          POST_REVIEWER -> POST_VALIDATION

        Semantics for single mode:
          PRE_PLANNER:  durable run established, before dispatch
          POST_PLANNER: executor dispatch completed, result accepted
          POST_CODER:   changed files durably persisted
          POST_REVIEWER: validation-ready state accepted
          POST_VALIDATION: validation completed
        """
        from .task_execution import TaskExecutionOutcome
        from .task_runtime import LocalValidationRunner
        from .opencode_executor import (
            _collect_product_diff,
            _collect_final_product_files,
        )

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        run = self.store._get_durable_run(lease.run_id)

        if run.accepted_checkpoint == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            review_status = (
                "READY_FOR_REVIEW_FIXTURE"
                if stored.executor_kind == "deterministic_fixture"
                else "READY_FOR_REVIEW"
            )
            if stored.status == review_status:
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=True,
                    validation_command_id=run.validation_command_id or "git_diff_check",
                    validation_exit_code=run.validation_exit_code or 0,
                )
            raise TaskExecutionError(
                f"durable_single_post_validation_without_ready:{task_id}"
            )

        task = self.store.get_task(task_id)
        executor_kind = task.executor_kind
        review_status = (
            "READY_FOR_REVIEW_FIXTURE"
            if executor_kind == "deterministic_fixture"
            else "READY_FOR_REVIEW"
        )
        executor_kwargs = self._build_executor_kwargs(task)

        # --- External dispatch via the same router path as TaskExecutionService ---
        # For deterministic_fixture, the executor creates its own worktree internally.
        # For opencode, prepare_worktree_once is used to establish identity first.
        use_prepare = executor_kind == "opencode"

        if use_prepare:
            try:
                executor = self.router.create_executor(
                    executor_kind=executor_kind, **executor_kwargs
                )
            except Exception as exc:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked", detail=str(exc),
                    owner=lease.owner, epoch=lease.epoch,
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

            try:
                prepared = executor.prepare_worktree_once(
                    task_id, Path(workspace_root),
                    self._execution_service._store_event_callback
                )
            except Exception as exc:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked",
                    detail=f"worktree_preparation_failed:{exc}",
                    owner=lease.owner, epoch=lease.epoch,
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

            wt_path = str(prepared.worktree)
            if not Path(wt_path).exists():
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked",
                    detail=f"prepared_worktree_missing:{wt_path}",
                    owner=lease.owner, epoch=lease.epoch,
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

            wt_head_sha = self._git_rev_parse_head(wt_path)
            if not wt_head_sha:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked",
                    detail=f"prepared_worktree_empty_HEAD:{wt_path}",
                    owner=lease.owner, epoch=lease.epoch,
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

            repo_base_sha = wt_head_sha

            self.store._set_worktree_identity(
                lease.run_id, wt_path, wt_head_sha,
                lease.owner, lease.epoch,
            )
            self.store._set_authority_identity(
                lease.run_id,
                self._trusted_authority_sha(),
                self._trusted_planning_sha(),
                lease.owner, lease.epoch,
            )
            self.store._set_repository_base_sha(
                lease.run_id, repo_base_sha,
                lease.owner, lease.epoch,
            )

            task_db_path = self.store.db_path
            task_db_dir = os.path.dirname(os.path.abspath(task_db_path)) or "."
            checkpoint_dir = os.path.join(task_db_dir, "durable_checkpoints")
            os.makedirs(checkpoint_dir, exist_ok=True)
            checkpoint_db_path = os.path.join(
                checkpoint_dir, f"{lease.run_id}.sqlite3"
            )
            self.store._set_checkpoint_db_path(
                lease.run_id, checkpoint_db_path,
                lease.owner, lease.epoch,
            )
        else:
            wt_path = ""
            repo_base_sha = ""

        # PRE_PLANNER: durable run established before any external dispatch.
        self.store._accept_checkpoint(
            lease.run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch
        )
        _check_crash_seam("PRE_PLANNER")

        baseline_product = (
            _collect_product_diff(Path(wt_path))
            if wt_path and Path(wt_path).exists() else ()
        )
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, baseline_product,
            lease.owner, lease.epoch,
        )

        self.store._fenced_transition_to(
            lease.run_id, task_id, "RUNNING",
            lease.owner, lease.epoch,
        )

        # --- Record external operation BEFORE dispatch ---
        idempotency_key = f"single-exec-{task_id}-{run.execution_id}"
        request_digest = _digest(_json_payload({
            "task_id": task_id,
            "execution_id": run.execution_id,
            "workspace_root": workspace_root,
            "repo_base": repo_base_sha,
        }))
        ext_op = self.store._record_external_operation(
            operation_key=f"single-exec-{task_id}",
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )

        val_command_id = "git_diff_check"
        try:
            exec_result = self._execution_service._dispatch_executor(
                task=task,
                workspace_root=workspace_root,
                validation_command_id=val_command_id,
                executor_kwargs=executor_kwargs,
            )
        except Exception as exc:
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification="executor_dispatch_failed",
                detail=f"executor_dispatch_exception:{exc}",
                owner=lease.owner, epoch=lease.epoch,
            )
            self.store._fenced_terminalize(
                lease.run_id, task_id,
                terminal_status="FAILED",
                validation_command_id="",
                validation_exit_code=-1,
                validation_output_digest="",
                failure_classification="executor_dispatch_failed",
                failure_detail=f"executor_dispatch_exception:{exc}",
                owner=lease.owner, epoch=lease.epoch,
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

        # --- Reconcile external operation ---
        self.store._reconcile_external_operation(
            operation_id=ext_op.operation_id,
            external_operation_id=ext_op.operation_id,
            result_state="success" if exec_result["success"] else "failure",
        )

        if not exec_result["success"]:
            classification = (
                "blocked"
                if "unapproved" in exec_result.get("error", "")
                else exec_result.get("failure_classification", "failed")
            ) or "failed"
            self.store._accept_checkpoint(
                lease.run_id, "POST_PLANNER",
                _digest(str(exec_result.get("error", ""))),
                1, lease.owner, lease.epoch,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_CODER", "",
                1, lease.owner, lease.epoch,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_REVIEWER", "",
                1, lease.owner, lease.epoch,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_VALIDATION", "",
                1, lease.owner, lease.epoch,
            )
            self.store._fenced_terminalize(
                lease.run_id, task_id,
                terminal_status="FAILED",
                validation_command_id=exec_result.get("validation_command_id", ""),
                validation_exit_code=exec_result.get("validation_exit_code", -1),
                validation_output_digest=exec_result.get("validation_output_digest", ""),
                failure_classification=classification,
                failure_detail=exec_result.get("error", "executor failed"),
                owner=lease.owner, epoch=lease.epoch,
            )
            final = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=final.execution_id,
                success=False,
                validation_command_id=exec_result.get("validation_command_id", ""),
                validation_exit_code=exec_result.get("validation_exit_code", -1),
                failure_classification=final.failure_classification,
                failure_detail=final.failure_detail,
            )

        self.store._accept_checkpoint(
            lease.run_id, "POST_PLANNER",
            _digest(_json_payload(exec_result)),
            1, lease.owner, lease.epoch,
        )
        _check_crash_seam("POST_PLANNER")

        self.store._fenced_set_changed_files(
            lease.run_id, task_id, tuple(exec_result.get("changed_files", [])),
            lease.owner, lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_CODER", "",
            1, lease.owner, lease.epoch,
        )
        _check_crash_seam("POST_CODER")

        self.store._set_validation_result(
            lease.run_id,
            command_id=exec_result.get("validation_command_id", val_command_id),
            exit_code=exec_result.get("validation_exit_code", 0),
            output_digest=exec_result.get("validation_output_digest", ""),
            owner=lease.owner, epoch=lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_REVIEWER", "",
            1, lease.owner, lease.epoch,
        )
        _check_crash_seam("POST_REVIEWER")

        # For opencode, run final git_diff_check in the prepared worktree.
        # For deterministic_fixture, the executor already ran validation internally.
        if use_prepare and wt_path:
            val_runner = LocalValidationRunner()
            try:
                val_exit, val_output, val_digest = val_runner.run(
                    task_id=task_id,
                    command_id=val_command_id,
                    cwd=wt_path,
                )
            except Exception:
                val_exit, val_output, val_digest = -1, "", ""
        else:
            val_exit = exec_result.get("validation_exit_code", 0)
            val_output = ""
            val_digest = exec_result.get("validation_output_digest", "")

        self.store._set_validation_result(
            lease.run_id,
            command_id=val_command_id,
            exit_code=val_exit,
            output_digest=val_digest,
            owner=lease.owner, epoch=lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_VALIDATION", "",
            1, lease.owner, lease.epoch,
        )
        _check_crash_seam("POST_VALIDATION")

        final_changed = exec_result.get("changed_files", [])
        if use_prepare and wt_path:
            final_changed = _collect_final_product_files(Path(wt_path))
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, tuple(final_changed),
            lease.owner, lease.epoch,
        )

        self.store._fenced_transition_to(
            lease.run_id, task_id, "VALIDATING",
            lease.owner, lease.epoch,
        )
        if val_exit == 0:
            self.store._fenced_transition_to(
                lease.run_id, task_id, review_status,
                lease.owner, lease.epoch,
            )
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="VALIDATED",
                title="Durable single execution validated",
                description="single-mode executor dispatch + validation completed",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": val_command_id,
                    "run_id": lease.run_id,
                    "executor_kind": executor_kind,
                },
                owner=lease.owner, epoch=lease.epoch,
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=val_command_id,
                validation_exit_code=val_exit,
            )

        self.store._fenced_terminalize(
            lease.run_id, task_id,
            terminal_status="FAILED",
            validation_command_id=val_command_id,
            validation_exit_code=val_exit,
            validation_output_digest=val_digest,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
            owner=lease.owner, epoch=lease.epoch,
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id=val_command_id,
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
        )

    def _acquire_or_find_lease(
        self,
        task_id: str,
        lease_owner: str,
        repository_base_sha: str,
        workspace_root: str,
    ) -> LeaseHandle:
        task = self.store.get_task(task_id)
        task_status = None
        if task.status == "QUEUED":
            task_status = "QUEUED"
        return self.store._acquire_durable_lease(
            task_id=task_id,
            execution_id=task.execution_id,
            lease_owner=lease_owner,
            expiry_ms=self.expiry_ms,
            execution_authority_sha=self._trusted_authority_sha(),
            planning_sha=self._trusted_planning_sha(),
            task_status=task_status,
        )

    def _execute_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        lease: LeaseHandle,
        *,
        checkpointer: Any | None = None,
    ) -> Any:
        """Execute durable sequential team with per-role immediate checkpoint acceptance.

        The durable first-run path owns the role loop directly. After each
        successful role:
        1. existing role-specific invariants are validated;
        2. artifact/diff digest is persisted;
        3. the POST_<ROLE> checkpoint is accepted IMMEDIATELY in TaskStore;
        4. only then may the next role start.

        This ensures that a crash after any role's acceptance leaves the
        durable state consistent and resumable from the next role.
        """
        from .task_execution import TaskExecutionOutcome
        from .task_runtime import LocalValidationRunner
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
        from reverse_agent.workflows.team_graph import TeamGraphError

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
        run = self.store._get_durable_run(lease.run_id)

        if run.accepted_checkpoint == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            if stored.status == "READY_FOR_REVIEW":
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

        task = self.store.get_task(task_id)

        executor_kwargs = self._build_executor_kwargs(task)
        try:
            executor = self.router.create_executor(
                executor_kind="opencode", **executor_kwargs
            )
        except Exception as exc:
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification="blocked", detail=str(exc),
                owner=lease.owner, epoch=lease.epoch,
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

        try:
            prepared = executor.prepare_worktree_once(
                task_id, Path(workspace_root),
                self._execution_service._store_event_callback
            )
        except Exception as exc:
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification="blocked",
                detail=f"worktree_preparation_failed:{exc}",
                owner=lease.owner, epoch=lease.epoch,
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

        wt_path = str(prepared.worktree)

        # Require prepared path to exist and git rev-parse HEAD to be non-empty.
        if not Path(wt_path).exists():
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification="blocked",
                detail=f"prepared_worktree_missing:{wt_path}",
                owner=lease.owner, epoch=lease.epoch,
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

        wt_head_sha = self._git_rev_parse_head(wt_path)
        if not wt_head_sha:
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification="blocked",
                detail=f"prepared_worktree_empty_HEAD:{wt_path}",
                owner=lease.owner, epoch=lease.epoch,
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

        repo_base_sha = wt_head_sha

        self.store._set_worktree_identity(
            lease.run_id, wt_path, wt_head_sha,
            lease.owner, lease.epoch,
        )
        self.store._set_authority_identity(
            lease.run_id,
            self._trusted_authority_sha(),
            self._trusted_planning_sha(),
            lease.owner, lease.epoch,
        )

        self.store._set_repository_base_sha(
            lease.run_id, repo_base_sha,
            lease.owner, lease.epoch,
        )

        # Compute deterministic checkpoint DB path from task DB directory.
        task_db_path = self.store.db_path
        task_db_dir = os.path.dirname(os.path.abspath(task_db_path)) or "."
        checkpoint_dir = os.path.join(task_db_dir, "durable_checkpoints")
        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_db_path = os.path.join(
            checkpoint_dir, f"{lease.run_id}.sqlite3"
        )
        self.store._set_checkpoint_db_path(
            lease.run_id, checkpoint_db_path,
            lease.owner, lease.epoch,
        )

        # Production filesystem SQLite checkpointer with strict serde.
        import sqlite3 as _sqlite3
        _cp_conn = _sqlite3.connect(
            checkpoint_db_path,
            isolation_level=None,
            check_same_thread=False,
        )
        _cp_conn.execute("PRAGMA journal_mode=WAL")
        _production_saver = _make_strict_saver(_cp_conn)
        _production_saver.setup()

        # PRE_PLANNER is accepted ONLY after worktree identity + authority
        # identity + repository base + checkpoint DB are durably persisted.
        self.store._accept_checkpoint(
            lease.run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch
        )
        _check_crash_seam("PRE_PLANNER")

        handoff = handoff_dir(prepared.worktree)
        self.store._fenced_add_event(
            lease.run_id, task_id,
            event_type="EXECUTOR_RUNNING",
            title="Durable sequential team execution",
            description="planner->coder->reviewer with per-role checkpoint acceptance",
            metadata={
                "execution_id": run.execution_id,
                "run_id": lease.run_id,
                "worktree_path": wt_path,
                "worktree_head_sha": wt_head_sha,
                "repository_base_sha": repo_base_sha,
                "checkpoint_db_path": checkpoint_db_path,
            },
            owner=lease.owner, epoch=lease.epoch,
        )
        baseline_product = _collect_product_diff(prepared.worktree)
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, baseline_product,
            lease.owner, lease.epoch,
        )

        # Task remains PREPARING_WORKSPACE through executor creation,
        # worktree preparation, and identity persistence. Only after
        # PRE_PLANNER is accepted does the task become RUNNING.
        self.store._fenced_transition_to(
            lease.run_id, task_id, "RUNNING",
            lease.owner, lease.epoch,
        )

        plan_digest = ""
        review_digest = ""
        coder_product_snapshot: tuple[dict[str, Any], ...] = ()
        run_role_attempt = run.role_attempt
        _graph_config = {
            "configurable": {"thread_id": lease.run_id}
        }

        for role in ("planner", "coder", "reviewer"):
            checkpoint_name = _checkpoint_name_for_role(role)
            if not checkpoint_name:
                continue

            result = self._execute_single_role(
                role=role,
                task_id=task_id,
                prepared=prepared,
                handoff=handoff,
                executor=executor,
                baseline=baseline_product,
                plan_digest=plan_digest,
                role_attempt=run_role_attempt,
                coder_product_snapshot=coder_product_snapshot,
                checkpointer=_production_saver,
                graph_config=_graph_config,
            )

            if not result["success"]:
                self._complete_durable_failure(
                    task_id, run, lease,
                    baseline_product, plan_digest,
                    roles_executed=result.get("roles_executed", []),
                    role_results=result.get("role_results", []),
                    classification=result.get("classification", "failed"),
                    failure_detail=result.get("detail", "role failed"),
                )
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=False,
                    validation_command_id="",
                    validation_exit_code=result.get("val_exit", -1),
                    failure_classification=result.get("classification", "failed"),
                    failure_detail=result.get("detail", "role failed"),
                )

            # --- Persist digest and accept checkpoint IMMEDIATELY ---
            if role == "planner":
                plan_digest = result["digest"]
                self.store._set_planner_handoff_digest(
                    lease.run_id, plan_digest, lease.owner, lease.epoch
                )
            elif role == "coder":
                coder_product_snapshot = result["snapshot"]
                coder_digest = _digest(_json_payload(list(coder_product_snapshot)))
                self.store._set_coder_product_diff_digest(
                    lease.run_id, coder_digest, lease.owner, lease.epoch
                )
                plan_digest = result.get("plan_digest", plan_digest)

            elif role == "reviewer":
                review_digest = result["digest"]
                self.store._set_reviewer_handoff_digest(
                    lease.run_id, review_digest, lease.owner, lease.epoch
                )

            head_sha = self._git_rev_parse_head(wt_path)
            repo_base = self.store._get_durable_run(lease.run_id).repository_base_sha
            if repo_base and head_sha != repo_base:
                self._complete_durable_failure(
                    task_id, run, lease, baseline_product, plan_digest,
                    roles_executed=result.get("roles_executed", []),
                    role_results=result.get("role_results", []),
                    classification="head_moved",
                    failure_detail=(
                        f"HEAD moved during {role}: "
                        f"expected={repo_base} actual={head_sha}"
                    ),
                )
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=False,
                    validation_command_id="",
                    validation_exit_code=-1,
                    failure_classification="head_moved",
                    failure_detail=(
                        f"HEAD moved during {role}: "
                        f"expected={repo_base} actual={head_sha}"
                    ),
                )

            self.store._accept_checkpoint(
                lease.run_id, checkpoint_name,
                result.get("digest", ""),
                run_role_attempt, lease.owner, lease.epoch,
            )

            # --- Crash injection seam AFTER checkpoint acceptance ---
            _check_crash_seam(checkpoint_name)

        # --- Validation ---
        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=wt_path,
            )
        except Exception:
            val_exit, val_output, val_digest = -1, "", ""

        self.store._set_validation_result(
            lease.run_id,
            command_id="git_diff_check",
            exit_code=val_exit,
            output_digest=val_digest,
            owner=lease.owner, epoch=lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_VALIDATION", "",
            run_role_attempt, lease.owner, lease.epoch,
        )

        _remove_handoff(handoff)
        final_changed = _collect_final_product_files(prepared.worktree)
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, final_changed,
            lease.owner, lease.epoch,
        )

        self.store._fenced_transition_to(
            lease.run_id, task_id, "VALIDATING",
            lease.owner, lease.epoch,
        )
        if val_exit == 0:
            self.store._fenced_transition_to(
                lease.run_id, task_id, "READY_FOR_REVIEW",
                lease.owner, lease.epoch,
            )
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="VALIDATED",
                title="Durable sequential team validated",
                description="per-role checkpoint acceptance completed",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": "git_diff_check",
                    "plan_digest": plan_digest,
                    "review_digest": review_digest,
                    "run_id": lease.run_id,
                },
                owner=lease.owner, epoch=lease.epoch,
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id="git_diff_check",
                validation_exit_code=val_exit,
            )

        self.store._fenced_terminalize(
            lease.run_id, task_id,
            terminal_status="FAILED",
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            validation_output_digest=val_digest,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
            owner=lease.owner, epoch=lease.epoch,
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
        )

    def _build_executor_kwargs(self, task: Any) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if getattr(task, "executor_kind", "") == "opencode":
            binding_ref = getattr(task, "binding_ref", "") or ""
            if binding_ref and self.binding_resolver is not None:
                kwargs["binding_resolution"] = self.binding_resolver.resolve(
                    binding_ref, task_executor="opencode"
                )
            else:
                model_id = (
                    getattr(task, "model_profile_ref", "") or ""
                ) or os.environ.get("REVERSE_AGENT_OPENCODE_MODEL", "")
                kwargs["model_id"] = model_id
            kwargs["repo_dir"] = os.environ.get("REVERSE_AGENT_REPO_DIR", "")
            kwargs["base_ref"] = getattr(task, "branch", "") or ""
            if self.lease_provider is not None:
                kwargs["lease_provider"] = self.lease_provider
        return kwargs

    @staticmethod
    def _git_rev_parse_head(wt_path: str) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=wt_path, capture_output=True, text=True, check=True,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _execute_single_role(
        self,
        *,
        role: str,
        task_id: str,
        prepared: Any,
        handoff: Path,
        executor: Any,
        baseline: tuple[dict[str, Any], ...],
        plan_digest: str,
        role_attempt: int,
        coder_product_snapshot: tuple[dict[str, Any], ...] | None = None,
        checkpointer: Any | None = None,
        graph_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from .opencode_executor import (
            RoleContext,
            _collect_product_diff,
            _handoff_digest,
            _validate_plan_handoff,
            _validate_review_handoff,
        )
        from reverse_agent.workflows.team_graph import (
            TeamGraphError,
            WorkerAssignment,
            WorkerExecutionResult,
            build_sequential_team_graph,
        )

        handoff_path = handoff
        if hasattr(prepared, "worktree"):
            wt = prepared.worktree
            prep_for_executor = prepared
        else:
            wt = prepared
            prep_for_executor = _FakePreparedCtx(worktree=prepared)
        if isinstance(wt, Path):
            wt_str = str(wt)
        else:
            wt_str = str(wt)
        _coder_snap: tuple[dict[str, Any], ...] = coder_product_snapshot or ()
        result_digest = ""
        roles_executed: list[str] = []
        role_results: list[dict[str, Any]] = []

        def _role_worker(wa: "WorkerAssignment") -> "WorkerExecutionResult":
            nonlocal plan_digest, result_digest, _coder_snap
            r = wa.role
            roles_executed.append(r)
            role_context = RoleContext(
                role=r, task_id=wa.task_id,
                workspace=Path(wt_str),
                plan_path=handoff_path / "plan.md",
                plan_digest=plan_digest,
            )
            if r == "planner":
                handoff_path.mkdir(parents=True, exist_ok=True)
            try:
                result = executor.execute_role_prepared(
                    prep_for_executor, self.store,
                    role_context=role_context,
                    event_callback=self._execution_service._store_event_callback,
                )
            except Exception as exc:
                role_results.append({
                    "role": r, "success": False, "validation_exit_code": -1,
                    "classification": "executor_error",
                    "detail": f"{exc.__class__.__name__}:{exc}",
                })
                return WorkerExecutionResult(
                    worker_id=wa.worker_id, task_id=wa.task_id,
                    execution_id="", success=False, validation_exit_code=-1,
                    failure_classification="executor_error",
                    failure_detail=f"{exc.__class__.__name__}:{exc}",
                    reasons=(f"executor_exception:{exc.__class__.__name__}",),
                )

            if not result.success:
                role_results.append({
                    "role": r, "success": False,
                    "validation_exit_code": result.validation_exit_code,
                    "classification": result.failure_classification or "role_failed",
                    "detail": result.error,
                })
                return WorkerExecutionResult(
                    worker_id=wa.worker_id, task_id=wa.task_id,
                    execution_id=getattr(result, "execution_id", ""),
                    success=False, validation_exit_code=result.validation_exit_code,
                    failure_classification=result.failure_classification,
                    failure_detail=result.error,
                    reasons=(result.failure_classification or "role_failed",),
                )

            if r == "planner":
                invalid = _validate_plan_handoff(handoff_path / "plan.md")
                if invalid:
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "invalid_plan_handoff", "detail": invalid,
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="invalid_plan_handoff",
                        failure_detail=invalid, reasons=("invalid_plan_handoff",),
                    )
                result_digest = _handoff_digest(handoff_path / "plan.md")
                planner_post = _collect_product_diff(Path(wt_str))
                if planner_post != baseline:
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "planner_product_mutation",
                        "detail": "planner mutated product files",
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="planner_product_mutation",
                        failure_detail="planner mutated product files",
                        reasons=("planner_product_mutation",),
                    )
            elif r == "coder":
                if not (handoff_path / "plan.md").is_file():
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "missing_plan_handoff",
                        "detail": "plan handoff missing",
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="missing_plan_handoff",
                        failure_detail="plan handoff missing",
                        reasons=("missing_plan_handoff",),
                    )
                _coder_snap = _collect_product_diff(Path(wt_str))
                if not _coder_snap:
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "no_coder_product_diff",
                        "detail": "coder produced no product diff",
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="no_coder_product_diff",
                        failure_detail="coder produced no product diff",
                        reasons=("no_coder_product_diff",),
                    )
            elif r == "reviewer":
                invalid_rev = _validate_review_handoff(handoff_path / "review.md")
                if invalid_rev:
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "invalid_review_handoff", "detail": invalid_rev,
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="invalid_review_handoff",
                        failure_detail=invalid_rev, reasons=("invalid_review_handoff",),
                    )
                result_digest = _handoff_digest(handoff_path / "review.md")
                reviewer_post = _collect_product_diff(Path(wt_str))
                if reviewer_post != _coder_snap:
                    role_results.append({
                        "role": r, "success": False, "validation_exit_code": -1,
                        "classification": "reviewer_product_mutation",
                        "detail": "reviewer mutated product",
                    })
                    return WorkerExecutionResult(
                        worker_id=wa.worker_id, task_id=wa.task_id,
                        execution_id=result.execution_id,
                        success=False, validation_exit_code=-1,
                        failure_classification="reviewer_product_mutation",
                        failure_detail="reviewer mutated product",
                        reasons=("reviewer_product_mutation",),
                    )

            role_results.append({
                "role": r, "success": True,
                "validation_exit_code": result.validation_exit_code,
            })
            return WorkerExecutionResult(
                worker_id=wa.worker_id, task_id=wa.task_id,
                execution_id=result.execution_id,
                success=True, validation_exit_code=result.validation_exit_code,
                failure_classification="", failure_detail="",
            )

        base_assignment = WorkerAssignment(
            worker_id="durable_sequential",
            role=role,
            task_id=task_id,
            workspace_root=str(wt_str),
        )

        graph = build_sequential_team_graph(
            worker=_role_worker,
            skip_roles=set(("planner", "coder", "reviewer")) - {role},
            checkpointer=checkpointer,
        )
        try:
            graph.invoke(
                {"assignments": [base_assignment.to_dict()]},
                config=graph_config or {},
            )
        except TeamGraphError as exc:
            last = role_results[-1] if role_results else {}
            return {
                "success": False,
                "val_exit": -1,
                "classification": last.get("classification", "failed"),
                "detail": str(exc),
                "roles_executed": roles_executed,
                "role_results": role_results,
                "digest": "",
                "snapshot": (),
                "plan_digest": plan_digest,
            }

        last = role_results[-1] if role_results else {}
        snapshot_val = _coder_snap if role == "coder" else ()
        return {
            "success": True,
            "val_exit": 0,
            "classification": "",
            "detail": "",
            "roles_executed": roles_executed,
            "role_results": role_results,
            "digest": result_digest,
            "snapshot": snapshot_val,
            "plan_digest": plan_digest,
        }

    def _complete_durable_failure(
        self, task_id: str, run: Any, lease: Any,
        baseline: tuple[dict[str, Any], ...], plan_digest: str,
        roles_executed: list[str], role_results: list[dict[str, Any]],
        classification: str, failure_detail: str,
    ) -> None:
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, baseline,
            lease.owner, lease.epoch,
        )
        try:
            self.store._fenced_classify_failure(
                lease.run_id, task_id,
                classification=classification,
                detail=f"durable sequential team failed:{failure_detail}",
                owner=lease.owner, epoch=lease.epoch,
            )
        except TaskStoreError:
            pass
        try:
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="EXECUTOR_FINISHED",
                title="Durable sequential team failed",
                description=failure_detail,
                metadata={
                    "classification": classification,
                    "roles": roles_executed,
                    "run_id": lease.run_id,
                    "plan_digest": plan_digest,
                },
                owner=lease.owner, epoch=lease.epoch,
            )
        except TaskStoreError:
            pass

    # ---------------------------------------------------------------
    # Resume
    # ---------------------------------------------------------------

    def resume_sequential_team(
        self,
        task_id: str,
        *,
        workspace_root: str = "",
        lease_owner: str = "local",
        repository_base_sha: str = "",
        execution_authority_sha: str | None = None,
        planning_sha: str | None = None,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        """Resume a durable sequential-team run from the last accepted checkpoint.

        Validates ALL identity invariants fail-closed. None/empty/whitespace
        authority or planning SHA fail before any recovery claim or epoch
        increment.
        """
        from .task_execution import TaskExecutionOutcome

        auth_sha, plan_sha = self._assert_trusted_identity_for_resume(
            execution_authority_sha=execution_authority_sha,
            planning_sha=planning_sha,
        )
        if repository_base_sha:
            repo_sha = repository_base_sha
        else:
            repo_sha = ""

        run = self.store._find_active_durable_run(task_id)
        if run is None:
            raise DurableResumeError(f"no_active_durable_run:{task_id}")

        run_obj = self.store._get_durable_run(run["run_id"])

        stored_task = self.store.get_task(task_id)

        now_ms = _utc_now_ms()
        lease_expiry_ms = int(getattr(run_obj, "lease_expiry_ms", 0) or 0)
        existing_owner = getattr(run_obj, "lease_owner", "") or ""
        existing_epoch = int(getattr(run_obj, "lease_epoch", 0) or 0)

        if stored_task.status in ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"):
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run_obj.execution_id,
                success=True,
                validation_command_id=run_obj.validation_command_id or "git_diff_check",
                validation_exit_code=run_obj.validation_exit_code or 0,
            )

        if stored_task.orchestration_mode != "sequential_team":
            raise DurableResumeError(
                f"invalid_orchestration_mode:{stored_task.orchestration_mode}"
            )
        if stored_task.executor_kind != "opencode":
            raise DurableResumeError(
                f"invalid_executor_kind:{stored_task.executor_kind}"
            )

        if auth_sha and run_obj.execution_authority_sha != auth_sha:
            raise DurableResumeError(
                f"authority_sha_mismatch:{run_obj.execution_authority_sha}!={auth_sha}"
            )
        if plan_sha and run_obj.planning_sha != plan_sha:
            raise DurableResumeError(
                f"planning_sha_mismatch:{run_obj.planning_sha}!={plan_sha}"
            )
        if repo_sha and run_obj.repository_base_sha != repo_sha:
            raise DurableResumeError(
                f"base_sha_mismatch:{run_obj.repository_base_sha}!={repo_sha}"
            )

        live_statuses = frozenset({
            "PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING",
        })
        if (
            stored_task.status in live_statuses
            and lease_expiry_ms > now_ms
            and existing_owner
            and existing_epoch > 0
        ):
            raise DurableResumeError(
                f"durable_run_lease_live:{task_id}:"
                f"status={stored_task.status}:epoch={existing_epoch}:"
                f"owner={existing_owner}"
            )

        recovery_class = getattr(run_obj, "recovery_classification", "") or ""
        if stored_task.status != "INTERRUPTED":
            if stored_task.status not in ("BLOCKED", "FAILED", "CANCELLED"):
                raise DurableResumeError(
                    f"invalid_resume_status:{stored_task.status}"
                )

        if stored_task.status == "INTERRUPTED":
            if recovery_class not in ("orphan_stale_lease", "interrupted", "recovering"):
                raise DurableResumeError(
                    f"invalid_recovery_classification:{recovery_class}"
                )

        wt_path = run_obj.worktree_path
        if not wt_path:
            wt_path = workspace_root
        if workspace_root and run_obj.worktree_path != workspace_root:
            raise DurableResumeError(
                f"workspace_mismatch:{run_obj.worktree_path}!={workspace_root}"
            )

        if not Path(wt_path).exists():
            raise DurableResumeError(f"worktree_not_found:{wt_path}")

        actual_head = self._git_rev_parse_head(wt_path)
        stored_base = getattr(run_obj, "repository_base_sha", "") or ""
        if stored_base and actual_head != stored_base:
            raise DurableResumeError(
                f"repository_base_head_mismatch:{stored_base}!={actual_head}"
            )
        stored_wt_head = getattr(run_obj, "worktree_head_sha", "") or ""
        if stored_wt_head and actual_head != stored_wt_head:
            raise DurableResumeError(
                f"worktree_head_mismatch:{stored_wt_head}!={actual_head}"
            )

        accepted_cp = getattr(run_obj, "accepted_checkpoint", "") or ""
        if accepted_cp == "":
            raise DurableResumeError(
                f"pre_pre_planner_no_reconstruction_path:{task_id}:"
                f"accepted_checkpoint_empty_fail_closed"
            )

        resume_owner = lease_owner or existing_owner or "task-api-resume"
        require_interrupted = stored_task.status == "INTERRUPTED"
        lease = self.store._recover_durable_lease(
            run_obj.run_id, resume_owner,
            expiry_ms=self.expiry_ms,
            require_interrupted=require_interrupted,
        )
        _hb = _HeartbeatContext(
            store=self.store,
            run_id=lease.run_id,
            owner=lease.owner,
            epoch=lease.epoch,
            expiry_ms=self.expiry_ms,
            heartbeat_window_ms=self.heartbeat_window_ms,
        )
        try:
            return _hb.heartbeat_during(
                lambda: self._resume_with_lease(
                    task_id, wt_path, run_obj, lease,
                    checkpointer=checkpointer,
                )
            )
        except _CrashSimulated:
            raise
        except Exception:
            self.store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
            raise

    # ---------------------------------------------------------------
    # Single-mode durable resume / recovery
    # ---------------------------------------------------------------

    def resume_single(
        self,
        task_id: str,
        *,
        workspace_root: str = "",
        lease_owner: str = "task-api-resume",
        repository_base_sha: str = "",
        execution_authority_sha: str | None = None,
        planning_sha: str | None = None,
    ) -> Any:
        """Resume/recover a durable single-mode run from the last accepted
        checkpoint. Uses same fencing, identity, and recovery semantics as
        sequential-team resume; executor dispatch is skipped when its result
        has already been durably accepted.
        """
        from .task_execution import TaskExecutionOutcome

        auth_sha, plan_sha = self._assert_trusted_identity_for_resume(
            execution_authority_sha=execution_authority_sha,
            planning_sha=planning_sha,
        )

        run_raw = self.store._find_active_durable_run(task_id)
        if run_raw is None:
            raise DurableResumeError(f"no_active_durable_run:{task_id}")

        if isinstance(run_raw, dict):
            run_id = run_raw["run_id"]
        else:
            run_id = run_raw.run_id
        run_obj = self.store._get_durable_run(run_id)
        stored_task = self.store.get_task(task_id)

        if stored_task.status in ("READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"):
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run_obj.execution_id,
                success=True,
                validation_command_id=run_obj.validation_command_id or "git_diff_check",
                validation_exit_code=run_obj.validation_exit_code or 0,
            )

        if stored_task.orchestration_mode != "single":
            raise DurableResumeError(
                f"invalid_orchestration_mode:{stored_task.orchestration_mode}"
            )

        if auth_sha and run_obj.execution_authority_sha != auth_sha:
            raise DurableResumeError(
                f"authority_sha_mismatch:{run_obj.execution_authority_sha}!={auth_sha}"
            )
        if plan_sha and run_obj.planning_sha != plan_sha:
            raise DurableResumeError(
                f"planning_sha_mismatch:{run_obj.planning_sha}!={plan_sha}"
            )

        now_ms = _utc_now_ms()
        lease_expiry_ms = int(getattr(run_obj, "lease_expiry_ms", 0) or 0)
        existing_owner = getattr(run_obj, "lease_owner", "") or ""
        existing_epoch = int(getattr(run_obj, "lease_epoch", 0) or 0)

        live_statuses = frozenset({
            "PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE", "VALIDATING",
        })
        if (
            stored_task.status in live_statuses
            and lease_expiry_ms > now_ms
            and existing_owner
            and existing_epoch > 0
        ):
            raise DurableResumeError(
                f"durable_run_lease_live:{task_id}:"
                f"status={stored_task.status}:epoch={existing_epoch}:"
                f"owner={existing_owner}"
            )

        recovery_class = getattr(run_obj, "recovery_classification", "") or ""
        if stored_task.status == "INTERRUPTED":
            if recovery_class not in ("orphan_stale_lease", "interrupted", "recovering"):
                raise DurableResumeError(
                    f"invalid_recovery_classification:{recovery_class}"
                )
        elif stored_task.status not in ("BLOCKED", "FAILED", "CANCELLED", "INTERRUPTED"):
            raise DurableResumeError(
                f"invalid_resume_status:{stored_task.status}"
            )

        wt_path = run_obj.worktree_path
        if not wt_path:
            wt_path = workspace_root
        if workspace_root and run_obj.worktree_path and run_obj.worktree_path != workspace_root:
            raise DurableResumeError(
                f"workspace_mismatch:{run_obj.worktree_path}!={workspace_root}"
            )

        accepted_cp_pre = getattr(run_obj, "accepted_checkpoint", "") or ""
        if not Path(wt_path).exists() and accepted_cp_pre != "PRE_PLANNER":
            raise DurableResumeError(f"worktree_not_found:{wt_path}")

        if Path(wt_path).exists():
            actual_head = self._git_rev_parse_head(wt_path)
            stored_base = getattr(run_obj, "repository_base_sha", "") or ""
            if stored_base and actual_head != stored_base:
                raise DurableResumeError(
                    f"repository_base_head_mismatch:{stored_base}!={actual_head}"
                )

        accepted_cp = getattr(run_obj, "accepted_checkpoint", "") or ""
        if accepted_cp == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run_obj.execution_id,
                success=True,
                validation_command_id=run_obj.validation_command_id or "git_diff_check",
                validation_exit_code=run_obj.validation_exit_code or 0,
            )

        if accepted_cp == "":
            raise DurableResumeError(
                f"pre_pre_planner_no_reconstruction_path:{task_id}:"
                f"accepted_checkpoint_empty_fail_closed"
            )

        resume_owner = lease_owner or existing_owner or "task-api-resume"
        require_interrupted = stored_task.status == "INTERRUPTED"
        lease = self.store._recover_durable_lease(
            run_id, resume_owner,
            expiry_ms=self.expiry_ms,
            require_interrupted=require_interrupted,
        )
        assert lease.epoch > existing_epoch, "recovery epoch must be strictly newer"

        _hb = _HeartbeatContext(
            store=self.store,
            run_id=lease.run_id,
            owner=lease.owner,
            epoch=lease.epoch,
            expiry_ms=self.expiry_ms,
            heartbeat_window_ms=self.heartbeat_window_ms,
        )
        try:
            return _hb.heartbeat_during(
                lambda: self._resume_single_with_lease(
                    task_id, wt_path, run_obj, lease,
                )
            )
        except _CrashSimulated:
            raise
        except Exception:
            self.store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
            raise

    def _resume_single_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        run: Any,
        lease: LeaseHandle,
    ) -> Any:
        """Resume a single-mode durable run.

        Based on last accepted checkpoint:
        - PRE_PLANNER: identity persisted but executor not yet dispatched;
          re-dispatch allowed (crash occurred before external call).
        - POST_PLANNER / POST_CODER / POST_REVIEWER: executor result already
          durably accepted; continue to validation WITHOUT re-dispatch.
        - POST_VALIDATION: already complete; return success.
        """
        from .task_execution import TaskExecutionOutcome
        from .task_runtime import LocalValidationRunner
        from .opencode_executor import (
            _collect_product_diff,
            _collect_final_product_files,
        )

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)

        stored = self.store.get_task(task_id)
        if stored.status == "INTERRUPTED":
            self.store._fenced_transition_to(
                lease.run_id, task_id, "RUNNING",
                lease.owner, lease.epoch,
            )

        accepted = run.accepted_checkpoint
        if accepted == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=run.validation_command_id or "git_diff_check",
                validation_exit_code=run.validation_exit_code or 0,
            )

        wt_path = str(run.worktree_path or workspace_root)
        prepared_path = Path(wt_path)
        baseline_product = _collect_product_diff(prepared_path) if prepared_path.exists() else ()
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, baseline_product,
            lease.owner, lease.epoch,
        )

        role_attempt = run.role_attempt

        if accepted in ("POST_PLANNER", "POST_CODER", "POST_REVIEWER"):
            # Executor result already durably accepted; skip dispatch.
            pass
        elif accepted == "PRE_PLANNER":
            # Identity persisted but executor not yet dispatched;
            # re-dispatch is safe (crash occurred before external call).
            task = self.store.get_task(task_id)
            executor_kind = task.executor_kind
            executor_kwargs = self._build_executor_kwargs(task)
            try:
                executor = self.router.create_executor(
                    executor_kind=executor_kind, **executor_kwargs
                )
            except Exception as exc:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked", detail=str(exc),
                    owner=lease.owner, epoch=lease.epoch,
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

            # Record external operation before re-dispatch.
            idempotency_key = f"single-exec-{task_id}-{run.execution_id}"
            request_digest = _digest(_json_payload({
                "task_id": task_id,
                "execution_id": run.execution_id,
                "workspace_root": workspace_root,
                "repo_base": run.repository_base_sha,
            }))

            # Check if we already have a recorded (but unreconciled) operation.
            if self.store._external_operation_prevents_dispatch(
                idempotency_key, request_digest,
            ):
                # Ambiguous: dispatch may have happened but completion unproven.
                # FAIL CLOSED: do not re-issue.
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="ambiguous_external_operation",
                    detail="external operation already recorded; refusing second dispatch",
                    owner=lease.owner, epoch=lease.epoch,
                )
                self.store._fenced_terminalize(
                    lease.run_id, task_id,
                    terminal_status="FAILED",
                    validation_command_id="",
                    validation_exit_code=-1,
                    validation_output_digest="",
                    failure_classification="ambiguous_external_operation",
                    failure_detail="external operation already recorded; refusing second dispatch",
                    owner=lease.owner, epoch=lease.epoch,
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

            ext_op = self.store._record_external_operation(
                operation_key=f"single-exec-{task_id}",
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )

            try:
                exec_result = self._execution_service._dispatch_executor(
                    task=task,
                    workspace_root=workspace_root,
                    validation_command_id="git_diff_check",
                    executor_kwargs=executor_kwargs,
                )
            except Exception as exc:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="executor_dispatch_failed",
                    detail=f"executor_dispatch_exception:{exc}",
                    owner=lease.owner, epoch=lease.epoch,
                )
                self.store._fenced_terminalize(
                    lease.run_id, task_id,
                    terminal_status="FAILED",
                    validation_command_id="",
                    validation_exit_code=-1,
                    validation_output_digest="",
                    failure_classification="executor_dispatch_failed",
                    failure_detail=f"executor_dispatch_exception:{exc}",
                    owner=lease.owner, epoch=lease.epoch,
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

            self.store._reconcile_external_operation(
                operation_id=ext_op.operation_id,
                external_operation_id=ext_op.operation_id,
                result_state="success" if exec_result["success"] else "failure",
            )

            if exec_result["success"]:
                computed_wt = os.path.join(workspace_root, task_id)
                if Path(computed_wt).exists():
                    self.store._set_worktree_identity(
                        lease.run_id, computed_wt,
                        self._git_rev_parse_head(computed_wt),
                        lease.owner, lease.epoch,
                    )
                    wt_path = computed_wt
                    prepared_path = Path(wt_path)
            else:
                self.store._accept_checkpoint(
                    lease.run_id, "POST_PLANNER",
                    _digest(str(exec_result.get("error", ""))),
                    role_attempt, lease.owner, lease.epoch,
                )
                self.store._accept_checkpoint(
                    lease.run_id, "POST_CODER", "",
                    role_attempt, lease.owner, lease.epoch,
                )
                self.store._accept_checkpoint(
                    lease.run_id, "POST_REVIEWER", "",
                    role_attempt, lease.owner, lease.epoch,
                )
                self.store._accept_checkpoint(
                    lease.run_id, "POST_VALIDATION", "",
                    role_attempt, lease.owner, lease.epoch,
                )
                classification = (
                    exec_result.get("failure_classification", "failed") or "failed"
                )
                self.store._fenced_terminalize(
                    lease.run_id, task_id,
                    terminal_status="FAILED",
                    validation_command_id=exec_result.get("validation_command_id", ""),
                    validation_exit_code=exec_result.get("validation_exit_code", -1),
                    validation_output_digest=exec_result.get("validation_output_digest", ""),
                    failure_classification=classification,
                    failure_detail=exec_result.get("error", "executor failed"),
                    owner=lease.owner, epoch=lease.epoch,
                )
                final = self.store.get_task(task_id)
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=final.execution_id,
                    success=False,
                    validation_command_id=exec_result.get("validation_command_id", ""),
                    validation_exit_code=exec_result.get("validation_exit_code", -1),
                    failure_classification=final.failure_classification,
                    failure_detail=final.failure_detail,
                )

            # Accept POST_PLANNER, POST_CODER, POST_REVIEWER for successful dispatch.
            self.store._accept_checkpoint(
                lease.run_id, "POST_PLANNER",
                _digest(_json_payload(exec_result)),
                role_attempt, lease.owner, lease.epoch,
            )
            _check_crash_seam("POST_PLANNER")
            self.store._fenced_set_changed_files(
                lease.run_id, task_id, tuple(exec_result.get("changed_files", [])),
                lease.owner, lease.epoch,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_CODER", "",
                role_attempt, lease.owner, lease.epoch,
            )
            _check_crash_seam("POST_CODER")
            self.store._set_validation_result(
                lease.run_id,
                command_id=exec_result.get("validation_command_id", "git_diff_check"),
                exit_code=exec_result.get("validation_exit_code", 0),
                output_digest=exec_result.get("validation_output_digest", ""),
                owner=lease.owner, epoch=lease.epoch,
            )
            self.store._accept_checkpoint(
                lease.run_id, "POST_REVIEWER", "",
                role_attempt, lease.owner, lease.epoch,
            )
            _check_crash_seam("POST_REVIEWER")

        # --- Validation phase (common path) ---
        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=wt_path,
            )
        except Exception:
            val_exit, val_output, val_digest = -1, "", ""

        self.store._set_validation_result(
            lease.run_id,
            command_id="git_diff_check",
            exit_code=val_exit,
            output_digest=val_digest,
            owner=lease.owner, epoch=lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_VALIDATION", "",
            role_attempt, lease.owner, lease.epoch,
        )
        _check_crash_seam("POST_VALIDATION")

        final_changed = _collect_final_product_files(prepared_path)
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, final_changed,
            lease.owner, lease.epoch,
        )

        self.store._fenced_transition_to(
            lease.run_id, task_id, "VALIDATING",
            lease.owner, lease.epoch,
        )
        if val_exit == 0:
            self.store._fenced_transition_to(
                lease.run_id, task_id, "READY_FOR_REVIEW",
                lease.owner, lease.epoch,
            )
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="VALIDATED",
                title="Durable single execution validated (resume)",
                description="resume validation completed",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": "git_diff_check",
                    "run_id": lease.run_id,
                },
                owner=lease.owner, epoch=lease.epoch,
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id="git_diff_check",
                validation_exit_code=val_exit,
            )

        self.store._fenced_terminalize(
            lease.run_id, task_id,
            terminal_status="FAILED",
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            validation_output_digest=val_digest,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
            owner=lease.owner, epoch=lease.epoch,
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
        )

    def _resume_with_lease(
        self,
        task_id: str,
        workspace_root: str,
        run: Any,
        lease: LeaseHandle,
        *,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        from .task_execution import TaskExecutionOutcome
        from .opencode_executor import _collect_product_diff

        if run.accepted_checkpoint == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            if stored.status == "READY_FOR_REVIEW":
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=True,
                    validation_command_id=run.validation_command_id or "git_diff_check",
                    validation_exit_code=run.validation_exit_code or 0,
                )

        if run.accepted_checkpoint == "":
            if not run.worktree_path:
                raise DurableResumeError(
                    f"pre_pre_planner_crash_no_prepared_worktree:{task_id}:"
                    f"cannot_dispatch_roles_from_workspace_root_fail_closed"
                )
            actual_head = self._git_rev_parse_head(run.worktree_path)
            stored_wt_head = getattr(run, "worktree_head_sha", "") or ""
            if stored_wt_head and actual_head != stored_wt_head:
                raise DurableResumeError(
                    f"pre_pre_planner_worktree_head_mismatch:{task_id}:"
                    f"stored={stored_wt_head}:actual={actual_head}"
                )
            if not stored_wt_head:
                raise DurableResumeError(
                    f"pre_pre_planner_no_worktree_identity:{task_id}:"
                    f"cannot_prove_prepared_worktree_fail_closed"
                )

        if run.accepted_checkpoint == "POST_REVIEWER":
            return self._resume_from_post_reviewer(task_id, run, lease, run.role_attempt)

        run_role_attempt = run.role_attempt

        # Interrupted Coder handling: if Coder started but POST_CODER was not accepted,
        # preserve partial diff, persist bounded digest, increment attempt.
        if run.accepted_checkpoint in ("PRE_PLANNER", "POST_PLANNER") and run.current_role == "coder":
            wt_path = run.worktree_path or workspace_root
            partial = _collect_product_diff(Path(wt_path)) if Path(wt_path).exists() else ()
            if partial:
                partial_digest = _digest(_json_payload(list(partial)))
                self.store._set_partial_coder_diff_digest(
                    lease.run_id, partial_digest, lease.owner, lease.epoch
                )
                self.store._set_coder_product_diff_digest(
                    lease.run_id, partial_digest, lease.owner, lease.epoch
                )
            run_role_attempt = run_role_attempt + 1
            self.store._set_role_attempt(
                lease.run_id, "coder", run_role_attempt, lease.owner, lease.epoch
            )
            self.store._set_recovery_classification(
                lease.run_id, "interrupted", lease.owner, lease.epoch
            )

        return self._resume_roles(
            task_id=task_id,
            workspace_root=workspace_root,
            run=run,
            lease=lease,
            executor=None,
            accepted=run.accepted_checkpoint,
            current_role=run.current_role,
            role_attempt=run_role_attempt,
            checkpointer=checkpointer,
        )

    def _resume_roles(
        self,
        *,
        task_id: str,
        workspace_root: str,
        run: Any,
        lease: LeaseHandle,
        executor: Any,
        accepted: str,
        current_role: str,
        role_attempt: int,
        checkpointer: Any | None = None,
    ) -> TaskExecutionOutcome:
        from .task_execution import TaskExecutionOutcome
        from .task_runtime import LocalValidationRunner
        from .opencode_executor import (
            _collect_product_diff,
            _collect_final_product_files,
            _handoff_digest,
            _remove_handoff,
            handoff_dir,
        )
        from reverse_agent.workflows.team_graph import TeamGraphError

        self.store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)

        stored = self.store.get_task(task_id)
        if stored.status == "INTERRUPTED":
            self.store._fenced_transition_to(
                lease.run_id, task_id, "RUNNING",
                lease.owner, lease.epoch,
            )

        if accepted == "POST_REVIEWER":
            return self._resume_from_post_reviewer(task_id, run, lease, role_attempt)
        if accepted == "POST_VALIDATION":
            stored = self.store.get_task(task_id)
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id=run.validation_command_id or "git_diff_check",
                validation_exit_code=run.validation_exit_code or 0,
            )

        if executor is None:
            task = self.store.get_task(task_id)
            try:
                executor = self.router.create_executor(
                    executor_kind="opencode", **self._build_executor_kwargs(task)
                )
            except Exception as exc:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="blocked", detail=str(exc),
                    owner=lease.owner, epoch=lease.epoch,
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

        wt_path = run.worktree_path or workspace_root
        prepared_path = Path(wt_path)
        handoff = handoff_dir(prepared_path) if prepared_path.exists() else None

        baseline_product = _collect_product_diff(prepared_path) if prepared_path.exists() else ()
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, baseline_product,
            lease.owner, lease.epoch,
        )

        plan_digest = run.planner_handoff_digest
        review_digest = run.reviewer_handoff_digest
        coder_product_snapshot: tuple[dict[str, Any], ...] = ()

        if accepted == "POST_CODER":
            persisted_coder_digest = run.coder_product_diff_digest
            if persisted_coder_digest == "":
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="coder_snapshot_missing",
                    detail="persistent Coder snapshot digest is empty; refusing to resume Reviewer",
                    owner=lease.owner, epoch=lease.epoch,
                )
                final = self.store.get_task(task_id)
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=final.execution_id,
                    success=False, validation_command_id="",
                    validation_exit_code=-1,
                    failure_classification="coder_snapshot_missing",
                    failure_detail="persistent Coder snapshot digest is empty; refusing to resume Reviewer",
                )
            reconstructed_digest = _digest(_json_payload(list(baseline_product)))
            if reconstructed_digest != persisted_coder_digest:
                self.store._fenced_classify_failure(
                    lease.run_id, task_id,
                    classification="coder_snapshot_mismatch",
                    detail=f"persisted Coder snapshot digest {persisted_coder_digest} does not match reconstructed worktree digest {reconstructed_digest}; refusing to resume Reviewer",
                    owner=lease.owner, epoch=lease.epoch,
                )
                final = self.store.get_task(task_id)
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=final.execution_id,
                    success=False, validation_command_id="",
                    validation_exit_code=-1,
                    failure_classification="coder_snapshot_mismatch",
                    failure_detail=f"persisted Coder snapshot digest {persisted_coder_digest} does not match reconstructed worktree digest {reconstructed_digest}; refusing to resume Reviewer",
                )
            coder_product_snapshot = baseline_product

        _graph_config = {"configurable": {"thread_id": lease.run_id}}

        # Resolve production checkpointer from persisted checkpoint_db_path
        _resume_saver = checkpointer
        if _resume_saver is None and run.checkpoint_db_path:
            cp_path = run.checkpoint_db_path
            if Path(cp_path).exists():
                import sqlite3 as _sq3
                _cp_conn = _sq3.connect(
                    cp_path, isolation_level=None, check_same_thread=False
                )
                _cp_conn.execute("PRAGMA journal_mode=WAL")
                _resume_saver = _make_strict_saver(_cp_conn)

        remaining_roles = [
            r for r, cp in [
                ("planner", "POST_PLANNER"),
                ("coder", "POST_CODER"),
                ("reviewer", "POST_REVIEWER"),
            ]
            if cp not in ("POST_PLANNER",) or accepted != "POST_PLANNER"
            if cp not in ("POST_PLANNER", "POST_CODER") or accepted != "POST_CODER"
        ]

        if accepted == "PRE_PLANNER":
            remaining_roles = ["planner", "coder", "reviewer"]
        elif accepted == "POST_PLANNER":
            remaining_roles = ["coder", "reviewer"]
        elif accepted == "POST_CODER":
            remaining_roles = ["reviewer"]
        elif accepted == "POST_REVIEWER":
            return self._resume_from_post_reviewer(task_id, run, lease, role_attempt)

        for role in remaining_roles:
            cp_name = _checkpoint_name_for_role(role)
            if not cp_name:
                continue

            result = self._execute_single_role(
                role=role,
                task_id=task_id,
                prepared=prepared_path,
                handoff=handoff or Path(wt_path) / ".handoff",
                executor=executor,
                baseline=baseline_product,
                plan_digest=plan_digest,
                role_attempt=role_attempt,
                coder_product_snapshot=coder_product_snapshot,
                checkpointer=_resume_saver,
                graph_config=_graph_config,
            )

            if not result["success"]:
                self._complete_durable_failure(
                    task_id, run, lease, baseline_product, plan_digest,
                    roles_executed=result.get("roles_executed", []),
                    role_results=result.get("role_results", []),
                    classification=result.get("classification", "failed"),
                    failure_detail=result.get("detail", "role failed"),
                )
                return TaskExecutionOutcome(
                    task_id=task_id,
                    execution_id=run.execution_id,
                    success=False, validation_command_id="",
                    validation_exit_code=result.get("val_exit", -1),
                    failure_classification=result.get("classification", "failed"),
                    failure_detail=result.get("detail", "role failed"),
                )

            if role == "planner":
                plan_digest = result["digest"]
                self.store._set_planner_handoff_digest(
                    lease.run_id, plan_digest, lease.owner, lease.epoch
                )
            elif role == "coder":
                coder_product_snapshot = result["snapshot"]
                coder_digest = _digest(_json_payload(list(coder_product_snapshot)))
                self.store._set_coder_product_diff_digest(
                    lease.run_id, coder_digest, lease.owner, lease.epoch
                )
                plan_digest = result.get("plan_digest", plan_digest)
            elif role == "reviewer":
                review_digest = result["digest"]
                self.store._set_reviewer_handoff_digest(
                    lease.run_id, review_digest, lease.owner, lease.epoch
                )

            self.store._accept_checkpoint(
                lease.run_id, cp_name,
                result.get("digest", ""),
                role_attempt, lease.owner, lease.epoch,
            )
            _check_crash_seam(cp_name)

        val_runner = LocalValidationRunner()
        try:
            val_exit, val_output, val_digest = val_runner.run(
                task_id=task_id, command_id="git_diff_check", cwd=wt_path,
            )
        except Exception:
            val_exit, val_output, val_digest = -1, "", ""

        self.store._set_validation_result(
            lease.run_id, command_id="git_diff_check",
            exit_code=val_exit, output_digest=val_digest,
            owner=lease.owner, epoch=lease.epoch,
        )
        self.store._accept_checkpoint(
            lease.run_id, "POST_VALIDATION", "",
            role_attempt, lease.owner, lease.epoch,
        )

        if handoff:
            _remove_handoff(handoff)
        final_changed = _collect_final_product_files(prepared_path)
        self.store._fenced_set_changed_files(
            lease.run_id, task_id, final_changed,
            lease.owner, lease.epoch,
        )

        self.store._fenced_transition_to(
            lease.run_id, task_id, "VALIDATING",
            lease.owner, lease.epoch,
        )
        if val_exit == 0:
            self.store._fenced_transition_to(
                lease.run_id, task_id, "READY_FOR_REVIEW",
                lease.owner, lease.epoch,
            )
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="VALIDATED",
                title="Durable sequential team validated (resume)",
                description="resume per-role checkpoint acceptance completed",
                metadata={
                    "validation_exit_code": val_exit,
                    "validation_command_id": "git_diff_check",
                    "plan_digest": plan_digest,
                    "review_digest": review_digest,
                    "run_id": lease.run_id,
                },
                owner=lease.owner, epoch=lease.epoch,
            )
            return TaskExecutionOutcome(
                task_id=task_id,
                execution_id=run.execution_id,
                success=True,
                validation_command_id="git_diff_check",
                validation_exit_code=val_exit,
            )

        self.store._fenced_terminalize(
            lease.run_id, task_id,
            terminal_status="FAILED",
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            validation_output_digest=val_digest,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
            owner=lease.owner, epoch=lease.epoch,
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
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

        self.store._fenced_transition_to(
            lease.run_id, task_id, "VALIDATING",
            lease.owner, lease.epoch,
        )
        if val_exit == 0:
            self.store._fenced_transition_to(
                lease.run_id, task_id, "READY_FOR_REVIEW",
                lease.owner, lease.epoch,
            )
            self.store._fenced_add_event(
                lease.run_id, task_id,
                event_type="VALIDATED",
                title="Sequential team validated (resume from POST_REVIEWER)",
                description="post-reviewer validation passed",
                metadata={"validation_exit_code": val_exit},
                owner=lease.owner, epoch=lease.epoch,
            )
            self.store._set_validation_result(
                lease.run_id,
                command_id="git_diff_check",
                exit_code=val_exit,
                output_digest=val_digest,
                owner=lease.owner, epoch=lease.epoch,
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
        self.store._fenced_terminalize(
            lease.run_id, task_id,
            terminal_status="FAILED",
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            validation_output_digest=val_digest,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
            owner=lease.owner, epoch=lease.epoch,
        )
        return TaskExecutionOutcome(
            task_id=task_id,
            execution_id=run.execution_id,
            success=False,
            validation_command_id="git_diff_check",
            validation_exit_code=val_exit,
            failure_classification="deterministic_validation_failure",
            failure_detail=f"git_diff_check exit={val_exit}",
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
            expiry_ms=self.expiry_ms,
            execution_authority_sha=self._trusted_authority_sha(),
            planning_sha=self._trusted_planning_sha(),
        )

    def heartbeat_lease(self, run_id: str, owner: str, epoch: int) -> None:
        self.store._heartbeat_durable_lease(run_id, owner, epoch, self.expiry_ms)

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
        return self.store._recover_durable_lease(
            run_id, lease_owner, expiry_ms=self.expiry_ms,
            require_interrupted=False,
        )

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

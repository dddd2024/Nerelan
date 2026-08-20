"""Crash-resumable coordinator for explicitly activated autonomous windows."""

from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import threading
import time
import uuid
from typing import Any, Callable

from .autonomy import AutonomyService
from .control_store import PlatformControlStore
from .durable_execution import DurableExecutionService
from .run_store import TaskStore, TaskStoreError
from .task_execution import TaskExecutionService
from .task_runtime import ExecutorRouter
from reverse_agent.architecture.contracts import (
    WorkerAssignment,
    WorkerExecutionResult,
)
from reverse_agent.workflows.team_graph import build_team_graph


TaskExecutor = Callable[[str], Any]


class UnattendedCoordinator:
    """Runs queued Goal tasks without duplicating or bypassing policy checks.

    The loop is inert until both the trusted host enables it and an owner has
    activated a bounded window. Atomic claims live in SQLite, so a restarted
    coordinator can safely continue after durable-run reconciliation.
    """

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore,
        autonomy: AutonomyService,
        router: ExecutorRouter,
        workspace_root: str | Path,
        binding_resolver: Any | None = None,
        lease_provider: Any | None = None,
        execution_authority_sha: str = "",
        planning_sha: str = "",
        task_executor: TaskExecutor | None = None,
        poll_interval: float = 1.0,
        claim_lease_ms: int = 15 * 60 * 1000,
        owner: str | None = None,
    ) -> None:
        self.store = store
        self.control_store = control_store
        self.autonomy = autonomy
        self.router = router
        self.workspace_root = str(Path(workspace_root).resolve())
        self.binding_resolver = binding_resolver
        self.lease_provider = lease_provider
        self.execution_authority_sha = execution_authority_sha
        self.planning_sha = planning_sha
        self.task_executor = task_executor
        self.poll_interval = max(0.1, poll_interval)
        self.claim_lease_ms = max(10_000, claim_lease_ms)
        self.owner = owner or f"coordinator-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_error = ""
        self._last_batch: dict[str, Any] = {}
        self._ticks = 0
        self._executions = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        Path(self.workspace_root).mkdir(parents=True, exist_ok=True)
        self.reconcile()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="reverse-agent-unattended", daemon=True
        )
        self._thread.start()

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        self._thread = None

    def reconcile(self) -> tuple[str, ...]:
        durable = self._durable_service()
        reconciled: list[str] = []
        try:
            result = durable.reconcile_expired_runs()
        except Exception as exc:
            self._last_error = f"reconcile_failed:{type(exc).__name__}"
            result = None
        if isinstance(result, (list, tuple)):
            reconciled.extend(str(value) for value in result)
        elif result is not None:
            reconciled.append(str(result))
        try:
            reconciled.extend(
                self.control_store.reconcile_expired_budget_reservations()
            )
        except Exception as exc:
            self._last_error = f"budget_reconcile_failed:{type(exc).__name__}"
        return tuple(reconciled)

    def tick(self) -> int:
        self._ticks += 1
        window = self.control_store.active_window()
        if window is None:
            return 0
        claimed: dict[str, int] = {}
        for task_id in self.control_store.runnable_tasks(
            window.id, limit=window.max_concurrent_tasks
        ):
            task = self.store.get_task(task_id)
            operation = "resume_task" if task.status == "INTERRUPTED" else "execute_task"
            if not self.autonomy.authorize(
                window_id=window.id,
                operation=operation,
                repository=task.repository,
                subject_id=task_id,
                input_payload={"task_id": task_id, "status": task.status},
            ):
                continue
            try:
                epoch, _ = self.control_store.claim_task(
                    window_id=window.id,
                    task_id=task_id,
                    owner=self.owner,
                    lease_ms=self.claim_lease_ms,
                )
            except TaskStoreError as exc:
                if str(exc) in {
                    "window_wip_limit_reached", "window_task_budget_exhausted",
                    "window_retry_budget_exhausted", "window_token_budget_exhausted",
                    "window_cost_budget_exhausted",
                }:
                    break
                if str(exc) == "task_already_claimed":
                    continue
                self._last_error = str(exc)
                continue
            claimed[task_id] = epoch
        if not claimed:
            return 0
        return self._execute_claimed_batch(window_id=window.id, claimed=claimed)

    def _execute_claimed_batch(
        self,
        *,
        window_id: str,
        claimed: dict[str, int],
    ) -> int:
        """Fan out an already-admitted batch through LangGraph ``Send``.

        Claims and budget reservations are acquired before graph invocation.
        Each branch owns one distinct durable TaskStore task and finalizes only
        that task's claim. A process-level crash therefore leaves the existing
        per-task claim, reservation, durable lease and checkpoint recovery
        protocol intact; there is deliberately no aggregate batch database.
        """

        def execute_assignment(
            assignment: WorkerAssignment,
        ) -> WorkerExecutionResult:
            task_id = assignment.task_id
            epoch = claimed[task_id]
            try:
                outcome = self._execute_task(task_id)
                final = self.store.get_task(task_id)
                success = bool(getattr(outcome, "success", True)) and final.status in {
                    "READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"
                }
                result = "success" if success else f"terminal:{final.status}"
                self.control_store.complete_task_claim(
                    window_id=window_id,
                    task_id=task_id,
                    owner=self.owner,
                    epoch=epoch,
                    result=result,
                )
                return WorkerExecutionResult(
                    worker_id=assignment.worker_id,
                    task_id=task_id,
                    execution_id=str(
                        getattr(outcome, "execution_id", "")
                        or final.execution_id
                    ),
                    success=success,
                    validation_exit_code=int(
                        getattr(outcome, "validation_exit_code", 0 if success else -1)
                    ),
                    evidence_ids=tuple(getattr(outcome, "evidence_ids", ())),
                    failure_classification=final.failure_classification,
                    failure_detail=final.failure_detail,
                    reasons=("claim_completed",),
                )
            except Exception as exc:
                try:
                    self.control_store.abandon_task_claim(
                        window_id=window_id,
                        task_id=task_id,
                        owner=self.owner,
                        epoch=epoch,
                        reason=f"execution_failed:{task_id}:{type(exc).__name__}",
                    )
                except TaskStoreError:
                    pass
                return WorkerExecutionResult(
                    worker_id=assignment.worker_id,
                    task_id=task_id,
                    execution_id="",
                    success=False,
                    validation_exit_code=-1,
                    failure_classification="coordinator_execution_error",
                    failure_detail=type(exc).__name__,
                    reasons=("claim_abandoned", f"worker_exception:{type(exc).__name__}"),
                )

        assignments = [
            WorkerAssignment(
                worker_id=f"task-{index:03d}",
                role="task_executor",
                task_id=task_id,
                workspace_root=self.workspace_root,
            ).to_dict()
            for index, task_id in enumerate(sorted(claimed), start=1)
        ]
        try:
            graph_result = build_team_graph(worker=execute_assignment).invoke(
                {"assignments": assignments}
            )
        except Exception as exc:
            for task_id, epoch in claimed.items():
                try:
                    self.control_store.abandon_task_claim(
                        window_id=window_id,
                        task_id=task_id,
                        owner=self.owner,
                        epoch=epoch,
                        reason=f"parallel_batch_failed:{type(exc).__name__}",
                    )
                except TaskStoreError:
                    pass
            self._refresh_claimed_goals(tuple(claimed))
            self._last_error = f"parallel_batch_failed:{type(exc).__name__}"
            self._last_batch = {
                "accepted": False,
                "size": len(claimed),
                "reasons": [self._last_error],
            }
            return 0

        team_result = dict(graph_result.get("team_execution_result") or {})
        worker_results = list(team_result.get("worker_results") or [])
        self._refresh_claimed_goals(tuple(claimed))
        completed = sum(
            "claim_completed" in tuple(result.get("reasons") or ())
            for result in worker_results
        )
        self._executions += completed
        self._last_batch = {
            "accepted": bool(team_result.get("accepted", False)),
            "size": len(worker_results),
            "task_ids": [str(result.get("task_id", "")) for result in worker_results],
            "reasons": list(team_result.get("reasons") or []),
            "failures": [
                {
                    "task_id": str(result.get("task_id", "")),
                    "classification": str(result.get("failure_classification", "")),
                    "detail": str(result.get("failure_detail", ""))[:220],
                }
                for result in worker_results
                if not bool(result.get("success"))
            ],
        }
        failed = next(
            (result for result in worker_results if not bool(result.get("success"))),
            None,
        )
        if failed is not None:
            self._last_error = f"task_unsuccessful:{failed.get('task_id', '')}"
        return completed

    def _refresh_claimed_goals(self, task_ids: tuple[str, ...]) -> None:
        goal_ids: set[str] = set()
        for task_id in task_ids:
            try:
                goal_ids.add(self.control_store.goal_id_for_task(task_id))
            except TaskStoreError:
                self._last_error = f"goal_link_not_found:{task_id}"
        for goal_id in sorted(goal_ids):
            try:
                self.control_store.refresh_goal_status(goal_id)
            except TaskStoreError as exc:
                self._last_error = f"goal_refresh_failed:{type(exc).__name__}"

    def status(self) -> dict[str, Any]:
        active = self.control_store.active_window()
        return {
            "enabled": self._thread is not None and self._thread.is_alive(),
            "owner": self.owner,
            "ticks": self._ticks,
            "executions": self._executions,
            "last_error": self._last_error,
            "last_batch": dict(self._last_batch),
            "active_window_id": active.id if active else "",
            "workspace_root": self.workspace_root,
        }

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as exc:
                self._last_error = f"coordinator_tick_failed:{type(exc).__name__}"
            self._stop.wait(self.poll_interval)

    def _execute_task(self, task_id: str) -> Any:
        if self.task_executor is not None:
            return self.task_executor(task_id)
        task = self.store.get_task(task_id)
        durable_identity_available = bool(
            self.execution_authority_sha.strip() and self.planning_sha.strip()
        )
        if task.executor_kind == "deterministic_fixture" and not durable_identity_available:
            if task.status != "QUEUED":
                raise TaskStoreError(f"fixture_task_not_queued:{task.status}")
            return TaskExecutionService(store=self.store, router=self.router).execute(
                task_id, workspace_root=self.workspace_root
            )
        durable = self._durable_service()
        if task.status == "INTERRUPTED":
            if task.orchestration_mode == "single":
                return durable.resume_single(task_id=task_id, lease_owner=self.owner)
            return durable.resume_sequential_team(task_id=task_id, lease_owner=self.owner)
        if task.orchestration_mode == "single":
            return durable.execute_durable_single(
                task_id=task_id, workspace_root=self.workspace_root, lease_owner=self.owner
            )
        return durable.execute_durable_sequential_team(
            task_id=task_id, workspace_root=self.workspace_root, lease_owner=self.owner
        )

    def _durable_service(self) -> DurableExecutionService:
        return DurableExecutionService(
            store=self.store,
            router=self.router,
            binding_resolver=self.binding_resolver,
            lease_provider=self.lease_provider,
            execution_authority_sha=self.execution_authority_sha,
            planning_sha=self.planning_sha,
        )

"""Crash-resumable coordinator for explicitly activated autonomous windows."""

from __future__ import annotations

from dataclasses import asdict
import logging
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
from .task_execution import TaskExecutionService, TaskExecutionOutcome
from .task_runtime import ExecutorRouter, load_host_validation_contract, task_operation
from reverse_agent.architecture.contracts import (
    WorkerAssignment,
    WorkerExecutionResult,
)
from reverse_agent.workflows.team_graph import build_team_graph


_logger = logging.getLogger(__name__)


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
        goal_escalator: Any | None = None,
        quota_preparer: Any | None = None,
        quota_rerouter: Any | None = None,
        landing_loop=None, publication=None, goals=None,
    ) -> None:
        # goal_id -> escalations; hands FAILED agent_team tasks to stronger agents.
        self.landing_loop = landing_loop
        self.publication = publication
        self.goals = goals
        self.quota_preparer = quota_preparer
        # goal_id -> moves; quota-held tasks to an equal-or-higher-tier model (#1313 D).
        self.quota_rerouter = quota_rerouter
        self.goal_escalator = goal_escalator
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
        self.claim_lease_ms = max(1, claim_lease_ms)
        self.owner = owner or f"coordinator-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()
        self._dispatch_active = False
        # The live poller may refill idle slots while older batches are running.
        # Direct tick() remains synchronous for deterministic host/test callers.
        self._batch_threads: dict[threading.Thread, int] = {}
        self._active_task_ids: set[str] = set()
        # A later retry can overlap an older graph batch that still drains
        # another task. Epoch ownership keeps old finally blocks from erasing
        # the retry's active marker.
        self._active_task_epochs: dict[str, int] = {}
        self._worker_thread_ids: set[int] = set()
        self._manual_tick_active = False
        self._manual_tick_idle = threading.Event()
        self._manual_tick_idle.set()
        self._last_error = ""
        self._last_batch: dict[str, Any] = {}
        self._ticks = 0
        self._executions = 0

    def start(self) -> None:
        with self._lifecycle_lock:
            thread = self._thread
            if thread is not None and thread.is_alive():
                if self._stop.is_set():
                    self._last_error = "coordinator_still_draining"
                return
            if thread is not None:
                self._thread = None
            Path(self.workspace_root).mkdir(parents=True, exist_ok=True)
            self.reconcile()
            self._stop.clear()
            thread = threading.Thread(
                target=self._run, name="reverse-agent-unattended", daemon=True
            )
            self._thread = thread
            thread.start()

    def stop(self, *, timeout: float = 5.0) -> None:
        with self._lifecycle_lock:
            self._stop.set()
            thread = self._thread
            in_worker = (threading.current_thread() in self._batch_threads
                         or threading.get_ident() in self._worker_thread_ids)
        if thread is None:
            return
        if thread is threading.current_thread() or in_worker:
            self._last_error = "coordinator_stop_requested_from_worker"
            return
        thread.join(timeout=max(0.0, timeout))
        with self._lifecycle_lock:
            if self._thread is not thread:
                return
            if thread.is_alive():
                self._last_error = "coordinator_stop_timeout"
                return
            self._thread = None
            if self._last_error in {
                "coordinator_stop_timeout",
                "coordinator_still_draining",
                "coordinator_stop_requested_from_worker",
            }:
                self._last_error = ""

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

    def tick(self, *, background: bool = False) -> int:
        # External synchronous ticks must not race the live poller: they are
        # a separate deterministic invocation mode, not an extra worker slot.
        with self._lifecycle_lock:
            if background:
                if self._manual_tick_active:
                    return 0
            else:
                if (self._manual_tick_active
                        or (self._thread is not None and self._thread.is_alive())):
                    return 0
                self._manual_tick_active = True
                self._manual_tick_idle.clear()
        if background:
            return self._tick_impl(background=True)
        try:
            return self._tick_impl(background=False)
        finally:
            with self._lifecycle_lock:
                self._manual_tick_active = False
                self._manual_tick_idle.set()

    def _advance_landing(self, window):
        if self.landing_loop is None:
            return
        # Bounded scan over local intent; GitHub truth is read by each tick.
        if window is not None and self.publication is not None and self.goals is not None:
            from . import artifact_handoff as artifacts
            rows = self.control_store._conn.execute(
                "SELECT task_id FROM platform_goal_task_links LIMIT 100").fetchall()
            for row in rows:
                task = self.store.get_task(row["task_id"])
                if task.status != "READY_FOR_REVIEW" or not artifacts._load_evidence(
                        task, artifacts.ACCEPTED_CATEGORY, task.execution_id):
                    continue
                goal = self.control_store.get_goal(self.control_store.goal_id_for_task(task.id))
                if goal.window_id != window.id or self.control_store.landing_progress(goal.id):
                    continue
                try:
                    self.landing_loop.publish_and_review(task.id, window_id=window.id,
                        publication=self.publication, goals=self.goals,
                        execution=self._durable_service(), workspace_root=self.workspace_root)
                except TaskStoreError as exc:
                    self._last_error = str(exc)
                break
        rows = self.control_store._conn.execute(
            "SELECT identity,goal_id FROM platform_landing_state WHERE phase NOT IN "
            "('BLOCKED','COMPLETE','SUPERSEDED') ORDER BY next_attempt_ms LIMIT 10").fetchall()
        for row in rows:
            goal = self.control_store.get_goal(row["goal_id"])
            if goal.window_id:
                self.landing_loop.tick(row["identity"], window_id=goal.window_id)

    def _tick_impl(self, *, background: bool) -> int:
        if self._stop.is_set():
            return 0
        self._ticks += 1
        if self._stop.is_set():
            return 0
        window = self.control_store.active_window()
        if window is None:
            # An Owner-approved standing policy renews a time-expired window (#1310 D).
            try:
                window = self.control_store.renew_standing_window()
            except TaskStoreError as exc:
                self._last_error = f"standing_renewal_failed:{exc}"
                window = None
            if window is None:
                self._advance_landing(None)
                return 0
        try:
            self.control_store.adopt_standing_goals(window.id)
        except TaskStoreError as exc:
            self._last_error = f"standing_adoption_failed:{exc}"
        self._advance_landing(window)
        if getattr(self.autonomy, "delegated_mode", False) and "approve_goal" in window.capabilities:
            from .goal_service import GoalService
            try:
                self.autonomy.admit_goals(GoalService(store=self.store, control_store=self.control_store), window_id=window.id)
            except TaskStoreError as exc:
                self._last_error = str(exc)
                return 0
            if self._stop.is_set():
                return 0
        with self._lifecycle_lock:
            # Bound admission *before* claiming: old graph batches continue
            # running and still occupy slots even if newer tasks arrive.
            if self._dispatch_active and not background:
                return 0
            running_slots = len(self._active_task_ids) if background else 0
            free_slots = max(0, window.max_concurrent_tasks - running_slots)
        if free_slots == 0:
            return 0
        claimed: dict[str, int] = {}
        held: list[str] = []
        recovered = 0
        # A claimed task can still be QUEUED while its executor is running.
        # Scan past already-claimed rows instead of starving later candidates.
        for task_id in self.control_store.runnable_tasks(
            window.id, limit=500
        ):
            if len(claimed) >= free_slots:
                break
            if self._stop.is_set():
                break
            with self._lifecycle_lock:
                if task_id in self._active_task_ids:
                    # A live executor may outlast a DB Claim lease while the
                    # task stays QUEUED. Never create a second executor.
                    continue
            task = self.store.get_task(task_id)
            if self._stop.is_set():
                break
            if (self.control_store.is_strict_owner_window(window)
                    and task.status in {"READY_FOR_REVIEW", "FAILED"}):
                # Result-only recovery is not admission to validate_task. The
                # store rechecks identity and evidence atomically and finalizes
                # the original epoch/reservation without invoking any executor.
                try:
                    self.control_store.complete_persisted_host_claim(
                        window_id=window.id, task_id=task_id)
                except TaskStoreError as exc:
                    self._last_error = str(exc)
                    continue
                recovered += 1
                self._executions += 1
                continue
            operation = task_operation(task)
            if task.status in {"INTERRUPTED", "QUOTA_WAIT"} and operation != "validate_task":
                operation = "resume_task"
            if not self.autonomy.authorize(
                window_id=window.id,
                operation=operation,
                repository=task.repository,
                subject_id=task_id,
                input_payload={"task_id": task_id, "status": task.status},
            ):
                continue
            if self._stop.is_set():
                break
            try:
                if task.status == "QUOTA_WAIT" and self.quota_preparer is None:
                    raise TaskStoreError("QUOTA_WAIT:fresh_evidence_unavailable")
                if self.quota_preparer is not None:
                    self.quota_preparer(task)
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
                if str(exc).startswith("QUOTA_WAIT"):
                    held.append(task_id)
                self._last_error = str(exc)
                continue
            claimed[task_id] = epoch
            if self._stop.is_set():
                break
        if held:
            # A fully held goal claims nothing, so post-execution escalation never
            # runs for it: offer the held tasks to the rerouter here.
            self._reroute_held(held)
        if not claimed:
            return recovered
        if not self._begin_dispatch(background=background):
            self._abandon_claimed_before_dispatch(
                window_id=window.id,
                claimed=claimed,
                reason="coordinator_stop_requested_before_dispatch",
            )
            return 0
        if background:
            # The poller never blocks on a slow graph invocation. A later tick
            # can claim a *different* task up to the persisted window WIP cap.
            return recovered + (len(claimed) if self._launch_background_batch(window.id, claimed) else 0)
        try:
            return recovered + self._execute_claimed_batch(window_id=window.id, claimed=claimed)
        finally:
            self._finish_dispatch()

    def _begin_dispatch(self, *, background: bool = False) -> bool:
        """Linearize admissions against stop intent without holding the worker lock."""
        with self._lifecycle_lock:
            if self._stop.is_set() or (self._dispatch_active and not background):
                return False
            self._dispatch_active = True
            return True

    def _finish_dispatch(self) -> None:
        with self._lifecycle_lock:
            self._dispatch_active = bool(self._batch_threads)

    def _launch_background_batch(self, window_id: str, claimed: dict[str, int]) -> bool:
        """Keep graph batches tracked until all their worker claims settle."""
        def run_batch() -> None:
            try:
                self._execute_claimed_batch(window_id=window_id, claimed=claimed)
            except Exception as exc:
                # Durable leases/claim reconciliation remains authoritative if
                # an unforeseen worker-level exception escapes a batch.
                self._last_error = f"parallel_batch_failed:{type(exc).__name__}"
            finally:
                with self._lifecycle_lock:
                    for task_id, epoch in claimed.items():
                        if self._active_task_epochs.get(task_id) == epoch:
                            self._active_task_epochs.pop(task_id, None)
                            self._active_task_ids.discard(task_id)
                    self._batch_threads.pop(threading.current_thread(), None)
                    self._dispatch_active = bool(self._batch_threads)

        thread = threading.Thread(
            target=run_batch, name=f"reverse-agent-batch-{uuid.uuid4().hex[:8]}", daemon=True,
        )
        with self._lifecycle_lock:
            if self._stop.is_set():
                reason = "coordinator_stop_requested_before_dispatch"
            else:
                self._batch_threads[thread] = len(claimed)
                for task_id, epoch in claimed.items():
                    self._active_task_epochs[task_id] = epoch
                    self._active_task_ids.add(task_id)
                try:
                    thread.start()
                except Exception as exc:
                    # An OS/thread-start error must release the just-admitted
                    # claim immediately; do not wait for lease expiry.
                    self._batch_threads.pop(thread, None)
                    for task_id, epoch in claimed.items():
                        if self._active_task_epochs.get(task_id) == epoch:
                            self._active_task_epochs.pop(task_id, None)
                            self._active_task_ids.discard(task_id)
                    self._last_error = f"batch_start_failed:{type(exc).__name__}"
                    reason = "batch_start_failed"
                else:
                    return True
            self._dispatch_active = bool(self._batch_threads)
        self._abandon_claimed_before_dispatch(
            window_id=window_id, claimed=claimed, reason=reason,
        )
        return False

    def _abandon_claimed_before_dispatch(
        self,
        *,
        window_id: str,
        claimed: dict[str, int],
        reason: str,
    ) -> None:
        failures: list[str] = []
        for task_id, epoch in claimed.items():
            try:
                self.control_store.abandon_task_claim(
                    window_id=window_id,
                    task_id=task_id,
                    owner=self.owner,
                    epoch=epoch,
                    reason=reason,
                )
            except TaskStoreError as exc:
                failures.append(f"{task_id}:{type(exc).__name__}")
        self._refresh_claimed_goals(tuple(claimed))
        if failures:
            self._last_error = "coordinator_stop_claim_cleanup_failed"
        self._last_batch = {
            "accepted": False,
            "size": 0,
            "claimed_size": len(claimed),
            "task_ids": sorted(claimed),
            "reasons": [reason],
            "cleanup_failures": failures,
        }

    def _execute_with_claim_renewal(self, window_id: str, task_id: str, epoch: int) -> Any:
        stopped = threading.Event()

        def renew() -> None:
            while not stopped.wait(self.claim_lease_ms / 3000):
                try:
                    if self.control_store.renew_claim(
                        window_id=window_id, task_id=task_id, owner=self.owner,
                        epoch=epoch, lease_ms=self.claim_lease_ms,
                    ):
                        continue
                    _logger.warning("Coordinator claim renewal fenced: task=%s epoch=%s", task_id, epoch)
                except Exception:
                    _logger.exception("Coordinator claim renewal failed: task=%s epoch=%s", task_id, epoch)
                return

        thread = threading.Thread(target=renew, name="coordinator-claim-renewal", daemon=True)
        thread.start()
        try:
            return self._execute_task(task_id)
        finally:
            stopped.set()
            thread.join()

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
            with self._lifecycle_lock:
                self._worker_thread_ids.add(threading.get_ident())
            try:
                stored = self.store.get_task(task_id)
                if stored.status in {"READY_FOR_REVIEW", "FAILED"} and self.control_store.can_complete_host_claim(
                    window_id=window_id, task_id=task_id
                ):
                    # The previous producer already persisted the checker and
                    # terminal Task, but died before completing its original
                    # admission claim. Finalize that exact effect, never dispatch.
                    self.autonomy.check_task_scope(task_id, "validate_task")
                    outcome = TaskExecutionOutcome(task_id=task_id, execution_id=stored.execution_id,
                        success=stored.status == "READY_FOR_REVIEW" and stored.validation_exit_code == 0,
                        validation_command_id=stored.validation_command_id,
                        validation_exit_code=int(stored.validation_exit_code),
                        failure_classification=stored.failure_classification, failure_detail=stored.failure_detail)
                else:
                    outcome = self._execute_with_claim_renewal(window_id, task_id, epoch)
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
            finally:
                # Individual graph workers release their own slots on terminal
                # claim settlement. A slow sibling must not block replacement.
                with self._lifecycle_lock:
                    if self._active_task_epochs.get(task_id) == epoch:
                        self._active_task_epochs.pop(task_id, None)
                        self._active_task_ids.discard(task_id)
                    self._worker_thread_ids.discard(threading.get_ident())

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
        if failed is not None and not self._last_error.startswith("goal_escalation_failed:"):
            # Never mask an escalation error raised while refreshing this batch's goals.
            self._last_error = f"task_unsuccessful:{failed.get('task_id', '')}"
        return completed

    def _reroute_held(self, task_ids: list[str]) -> None:
        if self.quota_rerouter is None:
            return
        goal_ids: set[str] = set()
        for task_id in task_ids:
            try:
                goal_ids.add(self.control_store.goal_id_for_task(task_id))
            except TaskStoreError:
                continue  # a task outside any goal has no plan to re-route against
        for goal_id in sorted(goal_ids):
            try:
                self.quota_rerouter(goal_id)
            except Exception as exc:  # noqa: BLE001 - rerouting must never break the loop
                self._last_error = f"quota_reroute_failed:{type(exc).__name__}"

    def _refresh_claimed_goals(self, task_ids: tuple[str, ...]) -> None:
        if self._last_error.startswith("goal_escalation_failed:"):
            self._last_error = ""  # a fresh refresh reports its own escalation outcome
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
            if self.goal_escalator is not None:
                try:
                    self.goal_escalator(goal_id)
                except Exception as exc:  # noqa: BLE001 - escalation must never break the loop
                    self._last_error = f"goal_escalation_failed:{type(exc).__name__}"

    def status(self) -> dict[str, Any]:
        active = self.control_store.active_window()
        with self._lifecycle_lock:
            thread = self._thread
            alive = thread is not None and thread.is_alive()
            if alive and self._stop.is_set():
                lifecycle = "DRAINING"
            elif alive:
                lifecycle = "RUNNING"
            else:
                lifecycle = "STOPPED"
            accepting_work = lifecycle == "RUNNING"
            inflight_batch = self._dispatch_active
            inflight_task_count = len(self._active_task_ids)
        return {
            "enabled": alive,
            "lifecycle": lifecycle,
            "accepting_work": accepting_work,
            "inflight_batch": inflight_batch,
            "inflight_task_count": inflight_task_count,
            "owner": self.owner,
            "ticks": self._ticks,
            "executions": self._executions,
            "last_error": self._last_error,
            "last_batch": dict(self._last_batch),
            "active_window_id": active.id if active else "",
            # Unfinished work whose window can no longer dispatch; only an explicit rebind moves it.
            "stranded_goals": list(self.control_store.stranded_goals()),
            "workspace_root": self.workspace_root,
        }

    def _run(self) -> None:
        current = threading.current_thread()
        try:
            while not self._stop.is_set():
                try:
                    self.tick(background=True)
                except Exception as exc:
                    self._last_error = f"coordinator_tick_failed:{type(exc).__name__}"
                self._stop.wait(self.poll_interval)
        finally:
            # Stop is draining, not cancellation. Retain thread ownership and
            # all original lease/claim semantics until each live batch finishes.
            while True:
                with self._lifecycle_lock:
                    batches = tuple(self._batch_threads)
                if not batches:
                    break
                for batch in batches:
                    batch.join()
            # start() may have raced an already-running manual tick. Do not
            # report STOPPED while that synchronous execution is unfinished.
            self._manual_tick_idle.wait()
            with self._lifecycle_lock:
                self._dispatch_active = False
                if self._thread is current:
                    self._thread = None
                if self._last_error in {
                    "coordinator_stop_timeout",
                    "coordinator_still_draining",
                    "coordinator_stop_requested_from_worker",
                }:
                    self._last_error = ""

    def _execute_task(self, task_id: str) -> Any:
        if self.task_executor is not None:
            return self.task_executor(task_id)
        task = self.store.get_task(task_id)
        if load_host_validation_contract(task) is not None:
            # Reuse durable TaskStore leases and checkpoints. This branch must
            # precede all model-oriented durable dispatch and binding access.
            self.autonomy.check_task_scope(task_id, "validate_task")
            durable = self._durable_service()
            durable._assert_trusted_identity_for_execute()
            if task.status == "INTERRUPTED":
                with self.store._lock:
                    row = self.store._conn.execute(
                        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                        (task_id,)).fetchone()
                if row is None:
                    raise TaskStoreError("host_validation_resume_run_missing")
                lease = self.store._recover_durable_lease(row["run_id"], self.owner,
                    expiry_ms=durable.expiry_ms, require_interrupted=True)
            else:
                lease = durable._acquire_or_find_lease(task_id, self.owner, "", self.workspace_root)
            from .durable_execution import _HeartbeatContext
            heartbeat = _HeartbeatContext(store=self.store, run_id=lease.run_id, owner=lease.owner,
                epoch=lease.epoch, expiry_ms=durable.expiry_ms,
                heartbeat_window_ms=durable.heartbeat_window_ms)
            outcome = heartbeat.heartbeat_during(lambda: TaskExecutionService(
                store=self.store, router=self.router).execute_host_validation(task_id, lease=lease))
            # An unfinished producer retains its original expiring lease so
            # reconciliation can observe the abandoned Run after an exception
            # or abrupt exit. Only a durable terminal result releases ownership.
            if self.store.get_task(task_id).status in {"READY_FOR_REVIEW", "FAILED", "BLOCKED", "CANCELLED"}:
                self.store._release_durable_lease(lease.run_id, lease.owner, lease.epoch)
            return outcome
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
            window = self.control_store.active_window()
            if window is None or not self.autonomy.authorize(window_id=window.id,
                    operation="resume_task", repository=task.repository, subject_id=task_id,
                    input_payload={"task_id": task_id, "status": task.status}):
                raise TaskStoreError("quota_resume_authority_revoked")
            self.control_store.check_strict_task_admission(window.id, task_id)
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

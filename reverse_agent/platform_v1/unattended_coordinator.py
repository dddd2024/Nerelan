"""Crash-resumable coordinator for explicitly activated autonomous windows."""

from __future__ import annotations

from dataclasses import asdict
import logging
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time
import uuid
from typing import Any, Callable, Mapping

from .autonomy import AutonomyService
from .control_store import PlatformControlStore
from .durable_execution import DurableExecutionService, DurableResumeError
from .model_availability import HOST_VERSION_CHANGED, OWNER_WINDOW_POOL_MISROUTE
from .run_store import ORPHANED_PREPARATION, TaskStore, TaskStoreError, _utc_now, pre_dispatch_interruption
from .task_execution import TaskExecutionOutcome, TaskExecutionService
from .task_runtime import ExecutorRouter, load_host_validation_contract, task_operation
from reverse_agent.architecture.contracts import (
    WorkerAssignment,
    WorkerExecutionResult,
)
from reverse_agent.workflows.team_graph import build_team_graph


_logger = logging.getLogger(__name__)


TaskExecutor = Callable[[str], Any]

# Durable resume refusals that mean only the host's code identity changed under
# the run (a redeploy), never that the run itself is untrustworthy (#1515).
_HOST_VERSION_REFUSALS = ("authority_sha_mismatch:", "planning_sha_mismatch:")
# A durable resume refusal for a run interrupted before PRE_PLANNER: nothing was
# dispatched, so there is nothing to reconstruct (2026-11-17).
_PRE_DISPATCH_REFUSAL = "pre_pre_planner_no_reconstruction_path:"
# Host faults, never evidence about the account or model that was routed.
_HOST_CLOSED_CLASSES = frozenset({HOST_VERSION_CHANGED, ORPHANED_PREPARATION, OWNER_WINDOW_POOL_MISROUTE})

# Upper bound on any idle wait: a new goal, claim or receipt must never wait
# longer than this for the next poll, even if a quota window resets in hours.
IDLE_WAIT_CAP_SECONDS = 60.0
# An unchanged stuck goal is re-examined at most this often by the reconcile sweep (#1473).
SWEEP_REPEAT_SECONDS = 900.0
# Only delegate a long idle wait to Magpie's own `quota wait`; below this it is
# cheaper to just poll. The upper bound keeps one delegated wait from outliving
# a stop request by more than a minute (cancellation polls every 0.2 s).
QUOTA_WAIT_MIN_SECONDS = 60.0
QUOTA_WAIT_MAX_SECONDS = 3600.0
REEVALUATE_POLL_SECONDS = 5.0


class _AnySet:
    """``is_set`` over several events, for a wait that any of them may cancel."""

    def __init__(self, *events: threading.Event) -> None:
        self._events = events

    def is_set(self) -> bool:
        return any(event.is_set() for event in self._events)



def _failure_detail(exc: BaseException) -> str:
    """Resume refusals are host-generated codes worth keeping; other text stays out (#1322)."""
    if isinstance(exc, DurableResumeError) and str(exc):
        return f"{type(exc).__name__}:{str(exc)[:300]}"
    return type(exc).__name__


class UnattendedCoordinator:
    """Runs queued Goal tasks without duplicating or bypassing policy checks.

    The loop is inert until both the trusted host enables it and an owner has
    activated a bounded window. Atomic claims live in SQLite, so a restarted
    coordinator can safely continue after durable-run reconciliation.
    """

    _recovering: bool = False
    _skip_sweep_thread: int | None = None

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
        reconcile_interval: float = 60.0,
        claim_lease_ms: int = 15 * 60 * 1000,
        owner: str | None = None,
        goal_escalator: Any | None = None,
        quota_preparer: Any | None = None,
        quota_rerouter: Any | None = None,
        account_feedback: Any | None = None,
        idle_wait_hint: Any | None = None,
        quota_wait_target: str | None = None,
        landing_loop=None, publication=None, goals=None,
    ) -> None:
        # goal_id -> escalations; hands FAILED agent_team tasks to stronger agents.
        self.landing_loop = landing_loop
        self.publication = publication
        self.goals = goals
        self.quota_preparer = quota_preparer
        # goal_id -> moves; quota-held tasks to an equal-or-higher-tier model (#1313 D).
        self.quota_rerouter = quota_rerouter
        # (task, success) -> None; per-account feedback for the multi-account brain
        # (cooldown + measured reliability). Optional and best-effort.
        self.account_feedback = account_feedback
        # () -> seconds|None; how long until quota/account capacity plausibly returns.
        # Only consulted on an idle tick, and always bounded by IDLE_WAIT_CAP_SECONDS.
        self.idle_wait_hint = idle_wait_hint
        # Optional provider/account to hand a long idle wait to Magpie's own
        # blocking `quota wait`. None (the default) keeps local polling.
        self.quota_wait_target = quota_wait_target
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
        self._attempt_clock = time.monotonic
        self.poll_interval = max(0.1, poll_interval)
        # Startup only sees leases that already expired; a run orphaned by a host
        # restart while its lease was still live expires later and must be found.
        self.reconcile_interval = max(self.poll_interval, reconcile_interval)
        self.claim_lease_ms = max(1, claim_lease_ms)
        self.owner = owner or f"coordinator-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._stop = threading.Event()
        self._reevaluate = threading.Event()  # an account's quota reset: look at held work now
        self._thread: threading.Thread | None = None
        self._lifecycle_lock = threading.RLock()
        self._recovering = False
        self._skip_sweep_thread: int | None = None
        self._dispatch_active = False
        # The live poller may refill idle slots while older batches are running.
        # Direct tick() remains synchronous for deterministic host/test callers.
        self._batch_threads: dict[threading.Thread, int] = {}
        self._active_task_ids: set[str] = set()
        # A later retry can overlap an older graph batch that still drains
        # another task. Epoch ownership keeps old finally blocks from erasing
        # the retry's active marker.
        self._active_task_epochs: dict[str, int] = {}
        # The (window, epoch) of the claim the current worker thread executes
        # under, so a state change it makes can be fenced against that claim.
        self._claim_local = threading.local()
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
            # Refuse to activate dispatch while persisted durable-run state
            # cannot be reconciled. A paused host may expose read-only state,
            # but the coordinator must never poll with unknown recovery truth.
            # Hold the stop intent until reconciliation succeeds, so a failed
            # startup cannot be bypassed by a manual or background tick (#1347).
            # Defer the potentially slow escalation sweep to the coordinator thread
            # so host readiness and client UI startup are not blocked (#1622).
            self._stop.set()
            self._recovering = False
            self._skip_sweep_thread = threading.get_ident()
            try:
                self.reconcile(fail_closed_on_durable=True)
            finally:
                self._skip_sweep_thread = None
            self._recovering = self.goal_escalator is not None
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

    def reconcile(self, *, fail_closed_on_durable: bool = False) -> tuple[str, ...]:
        durable = self._durable_service()
        reconciled: list[str] = []
        with self._lifecycle_lock:
            live = frozenset(self._active_task_ids)
        try:
            # Runs this process is still executing are not orphans, even if the
            # machine slept past their lease (#1321).
            result = durable.reconcile_expired_runs(live_owner=self.owner, live_task_ids=live)
        except Exception as exc:
            self._last_error = f"reconcile_failed:{type(exc).__name__}"
            if fail_closed_on_durable:
                raise RuntimeError("coordinator_startup_reconciliation_failed") from exc
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
        try:
            # Restart-stranded preparations become retryable host faults (2026-11-17).
            reconciled.extend(f"orphaned_preparation:{task_id}"
                              for task_id in self.control_store.recover_orphaned_preparations())
        except Exception as exc:  # noqa: BLE001 - must never break reconciliation
            self._last_error = f"orphaned_preparation_recovery_failed:{type(exc).__name__}"
        if self._skip_sweep_thread != threading.get_ident():
            stop_event = self._stop if threading.current_thread() is self._thread else None
            self._sweep_escalations(stop_event=stop_event)
        return tuple(reconciled)

    def _next_sweep_delay(self, goal_id: str) -> float:
        """Seconds before re-examining an unchanged stuck goal (#1652)."""
        provider = getattr(self, "goals", None)
        if provider is None or not callable(getattr(provider, "next_backoff_delay", None)):
            provider = getattr(self.goal_escalator, "__self__", None)
        getter = getattr(provider, "next_backoff_delay", None)
        if not callable(getter):
            return SWEEP_REPEAT_SECONDS
        try:
            delay = getter(goal_id)
        except Exception:  # noqa: BLE001 - scheduling hint must never break reconciliation
            return SWEEP_REPEAT_SECONDS
        if type(delay) not in (int, float) or not math.isfinite(delay):
            return SWEEP_REPEAT_SECONDS
        return min(SWEEP_REPEAT_SECONDS, max(0.0, float(delay)))

    def _has_due_escalation_sweep(self) -> bool:
        seen = getattr(self, "_swept", None)
        if not seen:
            return False
        now = time.monotonic()
        return any(now >= next_due for _, next_due in seen.values())

    def _sweep_escalations(self, *, stop_event: threading.Event | None = None) -> None:
        """Re-examine the active window's goals with FAILED or BLOCKED tasks (#1473).

        Escalation otherwise runs only after a task this process just executed, so
        a task the host itself broke (restart during preparation, an interrupted
        run refused on resume) would wait forever once the host came back.
        """
        if self.goal_escalator is None or (stop_event is not None and stop_event.is_set()):
            return
        try:
            window = self.control_store.active_window()
            if window is None:
                return
            with self.control_store._lock:
                rows = self.control_store._conn.execute(
                    "SELECT g.id AS goal_id, t.id AS task_id, t.updated_at FROM platform_goals g "
                    "JOIN platform_goal_task_links l ON l.goal_id = g.id AND l.goal_revision = g.revision "
                    "JOIN tasks t ON t.id = l.task_id "
                    "WHERE g.window_id = ? AND g.status <> 'SUPERSEDED' "
                    "AND t.status IN ('FAILED', 'BLOCKED') ORDER BY g.id",
                    (window.id,)).fetchall()
        except Exception as exc:  # noqa: BLE001 - the sweep must never break reconciliation
            self._last_error = f"escalation_sweep_failed:{type(exc).__name__}"
            return
        # A goal is re-examined at once when one of its stuck tasks is new or changed,
        # when its earliest step backoff expires, and otherwise only every
        # SWEEP_REPEAT_SECONDS (an unroutable task would else log a selection failure
        # every minute).
        seen = getattr(self, "_swept", None)
        if seen is None:
            seen = self._swept = {}
        now = time.monotonic()
        due: dict[str, list[tuple[str, str]]] = {}
        for row in rows:
            due.setdefault(row["goal_id"], []).append((row["task_id"], row["updated_at"]))
        for goal_id, tasks in due.items():
            if stop_event is not None and stop_event.is_set():
                break
            last = seen.get(goal_id)
            if last is not None and last[0] == tasks and now < last[1]:
                continue
            seen[goal_id] = (tasks, now + SWEEP_REPEAT_SECONDS)
            try:
                self.goal_escalator(goal_id)
            except Exception as exc:  # noqa: BLE001 - one goal must not stop the others
                self._last_error = f"goal_escalation_failed:{type(exc).__name__}"
            else:
                seen[goal_id] = (tasks, now + self._next_sweep_delay(goal_id))
        for goal_id in set(seen) - set(due):
            seen.pop(goal_id, None)

    def tick(self, *, background: bool = False) -> int:
        # External synchronous ticks must not race the live poller: they are
        # a separate deterministic invocation mode, not an extra worker slot.
        with self._lifecycle_lock:
            if background:
                if self._manual_tick_active or self._recovering:
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

    def _can_resume_parked_review(self, goal: Any, task: Any, accepted: Mapping[str, Any],
                                  landing: Mapping[str, Any]) -> bool:
        """True when the verdict of this landing's own head is retained but was never posted.

        BLOCKED without a reason is a review that failed and later succeeded. WAITING is a
        publish that broke (a GitHub error) between recording the landing and its comment.
        """
        if (landing.get("head_sha") != accepted.get("commit")
                or not (landing.get("phase") == "WAITING"
                        or landing.get("phase") == "BLOCKED" and not landing.get("parking_reason"))
                or self.control_store.landing_operation(landing["identity"], "review_comment") is not None):
            return False
        review = self._planned_review(goal, task)
        return review is not None and self._has_retained_review(review)

    def _planned_review(self, goal: Any, task: Any) -> Any:
        """The current attempt of the one planned review of ``task``, or None."""
        links = {row["plan_task_id"]: row for row in self.control_store.list_goal_tasks(goal.id)
                 if int(row["goal_revision"]) == goal.revision}
        source = next((key for key, row in links.items() if row["task_id"] == task.id), None)
        reviews = [raw for raw in goal.tasks if raw.get("kind") == "review"
                   and raw.get("artifact_input") == {"plan_task_id": source}] if source else []
        link = links.get(reviews[0]["id"]) if len(reviews) == 1 else None
        try:
            return self.store.get_task(link["task_id"]) if link else None
        except (TaskStoreError, KeyError):
            return None

    @staticmethod
    def _has_retained_review(review: Any) -> bool:
        from . import model_review
        return any(row.get("category") == model_review.CATEGORY and row.get("label") == review.execution_id
                   for row in review.evidence_refs)

    def _republishes_rejected_head(self, goal: Any, task: Any, accepted: Mapping[str, Any],
                                   landing: Mapping[str, Any]) -> bool:
        """True when ``task`` is an accepted repair of the head this landing had rejected.

        Publishing waits for the repair's own review to ACCEPT, so nothing is pushed while
        a reviewer is missing and a second REJECT is repaired before anything new appears.
        The rejected head must have its confirmed REJECT comment, the repair evidence must
        lead back to it, and the PR must still be open, Draft and at that head (or at this
        one, when a push was interrupted): a PR somebody closed or moved is left alone. The
        old landing's own tick parks an interrupted push as ``landing_head_race``.
        """
        from . import artifact_handoff as artifacts
        reason = str(landing.get("parking_reason") or "")
        if (landing.get("head_sha") == accepted.get("commit")
                or not (landing.get("phase") == "WAITING"
                        or landing.get("phase") == "BLOCKED" and (not reason or "reject" in reason or reason == "landing_head_race"))):
            return False
        comment = self.control_store.landing_operation(landing["identity"], "review_comment")
        if comment is None or comment["status"] != "SUCCEEDED":
            return False
        review = self._planned_review(goal, task)
        if review is None or review.status != "READY_FOR_REVIEW" or not self._has_retained_review(review):
            return False
        # A repair may itself have been rejected and repaired before it was ever published.
        producer, seen = task, set()
        while producer.id not in seen:
            seen.add(producer.id)
            repair = artifacts._load_evidence(producer, "ReviewRepair", producer.execution_id)
            source = (repair or {}).get("producer") or {}
            if not source.get("commit"):
                return False
            if source["commit"] == landing.get("head_sha"):
                observed = self.landing_loop.github.observe_pr(dict(landing))
                return (observed.get("state") == "OPEN" and observed.get("draft") is True
                        and (observed.get("head_sha") == accepted["commit"]
                             or observed.get("head_sha") == landing["head_sha"] and reason != "landing_head_race"))
            try:
                producer = self.store.get_task(source["task_id"])
            except (TaskStoreError, KeyError):
                return False
        return False

    def _advance_landing(self, window):
        if self.landing_loop is None:
            return
        recovery = self.control_store.landing_recovery_identity(window)
        if recovery:
            self.landing_loop.tick(recovery, window_id=window.id)
        # Bounded scan over local intent; GitHub truth is read by each tick.
        if window is not None and self.publication is not None and self.goals is not None:
            from . import artifact_handoff as artifacts
            from .github_adapter import GitHubAdapterError
            for task_id in self.control_store.ready_window_tasks(window.id):
                task = self.store.get_task(task_id)
                if task.status != "READY_FOR_REVIEW":
                    continue
                accepted = artifacts._load_evidence(task, artifacts.ACCEPTED_CATEGORY, task.execution_id)
                if not accepted:
                    continue
                goal = self.control_store.get_goal(self.control_store.goal_id_for_task(task.id))
                landing = self.control_store.landing_progress(goal.id)
                if goal.window_id != window.id:
                    continue
                try:
                    if (landing is not None and not self._can_resume_parked_review(goal, task, accepted, landing)
                            and not self._republishes_rejected_head(goal, task, accepted, landing)):
                        continue
                    self.landing_loop.publish_and_review(task.id, window_id=window.id,
                        publication=self.publication, goals=self.goals,
                        execution=self._durable_service(), workspace_root=self.workspace_root)
                except TaskStoreError as exc:
                    if str(exc) == "goal_source_issue_closed":
                        # A fresh check can supersede this goal after the scan.
                        continue
                    self._last_error = str(exc)
                    continue  # one goal that cannot publish never holds the others back
                except (GitHubAdapterError, OSError, ValueError, subprocess.SubprocessError) as exc:
                    self._last_error = f"landing_publish_failed:{type(exc).__name__}"
                    continue
                break
        rows = self.control_store._conn.execute(
            "SELECT identity,goal_id FROM platform_landing_state WHERE phase NOT IN "
            "('BLOCKED','COMPLETE','SUPERSEDED') ORDER BY next_attempt_ms LIMIT 10").fetchall()
        for row in rows:
            if row["identity"] == recovery:
                continue
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
        with self._lifecycle_lock:
            # Bound admission *before* claiming: old graph batches continue
            # running and still occupy slots even if newer tasks arrive.
            if self._dispatch_active and not background:
                return 0
            running_slots = len(self._active_task_ids) if background else 0
            free_slots = max(0, window.max_concurrent_tasks - running_slots)
        if free_slots == 0:
            return 0
        if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") == "1" and self.goals is not None:
            try:
                self.goals.reconsider_initial_models(window.id, autonomy=self.autonomy)
            except Exception as exc:
                self._last_error = f"initial_model_recovery_failed:{type(exc).__name__}"
        claimed: dict[str, int] = {}
        held: list[str] = []
        recovered = 0
        retained_after_denial = None
        # A claimed task can still be QUEUED while its executor is running.
        # Scan past already-claimed rows instead of starving later candidates.
        for task_id in self.control_store.runnable_tasks(
            window.id, limit=500, respect_attempt_limits=True, respect_reservation_limits=True
        ):
            if len(claimed) >= free_slots:
                break
            if self._stop.is_set():
                break
            if retained_after_denial is not None and task_id not in retained_after_denial:
                continue
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
            if self.goals is not None:
                goal_id = self.control_store.goal_id_for_task(task_id)
                if goal_id and self.goals.stop_if_source_closed(goal_id):
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
                feedback_identity = self.quota_preparer(task) if self.quota_preparer is not None else None
                epoch, _ = self.control_store.claim_task(
                    window_id=window.id,
                    task_id=task_id,
                    owner=self.owner,
                    lease_ms=self.claim_lease_ms,
                    **({"feedback_identity": feedback_identity} if feedback_identity is not None else {}),
                )
            except TaskStoreError as exc:
                if str(exc) == "window_wip_limit_reached":
                    break
                if str(exc) in {"window_token_budget_exhausted", "window_cost_budget_exhausted"}:
                    # Avoid preparing more unfunded work this tick. Later
                    # tasks can still use a reservation they already hold.
                    try:
                        retained_after_denial = self.control_store.active_reservation_task_ids(window.id)
                    except sqlite3.Error:
                        self._last_error = "reservation_candidates_unavailable"
                        _logger.warning("reservation_candidates_unavailable window=%s", window.id)
                        break  # Dispatch the batch already claimed before the read fault.
                    continue
                if str(exc) in {"window_task_budget_exhausted", "window_retry_budget_exhausted"}:
                    # The other attempt class still has its own allowance.
                    continue
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
        self._claim_local.claim = (window_id, task_id, epoch)
        try:
            return self._execute_task(task_id)
        finally:
            self._claim_local.claim = None
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
                attempt_elapsed = None
                stored = self.store.get_task(task_id)
                if stored.status in {"READY_FOR_REVIEW", "FAILED"} and self.control_store.can_complete_host_claim(
                    window_id=window_id, task_id=task_id
                ):
                    # Host-check claims were scoped by the retired delegated
                    # policy authority (#1575); they cannot be finalized now.
                    raise TaskStoreError("delegated_policy_authority_unavailable")
                else:
                    # Resume can reuse checkpoints or only validate, without
                    # executing the routed account. Only time fresh attempts.
                    collect_timing = (stored.status == "QUEUED"
                                      and os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") == "1")
                    started = self._attempt_timestamp() if collect_timing else None
                    outcome = self._execute_with_claim_renewal(window_id, task_id, epoch)
                    if collect_timing:
                        finished = self._attempt_timestamp()
                        if (started is not None and finished is not None and finished >= started
                                and math.isfinite(finished - started)):
                            attempt_elapsed = finished - started
                        else:
                            self._last_error = "attempt_timing_unavailable"
                            _logger.warning("attempt_timing_unavailable task=%s epoch=%s", task_id, epoch)
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
                    **({"attempt_elapsed_seconds": attempt_elapsed} if attempt_elapsed is not None else {}),
                )
                if final.failure_classification not in _HOST_CLOSED_CLASSES:
                    # Pre-dispatch and host recovery failures supply no account evidence.
                    self._report_account_feedback(final, success=success)
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
                detail = _failure_detail(exc)
                try:
                    self.control_store.abandon_task_claim(
                        window_id=window_id,
                        task_id=task_id,
                        owner=self.owner,
                        epoch=epoch,
                        reason=f"execution_failed:{task_id}:{detail}",
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
                    failure_detail=detail,
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

    def _attempt_timestamp(self) -> float | None:
        try:
            value = self._attempt_clock()
            return float(value) if type(value) in (int, float) and math.isfinite(value) else None
        except Exception:  # noqa: BLE001 - optional timing never prevents execution
            return None

    def _report_account_feedback(self, task: Any, *, success: bool) -> None:
        """Hand one finished attempt to the multi-account brain (best-effort).

        Called once per executed task, after its claim is settled. The callback
        resolves the account and decides what to record; any failure here must
        never disturb the loop, because this is learning, not dispatch.
        """
        if self.account_feedback is None:
            return
        try:
            self.account_feedback(task, success)
        except Exception as exc:  # noqa: BLE001 - feedback must never break the loop
            self._last_error = f"account_feedback_failed:{type(exc).__name__}"

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
            recovering = alive and self._recovering and not self._stop.is_set()
            if alive and self._stop.is_set():
                lifecycle = "DRAINING"
            elif recovering:
                lifecycle = "RECOVERING"
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
            "recovering": recovering,
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

    def idle_wait(self, dispatched: int) -> float:
        """How long to wait before the next poll.

        When the pool knows capacity is gone (every account cooling down or a
        quota window resetting), polling every second for hours only burns CPU
        and re-observes the same exhausted accounts. An idle tick may therefore
        sleep until the hinted moment — never past ``IDLE_WAIT_CAP_SECONDS`` and
        never when a dispatch just happened or work is already in flight.
        """
        if dispatched or self.idle_wait_hint is None:
            return self.poll_interval
        with self._lifecycle_lock:
            if self._active_task_ids or self._dispatch_active:
                return self.poll_interval
        try:
            hint = self.idle_wait_hint()
        except Exception:  # noqa: BLE001 - a hint must never stall the loop
            return self.poll_interval
        if not isinstance(hint, (int, float)) or hint <= 0:
            return self.poll_interval
        return max(self.poll_interval, min(float(hint), IDLE_WAIT_CAP_SECONDS))

    def request_reevaluation(self) -> None:
        """End the idle wait and re-examine stuck goals: an account's quota reset was seen."""
        self._reevaluate.set()

    def _idle(self, poll_at: float) -> None:
        """Sleep until ``poll_at``, stop, or a requested re-evaluation (seen within 5 s)."""
        while not self._stop.is_set() and not self._reevaluate.is_set():
            remaining = poll_at - time.monotonic()
            if remaining <= 0:
                return
            self._stop.wait(min(remaining, REEVALUATE_POLL_SECONDS))

    def quota_wait(self, wait_seconds: float) -> bool:
        """Delegate a long idle wait to Magpie; ``True`` when capacity returned.

        Opt-in via ``quota_wait_target``; a no-op otherwise. The wait is bounded
        and cancellable by ``self._stop``, so shutdown is never delayed by a
        quota window — the reason this can live in the loop at all.
        """
        if self._stop.is_set() or not self.quota_wait_target or wait_seconds < QUOTA_WAIT_MIN_SECONDS:
            return False
        from .magpie_wait import wait_for_allowance

        budget = int(min(wait_seconds, QUOTA_WAIT_MAX_SECONDS))
        result = wait_for_allowance(self.quota_wait_target, timeout=f"{budget}s",
                                    cancel=_AnySet(self._stop, self._reevaluate))
        if result.get("available"):
            return True
        if result.get("reason") not in (None, "timeout", "allowance_available") and not (
                result.get("reason") == "cancelled" and self._reevaluate.is_set()):
            self._last_error = f"quota_wait_{result['reason']}"
        return False

    def _run(self) -> None:
        current = threading.current_thread()
        try:
            if self._recovering and not self._stop.is_set():
                try:
                    self._sweep_escalations(stop_event=self._stop)
                finally:
                    with self._lifecycle_lock:
                        self._recovering = False
            reconciled_at = time.monotonic()
            while not self._stop.is_set():
                if self._reevaluate.is_set():
                    self._reevaluate.clear()
                    getattr(self, "_swept", {}).clear()  # every stuck goal is due again
                    try:
                        self._sweep_escalations(stop_event=self._stop)
                    except Exception as exc:  # noqa: BLE001 - a sweep fault must not stop dispatch
                        self._last_error = f"escalation_sweep_failed:{type(exc).__name__}"
                if time.monotonic() - reconciled_at >= self.reconcile_interval:
                    reconciled_at = time.monotonic()
                    try:
                        self.reconcile()
                    except Exception as exc:  # a reconcile fault must not stop dispatch
                        self._last_error = f"reconcile_failed:{type(exc).__name__}"
                elif self._has_due_escalation_sweep():
                    try:
                        self._sweep_escalations(stop_event=self._stop)
                    except Exception as exc:  # noqa: BLE001 - a sweep fault must not stop dispatch
                        self._last_error = f"escalation_sweep_failed:{type(exc).__name__}"
                dispatched = 0
                try:
                    dispatched = self.tick(background=True)
                except Exception as exc:
                    self._last_error = f"coordinator_tick_failed:{type(exc).__name__}"
                wait = self.idle_wait(dispatched)
                poll_at = time.monotonic() + wait
                if self.quota_wait(wait):
                    continue  # allowance is back: poll now instead of sleeping
                # Delegation and local polling share the same idle interval.
                self._idle(poll_at)
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
                self._recovering = False
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
            # Approved host checks needed the retired delegated policy
            # authority (#1575). This precedes all model-oriented dispatch.
            raise TaskStoreError("delegated_policy_authority_unavailable")
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
                return self._resume_interrupted_durable(
                    task_id, lambda tid: durable.resume_single(task_id=tid, lease_owner=self.owner))
            return self._resume_interrupted_durable(
                task_id, lambda tid: durable.resume_sequential_team(task_id=tid, lease_owner=self.owner))
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

    def _resume_interrupted_durable(self, task_id: str, resume: Callable[[str], Any]) -> Any:
        """Resume an INTERRUPTED durable run, recovering a redeploy strand (#1515).

        A redeploy changes the host's code identity, so the authority/planning SHA
        recorded when the run started no longer matches and the durable resume
        refuses. That refusal is correct (a run is never resumed under new code),
        but it must close the attempt instead of stranding it: the task becomes
        FAILED ``host_version_changed``, a host fault that the normal retry path
        recovers without spending ``max_retries``.

        A run a restart stopped before PRE_PLANNER has nothing to reconstruct and
        resume refuses it (``pre_pre_planner_no_reconstruction_path``). While it is
        still a pre-dispatch interruption (no prepared worktree, no accepted
        checkpoint, no external-operation row) it is closed the same fenced way as
        FAILED ``orphaned_preparation`` (2026-11-17). Other refusals still raise.
        """
        observed = self._latest_durable_run_identity(task_id)
        try:
            return resume(task_id)
        except DurableResumeError as exc:
            text = str(exc)
            if text.startswith(_HOST_VERSION_REFUSALS):
                classification = HOST_VERSION_CHANGED
            elif text.startswith(_PRE_DISPATCH_REFUSAL) and self._still_pre_dispatch(task_id):
                classification = ORPHANED_PREPARATION
            else:
                raise
            self._fail_redeploy_stranded_task(task_id, detail=text[:220], observed=observed,
                                              classification=classification)
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

    def _latest_durable_run_identity(self, task_id: str) -> tuple[str, str, int] | None:
        with self.store._lock:
            row = self.store._conn.execute(
                "SELECT run_id, lease_owner, lease_epoch FROM durable_runs WHERE task_id = ? "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1", (task_id,)).fetchone()
        return None if row is None else (row["run_id"], row["lease_owner"], int(row["lease_epoch"]))

    def _still_pre_dispatch(self, task_id: str) -> bool:
        with self.store._lock:
            return pre_dispatch_interruption(self.store._conn, self.store.get_task(task_id), own_claim=True)

    def _fail_redeploy_stranded_task(self, task_id: str, *, detail: str,
                                     observed: tuple[str, str, int] | None,
                                     classification: str = HOST_VERSION_CHANGED) -> None:
        """Close a redeploy-stranded INTERRUPTED task as FAILED ``host_version_changed``
        (or, for a pre-dispatch interruption, ``orphaned_preparation``).

        One ``BEGIN IMMEDIATE`` transaction re-validates every identity the close
        depends on and then writes status, failure fields and the event together:
        this coordinator's claim (owner, epoch, window) is still ACTIVE and live,
        the task is still INTERRUPTED, and the durable run is the one observed
        before the resume with the same lease owner/epoch and no live lease. A
        successor that resumed, claimed or re-leased the task in between fails a
        check and nothing is written; the stale handler raises instead, so the
        worker abandons only its own claim.
        """
        prefix = "host_version" if classification == HOST_VERSION_CHANGED else classification
        claim = getattr(self._claim_local, "claim", None)
        if claim is None or claim[1] != task_id:
            raise TaskStoreError(f"{prefix}_close_unfenced:{task_id}")
        window_id, _, epoch = claim
        store = self.store
        with store._lock:
            conn = store._conn
            if conn.in_transaction:
                raise TaskStoreError(f"{prefix}_close_nested_transaction:{task_id}")
            conn.execute("BEGIN IMMEDIATE")
            try:
                reason = self._redeploy_close_refusal(conn, task_id, window_id=window_id, epoch=epoch,
                                                      observed=observed)
                if not reason and classification == ORPHANED_PREPARATION and not pre_dispatch_interruption(
                        conn, store.get_task(task_id), own_claim=True):
                    # Re-checked inside the write: a prepared worktree, an accepted
                    # checkpoint or any external-operation row is never closed here.
                    reason = "not_pre_dispatch"
                if reason:
                    raise TaskStoreError(f"{prefix}_close_fenced:{task_id}:{reason}")
                now = _utc_now()
                changed = conn.execute(
                    "UPDATE tasks SET status = 'FAILED', failure_classification = ?, failure_detail = ?, "
                    "failure_at = ?, updated_at = ? WHERE id = ? AND status = 'INTERRUPTED'",
                    (classification, detail, now, now, task_id)).rowcount
                if changed != 1:
                    raise TaskStoreError(f"{prefix}_close_fenced:{task_id}:task_not_interrupted")
                store._append_event(
                    task_id=task_id, event_type="EXECUTOR_FINISHED", title="Executor failed",
                    description=f"failure_classification={classification}",
                    metadata={"failure_classification": classification, "detail": detail,
                              "claim_epoch": epoch, "run_id": observed[0] if observed else ""})
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    def _redeploy_close_refusal(self, conn: Any, task_id: str, *, window_id: str, epoch: int,
                                observed: tuple[str, str, int] | None) -> str:
        now_ms = int(time.time() * 1000)
        claim = conn.execute(
            "SELECT window_id, owner, epoch, status, expires_at_ms FROM platform_coordinator_claims "
            "WHERE task_id = ?", (task_id,)).fetchone()
        if (claim is None or claim["status"] != "ACTIVE" or claim["owner"] != self.owner
                or int(claim["epoch"]) != epoch or claim["window_id"] != window_id
                or int(claim["expires_at_ms"]) <= now_ms):
            return "claim_not_current"
        task = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if task is None or task["status"] != "INTERRUPTED":
            return "task_not_interrupted"
        run = conn.execute(
            "SELECT run_id, lease_owner, lease_epoch, lease_expiry_ms FROM durable_runs WHERE task_id = ? "
            "ORDER BY created_at DESC, rowid DESC LIMIT 1", (task_id,)).fetchone()
        if observed is None or run is None or (run["run_id"], run["lease_owner"], int(run["lease_epoch"])) != observed:
            return "durable_run_changed"
        if run["lease_owner"] and int(run["lease_expiry_ms"]) > now_ms:
            return "durable_lease_live"
        return ""

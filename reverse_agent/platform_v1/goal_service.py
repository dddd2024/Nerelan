"""Persistent Goal -> Spec -> Plan -> Tasks workflow for Platform V2.

The artifact layout follows GitHub Spec Kit's separation of specification,
plan and executable tasks while retaining the existing TaskStore as execution
truth.  Planning is deterministic and editable; it makes no model call.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from collections import OrderedDict
from copy import deepcopy
import threading
import os
import re
import json
import time
import math
import subprocess
import hashlib
from pathlib import Path
import shutil

from .model_availability import transient_overload
from typing import Any, Mapping, Sequence

from .control_store import GoalRecord, PlatformControlStore, reject_sensitive_keys
from .repository_workspace import (
    RepositoryWorkspaceError,
    resolve_repository_workspace,
)
from .run_store import TaskStore, TaskStoreError
from .functional_validation import (
    freeze_contract, functional_evidence, load_contract, normalize_checks, repository_base,
)
from .quota_guard import LIMIT_HIT
from .model_router import task_traits
from .routing_inputs import requirements
from .required_review_artifact import normalize_required_artifacts, freeze_required_artifacts, load_required_artifacts
from .run_read_model import publication_projection

_INITIAL_WAIT = "initial_resource_wait"
INITIAL_MODEL_RECHECK_SECONDS = 60.0
GOAL_FORECAST_TTL_SECONDS = 10.0
_GOAL_FORECAST_CACHE_LIMIT = 128


def _initial_resource_wait(decision: Mapping[str, Any]) -> dict[str, Any] | None:
    """Host-owned opt-in marker, never a general retry of model refusal/failure."""
    if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") != "1":
        return None
    if decision.get("reason") not in {"no_runnable_model", "pinned_model_unavailable", "review_not_independent"}:
        return None
    if decision.get("temporary_resource_blocked") is not True:
        return None
    now = time.time()
    due = decision.get("retry_at")
    if type(due) not in (int, float) or not math.isfinite(due) or due <= now:
        due = now + INITIAL_MODEL_RECHECK_SECONDS
    return {"version": 1, "kind": "resource",
            "retry_at": max(now + 1, min(due, now + INITIAL_MODEL_RECHECK_SECONDS))}
from .artifact_handoff import (
    ACCEPTED_CATEGORY, _load_evidence, freeze_handoff_contract, load_handoff_contract, normalize_input,
    publication_blocker, published_plan_tasks, validate_plan_inputs,
)
from .task_runtime import HOST_VALIDATION_CONTRACT, ExecutorRuntimeError, load_host_validation_contract


def _resolve_orchestration_mode(payload: Mapping[str, Any]) -> str:
    """Goal-level orchestration mode with opt-in, evidence-gated self-evolution.

    The planner's task_count estimate is not known at goal creation, so this can
    only ever feed the *measured* break-even branch of
    :func:`orchestration_selector.select_orchestration`. Until real per-mode
    evidence exists the recommendation falls back to the default ladder, which we
    deliberately ignore here so behaviour is byte-for-byte identical to the legacy
    ``"sequential_team"`` default. An explicit user choice always wins (pin).

    Every step is guarded: with the master switch off, or if the brain raises,
    this returns the unchanged legacy default. It never blocks goal creation.
    """
    explicit = payload.get("orchestration_mode") if "orchestration_mode" in payload else None
    if explicit:
        return str(explicit)  # explicit Owner choice wins
    if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") != "1":
        return "sequential_team"
    try:
        from .multi_account.dispatch import recommend_orchestration_mode
        recommendation = recommend_orchestration_mode({})  # no planner estimate yet
        mode = recommendation.get("mode")
        reason = recommendation.get("reason", "")
        # Only override the legacy default when driven by *measured* evidence
        # (E1). The default-ladder branch is ignored so nothing changes until
        # the break-even ledger actually has data.
        if mode in ("single", "agent_team") and str(reason).startswith("measured_"):
            return str(mode)
    except Exception:  # noqa: BLE001 - brain optional; legacy default must hold
        pass
    return "sequential_team"


def _reroute_guard_skip(goal_service: Any, decision: Mapping[str, Any]) -> tuple[bool, Any]:
    """Seam C helper: should a quota-hold reroute onto the candidate account be skipped?

    Pure decision lifted out of ``GoalService._reroute_quota_held`` so it can be
    unit-tested without the full reroute fixture. Returns ``(skip, account_ref)``.
    It is flag-gated and best-effort: with the switch off, a missing provider or
    resolver, an unmappable binding, an unknown account, or any guard failure all
    return ``(False, None)`` so the legacy reroute still happens.
    """
    if os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") != "1":
        return False, None
    provider = getattr(goal_service, "account_status_provider", None)
    resolver = getattr(goal_service, "binding_account_resolver", None)
    if provider is None or resolver is None:
        return False, None
    try:
        candidate_account = resolver(decision.get("binding_ref"))
        if candidate_account is None:
            return False, None
        from .multi_account.dispatch import reroute_guard
        verdict = reroute_guard(provider(), candidate_account)
        return bool(verdict.get("skip")), candidate_account
    except Exception:  # noqa: BLE001 - the guard must never block the reroute
        return False, None


@dataclass(frozen=True)
class PlannedTask:
    id: str
    title: str
    instruction: str
    dependencies: tuple[str, ...] = ()
    capability: str = "execute_task"
    validation_checks: tuple[dict[str, str], ...] = ()
    artifact_input: dict[str, str] | None = None
    validation_command_id: str = ""
    agent_role: str = ""
    difficulty: int = 3
    kind: str = "code"
    context_need: int = 0
    needs: tuple[str, ...] = ()
    required_artifacts: tuple[dict[str, str], ...] = ()


AGENT_TASK_ROLES = frozenset({"planner", "complex", "coder", "simple", "reviewer"})
# Compatibility fallback for callers supplying only a legacy role resolver.
ESCALATION_LADDER = {"simple": "coder", "coder": "complex"}
# Failures a pricier agent would hit the same way (login, workspace, base,
# contract, artifact, budget, cancellation, transport) never escalate.
# Provider overload: bounded same-model retries with exponential backoff.
MAX_TRANSIENT_RETRIES = 2
TRANSIENT_BACKOFF_SECONDS = 120


def _parse_utc(value: str) -> float | None:
    from datetime import datetime
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


_NON_AGENT_FAILURE = re.compile(
    r"auth|login|readiness|unavailable|not_found|network|transport|dispatch|session|resume|workspace"
    r"|contract|artifact|budget|reservation|cancel|head_moved|base|ambiguous|coordinator|process_start"
    r"|rate_limit|quota|api_error")

_LEGACY_CLEANUP_UNCERTAIN_PREFIX = "opencode_timeout:cleanup_unconfirmed:"


def _explicit_cleanup_uncertainty(failed: Any) -> bool:
    if failed.failure_classification == "cleanup_unconfirmed":
        return True
    return (failed.failure_classification == "timeout"
            and (failed.failure_detail or "").startswith(_LEGACY_CLEANUP_UNCERTAIN_PREFIX))


def _plan_task_dict(task: "PlannedTask") -> dict[str, Any]:
    payload = asdict(task)
    if not payload["agent_role"]:
        # Keep the legacy role optional; difficulty and kind are always explicit.
        del payload["agent_role"]
    return payload
DEFAULT_AGENT_ROLE = "coder"


@dataclass(frozen=True)
class GoalPlan:
    goal: GoalRecord
    planner: str
    spec_kit_available: bool
    quota_fit: dict[str, Any] | None = None


def goal_to_dict(goal: GoalRecord, *, links: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    payload = asdict(goal)
    payload["tasks"] = [dict(item) for item in goal.tasks]
    payload["acceptance_criteria"] = list(goal.acceptance_criteria)
    payload["task_links"] = [dict(item) for item in links]
    # COMPLETED aggregates execution, not functional or remote acceptance.
    payload["completion_scope"] = "EXECUTION_ONLY"
    payload["remote_acceptance"] = "NOT_OBSERVED"
    return payload


class GoalService:
    """Owns persisted planning, approval and idempotent task materialization."""

    def __init__(self, *, store: TaskStore, control_store: PlatformControlStore,
                 roster_resolver: Any | None = None, task_resolver: Any | None = None, quota_forecaster: Any | None = None, max_review_rounds: int = 3,
                 account_status_provider: Any | None = None, binding_account_resolver: Any | None = None) -> None:
        if type(max_review_rounds) is not int or max_review_rounds < 1:
            raise TaskStoreError("invalid_review_round_limit")
        self.max_review_rounds = max_review_rounds
        self.store = store
        self.control_store = control_store
        # role -> (executor_kind, binding_ref); supplied by the trusted host.
        self.roster_resolver = roster_resolver
        self.task_resolver = task_resolver
        self.quota_forecaster = quota_forecaster
        self._forecast_lock = threading.Lock()
        self._forecast_cache: OrderedDict[tuple[str, int], tuple[float, dict[str, Any]]] = OrderedDict()
        self._forecast_inflight: set[tuple[str, int]] = set()
        # Seam C (account-aware reroute guard): both are optional. When either is
        # None the guard is a no-op pass-through, so behaviour is unchanged.
        # ``account_status_provider`` yields live ``AccountStatus`` for the pool;
        # ``binding_account_resolver`` maps a candidate ``binding_ref`` to its
        # ``account_ref`` so the guard can judge whether that account is fit.
        self.account_status_provider = account_status_provider
        self.binding_account_resolver = binding_account_resolver

    def _task_route(self, goal: GoalRecord, plan_task: PlannedTask) -> tuple[str, str, str]:
        """(executor_kind, binding_ref, orchestration_mode) for one materialized task."""
        if goal.orchestration_mode != "agent_team":
            return goal.executor_kind, goal.binding_ref, goal.orchestration_mode
        if goal.binding_ref:
            return goal.executor_kind, goal.binding_ref, "single"
        if self.roster_resolver is None:
            raise TaskStoreError("agent_roster_unavailable")
        role = plan_task.agent_role or DEFAULT_AGENT_ROLE
        executor_kind, binding_ref = self.roster_resolver(role)
        if executor_kind not in {"opencode", "codex", "claude_code"} or not binding_ref:
            raise TaskStoreError(f"agent_role_unfilled:{role}")
        # Each role agent runs one task on its own; collaboration is across tasks.
        return executor_kind, binding_ref, "single"

    def create(self, payload: Mapping[str, Any]) -> GoalRecord:
        objective = str(payload.get("objective", "")).strip()
        title = str(payload.get("title", "")).strip() or self._title_from_objective(objective)
        repository = str(payload.get("repository", "dddd2024/reverse-agent")).strip()
        idempotency_key = str(payload.get("idempotency_key", "")).strip()
        if not idempotency_key:
            raise TaskStoreError("goal_idempotency_key_required")
        return self.control_store.create_goal(
            title=title,
            objective=objective,
            repository=repository,
            idempotency_key=idempotency_key,
            executor_kind=str(payload.get("executor_kind", "opencode")),
            orchestration_mode=_resolve_orchestration_mode(payload),
            binding_ref=str(payload.get("binding_ref", "")),
            policy_ref=str(payload.get("policy_ref", "")),
            window_id=str(payload.get("window_id", "")),
        )

    def plan(
        self,
        goal_id: str,
        *,
        expected_revision: int,
        acceptance_criteria: Sequence[str] = (),
        tasks: Sequence[Mapping[str, Any]] = (),
    ) -> GoalPlan:
        goal = self.control_store.get_goal(goal_id)
        if goal.revision != expected_revision:
            raise TaskStoreError("goal_revision_mismatch")
        if not isinstance(acceptance_criteria, (list, tuple)) or not isinstance(tasks, (list, tuple)):
            raise TaskStoreError("goal_plan_arrays_required")
        reject_sensitive_keys({"acceptance_criteria": list(acceptance_criteria), "tasks": list(tasks)})
        criteria = tuple(self._clean_lines(acceptance_criteria)) or self._derive_acceptance(goal.objective)
        planned = self._normalize_tasks(tasks) if tasks else self._derive_tasks(goal, criteria)
        spec = self._render_spec(goal, criteria)
        fit = self._quota_fit(goal, planned)
        plan = self._render_plan(goal, planned, fit)
        saved = self.control_store.save_goal_plan(
            goal_id,
            expected_revision=expected_revision,
            spec_markdown=spec,
            plan_markdown=plan,
            tasks=tuple(_plan_task_dict(item) for item in planned),
            acceptance_criteria=criteria,
        )
        return GoalPlan(
            goal=saved,
            planner="spec-kit-compatible/deterministic",
            spec_kit_available=shutil.which("specify") is not None,
            quota_fit=fit,
        )

    def approve(self, goal_id: str, *, expected_revision: int, policy_ref: str = "") -> GoalRecord:
        return self.control_store.approve_goal(
            goal_id, expected_revision=expected_revision, policy_ref=policy_ref
        )

    def admit_delegated(self, *, window_id: str, authority: Any, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """One SQLite commit covers delegated approval, enqueue and receipt.

        The trusted host supplies PolicyAuthority. No renderer API accepts it.
        Snapshot cardinality bounds admissions; task claims still charge the
        original window execution allowance independently.
        """
        from .autonomy import AutonomyService, bound_goal_admission, goal_admission_snapshots
        from .control_store import sha256_json
        goal_id = str(snapshot.get("goal_id", ""))
        with self.store._lock:
            conn = self.store._conn
            conn.execute("BEGIN IMMEDIATE")
            try:
                binding = authority.binding
                if dict(snapshot) not in goal_admission_snapshots(binding) or "approve_goal" not in binding["allowed_operations"]:
                    raise TaskStoreError("delegated_goal_outside_scope")
                window = self.control_store.get_window(window_id)
                persisted = self.control_store.window_policy_binding(window_id)
                expected_authority = {**binding, "decision_id": authority.decision_id,
                    "round_id": authority.round_id, "decision_content_sha256": authority.decision_content_sha256,
                    "decision_commit_sha": authority.decision_commit_sha,
                    "command_plan_sha256": authority.command_plan_sha256, "head_sha": authority.head_sha,
                    "base_sha": authority.base_sha, "branch": authority.branch}
                if (window.id != binding["window_id"] or window.status != "ACTIVE"
                        or "approve_goal" not in window.capabilities
                        or window.confirmation_mode != "DELEGATED_CONTROLLER"
                        or persisted["authority"] != expected_authority
                        or persisted["policy_digest_sha256"] != binding["policy_digest_sha256"]):
                    raise TaskStoreError("delegated_goal_window_binding_mismatch")
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                if not AutonomyService._parse_time(window.starts_at) <= now < AutonomyService._parse_time(window.expires_at):
                    raise TaskStoreError("delegated_goal_window_expired")
                goal = self.control_store.get_goal(goal_id)
                bound_goal_admission(binding, goal)
                if goal.repository != authority.repository or goal.repository not in window.repositories:
                    raise TaskStoreError("delegated_goal_repository_mismatch")
                payload = {"snapshot": dict(snapshot), "decision_content_sha256": authority.decision_content_sha256,
                           "controller_identity": binding["controller_identity"], "personally_human": False}
                prior = conn.execute(
                    "SELECT * FROM platform_operation_receipts WHERE window_id = ? AND operation_type = 'goal_admission' "
                    "AND subject_id = ? AND decision = 'allowed'", (window_id, goal_id)).fetchone()
                if prior is not None:
                    if prior["input_digest"] != sha256_json(payload) or goal.window_id != window_id:
                        raise TaskStoreError("delegated_goal_replay_conflict")
                    conn.execute("COMMIT")
                    return {"goal_id": goal_id, "admitted": True, "replayed": True}
                if goal.status != "PLANNED" or goal.window_id not in {"", window_id}:
                    raise TaskStoreError("delegated_goal_not_planned")
                planned = tuple(self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks))
                if (len(planned) != 1 or planned[0].id != binding["plan_task_id"]
                        or planned[0].capability != "validate_task" or planned[0].validation_command_id != "git_diff_check"
                        or planned[0].dependencies or planned[0].validation_checks):
                    raise TaskStoreError("delegated_goal_task_scope_mismatch")
                spent = conn.execute(
                    "SELECT COUNT(*) FROM platform_operation_receipts WHERE window_id = ? "
                    "AND operation_type = 'goal_admission' AND decision = 'allowed'", (window_id,)).fetchone()[0]
                if spent >= len(goal_admission_snapshots(binding)) or window.tasks_started >= window.max_tasks:
                    raise TaskStoreError("delegated_goal_budget_exhausted")
                self.control_store.approve_goal(goal_id, expected_revision=goal.revision, policy_ref=window.policy_id)
                self._launch(goal_id, expected_revision=goal.revision, window_id=window_id, probe_availability=False)
                self.control_store.append_receipt(
                    window_id=window_id, operation_type="goal_admission", capability="approve_goal",
                    repository=goal.repository, subject_id=goal_id, decision="allowed",
                    reason="exact_delegated_goal_snapshot", input_payload=payload,
                    external_id=goal_id, result="APPROVED_AND_ENQUEUED")
                conn.execute("COMMIT")
                return {"goal_id": goal_id, "admitted": True, "replayed": False}
            except BaseException as exc:
                conn.execute("ROLLBACK")
                if isinstance(exc, TaskStoreError) and str(exc) == "receipt_persistence_failed":
                    # Keep the window hard stop even though the admission rolled back.
                    conn.execute("UPDATE platform_autonomous_windows SET status = 'BLOCKED', "
                                 "stop_reason = 'receipt_persistence_failed' WHERE id = ?", (window_id,))
                    raise
                if not isinstance(exc, TaskStoreError):
                    raise
                # Record each stable denial once, so polling does not manufacture
                # progress or consume unbounded receipt storage.
                reason = str(exc)
                identity = sha256_json({"snapshot": dict(snapshot), "reason": reason})
                conn.execute("BEGIN IMMEDIATE")
                try:
                    previous = conn.execute(
                        "SELECT id FROM platform_operation_receipts WHERE window_id = ? "
                        "AND operation_type = 'goal_admission' AND subject_id = ? AND decision = 'denied' "
                        "AND input_digest = ?", (window_id, goal_id, identity)).fetchone()
                    if previous is None:
                        self.control_store.append_receipt(
                            window_id=window_id, operation_type="goal_admission", capability="approve_goal",
                            repository=authority.repository, subject_id=goal_id, decision="denied", reason=reason,
                            input_payload={"snapshot": dict(snapshot), "reason": reason})
                    conn.execute("COMMIT")
                except BaseException as denial_error:
                    conn.execute("ROLLBACK")
                    if isinstance(denial_error, TaskStoreError) and str(denial_error) == "receipt_persistence_failed":
                        conn.execute("UPDATE platform_autonomous_windows SET status = 'BLOCKED', "
                                     "stop_reason = 'receipt_persistence_failed' WHERE id = ?", (window_id,))
                    raise
                return {"goal_id": goal_id, "admitted": False, "replayed": previous is not None, "reason": reason}

    def amend(
        self, goal_id: str, *, expected_revision: int, objective: str,
        repository: str | None = None, executor_kind: str | None = None,
        orchestration_mode: str | None = None, binding_ref: str | None = None,
    ) -> GoalRecord:
        return self.control_store.amend_goal(
            goal_id, expected_revision=expected_revision, objective=objective,
            repository=repository, executor_kind=executor_kind,
            orchestration_mode=orchestration_mode, binding_ref=binding_ref,
        )

    def launch(self, goal_id: str, *, expected_revision: int, window_id: str) -> GoalRecord:
        # Serialize the approved snapshot with all materialization writes, including
        # against configuration updates made through another SQLite connection.
        with self.store._lock:
            self.store._conn.execute("BEGIN IMMEDIATE")
            try:
                goal = self._launch(goal_id, expected_revision=expected_revision, window_id=window_id)
                self.store._conn.execute("COMMIT")
                return goal
            except BaseException:
                self.store._conn.execute("ROLLBACK")
                raise

    def rebind(self, goal_id: str, *, window_id: str) -> dict[str, Any]:
        """Explicit Owner rebind of a stranded Goal to a new active window (#1277)."""
        outcome = self.control_store.rebind_goal_to_window(goal_id, window_id=window_id)
        return {**outcome, "goal": self.detail(goal_id)}

    def _launch(self, goal_id: str, *, expected_revision: int, window_id: str,
                probe_availability: bool = True, _owner_window_admission: bool = False) -> GoalRecord:
        goal = self.control_store.get_goal(goal_id)
        if goal.revision != expected_revision:
            raise TaskStoreError("goal_not_launchable")
        if goal.status == "RUNNING" and goal.window_id == window_id:
            return goal
        if goal.status != "APPROVED":
            raise TaskStoreError("goal_not_launchable")
        window = self.control_store.get_window(window_id)
        if window.status != "ACTIVE":
            raise TaskStoreError("goal_requires_active_window")
        if goal.repository not in window.repositories:
            raise TaskStoreError("goal_repository_outside_window")
        if self.control_store.is_owner_window(window) and not _owner_window_admission:
            # The Owner confirmed this window's Goals by name; nothing else is launched into it.
            raise TaskStoreError("owner_window_goal_not_confirmed")
        planned_tasks = tuple(self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks))
        if self.control_store.is_strict_owner_window(window):
            if (goal.orchestration_mode != "single" or len(planned_tasks) != 1
                    or any(other.id != goal.id for other in self.control_store.list_window_goals(window_id))):
                raise TaskStoreError("strict_window_requires_one_single_task_goal")
        for item in planned_tasks:
            if item.capability not in window.capabilities:
                raise TaskStoreError(f"goal_window_missing_{item.capability}_capability")
            if item.validation_command_id and (goal.orchestration_mode not in {"single", "agent_team"} or item.artifact_input
                                               or item.validation_checks):
                raise TaskStoreError("host_validation_requires_standalone_single_task")
        routes, decisions = self._route_tasks(goal, planned_tasks, window_id=window_id,
                                              probe_availability=probe_availability)
        if any(kind in {"opencode", "codex", "claude_code"} for kind, _, _ in routes):
            try:
                resolve_repository_workspace(goal.repository)
            except RepositoryWorkspaceError as exc:
                raise TaskStoreError(
                    str(exc)
                )

        functional_base = repository_base(goal.repository) if any(
            kind in {"codex", "claude_code"} for kind, _, _ in routes) or any(
            raw.get("validation_checks") for raw in goal.tasks
        ) or any((decision or {}).get(_INITIAL_WAIT) for decision in decisions.values()) else ""
        for seq, raw in enumerate(goal.tasks):
            plan_task = self._normalize_task(raw, seq=seq)
            executor_kind, binding_ref, orchestration_mode = routes[seq]
            decision = decisions[seq]
            if (decision or {}).get(_INITIAL_WAIT):
                if re.fullmatch(r"[0-9a-f]{40}", functional_base):
                    decision[_INITIAL_WAIT] = {**decision[_INITIAL_WAIT], "base_commit": functional_base,
                        "goal_id": goal.id, "goal_revision": goal.revision,
                        "goal_artifact_digest": goal.artifact_digest, "plan_task_id": plan_task.id}
                else:
                    decision.pop(_INITIAL_WAIT)
            task = self.store.create_task(
                title=self._execution_title(goal, plan_task),
                repository=goal.repository,
                executor_kind=executor_kind,
                binding_ref=binding_ref,
                branch=functional_base if executor_kind in {"codex", "claude_code"} or (decision or {}).get(_INITIAL_WAIT) else "",
                permission_profile="AUTONOMOUS_WINDOW",
                policy_ref=window.id if plan_task.validation_command_id else window.policy_id,
                idempotency_key=f"goal:{goal.id}:r{goal.revision}:{plan_task.id}",
                orchestration_mode=orchestration_mode,
            )
            if decisions[seq] is not None:
                if not decisions[seq].get("binding_ref"):
                    if decision.get(_INITIAL_WAIT):
                        decision[_INITIAL_WAIT]["task_id"] = task.id
                        decision[_INITIAL_WAIT]["execution_id"] = task.execution_id
                    self.store.block_model_selection(task.id, decision=decisions[seq])
                else:
                    self._record_model_selection(task, decisions[seq])
            freeze_contract(self.store, task, goal=goal, plan_task=plan_task, base_commit=functional_base)
            freeze_required_artifacts(self.store, task, goal=goal, plan_task=plan_task)
            freeze_handoff_contract(self.store, task, goal=goal, plan_task=plan_task, base_commit=functional_base)
            if plan_task.validation_command_id:
                self._freeze_host_validation(task, goal, plan_task, window)
            try:
                self.control_store.link_goal_task(
                    goal.id,
                    goal_revision=goal.revision,
                    plan_task_id=plan_task.id,
                    task_id=task.id,
                    dependencies=plan_task.dependencies,
                    seq=seq,
                )
            except Exception as exc:
                if "UNIQUE constraint failed" not in str(exc):
                    raise
        current = self.control_store.get_goal(goal_id)
        if current.status == "RUNNING" and current.window_id == window_id:
            return current
        running = self.control_store.mark_goal_running(goal.id, revision=goal.revision, window_id=window_id)
        if any(decision is not None and not decision.get("binding_ref") for decision in decisions.values()):
            return self.control_store.refresh_goal_status(goal.id)
        return running

    def _initial_contracts_match(self, task: Any, goal: Any, plan: PlannedTask,
                                 planned: Mapping[str, PlannedTask], base: str) -> bool:
        """Validate existing frozen proof against the approved plan; never create it."""
        try:
            functional, handoff, required = load_contract(task), load_handoff_contract(task), load_required_artifacts(task)
            checks = list(normalize_checks(plan.validation_checks))
            export = any(item.artifact_input == {"plan_task_id": plan.id} for item in planned.values())
            if (task.repository != goal.repository or bool(checks) != (functional is not None)
                    or (plan.artifact_input is not None or export) != (handoff is not None)
                    or bool(plan.required_artifacts) != (required is not None)):
                return False
            if functional and (functional["checks"] != checks
                    or functional["requires_implementation"] != (plan.capability == "execute_task")):
                return False
            if handoff and (handoff["version"] != 2 or handoff["artifact_input"] != plan.artifact_input
                    or handoff["export_required"] != export or handoff["capability"] != plan.capability
                    or handoff["kind"] != plan.kind or handoff["agent_role"] != plan.agent_role):
                return False
            identity = {"task_id": task.id, "goal_id": goal.id, "goal_revision": goal.revision,
                        "goal_artifact_digest": goal.artifact_digest, "plan_task_id": plan.id}
            for contract in (functional, handoff):
                if contract and (contract["base_commit"] != base
                        or any(contract.get(key) != value for key, value in identity.items())):
                    return False
            return not required or (required["task_id"] == task.id and required["goal_id"] == goal.id
                and required["goal_revision"] == goal.revision
                and required["files"] == list(normalize_required_artifacts(plan.required_artifacts)))
        except (KeyError, TypeError, ValueError, TaskStoreError):
            return False

    def _initial_selection_state(self, task: Any, goal: Any, plan: PlannedTask,
                                 planned: Mapping[str, PlannedTask]) -> tuple[dict, str] | None:
        """Prove a marked initial task never entered execution; caller holds store lock."""
        if (plan.validation_command_id or task.status != "BLOCKED" or _INITIAL_WAIT not in task.failure_detail
                or task.binding_ref or task.workspace or task.model_profile_ref
                or task.validation_command_id or task.validation_exit_code is not None or task.validation_output_digest
                or task.repository != goal.repository
                or task.permission_profile != "AUTONOMOUS_WINDOW"
                or self.store._has_execution_history_locked(task.id)):
            return None
        for table in ("task_usage_observations", "platform_usage_charges", "durable_external_operations",
                      "task_changed_files", "platform_quota_admissions"):
            if self.store._conn.execute(f"SELECT 1 FROM {table} WHERE task_id=? LIMIT 1", (task.id,)).fetchone():
                return None
        if self.store._conn.execute("SELECT 1 FROM task_events WHERE task_id=? "
                "AND type NOT IN ('DISCOVERED','MODEL_SELECTION_FAILED') LIMIT 1", (task.id,)).fetchone():
            return None
        if any(ref.get("status") != "APPROVED" for ref in task.evidence_refs):
            return None
        event = self.store._conn.execute("SELECT id,metadata FROM task_events WHERE task_id=? "
            "AND type='MODEL_SELECTION_FAILED' ORDER BY seq DESC LIMIT 1", (task.id,)).fetchone()
        try:
            decision = json.loads(task.failure_detail)
            marker = decision[_INITIAL_WAIT]
            if event is None or json.loads(event["metadata"]) != decision or not isinstance(marker, dict):
                return None
            if task.failure_classification != decision.get("reason"):
                return None
            identity = {"task_id": task.id, "execution_id": task.execution_id, "goal_id": goal.id, "goal_revision": goal.revision,
                        "goal_artifact_digest": goal.artifact_digest, "plan_task_id": plan.id}
            if (type(marker.get("version")) is not int or marker["version"] != 1
                    or type(marker.get("goal_revision")) is not int
                    or any(marker.get(key) != value for key, value in identity.items())
                    or marker.get("kind") not in {"resource", "author"}
                    or type(marker.get("retry_at")) not in (int, float) or not math.isfinite(marker["retry_at"])
                    or marker.get("base_commit") != task.branch or not re.fullmatch(r"[0-9a-f]{40}", task.branch)):
                return None
            if marker["kind"] == "author":
                ancestry = self._review_ancestry(plan, planned)
                if (not ancestry or marker.get("author_plan_ids") != list(ancestry)
                        or decision.get("reason") != "review_not_independent"):
                    return None
            elif (decision.get("temporary_resource_blocked") is not True
                    or decision.get("reason") not in {"no_runnable_model", "pinned_model_unavailable", "review_not_independent"}):
                return None
            if not self._initial_contracts_match(task, goal, plan, planned, task.branch):
                return None
            return marker, event["id"]
        except (KeyError, TypeError, ValueError, TaskStoreError):
            return None

    def _initial_window_live(self, goal: Any, window_id: str) -> bool:
        with self.store._lock:
            window = self.control_store.get_window(window_id)
            active = self.store._conn.execute("SELECT id FROM platform_autonomous_windows WHERE status='ACTIVE' "
                "AND julianday(starts_at)<=julianday('now') AND julianday(expires_at)>julianday('now') "
                "ORDER BY created_at DESC LIMIT 1").fetchone()
            return bool(active and active["id"] == window_id and goal.window_id == window_id
                and goal.status in {"RUNNING", "BLOCKED"} and goal.repository in window.repositories
                and window.tasks_started < window.max_tasks)

    def _commit_initial_selection(self, goal: Any, plan: PlannedTask, task_id: str, event_id: str,
                                  decision: Mapping[str, Any], authors: Mapping[str, Any], autonomy: Any) -> bool:
        """CAS task, selection evidence and goal aggregation under one write transaction."""
        with self.store._lock:
            self.store._conn.execute("BEGIN IMMEDIATE")
            try:
                current = self.control_store.get_goal(goal.id)
                task = self.store.get_task(task_id)
                links = self.control_store.list_goal_tasks(goal.id)
                planned = {item.id: item for item in
                           (self._normalize_task(raw, seq=i) for i, raw in enumerate(current.tasks))}
                state = self._initial_selection_state(task, current, plan, planned)
                if (current.revision != goal.revision or current.artifact_digest != goal.artifact_digest
                        or not self._initial_window_live(current, goal.window_id)
                        or not any(row["task_id"] == task_id and row["plan_task_id"] == plan.id
                                   and int(row["goal_revision"]) == current.revision for row in links)
                        or state is None or state[1] != event_id
                        or self._review_authors(plan, current, planned, require_frozen=True) != authors):
                    self.store._conn.execute("ROLLBACK")
                    return False
                window = self.control_store.get_window(goal.window_id)
                if task.policy_ref != window.policy_id or plan.capability not in window.capabilities:
                    self.store._conn.execute("ROLLBACK")
                    return False
                autonomy._check_window_authority(goal.window_id)
                selected = bool(decision.get("binding_ref"))
                metadata = dict(decision)
                metadata.pop(_INITIAL_WAIT, None)
                if selected:
                    self.store._update_task_fields(task_id, {"status": "QUEUED",
                        "binding_ref": decision["binding_ref"], "executor_kind": decision["executor_kind"],
                        "failure_classification": "", "failure_detail": ""})
                    from .task_runtime import task_operation
                    allowed = autonomy.authorize(window_id=goal.window_id, operation=task_operation(self.store.get_task(task_id)),
                        repository=goal.repository, subject_id=task_id,
                        input_payload={"source": "initial_model_selection_recovery"})
                    if not allowed:
                        self.store._update_task_fields(task_id, {"status": "BLOCKED", "binding_ref": "",
                            "executor_kind": task.executor_kind})
                        metadata = {"reason": "initial_selection_authority_denied"}
                        selected = False
                else:
                    wait = _initial_resource_wait(metadata)
                    if wait:
                        metadata[_INITIAL_WAIT] = {**state[0], **wait}
                if not self._initial_window_live(current, goal.window_id):
                    self.store._conn.execute("ROLLBACK")
                    return False
                if selected:
                    metadata["selection_origin"] = "initial_resource_recovery"
                    self.store._append_event(task_id=task_id, event_type="MODEL_SELECTED", title="Initial model selected",
                        description=f"{decision['binding_ref']}: initial resource recovery", metadata=metadata)
                else:
                    self.store._update_task_fields(task_id, {"failure_classification": str(metadata["reason"]),
                        "failure_detail": json.dumps(metadata)})
                    self.store._append_event(task_id=task_id, event_type="MODEL_SELECTION_FAILED",
                        title="Initial model selection deferred", description=str(metadata["reason"]), metadata=metadata)
                self.control_store.refresh_goal_status(goal.id)
                self.store._conn.execute("COMMIT")
                return selected
            except BaseException:
                self.store._conn.execute("ROLLBACK")
                raise

    def reconsider_initial_models(self, window_id: str, *, autonomy: Any, limit: int = 25) -> tuple[str, ...]:
        """Reconsider only marked, never-dispatched initial waits in the existing window."""
        if (os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") != "1" or self.task_resolver is None
                or getattr(autonomy, "control_store", None) is not self.control_store):
            return ()
        selected, checked, authority_checked = [], 0, False
        for goal in self.control_store.list_window_goals(window_id):
            if checked >= limit:
                break
            if (goal.orchestration_mode != "agent_team" or goal.status not in {"RUNNING", "BLOCKED"}
                    or not self._initial_window_live(goal, window_id)):
                continue
            planned = {item.id: item for item in
                       (self._normalize_task(raw, seq=i) for i, raw in enumerate(goal.tasks))}
            links = {row["plan_task_id"]: row["task_id"] for row in self.control_store.list_goal_tasks(goal.id)
                     if int(row["goal_revision"]) == goal.revision}
            visited = set()
            def reconsider(plan_id):
                nonlocal checked, authority_checked
                if plan_id in visited or plan_id not in links or checked >= limit:
                    return
                visited.add(plan_id)
                plan = planned[plan_id]
                task_id = links[plan_id]
                with self.store._lock:
                    state = self._initial_selection_state(self.store.get_task(task_id), goal, plan, planned)
                if state is None:
                    return
                if state[0]["kind"] == "author":
                    for source in self._review_ancestry(plan, planned):
                        reconsider(source)
                elif state[0]["retry_at"] > time.time():
                    return
                if checked >= limit:
                    return
                try:
                    with self.store._lock:
                        authors = self._review_authors(plan, goal, planned, require_frozen=True)
                except TaskStoreError:
                    return  # no author identity is guessed from an unbound source
                if not authority_checked:
                    autonomy._check_window_authority(window_id)
                    authority_checked = True
                checked += 1
                try:
                    arguments = {key: value for key, value in authors.items() if key != "_initial_author_snapshot"}
                    decision = self.task_resolver(plan, goal=goal, probe_availability=False, **arguments)
                    if (not isinstance(decision, Mapping)
                            or decision.get("executor_kind") not in {"opencode", "codex", "claude_code"}
                            or any(not isinstance(decision.get(key), str) or not decision[key]
                                   or decision[key] != decision[key].strip() for key in ("binding_ref", "model_id", "reason"))):
                        decision = {"reason": "initial_selection_route_invalid"}
                except TaskStoreError as exc:
                    code = str(exc)
                    detail = getattr(exc, "decision", {})
                    decision = dict(detail) if isinstance(detail, Mapping) else {}
                    if code not in {"no_runnable_model", "pinned_model_unavailable", "review_not_independent", "no_willing_model"}:
                        decision = {"reason": "initial_selection_resolver_error", "error_type": type(exc).__name__}
                    else:
                        decision["reason"] = code
                    decision.pop("binding_ref", None)
                    decision.pop(_INITIAL_WAIT, None)
                except Exception as exc:
                    decision = {"reason": "initial_selection_resolver_error", "error_type": type(exc).__name__}
                if self._commit_initial_selection(goal, plan, task_id, state[1], decision, authors, autonomy):
                    selected.append(task_id)
            for plan_id in planned:
                reconsider(plan_id)
        return tuple(selected)

    def _route_tasks(self, goal: GoalRecord, planned_tasks: Sequence[PlannedTask], *, window_id: str,
                     probe_availability: bool = True) -> tuple[list[tuple[str, str, str]], dict[int, Any]]:
        """Route every planned task the way launch does, creating nothing.

        Returns ``(executor_kind, binding_ref, orchestration_mode)`` per task and the
        resolver decision per task (``None`` when the Goal is not routed). A task the
        resolver could not place gets an empty binding and its decision says why.
        Shared by launch and the Owner window preview so the two cannot drift.
        """
        # Resolve every task before creating any. Artifact authors are resolved first
        # so review independence also holds for plans saved in any order.
        decisions: dict[int, Any] = {}
        resolved: dict[int, tuple[str, str, str]] = {}
        indices = {item.id: i for i, item in enumerate(planned_tasks)}

        def resolve(seq: int) -> tuple[str, str, str]:
            if seq in resolved:
                return resolved[seq]
            item = planned_tasks[seq]
            if goal.orchestration_mode == "agent_team" and self.task_resolver is not None:
                pending_authors = ()
                try:
                    ancestry = self._review_ancestry(item, {t.id: t for t in planned_tasks})
                    author_bindings = tuple(resolve(indices[source])[1] for source in ancestry)
                    if ancestry and not all(author_bindings):
                        missing = [source for source, binding in zip(ancestry, author_bindings) if not binding]
                        if (os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED") == "1"
                                and all((decisions[indices[source]] or {}).get(_INITIAL_WAIT) for source in missing)):
                            pending_authors = ancestry
                        raise TaskStoreError("review_not_independent")
                    # Preserve the chosen identity even if binding configuration
                    # changes while resolving the rest of the plan.
                    author_models = tuple(decisions[indices[source]].get("model_id", "") for source in ancestry)
                    args = {"author_models": tuple(m for m in author_models if m),
                            "author_bindings": tuple(binding for binding, model in zip(author_bindings, author_models)
                                                     if not model)} if ancestry else {}
                    probe = {} if probe_availability else {"probe_availability": False}
                    decision = dict(self.task_resolver(item, goal=replace(goal, window_id=window_id), **args, **probe))
                    decision.pop(_INITIAL_WAIT, None)
                except TaskStoreError as exc:
                    if str(exc) not in {"no_willing_model", "no_runnable_model", "pinned_model_unavailable", "review_not_independent"}:
                        raise
                    decision = dict(getattr(exc, "decision", {"reason": str(exc)}))
                    decision.pop("binding_ref", None)
                    decision.pop(_INITIAL_WAIT, None)
                    wait = ({"version": 1, "kind": "author", "author_plan_ids": list(pending_authors),
                             "retry_at": time.time() + INITIAL_MODEL_RECHECK_SECONDS} if pending_authors
                            else _initial_resource_wait(decision))
                    if item.validation_command_id:
                        wait = None  # a fixed host checker is not model-selection work
                    if wait:
                        decision[_INITIAL_WAIT] = wait
                    decisions[seq] = decision
                    resolved[seq] = ("opencode", "", "single")
                    return resolved[seq]
                resolved[seq] = (decision["executor_kind"], decision["binding_ref"], "single")
                decisions[seq] = decision
            else:
                resolved[seq] = self._task_route(goal, item)
                decisions[seq] = None
            return resolved[seq]

        return [resolve(seq) for seq in range(len(planned_tasks))], decisions

    @staticmethod
    def _review_ancestry(task: PlannedTask, planned: Mapping[str, PlannedTask]) -> tuple[str, ...]:
        if not task.artifact_input or not (task.kind == "review" or task.agent_role == "reviewer"):
            return ()
        visited: set[str] = set()
        active: set[str] = set()
        def visit(task_id: str) -> None:
            if task_id in active or task_id not in planned:
                raise TaskStoreError("review_not_independent")
            if task_id in visited:
                return
            active.add(task_id)
            for dependency in planned[task_id].dependencies:
                visit(dependency)
            active.remove(task_id)
            visited.add(task_id)
        visit(task.artifact_input["plan_task_id"])
        return tuple(sorted(visited))

    def reroute_quota_held(self, goal_id: str) -> tuple[dict[str, Any], ...]:
        """Coordinator entry for quota holds; same window and mode bounds as escalation."""
        goal = self.control_store.get_goal(goal_id)
        if goal.orchestration_mode != "agent_team" or not goal.window_id or self.task_resolver is None:
            return ()
        window = self.control_store.get_window(goal.window_id)
        if window.status != "ACTIVE" or not self.store._conn.execute(
                "SELECT 1 FROM platform_autonomous_windows WHERE id = ? AND julianday(starts_at) <= julianday('now') "
                "AND julianday(expires_at) > julianday('now')", (window.id,)).fetchone():
            return ()
        planned = {item.id: item for item in (self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks))}
        return tuple(self._reroute_quota_held(goal, planned))

    def _reroute_quota_held(self, goal: Any, planned: Mapping[str, PlannedTask]) -> list[dict[str, Any]]:
        """A quota hold moves a never-started task to an equal-or-higher-tier model (#1313 D).

        The held model's selected tier is the floor: the router's no-downgrade rule
        picks a higher tier, then a distinct model at the same tier. If it can only
        offer the held model itself, or a lower tier, the task keeps waiting. Each
        task re-routes at most once, so holds on both models cannot make it flap.
        """
        moved = []
        for link in self.control_store.list_goal_tasks(goal.id):
            if link["status"] != "QUEUED" or int(link["goal_revision"]) != goal.revision:
                continue
            plan_task = planned.get(link["plan_task_id"])
            if plan_task is None or plan_task.validation_command_id:
                continue
            hold = self.control_store.quota_hold(link["task_id"])
            if hold is None:
                continue
            task = self.store.get_task(link["task_id"])
            if self._review_intent_hold(task, plan_task):
                continue
            events = self.store.get_events(task.id)
            if any(event.type == "MODEL_SELECTED" and event.metadata.get("reroute_reason") for event in events):
                continue
            selected = next((event.metadata for event in reversed(events) if event.type == "MODEL_SELECTED"
                             and event.metadata.get("binding_ref") == task.binding_ref), {})
            held_tier = selected.get("tier")
            if type(held_tier) is not int or not 1 <= held_tier <= 5:
                continue  # no recorded selection to compare against: never guess a floor
            try:
                decision = self.task_resolver(plan_task, goal=goal, failed_binding=task.binding_ref,
                                              failed_tier=held_tier, **self._review_authors(plan_task, goal, planned))
            except TaskStoreError:
                continue
            from .model_router import model_identity
            same_model = bool(selected.get("model_id")) and model_identity(
                str(decision.get("model_id") or "")) == model_identity(str(selected["model_id"]))
            if (decision.get("binding_ref") in {"", task.binding_ref} or same_model
                    or decision.get("downgrade_fallback")
                    or type(decision.get("tier")) is not int or decision["tier"] < held_tier):
                continue  # another binding of the held model is not a different model
            native = decision["executor_kind"] in {"codex", "claude_code"}
            try:
                base = self._approved_base(task)
            except TaskStoreError:
                continue
            if native and not base:
                continue  # native executors need an exact launch base; without one, keep waiting
            # Seam C: account-aware reroute guard. The brain may already have
            # flagged the candidate account as EXHAUSTED/ABNORMAL; rerouting the
            # held task onto it would defeat the fault-tolerance purpose. When the
            # guard says "skip" we leave the task waiting (preserving stability)
            # instead of sending it to a bad account.
            skip, candidate_account = _reroute_guard_skip(self, decision)
            if skip:
                self.store.add_event(
                    task.id, event_type="MODEL_SELECTED", title="Model selection skipped",
                    description=f"{decision.get('binding_ref')}: reroute_guard_skip (unfit account)",
                    metadata={"reroute_reason": None, "guard": "account_health",
                              "account_ref": candidate_account, "health": "UNFIT"})
                continue
            if not self.control_store.reroute_held_task(
                    task.id, expected_binding=task.binding_ref, binding_ref=decision["binding_ref"],
                    executor_kind=decision["executor_kind"], branch=base if native and base else ""):
                continue
            self.store.add_event(task.id, event_type="MODEL_SELECTED", title="Model selected",
                                 description=f"{decision['binding_ref']}: quota_hold_reroute from {task.binding_ref}",
                                 metadata=dict(decision, reroute_reason="quota_hold", from_binding=task.binding_ref,
                                               held_tier=held_tier, hold=hold))
            moved.append({"plan_task_id": plan_task.id, "task_id": task.id, "reason": "quota_hold_reroute",
                          "from_binding": task.binding_ref, "to_binding": decision["binding_ref"]})
        return moved

    def _review_authors(self, task: PlannedTask, goal: Any, planned: Mapping[str, PlannedTask], *,
                        require_frozen: bool = False) -> dict[str, Any]:
        """Resolve authors from execution facts, retaining replaced attempts."""
        ancestry = self._review_ancestry(task, planned)
        if not ancestry:
            return {}
        links = {row["plan_task_id"]: row for row in self.control_store.list_goal_tasks(goal.id)
                 if int(row["goal_revision"]) == goal.revision}
        models, bindings, executors = set(), set(), set()
        snapshot = []
        history = self.control_store.list_task_escalations(goal.id)
        for source in ancestry:
            if source not in links:
                raise TaskStoreError("review_not_independent")
            ids = {links[source]["task_id"]}
            ids.update(row["from_task_id"] for row in history
                       if row["plan_task_id"] == source and int(row["goal_revision"]) == goal.revision)
            for task_id in ids:
                attempt = self.store.get_task(task_id)
                executors.add(getattr(attempt, "executor_kind", "") or "")
                observations = self.store.list_usage_observations(task_id)
                if require_frozen and (any(row.status != "OBSERVED" for row in observations)
                        or self.store._conn.execute("SELECT 1 FROM durable_external_operations WHERE task_id=? "
                            "AND state NOT IN ('SUCCESS','FAILED','RECONCILED') LIMIT 1", (task_id,)).fetchone()):
                    raise TaskStoreError("review_not_independent")
                if require_frozen:
                    if not self._initial_contracts_match(attempt, goal, planned[source], planned, self._approved_base(attempt)):
                        raise TaskStoreError("review_not_independent")
                    selected = self.store._conn.execute("SELECT id,metadata FROM task_events "
                        "WHERE task_id=? AND type='MODEL_SELECTED' ORDER BY seq", (task_id,)).fetchall()
                    usage = self.store._conn.execute("SELECT id,execution_id,model_id,status FROM task_usage_observations "
                        "WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
                    snapshot.append((source, task_id, attempt.execution_id, attempt.executor_kind, attempt.binding_ref,
                                     tuple(tuple(row) for row in selected), tuple(tuple(row) for row in usage),
                                     tuple((ref["id"], ref["category"], ref["value"], ref["status"], ref["raw_json_digest"])
                                           for ref in attempt.evidence_refs)))
                recorded = {row.model_id for row in observations if row.model_id}
                if not recorded:
                    for event in self.store.get_events(task_id):
                        if event.type == "MODEL_SELECTED":
                            model = event.metadata.get("model_id") or next((row.get("model_id")
                                for row in event.metadata.get("candidates", ())
                                if row.get("binding_id") == attempt.binding_ref), None)
                            if model:
                                recorded.add(model)
                if recorded:
                    models.update(recorded)
                elif attempt.binding_ref and attempt.status == "QUEUED" and not require_frozen:
                    bindings.add(attempt.binding_ref)
                else:
                    raise TaskStoreError("review_not_independent")
        result = {"author_models": tuple(sorted(models)), "author_bindings": tuple(sorted(bindings)),
                  "author_executors": tuple(sorted(executors))}
        if require_frozen:
            result["_initial_author_snapshot"] = tuple(sorted(snapshot))
        return result

    def _review_intent_hold(self, task: Any, plan_task: PlannedTask | None) -> bool:
        """True when a review execution's reviewer call may still be outstanding (#1191).

        FAILED does not prove the call settled: if parking BLOCKED itself failed,
        generic dispatch cleanup may have written FAILED over a PENDING intent.
        An unresolved or unreadable journal holds automatic replacement; the raw
        status stays as written, with one typed hold event per distinct reason.
        If that event cannot be recorded, nothing new is scheduled either.
        """
        from . import model_review, artifact_handoff as artifacts
        review = plan_task is not None and (plan_task.kind == "review" or plan_task.agent_role == "reviewer")
        if not review:
            try:
                review = artifacts.model_review_input(task)
            except Exception:
                review = True  # an unreadable contract cannot prove this is not a review
        if not review:
            return False
        try:
            with self.store._lock:
                rows = model_review._journal_rows(self.store, model_review.rpc_intent_key(task.execution_id))
                rows += [dict(row) for row in self.store._conn.execute(
                    "SELECT * FROM durable_external_operations WHERE task_id = ? AND operation_key = ?",
                    (task.id, model_review.RPC_OPERATION)).fetchall()]
            pending = [row for row in rows if row.get("state") not in model_review.SETTLED_STATES]
            if not pending:
                return False
            hold = f"intent_{str(pending[0].get('state')).lower()}:{pending[0].get('operation_id')}"
            detail = (f"reviewer call {pending[0].get('operation_id')} for {task.execution_id} is journaled "
                      f"{pending[0].get('state')} and may have been dispatched or completed remotely")
        except Exception as exc:
            hold = f"intent_unverifiable:{type(exc).__name__}"
            detail = (f"reviewer journal for {task.execution_id} could not be read ({type(exc).__name__}); "
                      "an earlier reviewer call may have been dispatched or completed remotely")
        description = (f"model_review_retry_held:{hold}: {detail}; task status remains "
                       f"{task.status}/{task.failure_classification or 'unclassified'} as written; no replacement "
                       "reviewer execution is scheduled automatically; reconcile manually")
        try:
            if not any(event.type == "MODEL_SELECTION_FAILED"
                       and event.metadata.get("reason") == "model_review_intent_unresolved"
                       and event.metadata.get("hold") == hold for event in self.store.get_events(task.id)):
                self.store.add_event(task.id, event_type="MODEL_SELECTION_FAILED",
                                     title="Review retry held: reviewer call unresolved", description=description,
                                     metadata={"reason": "model_review_intent_unresolved", "hold": hold,
                                               "task_status": task.status,
                                               "failure_classification": task.failure_classification})
        except Exception as exc:
            raise TaskStoreError(f"model_review_retry_hold_unrecorded:{task.id}: {type(exc).__name__}; "
                                 "no replacement scheduled") from exc
        return True

    def _repair_rejected_reviews(self, goal_id: str) -> tuple[dict[str, Any], ...]:
        """Atomically admit bounded repairs per producer/revision.

        Escalation history counts review rounds separately from routing attempts;
        both replacement executions still spend the existing window retry budget.
        """
        from . import model_review, artifact_handoff as artifacts
        outcomes = []
        with self.store._lock:
            owns_transaction = not self.store._conn.in_transaction
            if owns_transaction:
                self.store._conn.execute("BEGIN IMMEDIATE")
            try:
                goal = self.control_store.get_goal(goal_id)
                active = self.store._conn.execute(
                    "SELECT 1 FROM platform_autonomous_windows WHERE id = ? AND status = 'ACTIVE' "
                    "AND julianday(starts_at) <= julianday('now') AND julianday(expires_at) > julianday('now')",
                    (goal.window_id,)).fetchone()
                if goal.orchestration_mode != "agent_team" or not active:
                    if owns_transaction:
                        self.store._conn.execute("COMMIT")
                    return ()
                window = self.control_store.get_window(goal.window_id)
                planned = {raw["id"]: self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks)}
                links = {row["plan_task_id"]: row for row in self.control_store.list_goal_tasks(goal_id)}
                history = self.control_store.list_task_escalations(goal_id)
                for review_id, link in links.items():
                    review_plan = planned[review_id]
                    failed = self.store.get_task(link["task_id"])
                    if review_plan.artifact_input and artifacts.model_review_input(failed):
                        source_id = review_plan.artifact_input["plan_task_id"]
                        producer = self.store.get_task(links[source_id]["task_id"])
                        rounds = [row for row in history if int(row["goal_revision"]) == goal.revision
                                  and row["plan_task_id"] == source_id and row["reason"].startswith("model_review_repair:")]
                        feedback = artifacts._load_evidence(producer, "ReviewRepair", producer.execution_id)
                        if (producer.status == "READY_FOR_REVIEW" and feedback is not None
                                and feedback["review_task_id"] == failed.id):
                            if self._review_intent_hold(failed, review_plan):
                                continue
                            if len(history) >= window.max_retries:
                                self.store.block_model_selection(failed.id, decision={"reason": "routing_retry_budget_exhausted"})
                                continue
                            base = self._approved_base(producer)
                            decision = None
                            if self.task_resolver is not None:
                                try:
                                    decision = self.task_resolver(review_plan, goal=goal,
                                        **self._review_authors(review_plan, goal, planned))
                                except TaskStoreError as exc:
                                    self.store.block_model_selection(failed.id, decision=getattr(exc, "decision", {"reason": str(exc)}))
                                    continue
                            executor = decision["executor_kind"] if decision is not None else failed.executor_kind
                            binding_ref = decision["binding_ref"] if decision is not None else failed.binding_ref
                            fresh = self.store.create_task(title=self._execution_title(goal, review_plan), repository=goal.repository,
                                executor_kind=executor, binding_ref=binding_ref,
                                model_profile_ref="" if decision is not None else failed.model_profile_ref,
                                branch=base if executor in {"codex", "claude_code"} else "",
                                permission_profile=failed.permission_profile, policy_ref=failed.policy_ref,
                                idempotency_key=f"goal:{goal.id}:r{goal.revision}:{source_id}:review-round{len(rounds) + 1}:review")
                            if decision is not None:
                                self._record_model_selection(fresh, decision)
                            freeze_contract(self.store, fresh, goal=goal, plan_task=review_plan, base_commit=base)
                            freeze_handoff_contract(self.store, fresh, goal=goal, plan_task=review_plan, base_commit=base)
                            self.control_store.escalate_goal_task(goal.id, goal_revision=goal.revision, plan_task_id=review_id,
                                from_task_id=failed.id, to_task_id=fresh.id, from_role=review_plan.agent_role,
                                to_role=review_plan.agent_role, reason=f"model_review_refresh:{failed.id}")
                            outcomes.append({"plan_task_id": review_id, "from_task_id": failed.id, "to_task_id": fresh.id})
                            history = self.control_store.list_task_escalations(goal_id)
                            continue
                    if (failed.status != "FAILED" or failed.failure_classification != "model_review_rejected"
                            or not artifacts.model_review_input(failed)
                            or self.control_store.can_complete_host_claim(window_id=window.id, task_id=failed.id)):
                        continue
                    if self._review_intent_hold(failed, review_plan):
                        continue
                    try:
                        rows = [row for row in failed.evidence_refs if row.get("category") == "ModelReview"]
                        if len(rows) != 1:
                            continue
                        run = self.store._get_durable_run(json.loads(rows[0]["detail"])["run_id"])
                        evidence = model_review.verified_evidence(self.store, failed, run, require_accept=False)
                        if evidence["result"]["verdict"] != "REJECT":
                            continue
                        binding = artifacts.load_input_binding(failed)
                    except (TaskStoreError, KeyError, ValueError, TypeError, OSError):
                        continue
                    source_id = review_plan.artifact_input["plan_task_id"]
                    producer = self.store.get_task(links[source_id]["task_id"])
                    rounds = [row for row in history if int(row["goal_revision"]) == goal.revision
                              and row["plan_task_id"] == source_id and row["reason"].startswith("model_review_repair:")]
                    if len(rounds) + 1 >= self.max_review_rounds or len(history) + 2 > window.max_retries:
                        self.store.block_model_selection(failed.id, decision={"reason":
                            "model_review_round_limit" if len(rounds) + 1 >= self.max_review_rounds else "routing_retry_budget_exhausted"})
                        continue
                    source_plan = planned[source_id]
                    base = self._approved_base(producer)
                    try:
                        repair_decision = self.task_resolver(source_plan, goal=goal) if self.task_resolver is not None else None
                    except TaskStoreError as exc:
                        self.store.block_model_selection(failed.id, decision=getattr(exc, "decision", {"reason": str(exc)}))
                        continue
                    repair_executor = repair_decision["executor_kind"] if repair_decision else producer.executor_kind
                    repair = self.store.create_task(title=self._execution_title(goal, source_plan), repository=goal.repository,
                        executor_kind=repair_executor,
                        binding_ref=repair_decision["binding_ref"] if repair_decision else producer.binding_ref,
                        model_profile_ref="" if repair_decision else producer.model_profile_ref,
                        branch=base if repair_executor in {"codex", "claude_code"} else "",
                        permission_profile=producer.permission_profile, policy_ref=producer.policy_ref,
                        idempotency_key=f"goal:{goal.id}:r{goal.revision}:{source_id}:review-round{len(rounds) + 2}:repair")
                    if repair_decision is not None:
                        self._record_model_selection(repair, repair_decision)
                    freeze_contract(self.store, repair, goal=goal, plan_task=source_plan, base_commit=base)
                    freeze_handoff_contract(self.store, repair, goal=goal, plan_task=source_plan, base_commit=base)
                    self.store._bind_artifact_evidence(repair.id, category="ReviewRepair", label=repair.execution_id,
                        document={"review_task_id": failed.id, "review_digest": model_review.digest(evidence),
                                  "findings": evidence["result"]["findings"], "producer": binding["producer"]})
                    self.control_store.escalate_goal_task(goal.id, goal_revision=goal.revision, plan_task_id=source_id,
                        from_task_id=producer.id, to_task_id=repair.id, from_role=source_plan.agent_role,
                        to_role=source_plan.agent_role, reason=f"model_review_repair:{failed.id}")
                    outcomes.append({"plan_task_id": source_id, "from_task_id": producer.id, "to_task_id": repair.id})
                    history = self.control_store.list_task_escalations(goal_id)
                if owns_transaction:
                    self.store._conn.execute("COMMIT")
            except BaseException:
                if owns_transaction:
                    self.store._conn.execute("ROLLBACK")
                raise
        self.control_store.refresh_goal_status(goal_id)
        return tuple(outcomes)

    def escalate_failed_tasks(self, goal_id: str) -> tuple[dict[str, Any], ...]:
        """Retry FAILED agent_team tasks by measured tier (legacy resolvers use roles).

        Only FAILED tasks escalate: BLOCKED (policy/blocker) and CANCELLED never do,
        and nothing escalates outside the Goal's still-active window. The failed task
        and its evidence stay in place; only the plan task's link moves on.
        """
        repairs = self._repair_rejected_reviews(goal_id)
        goal = self.control_store.get_goal(goal_id)
        if (goal.orchestration_mode != "agent_team" or not goal.window_id
                or (self.roster_resolver is None and self.task_resolver is None)):
            return repairs
        window = self.control_store.get_window(goal.window_id)
        if window.status != "ACTIVE" or not self.store._conn.execute(
                "SELECT 1 FROM platform_autonomous_windows WHERE id = ? AND julianday(starts_at) <= julianday('now') "
                "AND julianday(expires_at) > julianday('now')",
                (window.id,)).fetchone():
            return repairs
        history = self.control_store.list_task_escalations(goal_id)
        planned = {item.id: item for item in (self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks))}
        outcomes = list(repairs)
        if self.task_resolver is not None:
            outcomes.extend(self._reroute_quota_held(goal, planned))
        for link in self.control_store.list_goal_tasks(goal_id):
            if link["status"] != "FAILED" or int(link["goal_revision"]) != goal.revision:
                continue
            plan_task = planned.get(link["plan_task_id"])
            if plan_task is None or plan_task.validation_command_id:
                continue  # host validation is not model work; a stronger agent cannot fix it
            failed = self.store.get_task(link["task_id"])
            if _explicit_cleanup_uncertainty(failed):
                continue
            if self._review_intent_hold(failed, plan_task):
                continue  # FAILED over an unresolved reviewer call never authorizes a second call
            from .contract_recovery import failed_snapshot, KINDS, FIXUP, record_attempt_disposition
            from .artifact_handoff import _load_evidence
            structured = functional_evidence(failed)
            all_results = [row for row in failed.evidence_refs if row.get("category") == "FunctionalValidation"]
            rows = [row for row in all_results if row.get("value") == failed.validation_output_digest]
            if all_results and (not rows or structured.get("result_digest") != failed.validation_output_digest):
                continue
            miss = False
            if rows:
                try:
                    result = json.loads(rows[-1]["detail"])
                    miss = (structured.get("result_digest") == failed.validation_output_digest
                            and result.get("failure_kind") in KINDS)
                    if result.get("failure_kind") in KINDS and not miss:
                        continue
                    if result.get("failure_kind") == "check_timeout":
                        continue  # already re-run once on its explicit targets; never a capability signal
                except (ValueError, TypeError):
                    continue
            overloaded = not miss and failed.status == "FAILED" and transient_overload(
                failed.failure_classification, failed.failure_detail)
            if overloaded:
                transient = sum(row["plan_task_id"] == plan_task.id and row.get("reason") == "transient_overload"
                                for row in history)
                if transient >= MAX_TRANSIENT_RETRIES:
                    overloaded = False  # persistent overload: ordinary routing may move on
                else:
                    failed_at = _parse_utc(failed.updated_at)
                    wait = TRANSIENT_BACKOFF_SECONDS * (2 ** transient)
                    if failed_at is not None and time.time() < failed_at + wait:
                        continue  # backoff; a later tick retries without spending budget
                    snapshot = None
                    try:
                        from .contract_recovery import attempt_worktree, retain_interrupted_tree
                        worktree = attempt_worktree(self.store, failed)
                        if worktree is not None:
                            snapshot = retain_interrupted_tree(self.store, failed.id, worktree=worktree)
                    except (TaskStoreError, OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                        snapshot = None  # retried from the approved base when the tree is unavailable
            if miss:
                if any(row["plan_task_id"] == plan_task.id and row.get("reason") == "contract_fixup" for row in history):
                    record_attempt_disposition(self.store, failed, reused=False, snapshot_digest="")
                    continue
                try:
                    root = resolve_repository_workspace(failed.repository).repo_dir
                    snapshot = failed_snapshot(failed, root=root)
                except (TaskStoreError, OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                    continue
            model_review = (load_handoff_contract(failed) or {}).get("validation_mode") == "model_review"
            # Rejections belong to the verified repair loop above, including when
            # their evidence is invalid. An attempt without a verdict retries the
            # review itself and must never authorize a producer repair.
            if model_review and failed.failure_classification == "model_review_rejected":
                continue
            refusal = failed.failure_classification == "MODEL_REFUSED"
            # Durable executors store "MODEL_UNAVAILABLE:<marker>" (#1460).
            unavailable = (failed.failure_classification or "").split(":", 1)[0] == "MODEL_UNAVAILABLE"
            quota_failure = bool(LIMIT_HIT.search(failed.failure_classification or ""))
            if not miss and not overloaded and not model_review and not refusal and not unavailable and not quota_failure and _NON_AGENT_FAILURE.search(failed.failure_classification or ""):
                continue
            if self.control_store.can_complete_host_claim(window_id=window.id, task_id=failed.id):
                continue  # the claim is still being recovered and its reservation settled
            if len(history) >= window.max_retries:
                record_attempt_disposition(self.store, failed, reused=False, snapshot_digest="")
                if refusal or unavailable:
                    self.store.block_model_selection(failed.id, decision={"reason": "routing_retry_budget_exhausted",
                        "attempt_classification": failed.failure_classification})
                    self.control_store.refresh_goal_status(goal_id)
                break  # routing retries also remain inside the Owner's window budget
            previous = [row for row in history if row["plan_task_id"] == plan_task.id]
            role = previous[-1]["to_role"] if previous else (plan_task.agent_role or DEFAULT_AGENT_ROLE)
            decision = None
            if miss or overloaded:
                # Contract misses and provider overload are not capability failures:
                # the same model retries, never a weaker one.
                target = (role, failed.executor_kind, failed.binding_ref)
            elif self.task_resolver is not None:
                # Compare with the tier actually selected for this attempt, rather
                # than a tier that fresh failure evidence may already have lowered.
                selected = next((event.metadata for event in reversed(self.store.get_events(failed.id))
                                 if event.type == "MODEL_SELECTED"), {})
                failed_tier = selected.get("tier")
                if type(failed_tier) is not int or not 1 <= failed_tier <= 5:
                    failed_tier = None
                refused_models = []
                attempt_ids = [row["from_task_id"] for row in previous] + [failed.id]
                for attempt_id in attempt_ids:
                    attempt = self.store.get_task(attempt_id)
                    events = self.store.get_events(attempt_id)
                    if attempt.failure_classification != "MODEL_REFUSED" and not any(e.type == "MODEL_REFUSED" for e in events):
                        continue
                    for event in events:
                        if event.type == "MODEL_SELECTED":
                            model = event.metadata.get("model_id") or next((row.get("model_id")
                                for row in event.metadata.get("candidates", ())
                                if row.get("binding_id") == attempt.binding_ref), None)
                            if model:
                                refused_models.append(model)
                try:
                    retry_args = {"refused_models": refused_models} if refused_models else {}
                    retry_args.update(self._review_authors(plan_task, goal, planned))
                    decision = self.task_resolver(plan_task, goal=goal,
                                                  failed_binding="" if refusal or refused_models or unavailable else failed.binding_ref,
                                                  failed_tier=failed_tier if not unavailable else 0, **retry_args)
                except TaskStoreError as exc:
                    if str(exc) == "review_not_independent":
                        self.store.block_model_selection(failed.id, decision=getattr(exc, "decision", {"reason": str(exc)}))
                        self.control_store.refresh_goal_status(goal_id)
                        continue
                    if refusal and str(exc) in {"no_willing_model", "pinned_model_unavailable", "no_runnable_model"}:
                        self.store.block_refused_task(failed.id, refusals=refused_models, decision=getattr(exc, "decision", None))
                        self.control_store.refresh_goal_status(goal_id)
                        continue
                    if unavailable:
                        self.store.block_model_selection(failed.id, decision=getattr(exc, "decision", {"reason": str(exc)}))
                        self.control_store.refresh_goal_status(goal_id)
                        continue
                    self.store.add_event(failed.id, event_type="MODEL_SELECTION_FAILED",
                                         title="Escalation model selection failed",
                                         description=str(exc), metadata={"reason": str(exc)})
                    continue
                target = (role, decision["executor_kind"], decision["binding_ref"])
            elif refusal:
                continue  # legacy role-only routing has no refusal evidence
            elif quota_failure:
                # The account was out of quota, not the agent out of skill: the same role moves to the
                # stand-in the quota guard now picks, never up the ladder. No stand-in: stays BLOCKED.
                try:
                    executor_kind, binding_ref = self.roster_resolver(role)
                except TaskStoreError:
                    continue
                if binding_ref == failed.binding_ref:
                    continue
                target = (role, executor_kind, binding_ref)
            else:
                target = self._stronger_route(role, failed.binding_ref)
            if (target is None and failed.failure_classification == "deterministic_validation_failure"
                    and not any(str(row.get("reason", "")).startswith("failed:deterministic_validation_failure")
                                and row.get("from_role") == row.get("to_role") for row in previous)):
                # No stronger agent: the same one retries once, now seeing which checks failed
                # (functional_feedback reaches it through the context packet).
                target = (role, failed.executor_kind, failed.binding_ref)
            if target is None:
                continue  # no stronger distinct agent: the Goal stays BLOCKED for the Owner
            next_role, executor_kind, binding_ref = target
            step = len(previous) + 1
            native = executor_kind in {"codex", "claude_code"}
            try:
                base = self._approved_base(failed)
            except TaskStoreError:
                continue
            if not base and native:
                # The approved plan pinned no base (no checks, no handoff, no native
                # agent), so the failed attempt itself ran against the live HEAD.
                base = repository_base(goal.repository)
            if not miss and not (overloaded and snapshot is not None):
                record_attempt_disposition(self.store, failed, reused=False, snapshot_digest="")
            task = self.store.create_task(
                title=self._execution_title(goal, plan_task), repository=goal.repository,
                executor_kind=executor_kind, binding_ref=binding_ref,
                branch=base if native or miss or overloaded else "",
                permission_profile="AUTONOMOUS_WINDOW", policy_ref=window.policy_id,
                idempotency_key=f"goal:{goal.id}:r{goal.revision}:{plan_task.id}:e{step}",
                orchestration_mode="single",
            )
            if decision is None and (miss or overloaded):
                # The same binding retries: carry its selection evidence (context window,
                # context need, reservation) so the model-specific context check still applies.
                decision = next((event.metadata for event in reversed(self.store.get_events(failed.id))
                                 if event.type == "MODEL_SELECTED"
                                 and event.metadata.get("binding_ref") == failed.binding_ref), None)
            if decision is not None:
                self._record_model_selection(task, decision)
            freeze_contract(self.store, task, goal=goal, plan_task=plan_task, base_commit=base)
            freeze_required_artifacts(self.store, task, goal=goal, plan_task=plan_task)
            freeze_handoff_contract(self.store, task, goal=goal, plan_task=plan_task, base_commit=base)
            from .artifact_handoff import _load_evidence
            repair = _load_evidence(failed, "ReviewRepair", failed.execution_id)
            if repair is not None:
                self.store._bind_artifact_evidence(task.id, category="ReviewRepair", label=task.execution_id,
                                                 document=repair)
            if overloaded and snapshot is not None:
                from .functional_validation import digest
                self.store._bind_artifact_evidence(task.id, category=FIXUP, label=task.execution_id,
                    document={"task_id": task.id, "execution_id": task.execution_id,
                              "source_task_id": failed.id, "snapshot_digest": digest(snapshot),
                              "feedback": snapshot["feedback"]})
                record_attempt_disposition(self.store, failed, reused=True, snapshot_digest=digest(snapshot))
            if overloaded:
                # Events reach the context packet; evidence detail does not.
                self.store.add_event(task.id, event_type="VALIDATED", title="Retry after provider overload",
                                     description=(snapshot["feedback"] if snapshot is not None else
                                                  "The provider was at capacity; your previous attempt was cut "
                                                  "off and is not available. Start from the approved base."),
                                     metadata={"source_task_id": failed.id})
            if miss:
                from .functional_validation import digest
                self.store._bind_artifact_evidence(task.id, category=FIXUP, label=task.execution_id,
                    document={"task_id": task.id, "execution_id": task.execution_id,
                              "source_task_id": failed.id, "snapshot_digest": digest(snapshot),
                              "feedback": snapshot["feedback"]})
                self.store.add_event(task.id, event_type="VALIDATED", title="Contract fix-up required",
                                     description=snapshot["feedback"], metadata={"source_task_id": failed.id})
                record_attempt_disposition(self.store, failed, reused=True, snapshot_digest=digest(snapshot))
            reason = ("contract_fixup" if miss else "transient_overload" if overloaded
                      else f"failed:{failed.failure_classification or 'unknown'}")
            self.control_store.escalate_goal_task(
                goal.id, goal_revision=goal.revision, plan_task_id=plan_task.id, from_task_id=failed.id,
                to_task_id=task.id, from_role=role, to_role=next_role, reason=reason)
            history = (*history, {"plan_task_id": plan_task.id, "from_role": role, "to_role": next_role,
                                  "reason": reason})
            outcomes.append({"plan_task_id": plan_task.id, "from_task_id": failed.id, "to_task_id": task.id,
                             "from_role": role, "to_role": next_role, "step": step, "reason": reason})
        if outcomes:
            self.control_store.refresh_goal_status(goal_id)
        return tuple(outcomes)

    def _record_model_selection(self, task: Any, decision: Mapping[str, Any]) -> None:
        if any(event.type == "MODEL_SELECTED" for event in self.store.get_events(task.id)):
            return
        self.store.add_event(task.id, event_type="MODEL_SELECTED", title="Model selected",
                             description=f"{decision['binding_ref']}: {decision['reason']}", metadata=decision)

    @staticmethod
    def _approved_base(failed: Any) -> str:
        """The base the Goal's launch froze for this task, never the repository's current HEAD."""
        bases = {contract["base_commit"] for contract in (load_contract(failed), load_handoff_contract(failed))
                 if contract is not None}
        if failed.executor_kind in {"codex", "claude_code"} and re.fullmatch(r"[0-9a-f]{40}", failed.branch or ""):
            bases.add(failed.branch)
        if len(bases) > 1:
            raise TaskStoreError("escalation_base_ambiguous")
        return next(iter(bases), "")

    def _stronger_route(self, role: str, current_binding: str) -> tuple[str, str, str] | None:
        """Next role up the ladder whose agent differs from the one that failed."""
        next_role = ESCALATION_LADDER.get(role)
        while next_role is not None:
            try:
                executor_kind, binding_ref = self.roster_resolver(next_role)
            except TaskStoreError:
                executor_kind, binding_ref = "", ""
            if binding_ref and binding_ref != current_binding and executor_kind in {"opencode", "codex", "claude_code"}:
                return next_role, executor_kind, binding_ref
            next_role = ESCALATION_LADDER.get(next_role)
        return None

    def _freeze_host_validation(self, task: Any, goal: GoalRecord, plan_task: PlannedTask, window: Any) -> None:
        binding = self.control_store.window_policy_binding(window.id)
        authority = binding.get("authority", {})
        from .autonomy import bound_goal_admission
        admitted = bound_goal_admission(authority, goal)
        expected_key = admitted["idempotency_key"] if admitted else authority.get("goal_idempotency_key")
        if (not binding.get("canonical_policy") or not isinstance(authority, Mapping)
                or authority.get("plan_task_id") != plan_task.id
                or expected_key != goal.idempotency_key
                or "git_diff_check" not in authority.get("validation_command_ids", ())):
            raise TaskStoreError("host_validation_requires_bound_authority")
        workspace = resolve_repository_workspace(goal.repository)
        if workspace.repo_dir != Path(authority["workspace_path"]).resolve():
            raise TaskStoreError("host_validation_workspace_mismatch")
        contract = {"version": 1, "task_id": task.id, "repository": task.repository,
                    "goal_id": goal.id, "goal_revision": goal.revision,
                    "goal_artifact_digest": goal.artifact_digest, "plan_task_id": plan_task.id,
                    "capability": "validate_task", "validation_command_id": plan_task.validation_command_id,
                    "window_id": window.id, "policy_digest": window.policy_digest,
                    "workspace_path": str(workspace.repo_dir), "base_sha": authority["head_sha"],
                    "allowed_paths": list(authority["validation_paths"]),
                    "goal_idempotency_key": goal.idempotency_key}
        try:
            previous = load_host_validation_contract(self.store.get_task(task.id))
        except ExecutorRuntimeError as exc:
            raise TaskStoreError(str(exc)) from exc
        if previous is not None:
            if previous != contract:
                raise TaskStoreError("host_validation_contract_conflict")
            return
        detail = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        identity = hashlib.sha256(detail.encode("utf-8")).hexdigest()
        self.store.add_evidence(task.id, category=HOST_VALIDATION_CONTRACT, label="approved_host_check",
                                value=identity, status="APPROVED", detail=detail, raw_json_digest=identity)

    def list(self, *, limit: int = 100) -> list[dict[str, Any]]:
        goals = self.control_store.list_goals(limit=limit)
        payload: list[dict[str, Any]] = []
        for goal in goals:
            payload.append(self._response_snapshot(goal.id, forecast=False))
        return payload

    def list_page(self, *, limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
        goals, total, next_cursor = self.control_store.list_goals_page(limit=limit, cursor=cursor)
        return {
            "goals": [self._response_snapshot(goal.id, forecast=False) for goal in goals],
            "total": total,
            "next_cursor": next_cursor,
        }

    def detail(self, goal_id: str) -> dict[str, Any]:
        return self._response_snapshot(goal_id)

    def _response_snapshot(self, goal_id: str, *, forecast: bool = True) -> dict[str, Any]:
        """Build one coherent goal response after durable status reconciliation.

        The quota forecast routes every task across the whole binding catalog.
        Lists are polled, so they carry ``quota_fit: None``; the detail view
        caches forecasts by revision after the store lock is released. Polls
        overlapping a refresh return the previous same-revision forecast (or
        None on a cold cache) instead of waiting behind a slow forecast.
        """

        response, goal = self._locked_snapshot(goal_id)
        if forecast and goal.tasks:
            response["quota_fit"] = self._cached_quota_fit(goal)
        return response

    def _cached_quota_fit(self, goal: GoalRecord) -> dict[str, Any] | None:
        key = (goal.id, goal.revision)
        with self._forecast_lock:
            cached = self._forecast_cache.get(key)
            if cached is not None:
                self._forecast_cache.move_to_end(key)
            if (cached is not None and time.monotonic() - cached[0] < GOAL_FORECAST_TTL_SECONDS
                    or key in self._forecast_inflight):
                return deepcopy(cached[1]) if cached else None
            self._forecast_inflight.add(key)
        try:
            fit = dict(self._quota_fit(goal, self._normalize_tasks(goal.tasks)))
            fit["computed_at"] = time.time()
            with self._forecast_lock:
                self._forecast_cache[key] = (time.monotonic(), deepcopy(fit))
                self._forecast_cache.move_to_end(key)
                while len(self._forecast_cache) > _GOAL_FORECAST_CACHE_LIMIT:
                    self._forecast_cache.popitem(last=False)
            return fit
        finally:
            with self._forecast_lock:
                self._forecast_inflight.discard(key)

    def _locked_snapshot(self, goal_id: str) -> tuple[dict[str, Any], GoalRecord]:
        with self.store._lock:
            conn = self.store._conn
            owns_transaction = not conn.in_transaction
            if owns_transaction:
                # Reconciliation may update the Goal: obtain the write lock before
                # reading, including against other TaskStore connections.
                conn.execute("BEGIN IMMEDIATE")
            else:
                conn.execute("SAVEPOINT goal_response_snapshot")
            try:
                goal = self.control_store.refresh_goal_status(goal_id)
                links = [
                    self._task_link_evidence(goal, link)
                    for link in self.control_store.list_goal_tasks(goal_id)
                ]
                if links:
                    statuses = {str(link["status"]) for link in links}
                    status = ("COMPLETED" if statuses <= {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}
                              else "BLOCKED" if statuses & {"FAILED", "BLOCKED", "CANCELLED"}
                              else "RUNNING")
                    if status != goal.status:
                        # Preserve coherence if an enclosing in-process operation
                        # changed a Task during reconciliation on this connection.
                        goal = self.control_store.refresh_goal_status(goal_id)
                response = goal_to_dict(goal, links=links)
                response["quota_fit"] = None
                response["account_accounting"] = self.control_store.account_budget_summary(goal.window_id) if goal.window_id else {}
                conn.execute("COMMIT" if owns_transaction else "RELEASE goal_response_snapshot")
                return response, goal
            except BaseException:
                if owns_transaction:
                    conn.execute("ROLLBACK")
                else:
                    conn.execute("ROLLBACK TO goal_response_snapshot")
                    conn.execute("RELEASE goal_response_snapshot")
                raise

    def _task_link_evidence(self, goal: GoalRecord, link: Mapping[str, Any]) -> dict[str, Any]:
        task = self.store.get_task(str(link["task_id"]), event_limit=0)
        proof = functional_evidence(task)
        try:
            contract = load_contract(task)
            # In a multi-agent team each task runs on its role's executor, not the goal default.
            executor_matches = (task.executor_kind in {"opencode", "codex", "claude_code"}
                                if goal.orchestration_mode == "agent_team"
                                else task.executor_kind == goal.executor_kind)
            matches = (task.repository == goal.repository and executor_matches
                       and (contract is None or (
                           contract["goal_id"] == goal.id
                           and contract["goal_revision"] == goal.revision == link["goal_revision"]
                           and contract["goal_artifact_digest"] == goal.artifact_digest
                           and contract["plan_task_id"] == link["plan_task_id"])))
        except TaskStoreError:
            matches = False
        if not matches:
            proof = {"status": "UNVERIFIED", "verified": False,
                     "reason": "goal_functional_contract_mismatch"}
        publication = self.control_store.get_publication(task.id)
        if publication is not None and publication.repository != task.repository:
            publication = None
        blocked = ""
        if goal.window_id and publication is None and task.status == "READY_FOR_REVIEW":
            plan_task_id = str(link["plan_task_id"])
            blocked = publication_blocker(goal.tasks, plan_task_id)
            if not blocked and plan_task_id in published_plan_tasks(goal.tasks):
                try:
                    accepted = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
                except TaskStoreError:
                    accepted = None
                if accepted is None:
                    blocked = "functional_validation_not_accepted"
        return {
            **link, "executor_kind": task.executor_kind, "binding_ref": task.binding_ref,
            "functional_validation": proof,
            "publication": publication_projection(publication),
            # #1462: a finished task the host will not publish says why.
            "publication_blocked": blocked,
        }

    @staticmethod
    def _title_from_objective(objective: str) -> str:
        clean = re.sub(r"\s+", " ", objective).strip()
        return (clean[:77] + "...") if len(clean) > 80 else clean

    @staticmethod
    def _clean_lines(values: Sequence[str]) -> tuple[str, ...]:
        return tuple(str(value).strip() for value in values if str(value).strip())

    @staticmethod
    def _derive_acceptance(objective: str) -> tuple[str, ...]:
        return (
            f"The requested outcome is demonstrably delivered: {objective.strip()}",
            "Relevant deterministic checks pass on the exact implementation head.",
            "Changed paths and external operations remain inside the active policy.",
        )

    def _derive_tasks(self, goal: GoalRecord, criteria: Sequence[str]) -> tuple[PlannedTask, ...]:
        acceptance = "; ".join(criteria)
        return (
            PlannedTask(
                id="T001",
                title="Analyze, implement, and verify the goal",
                instruction=(
                    f"Inspect {goal.repository} and analyze this objective before editing: {goal.objective}. "
                    "Implement the smallest complete approved outcome by reusing mature repository capabilities "
                    "and preserving the existing architecture. Keep analysis, implementation, and verification "
                    "inside this same runtime Task and prepared worktree. Verify the exact implementation artifact "
                    "and diff produced by the coder; do not reconstruct or validate an independent repository "
                    "baseline. Run the relevant deterministic checks and produce reviewable evidence against these "
                    f"acceptance criteria: {acceptance}"
                ),
            ),
        )

    def _normalize_tasks(self, tasks: Sequence[Mapping[str, Any]]) -> tuple[PlannedTask, ...]:
        if not tasks or len(tasks) > 50:
            raise TaskStoreError("goal_tasks_count_invalid")
        result = tuple(self._normalize_task(item, seq=index) for index, item in enumerate(tasks))
        ids = {item.id for item in result}
        if len(ids) != len(result):
            raise TaskStoreError("duplicate_plan_task_id")
        for item in result:
            if item.id in item.dependencies or any(dep not in ids for dep in item.dependencies):
                raise TaskStoreError(f"invalid_plan_task_dependencies:{item.id}")
        graph = {item.id: item.dependencies for item in result}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise TaskStoreError("cyclic_plan_task_dependencies")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in graph[task_id]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)
        validate_plan_inputs(result)
        return result

    @staticmethod
    def _normalize_task(raw: Mapping[str, Any], *, seq: int) -> PlannedTask:
        task_id = str(raw.get("id", f"T{seq + 1:03d}")).strip()
        title = str(raw.get("title", "")).strip()
        instruction = str(raw.get("instruction", "")).strip()
        dependencies = tuple(str(value).strip() for value in raw.get("dependencies", ()) if str(value).strip())
        capability = str(raw.get("capability", "execute_task")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", task_id) or not title or not instruction:
            raise TaskStoreError("invalid_plan_task")
        if capability not in {"execute_task", "validate_task"}:
            raise TaskStoreError(f"unsupported_plan_task_capability:{capability}")
        checks = normalize_checks(raw.get("validation_checks", ()))
        artifact_input = normalize_input(raw.get("artifact_input"))
        command = raw.get("validation_command_id", "")
        if (not isinstance(command, str) or (command and
                (command != "git_diff_check" or capability != "validate_task" or artifact_input or checks))):
            raise TaskStoreError("unsupported_standalone_validation_command")
        required_artifacts = normalize_required_artifacts(raw.get("required_artifacts", ()))
        if required_artifacts and (capability != "execute_task" or checks or artifact_input or command):
            raise TaskStoreError("required_artifacts_require_standalone_execution")
        agent_role = str(raw.get("agent_role", "") or "").strip()
        if agent_role and agent_role not in AGENT_TASK_ROLES:
            raise TaskStoreError(f"unsupported_agent_role:{agent_role}")
        try:
            difficulty, kind = task_traits(raw)
            context_need, needs = requirements(raw)
        except ValueError as exc:
            raise TaskStoreError(str(exc)) from exc
        if kind == "review" or agent_role == "reviewer":
            if artifact_input is None:
                raise TaskStoreError("model_review_artifact_input_required")
            capability = "validate_task"
        return PlannedTask(
            id=task_id,
            title=title,
            instruction=instruction,
            dependencies=dependencies,
            capability=capability,
            validation_checks=checks,
            artifact_input=artifact_input,
            validation_command_id=command,
            agent_role=agent_role,
            difficulty=difficulty,
            kind=kind,
            context_need=context_need,
            needs=needs,
            required_artifacts=required_artifacts,
        )

    @staticmethod
    def _execution_title(goal: GoalRecord, task: PlannedTask) -> str:
        authorization = ("\n\nSecurity simulation scope: Owner-authorized research on locally hosted or open models "
                         "in the Owner research environment. No third-party system is targeted. "
                         "Perform only the authorized scope described below."
                         if "security_simulation" in task.needs else "")
        from .functional_validation import validation_guidance
        guidance = validation_guidance(task.validation_checks)
        validation = ("\n\nyour tests must be in exactly these files: " + ", ".join(guidance["targets"])
                      if guidance["targets"] else "")
        return f"[{goal.title}] {task.id} {task.title}{authorization}\n\n{task.instruction}{validation}"

    @staticmethod
    def _render_spec(goal: GoalRecord, criteria: Sequence[str]) -> str:
        acceptance = "\n".join(f"- {criterion}" for criterion in criteria)
        return (
            f"# Specification: {goal.title}\n\n"
            f"## Objective\n\n{goal.objective}\n\n"
            f"## Repository\n\n`{goal.repository}`\n\n"
            f"## Acceptance criteria\n\n{acceptance}\n"
        )

    def _quota_fit(self, goal, tasks):
        if self.quota_forecaster is None:
            return {"status": "UNKNOWN", "uncertain": True, "forecast_only": True,
                    "availability_guaranteed": False, "accounts": {}}
        return self.quota_forecaster(goal, tasks)

    @staticmethod
    def _render_plan(goal: GoalRecord, tasks: Sequence[PlannedTask], fit=None) -> str:
        lines = [f"# Plan: {goal.title}", "", "## Execution tasks", ""]
        for item in tasks:
            deps = ", ".join(item.dependencies) if item.dependencies else "none"
            lines.extend(
                [
                    f"### {item.id} — {item.title}",
                    "",
                    item.instruction,
                    "",
                    f"Dependencies: {deps}",
                    f"Capability: `{item.capability}`",
                    f"Difficulty: {item.difficulty}; kind: `{item.kind}`",
                    *([f"Host check: `{item.validation_command_id}` (patch hygiene only)"]
                      if item.validation_command_id else []),
                    "Functional checks: " + (", ".join(
                        f"`{check['profile_id']}` in `{check['working_directory']}`"
                        + (" on " + ", ".join(f"`{target}`" for target in check["targets"]) if check.get("targets") else "")
                        for check in item.validation_checks
                    ) or "not selected (patch hygiene alone is not functional verification)"),
                    *([f"Required review output: `{v['path']}` exact `{v['expected_sha']}`"
                       for v in item.required_artifacts]),
                    *([f"Accepted artifact input: `{item.artifact_input['plan_task_id']}`"]
                      if item.artifact_input else []),
                    "",
                ]
            )
        if fit is not None:
            lines.extend(["## Quota fit forecast", "", "Read-only forecast; no capacity reserved or future availability promised.",
                          "", "```json", json.dumps(fit, sort_keys=True), "```", ""])
        return "\n".join(lines)

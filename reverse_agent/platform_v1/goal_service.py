"""Persistent Goal -> Spec -> Plan -> Tasks workflow for Platform V2.

The artifact layout follows GitHub Spec Kit's separation of specification,
plan and executable tasks while retaining the existing TaskStore as execution
truth.  Planning is deterministic and editable; it makes no model call.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import json
import hashlib
from pathlib import Path
import shutil
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
from .run_read_model import publication_projection
from .artifact_handoff import freeze_handoff_contract, normalize_input, validate_plan_inputs
from .task_runtime import HOST_VALIDATION_CONTRACT, ExecutorRuntimeError, load_host_validation_contract


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


@dataclass(frozen=True)
class GoalPlan:
    goal: GoalRecord
    planner: str
    spec_kit_available: bool


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

    def __init__(self, *, store: TaskStore, control_store: PlatformControlStore) -> None:
        self.store = store
        self.control_store = control_store

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
            orchestration_mode=str(payload.get("orchestration_mode", "sequential_team")),
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
        plan = self._render_plan(goal, planned)
        saved = self.control_store.save_goal_plan(
            goal_id,
            expected_revision=expected_revision,
            spec_markdown=spec,
            plan_markdown=plan,
            tasks=tuple(asdict(item) for item in planned),
            acceptance_criteria=criteria,
        )
        return GoalPlan(
            goal=saved,
            planner="spec-kit-compatible/deterministic",
            spec_kit_available=shutil.which("specify") is not None,
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
                self._launch(goal_id, expected_revision=goal.revision, window_id=window_id)
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

    def _launch(self, goal_id: str, *, expected_revision: int, window_id: str) -> GoalRecord:
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
        planned_tasks = tuple(self._normalize_task(raw, seq=seq) for seq, raw in enumerate(goal.tasks))
        for item in planned_tasks:
            if item.capability not in window.capabilities:
                raise TaskStoreError(f"goal_window_missing_{item.capability}_capability")
            if item.validation_command_id and (goal.orchestration_mode != "single" or item.artifact_input
                                               or item.validation_checks):
                raise TaskStoreError("host_validation_requires_standalone_single_task")
        if goal.executor_kind == "opencode":
            try:
                resolve_repository_workspace(goal.repository)
            except RepositoryWorkspaceError as exc:
                raise TaskStoreError(
                    str(exc)
                )

        functional_base = repository_base(goal.repository) if any(
            raw.get("validation_checks") for raw in goal.tasks
        ) else ""
        for seq, raw in enumerate(goal.tasks):
            plan_task = self._normalize_task(raw, seq=seq)
            task = self.store.create_task(
                title=self._execution_title(goal, plan_task),
                repository=goal.repository,
                executor_kind=goal.executor_kind,
                binding_ref=goal.binding_ref,
                permission_profile="AUTONOMOUS_WINDOW",
                policy_ref=window.id if plan_task.validation_command_id else window.policy_id,
                idempotency_key=f"goal:{goal.id}:r{goal.revision}:{plan_task.id}",
                orchestration_mode=goal.orchestration_mode,
            )
            freeze_contract(self.store, task, goal=goal, plan_task=plan_task, base_commit=functional_base)
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
        return self.control_store.mark_goal_running(
            goal.id, revision=goal.revision, window_id=window_id
        )

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
            payload.append(self._response_snapshot(goal.id))
        return payload

    def list_page(self, *, limit: int = 100, cursor: str | None = None) -> dict[str, Any]:
        goals, total, next_cursor = self.control_store.list_goals_page(limit=limit, cursor=cursor)
        return {
            "goals": [self._response_snapshot(goal.id) for goal in goals],
            "total": total,
            "next_cursor": next_cursor,
        }

    def detail(self, goal_id: str) -> dict[str, Any]:
        return self._response_snapshot(goal_id)

    def _response_snapshot(self, goal_id: str) -> dict[str, Any]:
        """Build one coherent goal response after durable status reconciliation."""

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
                conn.execute("COMMIT" if owns_transaction else "RELEASE goal_response_snapshot")
                return response
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
            matches = (task.repository == goal.repository and task.executor_kind == goal.executor_kind
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
        return {
            **link, "executor_kind": task.executor_kind,
            "functional_validation": proof,
            "publication": publication_projection(publication),
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
        return PlannedTask(task_id, title, instruction, dependencies, capability, checks, artifact_input, command)

    @staticmethod
    def _execution_title(goal: GoalRecord, task: PlannedTask) -> str:
        return f"[{goal.title}] {task.id} {task.title}\n\n{task.instruction}"

    @staticmethod
    def _render_spec(goal: GoalRecord, criteria: Sequence[str]) -> str:
        acceptance = "\n".join(f"- {criterion}" for criterion in criteria)
        return (
            f"# Specification: {goal.title}\n\n"
            f"## Objective\n\n{goal.objective}\n\n"
            f"## Repository\n\n`{goal.repository}`\n\n"
            f"## Acceptance criteria\n\n{acceptance}\n"
        )

    @staticmethod
    def _render_plan(goal: GoalRecord, tasks: Sequence[PlannedTask]) -> str:
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
                    *([f"Host check: `{item.validation_command_id}` (patch hygiene only)"]
                      if item.validation_command_id else []),
                    "Functional checks: " + (", ".join(
                        f"`{check['profile_id']}` in `{check['working_directory']}`" for check in item.validation_checks
                    ) or "not selected (patch hygiene alone is not functional verification)"),
                    *([f"Accepted artifact input: `{item.artifact_input['plan_task_id']}`"]
                      if item.artifact_input else []),
                    "",
                ]
            )
        return "\n".join(lines)

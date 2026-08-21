"""Persistent Goal -> Spec -> Plan -> Tasks workflow for Platform V2.

The artifact layout follows GitHub Spec Kit's separation of specification,
plan and executable tasks while retaining the existing TaskStore as execution
truth.  Planning is deterministic and editable; it makes no model call.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import shutil
from typing import Any, Mapping, Sequence

from .control_store import GoalRecord, PlatformControlStore, reject_sensitive_keys
from .run_store import TaskStore, TaskStoreError


@dataclass(frozen=True)
class PlannedTask:
    id: str
    title: str
    instruction: str
    dependencies: tuple[str, ...] = ()
    capability: str = "execute_task"


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

    def amend(self, goal_id: str, *, expected_revision: int, objective: str) -> GoalRecord:
        return self.control_store.amend_goal(
            goal_id, expected_revision=expected_revision, objective=objective
        )

    def launch(self, goal_id: str, *, expected_revision: int, window_id: str) -> GoalRecord:
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
        if "execute_task" not in window.capabilities:
            raise TaskStoreError("goal_window_missing_execute_task_capability")

        for seq, raw in enumerate(goal.tasks):
            plan_task = self._normalize_task(raw, seq=seq)
            task = self.store.create_task(
                title=self._execution_title(goal, plan_task),
                repository=goal.repository,
                executor_kind=goal.executor_kind,
                binding_ref=goal.binding_ref,
                permission_profile="AUTONOMOUS_WINDOW",
                policy_ref=window.policy_id,
                idempotency_key=f"goal:{goal.id}:r{goal.revision}:{plan_task.id}",
                orchestration_mode=goal.orchestration_mode,
            )
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

    def list(self, *, limit: int = 100) -> list[dict[str, Any]]:
        goals = self.control_store.list_goals(limit=limit)
        payload: list[dict[str, Any]] = []
        for goal in goals:
            links = self.control_store.list_goal_tasks(goal.id)
            refreshed = self.control_store.refresh_goal_status(goal.id)
            payload.append(goal_to_dict(refreshed, links=links))
        return payload

    def detail(self, goal_id: str) -> dict[str, Any]:
        goal = self.control_store.refresh_goal_status(goal_id)
        return goal_to_dict(goal, links=self.control_store.list_goal_tasks(goal_id))

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
        return (
            PlannedTask(
                id="T001",
                title="Analyze the goal and repository",
                instruction=(
                    f"Inspect {goal.repository} and turn this objective into a bounded implementation approach: "
                    f"{goal.objective}. Preserve existing architecture and record assumptions."
                ),
            ),
            PlannedTask(
                id="T002",
                title="Implement the approved outcome",
                instruction=(
                    f"Implement the smallest complete change for: {goal.objective}. "
                    "Reuse mature repository capabilities and keep changes reviewable."
                ),
                dependencies=("T001",),
            ),
            PlannedTask(
                id="T003",
                title="Verify and prepare evidence",
                instruction=(
                    "Run the relevant deterministic checks, review the exact diff, and produce evidence for: "
                    + "; ".join(criteria)
                ),
                dependencies=("T002",),
                capability="validate_task",
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
        return PlannedTask(task_id, title, instruction, dependencies, capability)

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
                    "",
                ]
            )
        return "\n".join(lines)

"""Project overview: one read-only facade over Goals, windows and Agent Runs.

The coordinator is a role over durable records, not a chat (#1286 §4.1). This
module answers "what is running, what is waiting, and what needs the Owner"
from the existing TaskStore and control-store rows only. It never writes,
never reconciles, never expires a window and grants no authority: an expired
window that the store has not yet marked EXPIRED is reported as expired here
without being changed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .control_store import AutonomousWindowRecord, GoalRecord, PlatformControlStore
from .run_read_model import STALE_AFTER_SECONDS, RunReadModel
from .run_store import TaskStore, TaskStoreError

MAX_GOALS = 100
MAX_TASKS_PER_GOAL = 100

TASK_STATES = frozenset({
    "queued", "waiting_dependencies", "waiting_window", "running", "validating",
    "ready_for_review", "blocked", "failed", "stale", "unknown",
})
OWNER_ACTIONS = frozenset({
    "plan_goal", "approve_plan", "launch_goal", "renew_window",
    "review_result", "resolve_blocked_task", "resume_task", "inspect_stale_task",
})
_DONE = frozenset({"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"})
_TERMINAL = _DONE | {"FAILED", "CANCELLED"}


def _parse(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def window_state(window: AutonomousWindowRecord, now: datetime) -> str:
    """Effective window state; ``ACTIVE`` past its expiry reads as ``EXPIRED``."""
    if window.status != "ACTIVE":
        return window.status
    starts, expires = _parse(window.starts_at), _parse(window.expires_at)
    if expires is not None and expires <= now:
        return "EXPIRED"
    if starts is not None and starts > now:
        return "PENDING"
    return "ACTIVE"


def task_state(run: Mapping[str, Any], *, dependencies_met: bool, window_active: bool) -> str:
    status = str(run.get("status", ""))
    liveness = str(run.get("liveness", ""))
    if status in _DONE:
        return "ready_for_review"
    if status == "BLOCKED":
        return "blocked"
    if status in {"FAILED", "CANCELLED"}:
        return "failed"
    if liveness == "STALE":
        return "stale"
    if status == "QUEUED":
        if not dependencies_met:
            return "waiting_dependencies"
        return "queued" if window_active else "waiting_window"
    if status == "VALIDATING":
        return "validating"
    if liveness in {"ACTIVE", "WAITING"} and status in {"PREPARING_WORKSPACE", "RUNNING", "RUNNING_FIXTURE"}:
        return "running"
    return "unknown"


class ProjectOverview:
    """Derived project summary; read-only by construction."""

    def __init__(
        self,
        *,
        store: TaskStore,
        control_store: PlatformControlStore,
        clock: Callable[[], datetime] | None = None,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
    ) -> None:
        self.store = store
        self.control_store = control_store
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._runs = RunReadModel(
            store=store, control_store=control_store, clock=self._clock,
            stale_after_seconds=stale_after_seconds,
        )

    def overview(self, *, limit: int = MAX_GOALS) -> dict[str, Any]:
        now = self._clock().astimezone(timezone.utc)
        goals = self.control_store.list_goals(limit=max(1, min(limit, MAX_GOALS)))
        summaries = [self.goal_summary(goal, now=now) for goal in goals]
        owner_actions = [action for summary in summaries for action in summary["owner_actions"]]
        task_counts: dict[str, int] = {}
        for summary in summaries:
            for state, count in summary["task_counts"].items():
                task_counts[state] = task_counts.get(state, 0) + count
        return {
            "authority": "NONE",
            "generated_at": now.isoformat().replace("+00:00", "Z"),
            "goals": summaries,
            "goal_counts": _count(summary["status"] for summary in summaries),
            "task_counts": dict(sorted(task_counts.items())),
            "owner_actions": owner_actions,
        }

    def goal_summary(self, goal: GoalRecord, *, now: datetime | None = None) -> dict[str, Any]:
        now = (now or self._clock()).astimezone(timezone.utc)
        window = self._window(goal.window_id)
        effective_window = window_state(window, now) if window is not None else ""
        window_active = effective_window == "ACTIVE"
        all_links = self.control_store.list_goal_tasks(goal.id)
        done_plan_ids = {str(link["plan_task_id"]) for link in all_links if link["status"] in _DONE}
        links = all_links[:MAX_TASKS_PER_GOAL]
        tasks = []
        for link in links:
            try:
                run = self._runs.run_detail(str(link["task_id"]))
            except TaskStoreError:
                continue
            dependencies = tuple(str(item) for item in link["dependencies"])
            state = task_state(
                run, dependencies_met=set(dependencies) <= done_plan_ids, window_active=window_active,
            )
            tasks.append({
                "task_id": run["task_id"],
                "plan_task_id": str(link["plan_task_id"]),
                "title": run["title"],
                "status": run["status"],
                "state": state,
                "liveness": run["liveness"],
                "stage": run["stage"],
                "dependencies": list(dependencies),
                "resume": run["controls"]["resume"]["availability"],
                "publication": run["publication"],
                "usage": run["usage"],
            })
        unfinished = any(task["status"] not in _TERMINAL for task in tasks)
        return {
            "goal_id": goal.id,
            "title": goal.title,
            "repository": goal.repository,
            "status": goal.status,
            "revision": goal.revision,
            "window": None if window is None else {
                "window_id": window.id,
                "status": window.status,
                "effective_status": effective_window,
                "expires_at": window.expires_at,
                "max_concurrent_tasks": window.max_concurrent_tasks,
                "tasks_started": window.tasks_started,
                "max_tasks": window.max_tasks,
                "budget": self.control_store.window_budget_summary(window.id),
            },
            "tasks": tasks,
            "task_counts": _count(task["state"] for task in tasks),
            "escalations": len(self.control_store.list_task_escalations(goal.id)),
            "owner_actions": _owner_actions(goal, tasks, effective_window, unfinished),
        }

    def _window(self, window_id: str) -> AutonomousWindowRecord | None:
        if not window_id:
            return None
        try:
            return self.control_store.get_window(window_id)
        except TaskStoreError:
            return None


def _count(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _owner_actions(
    goal: GoalRecord, tasks: Sequence[Mapping[str, Any]], effective_window: str, unfinished: bool,
) -> list[dict[str, str]]:
    def action(kind: str, task_id: str = "", reason: str = "") -> dict[str, str]:
        return {"action": kind, "goal_id": goal.id, "task_id": task_id, "reason": reason}

    if goal.status == "DRAFT":
        return [action("plan_goal")]
    if goal.status == "PLANNED":
        return [action("approve_plan")]
    if goal.status == "APPROVED":
        return [action("launch_goal")]
    actions = []
    if goal.status == "RUNNING" and unfinished and effective_window != "ACTIVE":
        actions.append(action("renew_window", reason=effective_window.lower() or "no_window"))
    for task in tasks:
        state = task["state"]
        if state == "ready_for_review":
            actions.append(action("review_result", task["task_id"]))
        elif state in {"blocked", "failed"}:
            actions.append(action("resolve_blocked_task", task["task_id"], reason=task["status"].lower()))
        elif state == "stale":
            kind = "resume_task" if task["resume"] == "AVAILABLE" else "inspect_stale_task"
            actions.append(action(kind, task["task_id"]))
    return actions

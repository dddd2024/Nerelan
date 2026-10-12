"""Planner agent: decompose a Goal into role-tagged tasks for the Agent team.

The planner role's agent (a native CLI executor: Claude Code or Codex) runs
read-only in the configured repository and must answer with one JSON object.
That plan then goes through the ordinary GoalService validation, so a
malformed or out-of-policy plan is rejected exactly like a hand-written one.
Planning runs as a background job because it can take minutes; callers poll
its status. The job never launches anything: the Goal only becomes PLANNED,
and the Owner still reviews, edits and approves it.
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .run_store import TaskStoreError

ROLE_GUIDE = {
    "planner": "decomposition and design only (expensive; avoid for implementation)",
    "complex": "architecture-level or multi-file changes that need strong reasoning",
    "coder": "ordinary feature work and bug fixes",
    "simple": "documentation, tests, small mechanical edits (cheapest)",
    "reviewer": "review of another task's result (use for explicit review tasks only)",
}
MAX_PLAN_TASKS = 12
PLAN_TIMEOUT_SECONDS = 600


def build_planner_prompt(*, objective: str, repository: str) -> str:
    roles = "\n".join(f"- {name}: {purpose}" for name, purpose in ROLE_GUIDE.items())
    return (
        "You are the planner of a multi-agent software team. Read the repository in the current "
        "directory (read-only) and decompose the objective into a small set of concrete tasks. "
        "Assign each task the cheapest role that can do it well, so most work goes to cheaper agents.\n\n"
        f"Repository: {repository}\nObjective: {objective}\n\nRoles:\n{roles}\n\n"
        "Rules: at most " + str(MAX_PLAN_TASKS) + " tasks; ids T001, T002, ...; dependencies reference "
        "earlier ids only; each instruction is self-contained (the agent sees only its own task); do not "
        "plan commits, pushes, releases or dependency installs.\n\n"
        "Answer with exactly one JSON object and nothing else:\n"
        '{"tasks": [{"id": "T001", "title": "...", "instruction": "...", "agent_role": "coder", '
        '"dependencies": []}], "acceptance_criteria": ["..."]}'
    )


def extract_plan(text: str) -> dict[str, Any]:
    """Parse the planner's single JSON object (tolerating a fenced code block)."""
    if not isinstance(text, str) or not text.strip():
        raise TaskStoreError("agent_plan_empty")
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    elif not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise TaskStoreError("agent_plan_not_json")
        candidate = candidate[start:end + 1]
    try:
        plan = json.loads(candidate)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise TaskStoreError("agent_plan_not_json") from exc
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list) or not plan["tasks"]:
        raise TaskStoreError("agent_plan_tasks_required")
    if len(plan["tasks"]) > MAX_PLAN_TASKS:
        raise TaskStoreError("agent_plan_too_many_tasks")
    allowed = {"id", "title", "instruction", "agent_role", "dependencies"}
    tasks = []
    for raw in plan["tasks"]:
        if not isinstance(raw, dict):
            raise TaskStoreError("agent_plan_task_invalid")
        # Only plain fields: a planner cannot request host checks, artifacts or capabilities.
        tasks.append({key: raw[key] for key in allowed if key in raw})
    criteria = plan.get("acceptance_criteria", [])
    if not isinstance(criteria, list) or not all(isinstance(item, str) for item in criteria):
        raise TaskStoreError("agent_plan_criteria_invalid")
    return {"tasks": tasks, "acceptance_criteria": criteria[:20]}


def run_planner_cli(*, executor_kind: str, model_id: str, repo_dir: str, prompt: str,
                    timeout: float = PLAN_TIMEOUT_SECONDS, executor_factory: Callable[..., Any] | None = None) -> str:
    """Run the planner read-only in the source repository; return its final text."""
    from .codex_executor import CodexExecutor, CodexPreparedContext
    from .claude_executor import ClaudeCodeExecutor
    classes = {"claude_code": ClaudeCodeExecutor, "codex": CodexExecutor}
    if executor_kind not in classes:
        raise TaskStoreError("agent_planner_requires_native_executor")
    factory = executor_factory or classes[executor_kind]
    executor = factory(model_id=model_id, repo_dir=repo_dir, timeout=min(timeout, 600), sandbox="read-only")
    cli = executor._resolve_cli()
    if executor._readiness_probe(cli) != "managed_login_ready":
        raise TaskStoreError(f"{executor_kind}_managed_login_unavailable")
    # Read-only: no worktree is prepared and no host checks run; the repo is only read.
    prepared = CodexPreparedContext(Path(repo_dir).resolve(), "", f"plan-{int(time.time())}", cli, executor.KIND)
    parser = executor._parser(None)
    code = executor._stream(prepared, prompt, parser)
    turn = parser.finish()
    if code != 0 or turn.failed:
        raise TaskStoreError(turn.failure_classification or f"{executor_kind}_planner_failed")
    return turn.final_text


@dataclass
class PlanJob:
    goal_id: str
    status: str = "RUNNING"  # RUNNING | PLANNED | FAILED
    error: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    planner: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"goal_id": self.goal_id, "status": self.status, "error": self.error,
                "started_at": self.started_at, "finished_at": self.finished_at, "planner": dict(self.planner)}


class AgentPlanner:
    """Process-local registry of background planning jobs (one per Goal)."""

    def __init__(self, *, goal_service: Any, roster_resolver: Callable[[str], tuple[str, str]],
                 binding_model: Callable[[str], str], repo_dir_for: Callable[[str], str],
                 runner: Callable[..., str] = run_planner_cli) -> None:
        self._goals = goal_service
        self._roster = roster_resolver
        self._binding_model = binding_model
        self._repo_dir_for = repo_dir_for
        self._runner = runner
        self._jobs: dict[str, PlanJob] = {}
        self._lock = threading.Lock()

    def status(self, goal_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(goal_id)
            return job.to_dict() if job else {"goal_id": goal_id, "status": "NONE", "error": ""}

    def start(self, goal_id: str, *, expected_revision: int, background: bool = True) -> dict[str, Any]:
        goal = self._goals.control_store.get_goal(goal_id)
        if goal.revision != expected_revision:
            raise TaskStoreError("goal_revision_mismatch")
        if goal.status not in {"DRAFT", "PLANNED"}:
            raise TaskStoreError("goal_not_plannable")
        if goal.orchestration_mode != "agent_team":
            raise TaskStoreError("agent_planner_requires_agent_team_goal")
        executor_kind, binding_ref = self._roster("planner")
        if executor_kind not in {"claude_code", "codex"}:
            raise TaskStoreError("agent_planner_requires_native_executor")
        with self._lock:
            current = self._jobs.get(goal_id)
            if current is not None and current.status == "RUNNING":
                return current.to_dict()
            job = PlanJob(goal_id, planner={"executor_kind": executor_kind, "binding_ref": binding_ref})
            self._jobs[goal_id] = job
        work = lambda: self._run(job, goal, executor_kind, binding_ref)  # noqa: E731
        if background:
            threading.Thread(target=work, name=f"agent-plan-{goal_id}", daemon=True).start()
        else:
            work()
        return self.status(goal_id)

    def _run(self, job: PlanJob, goal: Any, executor_kind: str, binding_ref: str) -> None:
        try:
            text = self._runner(executor_kind=executor_kind, model_id=self._binding_model(binding_ref),
                                repo_dir=self._repo_dir_for(goal.repository),
                                prompt=build_planner_prompt(objective=goal.objective, repository=goal.repository))
            plan = extract_plan(text)
            current = self._goals.control_store.get_goal(goal.id)
            # DRAFT -> PLANNED keeps the revision, so also compare status and plan digest:
            # a plan the Owner saved while the planner ran is never overwritten.
            if (current.revision, current.status, current.artifact_digest) != (
                    goal.revision, goal.status, goal.artifact_digest):
                raise TaskStoreError("goal_changed_during_planning")
            self._goals.plan(goal.id, expected_revision=goal.revision, tasks=plan["tasks"],
                             acceptance_criteria=plan["acceptance_criteria"])
            outcome, error = "PLANNED", ""
        except TaskStoreError as exc:
            outcome, error = "FAILED", str(exc)[:200]
        except Exception as exc:  # noqa: BLE001 - surface any planner failure as a finite code
            outcome, error = "FAILED", f"agent_planner_error:{type(exc).__name__}"
        with self._lock:
            job.status, job.error, job.finished_at = outcome, error, time.time()


def planner_status_payload(planner: AgentPlanner | None, goal_id: str) -> Mapping[str, Any]:
    if planner is None:
        return {"goal_id": goal_id, "status": "UNAVAILABLE", "error": "agent_planner_unavailable"}
    return planner.status(goal_id)

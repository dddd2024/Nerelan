"""Planner agent: decompose a Goal into difficulty-tagged tasks for the Agent team.

The planner role's agent (a native CLI executor: Claude Code or Codex) runs
read-only in a disposable detached worktree and must answer with one JSON object.
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

from .functional_validation import _CATALOG as _CHECK_CATALOG
from .model_router import task_traits
from .routing_inputs import requirements
from .opencode_executor import redact_secrets
from .run_store import TaskStoreError
from .task_runtime import ExecutorRuntimeError
from . import repository_preparation

ROLE_GUIDE = {
    "planner": "decomposition and design only (expensive; avoid for implementation)",
    "complex": "architecture-level or multi-file changes that need strong reasoning",
    "coder": "ordinary feature work and bug fixes",
    "simple": "documentation, tests, small mechanical edits (cheapest)",
    "reviewer": ("review of another task's result (use for explicit review tasks only); it reads and runs "
                 "checks but never modifies files, and must take that task's result as artifact_input"),
}
MAX_PLAN_TASKS = 12
# Approved host-run functional check profiles a planner may attach (see functional_validation).
CHECK_PROFILES = ("python_pytest", "npm_test")
PLAN_TIMEOUT_SECONDS = 600


CHECK_TIMEOUT_SECONDS = min(profile["timeout_seconds"] for profile in _CHECK_CATALOG.values())


def build_planner_prompt(*, objective: str, repository: str) -> str:
    roles = "\n".join(f"- {name}: {purpose}" for name, purpose in ROLE_GUIDE.items())
    return (
        "You are the planner of a multi-agent software team. Read the repository in the current "
        "directory (read-only) and decompose the objective into a small set of concrete tasks. "
        "Assign every task difficulty (integer 1-5) and kind (code, analysis, writing, research_design, review). "
        "Also estimate context_need (input tokens for files/data) and needs (a subset of long_context, "
        "tool_use, vision, security_simulation, chinese, low_latency). security_simulation is only "
        "Owner-authorized local/open-model research in the Owner lab, never third-party systems. "
        "Difficulty: 1 trivial edit/format; 2 small single-file change or short summary; "
        "3 normal feature/bug fix or data analysis; 4 multi-file design, subtle bug or experiment design; "
        "5 hard reasoning, architecture or research judgement.\n\n"
        f"Repository: {repository}\nObjective: {objective}\n\nLegacy roles (optional):\n{roles}\n\n"
        "Rules: at most " + str(MAX_PLAN_TASKS) + " tasks; ids T001, T002, ...; dependencies reference "
        "earlier ids only; each instruction is self-contained (the agent sees only its own task); do not "
        "plan commits, pushes, releases or dependency installs.\n"
        "Every task with kind=review or agent_role=reviewer must declare artifact_input; "
        "it performs a model review of that artifact, with host checks as separate evidence. "
        "Dependencies only order tasks; each task starts from the approved base and cannot see another "
        "task's changes. When a task must build on a predecessor's changes, set "
        '"artifact_input": {"plan_task_id": "<that dependency id>"} (exactly one, and it must be listed in '
        "dependencies), and give BOTH tasks \"validation_checks\" chosen from: "
        + ", ".join(CHECK_PROFILES) + ' as [{"profile_id": "...", "working_directory": "."}]. '
        "A python_pytest check without targets runs the whole suite under working_directory, which is "
        "usually too slow; list the test files that cover the task as \"targets\" (paths relative to "
        'working_directory, up to 16), e.g. {"profile_id": "python_pytest", "working_directory": ".", '
        '"targets": ["tests/test_feature.py"]}. A target must exist when the check runs, so a task that '
        "creates a test file may target it, but its predecessor must target tests that already exist. "
        "Each check must finish within " + str(CHECK_TIMEOUT_SECONDS) + " seconds, so choose a few fast, "
        "focused test files (unit tests for the modules the task changes), not large integration suites. "
        "Prefer independent tasks when they do not need each other's output.\n\n"
        "Answer with exactly one JSON object and nothing else:\n"
        '{"tasks": [{"id": "T001", "title": "...", "instruction": "...", "difficulty": 3, "kind": "code", '
        '"dependencies": [], "validation_checks": [{"profile_id": "python_pytest", "working_directory": ".", '
        '"targets": ["tests/test_existing.py"]}]}, '
        '{"id": "T002", "title": "...", "instruction": "...", "difficulty": 2, "kind": "code", "dependencies": ["T001"], '
        '"artifact_input": {"plan_task_id": "T001"}, '
        '"validation_checks": [{"profile_id": "python_pytest", "working_directory": ".", '
        '"targets": ["tests/test_new_feature.py"]}]}], '
        '"acceptance_criteria": ["..."]}'
    )


def _parse_plan_object(text: str) -> Any:
    """Locate and parse the planner's single JSON object.

    Tolerates a fenced code block and leading/trailing prose. If the fenced-block
    regex or the first-'{'..last-'}' slice fails to parse (often because trailing
    prose added stray braces), scan each '{' that starts a line and raw_decode
    until one yields an object with a 'tasks' list.
    """
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
        return json.loads(candidate)
    except (json.JSONDecodeError, RecursionError):
        pass
    # The slice captured stray braces from surrounding prose; decode from each
    # line-start '{' and keep the first object that looks like a plan.
    decoder = json.JSONDecoder()
    for match in re.finditer(r"(?m)^[ \t]*\{", text):
        try:
            obj, _ = decoder.raw_decode(text, match.end() - 1)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get("tasks"), list) and obj["tasks"]:
            return obj
    raise TaskStoreError("agent_plan_not_json")


def extract_plan(text: str) -> dict[str, Any]:
    """Parse the planner's single JSON object (tolerating a fenced code block)."""
    if not isinstance(text, str) or not text.strip():
        raise TaskStoreError("agent_plan_empty")
    plan = _parse_plan_object(text)
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list) or not plan["tasks"]:
        raise TaskStoreError("agent_plan_tasks_required")
    if len(plan["tasks"]) > MAX_PLAN_TASKS:
        raise TaskStoreError("agent_plan_too_many_tasks")
    # Approved checks and predecessor artifacts let a chain build on earlier work; GoalService
    # validation still requires catalog profiles and an artifact from a declared dependency.
    allowed = {"id", "title", "instruction", "agent_role", "difficulty", "kind", "dependencies",
               "validation_checks", "artifact_input", "context_need", "needs"}
    tasks = []
    for raw in plan["tasks"]:
        if not isinstance(raw, dict):
            raise TaskStoreError("agent_plan_task_invalid")
        # Capabilities and host validation commands are never taken from a planner. A review
        # validates its input artifact without changing it, so reviewer tasks are derived as
        # validate_task (the host rejects any tree change); everything else stays execute_task.
        task = {key: raw[key] for key in allowed if key in raw}
        try:
            task["difficulty"], task["kind"] = task_traits(task)
            task["context_need"], task["needs"] = requirements(task)
        except ValueError as exc:
            raise TaskStoreError(str(exc)) from exc
        if task.get("agent_role") == "reviewer" or task["kind"] == "review":
            if task.get("artifact_input") is None:
                raise TaskStoreError("model_review_artifact_input_required")
            task["capability"] = "validate_task"
        tasks.append(task)
    criteria = plan.get("acceptance_criteria", [])
    if not isinstance(criteria, list) or not all(isinstance(item, str) for item in criteria):
        raise TaskStoreError("agent_plan_criteria_invalid")
    return {"tasks": tasks, "acceptance_criteria": criteria[:20]}


def run_planner_cli(*, executor_kind: str, model_id: str, repo_dir: str, prompt: str,
                    timeout: float = PLAN_TIMEOUT_SECONDS, executor_factory: Callable[..., Any] | None = None) -> str:
    """Run the planner read-only in its isolated workspace; return its final text."""
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
    # AgentPlanner owns the disposable worktree; native tools remain read-only.
    prepared = CodexPreparedContext(Path(repo_dir).resolve(), "", f"plan-{int(time.time())}", cli, executor.KIND)
    parser = executor._parser(None)
    code = executor._stream(prepared, prompt, parser)
    turn = parser.finish()
    if code != 0 or turn.failed:
        raise TaskStoreError(turn.failure_classification or f"{executor_kind}_planner_failed")
    # Usage is reported with the job (tokens when the CLI reports them, otherwise unknown).
    return PlannerOutput(turn.final_text, dict(turn.usage) if turn.usage is not None else None)


@dataclass(frozen=True)
class PlannerOutput:
    text: str
    usage: dict[str, int] | None = None


_RAW_EXCERPT_LIMIT = 2000


def _raw_excerpt(text: str) -> str:
    """First and last 2000 chars of the planner's final text, secret-redacted."""
    redacted = redact_secrets(text or "")
    if len(redacted) <= _RAW_EXCERPT_LIMIT * 2:
        return redacted
    return (redacted[:_RAW_EXCERPT_LIMIT] + "\n...[truncated]...\n"
            + redacted[-_RAW_EXCERPT_LIMIT:])


@dataclass
class PlanJob:
    goal_id: str
    status: str = "RUNNING"  # RUNNING | PLANNED | FAILED
    error: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    planner: dict[str, str] = field(default_factory=dict)
    usage: dict[str, int] | None = None
    raw_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = {"goal_id": self.goal_id, "status": self.status, "error": self.error,
                "started_at": self.started_at, "finished_at": self.finished_at, "planner": dict(self.planner),
                # A planner run is a model call: unknown usage is reported as unknown, never as zero.
                "usage_status": "observed_tokens" if self.usage is not None else "unknown",
                "token_usage": dict(self.usage) if self.usage is not None else None}
        # Only a failed parse keeps the raw excerpt, so the cause can be diagnosed.
        if self.status == "FAILED" and self.raw_excerpt:
            data["raw_excerpt"] = self.raw_excerpt
        return data


_RUNTIME_CODES = frozenset({
    "native_task_temp_unavailable", "planner_path_invalid", "planner_base_invalid",
    "planner_git_failed", "planner_preparation_failed", "planner_identity_invalid",
    "planner_busy", "planner_destination_exists", "planner_head_mismatch",
} | {f"{kind}_{suffix}" for kind in ("codex", "claude_code") for suffix in (
    "cli_missing", "cli_requires_native_executable", "cli_unavailable", "model_id_invalid",
    "sandbox_invalid", "timeout_invalid", "managed_login_unavailable", "process_start_failed",
    "requires_managed_session_binding", "session_unavailable", "relay_requires_lease_provider",
)})


def _runtime_error_code(exc: ExecutorRuntimeError) -> str:
    # Runtime errors have no code attribute: args[0] is a string, sometimes with
    # diagnostic output appended after a colon. Never publish that diagnostic.
    value = exc.args[0] if exc.args and isinstance(exc.args[0], str) else ""
    code = value.split(":", 1)[0]
    return code if code in _RUNTIME_CODES else "ExecutorRuntimeError"


class AgentPlanner:
    """Process-local registry of background planning jobs (one per Goal)."""

    def __init__(self, *, goal_service: Any, roster_resolver: Callable[[str], tuple[str, str]],
                 binding_model: Callable[[str], str], repo_dir_for: Callable[[str], str],
                 runner: Callable[..., str] = run_planner_cli,
                 workspace_root: str | Path | None = None) -> None:
        self._goals = goal_service
        self._roster = roster_resolver
        self._binding_model = binding_model
        self._repo_dir_for = repo_dir_for
        self._runner = runner
        self._workspace_root = workspace_root or (Path(goal_service.store.db_path).absolute().parent / "task_workspaces")
        self._jobs: dict[str, PlanJob] = {}
        self._lock = threading.Lock()

    def status(self, goal_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(goal_id)
            return job.to_dict() if job else {"goal_id": goal_id, "status": "NONE", "error": ""}

    def start(self, goal_id: str, *, expected_revision: int, background: bool = True,
              base_commit: str | None = None) -> dict[str, Any]:
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
        # No frozen-goal-base contract is exposed by this GoalRecord. Callers
        # can supply an explicit base without adding a persistent goal field.
        # Pin before dispatch: the source HEAD may move while this job is queued.
        try:
            source = repository_preparation._planner_path(self._repo_dir_for(goal.repository))
            base = "HEAD" if base_commit is None else base_commit
            if not isinstance(base, str) or not base or base.startswith("-"):
                raise ExecutorRuntimeError("planner_base_invalid")
            pinned = repository_preparation._planner_git(source, "rev-parse", "--verify", base + "^{commit}")
        except Exception as exc:
            code = _runtime_error_code(exc) if isinstance(exc, ExecutorRuntimeError) else type(exc).__name__
            with self._lock:
                job.status, job.error, job.finished_at = "FAILED", f"agent_planner_error:{code}", time.time()
            return self.status(goal_id)
        work = lambda: self._run(job, goal, executor_kind, binding_ref, source, pinned)  # noqa: E731
        if background:
            threading.Thread(target=work, name=f"agent-plan-{goal_id}", daemon=True).start()
        else:
            work()
        return self.status(goal_id)

    def _run(self, job: PlanJob, goal: Any, executor_kind: str, binding_ref: str,
             source: Path, base_commit: str) -> None:
        try:
            with repository_preparation.planner_worktree(
                    source, self._workspace_root, goal.id, goal.revision, base_commit) as (workspace, _):
                output = self._runner(
                    executor_kind=executor_kind, model_id=self._binding_model(binding_ref),
                    repo_dir=str(workspace),
                    prompt=build_planner_prompt(objective=goal.objective, repository=goal.repository))
            if isinstance(output, PlannerOutput):
                text, job.usage = output.text, output.usage
            else:
                text = output
            try:
                plan = extract_plan(text)
            except TaskStoreError:
                # The expensive planner run produced unparseable text; keep a bounded
                # excerpt so the cause can be diagnosed instead of being lost.
                job.raw_excerpt = _raw_excerpt(text)
                raise
            current = self._goals.control_store.get_goal(goal.id)
            # DRAFT -> PLANNED keeps the revision, so also compare status and plan digest:
            # a plan the Owner saved while the planner ran is never overwritten.
            if (current.revision, current.status, current.artifact_digest) != (
                    goal.revision, goal.status, goal.artifact_digest):
                raise TaskStoreError("goal_changed_during_planning")
            self._goals.plan(goal.id, expected_revision=goal.revision, tasks=plan["tasks"],
                             acceptance_criteria=plan["acceptance_criteria"])
            outcome, error = "PLANNED", ""
        except ExecutorRuntimeError as exc:
            outcome, error = "FAILED", f"agent_planner_error:{_runtime_error_code(exc)}"
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

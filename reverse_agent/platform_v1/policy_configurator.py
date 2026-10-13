"""Natural-language Agent team configuration.

The Owner describes preferences in one sentence ("规划用最强的，日常编码尽量免费，
Kimi 别用"). A ready native account model reads that sentence together with the
real list of saved bindings and their observed health, read-only, and proposes
a team: which binding fills each role, which bindings to avoid, and a Chinese
explanation. Nothing is applied until the Owner confirms; applying goes
through the roster's own validation (bindings exist and are enabled, the
reviewer differs from the coder).
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from ..model_access.contracts import AGENT_ROLES
from .agent_planner import PlannerOutput, run_planner_cli
from .run_store import TaskStoreError

MAX_TEXT = 2000
ROLE_PURPOSE = {
    "planner": "decomposes goals and designs (few calls, needs the strongest reasoning)",
    "complex": "architecture-level or multi-file changes",
    "coder": "ordinary feature work and bug fixes (most tasks)",
    "simple": "docs, tests, small edits (cheapest is best)",
    "reviewer": "reviews another agent's result; must be a different model than coder",
}


def build_policy_prompt(*, text: str, bindings: Sequence[Mapping[str, Any]],
                        health: Mapping[str, Mapping[str, Any]]) -> str:
    lines = []
    for item in bindings:
        stats = health.get(item["binding_id"], {})
        lines.append(f'- {item["binding_id"]}: executor={item["executor_id"]}, model={item["model_id"]}, '
                     f'connection={item["connection_id"]} ({item.get("cost_class", "unknown")}), '
                     f'recent ok={stats.get("ok", 0)} failed={stats.get("failed", 0)} '
                     f'timeouts={stats.get("timeouts", 0)} rate_limited={stats.get("rate_limited", 0)} '
                     f'typical_ok_minutes={_minutes(stats.get("median_ok_seconds"))}')
    roles = "\n".join(f"- {role}: {ROLE_PURPOSE[role]}" for role in AGENT_ROLES)
    return (
        "You configure a multi-agent software team from the owner's preference sentence. "
        "Choose, for every role, the saved binding that best matches the preference, using only the "
        "binding ids listed. Prefer cheaper bindings where the preference does not ask for strength, "
        "avoid bindings that are recently failing or rate limited, and honor explicit exclusions. "
        "A binding that times out but also succeeds is slow, not broken: it suits cheap, non-urgent work. "
        "Planner must be a binding whose executor is claude_code or codex. Reviewer must use a different "
        "model than coder.\n\n"
        f"Owner preference (may be Chinese):\n{text}\n\nRoles:\n{roles}\n\nSaved bindings:\n" + "\n".join(lines) +
        "\n\nAnswer with exactly one JSON object and nothing else:\n"
        '{"roles": {"planner": "<binding_id>", "complex": "...", "coder": "...", "simple": "...", '
        '"reviewer": "..."}, "excluded": ["<binding_id>"], '
        '"explanation": "<two or three sentences in Chinese explaining the choice>"}'
    )


def extract_policy(text: str, *, known: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Validate the interpreter's proposal against the real bindings; never invent ids."""
    candidate = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    elif not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise TaskStoreError("agent_policy_not_json")
        candidate = candidate[start:end + 1]
    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise TaskStoreError("agent_policy_not_json") from exc
    roles = data.get("roles") if isinstance(data, dict) else None
    if not isinstance(roles, dict):
        raise TaskStoreError("agent_policy_roles_required")
    excluded = data.get("excluded", [])
    if not isinstance(excluded, list) or not all(isinstance(item, str) for item in excluded):
        raise TaskStoreError("agent_policy_excluded_invalid")
    proposal: dict[str, str] = {}
    for role in AGENT_ROLES:
        binding = roles.get(role, "")
        if binding in ("", None):
            continue
        if not isinstance(binding, str) or binding not in known:
            raise TaskStoreError(f"agent_policy_unknown_binding:{role}")
        if binding in excluded:
            raise TaskStoreError(f"agent_policy_role_uses_excluded_binding:{role}")
        proposal[role] = binding
    planner = proposal.get("planner")
    if planner and known[planner]["executor_id"] not in {"claude_code", "codex"}:
        raise TaskStoreError("agent_policy_planner_requires_native_executor")
    explanation = data.get("explanation", "")
    if not isinstance(explanation, str):
        raise TaskStoreError("agent_policy_explanation_invalid")
    return {"roles": proposal, "excluded": [item for item in excluded if item in known][:50],
            "explanation": explanation.strip()[:1000]}


@dataclass
class PolicyJob:
    id: str
    text: str
    status: str = "RUNNING"  # RUNNING | PROPOSED | FAILED | APPLIED
    error: str = ""
    proposal: dict[str, Any] = field(default_factory=dict)
    interpreter: dict[str, str] = field(default_factory=dict)
    usage: dict[str, int] | None = None
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "text": self.text, "status": self.status, "error": self.error,
                "proposal": dict(self.proposal), "interpreter": dict(self.interpreter),
                "usage_status": "observed_tokens" if self.usage is not None else "unknown",
                "token_usage": dict(self.usage) if self.usage is not None else None,
                "started_at": self.started_at}


class PolicyConfigurator:
    """Process-local jobs that turn a preference sentence into a proposed team."""

    def __init__(self, *, bindings: Callable[[], Sequence[Mapping[str, Any]]],
                 health: Callable[[], Mapping[str, Mapping[str, int]]],
                 interpreter: Callable[[], tuple[str, str, str]],
                 apply_roster: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                 runner: Callable[..., Any] = run_planner_cli) -> None:
        self._bindings = bindings
        self._health = health
        self._interpreter = interpreter  # -> (executor_kind, binding_id, model_id)
        self._apply_roster = apply_roster
        self._runner = runner
        self._jobs: dict[str, PolicyJob] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TaskStoreError("agent_policy_job_not_found")
            return job.to_dict()

    def interpret(self, text: str, *, background: bool = True) -> dict[str, Any]:
        text = (text or "").strip()
        if not text or len(text) > MAX_TEXT:
            raise TaskStoreError("agent_policy_text_invalid")
        executor_kind, binding_id, model_id = self._interpreter()
        if executor_kind not in {"claude_code", "codex"}:
            raise TaskStoreError("agent_policy_requires_native_interpreter")
        with self._lock:
            if any(job.status == "RUNNING" for job in self._jobs.values()):
                raise TaskStoreError("agent_policy_job_running")
            job = PolicyJob(uuid.uuid4().hex[:16], text,
                            interpreter={"executor_kind": executor_kind, "binding_id": binding_id})
            self._jobs[job.id] = job
        work = lambda: self._run(job, executor_kind, model_id)  # noqa: E731
        if background:
            threading.Thread(target=work, name=f"agent-policy-{job.id}", daemon=True).start()
        else:
            work()
        return self.get(job.id)

    def _run(self, job: PolicyJob, executor_kind: str, model_id: str) -> None:
        workdir = tempfile.mkdtemp(prefix="nerelan-policy-")
        try:
            bindings = [dict(item) for item in self._bindings() if item.get("enabled", True)]
            known = {item["binding_id"]: item for item in bindings}
            prompt = build_policy_prompt(text=job.text, bindings=bindings, health=self._health())
            # The interpreter needs no repository: it runs read-only in an empty directory.
            output = self._runner(executor_kind=executor_kind, model_id=model_id, repo_dir=workdir, prompt=prompt)
            if isinstance(output, PlannerOutput):
                text, job.usage = output.text, output.usage
            else:
                text = output
            proposal = extract_policy(text, known=known)
            outcome, error = "PROPOSED", ""
        except TaskStoreError as exc:
            proposal, outcome, error = {}, "FAILED", str(exc)[:200]
        except Exception as exc:  # noqa: BLE001 - finite failure code for any interpreter error
            proposal, outcome, error = {}, "FAILED", f"agent_policy_error:{type(exc).__name__}"
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
        with self._lock:
            job.proposal, job.status, job.error = proposal, outcome, error

    def apply(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise TaskStoreError("agent_policy_job_not_found")
            if job.status != "PROPOSED":
                raise TaskStoreError("agent_policy_not_proposed")
            proposal = dict(job.proposal)
        try:
            roster = self._apply_roster({"roles": proposal["roles"], "policy": {
                "text": job.text, "explanation": proposal["explanation"], "excluded": proposal["excluded"]}})
        except ValueError as exc:  # roster validation (e.g. reviewer equals coder)
            raise TaskStoreError(str(exc)) from exc
        with self._lock:
            job.status = "APPLIED"
        return {"job": self.get(job_id), "roster": dict(roster)}


def _minutes(seconds: Any) -> str:
    return f"{seconds / 60:.1f}" if isinstance(seconds, (int, float)) else "unknown"


def binding_health(store: Any, *, limit: int = 500) -> dict[str, dict[str, Any]]:
    """Recent per-binding profiles from the TaskStore (provider-free observation)."""
    from .model_profiles import compute_agent_profiles
    return compute_agent_profiles(store, limit=limit)

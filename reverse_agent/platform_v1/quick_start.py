"""One sentence -> planned Goals and an Owner window request (one-step start, steps 3-4).

The Owner writes one line in the input box, for example "修复 #1350、#1285，跑一天".
This module turns it into Goals ready for an Owner window and the window request a
preset describes. It creates and plans Goals only: approval, launch and activation
stay with the Owner window admission and its host-side confirmation.

Every Goal is an ``agent_team`` Goal with no pinned binding, so launch routes each
task inside the confirmed pool (a routed ``single`` Goal gets no binding; that was
the 2026-11-08 BLOCKED window). Issue text is data: it becomes the Goal objective
the executor reads, never an instruction to this host.

Presets follow the Owner decision of 2026-11-09 (ONE_STEP_START_PLAN section 4).
An optional ``owner_window_presets.json`` next to the task store may change the
numbers; the store's hard ceilings still apply at admission.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from .control_store import OWNER_WINDOW_CAPABILITIES, OWNER_WINDOW_MAX_GOALS
from .run_store import TaskStoreError

MAX_TEXT_CHARS = 2_000
MAX_ISSUE_BODY_CHARS = 12_000
CAPABILITIES = ("execute_task", "resume_task", "reconcile_task", "validate_task", "open_draft_pr")

PRESETS: dict[str, dict[str, Any]] = {
    "trial": {"label": "试跑", "hours": 2, "max_concurrent": 1, "max_retries": 1, "max_token_units": 300_000},
    "day": {"label": "一天", "hours": 24, "max_concurrent": 1, "max_retries": 2, "max_token_units": 2_000_000},
    "week": {"label": "一周", "hours": 168, "max_concurrent": 2, "max_retries": 2, "max_token_units": 10_000_000},
}
DEFAULT_PRESET = "day"
_PRESET_KEYS = ("hours", "max_concurrent", "max_retries", "max_token_units")

_ISSUE_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d{1,7})\b")
_ISSUE_NUMBER = re.compile(r"(?<![\w/&])#(\d{1,7})\b")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_PRESET_HINTS = (
    ("week", re.compile(r"一周|7\s*天|七天|week", re.I)),
    ("trial", re.compile(r"试跑|试一下|两小时|2\s*小时|trial", re.I)),
    ("day", re.compile(r"一天|24\s*小时|整天|day", re.I)),
)

ACCEPTANCE = (
    "The change resolves {subject} as its Acceptance/Ask section describes",
    "Focused tests cover the change and pass; git diff --check is clean",
    "No governance, workflow, landing_review.py or dependency file changes",
)


def presets(state_dir: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Built-in presets, with any Owner overrides from ``owner_window_presets.json``."""
    merged = {name: dict(values) for name, values in PRESETS.items()}
    path = Path(state_dir) / "owner_window_presets.json" if state_dir else None
    if path is None or not path.is_file():
        return merged
    try:
        overrides = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TaskStoreError("owner_window_presets_invalid") from exc
    if not isinstance(overrides, dict):
        raise TaskStoreError("owner_window_presets_invalid")
    for name, values in overrides.items():
        if name not in merged or not isinstance(values, dict):
            raise TaskStoreError("owner_window_presets_invalid")
        for key, value in values.items():
            if key not in _PRESET_KEYS or isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise TaskStoreError("owner_window_presets_invalid")
            merged[name][key] = value
    return merged


def window_request(preset: Mapping[str, Any], goal_ids: list[str], *, tasks: int) -> dict[str, Any]:
    """The Owner window request a preset describes; Draft PRs only, paid API excluded by the pool."""
    return {"goal_ids": goal_ids, "hours": float(preset["hours"]),
            "max_tasks": max(tasks, 1) * (1 + int(preset["max_retries"])),
            "max_concurrent": int(preset["max_concurrent"]), "max_retries": int(preset["max_retries"]),
            "capabilities": [c for c in CAPABILITIES if c in OWNER_WINDOW_CAPABILITIES],
            "max_token_units": int(preset["max_token_units"]), "max_cost_micro_units": 0}


def parse(text: str, repository: str) -> dict[str, Any]:
    """Issue references (links or ``#N`` in ``repository``) and the preset the text asks for."""
    text = str(text or "").strip()
    if not text or len(text) > MAX_TEXT_CHARS:
        raise TaskStoreError("quick_start_text_invalid")
    if not _REPOSITORY.fullmatch(repository or ""):
        raise TaskStoreError("quick_start_repository_invalid")
    issues: list[tuple[str, int]] = []
    for repo, number in _ISSUE_URL.findall(text):
        issues.append((repo, int(number)))
    for number in _ISSUE_NUMBER.findall(_ISSUE_URL.sub(" ", text)):
        issues.append((repository, int(number)))
    issues = list(dict.fromkeys(issues))
    if any(repo.lower() != repository.lower() for repo, _ in issues):
        raise TaskStoreError("quick_start_issue_outside_repository")
    if len(issues) > OWNER_WINDOW_MAX_GOALS:
        raise TaskStoreError("quick_start_too_many_issues")
    preset = next((name for name, hint in _PRESET_HINTS if hint.search(text)), DEFAULT_PRESET)
    return {"text": text, "repository": repository, "issues": [number for _, number in issues], "preset": preset}


def gh_issue_reader(repository: str, number: int) -> dict[str, Any]:
    """Read one issue with the authenticated ``gh`` CLI (no token is handled here)."""
    result = subprocess.run(
        ["gh", "issue", "view", str(number), "--repo", repository, "--json", "number,title,body,state,url"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if result.returncode != 0:
        raise TaskStoreError(f"quick_start_issue_unreadable:{number}")
    try:
        raw = json.loads(result.stdout)
    except ValueError as exc:
        raise TaskStoreError(f"quick_start_issue_unreadable:{number}") from exc
    return {"number": int(raw.get("number", number)), "title": str(raw.get("title", "")),
            "body": str(raw.get("body", "")), "state": str(raw.get("state", "")), "url": str(raw.get("url", ""))}


class QuickStart:
    """Creates and plans the Goals one sentence asks for. Creates no window."""

    def __init__(self, goal_service: Any, *, issue_reader: Callable[[str, int], Mapping[str, Any]] = gh_issue_reader,
                 state_dir: str | Path | None = None) -> None:
        self._goals = goal_service
        self._read_issue = issue_reader
        self._state_dir = state_dir

    def draft(self, text: str, repository: str, *, preset: str = "") -> dict[str, Any]:
        request = parse(text, repository)
        options = presets(self._state_dir)
        chosen = preset or request["preset"]
        if chosen not in options:
            raise TaskStoreError("quick_start_preset_invalid")
        specs = [self._issue_spec(repository, number) for number in request["issues"]] or [
            self._text_spec(request["text"])]
        goals = [self._planned(repository, spec) for spec in specs]
        tasks = sum(len(goal.tasks) for goal in goals)
        return {"goals": [{"id": goal.id, "title": goal.title, "status": goal.status, "tasks": list(goal.tasks)}
                          for goal in goals],
                "preset": chosen, "presets": options,
                "request": window_request(options[chosen], [goal.id for goal in goals], tasks=tasks)}

    def _issue_spec(self, repository: str, number: int) -> dict[str, str]:
        issue = self._read_issue(repository, number)
        if str(issue.get("state", "")).upper() != "OPEN":
            raise TaskStoreError(f"quick_start_issue_not_open:{number}")
        url = issue.get("url") or f"https://github.com/{repository}/issues/{number}"
        title = f"#{number} {issue.get('title', '')}".strip()
        body = str(issue.get("body", ""))[:MAX_ISSUE_BODY_CHARS]
        return {"key": f"issue-{number}", "title": title[:200], "subject": url,
                "objective": f"Resolve {url}\n\n# {issue.get('title', '')}\n\n{body}".strip()}

    @staticmethod
    def _text_spec(text: str) -> dict[str, str]:
        return {"key": "text", "title": text.splitlines()[0][:200], "subject": "the request", "objective": text}

    def _planned(self, repository: str, spec: Mapping[str, str]) -> Any:
        # Same sentence and same issue text -> same Goal; a changed issue makes a new one.
        # A Goal already used by a window (running, blocked, done) is not reused: the
        # next attempt gets its own Goal.
        digest = hashlib.sha256(spec["objective"].encode("utf-8")).hexdigest()[:16]
        for attempt in range(1, 21):
            goal = self._goals.create({
                "title": spec["title"], "objective": spec["objective"], "repository": repository,
                "idempotency_key": f"quick-start:{repository}:{spec['key']}:{digest}:{attempt}",
                "executor_kind": "opencode", "binding_ref": "", "orchestration_mode": "agent_team"})
            if goal.status in {"DRAFT", "PLANNED"} and not goal.window_id:
                break
        else:
            raise TaskStoreError("quick_start_too_many_attempts")
        if goal.status == "PLANNED":
            return goal
        label = spec["title"].split(" ", 1)[0] if spec["key"].startswith("issue-") else "the request"
        return self._goals.plan(goal.id, expected_revision=goal.revision,
                                acceptance_criteria=[line.format(subject=spec["subject"]) for line in ACCEPTANCE],
                                tasks=[{"id": "implement", "title": f"Implement {label}",
                                        "instruction": "Follow the Goal objective and its scope rules.",
                                        "kind": "code", "difficulty": 3}]).goal

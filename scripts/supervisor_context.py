#!/usr/bin/env python3
"""Thin Codex Supervisor context collector (quota-free v0.2, fail-closed).

Calls ``git`` and ``gh`` to produce a bounded JSON repository context for an
audit prompt. Pure standard library. No real Codex/model calls, no live
GitHub writes, no full environment dumps, no credentials.

Fail-closed: if any required git/gh invocation fails, times out, returns
invalid JSON, or the main SHA is missing, ``collect_context`` raises
``ContextError`` and no context is emitted. Read failures are never masked
as empty Issue/PR lists.

Bounded: hard caps on issues / PRs / commits / titles / bodies. All command
execution goes through :func:`run_git` / :func:`run_gh` with explicit arg
lists (no shell), so unit tests inject fakes and never touch the network.

Usage:
    python scripts/supervisor_context.py \\
        --repository dddd2024/reverse-agent \\
        --output context.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

# Bounded limits.
MAX_ISSUES = 50
MAX_PRS = 50
MAX_COMMITS = 50
MAX_LABELS = 20
MAX_TITLE_LENGTH = 200
MAX_BODY_LENGTH = 4000
MAX_LABEL_LENGTH = 60

CommandRunner = Callable[[Sequence[str], float], "CommandOutcome"]


class ContextError(RuntimeError):
    """Raised when a required context collection step fails (fail-closed)."""


class CommandOutcome:
    """Bounded outcome of a command invocation."""

    __slots__ = ("exit_code", "stdout", "stderr", "timed_out")

    def __init__(self, exit_code: int, stdout: str, stderr: str, timed_out: bool) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def default_runner(args: Sequence[str], timeout: float) -> CommandOutcome:
    """Run a command with an explicit arg list (no shell)."""

    try:
        completed = subprocess.run(  # noqa: S603 - bounded, explicit arg list
            list(args),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandOutcome(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandOutcome(
            exit_code=-1,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            timed_out=True,
        )


def run_git(args: Sequence[str], runner: CommandRunner = default_runner, timeout: float = 30.0) -> CommandOutcome:
    return runner(["git", *args], timeout)


def run_gh(args: Sequence[str], runner: CommandRunner = default_runner, timeout: float = 30.0) -> CommandOutcome:
    return runner(["gh", *args], timeout)


def _bounded_text(value: str, max_length: int) -> str:
    stripped = value.strip()
    if len(stripped) > max_length:
        return stripped[:max_length]
    return stripped


def _parse_json_required(stdout: str, what: str) -> Any:
    """Parse ``gh ... --json`` output. Fail-closed on empty or invalid JSON."""

    text = stdout.strip()
    if not text:
        raise ContextError(f"{what}: empty output")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"{what}: invalid JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise ContextError(f"{what}: expected JSON array, got {type(parsed).__name__}")
    return parsed


def collect_context(
    repository: str,
    *,
    runner: CommandRunner = default_runner,
) -> Mapping[str, Any]:
    """Collect a bounded repository context via git + gh (fail-closed).

    Never includes environment variables, credentials, full stderr, tokens,
    cookies, or session data. Identical inputs produce identical contexts.

    Raises :class:`ContextError` if any required step fails.
    """

    default_branch = _git_default_branch(runner)
    main_sha = _git_branch_sha_required(default_branch, runner)
    current_branch = _git_current_branch(runner)
    current_head = _git_current_head(runner)
    worktree_clean = _git_worktree_clean(runner)
    open_issues = _gh_open_issues(repository, runner)
    open_prs = _gh_open_prs(repository, runner)
    commits = _git_recent_commits(default_branch, runner)

    # Bounded goal info from Issue #90 (parent product).
    issue_90_goal = _gh_issue_goal(repository, 90, runner)

    # PR #93 exact facts (head, CI, State Gate).
    pr_93_facts = _gh_pr_facts(repository, 93, runner)

    return {
        "repository": repository,
        "default_branch": default_branch,
        "main_sha": main_sha,
        "current_branch": current_branch,
        "current_head": current_head,
        "worktree_clean": worktree_clean,
        "issues": open_issues,
        "pull_requests": open_prs,
        "commits": commits,
        "issue_90_goal": issue_90_goal,
        "pr_93_facts": pr_93_facts,
    }


def _git_default_branch(runner: CommandRunner) -> str:
    outcome = run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], runner)
    if not outcome.ok or not outcome.stdout.strip():
        raise ContextError(f"git default-branch failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    return outcome.stdout.strip().split("/", 1)[-1]


def _git_branch_sha_required(branch: str, runner: CommandRunner) -> str:
    outcome = run_git(["rev-parse", f"refs/remotes/origin/{branch}"], runner)
    if not outcome.ok or not outcome.stdout.strip():
        raise ContextError(f"git rev-parse origin/{branch} failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    return outcome.stdout.strip()


def _git_current_branch(runner: CommandRunner) -> str:
    outcome = run_git(["branch", "--show-current"], runner)
    if not outcome.ok:
        raise ContextError(f"git branch --show-current failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    return outcome.stdout.strip() or "HEAD"


def _git_current_head(runner: CommandRunner) -> str:
    outcome = run_git(["rev-parse", "HEAD"], runner)
    if not outcome.ok:
        raise ContextError(f"git rev-parse HEAD failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    return outcome.stdout.strip()


def _git_worktree_clean(runner: CommandRunner) -> bool:
    outcome = run_git(["status", "--porcelain"], runner)
    if not outcome.ok:
        raise ContextError(f"git status failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    return outcome.stdout.strip() == ""


def _gh_open_issues(repository: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    outcome = run_gh(
        [
            "issue", "list",
            "--repo", repository,
            "--state", "open",
            "--limit", str(MAX_ISSUES),
            "--json", "number,title,labels",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"gh issue list failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    parsed = _parse_json_required(outcome.stdout, "gh issue list")
    items: list[Mapping[str, Any]] = []
    for raw in parsed[:MAX_ISSUES]:
        if not isinstance(raw, Mapping):
            continue
        labels_raw = raw.get("labels", [])
        if not isinstance(labels_raw, list):
            labels_raw = []
        labels = [
            _bounded_text(str(l.get("name", "")), MAX_LABEL_LENGTH)
            for l in labels_raw[:MAX_LABELS]
            if isinstance(l, Mapping) and str(l.get("name", "")).strip()
        ]
        items.append({
            "number": raw.get("number"),
            "title": _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH),
            "labels": labels,
        })
    items.sort(key=lambda i: (i.get("number") or 0, i.get("title") or ""))
    return items


def _gh_open_prs(repository: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    outcome = run_gh(
        [
            "pr", "list",
            "--repo", repository,
            "--state", "open",
            "--limit", str(MAX_PRS),
            "--json", "number,title,isDraft,headRefName,headRefOid,baseRefName",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"gh pr list failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    parsed = _parse_json_required(outcome.stdout, "gh pr list")
    items: list[Mapping[str, Any]] = []
    for raw in parsed[:MAX_PRS]:
        if not isinstance(raw, Mapping):
            continue
        items.append({
            "number": raw.get("number"),
            "title": _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH),
            "draft": bool(raw.get("isDraft", False)),
            "head_ref": _bounded_text(str(raw.get("headRefName", "")), MAX_LABEL_LENGTH),
            "head_sha": str(raw.get("headRefOid", "")).strip().lower(),
            "base_ref": _bounded_text(str(raw.get("baseRefName", "")), MAX_LABEL_LENGTH),
        })
    items.sort(key=lambda p: (p.get("number") or 0, p.get("title") or ""))
    return items


def _gh_issue_goal(repository: str, issue_number: int, runner: CommandRunner) -> Mapping[str, Any]:
    """Fetch bounded goal info from an Issue body."""

    outcome = run_gh(
        [
            "issue", "view", str(issue_number),
            "--repo", repository,
            "--json", "number,title,body",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"gh issue view {issue_number} failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    text = outcome.stdout.strip()
    if not text:
        raise ContextError(f"gh issue view {issue_number}: empty output")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"gh issue view {issue_number}: invalid JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ContextError(f"gh issue view {issue_number}: expected JSON object")
    title = _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH)
    body = _bounded_text(str(raw.get("body", "")), MAX_BODY_LENGTH)
    return {
        "number": raw.get("number", issue_number),
        "title": title,
        "goal_excerpt": body,
    }


def _gh_pr_facts(repository: str, pr_number: int, runner: CommandRunner) -> Mapping[str, Any]:
    """Fetch PR exact head, CI success, and State Gate failure facts."""

    outcome = run_gh(
        [
            "pr", "view", str(pr_number),
            "--repo", repository,
            "--json", "number,title,isDraft,state,headRefName,headRefOid,baseRefName",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"gh pr view {pr_number} failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    text = outcome.stdout.strip()
    if not text:
        raise ContextError(f"gh pr view {pr_number}: empty output")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"gh pr view {pr_number}: invalid JSON: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ContextError(f"gh pr view {pr_number}: expected JSON object")

    # Fetch check runs (bounded, no stderr/env/token in output).
    checks = _gh_pr_checks(repository, pr_number, runner)

    return {
        "number": raw.get("number", pr_number),
        "title": _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH),
        "draft": bool(raw.get("isDraft", False)),
        "state": str(raw.get("state", "")),
        "head_ref": _bounded_text(str(raw.get("headRefName", "")), MAX_LABEL_LENGTH),
        "head_sha": str(raw.get("headRefOid", "")).strip().lower(),
        "base_ref": _bounded_text(str(raw.get("baseRefName", "")), MAX_LABEL_LENGTH),
        "checks": checks,
    }


def _gh_pr_checks(repository: str, pr_number: int, runner: CommandRunner) -> list[Mapping[str, Any]]:
    """Fetch bounded PR check facts (name, state, run_id)."""

    outcome = run_gh(
        [
            "pr", "checks", str(pr_number),
            "--repo", repository,
            "--json", "name,state,link",
        ],
        runner,
    )
    if not outcome.ok:
        # pr checks may return non-zero if no checks; treat as empty but record.
        return []
    text = outcome.stdout.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    items: list[Mapping[str, Any]] = []
    for raw in parsed[:MAX_LABELS]:
        if not isinstance(raw, Mapping):
            continue
        link = str(raw.get("link", "") or "")
        # Extract run_id from link if present (bounded, no credentials).
        run_id = ""
        if "/runs/" in link:
            run_id = link.split("/runs/", 1)[1].split("/", 1)[0]
        items.append({
            "name": _bounded_text(str(raw.get("name", "")), MAX_LABEL_LENGTH),
            "state": str(raw.get("state", "")).strip().lower(),
            "run_id": run_id,
        })
    return items


def _git_recent_commits(branch: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    outcome = run_git(
        ["log", "--oneline", "-n", str(MAX_COMMITS), f"refs/remotes/origin/{branch}"],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"git log failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    commits: list[Mapping[str, Any]] = []
    for line in outcome.stdout.splitlines()[:MAX_COMMITS]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        sha = parts[0].lower()
        title = _bounded_text(parts[1] if len(parts) > 1 else "", MAX_TITLE_LENGTH)
        commits.append({"sha": sha, "title": title})
    return commits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect a bounded Codex Supervisor context (fail-closed)")
    parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    parser.add_argument("--output", help="Output path (default: stdout)")
    args = parser.parse_args(argv)

    try:
        context = collect_context(args.repository)
    except ContextError as exc:
        # Fail-closed: print error to stderr, no context emitted, non-zero exit.
        print(json.dumps({"error": str(exc), "context": None}, sort_keys=True), file=sys.stderr)
        return 1

    text = json.dumps(context, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

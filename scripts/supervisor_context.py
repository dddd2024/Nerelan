#!/usr/bin/env python3
"""Thin Codex Supervisor context collector (quota-free v0).

Calls ``git`` and ``gh`` to produce a bounded JSON repository context for an
audit prompt. Pure standard library. No real Codex/model calls, no live
GitHub writes, no full environment dumps, no credentials.

Bounded: hard caps on issues / PRs / commits / titles / bodies. All command
execution goes through :func:`run_git` / :func:`run_gh` with explicit arg
lists (no shell), so unit tests inject fakes and never touch the network.

Usage:
    python scripts/supervisor_context.py \
        --repository dddd2024/reverse-agent \
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


def _parse_json_lines(stdout: str) -> list[Mapping[str, Any]]:
    """Parse ``gh ... --json`` output (a JSON array) robustly."""

    text = stdout.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def collect_context(
    repository: str,
    *,
    runner: CommandRunner = default_runner,
) -> Mapping[str, Any]:
    """Collect a bounded repository context via git + gh.

    Never includes environment variables, credentials, full logs, or full
    repository contents. Identical inputs produce identical contexts.
    """

    default_branch = _git_default_branch(runner)
    main_sha = _git_branch_sha(default_branch, runner)
    current_branch = _git_current_branch(runner)
    current_head = _git_current_head(runner)
    worktree_clean = _git_worktree_clean(runner)
    issues = _gh_open_issues(repository, runner)
    pull_requests = _gh_open_prs(repository, runner)
    commits = _git_recent_commits(default_branch, runner)

    return {
        "repository": repository,
        "default_branch": default_branch,
        "main_sha": main_sha,
        "current_branch": current_branch,
        "current_head": current_head,
        "worktree_clean": worktree_clean,
        "issues": issues,
        "pull_requests": pull_requests,
        "commits": commits,
    }


def _git_default_branch(runner: CommandRunner) -> str:
    outcome = run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], runner)
    if outcome.ok and outcome.stdout.strip():
        return outcome.stdout.strip().split("/", 1)[-1]
    return "main"


def _git_branch_sha(branch: str, runner: CommandRunner) -> str:
    outcome = run_git(["rev-parse", f"refs/remotes/origin/{branch}"], runner)
    if not outcome.ok:
        return ""
    return outcome.stdout.strip()


def _git_current_branch(runner: CommandRunner) -> str:
    outcome = run_git(["branch", "--show-current"], runner)
    if not outcome.ok:
        return ""
    return outcome.stdout.strip() or "HEAD"


def _git_current_head(runner: CommandRunner) -> str:
    outcome = run_git(["rev-parse", "HEAD"], runner)
    return outcome.stdout.strip() if outcome.ok else ""


def _git_worktree_clean(runner: CommandRunner) -> bool:
    outcome = run_git(["status", "--porcelain"], runner)
    return bool(outcome.ok and outcome.stdout.strip() == "")


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
    items: list[Mapping[str, Any]] = []
    for raw in _parse_json_lines(outcome.stdout)[:MAX_ISSUES]:
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
    items: list[Mapping[str, Any]] = []
    for raw in _parse_json_lines(outcome.stdout)[:MAX_PRS]:
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


def _git_recent_commits(branch: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    outcome = run_git(
        ["log", "--oneline", "-n", str(MAX_COMMITS), f"refs/remotes/origin/{branch}"],
        runner,
    )
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
    parser = argparse.ArgumentParser(description="Collect a bounded Codex Supervisor context")
    parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    parser.add_argument("--output", help="Output path (default: stdout)")
    args = parser.parse_args(argv)

    context = collect_context(args.repository)
    text = json.dumps(context, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

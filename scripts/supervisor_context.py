#!/usr/bin/env python3
"""Thin Codex Supervisor context collector (v0.4, fail-closed).

Calls ``git`` and ``gh`` to produce a bounded JSON repository context for an
audit prompt. Pure standard library. No real Codex/model calls, no live
GitHub writes, no full environment dumps, no credentials.

Fail-closed: if any required git/gh invocation fails, times out, returns
invalid JSON, or the main SHA is missing, ``collect_context`` raises
``ContextError`` and no context is emitted. Read failures are never masked
as empty Issue/PR lists.

v0.3 changes (fail-closed closure):
- Checks are collected via ``gh api`` check-runs bound to the exact head SHA,
  not ``gh pr checks`` (whose non-zero exit was wrongly treated as "no checks").
- Failed checks retain name, status, conclusion, and bounded run reference.
- Issue and PR lists use paginated ``gh api`` (not ``gh issue list --limit``).
- The goal Issue and active PR are configurable (no hardcoded #90 / #93).

Bounded: hard caps on issues / PRs / commits / titles / bodies. All command
execution goes through :func:`run_git` / :func:`run_gh` with explicit arg
lists (no shell), so unit tests inject fakes and never touch the network.

Usage:
    python scripts/supervisor_context.py \\
        --repository dddd2024/reverse-agent \\
        --goal-issue 90 \\
        --active-pr 93 \\
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

# Pagination safety caps.
MAX_ISSUE_PAGES = 10
MAX_CHECK_PAGES = 10
PAGE_SIZE = 100
MAX_TOTAL_ISSUES = 500  # safety cap across all pages
MAX_TOTAL_CHECK_RUNS = 500  # finite cap across all pages

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


def _parse_json_object_required(stdout: str, what: str) -> Mapping[str, Any]:
    """Parse ``gh ... --json`` output as a JSON object. Fail-closed."""

    text = stdout.strip()
    if not text:
        raise ContextError(f"{what}: empty output")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"{what}: invalid JSON: {exc}") from exc
    if not isinstance(parsed, Mapping):
        raise ContextError(f"{what}: expected JSON object, got {type(parsed).__name__}")
    return parsed


def _parse_json_array_required(stdout: str, what: str) -> list[Any]:
    """Parse ``gh ... --json`` output as a JSON array. Fail-closed."""

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
    goal_issue: int = 90,
    active_pr: int | None = None,
    runner: CommandRunner = default_runner,
) -> Mapping[str, Any]:
    """Collect a bounded repository context via git + gh (fail-closed).

    Never includes environment variables, credentials, full stderr, tokens,
    cookies, or session data. Identical inputs produce identical contexts.

    Args:
        repository: ``owner/name`` repository slug.
        goal_issue: Issue number carrying the bounded goal (default 90).
        active_pr: PR number for exact-head/check facts. If ``None``, the
            PR is derived from the current branch via the GitHub API. Zero
            or multiple matching PRs raises :class:`ContextError`.
        runner: Command runner (injectable for tests).

    Raises :class:`ContextError` if any required step fails.
    """

    default_branch = _git_default_branch(runner)
    local_main_sha = _git_branch_sha_required(default_branch, runner)
    github_main_sha = _gh_main_sha_required(repository, runner)
    if github_main_sha != local_main_sha:
        raise ContextError(
            "GitHub main does not match local origin/main: "
            f"{github_main_sha}!={local_main_sha}"
        )
    main_sha = github_main_sha
    current_branch = _git_current_branch(runner)
    current_head = _git_current_head(runner)
    worktree_clean = _git_worktree_clean(runner)
    open_issues = _gh_open_issues(repository, runner)
    open_prs = _gh_open_prs(repository, runner)
    commits = _git_recent_commits(default_branch, runner)

    # Bounded goal info from the configurable goal Issue.
    issue_goal = _gh_issue_goal(repository, goal_issue, runner)

    # Resolve the active PR number (derive from branch if not given).
    if active_pr is None:
        active_pr = _derive_active_pr(repository, current_branch, runner)

    # Active PR exact facts (head, checks).
    pr_facts = _gh_pr_facts(repository, active_pr, runner, exact_head=current_head)

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
        "goal_issue_number": goal_issue,
        "issue_goal": issue_goal,
        "active_pr_number": active_pr,
        "pr_facts": pr_facts,
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


def _gh_main_sha_required(repository: str, runner: CommandRunner) -> str:
    """Return the verified GitHub ``refs/heads/main`` commit SHA."""

    outcome = run_gh(
        ["api", f"repos/{repository}/git/refs/heads/main", "--method", "GET"],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            "gh api refs/heads/main failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    raw = _parse_json_object_required(outcome.stdout, "gh api refs/heads/main")
    obj = raw.get("object")
    if not isinstance(obj, Mapping):
        raise ContextError("gh api refs/heads/main: missing object")
    sha = str(obj.get("sha", "") or "").strip().lower()
    if not _is_full_sha(sha):
        raise ContextError("gh api refs/heads/main: missing or malformed object.sha")
    return sha


def _gh_open_issues(repository: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    """Fetch bounded open Issues via paginated ``gh api``.

    Filters out PR entries (the ``/issues`` endpoint includes PRs that have
    a ``pull_request`` field). Fail-closed on any page failure or malformed
    entry.
    """

    items: list[Mapping[str, Any]] = []
    for page in range(1, MAX_ISSUE_PAGES + 1):
        outcome = run_gh(
            [
                "api", f"repos/{repository}/issues", "--method", "GET",
                "--field", "state=open",
                "--field", f"per_page={PAGE_SIZE}",
                "--field", f"page={page}",
            ],
            runner,
        )
        if not outcome.ok:
            raise ContextError(f"gh api issues page {page} failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
        parsed = _parse_json_array_required(outcome.stdout, f"gh api issues page {page}")
        if not parsed:
            break  # empty page — done.
        for raw in parsed:
            if not isinstance(raw, Mapping):
                raise ContextError(f"gh api issues page {page}: non-object entry")
            # Filter out PR entries.
            if "pull_request" in raw:
                continue
            if "number" not in raw or "title" not in raw:
                raise ContextError(f"gh api issues page {page}: missing number/title")
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
            if len(items) >= MAX_TOTAL_ISSUES:
                raise ContextError(f"gh api issues: exceeded safety cap {MAX_TOTAL_ISSUES}")
        if len(parsed) < PAGE_SIZE:
            break  # last page.
    # Return only the first MAX_ISSUES for the context (bounded).
    items.sort(key=lambda i: (i.get("number") or 0, i.get("title") or ""))
    return items[:MAX_ISSUES]


def _gh_open_prs(repository: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    """Fetch bounded open PRs via ``gh pr list`` (paginated by gh internally)."""

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
    parsed = _parse_json_array_required(outcome.stdout, "gh pr list")
    items: list[Mapping[str, Any]] = []
    for raw in parsed[:MAX_PRS]:
        if not isinstance(raw, Mapping):
            raise ContextError("gh pr list: non-object entry")
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
    raw = _parse_json_object_required(outcome.stdout, f"gh issue view {issue_number}")
    title = _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH)
    body = _bounded_text(str(raw.get("body", "")), MAX_BODY_LENGTH)
    return {
        "number": raw.get("number", issue_number),
        "title": title,
        "goal_excerpt": body,
    }


def _derive_active_pr(repository: str, branch: str, runner: CommandRunner) -> int:
    """Derive the active PR number from the current branch via GitHub API.

    Queries ``gh api repos/.../pulls?head=<owner>:<branch>&state=open``.
    Exactly one match is required; zero or multiple raises ContextError.
    """

    owner = repository.split("/", 1)[0]
    head = f"{owner}:{branch}"
    outcome = run_gh(
        [
            "api", f"repos/{repository}/pulls", "--method", "GET",
            "--field", f"head={head}",
            "--field", "state=open",
            "--field", "per_page=10",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(f"gh api pulls (derive) failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
    parsed = _parse_json_array_required(outcome.stdout, "gh api pulls (derive)")
    if len(parsed) == 0:
        raise ContextError(f"gh api pulls (derive): no open PR for branch {branch}")
    if len(parsed) > 1:
        raise ContextError(f"gh api pulls (derive): multiple open PRs for branch {branch}")
    pr = parsed[0]
    if not isinstance(pr, Mapping) or "number" not in pr:
        raise ContextError("gh api pulls (derive): malformed PR entry")
    return int(pr["number"])


def _gh_pr_facts(
    repository: str,
    pr_number: int,
    runner: CommandRunner,
    *,
    exact_head: str,
) -> Mapping[str, Any]:
    """Fetch PR exact head and check-run facts.

    Checks are collected via ``gh api`` check-runs bound to ``exact_head``,
    not ``gh pr checks`` (whose non-zero exit was wrongly treated as empty).
    """

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
    raw = _parse_json_object_required(outcome.stdout, f"gh pr view {pr_number}")

    local_head = exact_head.strip().lower()
    pr_head_raw = raw.get("headRefOid")
    if not isinstance(pr_head_raw, str):
        raise ContextError(f"gh pr view {pr_number}: missing or malformed headRefOid")
    pr_head = pr_head_raw.strip().lower()
    if not _is_full_sha(local_head):
        raise ContextError("local HEAD is missing or malformed")
    if not _is_full_sha(pr_head):
        raise ContextError(f"gh pr view {pr_number}: missing or malformed headRefOid")
    if pr_head != local_head:
        raise ContextError(
            f"PR headRefOid does not match local HEAD: {pr_head}!={local_head}"
        )

    # Fetch check runs via API (bounded, no stderr/env/token in output).
    checks = _gh_check_runs(repository, local_head, runner)

    return {
        "number": raw.get("number", pr_number),
        "title": _bounded_text(str(raw.get("title", "")), MAX_TITLE_LENGTH),
        "draft": bool(raw.get("isDraft", False)),
        "state": str(raw.get("state", "")),
        "head_ref": _bounded_text(str(raw.get("headRefName", "")), MAX_LABEL_LENGTH),
        "head_sha": pr_head,
        "base_ref": _bounded_text(str(raw.get("baseRefName", "")), MAX_LABEL_LENGTH),
        "exact_head": local_head,
        "checks": checks,
    }


def _gh_check_runs(repository: str, head_sha: str, runner: CommandRunner) -> list[Mapping[str, Any]]:
    """Fetch bounded check-run facts via ``gh api`` bound to exact head SHA.

    Returns a list of ``{name, status, conclusion, run_url}`` dicts. Failed
    checks are included (not masked). Fail-closed on any page failure,
    invalid JSON, or incomplete pagination.
    """

    sha = head_sha.strip().lower()
    if not sha:
        raise ContextError("gh api check-runs: empty head SHA")
    items: list[Mapping[str, Any]] = []
    expected_total: int | None = None
    for page in range(1, MAX_CHECK_PAGES + 1):
        outcome = run_gh(
            [
                "api", f"repos/{repository}/commits/{sha}/check-runs", "--method", "GET",
                "--field", f"per_page={PAGE_SIZE}",
                "--field", f"page={page}",
            ],
            runner,
        )
        if not outcome.ok:
            raise ContextError(f"gh api check-runs page {page} failed (exit={outcome.exit_code}, timed_out={outcome.timed_out})")
        raw = _parse_json_object_required(outcome.stdout, f"gh api check-runs page {page}")
        total_count = raw.get("total_count")
        if isinstance(total_count, bool) or not isinstance(total_count, int) or total_count < 0:
            raise ContextError(f"gh api check-runs page {page}: missing or malformed total_count")
        if total_count > MAX_TOTAL_CHECK_RUNS:
            raise ContextError(
                f"gh api check-runs: total_count {total_count} exceeds safety cap {MAX_TOTAL_CHECK_RUNS}"
            )
        if expected_total is None:
            expected_total = total_count
            required_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
            if required_pages > MAX_CHECK_PAGES:
                raise ContextError(
                    f"gh api check-runs: pagination requires {required_pages} pages, cap is {MAX_CHECK_PAGES}"
                )
        elif total_count != expected_total:
            raise ContextError(
                f"gh api check-runs page {page}: total_count changed "
                f"from {expected_total} to {total_count}"
            )
        runs = raw.get("check_runs")
        if not isinstance(runs, list):
            raise ContextError(f"gh api check-runs page {page}: missing check_runs array")
        if len(runs) > PAGE_SIZE:
            raise ContextError(f"gh api check-runs page {page}: page exceeds per_page={PAGE_SIZE}")
        for run in runs:
            if not isinstance(run, Mapping):
                raise ContextError(f"gh api check-runs page {page}: non-object run")
            name = run.get("name")
            status = run.get("status")
            conclusion = run.get("conclusion")
            run_url = run.get("html_url")
            if not isinstance(name, str) or not name.strip():
                raise ContextError(f"gh api check-runs page {page}: missing or malformed name")
            if not isinstance(status, str) or not status.strip():
                raise ContextError(f"gh api check-runs page {page}: missing or malformed status")
            if conclusion is not None and not isinstance(conclusion, str):
                raise ContextError(f"gh api check-runs page {page}: malformed conclusion")
            if run_url is not None and not isinstance(run_url, str):
                raise ContextError(f"gh api check-runs page {page}: malformed html_url")
            items.append({
                "name": _bounded_text(name, MAX_LABEL_LENGTH),
                "status": status.strip().lower(),
                "conclusion": (conclusion or "").strip().lower(),
                "run_url": _bounded_text(run_url or "", 200),
            })
        if len(items) > total_count:
            raise ContextError(
                f"gh api check-runs: returned {len(items)} records but total_count is {total_count}"
            )
        if len(items) == total_count:
            return items
        if not runs or len(runs) < PAGE_SIZE:
            raise ContextError(
                f"gh api check-runs: incomplete pagination returned {len(items)} of {total_count}"
            )
    if expected_total is None or len(items) != expected_total:
        raise ContextError(
            "gh api check-runs: pagination cap reached before total_count was satisfied"
        )
    return items


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


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
    parser = argparse.ArgumentParser(description="Collect a bounded Codex Supervisor context (fail-closed v0.3)")
    parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    parser.add_argument("--goal-issue", type=int, default=90, help="Issue number carrying the bounded goal (default: 90)")
    parser.add_argument("--active-pr", type=int, default=None, help="Active PR number (default: derive from current branch)")
    parser.add_argument("--output", help="Output path (default: stdout)")
    args = parser.parse_args(argv)

    try:
        context = collect_context(
            args.repository,
            goal_issue=args.goal_issue,
            active_pr=args.active_pr,
        )
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

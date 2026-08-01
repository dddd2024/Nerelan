#!/usr/bin/env python3
"""Thin Codex Supervisor context collector (v0.5, fail-closed).

Calls ``git`` and ``gh`` to produce a bounded JSON repository context for an
audit prompt. Pure standard library. No real model calls, no live GitHub
writes, no environment dumps, and no credentials.

Windows subprocess output is captured as bytes and decoded as strict UTF-8.
Locale-dependent ANSI/GBK decoding is never used. Invalid UTF-8 is converted
into a finite non-success outcome so no partial context is emitted.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

MAX_ISSUES = 50
MAX_PRS = 50
MAX_COMMITS = 50
MAX_LABELS = 20
MAX_TITLE_LENGTH = 200
MAX_BODY_LENGTH = 4000
MAX_LABEL_LENGTH = 60
MAX_ISSUE_PAGES = 10
MAX_CHECK_PAGES = 10
PAGE_SIZE = 100
MAX_TOTAL_ISSUES = 500
MAX_TOTAL_CHECK_RUNS = 500
DECODE_ERROR_EXIT_CODE = -2

CommandRunner = Callable[[Sequence[str], float], "CommandOutcome"]


class ContextError(RuntimeError):
    """Raised when a required context collection step fails."""


class CommandOutcome:
    """Bounded command outcome whose streams are always strings."""

    __slots__ = ("exit_code", "stdout", "stderr", "timed_out")

    def __init__(
        self,
        exit_code: int,
        stdout: str | None,
        stderr: str | None,
        timed_out: bool,
    ) -> None:
        self.exit_code = int(exit_code)
        self.stdout = stdout if isinstance(stdout, str) else ""
        self.stderr = stderr if isinstance(stderr, str) else ""
        self.timed_out = bool(timed_out)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def _decode_utf8_stream(value: bytes | str | None) -> tuple[str, bool]:
    """Return ``(text, valid_utf8)`` while preserving a string invariant."""

    if value is None:
        return "", True
    if isinstance(value, str):
        return value, True
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="strict"), True
        except UnicodeDecodeError:
            return "", False
    return "", False


def default_runner(args: Sequence[str], timeout: float) -> CommandOutcome:
    """Run a bounded command without shell or locale-dependent decoding."""

    try:
        completed = subprocess.run(  # noqa: S603 - explicit bounded arg list
            list(args),
            capture_output=True,
            text=False,
            timeout=timeout,
            check=False,
        )
        stdout, stdout_valid = _decode_utf8_stream(completed.stdout)
        stderr, stderr_valid = _decode_utf8_stream(completed.stderr)
        if not stdout_valid or not stderr_valid:
            return CommandOutcome(
                DECODE_ERROR_EXIT_CODE,
                "",
                "UTF8_DECODE_ERROR",
                False,
            )
        return CommandOutcome(completed.returncode, stdout, stderr, False)
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_valid = _decode_utf8_stream(exc.stdout)
        stderr, stderr_valid = _decode_utf8_stream(exc.stderr)
        if not stdout_valid or not stderr_valid:
            return CommandOutcome(
                DECODE_ERROR_EXIT_CODE,
                "",
                "UTF8_DECODE_ERROR",
                True,
            )
        return CommandOutcome(-1, stdout, stderr, True)


def run_git(
    args: Sequence[str],
    runner: CommandRunner = default_runner,
    timeout: float = 30.0,
) -> CommandOutcome:
    return runner(["git", *args], timeout)


def run_gh(
    args: Sequence[str],
    runner: CommandRunner = default_runner,
    timeout: float = 30.0,
) -> CommandOutcome:
    return runner(["gh", *args], timeout)


def _bounded_text(value: str, max_length: int) -> str:
    stripped = value.strip()
    return stripped[:max_length] if len(stripped) > max_length else stripped


def _parse_json_object_required(stdout: str, what: str) -> Mapping[str, Any]:
    text = stdout.strip()
    if not text:
        raise ContextError(f"{what}: empty output")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"{what}: invalid JSON: {exc}") from exc
    if not isinstance(parsed, Mapping):
        raise ContextError(
            f"{what}: expected JSON object, got {type(parsed).__name__}"
        )
    return parsed


def _parse_json_array_required(stdout: str, what: str) -> list[Any]:
    text = stdout.strip()
    if not text:
        raise ContextError(f"{what}: empty output")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextError(f"{what}: invalid JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise ContextError(
            f"{what}: expected JSON array, got {type(parsed).__name__}"
        )
    return parsed


def collect_context(
    repository: str,
    *,
    goal_issue: int = 90,
    active_pr: int | None = None,
    runner: CommandRunner = default_runner,
) -> Mapping[str, Any]:
    default_branch = _git_default_branch(runner)
    local_main_sha = _git_branch_sha_required(default_branch, runner)
    github_main_sha = _gh_main_sha_required(repository, runner)
    if github_main_sha != local_main_sha:
        raise ContextError(
            "GitHub main does not match local origin/main: "
            f"{github_main_sha}!={local_main_sha}"
        )

    current_branch = _git_current_branch(runner)
    current_head = _git_current_head(runner)
    worktree_clean = _git_worktree_clean(runner)
    open_issues = _gh_open_issues(repository, runner)
    open_prs = _gh_open_prs(repository, runner)
    commits = _git_recent_commits(default_branch, runner)
    issue_goal = _gh_issue_goal(repository, goal_issue, runner)

    if active_pr is None:
        active_pr = _derive_active_pr(repository, current_branch, runner)
    pr_facts = _gh_pr_facts(
        repository,
        active_pr,
        runner,
        exact_head=current_head,
    )

    return {
        "repository": repository,
        "default_branch": default_branch,
        "main_sha": github_main_sha,
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
    outcome = run_git(
        ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        runner,
    )
    if not outcome.ok or not outcome.stdout.strip():
        raise ContextError(
            "git default-branch failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    return outcome.stdout.strip().split("/", 1)[-1]


def _git_branch_sha_required(branch: str, runner: CommandRunner) -> str:
    outcome = run_git(
        ["rev-parse", f"refs/remotes/origin/{branch}"],
        runner,
    )
    if not outcome.ok or not outcome.stdout.strip():
        raise ContextError(
            f"git rev-parse origin/{branch} failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    return outcome.stdout.strip()


def _git_current_branch(runner: CommandRunner) -> str:
    outcome = run_git(["branch", "--show-current"], runner)
    if not outcome.ok:
        raise ContextError(
            "git branch --show-current failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    return outcome.stdout.strip() or "HEAD"


def _git_current_head(runner: CommandRunner) -> str:
    outcome = run_git(["rev-parse", "HEAD"], runner)
    if not outcome.ok:
        raise ContextError(
            "git rev-parse HEAD failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    return outcome.stdout.strip()


def _git_worktree_clean(runner: CommandRunner) -> bool:
    outcome = run_git(["status", "--porcelain"], runner)
    if not outcome.ok:
        raise ContextError(
            "git status failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    return outcome.stdout.strip() == ""


def _gh_main_sha_required(repository: str, runner: CommandRunner) -> str:
    outcome = run_gh(
        ["api", f"repos/{repository}/git/refs/heads/main", "--method", "GET"],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            "gh api refs/heads/main failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    raw = _parse_json_object_required(
        outcome.stdout,
        "gh api refs/heads/main",
    )
    obj = raw.get("object")
    if not isinstance(obj, Mapping):
        raise ContextError("gh api refs/heads/main: missing object")
    sha = str(obj.get("sha", "") or "").strip().lower()
    if not _is_full_sha(sha):
        raise ContextError(
            "gh api refs/heads/main: missing or malformed object.sha"
        )
    return sha


def _gh_open_issues(
    repository: str,
    runner: CommandRunner,
) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    for page in range(1, MAX_ISSUE_PAGES + 1):
        outcome = run_gh(
            [
                "api",
                f"repos/{repository}/issues",
                "--method",
                "GET",
                "--field",
                "state=open",
                "--field",
                f"per_page={PAGE_SIZE}",
                "--field",
                f"page={page}",
            ],
            runner,
        )
        if not outcome.ok:
            raise ContextError(
                f"gh api issues page {page} failed "
                f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
            )
        parsed = _parse_json_array_required(
            outcome.stdout,
            f"gh api issues page {page}",
        )
        if not parsed:
            break
        for raw in parsed:
            if not isinstance(raw, Mapping):
                raise ContextError(
                    f"gh api issues page {page}: non-object entry"
                )
            if "pull_request" in raw:
                continue
            if "number" not in raw or "title" not in raw:
                raise ContextError(
                    f"gh api issues page {page}: missing number/title"
                )
            labels_raw = raw.get("labels", [])
            if not isinstance(labels_raw, list):
                labels_raw = []
            labels = [
                _bounded_text(str(label.get("name", "")), MAX_LABEL_LENGTH)
                for label in labels_raw[:MAX_LABELS]
                if isinstance(label, Mapping)
                and str(label.get("name", "")).strip()
            ]
            items.append(
                {
                    "number": raw.get("number"),
                    "title": _bounded_text(
                        str(raw.get("title", "")),
                        MAX_TITLE_LENGTH,
                    ),
                    "labels": labels,
                }
            )
            if len(items) >= MAX_TOTAL_ISSUES:
                raise ContextError(
                    f"gh api issues: exceeded safety cap {MAX_TOTAL_ISSUES}"
                )
        if len(parsed) < PAGE_SIZE:
            break
    items.sort(key=lambda item: (item.get("number") or 0, item.get("title") or ""))
    return items[:MAX_ISSUES]


def _gh_open_prs(
    repository: str,
    runner: CommandRunner,
) -> list[Mapping[str, Any]]:
    outcome = run_gh(
        [
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
            "--limit",
            str(MAX_PRS),
            "--json",
            "number,title,isDraft,headRefName,headRefOid,baseRefName",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            "gh pr list failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    parsed = _parse_json_array_required(outcome.stdout, "gh pr list")
    items: list[Mapping[str, Any]] = []
    for raw in parsed[:MAX_PRS]:
        if not isinstance(raw, Mapping):
            raise ContextError("gh pr list: non-object entry")
        items.append(
            {
                "number": raw.get("number"),
                "title": _bounded_text(
                    str(raw.get("title", "")),
                    MAX_TITLE_LENGTH,
                ),
                "draft": bool(raw.get("isDraft", False)),
                "head_ref": _bounded_text(
                    str(raw.get("headRefName", "")),
                    MAX_LABEL_LENGTH,
                ),
                "head_sha": str(raw.get("headRefOid", "")).strip().lower(),
                "base_ref": _bounded_text(
                    str(raw.get("baseRefName", "")),
                    MAX_LABEL_LENGTH,
                ),
            }
        )
    items.sort(key=lambda item: (item.get("number") or 0, item.get("title") or ""))
    return items


def _gh_issue_goal(
    repository: str,
    issue_number: int,
    runner: CommandRunner,
) -> Mapping[str, Any]:
    outcome = run_gh(
        [
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repository,
            "--json",
            "number,title,body",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            f"gh issue view {issue_number} failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    raw = _parse_json_object_required(
        outcome.stdout,
        f"gh issue view {issue_number}",
    )
    return {
        "number": raw.get("number", issue_number),
        "title": _bounded_text(
            str(raw.get("title", "")),
            MAX_TITLE_LENGTH,
        ),
        "goal_excerpt": _bounded_text(
            str(raw.get("body", "")),
            MAX_BODY_LENGTH,
        ),
    }


def _derive_active_pr(
    repository: str,
    branch: str,
    runner: CommandRunner,
) -> int:
    owner = repository.split("/", 1)[0]
    outcome = run_gh(
        [
            "api",
            f"repos/{repository}/pulls",
            "--method",
            "GET",
            "--field",
            f"head={owner}:{branch}",
            "--field",
            "state=open",
            "--field",
            "per_page=10",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            "gh api pulls (derive) failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    parsed = _parse_json_array_required(
        outcome.stdout,
        "gh api pulls (derive)",
    )
    if len(parsed) == 0:
        raise ContextError(
            f"gh api pulls (derive): no open PR for branch {branch}"
        )
    if len(parsed) > 1:
        raise ContextError(
            f"gh api pulls (derive): multiple open PRs for branch {branch}"
        )
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
    outcome = run_gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repository,
            "--json",
            "number,title,isDraft,state,headRefName,headRefOid,baseRefName",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            f"gh pr view {pr_number} failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    raw = _parse_json_object_required(
        outcome.stdout,
        f"gh pr view {pr_number}",
    )
    local_head = exact_head.strip().lower()
    pr_head_raw = raw.get("headRefOid")
    if not isinstance(pr_head_raw, str):
        raise ContextError(
            f"gh pr view {pr_number}: missing or malformed headRefOid"
        )
    pr_head = pr_head_raw.strip().lower()
    if not _is_full_sha(local_head):
        raise ContextError("local HEAD is missing or malformed")
    if not _is_full_sha(pr_head):
        raise ContextError(
            f"gh pr view {pr_number}: missing or malformed headRefOid"
        )
    if pr_head != local_head:
        raise ContextError(
            f"PR headRefOid does not match local HEAD: {pr_head}!={local_head}"
        )
    checks = _gh_check_runs(repository, local_head, runner)
    return {
        "number": raw.get("number", pr_number),
        "title": _bounded_text(
            str(raw.get("title", "")),
            MAX_TITLE_LENGTH,
        ),
        "draft": bool(raw.get("isDraft", False)),
        "state": str(raw.get("state", "")),
        "head_ref": _bounded_text(
            str(raw.get("headRefName", "")),
            MAX_LABEL_LENGTH,
        ),
        "head_sha": pr_head,
        "base_ref": _bounded_text(
            str(raw.get("baseRefName", "")),
            MAX_LABEL_LENGTH,
        ),
        "exact_head": local_head,
        "checks": checks,
    }


def _gh_check_runs(
    repository: str,
    head_sha: str,
    runner: CommandRunner,
) -> list[Mapping[str, Any]]:
    sha = head_sha.strip().lower()
    if not sha:
        raise ContextError("gh api check-runs: empty head SHA")
    items: list[Mapping[str, Any]] = []
    expected_total: int | None = None
    for page in range(1, MAX_CHECK_PAGES + 1):
        outcome = run_gh(
            [
                "api",
                f"repos/{repository}/commits/{sha}/check-runs",
                "--method",
                "GET",
                "--field",
                f"per_page={PAGE_SIZE}",
                "--field",
                f"page={page}",
            ],
            runner,
        )
        if not outcome.ok:
            raise ContextError(
                f"gh api check-runs page {page} failed "
                f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
            )
        raw = _parse_json_object_required(
            outcome.stdout,
            f"gh api check-runs page {page}",
        )
        total_count = raw.get("total_count")
        if (
            isinstance(total_count, bool)
            or not isinstance(total_count, int)
            or total_count < 0
        ):
            raise ContextError(
                f"gh api check-runs page {page}: missing or malformed total_count"
            )
        if total_count > MAX_TOTAL_CHECK_RUNS:
            raise ContextError(
                f"gh api check-runs: total_count {total_count} exceeds "
                f"safety cap {MAX_TOTAL_CHECK_RUNS}"
            )
        if expected_total is None:
            expected_total = total_count
            required_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
            if required_pages > MAX_CHECK_PAGES:
                raise ContextError(
                    "gh api check-runs: pagination requires "
                    f"{required_pages} pages, cap is {MAX_CHECK_PAGES}"
                )
        elif total_count != expected_total:
            raise ContextError(
                f"gh api check-runs page {page}: total_count changed "
                f"from {expected_total} to {total_count}"
            )
        runs = raw.get("check_runs")
        if not isinstance(runs, list):
            raise ContextError(
                f"gh api check-runs page {page}: missing check_runs array"
            )
        if len(runs) > PAGE_SIZE:
            raise ContextError(
                f"gh api check-runs page {page}: page exceeds per_page={PAGE_SIZE}"
            )
        for run in runs:
            if not isinstance(run, Mapping):
                raise ContextError(
                    f"gh api check-runs page {page}: non-object run"
                )
            name = run.get("name")
            status = run.get("status")
            conclusion = run.get("conclusion")
            run_url = run.get("html_url")
            if not isinstance(name, str) or not name.strip():
                raise ContextError(
                    f"gh api check-runs page {page}: missing or malformed name"
                )
            if not isinstance(status, str) or not status.strip():
                raise ContextError(
                    f"gh api check-runs page {page}: missing or malformed status"
                )
            if conclusion is not None and not isinstance(conclusion, str):
                raise ContextError(
                    f"gh api check-runs page {page}: malformed conclusion"
                )
            if run_url is not None and not isinstance(run_url, str):
                raise ContextError(
                    f"gh api check-runs page {page}: malformed html_url"
                )
            items.append(
                {
                    "name": _bounded_text(name, MAX_LABEL_LENGTH),
                    "status": status.strip().lower(),
                    "conclusion": (conclusion or "").strip().lower(),
                    "run_url": _bounded_text(run_url or "", 200),
                }
            )
        if len(items) > total_count:
            raise ContextError(
                f"gh api check-runs: returned {len(items)} records "
                f"but total_count is {total_count}"
            )
        if len(items) == total_count:
            return items
        if not runs or len(runs) < PAGE_SIZE:
            raise ContextError(
                "gh api check-runs: incomplete pagination returned "
                f"{len(items)} of {total_count}"
            )
    if expected_total is None or len(items) != expected_total:
        raise ContextError(
            "gh api check-runs: pagination cap reached before total_count "
            "was satisfied"
        )
    return items


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(
        character in "0123456789abcdef" for character in value
    )


def _git_recent_commits(
    branch: str,
    runner: CommandRunner,
) -> list[Mapping[str, Any]]:
    outcome = run_git(
        [
            "log",
            "--oneline",
            "-n",
            str(MAX_COMMITS),
            f"refs/remotes/origin/{branch}",
        ],
        runner,
    )
    if not outcome.ok:
        raise ContextError(
            "git log failed "
            f"(exit={outcome.exit_code}, timed_out={outcome.timed_out})"
        )
    commits: list[Mapping[str, Any]] = []
    for line in outcome.stdout.splitlines()[:MAX_COMMITS]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        commits.append(
            {
                "sha": parts[0].lower(),
                "title": _bounded_text(
                    parts[1] if len(parts) > 1 else "",
                    MAX_TITLE_LENGTH,
                ),
            }
        )
    return commits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect a bounded Codex Supervisor context (fail-closed v0.5)"
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--goal-issue", type=int, default=90)
    parser.add_argument("--active-pr", type=int, default=None)
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    try:
        context = collect_context(
            args.repository,
            goal_issue=args.goal_issue,
            active_pr=args.active_pr,
        )
    except ContextError as exc:
        print(
            json.dumps(
                {"error": str(exc), "context": None},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
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

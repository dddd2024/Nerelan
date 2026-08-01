#!/usr/bin/env python3
"""Thin Codex Supervisor publication planner (v0.4, fail-closed).

Searches existing Issues (ALL states — open and closed) for the cycle marker
via paginated ``gh api``, then produces a bounded publication plan:
``create_issue``, ``update_issue``, or ``no_op``. Never closes issues, never
modifies PRs, never touches main.

Default mode is **dry-run** (zero GitHub writes). GitHub writes happen only
when ``--live`` is passed explicitly, and even then only ``create_issue`` /
``update_issue`` (no merge, no close, no main push).

v0.3 changes (fail-closed closure):
- Issue discovery uses paginated ``gh api repos/<repo>/issues?state=all``
  (NOT ``gh issue list --state all --limit 100``). Pull Request entries
  returned by the ``/issues`` endpoint are filtered out. Any page failure,
  invalid JSON, missing number/body/state, or over-cap result is fail-closed.
  Malformed entries are NOT silently skipped.
- Remote main verification queries ``gh api repos/<repo>/git/refs/heads/main``
  before any live write. The GitHub-side main SHA must equal
  ``audited_main_sha`` AND the local ``origin/main`` must equal the GitHub
  main SHA. Any drift → zero writes.
- Closed-Issue Marker handling: same content → ``no_op``; different content
  → ``CLOSED_MARKER_REQUIRES_OWNER`` (zero writes, no auto-edit, no reopen,
  no surrogate create). Same Marker in two Issues → fail-closed. Multiple
  Markers in one Issue → fail-closed.
- Single-machine publish lock: a runtime-only exclusive lock (stdlib only)
  is acquired in the system temp directory before any live guard / Marker
  query / GitHub mutation. Lock is atomically acquired (``O_EXCL``) and
  released in ``finally``. If the lock already exists, zero writes. This
  lock does NOT provide cross-machine distributed atomicity.

Fail-closed rules (carried from v0.2):
- Discovery failure (gh failure, invalid JSON, incomplete results) → zero writes.
- Marker found in two Issues → fail-closed, zero writes.
- Body exceeding ``MAX_BODY_LENGTH`` → rejected (NOT truncated).
- Live write re-queries marker (TOCTOU guard) before any ``gh issue`` write.

Pure standard library. No real Codex/model calls.

Usage (dry-run):
    python scripts/supervisor_publish.py plan \\
        --result audit_result.json \\
        --repository dddd2024/reverse-agent \\
        --main-sha 16526801bda2a816fc707342f903c1ad037de9bd
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from typing import Any, Callable, Mapping, Sequence

# Import the validator (same scripts directory). When run as a script this
# works because Python adds the script's directory to sys.path[0].
from supervisor_validate import (
    MARKER_TEMPLATE,
    POLICY_VERSION,
    SCHEMA_VERSION,
    compute_cycle_key,
    find_all_marker_keys,
    find_marker_key,
    make_marker,
    validate_audit_result,
)
from supervisor_context import CommandOutcome, CommandRunner, default_runner, run_git, run_gh

ACTION_CREATE_ISSUE = "create_issue"
ACTION_UPDATE_ISSUE = "update_issue"
ACTION_NO_OP = "no_op"

MAX_BODY_LENGTH = 8000
MAX_TITLE_LENGTH = 200

# Pagination safety caps.
MAX_ISSUE_PAGES = 10
PAGE_SIZE = 100
MAX_TOTAL_ISSUES = 500  # safety cap across all pages

# Expected live-guard constants.
EXPECTED_OWNER = "dddd2024"
EXPECTED_BRANCH = "agent/codex-supervisor-foundation-v0"

# Finite, machine-readable error codes.
ERR_DISCOVERY_FAILED = "DISCOVERY_FAILED"
ERR_DUPLICATE_MARKER = "DUPLICATE_MARKER"
ERR_MULTI_MARKER_IN_ISSUE = "MULTI_MARKER_IN_ISSUE"
ERR_CLOSED_MARKER_REQUIRES_OWNER = "CLOSED_MARKER_REQUIRES_OWNER"
ERR_BODY_TOO_LONG = "BODY_TOO_LONG"
ERR_LIVE_GUARD_OWNER = "LIVE_GUARD_OWNER"
ERR_LIVE_GUARD_WORKTREE_DIRTY = "LIVE_GUARD_WORKTREE_DIRTY"
ERR_LIVE_GUARD_BRANCH = "LIVE_GUARD_BRANCH"
ERR_LIVE_GUARD_MAIN_DRIFT = "LIVE_GUARD_MAIN_DRIFT"
ERR_LIVE_GUARD_REMOTE_MAIN = "LIVE_GUARD_REMOTE_MAIN"
ERR_LIVE_GUARD_LOCAL_MAIN = "LIVE_GUARD_LOCAL_MAIN"
ERR_LIVE_GUARD_MARKER_QUERY = "LIVE_GUARD_MARKER_QUERY"
ERR_LIVE_GUARD_DUPLICATE_MARKER = "LIVE_GUARD_DUPLICATE_MARKER"
ERR_TOCTOU = "TOCTOU_MARKER_APPEARED"
ERR_LOCK_BUSY = "LOCK_BUSY"


# =====================================================================
# Single-machine publish lock (Task 7).
#
# Runtime-only exclusive lock backed by an atomic file creation in the
# system temp directory. Pure standard library. Does NOT provide cross-
# machine distributed atomicity — it only serializes live publications
# on a single host.
# =====================================================================


class PublishLock:
    """Runtime-only exclusive lock for live publication.

    Acquired atomically via ``O_CREAT | O_EXCL`` on a path in the system
    temp directory (NOT inside the repository). Released in ``__exit__``
    via ``os.unlink``. If the lock file already exists, acquisition fails
    and zero writes must be performed.

    This lock is single-machine only. It does NOT coordinate across hosts
    and does NOT coordinate with other processes that bypass it. It is a
    guard against accidental concurrent live publications on the same
    machine (e.g. two terminals running ``--live`` in parallel).
    """

    def __init__(self, *, name: str = "reverse-agent-supervisor-publish.lock") -> None:
        self._name = name
        self._path: str | None = None
        self._owned = False

    @property
    def path(self) -> str | None:
        return self._path

    def __enter__(self) -> "PublishLock":
        path = os.path.join(tempfile.gettempdir(), self._name)
        try:
            # O_CREAT | O_EXCL: atomic create. Fails if the file exists.
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            self._owned = False
            self._path = path
            raise LockBusyError(path)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
        finally:
            os.close(fd)
        self._path = path
        self._owned = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._owned and self._path is not None:
            try:
                os.unlink(self._path)
            except FileNotFoundError:
                pass
            self._owned = False
            self._path = None


class LockBusyError(RuntimeError):
    """Raised when the publish lock is already held by another process."""


# =====================================================================
# Body construction and content digest.
# =====================================================================


def build_issue_body(next_task: Mapping[str, Any], marker: str) -> str:
    """Build the bounded issue body for a next_task, embedding the marker.

    Raises ``ValueError`` if the body exceeds ``MAX_BODY_LENGTH`` (fail-closed,
    no truncation).
    """

    forbidden = next_task.get("forbidden_scope", []) or []
    operations = next_task.get("requested_operations", []) or []
    lines = [
        marker,
        "",
        f"# {next_task['title']}",
        "",
        f"**Goal:** {next_task['goal']}",
        "",
        "## Allowed scope",
    ]
    lines.extend(f"- {item}" for item in next_task.get("allowed_scope", []))
    lines.append("")
    lines.append("## Forbidden scope")
    if forbidden:
        lines.extend(f"- {item}" for item in forbidden)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Requested operations")
    if operations:
        lines.extend(f"- {op}" for op in operations)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Acceptance checks")
    lines.extend(f"- {item}" for item in next_task.get("acceptance_checks", []))
    lines.append("")
    lines.append("## Execution prompt")
    lines.append(next_task.get("execution_prompt", ""))
    body = "\n".join(lines)
    if len(body) > MAX_BODY_LENGTH:
        raise ValueError(f"{ERR_BODY_TOO_LONG}:{len(body)}>{MAX_BODY_LENGTH}")
    return body


def content_digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# =====================================================================
# Publication planning.
# =====================================================================


def plan_publication(
    *,
    audit_result: Mapping[str, Any],
    repository: str,
    main_sha: str,
    existing_issues: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Return a bounded publication plan (fail-closed).

    ``existing_issues`` is a list of ``{"number", "title", "body", "state"}``
    dicts (from paginated ``gh api``). The plan never performs writes; the
    caller decides whether to apply it (dry-run vs --live).

    Fail-closed:
    - If two Issues carry the same marker, returns a no-op with
      ``ERR_DUPLICATE_MARKER`` (zero writes).
    - If a single Issue carries multiple distinct markers, returns a no-op
      with ``ERR_MULTI_MARKER_IN_ISSUE`` (zero writes).
    - If a closed Issue carries the same marker with identical content,
      returns no_op (no duplicate create).
    - If a closed Issue carries the same marker with different content,
      returns no-op with ``ERR_CLOSED_MARKER_REQUIRES_OWNER`` (zero writes,
      no auto-edit, no reopen, no surrogate create).
    """

    ok, errors, parsed = validate_audit_result(
        audit_result, expected_repository=repository, expected_main_sha=main_sha
    )
    if not ok or parsed is None:
        return {
            "action": ACTION_NO_OP,
            "schema_valid": False,
            "policy_allowed": False,
            "errors": errors,
            "marker": None,
            "idempotency_key": None,
            "target_issue": None,
            "title": None,
            "body": None,
            "content_digest": None,
        }

    next_task = parsed.get("next_task")
    if next_task is None:
        return {
            "action": ACTION_NO_OP,
            "schema_valid": True,
            "policy_allowed": True,
            "errors": [],
            "marker": None,
            "idempotency_key": None,
            "target_issue": None,
            "title": None,
            "body": None,
            "content_digest": None,
        }

    key = compute_cycle_key(
        repository=repository,
        main_sha=main_sha,
        schema_version=SCHEMA_VERSION,
        policy_version=POLICY_VERSION,
        goal=next_task["goal"],
        allowed_scope=next_task["allowed_scope"],
        forbidden_scope=next_task["forbidden_scope"],
        requested_operations=next_task["requested_operations"],
        acceptance_checks=next_task["acceptance_checks"],
    )
    marker = make_marker(key)
    title = next_task["title"]

    # Build body (fail-closed on oversize).
    try:
        body = build_issue_body(next_task, marker)
    except ValueError as exc:
        return {
            "action": ACTION_NO_OP,
            "schema_valid": True,
            "policy_allowed": False,
            "errors": [str(exc)],
            "marker": marker,
            "idempotency_key": key,
            "target_issue": None,
            "title": title,
            "body": None,
            "content_digest": None,
        }
    digest = content_digest(body)

    # Multi-marker-within-one-Issue check (fail-closed).
    for issue in existing_issues:
        issue_body = str(issue.get("body", "") or "")
        keys_in_issue = find_all_marker_keys(issue_body)
        if len(keys_in_issue) > 1:
            return {
                "action": ACTION_NO_OP,
                "schema_valid": True,
                "policy_allowed": False,
                "errors": [f"{ERR_MULTI_MARKER_IN_ISSUE}:issue={issue.get('number')} count={len(keys_in_issue)}"],
                "marker": marker,
                "idempotency_key": key,
                "target_issue": None,
                "title": title,
                "body": body,
                "content_digest": digest,
            }

    # Scan ALL issues (open + closed) for the marker.
    matched: list[Mapping[str, Any]] = []
    for issue in existing_issues:
        issue_body = str(issue.get("body", "") or "")
        if find_marker_key(issue_body) == key:
            matched.append(issue)

    if len(matched) > 1:
        # Fail-closed: duplicate marker in two issues.
        return {
            "action": ACTION_NO_OP,
            "schema_valid": True,
            "policy_allowed": False,
            "errors": [f"{ERR_DUPLICATE_MARKER}:{len(matched)} issues"],
            "marker": marker,
            "idempotency_key": key,
            "target_issue": None,
            "title": title,
            "body": body,
            "content_digest": digest,
        }

    if len(matched) == 1:
        matched_issue = matched[0]
        matched_number = matched_issue.get("number")
        matched_state = str(matched_issue.get("state", "") or "").upper()
        matched_body = str(matched_issue.get("body", "") or "")
        same_content = _normalize_body(matched_body) == _normalize_body(body)

        # Closed-Issue Marker handling (Task 4).
        if matched_state == "CLOSED":
            if same_content:
                # Identical content in closed Issue: no duplicate create.
                return {
                    "action": ACTION_NO_OP,
                    "schema_valid": True,
                    "policy_allowed": True,
                    "errors": [],
                    "marker": marker,
                    "idempotency_key": key,
                    "target_issue": matched_number,
                    "title": title,
                    "body": body,
                    "content_digest": digest,
                    "closed_match": True,
                }
            # Different content in closed Issue: requires owner action.
            # No auto-edit, no reopen, no surrogate create.
            return {
                "action": ACTION_NO_OP,
                "schema_valid": True,
                "policy_allowed": False,
                "errors": [f"{ERR_CLOSED_MARKER_REQUIRES_OWNER}:issue={matched_number}"],
                "marker": marker,
                "idempotency_key": key,
                "target_issue": matched_number,
                "title": title,
                "body": body,
                "content_digest": digest,
                "closed_match": True,
            }

        # Open Issue with marker.
        if same_content:
            return {
                "action": ACTION_NO_OP,
                "schema_valid": True,
                "policy_allowed": True,
                "errors": [],
                "marker": marker,
                "idempotency_key": key,
                "target_issue": matched_number,
                "title": title,
                "body": body,
                "content_digest": digest,
            }
        return {
            "action": ACTION_UPDATE_ISSUE,
            "schema_valid": True,
            "policy_allowed": True,
            "errors": [],
            "marker": marker,
            "idempotency_key": key,
            "target_issue": matched_number,
            "title": title,
            "body": body,
            "content_digest": digest,
            "planning_audit_result": parsed,
            "preimage_title_digest": content_digest(
                str(matched_issue.get("title", "") or "")
            ),
            "preimage_body_digest": content_digest(matched_body),
        }

    # No match — create. (Closed issues with same marker would have matched above.)
    return {
        "action": ACTION_CREATE_ISSUE,
        "schema_valid": True,
        "policy_allowed": True,
        "errors": [],
        "marker": marker,
        "idempotency_key": key,
        "target_issue": None,
        "title": title,
        "body": body,
        "content_digest": digest,
    }


def _normalize_body(body: str) -> str:
    return " ".join(body.split())


# =====================================================================
# Issue discovery (Task 2): paginated gh api, filter PRs, fail-closed.
# =====================================================================


def fetch_existing_issues(
    repository: str,
    *,
    runner: CommandRunner = default_runner,
) -> tuple[list[Mapping[str, Any]], str | None]:
    """Fetch bounded Issues (ALL states) via paginated ``gh api``.

    Returns ``(issues, error)``. On failure, ``issues`` is empty and
    ``error`` is a non-None string (fail-closed: caller must not write).

    v0.3 changes:
    - Uses ``gh api repos/<repo>/issues?state=all`` with explicit pagination
      (NOT ``gh issue list --state all --limit 100``).
    - Filters out Pull Request entries (the ``/issues`` endpoint includes
      PRs that have a ``pull_request`` field).
    - Any page failure, invalid JSON, missing number/body/state, or
      over-cap result is fail-closed.
    - Malformed entries are NOT silently skipped.
    """

    items: list[Mapping[str, Any]] = []
    for page in range(1, MAX_ISSUE_PAGES + 1):
        outcome = run_gh(
            [
                "api", f"repos/{repository}/issues", "--method", "GET",
                "--field", "state=all",
                "--field", f"per_page={PAGE_SIZE}",
                "--field", f"page={page}",
            ],
            runner,
        )
        if not outcome.ok:
            return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} exit={outcome.exit_code} timed_out={outcome.timed_out}"
        text = outcome.stdout.strip()
        if not text:
            return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} empty output"
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} invalid JSON: {exc}"
        if not isinstance(parsed, list):
            return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} expected array"
        if not parsed:
            break  # empty page — done.
        for raw in parsed:
            if not isinstance(raw, Mapping):
                return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} non-object entry"
            # Filter out PR entries (the /issues endpoint returns PRs too).
            if "pull_request" in raw:
                continue
            # Required fields (fail-closed — no silent skip).
            for required in ("number", "body", "state"):
                if required not in raw:
                    return [], f"{ERR_DISCOVERY_FAILED}:gh api issues page {page} missing {required}"
            items.append({
                "number": raw.get("number"),
                "title": str(raw.get("title", "") or ""),
                "body": str(raw.get("body", "") or ""),
                "state": str(raw.get("state", "") or ""),
            })
            if len(items) >= MAX_TOTAL_ISSUES:
                return [], f"{ERR_DISCOVERY_FAILED}:exceeded safety cap {MAX_TOTAL_ISSUES}"
        if len(parsed) < PAGE_SIZE:
            break  # last page.
    return items, None


# =====================================================================
# Remote main verification (Task 3).
# =====================================================================


def verify_remote_main(
    *,
    repository: str,
    expected_main_sha: str,
    runner: CommandRunner = default_runner,
) -> tuple[bool, list[str]]:
    """Verify GitHub-side main and local origin/main consistency.

    All of the following must hold:
    - ``gh api repos/<repo>/git/refs/heads/main`` succeeds and returns
      a 40-hex SHA equal to ``expected_main_sha``.
    - Local ``git rev-parse refs/remotes/origin/main`` succeeds and returns
      the same SHA as the GitHub-side main.

    Returns ``(ok, errors)``. Any failure → zero writes.
    """

    errors: list[str] = []

    # 1. GitHub-side main via gh api.
    remote_outcome = run_gh(
        ["api", f"repos/{repository}/git/refs/heads/main", "--method", "GET"],
        runner,
    )
    if not remote_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:gh api refs/heads/main failed exit={remote_outcome.exit_code}")
    else:
        text = remote_outcome.stdout.strip()
        if not text:
            errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:gh api refs/heads/main empty output")
        else:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:invalid JSON: {exc}")
                parsed = None
            if isinstance(parsed, Mapping):
                obj = parsed.get("object")
                if not isinstance(obj, Mapping) or "sha" not in obj:
                    errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:missing object.sha")
                else:
                    remote_sha = str(obj.get("sha", "") or "").strip().lower()
                    if not _is_full_sha(remote_sha):
                        errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:invalid sha {remote_sha!r}")
                    elif remote_sha != expected_main_sha.strip().lower():
                        errors.append(f"{ERR_LIVE_GUARD_REMOTE_MAIN}:{remote_sha}!={expected_main_sha}")

    # 2. Local origin/main via git.
    local_outcome = run_git(["rev-parse", "refs/remotes/origin/main"], runner)
    if not local_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_LOCAL_MAIN}:git rev-parse origin/main failed exit={local_outcome.exit_code}")
    else:
        local_sha = local_outcome.stdout.strip().lower()
        if not _is_full_sha(local_sha):
            errors.append(f"{ERR_LIVE_GUARD_LOCAL_MAIN}:invalid sha {local_sha!r}")
        elif local_sha != expected_main_sha.strip().lower():
            errors.append(f"{ERR_LIVE_GUARD_LOCAL_MAIN}:{local_sha}!={expected_main_sha}")

    # Summary code: if any main-drift error was raised, also emit a general
    # MAIN_DRIFT marker so callers checking for the generic code still catch it.
    if any(e.startswith(ERR_LIVE_GUARD_REMOTE_MAIN) or e.startswith(ERR_LIVE_GUARD_LOCAL_MAIN) for e in errors):
        errors.append(f"{ERR_LIVE_GUARD_MAIN_DRIFT}:remote or local main differs from {expected_main_sha}")

    return (len(errors) == 0), errors


def _is_full_sha(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


# =====================================================================
# Live guard (Task 3 integration).
# =====================================================================


def live_guard(
    *,
    repository: str,
    expected_main_sha: str,
    expected_owner: str = EXPECTED_OWNER,
    expected_branch: str = EXPECTED_BRANCH,
    runner: CommandRunner = default_runner,
) -> tuple[bool, list[str]]:
    """Verify pre-conditions before any live GitHub write.

    Checks (v0.3):
    - gh login user is ``expected_owner``.
    - Worktree is clean.
    - Current branch is ``expected_branch`` (and NOT main).
    - GitHub-side main (via ``gh api refs/heads/main``) equals ``expected_main_sha``.
    - Local ``origin/main`` equals the GitHub-side main.
    - Marker query succeeds (no discovery failure, no duplicate marker).

    Returns ``(allowed, errors)``. If any check fails, zero writes occur.
    """

    errors: list[str] = []

    # 1. gh login user.
    user_outcome = run_gh(["api", "user", "--method", "GET", "--jq", ".login"], runner)
    if not user_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_OWNER}:gh api user failed")
    else:
        login = user_outcome.stdout.strip().lower()
        if login != expected_owner.lower():
            errors.append(f"{ERR_LIVE_GUARD_OWNER}:{login}!={expected_owner}")

    # 2. Worktree clean.
    status_outcome = run_git(["status", "--porcelain"], runner)
    if not status_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_WORKTREE_DIRTY}:git status failed")
    elif status_outcome.stdout.strip() != "":
        errors.append(f"{ERR_LIVE_GUARD_WORKTREE_DIRTY}:working tree not clean")

    # 3. Current branch.
    branch_outcome = run_git(["branch", "--show-current"], runner)
    if not branch_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_BRANCH}:git branch failed")
    else:
        branch = branch_outcome.stdout.strip()
        if branch == "main":
            errors.append(f"{ERR_LIVE_GUARD_BRANCH}:on main")
        elif branch != expected_branch:
            errors.append(f"{ERR_LIVE_GUARD_BRANCH}:{branch}!={expected_branch}")

    # 4. Remote main verification (Task 3): GitHub main + local origin/main.
    main_ok, main_errors = verify_remote_main(
        repository=repository,
        expected_main_sha=expected_main_sha,
        runner=runner,
    )
    if not main_ok:
        errors.extend(main_errors)

    if errors:
        return False, errors

    # 5. Marker query complete (re-fetch and check no duplicate).
    issues, discovery_err = fetch_existing_issues(repository, runner=runner)
    if discovery_err is not None:
        errors.append(f"{ERR_LIVE_GUARD_MARKER_QUERY}:{discovery_err}")
        return False, errors

    return True, errors


# =====================================================================
# Plan application (with publish lock — Task 7).
# =====================================================================


def apply_plan(
    plan: Mapping[str, Any],
    *,
    repository: str,
    expected_main_sha: str,
    runner: CommandRunner = default_runner,
    live: bool,
) -> Mapping[str, Any]:
    """Apply a publication plan. No-op unless ``live=True``.

    Even in live mode, only ``create_issue`` / ``update_issue`` are
    performed. Never closes issues, never modifies PRs, never touches main.

    Live guard + TOCTOU re-query are performed before any write. If any
    guard fails, zero writes occur.

    v0.3: the live path is wrapped in a single-machine publish lock
    (:class:`PublishLock`). If the lock is already held, zero writes.
    """

    action = plan.get("action")
    if action == ACTION_NO_OP:
        return {"applied": False, "action": action, "reason": "no_op", "live": live}

    if not live:
        return {"applied": False, "action": action, "reason": "dry_run", "live": False}

    # Single-machine publish lock (Task 7): hold the lock across the entire
    # live path (live guard + TOCTOU re-query + GitHub mutation). If the
    # lock is already held, zero writes.
    try:
        with PublishLock():
            return _apply_plan_locked(
                plan,
                repository=repository,
                expected_main_sha=expected_main_sha,
                runner=runner,
            )
    except LockBusyError as exc:
        return {
            "applied": False,
            "action": action,
            "reason": ERR_LOCK_BUSY,
            "live": True,
            "lock_path": str(exc),
        }


def _apply_plan_locked(
    plan: Mapping[str, Any],
    *,
    repository: str,
    expected_main_sha: str,
    runner: CommandRunner,
) -> Mapping[str, Any]:
    """Apply the plan while holding the publish lock."""

    action = plan.get("action")

    # Live guard: verify pre-conditions (incl. remote main verification).
    guard_ok, guard_errors = live_guard(
        repository=repository,
        expected_main_sha=expected_main_sha,
        runner=runner,
    )
    if not guard_ok:
        return {
            "applied": False,
            "action": action,
            "reason": "live_guard_failed",
            "live": True,
            "guard_errors": guard_errors,
        }

    # TOCTOU: re-query marker right before write.
    key = plan.get("idempotency_key")
    if key is None:
        return {"applied": False, "action": action, "reason": "no_marker_key", "live": True}

    issues, discovery_err = fetch_existing_issues(repository, runner=runner)
    if discovery_err is not None:
        return {
            "applied": False,
            "action": action,
            "reason": "toctou_discovery_failed",
            "live": True,
            "discovery_error": discovery_err,
        }

    matched_numbers = [
        issue.get("number")
        for issue in issues
        if find_marker_key(str(issue.get("body", "") or "")) == key
    ]

    if len(matched_numbers) > 1:
        return {
            "applied": False,
            "action": action,
            "reason": "toctou_duplicate_marker",
            "live": True,
            "matched": matched_numbers,
        }

    if action == ACTION_CREATE_ISSUE:
        # TOCTOU: if marker appeared since plan, fail-closed.
        if matched_numbers:
            return {
                "applied": False,
                "action": action,
                "reason": ERR_TOCTOU,
                "live": True,
                "matched": matched_numbers,
            }
        outcome = run_gh(
            [
                "issue", "create",
                "--repo", repository,
                "--title", str(plan.get("title", "")),
                "--body", str(plan.get("body", "")),
            ],
            runner,
        )
        return {
            "applied": outcome.ok,
            "action": action,
            "live": True,
            "exit_code": outcome.exit_code,
            "issue_url": outcome.stdout.strip() if outcome.ok else None,
        }

    if action == ACTION_UPDATE_ISSUE:
        # Update title AND body together.
        target = plan.get("target_issue")
        if target is None:
            return {"applied": False, "action": action, "reason": "no_target", "live": True}
        target_matches = [issue for issue in issues if issue.get("number") == target]
        if len(target_matches) != 1 or target not in matched_numbers:
            return {
                "applied": False,
                "action": action,
                "reason": ERR_TOCTOU,
                "live": True,
                "matched": matched_numbers,
            }
        target_issue = target_matches[0]
        target_title = str(target_issue.get("title", "") or "")
        target_body = str(target_issue.get("body", "") or "")
        target_markers = find_all_marker_keys(target_body)
        if str(target_issue.get("state", "") or "").upper() != "OPEN":
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_target_not_open",
                "live": True,
            }
        if len(target_markers) != 1 or target_markers[0] != key:
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_marker_changed",
                "live": True,
            }
        if content_digest(target_title) != plan.get("preimage_title_digest"):
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_title_changed",
                "live": True,
            }
        if content_digest(target_body) != plan.get("preimage_body_digest"):
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_body_changed",
                "live": True,
            }
        planning_audit_result = plan.get("planning_audit_result")
        if not isinstance(planning_audit_result, Mapping):
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_missing_planning_input",
                "live": True,
            }
        fresh_plan = plan_publication(
            audit_result=planning_audit_result,
            repository=repository,
            main_sha=expected_main_sha,
            existing_issues=issues,
        )
        if (
            fresh_plan.get("action") != ACTION_UPDATE_ISSUE
            or fresh_plan.get("target_issue") != target
            or fresh_plan.get("marker") != plan.get("marker")
        ):
            return {
                "applied": False,
                "action": action,
                "reason": "toctou_fresh_plan_changed",
                "live": True,
            }
        outcome = run_gh(
            [
                "issue", "edit", str(target),
                "--repo", repository,
                "--title", str(plan.get("title", "")),
                "--body", str(plan.get("body", "")),
            ],
            runner,
        )
        return {
            "applied": outcome.ok,
            "action": action,
            "live": True,
            "exit_code": outcome.exit_code,
            "target_issue": target,
        }

    return {"applied": False, "action": action, "reason": "unknown_action", "live": True}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Codex Supervisor publication (dry-run by default, fail-closed v0.3)")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Produce a dry-run publication plan")
    plan_parser.add_argument("--result", required=True, help="Path to audit result JSON")
    plan_parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    plan_parser.add_argument("--main-sha", required=True, help="Exact main SHA (40 hex chars)")
    plan_parser.add_argument("--existing-issues", help="Path to JSON file of existing issues (default: query gh api)")
    plan_parser.add_argument("--live", action="store_true", help="Apply the plan (writes to GitHub). Default is dry-run.")

    args = parser.parse_args(argv)

    with open(args.result, encoding="utf-8") as handle:
        audit_result = json.load(handle)

    if args.existing_issues:
        with open(args.existing_issues, encoding="utf-8") as handle:
            existing_issues = json.load(handle)
        discovery_err: str | None = None
    else:
        existing_issues, discovery_err = fetch_existing_issues(args.repository)

    if discovery_err is not None:
        plan = {
            "action": ACTION_NO_OP,
            "schema_valid": False,
            "policy_allowed": False,
            "errors": [discovery_err],
            "marker": None,
            "idempotency_key": None,
            "target_issue": None,
            "title": None,
            "body": None,
            "content_digest": None,
        }
    else:
        plan = plan_publication(
            audit_result=audit_result,
            repository=args.repository,
            main_sha=args.main_sha,
            existing_issues=existing_issues,
        )

    if args.live and plan.get("action") in (ACTION_CREATE_ISSUE, ACTION_UPDATE_ISSUE):
        plan["apply_result"] = apply_plan(
            plan,
            repository=args.repository,
            expected_main_sha=args.main_sha,
            live=True,
        )

    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if plan.get("schema_valid") else 1


if __name__ == "__main__":
    sys.exit(main())

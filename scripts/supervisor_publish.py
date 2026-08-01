#!/usr/bin/env python3
"""Thin Codex Supervisor publication planner (quota-free v0.2, fail-closed).

Searches existing Issues (ALL states — open and closed) for the cycle marker
via ``gh``, then produces a bounded publication plan: ``create_issue``,
``update_issue``, or ``no_op``. Never closes issues, never modifies PRs,
never touches main.

Default mode is **dry-run** (zero GitHub writes). GitHub writes happen only
when ``--live`` is passed explicitly, and even then only ``create_issue`` /
``update_issue`` (no merge, no close, no main push).

Fail-closed rules:
- Discovery failure (gh failure, invalid JSON, incomplete results) → zero writes.
- Marker found in two Issues → fail-closed, zero writes.
- Closed Issue with same marker → no duplicate create.
- Live write re-queries marker (TOCTOU guard) before any ``gh issue`` write.
- Body exceeding ``MAX_BODY_LENGTH`` → rejected (NOT truncated).
- Live guard verifies owner, clean worktree, branch, main SHA before any write.

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
import sys
from typing import Any, Callable, Mapping, Sequence

# Import the validator (same scripts directory). When run as a script this
# works because Python adds the script's directory to sys.path[0].
from supervisor_validate import (
    MARKER_TEMPLATE,
    POLICY_VERSION,
    SCHEMA_VERSION,
    compute_cycle_key,
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

# Expected live-guard constants.
EXPECTED_OWNER = "dddd2024"
EXPECTED_BRANCH = "agent/codex-supervisor-foundation-v0"

# Finite, machine-readable error codes.
ERR_DISCOVERY_FAILED = "DISCOVERY_FAILED"
ERR_DUPLICATE_MARKER = "DUPLICATE_MARKER"
ERR_BODY_TOO_LONG = "BODY_TOO_LONG"
ERR_LIVE_GUARD_OWNER = "LIVE_GUARD_OWNER"
ERR_LIVE_GUARD_WORKTREE_DIRTY = "LIVE_GUARD_WORKTREE_DIRTY"
ERR_LIVE_GUARD_BRANCH = "LIVE_GUARD_BRANCH"
ERR_LIVE_GUARD_MAIN_DRIFT = "LIVE_GUARD_MAIN_DRIFT"
ERR_LIVE_GUARD_MARKER_QUERY = "LIVE_GUARD_MARKER_QUERY"
ERR_LIVE_GUARD_DUPLICATE_MARKER = "LIVE_GUARD_DUPLICATE_MARKER"
ERR_TOCTOU = "TOCTOU_MARKER_APPEARED"


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


def plan_publication(
    *,
    audit_result: Mapping[str, Any],
    repository: str,
    main_sha: str,
    existing_issues: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Return a bounded publication plan (fail-closed).

    ``existing_issues`` is a list of ``{"number", "title", "body", "state"}``
    dicts (typically from ``gh issue list --state all``). The plan never
    performs writes; the caller decides whether to apply it (dry-run vs --live).

    Fail-closed:
    - If two Issues carry the same marker, returns a no-op with
      ``ERR_DUPLICATE_MARKER`` (zero writes).
    - If a closed Issue carries the same marker, returns no-op (no duplicate create).
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
        matched_body = str(matched_issue.get("body", "") or "")
        if _normalize_body(matched_body) == _normalize_body(body):
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


def fetch_existing_issues(
    repository: str,
    *,
    runner: CommandRunner = default_runner,
) -> tuple[list[Mapping[str, Any]], str | None]:
    """Fetch bounded Issues (ALL states) via gh.

    Returns ``(issues, error)``. On failure, ``issues`` is empty and
    ``error`` is a non-None string (fail-closed: caller must not write).
    """

    outcome = run_gh(
        [
            "issue", "list",
            "--repo", repository,
            "--state", "all",
            "--limit", "100",
            "--json", "number,title,body,state",
        ],
        runner,
    )
    if not outcome.ok:
        return [], f"{ERR_DISCOVERY_FAILED}:gh issue list exit={outcome.exit_code} timed_out={outcome.timed_out}"
    text = outcome.stdout.strip()
    if not text:
        return [], f"{ERR_DISCOVERY_FAILED}:gh issue list empty output"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], f"{ERR_DISCOVERY_FAILED}:gh issue list invalid JSON: {exc}"
    if not isinstance(parsed, list):
        return [], f"{ERR_DISCOVERY_FAILED}:gh issue list expected array"
    # Validate each item has required fields (fail-closed on incomplete).
    items: list[Mapping[str, Any]] = []
    for raw in parsed:
        if not isinstance(raw, Mapping):
            continue
        if "number" not in raw or "body" not in raw:
            continue
        items.append({
            "number": raw.get("number"),
            "title": str(raw.get("title", "") or ""),
            "body": str(raw.get("body", "") or ""),
            "state": str(raw.get("state", "") or ""),
        })
    return items, None


def live_guard(
    *,
    repository: str,
    expected_main_sha: str,
    expected_owner: str = EXPECTED_OWNER,
    expected_branch: str = EXPECTED_BRANCH,
    runner: CommandRunner = default_runner,
) -> tuple[bool, list[str]]:
    """Verify pre-conditions before any live GitHub write.

    Checks:
    - gh login user is ``expected_owner``.
    - Worktree is clean.
    - Current branch is ``expected_branch`` (and NOT main).
    - origin/main equals ``expected_main_sha``.
    - Marker query succeeds (no discovery failure, no duplicate marker).

    Returns ``(allowed, errors)``. If any check fails, zero writes occur.
    """

    errors: list[str] = []

    # 1. gh login user.
    user_outcome = run_gh(["api", "user", "--jq", ".login"], runner)
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

    # 4. origin/main == audited_main_sha.
    main_outcome = run_git(["rev-parse", "refs/remotes/origin/main"], runner)
    if not main_outcome.ok:
        errors.append(f"{ERR_LIVE_GUARD_MAIN_DRIFT}:git rev-parse origin/main failed")
    else:
        actual_main = main_outcome.stdout.strip().lower()
        if actual_main != expected_main_sha.strip().lower():
            errors.append(f"{ERR_LIVE_GUARD_MAIN_DRIFT}:{actual_main}!={expected_main_sha}")

    if errors:
        return False, errors

    # 5. Marker query complete (re-fetch and check no duplicate).
    issues, discovery_err = fetch_existing_issues(repository, runner=runner)
    if discovery_err is not None:
        errors.append(f"{ERR_LIVE_GUARD_MARKER_QUERY}:{discovery_err}")
        return False, errors

    return True, errors


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
    """

    action = plan.get("action")
    if action == ACTION_NO_OP:
        return {"applied": False, "action": action, "reason": "no_op", "live": live}

    if not live:
        return {"applied": False, "action": action, "reason": "dry_run", "live": False}

    # Live guard: verify pre-conditions.
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
        # TOCTOU: target must still carry the marker. If the target is gone
        # (e.g. deleted) or no longer carries the marker, fail-closed.
        if target not in matched_numbers:
            return {
                "applied": False,
                "action": action,
                "reason": ERR_TOCTOU,
                "live": True,
                "matched": matched_numbers,
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

    return {"applied": False, "action": action, "reason": "unknown_action", "live": live}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Codex Supervisor publication (dry-run by default, fail-closed)")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Produce a dry-run publication plan")
    plan_parser.add_argument("--result", required=True, help="Path to audit result JSON")
    plan_parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    plan_parser.add_argument("--main-sha", required=True, help="Exact main SHA (40 hex chars)")
    plan_parser.add_argument("--existing-issues", help="Path to JSON file of existing issues (default: query gh)")
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

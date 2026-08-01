#!/usr/bin/env python3
"""Thin Codex Supervisor publication planner (quota-free v0).

Searches existing open issues for the cycle marker via ``gh``, then produces
a bounded publication plan: ``create_issue``, ``update_issue``, or ``no_op``.
Never closes issues, never modifies PRs, never touches main.

Default mode is **dry-run** (zero GitHub writes). GitHub writes happen only
when ``--live`` is passed explicitly, and even then only ``create_issue`` /
``update_issue`` (no merge, no close, no main push).

Pure standard library. No real Codex/model calls.

Usage (dry-run):
    python scripts/supervisor_publish.py plan \
        --result audit_result.json \
        --repository dddd2024/reverse-agent \
        --main-sha 16526801bda2a816fc707342f903c1ad037de9bd
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Mapping, Sequence

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
from supervisor_context import default_runner, run_gh

ACTION_CREATE_ISSUE = "create_issue"
ACTION_UPDATE_ISSUE = "update_issue"
ACTION_NO_OP = "no_op"

MAX_BODY_LENGTH = 8000
MAX_AUDIT_COMMENT_LENGTH = 2000


def build_issue_body(next_task: Mapping[str, Any], marker: str) -> str:
    """Build the bounded issue body for a next_task, embedding the marker."""

    forbidden = next_task.get("forbidden_scope", []) or []
    stop = []  # minimal contract has no stop_conditions field
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
    lines.append("## Acceptance checks")
    lines.extend(f"- {item}" for item in next_task.get("acceptance_checks", []))
    lines.append("")
    lines.append("## Execution prompt")
    lines.append(next_task.get("execution_prompt", ""))
    body = "\n".join(lines)
    if len(body) > MAX_BODY_LENGTH:
        body = body[:MAX_BODY_LENGTH]
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
    """Return a bounded publication plan.

    ``existing_issues`` is a list of ``{"number", "title", "body"}`` dicts
    (typically from ``gh issue list``). The plan never performs writes; the
    caller decides whether to apply it (dry-run vs --live).
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
        # No next task: nothing to publish. Still report a valid no-op.
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
        acceptance_checks=next_task["acceptance_checks"],
    )
    marker = make_marker(key)
    title = next_task["title"]
    body = build_issue_body(next_task, marker)
    digest = content_digest(body)

    matched_number: int | None = None
    matched_body: str | None = None
    for issue in existing_issues:
        issue_body = str(issue.get("body", "") or "")
        if find_marker_key(issue_body) == key:
            matched_number = issue.get("number")
            matched_body = issue_body
            break

    if matched_number is None:
        action = ACTION_CREATE_ISSUE
        target_issue: int | None = None
    elif matched_body is not None and _normalize_body(matched_body) == _normalize_body(body):
        action = ACTION_NO_OP
        target_issue = matched_number
    else:
        action = ACTION_UPDATE_ISSUE
        target_issue = matched_number

    return {
        "action": action,
        "schema_valid": True,
        "policy_allowed": True,
        "errors": [],
        "marker": marker,
        "idempotency_key": key,
        "target_issue": target_issue,
        "title": title,
        "body": body,
        "content_digest": digest,
    }


def _normalize_body(body: str) -> str:
    return " ".join(body.split())


def fetch_existing_issues(repository: str, *, runner=default_runner) -> list[Mapping[str, Any]]:
    """Fetch bounded open issues (number/title/body) via gh."""

    outcome = run_gh(
        [
            "issue", "list",
            "--repo", repository,
            "--state", "open",
            "--limit", "100",
            "--json", "number,title,body",
        ],
        runner,
    )
    if not outcome.ok:
        return []
    try:
        parsed = json.loads(outcome.stdout)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def apply_plan(
    plan: Mapping[str, Any],
    *,
    repository: str,
    runner=default_runner,
    live: bool,
) -> Mapping[str, Any]:
    """Apply a publication plan. No-op unless ``live=True``.

    Even in live mode, only ``create_issue`` / ``update_issue`` are
    performed. Never closes issues, never modifies PRs, never touches main.
    Returns a record of what was (or would be) done.
    """

    action = plan.get("action")
    if action == ACTION_NO_OP:
        return {"applied": False, "action": action, "reason": "no_op", "live": live}

    if not live:
        return {"applied": False, "action": action, "reason": "dry_run", "live": False}

    if action == ACTION_CREATE_ISSUE:
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
        outcome = run_gh(
            [
                "issue", "edit", str(plan.get("target_issue")),
                "--repo", repository,
                "--body", str(plan.get("body", "")),
            ],
            runner,
        )
        return {
            "applied": outcome.ok,
            "action": action,
            "live": True,
            "exit_code": outcome.exit_code,
            "target_issue": plan.get("target_issue"),
        }
    return {"applied": False, "action": action, "reason": "unknown_action", "live": live}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Codex Supervisor publication (dry-run by default)")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="Produce a dry-run publication plan")
    plan_parser.add_argument("--result", required=True, help="Path to audit result JSON")
    plan_parser.add_argument("--repository", required=True, help="Repository (owner/name)")
    plan_parser.add_argument("--main-sha", required=True, help="Exact main SHA")
    plan_parser.add_argument("--existing-issues", help="Path to JSON file of existing issues (default: query gh)")
    plan_parser.add_argument("--live", action="store_true", help="Apply the plan (writes to GitHub). Default is dry-run.")

    args = parser.parse_args(argv)

    with open(args.result, encoding="utf-8") as handle:
        audit_result = json.load(handle)

    if args.existing_issues:
        with open(args.existing_issues, encoding="utf-8") as handle:
            existing_issues = json.load(handle)
    else:
        existing_issues = fetch_existing_issues(args.repository)

    plan = plan_publication(
        audit_result=audit_result,
        repository=args.repository,
        main_sha=args.main_sha,
        existing_issues=existing_issues,
    )

    if args.live and plan.get("action") in (ACTION_CREATE_ISSUE, ACTION_UPDATE_ISSUE):
        plan["apply_result"] = apply_plan(plan, repository=args.repository, live=True)

    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if plan.get("schema_valid") else 1


if __name__ == "__main__":
    sys.exit(main())

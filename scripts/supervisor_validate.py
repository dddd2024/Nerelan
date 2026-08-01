#!/usr/bin/env python3
"""Thin Codex Supervisor validator (quota-free v0.2, fail-closed).

Validates an external audit result against the minimal project contract,
applies project-specific security rules, and computes the stable cycle
marker. Pure standard library. No real Codex/model calls.

This is a thin script over git/gh + json/hashlib. It deliberately does NOT
introduce a Backend Protocol, Snapshot class hierarchy, or Publication
Planner framework (see Issue #92).

Fail-closed audit-result contract (v0.2):

    {
      "schema_version": "0.2",
      "repository": "dddd2024/reverse-agent",
      "audited_main_sha": "<40-hex-char SHA-256 git commit>",
      "status": "continue | revise | stop",
      "findings": [
        { "claim": "...", "evidence": ["<verifiable reference>"] }
      ],
      "next_task": null | {
        "title": "...",
        "goal": "<one bounded goal>",
        "allowed_scope": ["<path or operation>"],
        "forbidden_scope": ["<path or operation>"],
        "requested_operations": ["<closed-whitelist operation>"],
        "acceptance_checks": ["<deterministic check>"],
        "execution_prompt": "<complete prompt>"
      }
    }

Authority model: ``requested_operations`` is the authoritative permission
grant. Natural-language keyword scanning of free text (``allowed_scope``,
``execution_prompt``, ``goal``) is a *secondary* guard only — it can
additionally reject, but the absence of a keyword does not authorize an
operation that is not in ``requested_operations``.

Usage:
    python scripts/supervisor_validate.py \\
        --result audit_result.json \\
        --repository dddd2024/reverse-agent \\
        --main-sha 16526801bda2a816fc707342f903c1ad037de9bd
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "0.2"
POLICY_VERSION = "0.2"

VALID_STATUS = frozenset({"continue", "revise", "stop"})

# Closed whitelist of operations that next_task may request.
# This is the *authority*: an operation not listed here is forbidden even
# if no natural-language keyword scan catches it.
ALLOWED_OPERATIONS = frozenset({
    "read_repository",
    "edit_bounded_files",
    "run_checks",
    "push_named_branch",
    "create_or_update_draft_pr",
})

# Operations that are never permitted. Listing them here for documentation;
# the validator rejects any requested_operations item not in ALLOWED_OPERATIONS.
FORBIDDEN_OPERATIONS = frozenset({
    "push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "release",
    "deploy",
    "credential_access",
    "close_issue",
    "delete_branch",
    "rewrite_history",
})

MARKER_TEMPLATE = "<!-- reverse-agent-supervisor-cycle:{key} -->"
_MARKER_RE = re.compile(r"<!-- reverse-agent-supervisor-cycle:([0-9a-f]{64}) -->")

# Bounded limits (finite, deterministic).
MAX_FINDINGS = 50
MAX_EVIDENCE_PER_FINDING = 20
MAX_CLAIM_LENGTH = 1000
MAX_EVIDENCE_LENGTH = 500
MAX_TITLE_LENGTH = 200
MAX_GOAL_LENGTH = 1000
MAX_SCOPE_ITEMS = 50
MAX_SCOPE_LENGTH = 500
MAX_OPERATIONS = 20
MAX_ACCEPTANCE_CHECKS = 50
MAX_CHECK_LENGTH = 500
MAX_EXECUTION_PROMPT_LENGTH = 8000
MAX_REPOSITORY_LENGTH = 100

# Top-level required fields (strict — unknown fields rejected).
_TOP_LEVEL_FIELDS = frozenset({
    "schema_version", "repository", "audited_main_sha",
    "status", "findings", "next_task",
})

_NEXT_TASK_FIELDS = frozenset({
    "title", "goal", "allowed_scope", "forbidden_scope",
    "requested_operations", "acceptance_checks", "execution_prompt",
})

_FINDING_FIELDS = frozenset({"claim", "evidence"})

# Finite, machine-readable error codes.
INVALID_JSON = "INVALID_JSON"
INVALID_STATUS = "INVALID_STATUS"
FINDINGS_MISSING = "FINDINGS_MISSING"
FINDING_NO_EVIDENCE = "FINDING_NO_EVIDENCE"
FINDING_INVALID_CLAIM = "FINDING_INVALID_CLAIM"
NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED = "NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED"
NEXT_TASK_ALLOWED_SCOPE_EMPTY = "NEXT_TASK_ALLOWED_SCOPE_EMPTY"
NEXT_TASK_SCOPE_TOO_BROAD = "NEXT_TASK_SCOPE_TOO_BROAD"
NEXT_TASK_OPERATIONS_REQUIRED = "NEXT_TASK_OPERATIONS_REQUIRED"
NEXT_TASK_OPERATION_UNKNOWN = "NEXT_TASK_OPERATION_UNKNOWN"
POLICY_MERGE_FORBIDDEN = "POLICY_MERGE_FORBIDDEN"
POLICY_MAIN_PUSH_FORBIDDEN = "POLICY_MAIN_PUSH_FORBIDDEN"
POLICY_RELEASE_FORBIDDEN = "POLICY_RELEASE_FORBIDDEN"
POLICY_DEPLOYMENT_FORBIDDEN = "POLICY_DEPLOYMENT_FORBIDDEN"
POLICY_CREDENTIAL_ACCESS_FORBIDDEN = "POLICY_CREDENTIAL_ACCESS_FORBIDDEN"
POLICY_UNRELATED_MUTATION_FORBIDDEN = "POLICY_UNRELATED_MUTATION_FORBIDDEN"
POLICY_DANGEROUS_ACCEPTANCE_CHECK = "POLICY_DANGEROUS_ACCEPTANCE_CHECK"
FIELD_TOO_LONG = "FIELD_TOO_LONG"
FIELD_TOO_MANY = "FIELD_TOO_MANY"
UNKNOWN_FIELD = "UNKNOWN_FIELD"
SCHEMA_VERSION_MISMATCH = "SCHEMA_VERSION_MISMATCH"
REPOSITORY_MISMATCH = "REPOSITORY_MISMATCH"
MAIN_SHA_MISMATCH = "MAIN_SHA_MISMATCH"
INVALID_MAIN_SHA_FORMAT = "INVALID_MAIN_SHA_FORMAT"

# Whole-repo / unbounded scope markers (rejected).
_BROAD_SCOPES = frozenset({
    "*", "**", "**/*", ".", "./", "./**", "all", "entire repository",
    "entire_repo", "whole repo", "whole_repo", "repo-wide", "everything",
})

# Forbidden operation phrases (whole-word, case-insensitive) paired with the
# finite error code they raise. Used for *secondary* natural-language scan
# of allowed_scope, execution_prompt, goal, and acceptance_checks.
# ``forbidden_scope`` is NOT scanned: listing "merge" there means merge is
# forbidden (good), not requested.
_FORBIDDEN_PHRASES: tuple[tuple[str, str], ...] = (
    ("merge", POLICY_MERGE_FORBIDDEN),
    ("auto-merge", POLICY_MERGE_FORBIDDEN),
    ("auto_merge", POLICY_MERGE_FORBIDDEN),
    ("push main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("push to main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("write main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("release", POLICY_RELEASE_FORBIDDEN),
    ("deployment", POLICY_DEPLOYMENT_FORBIDDEN),
    ("deploy", POLICY_DEPLOYMENT_FORBIDDEN),
    ("read credentials", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("publish credentials", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read secrets", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("access secrets", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("secret access", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read token", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("publish token", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read chatgpt session", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("close unrelated issue", POLICY_UNRELATED_MUTATION_FORBIDDEN),
    ("modify unrelated issue", POLICY_UNRELATED_MUTATION_FORBIDDEN),
    ("close unrelated pr", POLICY_UNRELATED_MUTATION_FORBIDDEN),
    ("modify unrelated pr", POLICY_UNRELATED_MUTATION_FORBIDDEN),
)

# Dangerous commands that must not appear in acceptance_checks.
_DANGEROUS_COMMAND_PHRASES = (
    ("push main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("push to main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("git push origin main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("git push main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("merge", POLICY_MERGE_FORBIDDEN),
    ("auto-merge", POLICY_MERGE_FORBIDDEN),
    ("auto_merge", POLICY_MERGE_FORBIDDEN),
    ("gh pr merge", POLICY_MERGE_FORBIDDEN),
    ("release", POLICY_RELEASE_FORBIDDEN),
    ("gh release", POLICY_RELEASE_FORBIDDEN),
    ("deploy", POLICY_DEPLOYMENT_FORBIDDEN),
    ("deployment", POLICY_DEPLOYMENT_FORBIDDEN),
    ("force push", POLICY_MAIN_PUSH_FORBIDDEN),
    ("force-push", POLICY_MAIN_PUSH_FORBIDDEN),
    ("push --force", POLICY_MAIN_PUSH_FORBIDDEN),
    ("push -f origin main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("push -f main", POLICY_MAIN_PUSH_FORBIDDEN),
    ("rebase", POLICY_MAIN_PUSH_FORBIDDEN),
    ("reset --hard", POLICY_MAIN_PUSH_FORBIDDEN),
    ("read credentials", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read secrets", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read token", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
)

_NEGATION_TOKENS = ("do not ", "don't ", "never ", "must not ", "cannot ", "can't ", "without ", "avoid ", "forbid ", "no ", "not ")

_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def normalize_text(text: str) -> str:
    """Collapse all whitespace runs to single spaces and strip ends."""

    return " ".join(text.split())


def _stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def compute_cycle_key(
    *,
    repository: str,
    main_sha: str,
    schema_version: str,
    policy_version: str,
    goal: str,
    allowed_scope: Sequence[str],
    forbidden_scope: Sequence[str],
    requested_operations: Sequence[str],
    acceptance_checks: Sequence[str],
) -> str:
    """Return the 64-hex-char SHA-256 cycle key for a supervisor cycle.

    The idempotency key covers: repository, exact main SHA, schema/policy
    version, goal, allowed_scope, forbidden_scope, requested_operations,
    and acceptance_checks. Acceptance-check and scope order have no
    semantics, so they are sorted and de-duplicated before hashing.
    Same semantic inputs produce the same key; a material change to any
    covered field changes the key.
    """

    def _norm_seq(items: Sequence[str]) -> list[str]:
        return sorted({normalize_text(str(i)) for i in items if normalize_text(str(i))})

    payload = {
        "repository": repository.strip(),
        "main_sha": main_sha.strip().lower(),
        "schema_version": schema_version.strip(),
        "policy_version": policy_version.strip(),
        "goal": normalize_text(goal),
        "allowed_scope": _norm_seq(allowed_scope),
        "forbidden_scope": _norm_seq(forbidden_scope),
        "requested_operations": _norm_seq(requested_operations),
        "acceptance_checks": _norm_seq(acceptance_checks),
    }
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def make_marker(key: str) -> str:
    return MARKER_TEMPLATE.format(key=key)


def find_marker_key(text: str) -> str | None:
    match = _MARKER_RE.search(text)
    return match.group(1) if match is not None else None


def validate_audit_result(
    payload: object,
    *,
    expected_repository: str,
    expected_main_sha: str,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate an audit result (fail-closed).

    Returns ``(ok, errors, parsed)``. ``parsed`` is the normalized result
    dict when ok, else ``None``. Validation is total: any deviation produces
    a finite, machine-readable error code and never proceeds to marker
    computation.

    Fail-closed rules:
    - Unknown fields at top level, in findings, or in next_task are rejected.
    - ``schema_version`` must equal ``"0.2"``.
    - ``repository`` must exactly equal ``expected_repository``.
    - ``audited_main_sha`` must be a full 40-hex SHA and exactly equal
      ``expected_main_sha`` (case-insensitive).
    - ``requested_operations`` must be a non-empty subset of the closed
      whitelist. This is the authoritative permission grant.
    - ``acceptance_checks`` are scanned for dangerous commands.
    - Natural-language keyword scan of allowed_scope / execution_prompt /
      goal is a secondary guard (can reject, never authorizes).
    """

    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return False, [INVALID_JSON], None

    # Unknown top-level fields.
    for key in payload:
        if key not in _TOP_LEVEL_FIELDS:
            errors.append(f"{UNKNOWN_FIELD}:{key}")

    # schema_version
    schema_version = payload.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        errors.append(f"{SCHEMA_VERSION_MISMATCH}:{schema_version!r}")

    # repository — exact match.
    repository = payload.get("repository")
    if not isinstance(repository, str) or not repository.strip():
        errors.append(f"{REPOSITORY_MISMATCH}:missing")
    elif repository.strip() != expected_repository.strip():
        errors.append(f"{REPOSITORY_MISMATCH}:{repository!r}!={expected_repository!r}")
    elif len(repository.strip()) > MAX_REPOSITORY_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:repository")

    # audited_main_sha — full 40-hex, exact match.
    audited_main_sha = payload.get("audited_main_sha")
    if not isinstance(audited_main_sha, str) or not _FULL_SHA_RE.fullmatch(audited_main_sha.strip().lower()):
        errors.append(f"{INVALID_MAIN_SHA_FORMAT}:{audited_main_sha!r}")
    elif audited_main_sha.strip().lower() != expected_main_sha.strip().lower():
        errors.append(f"{MAIN_SHA_MISMATCH}:{audited_main_sha!r}!={expected_main_sha!r}")

    # status
    status = payload.get("status")
    if status not in VALID_STATUS:
        errors.append(f"{INVALID_STATUS}:{status!r}")

    # findings
    findings_raw = payload.get("findings")
    if not isinstance(findings_raw, list) or not findings_raw:
        errors.append(FINDINGS_MISSING)
    else:
        if len(findings_raw) > MAX_FINDINGS:
            errors.append(f"{FIELD_TOO_MANY}:findings")
        for idx, finding in enumerate(findings_raw):
            if not isinstance(finding, Mapping):
                errors.append(f"{FINDING_NO_EVIDENCE}:findings[{idx}]")
                continue
            for fkey in finding:
                if fkey not in _FINDING_FIELDS:
                    errors.append(f"{UNKNOWN_FIELD}:findings[{idx}].{fkey}")
            claim = finding.get("claim")
            if not isinstance(claim, str) or not claim.strip():
                errors.append(f"{FINDING_INVALID_CLAIM}:findings[{idx}]")
            elif len(claim.strip()) > MAX_CLAIM_LENGTH:
                errors.append(f"{FIELD_TOO_LONG}:findings[{idx}].claim")
            evidence = finding.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{FINDING_NO_EVIDENCE}:findings[{idx}]")
            else:
                if len(evidence) > MAX_EVIDENCE_PER_FINDING:
                    errors.append(f"{FIELD_TOO_MANY}:findings[{idx}].evidence")
                for ev in evidence:
                    if not isinstance(ev, str) or not ev.strip():
                        errors.append(f"{FINDING_NO_EVIDENCE}:findings[{idx}]")
                    elif len(ev.strip()) > MAX_EVIDENCE_LENGTH:
                        errors.append(f"{FIELD_TOO_LONG}:findings[{idx}].evidence")

    # next_task
    next_task = payload.get("next_task")
    normalized_task: dict[str, Any] | None = None
    if next_task is None:
        pass
    elif isinstance(next_task, Mapping):
        normalized_task = _validate_next_task(next_task, errors)
    else:
        errors.append("NEXT_TASK_INVALID")

    if errors:
        return False, _dedupe(errors), None

    parsed: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repository).strip(),
        "audited_main_sha": str(audited_main_sha).strip().lower(),
        "status": status,
        "findings": [
            {
                "claim": str(f.get("claim", "")).strip(),
                "evidence": [str(e).strip() for e in f.get("evidence", [])],
            }
            for f in findings_raw
            if isinstance(f, Mapping)
        ],
        "next_task": normalized_task,
    }
    return True, [], parsed


def _validate_next_task(task: Mapping[str, Any], errors: list[str]) -> dict[str, Any] | None:
    # Unknown fields.
    for key in task:
        if key not in _NEXT_TASK_FIELDS:
            errors.append(f"{UNKNOWN_FIELD}:next_task.{key}")

    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("NEXT_TASK_TITLE_REQUIRED")
    elif len(title.strip()) > MAX_TITLE_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:next_task.title")

    goal = task.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        errors.append("NEXT_TASK_GOAL_REQUIRED")
    elif len(goal.strip()) > MAX_GOAL_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:next_task.goal")

    allowed_scope = task.get("allowed_scope")
    if not isinstance(allowed_scope, list) or not allowed_scope:
        errors.append(NEXT_TASK_ALLOWED_SCOPE_EMPTY)
    else:
        if len(allowed_scope) > MAX_SCOPE_ITEMS:
            errors.append(f"{FIELD_TOO_MANY}:next_task.allowed_scope")
        for item in allowed_scope:
            if not isinstance(item, str) or not item.strip():
                errors.append(NEXT_TASK_ALLOWED_SCOPE_EMPTY)
            elif len(item.strip()) > MAX_SCOPE_LENGTH:
                errors.append(f"{FIELD_TOO_LONG}:next_task.allowed_scope")
            else:
                norm = normalize_text(item).lower()
                if norm in _BROAD_SCOPES:
                    errors.append(f"{NEXT_TASK_SCOPE_TOO_BROAD}:{item!r}")

    forbidden_scope = task.get("forbidden_scope", [])
    if not isinstance(forbidden_scope, list):
        errors.append("NEXT_TASK_FORBIDDEN_SCOPE_INVALID")
    elif len(forbidden_scope) > MAX_SCOPE_ITEMS:
        errors.append(f"{FIELD_TOO_MANY}:next_task.forbidden_scope")
    else:
        # Validate element types and lengths (fail-closed).
        for item in forbidden_scope:
            if not isinstance(item, str) or not item.strip():
                errors.append("NEXT_TASK_FORBIDDEN_SCOPE_INVALID")
            elif len(item.strip()) > MAX_SCOPE_LENGTH:
                errors.append(f"{FIELD_TOO_LONG}:next_task.forbidden_scope")

    # requested_operations — authoritative permission grant.
    requested_operations = task.get("requested_operations")
    if not isinstance(requested_operations, list) or not requested_operations:
        errors.append(NEXT_TASK_OPERATIONS_REQUIRED)
    else:
        if len(requested_operations) > MAX_OPERATIONS:
            errors.append(f"{FIELD_TOO_MANY}:next_task.requested_operations")
        for op in requested_operations:
            if not isinstance(op, str) or op not in ALLOWED_OPERATIONS:
                errors.append(f"{NEXT_TASK_OPERATION_UNKNOWN}:{op!r}")

    acceptance_checks = task.get("acceptance_checks")
    if not isinstance(acceptance_checks, list) or not acceptance_checks:
        errors.append(NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED)
    else:
        if len(acceptance_checks) > MAX_ACCEPTANCE_CHECKS:
            errors.append(f"{FIELD_TOO_MANY}:next_task.acceptance_checks")
        for item in acceptance_checks:
            if not isinstance(item, str) or not item.strip():
                errors.append(NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED)
            elif len(item.strip()) > MAX_CHECK_LENGTH:
                errors.append(f"{FIELD_TOO_LONG}:next_task.acceptance_checks")
            else:
                # Dangerous-command scan (fail-closed).
                norm = normalize_text(item).lower()
                for phrase, code in _DANGEROUS_COMMAND_PHRASES:
                    if phrase in norm:
                        errors.append(f"{POLICY_DANGEROUS_ACCEPTANCE_CHECK}:{code}")
                        break

    execution_prompt = task.get("execution_prompt")
    if not isinstance(execution_prompt, str) or not execution_prompt.strip():
        errors.append("NEXT_TASK_EXECUTION_PROMPT_REQUIRED")
    elif len(execution_prompt.strip()) > MAX_EXECUTION_PROMPT_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:next_task.execution_prompt")

    # Secondary natural-language keyword scan (auxiliary only).
    # allowed_scope: strict — any mention of a forbidden operation is rejected.
    # execution_prompt / goal: negation-aware.
    # forbidden_scope: NOT scanned (listing "merge" there is good).
    if isinstance(allowed_scope, list):
        _scan_policy_strict(
            [str(s) for s in allowed_scope if isinstance(s, str)],
            errors,
        )
    free_text: list[str] = []
    if isinstance(execution_prompt, str):
        free_text.append(execution_prompt)
    if isinstance(goal, str):
        free_text.append(goal)
    _scan_policy_free_text(free_text, errors)

    if errors:
        return None
    return {
        "title": str(title).strip(),
        "goal": str(goal).strip(),
        "allowed_scope": [str(s).strip() for s in allowed_scope],
        "forbidden_scope": [str(s).strip() for s in forbidden_scope],
        "requested_operations": [str(s) for s in requested_operations],
        "acceptance_checks": [str(s).strip() for s in acceptance_checks],
        "execution_prompt": str(execution_prompt).strip(),
    }


def _scan_policy_strict(texts: Sequence[str], errors: list[str]) -> None:
    """Strict scan for ``allowed_scope``: any mention of a forbidden
    operation is rejected, regardless of wording.
    """

    for text in texts:
        norm = normalize_text(text).lower()
        for phrase, code in _FORBIDDEN_PHRASES:
            if _matches_word(norm, phrase):
                errors.append(code)
                break  # one error per scope item is enough


def _scan_policy_free_text(texts: Sequence[str], errors: list[str]) -> None:
    """Negation-aware scan for free text (``execution_prompt``, ``goal``).

    A clause that starts with a negation token (e.g. "do not merge") is
    not flagged — it is forbidding the operation, not requesting it.
    """

    for text in texts:
        norm = normalize_text(text).lower()
        for clause in _split_clauses(norm):
            if any(clause.startswith(neg.rstrip()) for neg in _NEGATION_TOKENS):
                continue
            for phrase, code in _FORBIDDEN_PHRASES:
                if _matches_word(clause, phrase):
                    errors.append(code)
                    break  # one error per clause is enough


def _split_clauses(text: str) -> list[str]:
    parts = re.split(r"[.;:!?\n]", text)
    return [p.strip() for p in parts if p.strip()]


def _matches_word(text: str, keyword: str) -> bool:
    if text == keyword:
        return True
    if text.startswith(keyword + " "):
        return True
    if text.endswith(" " + keyword):
        return True
    return (" " + keyword + " ") in text


def _dedupe(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        if item not in seen:
            seen[item] = None
    return list(seen.keys())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Codex Supervisor audit result (fail-closed v0.2)")
    parser.add_argument("--result", required=True, help="Path to audit result JSON")
    parser.add_argument("--repository", required=True, help="Expected repository (owner/name)")
    parser.add_argument("--main-sha", required=True, help="Expected exact main SHA (40 hex chars)")
    args = parser.parse_args(argv)

    with open(args.result, encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError as exc:
            print(json.dumps({"valid": False, "errors": [f"{INVALID_JSON}:{exc}"], "marker": None}))
            return 1

    ok, errors, parsed = validate_audit_result(
        payload, expected_repository=args.repository, expected_main_sha=args.main_sha
    )

    marker = None
    if ok and parsed is not None and parsed.get("next_task") is not None:
        task = parsed["next_task"]
        key = compute_cycle_key(
            repository=args.repository,
            main_sha=args.main_sha,
            schema_version=SCHEMA_VERSION,
            policy_version=POLICY_VERSION,
            goal=task["goal"],
            allowed_scope=task["allowed_scope"],
            forbidden_scope=task["forbidden_scope"],
            requested_operations=task["requested_operations"],
            acceptance_checks=task["acceptance_checks"],
        )
        marker = make_marker(key)

    output = {
        "valid": ok,
        "errors": errors,
        "marker": marker,
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
    }
    print(json.dumps(output, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

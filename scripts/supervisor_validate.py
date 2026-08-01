#!/usr/bin/env python3
"""Thin Codex Supervisor validator (quota-free v0).

Validates an external audit result against the minimal project contract,
applies project-specific security rules, and computes the stable cycle
marker. Pure standard library. No real Codex/model calls.

This is a thin script over git/gh + json/hashlib. It deliberately does NOT
introduce a Backend Protocol, Snapshot class hierarchy, or Publication
Planner framework (see Issue #92).

Minimal audit-result contract:

    {
      "status": "continue | revise | stop",
      "findings": [
        { "claim": "...", "evidence": ["<verifiable reference>"] }
      ],
      "next_task": null | {
        "title": "...",
        "goal": "<one bounded goal>",
        "allowed_scope": ["<path or operation>"],
        "forbidden_scope": ["<path or operation>"],
        "acceptance_checks": ["<deterministic check>"],
        "execution_prompt": "<complete prompt>"
      }
    }

Usage:
    python scripts/supervisor_validate.py \
        --result audit_result.json \
        --repository dddd2024/reverse-agent \
        --main-sha 16526801bda2a816fc707342f903c1ad037de9bd
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "0.1"
POLICY_VERSION = "0.1"

VALID_STATUS = frozenset({"continue", "revise", "stop"})

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
MAX_ACCEPTANCE_CHECKS = 50
MAX_CHECK_LENGTH = 500
MAX_EXECUTION_PROMPT_LENGTH = 8000

# Finite, machine-readable error codes.
INVALID_JSON = "INVALID_JSON"
INVALID_STATUS = "INVALID_STATUS"
FINDINGS_MISSING = "FINDINGS_MISSING"
FINDING_NO_EVIDENCE = "FINDING_NO_EVIDENCE"
FINDING_INVALID_CLAIM = "FINDING_INVALID_CLAIM"
NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED = "NEXT_TASK_ACCEPTANCE_CHECKS_REQUIRED"
NEXT_TASK_ALLOWED_SCOPE_EMPTY = "NEXT_TASK_ALLOWED_SCOPE_EMPTY"
NEXT_TASK_SCOPE_TOO_BROAD = "NEXT_TASK_SCOPE_TOO_BROAD"
POLICY_MERGE_FORBIDDEN = "POLICY_MERGE_FORBIDDEN"
POLICY_MAIN_PUSH_FORBIDDEN = "POLICY_MAIN_PUSH_FORBIDDEN"
POLICY_RELEASE_FORBIDDEN = "POLICY_RELEASE_FORBIDDEN"
POLICY_DEPLOYMENT_FORBIDDEN = "POLICY_DEPLOYMENT_FORBIDDEN"
POLICY_CREDENTIAL_ACCESS_FORBIDDEN = "POLICY_CREDENTIAL_ACCESS_FORBIDDEN"
POLICY_UNRELATED_MUTATION_FORBIDDEN = "POLICY_UNRELATED_MUTATION_FORBIDDEN"
FIELD_TOO_LONG = "FIELD_TOO_LONG"
FIELD_TOO_MANY = "FIELD_TOO_MANY"

# Whole-repo / unbounded scope markers (rejected).
_BROAD_SCOPES = frozenset({"*", "**", "**/*", ".", "./", "./**", "all", "entire repository", "entire_repo", "whole repo", "whole_repo", "repo-wide", "everything"})

# Forbidden operation phrases (whole-word, case-insensitive) paired with the
# finite error code they raise. ``allowed_scope`` is scanned strictly (any
# mention is a request). Free text (execution_prompt, goal) is scanned with
# negation awareness so "do not merge" is not flagged. ``forbidden_scope`` is
# NOT scanned: listing "merge" there means merge is forbidden (good).
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

_NEGATION_TOKENS = ("do not ", "don't ", "never ", "must not ", "cannot ", "can't ", "without ", "avoid ", "forbid ", "no ", "not ")

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


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
    acceptance_checks: Sequence[str],
) -> str:
    """Return the 64-hex-char SHA-256 cycle key for a supervisor cycle.

    Acceptance-check order has no semantics, so checks are sorted and
    de-duplicated before hashing. Same semantic inputs produce the same key;
    a material change to main SHA, goal, policy version, or acceptance
    checks changes the key.
    """

    normalized_checks = sorted(
        {normalize_text(c) for c in acceptance_checks if normalize_text(c)}
    )
    payload = {
        "repository": repository.strip(),
        "main_sha": main_sha.strip().lower(),
        "schema_version": schema_version.strip(),
        "policy_version": policy_version.strip(),
        "goal": normalize_text(goal),
        "acceptance_checks": normalized_checks,
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
    """Validate an audit result.

    Returns ``(ok, errors, parsed)``. ``parsed`` is the normalized result
    dict when ok, else ``None``. Validation is total: any deviation produces
    a finite, machine-readable error code and never proceeds to marker
    computation.
    """

    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return False, [INVALID_JSON], None

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

    execution_prompt = task.get("execution_prompt")
    if not isinstance(execution_prompt, str) or not execution_prompt.strip():
        errors.append("NEXT_TASK_EXECUTION_PROMPT_REQUIRED")
    elif len(execution_prompt.strip()) > MAX_EXECUTION_PROMPT_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:next_task.execution_prompt")

    # Policy scan.
    # ``allowed_scope`` is scanned strictly: any mention of a forbidden
    # operation is a request to perform it.
    # ``execution_prompt`` and ``goal`` (free text) are scanned with
    # negation awareness so "do not merge" is not flagged.
    # ``forbidden_scope`` is NOT scanned: listing "merge" there means merge
    # is forbidden (good), not requested.
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
        "acceptance_checks": [str(s).strip() for s in acceptance_checks],
        "execution_prompt": str(execution_prompt).strip(),
    }


def _scan_policy_strict(texts: Sequence[str], errors: list[str]) -> None:
    """Strict scan for ``allowed_scope``: any mention of a forbidden
    operation is a request to perform it, regardless of wording.
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


def _sha_matches(actual: str, expected: str) -> bool:
    a = actual.strip().lower()
    e = expected.strip().lower()
    if not _SHA_RE.fullmatch(a) or not _SHA_RE.fullmatch(e):
        return False
    n = min(len(a), len(e))
    return a[:n] == e[:n]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Codex Supervisor audit result")
    parser.add_argument("--result", required=True, help="Path to audit result JSON")
    parser.add_argument("--repository", required=True, help="Expected repository (owner/name)")
    parser.add_argument("--main-sha", required=True, help="Expected exact main SHA")
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
            acceptance_checks=task["acceptance_checks"],
        )
        marker = make_marker(key)

    output = {"valid": ok, "errors": errors, "marker": marker, "schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION}
    print(json.dumps(output, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

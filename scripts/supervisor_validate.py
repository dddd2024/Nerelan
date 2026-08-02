#!/usr/bin/env python3
"""Thin Codex Supervisor validator (quota-free v0.3, fail-closed).

Validates an external audit result against the minimal project contract,
applies project-specific security rules, and computes the stable cycle
marker. Pure standard library. No real Codex/model calls.

This is a thin script over git/gh + json/hashlib. It deliberately does NOT
introduce a Backend Protocol, Snapshot class hierarchy, or Publication
Planner framework (see Issue #92).

v0.3 changes (fail-closed closure):
- No negation skip for goal / execution_prompt: a forbidden operation
  keyword appearing in these fields is rejected directly. Legitimate
  prohibitions belong in ``forbidden_scope``, not prompt negation.
- acceptance_checks use bounded command/token rules with word-boundary
  matching: ``git merge-base`` is allowed; ``gh pr merge``, push main,
  force-push, rebase, reset --hard, release, deploy, credential access,
  branch deletion, and shell chaining/redirection/substitution are rejected.
- Operation–prompt consistency: modifying files requires
  ``edit_bounded_files``, pushing a named branch requires
  ``push_named_branch``, updating a Draft PR requires
  ``create_or_update_draft_pr``.

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
POLICY_BRANCH_DELETION_FORBIDDEN = "POLICY_BRANCH_DELETION_FORBIDDEN"
POLICY_SHELL_METACHAR_FORBIDDEN = "POLICY_SHELL_METACHAR_FORBIDDEN"
OPERATION_PROMPT_INCONSISTENCY = "OPERATION_PROMPT_INCONSISTENCY"
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

# Finite mutation-surface vocabulary. Classification happens before permission
# checks so repository edits, Draft-PR metadata writes, unsupported GitHub
# writes, and reporting language cannot borrow one another's authority.
_REPOSITORY_MUTATION = "REPOSITORY_MUTATION"
_DRAFT_PR_MUTATION = "DRAFT_PR_MUTATION"
_UNSUPPORTED_GITHUB_MUTATION = "UNSUPPORTED_GITHUB_MUTATION"
_READ_ONLY = "READ_ONLY"
_NONE = "NONE"

# Strong verbs can establish repository-edit intent on their own after the
# clause has been ruled out as a metadata/reporting surface. Ambiguous verbs
# require a repository-artifact target in the same bounded clause.
_STRONG_EDIT_VERB_PATTERNS = (
    r"edit(?:s|ed|ing)?",
    r"modif(?:y|ies|ied|ying)",
    r"implement(?:s|ed|ing)?",
    r"patch(?:es|ed|ing)?",
    r"fix(?:es|ed|ing)?",
    r"refactor(?:s|ed|ing)?",
    r"rename(?:s|d|ing)?",
)
_AMBIGUOUS_EDIT_VERB_PATTERNS = (
    r"create(?:s|d|ing)?",
    r"update(?:s|d|ing)?",
    r"change(?:s|d|ing)?",
    r"write(?:s|ing)?",
    r"wrote",
    r"add(?:s|ed|ing)?",
    r"remove(?:s|d|ing)?",
    r"delete(?:s|d|ing)?",
)
_GITHUB_MUTATION_VERB_PATTERNS = (
    *_STRONG_EDIT_VERB_PATTERNS,
    *_AMBIGUOUS_EDIT_VERB_PATTERNS,
    r"close(?:s|d|ing)?",
    r"reopen(?:s|ed|ing)?",
    r"assign(?:s|ed|ing)?",
    r"unassign(?:s|ed|ing)?",
)
_REPOSITORY_ARTIFACT_TARGETS = (
    "file", "files", "code", "source", "source code", "script",
    "test", "tests", "docs", "documentation", "module", "function",
    "class", "implementation", "validator", "repository artifact",
)
_EDIT_CLAUSE_SPLIT_RE = re.compile(
    r"(?:[.!?](?:\s+|$)|[,;:\n]+|\b(?:but|however|then)\b)",
    re.IGNORECASE,
)
_DIRECT_NEGATION_BEFORE_RE = re.compile(
    r"(?:\bdo\s+not(?:\s+under\s+any\s+circumstances)?|\bdon't|\bnever|"
    r"\bmust\s+not|\bshould\s+not|\bwithout|"
    r"\bunder\s+no\s+circumstances|\bmust\s+never)\s+"
    r"(?:[a-z0-9_-]+\s+){0,3}$",
    re.IGNORECASE,
)
# A repository path needs either a relative directory plus a filename suffix,
# or a standalone filename whose suffix starts with a letter. This excludes
# slash-separated prose and decimal/version numbers.
_EXPLICIT_FILE_TARGET_RE = re.compile(
    r"(?:^|\s)(?:(?:[a-z0-9_.-]+[/\\])+(?:[a-z0-9_.-]+\.[a-z][a-z0-9.-]*)|"
    r"(?:\*|[a-z0-9_-]+)\.[a-z][a-z0-9]*)(?=\s|$)",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"(?:https?://\S+|(?:www\.)?github\.com/\S+)", re.IGNORECASE)
_DRAFT_PR_TARGET_RE = re.compile(
    r"\b(?:draft\s+(?:pr|pull\s+request)|pr\s+(?:description|body)|"
    r"pull\s+request\s+(?:description|body))\b|"
    r"\bgithub\.com/\S+/pull/\d+(?:\S*)?\s+(?:description|body)\b",
    re.IGNORECASE,
)
_UNSUPPORTED_GITHUB_ACTION_TARGET_PATTERNS = (
    # Issue fields and comments, with an optional number between target and field.
    r"(?:edit|modify|update|change|create|write|add|remove|delete)"
    r"(?:\s+[a-z0-9#_-]+){0,3}\s+issue(?:\s*#\d+)?\s+"
    r"(?:body|comment|state|title|labels?|assignees?)",
    # Issue lifecycle and direct interaction actions.
    r"(?:close|reopen|assign|unassign|comment\s+on)\s+(?:the\s+)?"
    r"issue(?:\s*#\d+)?",
    # Ordinary PR comment/review/label mutations.
    r"(?:edit|modify|update|change|create|write|add|remove|delete)"
    r"(?:\s+[a-z0-9#_-]+){0,3}\s+(?:pr|pull\s+request)(?:\s*#\d+)?\s+"
    r"(?:comment|review|review\s+comment|labels?)",
    r"(?:comment\s+on|review|approve|label)\s+(?:the\s+)?"
    r"(?:pr|pull\s+request)(?:\s*#\d+)?",
    r"mark\s+(?:the\s+)?(?:pr|pull\s+request)(?:\s*#\d+)?\s+ready",
    # Branch lifecycle writes. Branch push is a separately authorized surface.
    r"(?:create|delete|rename)\s+(?:the\s+|a\s+)?branch",
)
_PUSH_VERB_PATTERN = r"push(?:es|ed|ing)?"
_PUSH_TARGET_RE = re.compile(
    r"\b(?:named\s+branch|branch(?:es)?|origin)\b",
    re.IGNORECASE,
)
_REPORTING_TARGETS = (
    "audit report", "test report", "status report", "result summary",
    "status summary", "evidence summary", "result description",
    "status note", "report",
)

# Forbidden operation phrases (whole-word, case-insensitive) paired with the
# finite error code they raise. Used for *secondary* natural-language scan
# of allowed_scope, execution_prompt, goal, and acceptance_checks.
# ``forbidden_scope`` is NOT scanned: listing "merge" there means merge is
# forbidden (good), not requested.
#
# Word-boundary matching is used so that ``git merge-base`` is NOT flagged
# for "merge" (because "merge" is followed by "-", not a word boundary),
# while ``gh pr merge`` IS flagged (because "merge" is a whole word).
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
# Uses word-boundary matching so ``git merge-base`` is allowed but
# ``gh pr merge`` is rejected.
_DANGEROUS_COMMAND_PHRASES: tuple[tuple[str, str], ...] = (
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
    ("push -f", POLICY_MAIN_PUSH_FORBIDDEN),
    ("rebase", POLICY_MAIN_PUSH_FORBIDDEN),
    ("reset --hard", POLICY_MAIN_PUSH_FORBIDDEN),
    ("read credentials", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read secrets", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("read token", POLICY_CREDENTIAL_ACCESS_FORBIDDEN),
    ("git branch -D", POLICY_BRANCH_DELETION_FORBIDDEN),
    ("git branch -d", POLICY_BRANCH_DELETION_FORBIDDEN),
    ("git push --delete", POLICY_BRANCH_DELETION_FORBIDDEN),
    ("git push origin --delete", POLICY_BRANCH_DELETION_FORBIDDEN),
)

# Shell metacharacter patterns rejected in acceptance_checks.
# Checked with substring matching (these tokens are unambiguous).
_SHELL_METACHAR_CHECKS: tuple[tuple[str, str], ...] = (
    ("&&", "shell_chain"),
    ("||", "shell_chain"),
    ("$(", "command_substitution"),
    ("`", "backtick"),
    (" | ", "shell_pipe"),
    (" > ", "redirect"),
    (" >> ", "redirect"),
    (" < ", "redirect"),
    ("; ", "command_separator"),
)

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


def find_all_marker_keys(text: str) -> list[str]:
    """Return all marker keys found in ``text`` (for multi-marker detection)."""

    return [m.group(1) for m in _MARKER_RE.finditer(text)]


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
    - ``acceptance_checks`` are scanned for dangerous commands and shell
      metacharacters (word-boundary matching: ``git merge-base`` allowed,
      ``gh pr merge`` rejected).
    - Natural-language keyword scan of allowed_scope / execution_prompt /
      goal is a secondary guard (can reject, never authorizes). No negation
      skip in v0.3 — forbidden operations in free text are always rejected.
    - Operation–prompt consistency is verified.
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
                # Dangerous-command scan (word-boundary matching).
                # ``git merge-base`` is allowed; ``gh pr merge`` is rejected.
                # Use punctuation-aware normalization so trailing periods etc.
                # don't prevent phrase matching.
                norm_scan = _normalize_for_scan(item)
                rejected = False
                for phrase, code in _DANGEROUS_COMMAND_PHRASES:
                    if _matches_word(norm_scan, phrase):
                        errors.append(f"{POLICY_DANGEROUS_ACCEPTANCE_CHECK}:{code}")
                        rejected = True
                        break
                if not rejected:
                    # Shell metacharacter scan (substring matching).
                    # Use the original normalization (punctuation preserved)
                    # because the metacharacters themselves are the signal.
                    norm_raw = normalize_text(item).lower()
                    for token, reason in _SHELL_METACHAR_CHECKS:
                        if token in norm_raw:
                            errors.append(f"{POLICY_SHELL_METACHAR_FORBIDDEN}:{reason}")
                            break

    execution_prompt = task.get("execution_prompt")
    if not isinstance(execution_prompt, str) or not execution_prompt.strip():
        errors.append("NEXT_TASK_EXECUTION_PROMPT_REQUIRED")
    elif len(execution_prompt.strip()) > MAX_EXECUTION_PROMPT_LENGTH:
        errors.append(f"{FIELD_TOO_LONG}:next_task.execution_prompt")

    # --- v0.3: Strict natural-language keyword scan (NO negation skip). ---
    # allowed_scope: strict — any mention of a forbidden operation is rejected.
    # execution_prompt / goal: strict — NO negation skip in v0.3.
    #   A forbidden operation keyword appearing in goal or execution_prompt
    #   is rejected directly. Legitimate prohibitions belong in
    #   forbidden_scope, not prompt negation.
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
    # v0.3: use strict scan for free text too (no negation skip).
    _scan_policy_strict(free_text, errors)

    # --- v0.3: Operation–prompt consistency check. ---
    _check_operation_prompt_consistency(
        goal=goal if isinstance(goal, str) else "",
        execution_prompt=execution_prompt if isinstance(execution_prompt, str) else "",
        allowed_scope=allowed_scope if isinstance(allowed_scope, list) else [],
        requested_operations=requested_operations if isinstance(requested_operations, list) else [],
        errors=errors,
    )

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


def _normalize_for_scan(text: str) -> str:
    """Normalize text for keyword scanning: lowercase, collapse whitespace,
    and replace common punctuation with spaces so word-boundary matching
    handles trailing periods, commas, etc.

    Hyphens are preserved so that ``merge-base`` is NOT split into
    ``merge`` + ``base`` (``git merge-base`` must NOT be flagged for "merge").
    """

    norm = normalize_text(text).lower()
    # Replace punctuation (except hyphens) with spaces.
    for ch in ".,;:!?'\"()[]{}":
        norm = norm.replace(ch, " ")
    return " ".join(norm.split())


def _scan_policy_strict(texts: Sequence[str], errors: list[str]) -> None:
    """Strict scan: any mention of a forbidden operation is rejected,
    regardless of wording or negation. Word-boundary matching is used so
    that ``git merge-base`` is NOT flagged for "merge".

    All matching forbidden phrases are flagged (not just the first) so that
    a prompt mentioning both "merge" and "deploy" surfaces both violations.
    """

    for text in texts:
        norm = _normalize_for_scan(text)
        for phrase, code in _FORBIDDEN_PHRASES:
            if _matches_word(norm, phrase):
                errors.append(code)


def _occurrence_is_directly_negated(clause: str, start: int) -> bool:
    """Return whether the verb occurrence has a bounded direct negation."""

    return _DIRECT_NEGATION_BEFORE_RE.search(clause[:start]) is not None


def _clause_has_positive_verb(clause: str, patterns: Sequence[str]) -> bool:
    for pattern in patterns:
        for match in re.finditer(rf"\b(?:{pattern})\b", clause, re.IGNORECASE):
            if not _occurrence_is_directly_negated(clause, match.start()):
                return True
    return False


def _clause_has_positive_action_target(
    clause: str, patterns: Sequence[str]
) -> bool:
    """Match a finite action-target phrase whose action is not negated."""

    for pattern in patterns:
        for match in re.finditer(rf"\b(?:{pattern})\b", clause, re.IGNORECASE):
            if not _occurrence_is_directly_negated(clause, match.start()):
                return True
    return False


def _phrase_spans_longest_first(
    text: str, phrases: Sequence[str]
) -> tuple[tuple[int, int], ...]:
    """Return non-overlapping phrase spans, preferring the longest phrase."""

    spans: list[tuple[int, int]] = []
    for phrase in sorted(phrases, key=lambda value: (-len(value), value)):
        escaped = r"\s+".join(re.escape(part) for part in phrase.split())
        pattern = rf"(?<![a-z0-9_-]){escaped}(?![a-z0-9_-])"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = (match.start(), match.end())
            if any(candidate[0] < end and start < candidate[1] for start, end in spans):
                continue
            spans.append(candidate)
    return tuple(sorted(spans))


def _clause_has_repository_artifact_target(clause: str) -> bool:
    without_urls = _URL_RE.sub(" ", clause)
    if _EXPLICIT_FILE_TARGET_RE.search(without_urls) is not None:
        return True

    reporting_spans = _phrase_spans_longest_first(without_urls, _REPORTING_TARGETS)
    for target in sorted(
        _REPOSITORY_ARTIFACT_TARGETS, key=lambda value: (-len(value), value)
    ):
        escaped = r"\s+".join(re.escape(part) for part in target.split())
        pattern = rf"(?<![a-z0-9_-]){escaped}(?![a-z0-9_-])"
        for match in re.finditer(pattern, without_urls, re.IGNORECASE):
            if any(
                start <= match.start() and match.end() <= end
                for start, end in reporting_spans
            ):
                continue
            return True
    return False


def _classify_positive_mutation_surface(*texts: str) -> frozenset[str]:
    """Add all positive mutation surfaces found in each finite clause."""

    surfaces: set[str] = set()
    for text in texts:
        for raw_clause in _EDIT_CLAUSE_SPLIT_RE.split(normalize_text(text).lower()):
            clause = " ".join(raw_clause.split())
            if not clause:
                continue
            has_mutation_verb = _clause_has_positive_verb(
                clause, _GITHUB_MUTATION_VERB_PATTERNS
            )
            clause_surfaces: set[str] = set()
            has_draft_pr_mutation = (
                has_mutation_verb and _DRAFT_PR_TARGET_RE.search(clause) is not None
            )
            if has_draft_pr_mutation:
                surfaces.add(_DRAFT_PR_MUTATION)
                clause_surfaces.add(_DRAFT_PR_MUTATION)
            if _clause_has_positive_action_target(
                clause, _UNSUPPORTED_GITHUB_ACTION_TARGET_PATTERNS
            ):
                surfaces.add(_UNSUPPORTED_GITHUB_MUTATION)
                clause_surfaces.add(_UNSUPPORTED_GITHUB_MUTATION)

            target_analysis = _URL_RE.sub(" ", clause)
            has_repository_target = _clause_has_repository_artifact_target(clause)
            has_reporting_target = bool(
                _phrase_spans_longest_first(target_analysis, _REPORTING_TARGETS)
            )
            has_strong_edit = _clause_has_positive_verb(
                clause, _STRONG_EDIT_VERB_PATTERNS
            )
            has_ambiguous_edit = _clause_has_positive_verb(
                clause, _AMBIGUOUS_EDIT_VERB_PATTERNS
            )
            if has_repository_target and (has_strong_edit or has_ambiguous_edit):
                surfaces.add(_REPOSITORY_MUTATION)
                clause_surfaces.add(_REPOSITORY_MUTATION)
            elif (
                has_strong_edit
                and not has_reporting_target
                and not clause_surfaces
            ):
                surfaces.add(_REPOSITORY_MUTATION)
                clause_surfaces.add(_REPOSITORY_MUTATION)

            if not clause_surfaces:
                surfaces.add(_READ_ONLY if has_mutation_verb else _NONE)
    return frozenset(surfaces)


def _has_positive_named_branch_push_intent(*texts: str) -> bool:
    """Detect positive push publication bound to a branch/origin target."""

    for text in texts:
        for raw_clause in _EDIT_CLAUSE_SPLIT_RE.split(normalize_text(text).lower()):
            clause = " ".join(raw_clause.split())
            if not clause:
                continue
            for match in re.finditer(
                rf"\b(?:{_PUSH_VERB_PATTERN})\b", clause, re.IGNORECASE
            ):
                if _occurrence_is_directly_negated(clause, match.start()):
                    continue
                if _PUSH_TARGET_RE.search(clause[match.end():]):
                    return True
    return False


def _check_operation_prompt_consistency(
    *,
    goal: str,
    execution_prompt: str,
    allowed_scope: list,
    requested_operations: list,
    errors: list[str],
) -> None:
    """Verify that the requested_operations match what the prompt describes.

    - ``allowed_scope`` defines bounded accessible scope. Paths remain
      read-only unless ``edit_bounded_files`` is requested.
    - Positive clauses are first classified by mutation surface, then checked
      against the permission for that surface.
    - Positive branch/origin push intent requires ``push_named_branch``.
    """

    ops = {str(o) for o in requested_operations if isinstance(o, str)}
    surfaces = _classify_positive_mutation_surface(goal, execution_prompt)

    if (
        _REPOSITORY_MUTATION in surfaces
        and "edit_bounded_files" not in ops
    ):
        errors.append(
            f"{OPERATION_PROMPT_INCONSISTENCY}:edit_bounded_files_required"
        )

    if (
        _DRAFT_PR_MUTATION in surfaces
        and "create_or_update_draft_pr" not in ops
    ):
        errors.append(
            f"{OPERATION_PROMPT_INCONSISTENCY}:create_or_update_draft_pr_required"
        )

    if _UNSUPPORTED_GITHUB_MUTATION in surfaces:
        errors.append(
            f"{OPERATION_PROMPT_INCONSISTENCY}:unsupported_mutation_surface"
        )

    # Pushing a named branch requires push_named_branch.
    if _has_positive_named_branch_push_intent(goal, execution_prompt):
        if "push_named_branch" not in ops:
            errors.append(f"{OPERATION_PROMPT_INCONSISTENCY}:push_named_branch_required")

def _matches_word(text: str, keyword: str) -> bool:
    """Match ``keyword`` as a whole word in ``text``.

    Uses space-delimited boundaries so that ``merge`` matches in
    ``gh pr merge 93`` but NOT in ``git merge-base`` (where "merge"
    is followed by "-", not a space).
    """

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
    parser = argparse.ArgumentParser(description="Validate a Codex Supervisor audit result (fail-closed v0.3)")
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

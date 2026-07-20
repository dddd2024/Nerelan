"""Independent preflight validation for control-plane transition rounds."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, Iterable

from .command_authority import authorize_command, validate_command_plan
from .models import ExecutionEnvelope, TransitionAuthority, TransitionPreflightResult


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def _path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    candidate = pattern.replace("\\", "/").lstrip("./")
    if candidate.endswith("/**"):
        return normalized.startswith(candidate[:-3].rstrip("/") + "/")
    return normalized == candidate or fnmatch(normalized, candidate)


def _paths_within_scope(paths: Iterable[str], patterns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        path for path in paths
        if not any(_path_matches(path, pattern) for pattern in patterns)
    )


def validate_transition(
    authority: TransitionAuthority,
    envelopes: tuple[ExecutionEnvelope, ...] = (),
) -> TransitionPreflightResult:
    """Validate transition authority without consulting legacy acceptance state."""

    decision = authority.decision
    checks: list[dict[str, Any]] = []
    checks.append(_check(
        "decision_identity",
        decision.decision_id == authority.expected_decision_id,
        f"observed={decision.decision_id} expected={authority.expected_decision_id}",
    ))
    checks.append(_check(
        "round_identity",
        decision.round_id == authority.expected_round_id,
        f"observed={decision.round_id} expected={authority.expected_round_id}",
    ))
    checks.append(_check("decision_approved", decision.status == "APPROVED", f"status={decision.status}"))
    missing_skills = tuple(skill for skill in decision.skill_profiles if skill not in authority.active_skills)
    checks.append(_check("active_skills", not missing_skills, f"missing={list(missing_skills)}"))
    checks.append(_check(
        "legal_mainline",
        decision.mainline in authority.legal_mainlines,
        f"mainline={decision.mainline}",
    ))
    branch_ok = authority.actual_branch == authority.expected_branch
    checks.append(_check(
        "branch_identity",
        branch_ok,
        f"observed={authority.actual_branch} expected={authority.expected_branch}",
    ))
    checks.append(_check(
        "base_ancestry",
        bool(authority.base_sha) and authority.merge_base_sha == authority.base_sha,
        f"base={authority.base_sha} merge_base={authority.merge_base_sha}",
    ))
    checks.append(_check(
        "decision_ancestry",
        bool(authority.decision_commit_sha) and authority.decision_is_ancestor,
        f"decision_commit={authority.decision_commit_sha}",
    ))
    plan_identity_ok = (
        authority.command_plan.decision_id == decision.decision_id
        and authority.command_plan.round_id == decision.round_id
    )
    checks.append(_check(
        "command_plan_identity",
        plan_identity_ok,
        f"plan={authority.command_plan.decision_id}/{authority.command_plan.round_id}",
    ))
    plan_errors = validate_command_plan(authority.command_plan)
    checks.append(_check("command_plan_contract", not plan_errors, f"errors={list(plan_errors)}"))

    mutated_paths = tuple(dict.fromkeys(
        (*authority.observed_paths, *(path for envelope in envelopes for path in envelope.mutated_paths))
    ))
    outside_scope = _paths_within_scope(mutated_paths, authority.allowed_paths)
    forbidden_paths = tuple(
        path for path in mutated_paths
        if any(_path_matches(path, pattern) for pattern in authority.forbidden_paths)
    )
    checks.append(_check("allowed_path_scope", not outside_scope, f"outside={list(outside_scope)}"))
    checks.append(_check("forbidden_paths", not forbidden_paths, f"forbidden={list(forbidden_paths)}"))

    command_errors = tuple(
        error
        for envelope in envelopes
        for error in authorize_command(authority.command_plan, envelope)
    )
    checks.append(_check("command_authority", not command_errors, f"errors={list(command_errors)}"))
    operations = tuple(operation for envelope in envelopes for operation in envelope.operations)
    forbidden_operations = tuple(
        operation for operation in operations if operation in authority.forbidden_operations
    )
    checks.append(_check(
        "forbidden_operations",
        not forbidden_operations,
        f"forbidden={list(forbidden_operations)}",
    ))

    blocking = tuple(
        f"{check['name']}: {check['detail']}"
        for check in checks
        if check["status"] == "FAIL"
    )
    return TransitionPreflightResult(
        decision_id=decision.decision_id,
        round_id=decision.round_id,
        gate_status="PASSED" if not blocking else "BLOCKED",
        checks=tuple(checks),
        blocking_reasons=blocking,
    )

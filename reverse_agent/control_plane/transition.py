"""Independent preflight validation for control-plane transition rounds."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, Iterable

from .command_authority import authorize_command, canonical_command, validate_command_plan
from .execution_reconciliation import reconcile_executions
from .models import (
    CapabilityPolicy,
    ExecutionEnvelope,
    PathRiskFloor,
    TransitionAuthority,
    TransitionPreflightResult,
)


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


def _paths_in_forbidden(paths: Iterable[str], patterns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        path for path in paths
        if any(_path_matches(path, pattern) for pattern in patterns)
    )


def _capability_forbidden_operations(policy: CapabilityPolicy) -> tuple[str, ...]:
    """Map capability flags to forbidden operations.

    Each flag that is ``False`` must add its corresponding operation to the
    forbidden set so the machine gate stays in sync with the Decision.
    """

    mapping = {
        "runner_dispatch_allowed": "runner_dispatch",
        "model_api_invocation_allowed": "model_api_invocation",
        "external_reverse_tool_invocation_allowed": "external_reverse_tool_invocation",
        "unknown_binary_execution_allowed": "unknown_binary_execution",
        "destructive_operations_allowed": "destructive",
        "bmad_installation_allowed": "bmad_installation",
        "direct_push_to_main_allowed": "direct_push_main",
        "merge_allowed": "merge",
        "force_push_allowed": "force_push",
        "rebase_during_execution_allowed": "rebase",
        "tag_or_release_allowed": "tag_or_release",
    }
    operations: list[str] = []
    for field, operation in mapping.items():
        if not getattr(policy, field, False):
            operations.append(operation)
    return tuple(dict.fromkeys(operations))


def _envelope_network_violations(
    envelopes: tuple[ExecutionEnvelope, ...],
    policy: CapabilityPolicy,
) -> tuple[str, ...]:
    """Check that network access honors the capability policy.

    Local envelopes must not declare network operations unless they appear in
    ``local_network_exceptions``. CI envelopes must not declare network
    operations unless they appear in ``ci_network_exceptions``.
    """

    violations: list[str] = []
    network_operations = {"network_access", "network", "package_install", "dependency_install"}
    for envelope in envelopes:
        if not any(op in network_operations for op in envelope.operations):
            continue
        if envelope.execution_surface == "local":
            allowed_exceptions = policy.local_network_exceptions
        elif envelope.execution_surface == "ci_only":
            allowed_exceptions = policy.ci_network_exceptions
        else:
            allowed_exceptions = ()
        requested = canonical_command(envelope.command)
        if requested in {canonical_command(item) for item in allowed_exceptions}:
            continue
        violations.append(
            f"network_access_violation:{envelope.execution_surface}:{requested}"
        )
    return tuple(dict.fromkeys(violations))


def _path_risk_floor_violations(
    observed_paths: tuple[str, ...],
    path_risk_floor: PathRiskFloor | None,
    *,
    minimum: str = "R2",
) -> tuple[str, ...]:
    """Return paths that violate the risk floor for sensitive locations."""

    if path_risk_floor is None or not path_risk_floor.entries:
        return ()
    floor_rank = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
    minimum_rank = floor_rank.get(minimum, 2)
    violations: list[str] = []
    for path in observed_paths:
        risk = path_risk_floor.risk_for_path(path)
        if risk is None:
            continue
        if floor_rank.get(risk, 0) >= minimum_rank:
            violations.append(f"{path}:{risk}")
    return tuple(dict.fromkeys(violations))


def _reference_path_write_violations(
    observed_paths: tuple[str, ...],
    reference_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Ensure reference (read-only) paths are not mutated."""

    violations: list[str] = []
    for path in observed_paths:
        for pattern in reference_paths:
            if _path_matches(path, pattern):
                violations.append(f"{path}:reference_path_mutated")
                break
    return tuple(dict.fromkeys(violations))


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
    forbidden_paths = _paths_in_forbidden(mutated_paths, authority.forbidden_paths)
    checks.append(_check("allowed_path_scope", not outside_scope, f"outside={list(outside_scope)}"))
    checks.append(_check("forbidden_paths", not forbidden_paths, f"forbidden={list(forbidden_paths)}"))

    # Reference paths must remain read-only even when they appear in the Decision.
    # Paths explicitly allowed for mutation (in ``allowed_paths``) are excluded
    # so the gate can regenerate command_plan.json / execution_log.json without
    # tripping the read-only guard when the Decision authorizes those writes.
    reference_violations = _reference_path_write_violations(outside_scope, authority.reference_paths)
    checks.append(_check(
        "reference_paths_read_only",
        not reference_violations,
        f"violations={list(reference_violations)}",
    ))

    # Capability policy mapping.
    if authority.capability_policy is not None:
        capability_forbidden = _capability_forbidden_operations(authority.capability_policy)
        all_forbidden = tuple(dict.fromkeys((*authority.forbidden_operations, *capability_forbidden)))
        operations = tuple(operation for envelope in envelopes for operation in envelope.operations)
        forbidden_operations = tuple(
            operation for operation in operations if operation in all_forbidden
        )
        checks.append(_check(
            "capability_policy_enforced",
            not forbidden_operations,
            f"forbidden={list(forbidden_operations)}",
        ))
        network_violations = _envelope_network_violations(envelopes, authority.capability_policy)
        checks.append(_check(
            "network_policy_enforced",
            not network_violations,
            f"violations={list(network_violations)}",
        ))
    else:
        operations = tuple(operation for envelope in envelopes for operation in envelope.operations)
        forbidden_operations = tuple(
            operation for operation in operations if operation in authority.forbidden_operations
        )
        checks.append(_check(
            "forbidden_operations",
            not forbidden_operations,
            f"forbidden={list(forbidden_operations)}",
        ))

    # Path risk floor enforcement. Only paths outside the explicitly allowed
    # scope are checked; ``allowed_mutated_paths`` already authorizes those
    # writes and the risk floor's job is to classify, not to block authorized
    # regeneration of gate artifacts.
    if authority.path_risk_floor is not None and authority.path_risk_floor.entries:
        floor_violations = _path_risk_floor_violations(
            outside_scope,
            authority.path_risk_floor,
            minimum="R2",
        )
        checks.append(_check(
            "path_risk_floor_enforced",
            not floor_violations,
            f"violations={list(floor_violations)}",
        ))

    # Real execution reconciliation. When no envelopes are supplied the gate
    # must fail closed rather than report ``command_authority=PASS``.
    reconciliation = reconcile_executions(authority.command_plan, envelopes)
    checks.append(_check(
        "execution_reconciliation",
        reconciliation.status != "BLOCKED",
        f"status={reconciliation.status} reasons={list(reconciliation.blocking_reasons)}",
    ))
    checks.append(_check(
        "execution_evidence_present",
        not reconciliation.missing_evidence,
        f"missing_evidence={reconciliation.missing_evidence}",
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

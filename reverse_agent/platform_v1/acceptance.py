"""Deterministic accepter: derive acceptance from evidence, not agent claims.

The accepter evaluates ``ExecutionEvidence`` and returns a
``PlatformAcceptanceResult``. The agent's completion claim is never allowed
to override Git or test failures.
"""

from __future__ import annotations

from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)
from .policy_adapter import validate_changed_paths, validate_work_item


def evaluate_acceptance(
    binding: ExecutionBinding,
    evidence: ExecutionEvidence,
) -> PlatformAcceptanceResult:
    """Evaluate acceptance deterministically.

    Decision order (fail-closed at each step):
    1. Policy validation — if the binding is invalid, FAILED_TERMINAL.
    2. Changed-path scope — if any path is outside allowed scope, BLOCKED_APPROVAL.
    3. Git diff check — if failed, REWORK_REQUIRED.
    4. Tests — if failed, REWORK_REQUIRED (agent claim cannot override).
    5. CI checks — if failed, REWORK_REQUIRED (agent claim cannot override).
    6. All pass — ACCEPTED.
    """

    execution_id = binding.execution_id
    work_item = binding.work_item

    # 1. Policy validation
    try:
        validate_work_item(work_item)
    except Exception as exc:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(f"policy_validation_failed:{exc}",),
            evidence=evidence,
        )

    # 2. Changed-path scope
    outside = validate_changed_paths(evidence.changed_paths, work_item.allowed_paths)
    if outside:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="BLOCKED_APPROVAL",
            reasons=(f"out_of_scope_paths:{','.join(outside)}",),
            evidence=evidence,
        )

    # 3. Git diff check
    if not evidence.git_diff_check_passed:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="REWORK_REQUIRED",
            reasons=("git_diff_check_failed",),
            evidence=evidence,
        )

    # 4. Tests (agent claim cannot override)
    if not evidence.tests_passed:
        claim_note = ""
        if evidence.agent_completion_claim:
            claim_note = " (agent_claim_ignored)"
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="REWORK_REQUIRED",
            reasons=(f"tests_failed{claim_note}",),
            evidence=evidence,
        )

    # 5. CI checks (agent claim cannot override)
    if not evidence.ci_passed:
        claim_note = ""
        if evidence.agent_completion_claim:
            claim_note = " (agent_claim_ignored)"
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="REWORK_REQUIRED",
            reasons=(f"ci_checks_failed{claim_note}",),
            evidence=evidence,
        )

    # 6. All pass
    return PlatformAcceptanceResult(
        execution_id=execution_id,
        status="ACCEPTED",
        reasons=("all_checks_passed",),
        evidence=evidence,
    )


def can_retry(result: PlatformAcceptanceResult, binding: ExecutionBinding) -> bool:
    """Return True if the result allows a bounded retry."""

    if result.status == "ACCEPTED":
        return False
    if result.status == "FAILED_TERMINAL":
        return False
    # REWORK_REQUIRED and BLOCKED_APPROVAL may allow a retry if attempts remain
    from .contracts import MAX_ATTEMPTS
    return binding.attempt < MAX_ATTEMPTS

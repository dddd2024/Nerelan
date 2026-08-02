"""Deterministic accepter: derive acceptance from evidence, not agent claims.

The accepter evaluates ``ExecutionEvidence`` and returns a
``PlatformAcceptanceResult``. The agent's completion claim is never allowed
to override Git or test failures.

R2/R3 risk tiers return ``BLOCKED_APPROVAL`` before any backend invocation
or evidence evaluation.

F9: Fixture evidence (from ``from_mapping`` or stdin) that passes all checks
returns ``FIXTURE_VALIDATED`` — never ``ACCEPTED``, never ``live_ready: True``,
never the live-success exit code. Only the trusted live collector path can
return ``ACCEPTED`` with ``live_ready: True``.
"""

from __future__ import annotations

from .contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)
from .policy_adapter import (
    PolicyViolation,
    is_blocked_approval_violation,
    validate_changed_paths,
    validate_work_item,
)


def evaluate_acceptance(
    binding: ExecutionBinding,
    evidence: ExecutionEvidence,
) -> PlatformAcceptanceResult:
    """Evaluate acceptance deterministically.

    Decision order (fail-closed at each step):
    1. Policy validation — if R2/R3, BLOCKED_APPROVAL; other policy
       violations, FAILED_TERMINAL.
    2. Evidence binding — execution_id, repository, base_sha must match.
    3. Changed-path scope — if any path is outside allowed scope, BLOCKED_APPROVAL.
    4. Git diff check — if failed, REWORK_REQUIRED.
    5. Tests — if failed, REWORK_REQUIRED (agent claim cannot override).
    6. CI checks — if failed, REWORK_REQUIRED (agent claim cannot override).
    7. All pass — FIXTURE_VALIDATED for fixture evidence; ACCEPTED for live evidence.
    """

    execution_id = binding.execution_id
    work_item = binding.work_item

    # 1. Policy validation — R2/R3 blocked before any backend call
    try:
        validate_work_item(work_item)
    except PolicyViolation as exc:
        if is_blocked_approval_violation(exc):
            return PlatformAcceptanceResult(
                execution_id=execution_id,
                status="BLOCKED_APPROVAL",
                reasons=(f"blocked_approval:risk_tier={exc.detail}",),
                evidence=evidence,
            )
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(f"policy_validation_failed:{exc}",),
            evidence=evidence,
        )
    except Exception as exc:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(f"policy_validation_failed:{exc}",),
            evidence=evidence,
        )

    # 2. Evidence binding validation
    try:
        evidence.validate_binding(work_item)
    except Exception as exc:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(f"evidence_binding_failed:{exc}",),
            evidence=evidence,
        )

    # 2b. Head SHA and PR number binding (when the binding specifies expected values)
    if binding.expected_head_sha and evidence.head_sha != binding.expected_head_sha:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(
                f"head_sha_mismatch:evidence={evidence.head_sha} expected={binding.expected_head_sha}",
            ),
            evidence=evidence,
        )
    if binding.expected_pr_number and evidence.pr_number != binding.expected_pr_number:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="FAILED_TERMINAL",
            reasons=(
                f"pr_number_mismatch:evidence={evidence.pr_number} expected={binding.expected_pr_number}",
            ),
            evidence=evidence,
        )

    # 3. Changed-path scope
    outside = validate_changed_paths(evidence.changed_paths, work_item.allowed_paths)
    if outside:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="BLOCKED_APPROVAL",
            reasons=(f"out_of_scope_paths:{','.join(outside)}",),
            evidence=evidence,
        )

    # 4. Git diff check
    if not evidence.git_diff_check_passed:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="REWORK_REQUIRED",
            reasons=("git_diff_check_failed",),
            evidence=evidence,
        )

    # 5. Tests (agent claim cannot override)
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

    # 6. CI checks (agent claim cannot override)
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

    # 7. All pass — F9: fixture evidence returns FIXTURE_VALIDATED, not ACCEPTED.
    #    Only live evidence (from the trusted collector) returns ACCEPTED.
    if evidence.is_live:
        return PlatformAcceptanceResult(
            execution_id=execution_id,
            status="ACCEPTED",
            reasons=("all_checks_passed",),
            evidence=evidence,
        )
    return PlatformAcceptanceResult(
        execution_id=execution_id,
        status="FIXTURE_VALIDATED",
        reasons=("all_checks_passed_fixture",),
        evidence=evidence,
    )


def can_retry(result: PlatformAcceptanceResult, binding: ExecutionBinding) -> bool:
    """Return True if the result allows a bounded retry.

    F16: ``BLOCKED_APPROVAL``, ``FAILED_TERMINAL``, and ``ACCEPTED`` are never
    retryable. Only ``REWORK_REQUIRED`` with attempts remaining allows one
    bounded retry. ``FIXTURE_VALIDATED`` is not retryable (it is a success
    for fixture purposes).
    """

    if result.status in ("ACCEPTED", "FIXTURE_VALIDATED"):
        return False
    if result.status in ("BLOCKED_APPROVAL", "FAILED_TERMINAL"):
        return False
    # Only REWORK_REQUIRED with attempts remaining
    from .contracts import MAX_ATTEMPTS
    return binding.attempt < MAX_ATTEMPTS

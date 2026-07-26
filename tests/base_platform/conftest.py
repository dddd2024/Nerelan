from __future__ import annotations

import pytest

from reverse_agent.base_platform import (
    CapabilityManifest,
    GoalContract,
    NaturalLanguageRequest,
    RetryPolicy,
    SpecPackage,
)


@pytest.fixture
def approved_spec() -> SpecPackage:
    return SpecPackage(
        identity="spec:46",
        request=NaturalLanguageRequest(
            identity="request:46",
            text="Implement the approved bounded change.",
            requested_operations=("unit_test", "source_edit"),
        ),
        goal=GoalContract(
            identity="goal:46",
            objective="Deliver deterministic protocol contracts.",
            acceptance_criteria=("Contracts exist.", "Required checks pass."),
            required_checks=("git diff --check", "pytest"),
        ),
        approved=True,
        approval_identity="dddd2024/reverse-agent#46@digest",
        requested_risk_tier="R1",
        allowed_operations=("draft_pr", "source_edit", "unit_test"),
        forbidden_operations=("merge",),
        required_operations=("source_edit", "unit_test"),
        required_approval="r1-approved",
        required_checks=("pytest", "static-import-check"),
        requested_retry_policy=RetryPolicy(
            identity="retry:46",
            max_attempts=3,
            retryable_error_codes=("NETWORK_TRANSIENT", "LOCKED_FILE"),
        ),
    )


@pytest.fixture
def capabilities() -> CapabilityManifest:
    return CapabilityManifest(
        identity="capabilities:codex",
        supported_operations=("source_edit", "unit_test"),
        supported_risk_tiers=("R0", "R1"),
        required_checks=("git diff --check",),
        max_retry_attempts=2,
    )

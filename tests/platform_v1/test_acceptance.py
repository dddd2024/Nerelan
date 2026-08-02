"""Tests for the Platform V1 acceptance evaluator.

Covers:
- ACCEPTED when all checks pass (R0/R1 only; R2/R3 return BLOCKED_APPROVAL)
- BLOCKED_APPROVAL for R2/R3 risk tiers (before any backend invocation)
- FAILED_TERMINAL when evidence binding mismatches
- FAILED_TERMINAL for non-blocked-approval policy violations
- REWORK_REQUIRED when git diff check fails
- REWORK_REQUIRED when tests fail (agent claim cannot override)
- REWORK_REQUIRED when CI fails (agent claim cannot override)
- BLOCKED_APPROVAL when paths are out of scope
- live_ready depends on evidence collection_mode
- can_retry logic
"""

from __future__ import annotations

import pytest

from reverse_agent.platform_v1.acceptance import can_retry, evaluate_acceptance
from reverse_agent.platform_v1.contracts import (
    ExecutionBinding,
    ExecutionEvidence,
    PlatformWorkItem,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"
VALID_ISSUE_BODY_DIGEST = "a" * 40


def _make_work_item(**overrides) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ("reverse_agent/platform_v1/**", "tests/platform_v1/**"),
        "forbidden_operations": ("push_main", "merge"),
        "acceptance_criteria": ("pytest passes",),
        "goal": "test goal",
        "required_checks": ("pytest",),
        "approved_issue_body_digest": VALID_ISSUE_BODY_DIGEST,
        # R0 so the work item can reach ACCEPTED; tests that need R2/R3
        # override this explicitly.
        "risk_tier": "R0",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


def _make_evidence(work_item: PlatformWorkItem, **overrides) -> ExecutionEvidence:
    """Build evidence that binds to the given work item by default.

    The evidence's execution_id, repository, and base_sha are seeded from
    the work item so ``validate_binding`` passes unless the caller overrides
    them to test a mismatch.
    """

    defaults = {
        "execution_id": work_item.execution_id,
        "repository": work_item.repository,
        "base_sha": work_item.base_sha,
        "head_sha": VALID_HEAD_SHA,
        "pr_number": 97,
        "required_workflows": ("CI",),
        "changed_paths": ("reverse_agent/platform_v1/__init__.py",),
        "test_results": {"passed": True},
        "git_diff_check_passed": True,
        "agent_completion_claim": "",
        "ci_checks": ({"name": "CI", "conclusion": "SUCCESS"},),
        "collected_at": "",
    }
    defaults.update(overrides)
    return ExecutionEvidence(**defaults)


# ---------------------------------------------------------------------------
# evaluate_acceptance
# ---------------------------------------------------------------------------

class TestEvaluateAcceptance:
    def test_all_pass_fixture_returns_fixture_validated(self) -> None:
        # F9: fixture evidence returns FIXTURE_VALIDATED, not ACCEPTED
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FIXTURE_VALIDATED"
        assert "all_checks_passed_fixture" in result.reasons
        assert result.accepted is False
        assert result.live_ready is False

    def test_all_pass_live_returns_accepted(self) -> None:
        # F9: only live evidence returns ACCEPTED
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(binding.work_item, collection_mode="live")
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "ACCEPTED"
        assert "all_checks_passed" in result.reasons

    def test_git_diff_check_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(binding.work_item, git_diff_check_passed=False)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "git_diff_check_failed" in result.reasons

    def test_tests_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(binding.work_item, test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "tests_failed" in result.reasons

    def test_ci_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            required_workflows=("CI", "State Gate"),
            ci_checks=(
                {"name": "CI", "conclusion": "SUCCESS"},
                {"name": "State Gate", "conclusion": "FAILURE"},
            ),
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "ci_checks_failed" in result.reasons

    def test_out_of_scope_paths_return_blocked(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            changed_paths=(
                "reverse_agent/platform_v1/cli.py",
                "pyproject.toml",  # out of scope
            ),
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert any("out_of_scope_paths" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# R2/R3 blocked approval
# ---------------------------------------------------------------------------

class TestBlockedApproval:
    """R2/R3 risk tiers must return BLOCKED_APPROVAL before backend invocation."""

    def test_R2_returns_blocked_approval_not_accepted(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"))
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert any("blocked_approval" in r for r in result.reasons)
        assert result.accepted is False

    def test_R3_returns_blocked_approval_not_accepted(self) -> None:
        # R3 is valid at construction but blocked by policy.
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R3"))
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert any("blocked_approval" in r for r in result.reasons)
        assert result.accepted is False

    def test_R2_blocked_even_when_evidence_all_pass(self) -> None:
        # Even with perfect evidence, R2 must never return ACCEPTED.
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"))
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status != "ACCEPTED"
        assert result.status == "BLOCKED_APPROVAL"


# ---------------------------------------------------------------------------
# Evidence binding validation
# ---------------------------------------------------------------------------

class TestEvidenceBindingValidation:
    """Evidence binding mismatches return FAILED_TERMINAL."""

    def test_mismatched_execution_id_returns_failed_terminal(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            execution_id="exec-different",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FAILED_TERMINAL"
        assert any("evidence_binding_failed" in r for r in result.reasons)

    def test_mismatched_repository_returns_failed_terminal(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            repository="other/repo",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FAILED_TERMINAL"
        assert any("evidence_binding_failed" in r for r in result.reasons)

    def test_mismatched_base_sha_returns_failed_terminal(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            base_sha="0" * 40,
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FAILED_TERMINAL"
        assert any("evidence_binding_failed" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Non-blocked-approval policy violations return FAILED_TERMINAL
# ---------------------------------------------------------------------------

class TestPolicyValidationFailed:
    def test_policy_validation_failed_returns_terminal(self) -> None:
        # R0/R1 pass the tier check; an empty path scope is a non-blocked
        # policy violation, which the accepter maps to FAILED_TERMINAL.
        wi = _make_work_item()
        object.__setattr__(wi, "allowed_paths", ())
        binding = ExecutionBinding(work_item=wi)
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FAILED_TERMINAL"
        assert any("policy_validation_failed" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Agent claim cannot override
# ---------------------------------------------------------------------------

class TestAgentClaimCannotOverride:
    """The agent's completion claim must never override Git or test failures."""

    def test_agent_claim_does_not_override_tests_failed(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            test_results={"passed": False},
            agent_completion_claim="Task completed successfully. All tests pass.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert any("agent_claim_ignored" in r for r in result.reasons)

    def test_agent_claim_does_not_override_ci_failed(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            ci_checks=({"name": "CI", "conclusion": "FAILURE"},),
            agent_completion_claim="Done. CI is green.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert any("agent_claim_ignored" in r for r in result.reasons)

    def test_agent_claim_does_not_override_git_diff_failed(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            git_diff_check_passed=False,
            agent_completion_claim="All checks green.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "git_diff_check_failed" in result.reasons

    def test_agent_claim_preserved_in_evidence_when_all_pass(self) -> None:
        # F9: fixture evidence returns FIXTURE_VALIDATED; agent claim is preserved
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            agent_completion_claim="Done.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FIXTURE_VALIDATED"
        assert result.evidence.agent_completion_claim == "Done."


# ---------------------------------------------------------------------------
# live_ready
# ---------------------------------------------------------------------------

class TestLiveReady:
    """live_ready is True only when ACCEPTED with live-mode evidence.

    F9: Fixture evidence returns FIXTURE_VALIDATED (never ACCEPTED), and is
    never live_ready — even if all checks pass.
    """

    def test_fixture_evidence_returns_fixture_validated_not_live_ready(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            collection_mode="fixture",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "FIXTURE_VALIDATED"
        assert result.live_ready is False

    def test_live_evidence_accepted_and_live_ready(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            collection_mode="live",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "ACCEPTED"
        assert result.live_ready is True

    def test_rework_required_not_live_ready_even_with_live_evidence(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            binding.work_item,
            collection_mode="live",
            test_results={"passed": False},
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert result.live_ready is False

    def test_R2_blocked_not_live_ready_even_with_live_evidence(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"))
        evidence = _make_evidence(
            binding.work_item,
            collection_mode="live",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert result.live_ready is False


# ---------------------------------------------------------------------------
# can_retry
# ---------------------------------------------------------------------------

class TestCanRetry:
    """F16: Only REWORK_REQUIRED with attempts remaining can retry.

    BLOCKED_APPROVAL, FAILED_TERMINAL, ACCEPTED, and FIXTURE_VALIDATED are
    never retryable.
    """

    def test_accepted_cannot_retry(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(binding.work_item, collection_mode="live")
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "ACCEPTED"
        assert can_retry(result, binding) is False

    def test_fixture_validated_cannot_retry(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        result = evaluate_acceptance(binding, _make_evidence(binding.work_item))
        assert result.status == "FIXTURE_VALIDATED"
        assert can_retry(result, binding) is False

    def test_failed_terminal_cannot_retry(self) -> None:
        wi = _make_work_item()
        object.__setattr__(wi, "allowed_paths", ())
        binding = ExecutionBinding(work_item=wi)
        result = evaluate_acceptance(binding, _make_evidence(binding.work_item))
        assert result.status == "FAILED_TERMINAL"
        assert can_retry(result, binding) is False

    def test_rework_required_can_retry_attempt_one(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
        evidence = _make_evidence(binding.work_item, test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert can_retry(result, binding) is True

    def test_rework_required_cannot_retry_at_max_attempts(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=2)
        evidence = _make_evidence(binding.work_item, test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert can_retry(result, binding) is False

    def test_blocked_approval_R2_cannot_retry(self) -> None:
        # F16: BLOCKED_APPROVAL is never retryable, even with attempts remaining
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"), attempt=1)
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert can_retry(result, binding) is False

    def test_blocked_approval_R2_cannot_retry_at_max_attempts(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(risk_tier="R2"), attempt=2)
        evidence = _make_evidence(binding.work_item)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert can_retry(result, binding) is False

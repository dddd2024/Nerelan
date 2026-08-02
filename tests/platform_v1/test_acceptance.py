"""Tests for the Platform V1 acceptance evaluator.

Covers:
- ACCEPTED when all checks pass
- REWORK_REQUIRED when git diff check fails
- REWORK_REQUIRED when tests fail (agent claim cannot override)
- REWORK_REQUIRED when CI fails (agent claim cannot override)
- BLOCKED_APPROVAL when paths are out of scope
- FAILED_TERMINAL when policy validation fails
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


def _make_work_item(**overrides) -> PlatformWorkItem:
    defaults = {
        "source_issue_number": 96,
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "allowed_paths": ("reverse_agent/platform_v1/**", "tests/platform_v1/**"),
        "forbidden_operations": ("push_main", "merge"),
        "acceptance_criteria": ("pytest passes",),
        "risk_tier": "R2",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


def _make_evidence(**overrides) -> ExecutionEvidence:
    defaults = {
        "execution_id": "exec-1",
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
    def test_all_pass_returns_accepted(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence()
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "ACCEPTED"
        assert "all_checks_passed" in result.reasons

    def test_git_diff_check_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(git_diff_check_passed=False)
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "git_diff_check_failed" in result.reasons

    def test_tests_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "tests_failed" in result.reasons

    def test_ci_failed_returns_rework(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
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
            changed_paths=(
                "reverse_agent/platform_v1/cli.py",
                "pyproject.toml",  # out of scope
            ),
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "BLOCKED_APPROVAL"
        assert any("out_of_scope_paths" in r for r in result.reasons)

    def test_policy_validation_failed_returns_terminal(self) -> None:
        wi = _make_work_item()
        # Tamper with risk_tier to simulate an invalid binding
        object.__setattr__(wi, "risk_tier", "R3")
        binding = ExecutionBinding(work_item=wi)
        evidence = _make_evidence()
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
            test_results={"passed": False},
            agent_completion_claim="Task completed successfully. All tests pass.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert any("agent_claim_ignored" in r for r in result.reasons)

    def test_agent_claim_does_not_override_ci_failed(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            ci_checks=({"name": "CI", "conclusion": "FAILURE"},),
            agent_completion_claim="Done. CI is green.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert any("agent_claim_ignored" in r for r in result.reasons)

    def test_agent_claim_does_not_override_git_diff_failed(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(
            git_diff_check_passed=False,
            agent_completion_claim="All checks green.",
        )
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert "git_diff_check_failed" in result.reasons

    def test_agent_claim_preserved_in_evidence_when_all_pass(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        evidence = _make_evidence(agent_completion_claim="Done.")
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "ACCEPTED"
        assert result.evidence.agent_completion_claim == "Done."


# ---------------------------------------------------------------------------
# can_retry
# ---------------------------------------------------------------------------

class TestCanRetry:
    def test_accepted_cannot_retry(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        result = evaluate_acceptance(binding, _make_evidence())
        assert can_retry(result, binding) is False

    def test_failed_terminal_cannot_retry(self) -> None:
        wi = _make_work_item()
        object.__setattr__(wi, "risk_tier", "R3")
        binding = ExecutionBinding(work_item=wi)
        result = evaluate_acceptance(binding, _make_evidence())
        assert result.status == "FAILED_TERMINAL"
        assert can_retry(result, binding) is False

    def test_rework_required_can_retry_attempt_one(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
        evidence = _make_evidence(test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert can_retry(result, binding) is True

    def test_rework_required_cannot_retry_at_max_attempts(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=2)
        evidence = _make_evidence(test_results={"passed": False})
        result = evaluate_acceptance(binding, evidence)
        assert result.status == "REWORK_REQUIRED"
        assert can_retry(result, binding) is False

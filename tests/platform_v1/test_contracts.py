"""Tests for the Platform V1 core contracts.

Covers:
- PlatformWorkItem normalization, validation, and digest determinism
- ExecutionBinding attempt limits
- ExecutionEvidence immutability and derived flags
- PlatformAcceptanceResult status whitelist
"""

from __future__ import annotations

import pytest

from reverse_agent.platform_v1.contracts import (
    MAX_ATTEMPTS,
    VALID_ACCEPTANCE_STATUSES,
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PlatformWorkItem
# ---------------------------------------------------------------------------

class TestPlatformWorkItem:
    def test_valid_construction(self) -> None:
        wi = _make_work_item()
        assert wi.source_issue_number == 96
        assert wi.repository == "dddd2024/reverse-agent"
        assert wi.risk_tier == "R2"

    def test_path_normalization_strips_leading_dot_slash(self) -> None:
        wi = PlatformWorkItem(
            source_issue_number=1,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("./reverse_agent/platform_v1/foo.py", "reverse_agent\\platform_v1\\bar.py"),
            forbidden_operations=(),
            acceptance_criteria=(),
        )
        assert wi.allowed_paths == (
            "reverse_agent/platform_v1/foo.py",
            "reverse_agent/platform_v1/bar.py",
        )

    def test_path_deduplication_preserves_order(self) -> None:
        wi = PlatformWorkItem(
            source_issue_number=1,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("a.py", "b.py", "a.py"),
            forbidden_operations=(),
            acceptance_criteria=(),
        )
        assert wi.allowed_paths == ("a.py", "b.py")

    @pytest.mark.parametrize("broad", ["**", "*", ".", "./", "/", "", "./**", "*.*"])
    def test_broad_path_rejected(self, broad: str) -> None:
        with pytest.raises(ValueError, match="broad_path_rejected"):
            PlatformWorkItem(
                source_issue_number=1,
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                allowed_paths=(broad,),
                forbidden_operations=(),
                acceptance_criteria=(),
            )

    def test_empty_path_scope_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty_path_scope_rejected"):
            PlatformWorkItem(
                source_issue_number=1,
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                allowed_paths=(),
                forbidden_operations=(),
                acceptance_criteria=(),
            )

    @pytest.mark.parametrize("tier", ["R3", "R4", "R5", "RX"])
    def test_risk_tier_R3_or_higher_rejected(self, tier: str) -> None:
        with pytest.raises(ValueError, match="risk_tier_R3_or_higher_rejected"):
            _make_work_item(risk_tier=tier)

    def test_invalid_base_sha_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_base_sha"):
            _make_work_item(base_sha="not-a-sha")

    def test_short_base_sha_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_base_sha"):
            _make_work_item(base_sha="705a0bfd")

    def test_invalid_repository_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_repository"):
            _make_work_item(repository="not-a-repo")

    def test_non_positive_issue_number_rejected(self) -> None:
        with pytest.raises(ValueError, match="source_issue_number_must_be_positive_int"):
            _make_work_item(source_issue_number=0)

    def test_execution_id_is_deterministic(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.execution_id == wi2.execution_id
        assert wi1.execution_id == f"exec-issue-96-{VALID_BASE_SHA[:12]}"

    def test_branch_name_uses_target_branch_when_set(self) -> None:
        wi = _make_work_item(target_branch="agent/some-branch")
        assert wi.branch_name == "agent/some-branch"

    def test_branch_name_derived_when_target_branch_empty(self) -> None:
        wi = PlatformWorkItem(
            source_issue_number=42,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("a.py",),
            forbidden_operations=(),
            acceptance_criteria=(),
        )
        assert wi.branch_name == "agent/work-item-42"

    def test_pr_marker_is_deterministic(self) -> None:
        wi = _make_work_item()
        assert wi.pr_marker == f"pr-marker-issue-96-{VALID_BASE_SHA[:12]}"

    def test_digest_is_deterministic(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.digest == wi2.digest
        assert len(wi1.digest) == 64

    def test_digest_changes_when_path_scope_changes(self) -> None:
        wi1 = _make_work_item(allowed_paths=("a.py",))
        wi2 = _make_work_item(allowed_paths=("b.py",))
        assert wi1.digest != wi2.digest

    def test_from_mapping_roundtrip(self) -> None:
        wi = _make_work_item()
        data = {
            "source_issue_number": wi.source_issue_number,
            "repository": wi.repository,
            "base_sha": wi.base_sha,
            "allowed_paths": list(wi.allowed_paths),
            "forbidden_operations": list(wi.forbidden_operations),
            "acceptance_criteria": list(wi.acceptance_criteria),
            "risk_tier": wi.risk_tier,
            "target_branch": wi.target_branch,
        }
        wi2 = PlatformWorkItem.from_mapping(data)
        assert wi2.digest == wi.digest
        assert wi2.execution_id == wi.execution_id


# ---------------------------------------------------------------------------
# ExecutionBinding
# ---------------------------------------------------------------------------

class TestExecutionBinding:
    def test_default_attempt_is_one(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item())
        assert binding.attempt == 1
        assert binding.is_retry is False

    def test_attempt_two_is_retry(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=2)
        assert binding.is_retry is True

    def test_attempt_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_attempt"):
            ExecutionBinding(work_item=_make_work_item(), attempt=0)

    def test_attempt_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_attempt"):
            ExecutionBinding(work_item=_make_work_item(), attempt=-1)

    def test_attempt_exceeds_max_rejected(self) -> None:
        with pytest.raises(ValueError, match="max_attempts_exceeded"):
            ExecutionBinding(work_item=_make_work_item(), attempt=MAX_ATTEMPTS + 1)

    def test_next_attempt_increments(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=1)
        next_binding = binding.next_attempt()
        assert next_binding.attempt == 2
        assert next_binding.is_retry is True

    def test_next_attempt_exhausted_raises(self) -> None:
        binding = ExecutionBinding(work_item=_make_work_item(), attempt=MAX_ATTEMPTS)
        with pytest.raises(ValueError, match="retry_limit_exceeded"):
            binding.next_attempt()

    def test_third_attempt_rejected(self) -> None:
        # MAX_ATTEMPTS is 2, so attempt 3 must be rejected
        assert MAX_ATTEMPTS == 2
        with pytest.raises(ValueError, match="max_attempts_exceeded"):
            ExecutionBinding(work_item=_make_work_item(), attempt=3)

    def test_execution_id_matches_work_item(self) -> None:
        wi = _make_work_item()
        binding = ExecutionBinding(work_item=wi)
        assert binding.execution_id == wi.execution_id
        assert binding.branch_name == wi.branch_name
        assert binding.pr_marker == wi.pr_marker


# ---------------------------------------------------------------------------
# ExecutionEvidence
# ---------------------------------------------------------------------------

class TestExecutionEvidence:
    def test_default_evidence(self) -> None:
        evidence = ExecutionEvidence(execution_id="exec-1")
        assert evidence.changed_paths == ()
        assert evidence.test_results == {}
        assert evidence.git_diff_check_passed is False
        assert evidence.agent_completion_claim == ""
        assert evidence.ci_checks == ()
        assert evidence.tests_passed is False
        assert evidence.ci_passed is False

    def test_tests_passed_reads_passed_key(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            test_results={"passed": True, "total": 10, "failed": 0},
        )
        assert evidence.tests_passed is True

    def test_tests_passed_false_when_missing(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            test_results={"total": 10},
        )
        assert evidence.tests_passed is False

    def test_ci_passed_all_success(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            ci_checks=(
                {"name": "CI", "conclusion": "SUCCESS"},
                {"name": "Decision Preflight", "conclusion": "SUCCESS"},
            ),
        )
        assert evidence.ci_passed is True

    def test_ci_passed_false_when_any_failure(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            ci_checks=(
                {"name": "CI", "conclusion": "SUCCESS"},
                {"name": "State Gate", "conclusion": "FAILURE"},
            ),
        )
        assert evidence.ci_passed is False

    def test_ci_passed_false_when_empty(self) -> None:
        evidence = ExecutionEvidence(execution_id="exec-1", ci_checks=())
        assert evidence.ci_passed is False

    def test_ci_passed_accepts_status_field(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            ci_checks=({"name": "CI", "status": "SUCCESS"},),
        )
        assert evidence.ci_passed is True

    def test_from_mapping_roundtrip(self) -> None:
        data = {
            "execution_id": "exec-1",
            "changed_paths": ["a.py", "b.py"],
            "test_results": {"passed": True},
            "git_diff_check_passed": True,
            "agent_completion_claim": "done",
            "ci_checks": [{"name": "CI", "conclusion": "SUCCESS"}],
            "collected_at": "2026-08-02T00:00:00Z",
        }
        evidence = ExecutionEvidence.from_mapping(data)
        assert evidence.execution_id == "exec-1"
        assert evidence.changed_paths == ("a.py", "b.py")
        assert evidence.tests_passed is True
        assert evidence.git_diff_check_passed is True
        assert evidence.ci_passed is True


# ---------------------------------------------------------------------------
# PlatformAcceptanceResult
# ---------------------------------------------------------------------------

class TestPlatformAcceptanceResult:
    def test_accepted_status(self) -> None:
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("all_checks_passed",),
        )
        assert result.accepted is True

    def test_rework_required_status(self) -> None:
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="REWORK_REQUIRED",
            reasons=("tests_failed",),
        )
        assert result.accepted is False

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_acceptance_status"):
            PlatformAcceptanceResult(execution_id="exec-1", status="UNKNOWN")

    def test_to_mapping_serializes_evidence(self) -> None:
        evidence = ExecutionEvidence(
            execution_id="exec-1",
            changed_paths=("a.py",),
            test_results={"passed": True},
            git_diff_check_passed=True,
            ci_checks=({"name": "CI", "conclusion": "SUCCESS"},),
        )
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("ok",),
            evidence=evidence,
        )
        mapping = result.to_mapping()
        assert mapping["status"] == "ACCEPTED"
        assert mapping["evidence"]["tests_passed"] is True
        assert mapping["evidence"]["git_diff_check_passed"] is True
        assert mapping["evidence"]["ci_passed"] is True

    def test_to_mapping_handles_none_evidence(self) -> None:
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="FAILED_TERMINAL",
            reasons=("policy_failed",),
        )
        mapping = result.to_mapping()
        assert mapping["evidence"] is None

    def test_all_valid_acceptance_statuses_accepted(self) -> None:
        for status in VALID_ACCEPTANCE_STATUSES:
            result = PlatformAcceptanceResult(execution_id="exec-1", status=status)
            assert result.status == status

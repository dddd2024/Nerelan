"""Tests for the Platform V1 core contracts.

Covers:
- PlatformWorkItem normalization, validation, and digest determinism
- ExecutionBinding attempt limits
- ExecutionEvidence immutability and derived flags
- ExecutionEvidence binding validation
- PlatformAcceptanceResult status whitelist and live_ready property
"""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import subprocess
import textwrap

import pytest

from reverse_agent.platform_v1.contracts import (
    MAX_ATTEMPTS,
    VALID_ACCEPTANCE_STATUSES,
    EvidenceBindingError,
    ExecutionBinding,
    ExecutionEvidence,
    PlatformAcceptanceResult,
    PlatformWorkItem,
    _LIVE_FACTORY_TOKEN,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"
VALID_ISSUE_BODY_DIGEST = "a" * 64  # F25: SHA-256, 64 hex chars


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
        "risk_tier": "R2",
        "target_branch": "agent/platform-v1-openhands-codex-acp",
    }
    defaults.update(overrides)
    return PlatformWorkItem(**defaults)


def _make_evidence(**overrides) -> ExecutionEvidence:
    defaults = {
        "execution_id": "exec-1",
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "head_sha": VALID_HEAD_SHA,
        "pr_number": 97,
        "required_workflows": ("CI",),
        "changed_paths": ("reverse_agent/platform_v1/__init__.py",),
        "test_results": {"passed": True},
        "git_diff_check_passed": True,
        "agent_completion_claim": "",
        "ci_checks": ({"name": "CI", "status": "completed", "conclusion": "success"},),
        "collected_at": "",
    }
    defaults.update(overrides)
    # F27: live mode requires the module-private trusted factory token.
    if defaults.get("collection_mode") == "live":
        defaults["_factory_token"] = _LIVE_FACTORY_TOKEN
    return ExecutionEvidence(**defaults)


# ---------------------------------------------------------------------------
# PlatformWorkItem
# ---------------------------------------------------------------------------

class TestPlatformWorkItem:
    def test_valid_construction(self) -> None:
        wi = _make_work_item()
        assert wi.source_issue_number == 96
        assert wi.repository == "dddd2024/reverse-agent"
        assert wi.risk_tier == "R2"
        assert wi.goal == "test goal"
        assert wi.required_checks == ("pytest",)
        assert wi.approved_issue_body_digest == VALID_ISSUE_BODY_DIGEST

    def test_R3_is_valid_at_construction(self) -> None:
        # R3 is now a recognized risk tier (valid at construction); it is
        # blocked later by the policy adapter as a blocked_approval.
        wi = _make_work_item(risk_tier="R3")
        assert wi.risk_tier == "R3"

    @pytest.mark.parametrize("tier", ["R4", "R5", "RX"])
    def test_invalid_risk_tier_rejected(self, tier: str) -> None:
        with pytest.raises(ValueError, match="invalid_risk_tier"):
            _make_work_item(risk_tier=tier)

    def test_path_normalization_strips_leading_dot_slash(self) -> None:
        wi = PlatformWorkItem(
            source_issue_number=1,
            repository="a/b",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("./reverse_agent/platform_v1/foo.py", "reverse_agent\\platform_v1\\bar.py"),
            forbidden_operations=(),
            acceptance_criteria=(),
            goal="g",
            required_checks=("pytest",),
            approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
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
            goal="g",
            required_checks=("pytest",),
            approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
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
                goal="g",
                required_checks=("pytest",),
                approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
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
                goal="g",
                required_checks=("pytest",),
                approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
            )

    def test_empty_goal_rejected(self) -> None:
        with pytest.raises(ValueError, match="goal_must_be_non_empty_string"):
            _make_work_item(goal="")

    def test_empty_required_checks_rejected(self) -> None:
        with pytest.raises(ValueError, match="required_checks_must_not_be_empty"):
            _make_work_item(required_checks=())

    def test_invalid_approved_issue_body_digest_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_approved_issue_body_digest"):
            _make_work_item(approved_issue_body_digest="not-a-digest")

    def test_short_approved_issue_body_digest_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid_approved_issue_body_digest"):
            _make_work_item(approved_issue_body_digest="a" * 39)

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
        # execution_id is now derived from the canonical digest, not base_sha
        assert wi1.execution_id == f"exec-issue-96-{wi1.digest[:12]}"

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
            goal="g",
            required_checks=("pytest",),
            approved_issue_body_digest=VALID_ISSUE_BODY_DIGEST,
        )
        assert wi.branch_name == "agent/work-item-42"

    def test_pr_marker_is_deterministic(self) -> None:
        wi = _make_work_item()
        # pr_marker is now derived from the canonical digest, not base_sha
        assert wi.pr_marker == f"pr-marker-issue-96-{wi.digest[:12]}"

    def test_digest_is_deterministic(self) -> None:
        wi1 = _make_work_item()
        wi2 = _make_work_item()
        assert wi1.digest == wi2.digest
        assert len(wi1.digest) == 64

    def test_digest_changes_when_path_scope_changes(self) -> None:
        wi1 = _make_work_item(allowed_paths=("a.py",))
        wi2 = _make_work_item(allowed_paths=("b.py",))
        assert wi1.digest != wi2.digest

    def test_material_field_change_changes_identity(self) -> None:
        # Changing any materially meaningful field changes digest, execution_id,
        # and pr_marker — preventing collision with stale execution state.
        base = _make_work_item()

        for field, new_value in [
            ("goal", "different goal"),
            ("allowed_paths", ("some/other/path.py",)),
            ("acceptance_criteria", ("different criterion",)),
            ("required_checks", ("different-check",)),
            ("risk_tier", "R0"),
            ("target_branch", "agent/other-branch"),
            ("approved_issue_body_digest", "b" * 64),
            ("base_sha", "0" * 40),
            ("source_issue_number", 97),
            ("repository", "other/repo"),
            ("forbidden_operations", ("force_push",)),
        ]:
            changed = _make_work_item(**{field: new_value})
            assert changed.digest != base.digest, f"digest must change for {field}"
            assert changed.execution_id != base.execution_id, f"execution_id must change for {field}"
            assert changed.pr_marker != base.pr_marker, f"pr_marker must change for {field}"

    def test_to_digest_payload_includes_material_fields(self) -> None:
        wi = _make_work_item()
        payload = wi.to_digest_payload()
        assert "goal" in payload
        assert "required_checks" in payload
        assert "approved_issue_body_digest" in payload
        assert payload["goal"] == "test goal"
        assert payload["required_checks"] == ["pytest"]
        assert payload["approved_issue_body_digest"] == VALID_ISSUE_BODY_DIGEST

    def test_from_mapping_roundtrip(self) -> None:
        wi = _make_work_item()
        data = {
            "source_issue_number": wi.source_issue_number,
            "repository": wi.repository,
            "base_sha": wi.base_sha,
            "allowed_paths": list(wi.allowed_paths),
            "forbidden_operations": list(wi.forbidden_operations),
            "acceptance_criteria": list(wi.acceptance_criteria),
            "goal": wi.goal,
            "required_checks": list(wi.required_checks),
            "approved_issue_body_digest": wi.approved_issue_body_digest,
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
        # All binding fields are now required; defaults cannot be used.
        evidence = _make_evidence()
        assert evidence.changed_paths == ("reverse_agent/platform_v1/__init__.py",)
        assert evidence.test_results == {"passed": True}
        assert evidence.git_diff_check_passed is True
        assert evidence.agent_completion_claim == ""
        assert evidence.ci_checks == ({"name": "CI", "status": "completed", "conclusion": "success"},)
        assert evidence.tests_passed is True
        assert evidence.ci_passed is True
        assert evidence.collection_mode == "fixture"
        assert evidence.provenance == "caller_asserted"
        assert evidence.is_live is False

    def test_evidence_requires_repository(self) -> None:
        with pytest.raises(ValueError, match="invalid_repository"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="no-slash",
                base_sha=VALID_BASE_SHA,
                head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=("CI",),
            )

    def test_evidence_requires_valid_base_sha(self) -> None:
        with pytest.raises(ValueError, match="invalid_base_sha"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="a/b",
                base_sha="not-a-sha",
                head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=("CI",),
            )

    def test_evidence_requires_valid_head_sha(self) -> None:
        with pytest.raises(ValueError, match="invalid_head_sha"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                head_sha="not-a-sha",
                pr_number=97,
                required_workflows=("CI",),
            )

    def test_evidence_requires_positive_pr_number(self) -> None:
        with pytest.raises(ValueError, match="invalid_pr_number"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                head_sha=VALID_HEAD_SHA,
                pr_number=0,
                required_workflows=("CI",),
            )

    def test_evidence_rejects_invalid_collection_mode(self) -> None:
        with pytest.raises(ValueError, match="invalid_collection_mode"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="a/b",
                base_sha=VALID_BASE_SHA,
                head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=("CI",),
                collection_mode="bogus",
            )

    def test_tests_passed_reads_passed_key(self) -> None:
        evidence = _make_evidence(
            test_results={"passed": True, "total": 10, "failed": 0},
        )
        assert evidence.tests_passed is True

    def test_tests_passed_false_when_missing(self) -> None:
        evidence = _make_evidence(test_results={"total": 10})
        assert evidence.tests_passed is False

    def test_ci_passed_all_success(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI", "Decision Preflight"),
            ci_checks=(
                {"name": "CI", "status": "completed", "conclusion": "success"},
                {"name": "Decision Preflight", "status": "completed", "conclusion": "success"},
            ),
        )
        assert evidence.ci_passed is True

    def test_ci_passed_false_when_any_failure(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI", "State Gate"),
            ci_checks=(
                {"name": "CI", "status": "completed", "conclusion": "success"},
                {"name": "State Gate", "status": "completed", "conclusion": "FAILURE"},
            ),
        )
        assert evidence.ci_passed is False

    def test_ci_passed_false_when_empty(self) -> None:
        evidence = _make_evidence(ci_checks=())
        assert evidence.ci_passed is False

    def test_ci_passed_false_when_required_workflow_missing(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI", "State Gate"),
            ci_checks=({"name": "CI", "status": "completed", "conclusion": "success"},),
        )
        assert evidence.ci_passed is False

    def test_ci_passed_false_on_duplicate_workflow(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI",),
            ci_checks=(
                {"name": "CI", "status": "completed", "conclusion": "success"},
                {"name": "CI", "status": "completed", "conclusion": "success"},
            ),
        )
        assert evidence.ci_passed is False

    def test_ci_passed_requires_both_status_and_conclusion(self) -> None:
        # F24: Both status=completed AND conclusion=success are required.
        # status=SUCCESS alone (without conclusion) must fail.
        evidence = _make_evidence(
            required_workflows=("CI",),
            ci_checks=({"name": "CI", "status": "SUCCESS"},),
        )
        assert evidence.ci_passed is False

    def test_ci_passed_rejects_empty_conclusion(self) -> None:
        # F24: completed run with empty conclusion never passes.
        evidence = _make_evidence(
            required_workflows=("CI",),
            ci_checks=({"name": "CI", "status": "completed", "conclusion": ""},),
        )
        assert evidence.ci_passed is False

    def test_is_live_true_only_for_live_mode(self) -> None:
        live = _make_evidence(collection_mode="live")
        fixture = _make_evidence(collection_mode="fixture")
        assert live.is_live is True
        assert fixture.is_live is False

    def test_from_mapping_roundtrip(self) -> None:
        data = {
            "execution_id": "exec-1",
            "repository": "dddd2024/reverse-agent",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
            "changed_paths": ["a.py", "b.py"],
            "test_results": {"passed": True},
            "git_diff_check_passed": True,
            "agent_completion_claim": "done",
            "ci_checks": [{"name": "CI", "status": "completed", "conclusion": "success"}],
            "collected_at": "2026-08-02T00:00:00Z",
            "collection_mode": "fixture",
            "provenance": "caller_asserted",
        }
        evidence = ExecutionEvidence.from_mapping(data)
        assert evidence.execution_id == "exec-1"
        assert evidence.repository == "dddd2024/reverse-agent"
        assert evidence.base_sha == VALID_BASE_SHA
        assert evidence.head_sha == VALID_HEAD_SHA
        assert evidence.pr_number == 97
        assert evidence.required_workflows == ("CI",)
        assert evidence.changed_paths == ("a.py", "b.py")
        assert evidence.tests_passed is True
        assert evidence.git_diff_check_passed is True
        assert evidence.ci_passed is True


# ---------------------------------------------------------------------------
# ExecutionEvidence.validate_binding
# ---------------------------------------------------------------------------

class TestValidateBinding:
    def test_valid_binding_passes(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        # Should not raise
        evidence.validate_binding(wi)

    def test_mismatched_execution_id_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id="exec-different",
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError, match="execution_id_mismatch"):
            evidence.validate_binding(wi)

    def test_mismatched_repository_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository="other/repo",
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError, match="repository_mismatch"):
            evidence.validate_binding(wi)

    def test_mismatched_base_sha_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha="0" * 40,
        )
        with pytest.raises(EvidenceBindingError, match="base_sha_mismatch"):
            evidence.validate_binding(wi)

    def test_evidence_binding_error_carries_code_and_detail(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id="exec-different",
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError) as exc_info:
            evidence.validate_binding(wi)
        assert exc_info.value.code == "execution_id_mismatch"
        assert "exec-different" in exc_info.value.detail
        assert wi.execution_id in exc_info.value.detail


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

    def test_live_ready_true_only_when_accepted_and_live_evidence(self) -> None:
        live_evidence = _make_evidence(collection_mode="live")
        fixture_evidence = _make_evidence(collection_mode="fixture")

        accepted_live = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("ok",),
            evidence=live_evidence,
        )
        accepted_fixture = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("ok",),
            evidence=fixture_evidence,
        )
        rework_live = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="REWORK_REQUIRED",
            reasons=("tests_failed",),
            evidence=live_evidence,
        )
        accepted_no_evidence = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("ok",),
        )

        assert accepted_live.live_ready is True
        assert accepted_fixture.live_ready is False
        assert rework_live.live_ready is False
        assert accepted_no_evidence.live_ready is False

    def test_to_mapping_serializes_evidence(self) -> None:
        evidence = _make_evidence()
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="ACCEPTED",
            reasons=("ok",),
            evidence=evidence,
        )
        mapping = result.to_mapping()
        assert mapping["status"] == "ACCEPTED"
        assert mapping["live_ready"] is False  # fixture evidence
        assert mapping["evidence"]["tests_passed"] is True
        assert mapping["evidence"]["git_diff_check_passed"] is True
        assert mapping["evidence"]["ci_passed"] is True
        assert mapping["evidence"]["collection_mode"] == "fixture"
        assert mapping["evidence"]["provenance"] == "caller_asserted"

    def test_to_mapping_handles_none_evidence(self) -> None:
        result = PlatformAcceptanceResult(
            execution_id="exec-1",
            status="FAILED_TERMINAL",
            reasons=("policy_failed",),
        )
        mapping = result.to_mapping()
        assert mapping["evidence"] is None
        assert mapping["live_ready"] is False

    def test_all_valid_acceptance_statuses_accepted(self) -> None:
        for status in VALID_ACCEPTANCE_STATUSES:
            result = PlatformAcceptanceResult(execution_id="exec-1", status=status)
            assert result.status == status


# ---------------------------------------------------------------------------
# F9: Fixture/Live evidence boundary
# ---------------------------------------------------------------------------

class TestFixtureLiveBoundary:
    """F9: from_mapping always forces fixture/caller_asserted.

    Even if the caller supplies collection_mode=live or trusted provenance,
    the result is always fixture. Only create_live can produce live evidence.
    """

    def test_from_mapping_forces_fixture_even_when_caller_supplies_live(self) -> None:
        data = {
            "execution_id": "exec-1",
            "repository": "dddd2024/reverse-agent",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
            "collection_mode": "live",
            "provenance": "trusted_git_github_collector",
        }
        evidence = ExecutionEvidence.from_mapping(data)
        assert evidence.collection_mode == "fixture"
        assert evidence.provenance == "caller_asserted"
        assert evidence.is_live is False
        assert evidence.live_ready is False

    def test_from_mapping_forces_caller_asserted_even_with_trusted_provenance(self) -> None:
        data = {
            "execution_id": "exec-1",
            "repository": "dddd2024/reverse-agent",
            "base_sha": VALID_BASE_SHA,
            "head_sha": VALID_HEAD_SHA,
            "pr_number": 97,
            "required_workflows": ["CI"],
            "provenance": "trusted_git_github_collector",
        }
        evidence = ExecutionEvidence.from_mapping(data)
        assert evidence.provenance == "caller_asserted"
        assert evidence.is_live is False

    def test_create_live_produces_fixture_evidence_f27(self) -> None:
        """F27: create_live is deprecated and produces fixture evidence only.

        Only evidence_adapter._create_trusted_evidence can produce live
        evidence by passing the module-private _LIVE_FACTORY_TOKEN.
        """
        evidence = ExecutionEvidence.create_live(
            execution_id="exec-1",
            repository="dddd2024/reverse-agent",
            base_sha=VALID_BASE_SHA,
            head_sha=VALID_HEAD_SHA,
            pr_number=97,
            required_workflows=("CI",),
        )
        assert evidence.collection_mode == "fixture"
        assert evidence.provenance == "caller_asserted"
        assert evidence.is_live is False
        assert evidence.live_ready is False

    def test_fixture_evidence_live_ready_is_false(self) -> None:
        evidence = _make_evidence(collection_mode="fixture")
        assert evidence.live_ready is False
        assert evidence.is_live is False

    def test_live_evidence_live_ready_is_true(self) -> None:
        evidence = _make_evidence(collection_mode="live")
        assert evidence.live_ready is True
        assert evidence.is_live is True


# ---------------------------------------------------------------------------
# F12: Required workflow set must match exactly (no subset)
# ---------------------------------------------------------------------------

class TestRequiredWorkflowSetMatching:
    """F12: The observed workflow set must match the required set exactly.

    A subset of required workflows is rejected. A superset is also rejected.
    """

    def test_workflow_subset_rejected(self) -> None:
        # Required: CI + Decision Preflight; Observed: only CI
        evidence = _make_evidence(
            required_workflows=("CI", "Decision Preflight"),
            ci_checks=({"name": "CI", "conclusion": "SUCCESS"},),
        )
        assert evidence.ci_passed is False

    def test_workflow_superset_rejected(self) -> None:
        # Required: CI; Observed: CI + extra
        evidence = _make_evidence(
            required_workflows=("CI",),
            ci_checks=(
                {"name": "CI", "conclusion": "SUCCESS"},
                {"name": "Extra Workflow", "conclusion": "SUCCESS"},
            ),
        )
        assert evidence.ci_passed is False

    def test_workflow_exact_match_accepted(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI", "Decision Preflight"),
            ci_checks=(
                {"name": "CI", "status": "completed", "conclusion": "success"},
                {"name": "Decision Preflight", "status": "completed", "conclusion": "success"},
            ),
        )
        assert evidence.ci_passed is True

    def test_multi_word_workflow_names_preserved(self) -> None:
        evidence = _make_evidence(
            required_workflows=("CI", "Decision Preflight", "State Gate (push)"),
            ci_checks=(
                {"name": "CI", "status": "completed", "conclusion": "success"},
                {"name": "Decision Preflight", "status": "completed", "conclusion": "success"},
                {"name": "State Gate (push)", "status": "completed", "conclusion": "success"},
            ),
        )
        assert evidence.ci_passed is True


# ---------------------------------------------------------------------------
# F11: validate_exact_binding
# ---------------------------------------------------------------------------

class TestValidateExactBinding:
    """F11: The live path requires mandatory exact binding."""

    def test_valid_exact_binding_passes(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
            head_sha=VALID_HEAD_SHA,
            pr_number=97,
        )
        evidence.validate_exact_binding(
            wi,
            expected_head_sha=VALID_HEAD_SHA,
            expected_pr_number=97,
            expected_branch=wi.target_branch,
            authority_digest=wi.digest,
        )

    def test_wrong_head_sha_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError, match="head_sha_mismatch"):
            evidence.validate_exact_binding(
                wi,
                expected_head_sha="b" * 40,
                expected_pr_number=97,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
            )

    def test_wrong_pr_number_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
            pr_number=97,
        )
        with pytest.raises(EvidenceBindingError, match="pr_number_mismatch"):
            evidence.validate_exact_binding(
                wi,
                expected_head_sha=VALID_HEAD_SHA,
                expected_pr_number=98,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
            )

    def test_wrong_branch_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError, match="branch_mismatch"):
            evidence.validate_exact_binding(
                wi,
                expected_head_sha=VALID_HEAD_SHA,
                expected_pr_number=97,
                expected_branch="agent/wrong-branch",
                authority_digest=wi.digest,
            )

    def test_wrong_authority_digest_rejected(self) -> None:
        wi = _make_work_item()
        evidence = _make_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
        )
        with pytest.raises(EvidenceBindingError, match="authority_digest_mismatch"):
            evidence.validate_exact_binding(
                wi,
                expected_head_sha=VALID_HEAD_SHA,
                expected_pr_number=97,
                expected_branch=wi.target_branch,
                authority_digest="b" * 64,
            )


# ---------------------------------------------------------------------------
# required_checks_as_workflows (F12)
# ---------------------------------------------------------------------------

class TestRequiredChecksAsWorkflows:
    """F12: Required workflows come from the Work Item's required_checks."""

    def test_returns_required_checks_as_tuple(self) -> None:
        wi = _make_work_item(required_checks=("CI", "Decision Preflight"))
        assert wi.required_checks_as_workflows() == ("CI", "Decision Preflight")

    def test_returns_empty_tuple_when_no_checks(self) -> None:
        with pytest.raises(ValueError, match="required_checks_must_not_be_empty"):
            _make_work_item(required_checks=())


# ---------------------------------------------------------------------------
# F17/F28: Active Bootstrap intent binds PR #112 and exact authority digests
# ---------------------------------------------------------------------------

class TestActiveMergeIntentV6:
    """The active intent binds PR #112 while preserving prior intents.

    The v1, v2, and v3 assertions remain intact, and the v4 archive must be
    the exact B0 active Intent blob.
    """

    @pytest.fixture(autouse=True)
    def _load_intents(self) -> None:
        import json
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        intents_dir = repo_root / "project_state" / "mainline_merge_intents"
        self._active_path = intents_dir / "active.json"
        self._archive_v1_path = intents_dir / "archive" / "pr97_v1.json"
        self._archive_v2_path = intents_dir / "archive" / "pr97_v2.json"
        self._archive_v3_path = intents_dir / "archive" / "pr97_v3.json"
        self._archive_v4_path = intents_dir / "archive" / "pr97_v4.json"
        self._archive_pr108_path = intents_dir / "archive" / "pr108_v1.json"
        self._archive_pr110_path = intents_dir / "archive" / "pr110_v1.json"
        self._archive_pr112_path = intents_dir / "archive" / "pr112_v1.json"
        self._archive_pr112_v2_path = intents_dir / "archive" / "pr112_v2.json"
        self._decision_path = repo_root / "project_state" / "decision_packet.md"
        self._command_plan_path = repo_root / "project_state" / "gates" / "command_plan.json"
        self._active = json.loads(self._active_path.read_text(encoding="utf-8"))
        self._archive_v1 = json.loads(self._archive_v1_path.read_text(encoding="utf-8"))
        self._archive_v2 = json.loads(self._archive_v2_path.read_text(encoding="utf-8"))
        self._archive_v3 = json.loads(self._archive_v3_path.read_text(encoding="utf-8"))
        self._archive_v4 = json.loads(self._archive_v4_path.read_text(encoding="utf-8"))
        self._archive_pr108 = json.loads(
            self._archive_pr108_path.read_text(encoding="utf-8")
        )
        self._archive_pr110 = json.loads(
            self._archive_pr110_path.read_text(encoding="utf-8")
        )
        self._archive_pr112 = json.loads(
            self._archive_pr112_path.read_text(encoding="utf-8")
        )
        self._archive_pr112_v2 = json.loads(
            self._archive_pr112_v2_path.read_text(encoding="utf-8")
        )

    def test_active_binds_source_pr_112(self) -> None:
        assert self._active["source_pr"] == 112

    def test_active_binds_bootstrap_decision_id(self) -> None:
        assert self._active["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_utf8_semantic_guard_v3"
        )

    def test_active_binds_bootstrap_decision_content_sha256(self) -> None:
        sha = self._active["decision_identity"]["decision_content_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)
        assert sha == hashlib.sha256(self._decision_path.read_bytes()).hexdigest()
        assert sha != self._archive_v3["decision_identity"]["decision_content_sha256"]

    def test_active_binds_bootstrap_command_plan_sha256(self) -> None:
        sha = self._active["command_plan_sha256"]
        assert isinstance(sha, str) and len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)
        assert sha == hashlib.sha256(self._command_plan_path.read_bytes()).hexdigest()
        assert sha != self._archive_v3["command_plan_sha256"]

    def test_active_binds_locked_base_sha(self) -> None:
        assert self._active["locked_base_sha"] == (
            "93984db182b7ee11b3ccb8795bb5fc3741205b92"
        )

    def test_active_binds_merge_method(self) -> None:
        assert self._active["allowed_merge_method"] == "merge"

    def test_active_binds_required_workflows(self) -> None:
        workflows = self._active["required_workflows"]
        assert "CI" in workflows
        assert "Decision Preflight" in workflows
        assert "State Gate (pull_request)" in workflows
        assert "State Gate (push)" in workflows

    def test_active_has_bounded_expiry(self) -> None:
        expires = self._active.get("expires_at", "")
        assert expires and expires.endswith("Z")

    def test_archive_v1_exists_and_preserves_v1_decision_id(self) -> None:
        assert self._archive_v1["decision_identity"]["decision_id"] == (
            "decision_20260802_platform_v1_openhands_codex_acp_v1"
        )

    def test_archive_v2_exists_and_preserves_v2_decision_id(self) -> None:
        assert self._archive_v2["decision_identity"]["decision_id"] == (
            "decision_20260802_issue98_platform_v1_trust_binding_rework_v2"
        )

    def test_archive_v3_exists_and_preserves_v3_decision_id(self) -> None:
        assert self._archive_v3["decision_identity"]["decision_id"] == (
            "decision_20260802_issue99_platform_v1_live_evidence_boundary_v3"
        )

    def test_archive_v3_preserves_v3_source_pr(self) -> None:
        assert self._archive_v3["source_pr"] == 97

    def test_archive_v4_exists_and_preserves_v4_identity(self) -> None:
        assert self._archive_v4["source_pr"] == 97
        assert self._archive_v4["decision_identity"]["decision_id"] == (
            "decision_20260802_issue100_platform_v1_authority_collector_v4"
        )

    def test_archive_v4_is_exact_b0_active_blob(self) -> None:
        payload = self._archive_v4_path.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "1afd619ef90df7b01255d1cd16b483190f616df6"
        )

    def test_archive_pr108_preserves_bootstrap_v1_identity(self) -> None:
        assert self._archive_pr108["source_pr"] == 108
        assert self._archive_pr108["decision_identity"]["decision_id"] == (
            "decision_20260804_issue107_state_gate_bootstrap_pr108_v1"
        )
        assert self._archive_pr108["locked_base_sha"] == (
            "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
        )

    def test_archive_pr108_is_exact_b1_active_blob(self) -> None:
        payload = self._archive_pr108_path.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "32ca8e328e28467fcbe1857b7d300152fc89bdf4"
        )

    def test_archive_pr110_preserves_bootstrap_v2_identity(self) -> None:
        assert self._archive_pr110["source_pr"] == 110
        assert self._archive_pr110["decision_identity"]["decision_id"] == (
            "decision_20260804_issue109_pr110_bootstrap_test_rebind_v1"
        )
        assert self._archive_pr110["locked_base_sha"] == (
            "4aacd7f614342f5ca123b2afccdb9a49df886775"
        )

    def test_archive_pr110_is_exact_b2_active_blob(self) -> None:
        payload = self._archive_pr110_path.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "bb7ce4c1c61a88e63e0bdc14e0ce2fa4967fc842"
        )

    def test_archive_pr112_v1_preserves_rejected_identity(self) -> None:
        assert self._archive_pr112["source_pr"] == 112
        assert self._archive_pr112["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_bootstrap_v13_retry_v1"
        )
        assert self._archive_pr112["locked_base_sha"] == (
            "93984db182b7ee11b3ccb8795bb5fc3741205b92"
        )

    def test_archive_pr112_v1_is_exact_rejected_active_blob(self) -> None:
        payload = self._archive_pr112_path.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "639581296b8dfd8038871010f99aa68401568353"
        )

    def test_archive_pr112_v2_preserves_rejected_identity(self) -> None:
        assert self._archive_pr112_v2["source_pr"] == 112
        assert self._archive_pr112_v2["decision_identity"]["decision_id"] == (
            "decision_20260804_issue111_pr112_candidate_test_semantic_guard_v2"
        )
        assert self._archive_pr112_v2["locked_base_sha"] == (
            "93984db182b7ee11b3ccb8795bb5fc3741205b92"
        )

    def test_archive_pr112_v2_is_exact_rejected_active_blob(self) -> None:
        payload = self._archive_pr112_v2_path.read_bytes()
        header = f"blob {len(payload)}\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "770f19faba9e0f040656341beec0089ca87d3545"
        )


# ---------------------------------------------------------------------------
# PR112 v2: semantic-body guard adversarial contract
# ---------------------------------------------------------------------------

SEMANTIC_H0 = "ff7dd9091a48c5c2fad315812e672d5089824d09"
SEMANTIC_B3 = "b" * 40
SEMANTIC_PATHS = (
    "tests/platform_v1/test_authority_adapter.py",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py",
)


def _workflow_semantic_guard():
    workflow = (
        Path(__file__).resolve().parents[2] / ".github" / "workflows" / "state-gate.yml"
    ).read_text(encoding="utf-8")
    inline = workflow.split("python - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]
    module = ast.parse(textwrap.dedent(inline))
    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "validate_semantic_test_sources"
    )
    namespace = {
        "ast": ast,
        "copy": copy,
        "semantic_test_paths": SEMANTIC_PATHS,
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<trusted-guard>", "exec"), namespace)
    return namespace["validate_semantic_test_sources"]


def _semantic_h0_sources() -> dict[str, str]:
    return {
        path: subprocess.check_output(
            ["git", "show", f"{SEMANTIC_H0}:{path}"],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
        )
        for path in SEMANTIC_PATHS
    }


def _module_assignment(tree: ast.Module, name: str) -> ast.Assign:
    return next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    )


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    return next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name
    )


def _method(owner: ast.ClassDef, name: str) -> ast.FunctionDef:
    return next(
        node for node in owner.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _authorized_v14_sources(h0_sources: dict[str, str]) -> dict[str, str]:
    trees = {path: ast.parse(source) for path, source in h0_sources.items()}

    authority = trees[SEMANTIC_PATHS[0]]
    _module_assignment(authority, "BASE").value = ast.Constant(SEMANTIC_B3)

    merge = trees[SEMANTIC_PATHS[2]]
    _module_assignment(merge, "EXPECTED_ACTIVE_BASE_SHA").value = ast.Constant(SEMANTIC_B3)
    _module_assignment(merge, "EXPECTED_ACTIVE_DECISION_ID_PR106").value = ast.Constant(
        "decision_20260804_restore_path_a_state_gate_current_main_v14"
    )
    insert_at = next(
        index for index, node in enumerate(merge.body)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    )
    additions = ast.parse('''
PR106_HISTORICAL_BASE_SHA = "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
ARCHIVE_PR106_V11R2_PATH = INTENTS_DIR / "archive" / "pr106_v11r2.json"
PR106_V11R2_ACTIVE_COMMIT = "ff7dd9091a48c5c2fad315812e672d5089824d09"
''').body
    merge.body[insert_at:insert_at] = additions
    for class_name, method_name in (
        ("TestArchivedPr106V3Intent", "test_archive_pr106_v3_preserves_locked_base_sha"),
        ("TestArchivedPr106V4Intent", "test_archive_pr106_v4_preserves_locked_base_sha"),
    ):
        function = _method(_class(merge, class_name), method_name)
        target = next(
            node for node in ast.walk(function)
            if isinstance(node, ast.Name) and node.id == "EXPECTED_ACTIVE_BASE_SHA"
        )
        target.id = "PR106_HISTORICAL_BASE_SHA"
    merge.body.append(ast.parse('''
class TestArchivedPr106V11r2Intent:
    def test_archive_pr106_v11r2_file_exists(self) -> None:
        assert ARCHIVE_PR106_V11R2_PATH.exists()

    def test_archive_pr106_v11r2_is_exact_h0_active(self) -> None:
        payload = ARCHIVE_PR106_V11R2_PATH.read_bytes()
        original = _committed_blob(
            "project_state/mainline_merge_intents/active.json",
            ref=PR106_V11R2_ACTIVE_COMMIT,
        )
        assert payload == original

    def test_archive_pr106_v11r2_has_exact_git_blob(self) -> None:
        payload = ARCHIVE_PR106_V11R2_PATH.read_bytes()
        header = f"blob {len(payload)}\\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "27b0a28c0b227df07dbc6829057d04875dc930ac"
        )

    def test_archive_pr106_v11r2_preserves_identity_and_base(self) -> None:
        data = _load_json(ARCHIVE_PR106_V11R2_PATH)
        assert data["source_pr"] == 106
        assert data["decision_identity"]["decision_id"] == (
            "decision_20260804_restore_path_a_state_gate_current_main_v11r2"
        )
        assert data["locked_base_sha"] == PR106_HISTORICAL_BASE_SHA
''').body[0])

    contracts = trees[SEMANTIC_PATHS[1]]
    active_class = _class(contracts, "TestActiveMergeIntentV5")
    fixture = _method(active_class, "_load_intents")
    fixture.body.extend(ast.parse('''
self._archive_v11r2_pr106_path = intents_dir / "archive" / "pr106_v11r2.json"
self._archive_v11r2_pr106 = json.loads(
    self._archive_v11r2_pr106_path.read_text(encoding="utf-8")
)
''').body)
    decision_test = _method(active_class, "test_active_binds_v11r1_decision_id")
    decision_literal = next(
        node for node in ast.walk(decision_test)
        if isinstance(node, ast.Constant)
        and node.value == "decision_20260804_restore_path_a_state_gate_current_main_v11r2"
    )
    decision_literal.value = "decision_20260804_restore_path_a_state_gate_current_main_v14"
    base_test = _method(active_class, "test_active_binds_locked_base_sha")
    base_literal = next(
        node for node in ast.walk(base_test)
        if isinstance(node, ast.Constant)
        and node.value == "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
    )
    base_literal.value = SEMANTIC_B3
    active_class.body.extend(ast.parse('''
class _Holder:
    def test_archive_pr106_v11r2_is_exact_h0_active(self) -> None:
        payload = self._archive_v11r2_pr106_path.read_bytes()
        original = subprocess.check_output(
            [
                "git", "cat-file", "blob",
                "ff7dd9091a48c5c2fad315812e672d5089824d09:project_state/mainline_merge_intents/active.json",
            ],
            cwd=self._repo_root,
        )
        assert payload == original
        header = f"blob {len(payload)}\\0".encode("ascii")
        assert hashlib.sha1(header + payload).hexdigest() == (
            "27b0a28c0b227df07dbc6829057d04875dc930ac"
        )

    def test_archive_pr106_v11r2_preserves_identity_and_base(self) -> None:
        assert self._archive_v11r2_pr106["source_pr"] == 106
        assert self._archive_v11r2_pr106["decision_identity"]["decision_id"] == (
            "decision_20260804_restore_path_a_state_gate_current_main_v11r2"
        )
        assert self._archive_v11r2_pr106["locked_base_sha"] == (
            "fa4f240f7dffff78cdb182ce8655c2e2d7cb241f"
        )
''').body[0].body)

    return {path: ast.unparse(tree) for path, tree in trees.items()}


def _mutate_semantic_candidate(sources: dict[str, str], case: str) -> dict[str, str]:
    trees = {path: ast.parse(source) for path, source in sources.items()}
    authority = trees[SEMANTIC_PATHS[0]]
    contracts = trees[SEMANTIC_PATHS[1]]
    merge = trees[SEMANTIC_PATHS[2]]
    first_test = next(
        node for node in authority.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )
    if case == "assert_true":
        first_test.body = [ast.Assert(test=ast.Constant(True))]
    elif case == "assert_removed":
        first_test.body = [node for node in first_test.body if not isinstance(node, ast.Assert)]
    elif case == "pass_body":
        first_test.body = [ast.Pass()]
    elif case == "fixed_return":
        helper = next(node for node in authority.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_"))
        helper.body = [ast.Return(value=ast.Constant(b"fixed"))]
    elif case == "marker_moved":
        owner = _class(merge, "TestRecentPR106IntentArchives")
        marked = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.decorator_list)
        other = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and not node.decorator_list)
        other.decorator_list = marked.decorator_list
        marked.decorator_list = []
    elif case == "pytestmark":
        contracts.body.append(ast.parse("pytestmark = pytest.mark.skip").body[0])
    elif case == "test_disabled":
        contracts.body.append(ast.parse("__test__ = False").body[0])
    elif case == "collection_hook":
        contracts.body.append(ast.parse("def pytest_collection_modifyitems(items):\n    items.clear()").body[0])
    elif case == "fixture_weakened":
        fixture = _method(_class(contracts, "TestActiveMergeIntentV5"), "_load_intents")
        fixture.body = [ast.Pass()]
    elif case == "fixture_decorator":
        fixture = _method(_class(contracts, "TestActiveMergeIntentV5"), "_load_intents")
        fixture.decorator_list = ast.parse("@pytest.fixture(scope='session')\ndef f():\n    pass").body[0].decorator_list
    elif case == "test_moved":
        source_class = _class(merge, "TestArchivedPr106V3Intent")
        moved = next(node for node in source_class.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"))
        source_class.body.remove(moved)
        _class(merge, "TestArchivedPr106V4Intent").body.append(moved)
    elif case == "duplicate_identity":
        owner = _class(merge, "TestArchivedPr106V3Intent")
        owner.body.append(copy.deepcopy(next(node for node in owner.body if isinstance(node, ast.FunctionDef))))
    elif case == "module_call":
        authority.body.append(ast.Expr(value=ast.Call(func=ast.Name(id="print"), args=[ast.Constant("x")], keywords=[])))
    elif case == "import_changed":
        authority.body.append(ast.Import(names=[ast.alias(name="socket")]))
    elif case == "unauthorized_test":
        authority.body.append(ast.parse("def test_unapproved():\n    assert True").body[0])
    elif case == "historical_active_alias":
        historical = _method(
            _class(merge, "TestArchivedPr106V3Intent"),
            "test_archive_pr106_v3_preserves_locked_base_sha",
        )
        next(
            node for node in ast.walk(historical)
            if isinstance(node, ast.Name) and node.id == "PR106_HISTORICAL_BASE_SHA"
        ).id = "EXPECTED_ACTIVE_BASE_SHA"
    else:
        raise AssertionError(case)
    return {path: ast.unparse(tree) for path, tree in trees.items()}


class TestStateGateSemanticBodyGuardV2:
    def test_exact_authorized_v14_ast_transform_passes(self) -> None:
        h0_sources = _semantic_h0_sources()
        _workflow_semantic_guard()(
            h0_sources, _authorized_v14_sources(h0_sources), SEMANTIC_B3
        )

    @pytest.mark.parametrize(
        "case",
        (
            "assert_true",
            "assert_removed",
            "pass_body",
            "fixed_return",
            "marker_moved",
            "pytestmark",
            "test_disabled",
            "collection_hook",
            "fixture_weakened",
            "fixture_decorator",
            "test_moved",
            "duplicate_identity",
            "module_call",
            "import_changed",
            "unauthorized_test",
            "historical_active_alias",
        ),
    )
    def test_adversarial_semantic_weakening_is_rejected(self, case: str) -> None:
        h0_sources = _semantic_h0_sources()
        authorized = _authorized_v14_sources(h0_sources)
        with pytest.raises(ValueError):
            _workflow_semantic_guard()(
                h0_sources,
                _mutate_semantic_candidate(authorized, case),
                SEMANTIC_B3,
            )

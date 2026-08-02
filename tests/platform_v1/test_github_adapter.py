"""Tests for the structured GitHub adapter (F13).

Covers:
- Multi-word workflow names are preserved exactly
- State Gate (push) and State Gate (pull_request) are distinguishable
- Wrong head SHA workflow observations are rejected
- Required workflow subsets are rejected
- Duplicate workflows are rejected
- Non-SUCCESS conclusions (PENDING, SKIPPED, CANCELLED, FAILURE, etc.) are rejected
- FakeGitHubAdapter filters by expected head SHA
- validate_workflow_observations blocking reasons
"""

from __future__ import annotations

import pytest

from reverse_agent.platform_v1.github_adapter import (
    FakeGitHubAdapter,
    GitHubAdapterError,
    WorkflowCheck,
    validate_workflow_observations,
)


VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"
WRONG_HEAD_SHA = "0" * 40

REQUIRED_WORKFLOWS = (
    "CI",
    "Decision Preflight",
    "State Gate (pull_request)",
    "State Gate (push)",
)


def _make_check(
    name: str,
    *,
    head_sha: str = VALID_HEAD_SHA,
    conclusion: str = "SUCCESS",
    status: str = "COMPLETED",
) -> WorkflowCheck:
    return WorkflowCheck(
        name=name,
        run_id="123",
        head_sha=head_sha,
        event="push",
        status=status,
        conclusion=conclusion,
    )


def _all_required_success(head_sha: str = VALID_HEAD_SHA) -> tuple[WorkflowCheck, ...]:
    return tuple(
        _make_check(name, head_sha=head_sha)
        for name in REQUIRED_WORKFLOWS
    )


# ---------------------------------------------------------------------------
# WorkflowCheck
# ---------------------------------------------------------------------------

class TestWorkflowCheck:
    def test_multi_word_workflow_name_preserved(self) -> None:
        check = _make_check("Decision Preflight")
        assert check.name == "Decision Preflight"

    def test_state_gate_push_preserved(self) -> None:
        check = _make_check("State Gate (push)")
        assert check.name == "State Gate (push)"

    def test_state_gate_pull_request_preserved(self) -> None:
        check = _make_check("State Gate (pull_request)")
        assert check.name == "State Gate (pull_request)"

    def test_to_dict_preserves_all_fields(self) -> None:
        check = WorkflowCheck(
            name="CI",
            run_id="42",
            head_sha=VALID_HEAD_SHA,
            event="pull_request",
            status="COMPLETED",
            conclusion="SUCCESS",
            workflow_id="wf-123",
        )
        d = check.to_dict()
        assert d["name"] == "CI"
        assert d["run_id"] == "42"
        assert d["head_sha"] == VALID_HEAD_SHA
        assert d["event"] == "pull_request"
        assert d["status"] == "COMPLETED"
        assert d["conclusion"] == "SUCCESS"
        assert d["workflow_id"] == "wf-123"

    def test_status_and_conclusion_uppercased(self) -> None:
        check = WorkflowCheck(
            name="CI",
            run_id="1",
            head_sha=VALID_HEAD_SHA,
            event="push",
            status="completed",
            conclusion="success",
        )
        assert check.status == "COMPLETED"
        assert check.conclusion == "SUCCESS"


# ---------------------------------------------------------------------------
# push vs pull_request State Gate distinguishable
# ---------------------------------------------------------------------------

class TestStateGateDisambiguation:
    """F13: State Gate (push) and State Gate (pull_request) are distinct."""

    def test_push_and_pull_request_are_different_names(self) -> None:
        push = _make_check("State Gate (push)")
        pr = _make_check("State Gate (pull_request)")
        assert push.name != pr.name

    def test_both_required_workflows_can_coexist(self) -> None:
        checks = _all_required_success()
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert blocking == []

    def test_only_push_without_pull_request_rejected(self) -> None:
        checks = tuple(
            _make_check(name)
            for name in REQUIRED_WORKFLOWS
            if name != "State Gate (pull_request)"
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)
        assert "State Gate (pull_request)" in ",".join(blocking)

    def test_only_pull_request_without_push_rejected(self) -> None:
        checks = tuple(
            _make_check(name)
            for name in REQUIRED_WORKFLOWS
            if name != "State Gate (push)"
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)
        assert "State Gate (push)" in ",".join(blocking)


# ---------------------------------------------------------------------------
# Wrong head SHA rejection
# ---------------------------------------------------------------------------

class TestWrongHeadRejection:
    """F13: Workflow observations with wrong head SHA are rejected."""

    def test_wrong_head_workflow_rejected(self) -> None:
        checks = tuple(
            _make_check(name, head_sha=WRONG_HEAD_SHA)
            for name in REQUIRED_WORKFLOWS
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("wrong_head_workflow" in b for b in blocking)

    def test_partial_wrong_head_rejected(self) -> None:
        checks = tuple(
            _make_check(name, head_sha=WRONG_HEAD_SHA if name == "CI" else VALID_HEAD_SHA)
            for name in REQUIRED_WORKFLOWS
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("wrong_head_workflow" in b for b in blocking)
        assert "CI" in ",".join(blocking)


# ---------------------------------------------------------------------------
# Required workflow subset rejection
# ---------------------------------------------------------------------------

class TestWorkflowSubsetRejection:
    """F12/F13: A subset of required workflows is rejected."""

    def test_subset_rejected(self) -> None:
        checks = tuple(
            _make_check(name)
            for name in REQUIRED_WORKFLOWS[:2]  # only CI + Decision Preflight
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)

    def test_superset_rejected(self) -> None:
        checks = _all_required_success() + (
            _make_check("Extra Workflow"),
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("extra_workflows" in b for b in blocking)

    def test_empty_observations_rejected(self) -> None:
        blocking, _ = validate_workflow_observations(
            (), REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert "no_workflow_observations" in blocking


# ---------------------------------------------------------------------------
# Duplicate workflow rejection
# ---------------------------------------------------------------------------

class TestDuplicateWorkflowRejection:
    def test_duplicate_workflow_rejected(self) -> None:
        checks = _all_required_success() + (
            _make_check("CI"),
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("duplicate_workflow" in b for b in blocking)


# ---------------------------------------------------------------------------
# Non-SUCCESS conclusion rejection
# ---------------------------------------------------------------------------

class TestNonSuccessConclusionRejection:
    """F13: Non-SUCCESS conclusions are rejected."""

    @pytest.mark.parametrize("conclusion", [
        "PENDING", "SKIPPED", "CANCELLED", "UNKNOWN", "FAILURE",
        "TIMED_OUT", "ACTION_REQUIRED", "STALE", "NEUTRAL",
    ])
    def test_rejected_conclusion_blocked(self, conclusion: str) -> None:
        checks = tuple(
            _make_check(name, conclusion=conclusion if name == "CI" else "SUCCESS")
            for name in REQUIRED_WORKFLOWS
        )
        blocking, _ = validate_workflow_observations(
            checks, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("workflow_not_success" in b for b in blocking)
        assert "CI" in ",".join(blocking)


# ---------------------------------------------------------------------------
# FakeGitHubAdapter
# ---------------------------------------------------------------------------

class TestFakeGitHubAdapter:
    def test_returns_configured_checks(self) -> None:
        checks = _all_required_success()
        adapter = FakeGitHubAdapter(checks=checks)
        result = adapter.get_pr_checks(97, "dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert len(result) == len(checks)

    def test_filters_by_expected_head_sha(self) -> None:
        checks = _all_required_success() + tuple(
            _make_check(name, head_sha=WRONG_HEAD_SHA)
            for name in REQUIRED_WORKFLOWS
        )
        adapter = FakeGitHubAdapter(checks=checks)
        result = adapter.get_pr_checks(97, "dddd2024/reverse-agent", VALID_HEAD_SHA)
        # Only the 4 checks with matching head_sha are returned
        assert len(result) == 4

    def test_raises_when_configured_to_fail(self) -> None:
        adapter = FakeGitHubAdapter(
            fail_with=GitHubAdapterError("gh_pr_checks_failed", "exit=1"),
        )
        with pytest.raises(GitHubAdapterError) as exc_info:
            adapter.get_pr_checks(97, "dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert exc_info.value.code == "gh_pr_checks_failed"

    def test_call_count_increments(self) -> None:
        adapter = FakeGitHubAdapter(checks=_all_required_success())
        assert adapter.call_count == 0
        adapter.get_pr_checks(97, "dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert adapter.call_count == 1
        adapter.get_pr_checks(97, "dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert adapter.call_count == 2

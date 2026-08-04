"""Tests for the structured GitHub adapter (F22/F23/F24).

Covers:
- ``gh run list --commit`` structured fields (workflowName, event, headSha)
- Multi-word workflow names are preserved exactly
- State Gate (push) and State Gate (pull_request) are distinguishable
- ``baseline`` job name is never confused with ``CI`` workflow name (F23)
- Wrong head SHA workflow observations are rejected
- Required workflow subsets are rejected
- Duplicate workflows are rejected
- Non-SUCCESS conclusions (PENDING, SKIPPED, CANCELLED, FAILURE, etc.) rejected
- Empty conclusion with completed status is rejected (F24)
- FakeGitHubAdapter filters by expected head SHA
- validate_workflow_observations blocking reasons
- LiveGitHubAdapter requests only supported JSON fields (no ``detail``)
"""

from __future__ import annotations

import inspect
import json
from unittest.mock import patch

import pytest

from reverse_agent.platform_v1.github_adapter import (
    FakeGitHubAdapter,
    GitHubAdapterError,
    LiveGitHubAdapter,
    WorkflowRun,
    composite_name,
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


def _make_run(
    workflow_name: str,
    event: str = "pull_request",
    *,
    head_sha: str = VALID_HEAD_SHA,
    conclusion: str = "SUCCESS",
    status: str = "COMPLETED",
    run_id: str = "123",
) -> WorkflowRun:
    return WorkflowRun(
        workflow_name=workflow_name,
        event=event,
        run_id=run_id,
        head_sha=head_sha,
        status=status,
        conclusion=conclusion,
    )


def _all_required_success(head_sha: str = VALID_HEAD_SHA) -> tuple[WorkflowRun, ...]:
    """Return one SUCCESS run for each required (workflowName, event) key."""

    return (
        _make_run("CI", "pull_request", head_sha=head_sha),
        _make_run("Decision Preflight", "pull_request", head_sha=head_sha),
        _make_run("State Gate", "pull_request", head_sha=head_sha),
        _make_run("State Gate", "push", head_sha=head_sha),
    )


# ---------------------------------------------------------------------------
# WorkflowRun
# ---------------------------------------------------------------------------

class TestWorkflowRun:
    def test_multi_word_workflow_name_preserved(self) -> None:
        run = _make_run("Decision Preflight")
        assert run.workflow_name == "Decision Preflight"

    def test_state_gate_push_composite_name(self) -> None:
        run = _make_run("State Gate", "push")
        assert run.composite_name == "State Gate (push)"

    def test_state_gate_pull_request_composite_name(self) -> None:
        run = _make_run("State Gate", "pull_request")
        assert run.composite_name == "State Gate (pull_request)"

    def test_state_gate_pull_request_target_composite_name(self) -> None:
        # v9: pull_request_target is distinct from pull_request
        run = _make_run("State Gate", "pull_request_target")
        assert run.composite_name == "State Gate (pull_request_target)"

    def test_ci_composite_name_is_ci(self) -> None:
        run = _make_run("CI", "pull_request")
        assert run.composite_name == "CI"

    def test_decision_preflight_composite_name(self) -> None:
        run = _make_run("Decision Preflight", "pull_request")
        assert run.composite_name == "Decision Preflight"

    def test_to_dict_preserves_all_fields(self) -> None:
        run = WorkflowRun(
            workflow_name="CI",
            event="pull_request",
            run_id="42",
            head_sha=VALID_HEAD_SHA,
            head_branch="agent/branch",
            status="COMPLETED",
            conclusion="SUCCESS",
            workflow_id="wf-123",
            attempt=1,
        )
        d = run.to_dict()
        assert d["workflow_name"] == "CI"
        assert d["event"] == "pull_request"
        assert d["name"] == "CI"
        assert d["run_id"] == "42"
        assert d["head_sha"] == VALID_HEAD_SHA
        assert d["head_branch"] == "agent/branch"
        assert d["status"] == "COMPLETED"
        assert d["conclusion"] == "SUCCESS"
        assert d["workflow_id"] == "wf-123"
        assert d["attempt"] == 1

    def test_status_and_conclusion_uppercased(self) -> None:
        run = WorkflowRun(
            workflow_name="CI",
            event="push",
            run_id="1",
            head_sha=VALID_HEAD_SHA,
            status="completed",
            conclusion="success",
        )
        assert run.status == "COMPLETED"
        assert run.conclusion == "SUCCESS"

    def test_is_success_true_only_when_completed_and_success(self) -> None:
        ok = _make_run("CI")
        assert ok.is_success is True
        not_completed = _make_run("CI", status="IN_PROGRESS")
        assert not_completed.is_success is False
        not_success = _make_run("CI", conclusion="FAILURE")
        assert not_success.is_success is False


# ---------------------------------------------------------------------------
# composite_name helper
# ---------------------------------------------------------------------------

class TestCompositeName:
    def test_ci_pull_request(self) -> None:
        assert composite_name("CI", "pull_request") == "CI"

    def test_decision_preflight_pull_request(self) -> None:
        assert composite_name("Decision Preflight", "pull_request") == "Decision Preflight"

    def test_state_gate_push(self) -> None:
        assert composite_name("State Gate", "push") == "State Gate (push)"

    def test_state_gate_pull_request(self) -> None:
        assert composite_name("State Gate", "pull_request") == "State Gate (pull_request)"

    def test_state_gate_pull_request_target(self) -> None:
        # v9: pull_request_target is the trusted-target event, distinct from
        # pull_request and push.
        assert composite_name("State Gate", "pull_request_target") == "State Gate (pull_request_target)"

    def test_unknown_workflow_falls_back_to_parenthesized_event(self) -> None:
        # Unknown (workflowName, event) pairs fall back to "Name (event)" form.
        assert composite_name("Custom", "workflow_dispatch") == "Custom (workflow_dispatch)"


# ---------------------------------------------------------------------------
# F23: baseline (job name) is never confused with CI (workflow name)
# ---------------------------------------------------------------------------

class TestBaselineIsNotCI:
    """F23: The job ``name`` (e.g. ``baseline``) is never confused with the
    workflow ``workflowName`` (e.g. ``CI``)."""

    def test_baseline_run_does_not_satisfy_ci_requirement(self) -> None:
        # If a run with workflowName=baseline were observed (it should not be),
        # its composite_name would be "baseline (pull_request)", NOT "CI".
        run = _make_run("baseline", "pull_request")
        assert run.composite_name != "CI"
        assert run.composite_name == "baseline (pull_request)"

    def test_ci_workflow_name_satisfies_ci_requirement(self) -> None:
        run = _make_run("CI", "pull_request")
        assert run.composite_name == "CI"


# ---------------------------------------------------------------------------
# push vs pull_request State Gate distinguishable
# ---------------------------------------------------------------------------

class TestStateGateDisambiguation:
    """F23: State Gate (push) and State Gate (pull_request) are distinct."""

    def test_push_and_pull_request_are_different_composite_names(self) -> None:
        push = _make_run("State Gate", "push")
        pr = _make_run("State Gate", "pull_request")
        assert push.composite_name != pr.composite_name

    def test_both_required_workflows_can_coexist(self) -> None:
        runs = _all_required_success()
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert blocking == []

    def test_only_push_without_pull_request_rejected(self) -> None:
        runs = tuple(
            _make_run(wf, ev)
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)
        assert "State Gate (pull_request)" in ",".join(blocking)

    def test_only_pull_request_without_push_rejected(self) -> None:
        runs = tuple(
            _make_run(wf, ev)
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)
        assert "State Gate (push)" in ",".join(blocking)


# ---------------------------------------------------------------------------
# Wrong head SHA rejection
# ---------------------------------------------------------------------------

class TestWrongHeadRejection:
    """F22: Workflow observations with wrong head SHA are rejected."""

    def test_wrong_head_workflow_rejected(self) -> None:
        runs = tuple(
            _make_run(wf, ev, head_sha=WRONG_HEAD_SHA)
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("wrong_head_workflow" in b for b in blocking)

    def test_partial_wrong_head_rejected(self) -> None:
        runs = tuple(
            _make_run(wf, ev, head_sha=WRONG_HEAD_SHA if wf == "CI" else VALID_HEAD_SHA)
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("wrong_head_workflow" in b for b in blocking)
        assert "CI" in ",".join(blocking)


# ---------------------------------------------------------------------------
# Required workflow subset rejection
# ---------------------------------------------------------------------------

class TestWorkflowSubsetRejection:
    """F12/F22: A subset of required workflows is rejected."""

    def test_subset_rejected(self) -> None:
        runs = (
            _make_run("CI", "pull_request"),
            _make_run("Decision Preflight", "pull_request"),
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("missing_workflows" in b for b in blocking)

    def test_superset_rejected(self) -> None:
        runs = _all_required_success() + (
            _make_run("Extra Workflow", "pull_request"),
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
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
        runs = _all_required_success() + (
            _make_run("CI", "pull_request"),
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("duplicate_workflow" in b for b in blocking)


# ---------------------------------------------------------------------------
# Non-SUCCESS conclusion rejection (F24)
# ---------------------------------------------------------------------------

class TestNonSuccessConclusionRejection:
    """F24: Non-SUCCESS conclusions are rejected."""

    @pytest.mark.parametrize("conclusion", [
        "PENDING", "SKIPPED", "CANCELLED", "UNKNOWN", "FAILURE",
        "TIMED_OUT", "ACTION_REQUIRED", "STALE", "NEUTRAL",
    ])
    def test_rejected_conclusion_blocked(self, conclusion: str) -> None:
        runs = tuple(
            _make_run(wf, ev, conclusion=conclusion if wf == "CI" else "SUCCESS")
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("workflow_not_success" in b for b in blocking)
        assert "CI" in ",".join(blocking)


# ---------------------------------------------------------------------------
# F24: completed + empty conclusion never passes
# ---------------------------------------------------------------------------

class TestEmptyConclusionRejected:
    """F24: A completed run with empty conclusion never passes."""

    def test_empty_conclusion_blocked(self) -> None:
        runs = tuple(
            _make_run(wf, ev, conclusion="" if wf == "CI" else "SUCCESS")
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("workflow_not_success" in b for b in blocking)
        assert "CI" in ",".join(blocking)

    def test_empty_conclusion_not_success_on_run(self) -> None:
        run = _make_run("CI", conclusion="")
        assert run.is_success is False


# ---------------------------------------------------------------------------
# Pending/in_progress status rejected (F24)
# ---------------------------------------------------------------------------

class TestNonCompletedStatusRejected:
    """F24: Pending/queued/in_progress statuses are rejected."""

    @pytest.mark.parametrize("status", [
        "PENDING", "QUEUED", "IN_PROGRESS", "SKIPPED", "CANCELLED",
    ])
    def test_non_completed_status_blocked(self, status: str) -> None:
        runs = tuple(
            _make_run(wf, ev, status=status if wf == "CI" else "COMPLETED")
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        blocking, _ = validate_workflow_observations(
            runs, REQUIRED_WORKFLOWS, VALID_HEAD_SHA,
        )
        assert any("workflow_not_success" in b for b in blocking)


# ---------------------------------------------------------------------------
# FakeGitHubAdapter
# ---------------------------------------------------------------------------

class TestFakeGitHubAdapter:
    def test_returns_configured_runs(self) -> None:
        runs = _all_required_success()
        adapter = FakeGitHubAdapter(runs=runs)
        result = adapter.get_workflow_runs("dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert len(result) == len(runs)

    def test_filters_by_expected_head_sha(self) -> None:
        runs = _all_required_success() + tuple(
            _make_run(wf, ev, head_sha=WRONG_HEAD_SHA)
            for wf, ev in [
                ("CI", "pull_request"),
                ("Decision Preflight", "pull_request"),
                ("State Gate", "pull_request"),
                ("State Gate", "push"),
            ]
        )
        adapter = FakeGitHubAdapter(runs=runs)
        result = adapter.get_workflow_runs("dddd2024/reverse-agent", VALID_HEAD_SHA)
        # Only the 4 runs with matching head_sha are returned
        assert len(result) == 4

    def test_raises_when_configured_to_fail(self) -> None:
        adapter = FakeGitHubAdapter(
            fail_with=GitHubAdapterError("gh_run_list_failed", "exit=1"),
        )
        with pytest.raises(GitHubAdapterError) as exc_info:
            adapter.get_workflow_runs("dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert exc_info.value.code == "gh_run_list_failed"

    def test_call_count_increments(self) -> None:
        adapter = FakeGitHubAdapter(runs=_all_required_success())
        assert adapter.call_count == 0
        adapter.get_workflow_runs("dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert adapter.call_count == 1
        adapter.get_workflow_runs("dddd2024/reverse-agent", VALID_HEAD_SHA)
        assert adapter.call_count == 2


# ---------------------------------------------------------------------------
# F23: LiveGitHubAdapter requests only supported JSON fields (no ``detail``)
# ---------------------------------------------------------------------------

class TestLiveGitHubAdapterJsonFields:
    """F23: The live adapter uses ``gh run list`` with structured fields only.

    The unsupported ``detail`` field (used by ``gh pr checks``) must never
    be requested.
    """

    def _json_fields_string(self) -> str:
        # Inspect the LiveGitHubAdapter._JSON_FIELDS class attribute.
        return str(LiveGitHubAdapter._JSON_FIELDS)

    def test_requests_workflow_name_field(self) -> None:
        assert "workflowName" in self._json_fields_string()

    def test_requests_event_field(self) -> None:
        assert "event" in self._json_fields_string()

    def test_requests_head_sha_field(self) -> None:
        assert "headSha" in self._json_fields_string()

    def test_requests_status_field(self) -> None:
        assert "status" in self._json_fields_string()

    def test_requests_conclusion_field(self) -> None:
        assert "conclusion" in self._json_fields_string()

    def test_does_not_request_detail_field(self) -> None:
        # F23: ``detail`` is not a supported field on ``gh run list``.
        fields = self._json_fields_string()
        assert "detail" not in fields.lower()

    def test_uses_run_list_subcommand(self) -> None:
        # Inspect the source of get_workflow_runs to verify it calls
        # ``gh run list`` (not ``gh pr checks``).
        source = inspect.getsource(LiveGitHubAdapter.get_workflow_runs)
        assert '"run"' in source and '"list"' in source
        assert "pr checks" not in source


class TestLiveStateGateTargetPagination:
    """v10: canonical target discovery is complete and PR-associated."""

    @staticmethod
    def _raw_target(run_id: int, pr_number: int) -> dict:
        return {
            "id": run_id,
            "run_attempt": 1,
            "created_at": f"2026-08-04T00:00:{run_id:02d}Z",
            "repository": {"full_name": "dddd2024/reverse-agent"},
            "path": ".github/workflows/state-gate.yml",
            "event": "pull_request_target",
            "head_sha": VALID_HEAD_SHA,
            "head_branch": "main",
            "status": "completed",
            "conclusion": "success",
            "workflow_id": 123,
            "pull_requests": [{"number": pr_number}],
        }

    @staticmethod
    def _result(stdout: str, returncode: int = 0):
        class Result:
            pass
        result = Result()
        result.stdout = stdout
        result.stderr = ""
        result.returncode = returncode
        return result

    def test_all_pages_observed_and_other_pr_ignored(self) -> None:
        pages = [
            {"total_count": 2, "workflow_runs": [self._raw_target(1, 106)]},
            {"total_count": 2, "workflow_runs": [self._raw_target(2, 999)]},
        ]
        with patch(
            "reverse_agent.platform_v1.github_adapter.subprocess.run",
            return_value=self._result(json.dumps(pages)),
        ) as run:
            observed = LiveGitHubAdapter().get_state_gate_target_runs(
                "dddd2024/reverse-agent", 106, VALID_HEAD_SHA,
            )
        assert [item.run_id for item in observed] == ["1"]
        argv = run.call_args.args[0]
        assert "--paginate" in argv and "--slurp" in argv
        assert "event=pull_request_target" in argv
        assert "per_page=100" in argv

    @pytest.mark.parametrize(
        "reported_path",
        [
            ".github/workflows/state-gate.yml",
            ".github/workflows/state-gate.yml@main",
            ".github/workflows/state-gate.yml@refs/heads/main",
            f".github/workflows/state-gate.yml@{'a' * 40}",
        ],
    )
    def test_target_path_variants_share_canonical_identity(
        self, reported_path: str,
    ) -> None:
        raw = self._raw_target(1, 106)
        raw["path"] = reported_path
        pages = [{"total_count": 1, "workflow_runs": [raw]}]
        with patch(
            "reverse_agent.platform_v1.github_adapter.subprocess.run",
            return_value=self._result(json.dumps(pages)),
        ):
            observed = LiveGitHubAdapter().get_state_gate_target_runs(
                "dddd2024/reverse-agent", 106, VALID_HEAD_SHA,
            )
        assert observed[0].workflow_path == ".github/workflows/state-gate.yml"

    @pytest.mark.parametrize(
        "reported_path",
        [
            ".github/workflows/other.yml",
            ".github/workflows/state-gate.yml@",
            ".github/workflows/state-gate.yml@main@refs/heads/main",
            None,
        ],
    )
    def test_invalid_target_path_fails_closed(self, reported_path: object) -> None:
        raw = self._raw_target(1, 106)
        raw["path"] = reported_path
        pages = [{"total_count": 1, "workflow_runs": [raw]}]
        with patch(
            "reverse_agent.platform_v1.github_adapter.subprocess.run",
            return_value=self._result(json.dumps(pages)),
        ):
            with pytest.raises(GitHubAdapterError) as exc_info:
                LiveGitHubAdapter().get_state_gate_target_runs(
                    "dddd2024/reverse-agent", 106, VALID_HEAD_SHA,
                )
        assert exc_info.value.code == "state_gate_target_run_identity_mismatch"

    def test_incomplete_pagination_fails_closed(self) -> None:
        pages = [
            {"total_count": 2, "workflow_runs": [self._raw_target(1, 106)]},
        ]
        with patch(
            "reverse_agent.platform_v1.github_adapter.subprocess.run",
            return_value=self._result(json.dumps(pages)),
        ):
            with pytest.raises(GitHubAdapterError) as exc_info:
                LiveGitHubAdapter().get_state_gate_target_runs(
                    "dddd2024/reverse-agent", 106, VALID_HEAD_SHA,
                )
        assert exc_info.value.code == "state_gate_target_pagination_incomplete"

    def test_api_failure_fails_closed(self) -> None:
        with patch(
            "reverse_agent.platform_v1.github_adapter.subprocess.run",
            return_value=self._result("", returncode=1),
        ):
            with pytest.raises(GitHubAdapterError) as exc_info:
                LiveGitHubAdapter().get_state_gate_target_runs(
                    "dddd2024/reverse-agent", 106, VALID_HEAD_SHA,
                )
        assert exc_info.value.code == "state_gate_target_api_failed"

"""Tests for the Git/GitHub evidence adapter.

Covers:
- get_changed_paths via git diff (raises EvidenceCollectionError on failure)
- check_git_diff via git diff --check (raises EvidenceCollectionError on failure)
- parse_pr_checks output parsing
- merge_evidence: trusted overrides untrusted
- assemble_evidence: collects Git truth (collection_mode=live)
"""

from __future__ import annotations

import subprocess

import pytest

from reverse_agent.platform_v1.contracts import ExecutionEvidence
from reverse_agent.platform_v1.evidence_adapter import (
    EvidenceCollectionError,
    FakeCommandRunner,
    FakeGitAdapter,
    assemble_evidence,
    check_git_diff,
    collect_live_evidence,
    get_changed_paths,
    merge_evidence,
    parse_pr_checks,
)
from reverse_agent.platform_v1.github_adapter import (
    FakeGitHubAdapter,
    GitHubAdapterError,
    WorkflowCheck,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"


def _make_evidence(**overrides) -> ExecutionEvidence:
    defaults = {
        "execution_id": "exec-1",
        "repository": "dddd2024/reverse-agent",
        "base_sha": VALID_BASE_SHA,
        "head_sha": VALID_HEAD_SHA,
        "pr_number": 97,
        "required_workflows": ("CI",),
        "changed_paths": (),
        "test_results": {},
        "git_diff_check_passed": False,
        "agent_completion_claim": "",
        "ci_checks": (),
        "collected_at": "",
    }
    defaults.update(overrides)
    return ExecutionEvidence(**defaults)


# ---------------------------------------------------------------------------
# get_changed_paths
# ---------------------------------------------------------------------------

class TestGetChangedPaths:
    def test_returns_paths_from_git_diff(self, tmp_path) -> None:
        # Set up a tiny git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        (repo / "b.py").write_text("b = 2\n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b")

        paths = get_changed_paths(base_sha, "HEAD", str(repo))
        assert "b.py" in paths

    def test_raises_on_git_failure(self, tmp_path) -> None:
        # Non-existent base SHA in a non-repo directory -> git failure.
        # The adapter must raise EvidenceCollectionError, not return ().
        with pytest.raises(EvidenceCollectionError) as exc_info:
            get_changed_paths("0" * 40, "HEAD", str(tmp_path))
        assert exc_info.value.code == "git_diff_name_only_failed"
        assert "exit=" in exc_info.value.detail

    def test_does_not_return_empty_on_git_failure(self, tmp_path) -> None:
        # The old behavior returned () on git failure; the new contract
        # raises. Verify the function does NOT silently return an empty tuple.
        with pytest.raises(EvidenceCollectionError):
            get_changed_paths("0" * 40, "HEAD", str(tmp_path))


# ---------------------------------------------------------------------------
# check_git_diff
# ---------------------------------------------------------------------------

class TestCheckGitDiff:
    def test_returns_true_when_no_whitespace_errors(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        (repo / "b.py").write_text("b = 2\n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b")

        assert check_git_diff(base_sha, "HEAD", str(repo)) is True

    def test_returns_false_when_whitespace_errors(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        # trailing whitespace triggers git diff --check failure (exit 2)
        (repo / "b.py").write_text("b = 2   \n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b with trailing space")

        assert check_git_diff(base_sha, "HEAD", str(repo)) is False

    def test_raises_on_git_failure(self, tmp_path) -> None:
        # A non-repo directory causes git to fail with an unexpected exit
        # code (not 0 or 2), which must raise EvidenceCollectionError.
        with pytest.raises(EvidenceCollectionError) as exc_info:
            check_git_diff("0" * 40, "HEAD", str(tmp_path))
        assert exc_info.value.code == "git_diff_check_failed"
        assert "exit=" in exc_info.value.detail


# ---------------------------------------------------------------------------
# parse_pr_checks
# ---------------------------------------------------------------------------

class TestParsePrChecks:
    def test_parses_success_status(self) -> None:
        output = "CI\tSUCCESS\tmain\t1234567890\n"
        checks = parse_pr_checks(output)
        assert len(checks) == 1
        assert checks[0]["name"] == "CI"
        assert checks[0]["status"] == "SUCCESS"

    def test_parses_multiple_checks(self) -> None:
        output = (
            "CI\tSUCCESS\tmain\t123\n"
            "State Gate\tFAILURE\tmain\t124\n"
            "Decision Preflight\tSUCCESS\tmain\t125\n"
        )
        checks = parse_pr_checks(output)
        assert len(checks) == 3
        assert checks[0]["status"] == "SUCCESS"
        assert checks[1]["status"] == "FAILURE"
        assert checks[2]["status"] == "SUCCESS"

    def test_skips_header_and_empty_lines(self) -> None:
        output = (
            "name\tstate\tbranch\tid\n"
            "\n"
            "CI\tSUCCESS\tmain\t123\n"
        )
        checks = parse_pr_checks(output)
        assert len(checks) == 1
        assert checks[0]["name"] == "CI"

    def test_empty_output_returns_empty(self) -> None:
        assert parse_pr_checks("") == ()

    def test_unknown_status_default(self) -> None:
        output = "CI\tNEUTRAL\tmain\t123\n"
        checks = parse_pr_checks(output)
        assert len(checks) == 1
        assert checks[0]["status"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# merge_evidence
# ---------------------------------------------------------------------------

class TestMergeEvidence:
    def test_trusted_changed_paths_override_untrusted(self) -> None:
        untrusted = _make_evidence(
            changed_paths=("claimed.py",),
            agent_completion_claim="done",
        )
        trusted = _make_evidence(
            changed_paths=("actual.py",),
            git_diff_check_passed=True,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ("actual.py",)
        assert merged.agent_completion_claim == "done"

    def test_trusted_test_results_override_untrusted(self) -> None:
        untrusted = _make_evidence(
            test_results={"passed": True, "source": "agent"},
        )
        trusted = _make_evidence(
            test_results={"passed": False, "source": "git"},
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.tests_passed is False

    def test_trusted_git_diff_check_overrides(self) -> None:
        untrusted = _make_evidence(git_diff_check_passed=True)
        trusted = _make_evidence(git_diff_check_passed=False)
        merged = merge_evidence(untrusted, trusted)
        assert merged.git_diff_check_passed is False

    def test_trusted_ci_checks_override(self) -> None:
        untrusted = _make_evidence(
            ci_checks=({"name": "CI", "conclusion": "SUCCESS"},),
        )
        trusted = _make_evidence(
            ci_checks=({"name": "CI", "conclusion": "FAILURE"},),
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.ci_passed is False

    def test_trusted_empty_paths_do_not_fallback_to_untrusted(self) -> None:
        # F15: When trusted changed_paths is empty, it stays empty — NO fallback
        untrusted = _make_evidence(
            changed_paths=("from_agent.py",),
            agent_completion_claim="done",
        )
        trusted = _make_evidence(
            changed_paths=(),
            git_diff_check_passed=True,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ()
        # agent_completion_claim is audit-only and preserved from untrusted
        assert merged.agent_completion_claim == "done"

    def test_trusted_empty_test_results_do_not_fallback_to_untrusted(self) -> None:
        # F15: When trusted test_results is empty, it stays empty — NO fallback
        untrusted = _make_evidence(
            test_results={"passed": True, "source": "agent"},
            agent_completion_claim="agent says passed",
        )
        trusted = _make_evidence(
            test_results={},
            git_diff_check_passed=True,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.test_results == {}
        assert merged.tests_passed is False

    def test_trusted_binding_fields_propagate(self) -> None:
        untrusted = _make_evidence(
            repository="untrusted/repo",
            base_sha="0" * 40,
            head_sha="1" * 40,
            pr_number=1,
        )
        trusted = _make_evidence(
            repository="trusted/repo",
            base_sha=VALID_BASE_SHA,
            head_sha=VALID_HEAD_SHA,
            pr_number=97,
            required_workflows=("CI",),
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.repository == "trusted/repo"
        assert merged.base_sha == VALID_BASE_SHA
        assert merged.head_sha == VALID_HEAD_SHA
        assert merged.pr_number == 97
        assert merged.required_workflows == ("CI",)


# ---------------------------------------------------------------------------
# assemble_evidence
# ---------------------------------------------------------------------------

class TestAssembleEvidence:
    def test_assembles_from_git_state(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        (repo / "b.py").write_text("b = 2\n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b")
        head_sha = _git(repo, "rev-parse", "HEAD")

        evidence = assemble_evidence(
            execution_id="exec-1",
            repository="dddd2024/reverse-agent",
            base_sha=base_sha,
            head_sha=head_sha,
            pr_number=97,
            required_workflows=("CI",),
            repo_dir=str(repo),
            test_results={"passed": True},
            ci_checks=({"name": "CI", "conclusion": "SUCCESS"},),
            agent_completion_claim="done",
        )
        assert "b.py" in evidence.changed_paths
        assert evidence.git_diff_check_passed is True
        assert evidence.tests_passed is True
        assert evidence.ci_passed is True
        assert evidence.agent_completion_claim == "done"
        assert evidence.repository == "dddd2024/reverse-agent"
        assert evidence.pr_number == 97
        assert evidence.required_workflows == ("CI",)

    def test_sets_collection_mode_live_and_trusted_provenance(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        (repo / "b.py").write_text("b = 2\n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b")
        head_sha = _git(repo, "rev-parse", "HEAD")

        evidence = assemble_evidence(
            execution_id="exec-1",
            repository="dddd2024/reverse-agent",
            base_sha=base_sha,
            head_sha=head_sha,
            pr_number=97,
            required_workflows=("CI",),
            repo_dir=str(repo),
        )
        assert evidence.collection_mode == "live"
        assert evidence.provenance == "trusted_git_github_collector"
        assert evidence.is_live is True

    def test_raises_on_git_failure(self, tmp_path) -> None:
        # Non-existent base SHA -> get_changed_paths raises EvidenceCollectionError
        with pytest.raises(EvidenceCollectionError):
            assemble_evidence(
                execution_id="exec-1",
                repository="dddd2024/reverse-agent",
                base_sha="0" * 40,
                head_sha="HEAD",
                pr_number=97,
                required_workflows=("CI",),
                repo_dir=str(tmp_path),
            )


# ---------------------------------------------------------------------------
# collect_live_evidence (F14: collector owns truth)
# ---------------------------------------------------------------------------

class TestCollectLiveEvidence:
    """F14: The collector collects all facts through injectable adapters.

    It does NOT accept caller-supplied test pass/fail booleans or CI success
    lists. Git/GitHub/test collector failures return non-zero errors.
    """

    def _make_work_item(self):
        from reverse_agent.platform_v1.contracts import PlatformWorkItem
        return PlatformWorkItem(
            source_issue_number=99,
            repository="dddd2024/reverse-agent",
            base_sha=VALID_BASE_SHA,
            allowed_paths=("reverse_agent/platform_v1/**",),
            forbidden_operations=(),
            acceptance_criteria=(),
            goal="test",
            required_checks=("CI", "Decision Preflight"),
            approved_issue_body_digest="a" * 40,
            risk_tier="R0",
            target_branch="agent/platform-v1-openhands-codex-acp",
        )

    def test_collects_live_evidence_with_fake_adapters(self) -> None:
        wi = self._make_work_item()
        git = FakeGitAdapter(
            changed_paths=("reverse_agent/platform_v1/cli.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(checks=(
            WorkflowCheck(name="CI", run_id="1", head_sha=VALID_HEAD_SHA, event="push", status="COMPLETED", conclusion="SUCCESS"),
            WorkflowCheck(name="Decision Preflight", run_id="2", head_sha=VALID_HEAD_SHA, event="push", status="COMPLETED", conclusion="SUCCESS"),
        ))
        runner = FakeCommandRunner(exit_code=0)

        evidence = collect_live_evidence(
            execution_id=wi.execution_id,
            repository=wi.repository,
            base_sha=wi.base_sha,
            expected_head_sha=VALID_HEAD_SHA,
            pr_number=97,
            required_workflows=wi.required_checks,
            expected_branch=wi.target_branch,
            authority_digest=wi.digest,
            work_item=wi,
            git_adapter=git,
            github_adapter=gh,
            test_command_runner=runner,
            test_command="pytest -q",
        )
        assert evidence.is_live is True
        assert evidence.collection_mode == "live"
        assert evidence.provenance == "trusted_git_github_collector"
        assert evidence.head_sha == VALID_HEAD_SHA
        assert evidence.changed_paths == ("reverse_agent/platform_v1/cli.py",)
        assert evidence.git_diff_check_passed is True
        assert evidence.tests_passed is True

    def test_head_sha_mismatch_raises_error(self) -> None:
        wi = self._make_work_item()
        git = FakeGitAdapter(head_sha="0" * 40)
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                execution_id=wi.execution_id,
                repository=wi.repository,
                base_sha=wi.base_sha,
                expected_head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=wi.required_checks,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
                work_item=wi,
                git_adapter=git,
                github_adapter=FakeGitHubAdapter(),
            )
        assert exc_info.value.code == "head_sha_mismatch"

    def test_git_adapter_failure_raises_error(self) -> None:
        wi = self._make_work_item()
        git = FakeGitAdapter(
            head_sha=VALID_HEAD_SHA,
            fail_with=EvidenceCollectionError("git_rev_parse_failed", "test"),
        )
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                execution_id=wi.execution_id,
                repository=wi.repository,
                base_sha=wi.base_sha,
                expected_head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=wi.required_checks,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
                work_item=wi,
                git_adapter=git,
                github_adapter=FakeGitHubAdapter(),
            )
        assert exc_info.value.code == "git_rev_parse_failed"

    def test_github_adapter_failure_raises_error(self) -> None:
        wi = self._make_work_item()
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(
            fail_with=GitHubAdapterError("gh_pr_checks_failed", "exit=1"),
        )
        with pytest.raises(GitHubAdapterError) as exc_info:
            collect_live_evidence(
                execution_id=wi.execution_id,
                repository=wi.repository,
                base_sha=wi.base_sha,
                expected_head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=wi.required_checks,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
                work_item=wi,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "gh_pr_checks_failed"

    def test_workflow_validation_failure_raises_error(self) -> None:
        wi = self._make_work_item()
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        # Only CI provided, missing Decision Preflight
        gh = FakeGitHubAdapter(checks=(
            WorkflowCheck(name="CI", run_id="1", head_sha=VALID_HEAD_SHA, event="push", status="COMPLETED", conclusion="SUCCESS"),
        ))
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                execution_id=wi.execution_id,
                repository=wi.repository,
                base_sha=wi.base_sha,
                expected_head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=wi.required_checks,
                expected_branch=wi.target_branch,
                authority_digest=wi.digest,
                work_item=wi,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "workflow_validation_failed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git(repo, *args) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr}")
    return result.stdout.strip()

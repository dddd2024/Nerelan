"""Tests for the Git/GitHub evidence adapter.

Covers:
- get_changed_paths via git diff
- check_git_diff via git diff --check
- parse_pr_checks output parsing
- merge_evidence: trusted overrides untrusted
- assemble_evidence: collects Git truth
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from reverse_agent.platform_v1.contracts import ExecutionEvidence
from reverse_agent.platform_v1.evidence_adapter import (
    assemble_evidence,
    check_git_diff,
    get_changed_paths,
    merge_evidence,
    parse_pr_checks,
)


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

    def test_returns_empty_on_git_failure(self, tmp_path) -> None:
        # Non-existent base SHA
        paths = get_changed_paths("0" * 40, "HEAD", str(tmp_path))
        assert paths == ()


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
        # trailing whitespace triggers git diff --check failure
        (repo / "b.py").write_text("b = 2   \n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b with trailing space")

        assert check_git_diff(base_sha, "HEAD", str(repo)) is False


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
        untrusted = ExecutionEvidence(
            execution_id="exec-1",
            changed_paths=("claimed.py",),
            agent_completion_claim="done",
        )
        trusted = ExecutionEvidence(
            execution_id="exec-1",
            changed_paths=("actual.py",),
            git_diff_check_passed=True,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ("actual.py",)
        assert merged.agent_completion_claim == "done"

    def test_trusted_test_results_override_untrusted(self) -> None:
        untrusted = ExecutionEvidence(
            execution_id="exec-1",
            test_results={"passed": True, "source": "agent"},
        )
        trusted = ExecutionEvidence(
            execution_id="exec-1",
            test_results={"passed": False, "source": "git"},
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.tests_passed is False

    def test_trusted_git_diff_check_overrides(self) -> None:
        untrusted = ExecutionEvidence(
            execution_id="exec-1",
            git_diff_check_passed=True,
        )
        trusted = ExecutionEvidence(
            execution_id="exec-1",
            git_diff_check_passed=False,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.git_diff_check_passed is False

    def test_trusted_ci_checks_override(self) -> None:
        untrusted = ExecutionEvidence(
            execution_id="exec-1",
            ci_checks=({"name": "CI", "conclusion": "SUCCESS"},),
        )
        trusted = ExecutionEvidence(
            execution_id="exec-1",
            ci_checks=({"name": "CI", "conclusion": "FAILURE"},),
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.ci_passed is False

    def test_untrusted_paths_used_when_trusted_empty(self) -> None:
        untrusted = ExecutionEvidence(
            execution_id="exec-1",
            changed_paths=("from_agent.py",),
            agent_completion_claim="done",
        )
        trusted = ExecutionEvidence(
            execution_id="exec-1",
            changed_paths=(),
            git_diff_check_passed=True,
        )
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ("from_agent.py",)


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

        evidence = assemble_evidence(
            execution_id="exec-1",
            base_sha=base_sha,
            head_sha="HEAD",
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

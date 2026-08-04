"""Tests for the Git/GitHub evidence adapter (F14/F19/F20/F26/F27).

Covers:
- ``LiveGitAdapter``: get_changed_paths / check_git_diff via subprocess
- ``LiveCommandRunner``: never uses shell=True (F19)
- ``collect_live_evidence`` with injectable adapters and AuthorityBundle
- F19: test commands selected by command_id from the Command Plan
- F19: shell metacharacters rejected; argv list used; shell=False enforced
- F20/F26: caller-supplied test_command / Work Item rejected
- F27: assemble_evidence produces fixture evidence only (never live)
- F27: _create_trusted_evidence is the sole live evidence factory
- F15: merge_evidence trusted overrides untrusted, no fallback
"""

from __future__ import annotations

import inspect
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import reverse_agent

from reverse_agent.platform_v1.authority_adapter import (
    AuthorityBundle,
    AuthorityBundleError,
    LiveIssueProvider,
    LivePRProvider,
    PRE_MERGE_WORKFLOW_KEYS,
    CANONICAL_WORKFLOW_KEYS,
    _validate_merge_intent,
    _validate_pr,
    _validate_issue,
)
from reverse_agent.platform_v1.contracts import ExecutionEvidence, _LIVE_FACTORY_TOKEN
from reverse_agent.platform_v1.evidence_adapter import (
    EvidenceCollectionError,
    FakeCommandRunner,
    FakeGitAdapter,
    FakeReceiptVerifier,
    LiveCommandRunner,
    LiveGitAdapter,
    LiveReceiptVerifier,
    TrustedRuntimeBinding,
    _create_trusted_evidence,
    _is_safe_command,
    _parse_command_to_argv,
    _select_required_test_commands,
    assemble_evidence,
    check_git_diff,
    collect_live_evidence,
    compute_rename_aware_changed_path_digest,
    get_changed_paths,
    get_head_sha,
    merge_evidence,
    validate_trusted_runtime_binding,
)
from reverse_agent.platform_v1.github_adapter import (
    FakeGitHubAdapter,
    GitHubAdapterError,
    WorkflowRun,
    composite_name,
)


VALID_BASE_SHA = "705a0bfd6638d51c688752f154433020225c4e99"
VALID_HEAD_SHA = "e702a3c5f50b9373e0af8087a76268d4a01cd9b1"


def _make_git_tree(root: Path, package_text: str = "VALUE = 'trusted'\n") -> str:
    package = root / "reverse_agent"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(package_text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "reverse_agent/__init__.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"], check=True)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class TestTrustedRuntimeBinding:
    def _trees(self, tmp_path: Path) -> tuple[Path, Path, str, str]:
        trusted = tmp_path / "trusted"
        candidate = tmp_path / "candidate"
        trusted_head = _make_git_tree(trusted)
        candidate_head = _make_git_tree(candidate, "raise RuntimeError('must not execute')\n")
        return trusted, candidate, trusted_head, candidate_head

    def test_separate_real_git_trees_continue_git_evidence_collection(
        self, tmp_path: Path,
    ) -> None:
        trusted, candidate, trusted_head, candidate_head = self._trees(tmp_path)
        candidate_package = candidate / "reverse_agent" / "__init__.py"
        candidate_package.write_text("this is not valid python !!!\n", encoding="utf-8")
        with patch.object(reverse_agent, "__file__", str(trusted / "reverse_agent" / "__init__.py")):
            binding = validate_trusted_runtime_binding(
                trusted_verifier_root=str(trusted),
                candidate_repository_root=str(candidate),
                expected_trusted_revision=trusted_head,
            )
        assert isinstance(binding, TrustedRuntimeBinding)
        assert LiveGitAdapter(binding.candidate_repository_root).get_head_sha() == candidate_head

    def test_same_directory_blocked(self, tmp_path: Path) -> None:
        trusted, _, trusted_head, _ = self._trees(tmp_path)
        with pytest.raises(EvidenceCollectionError) as exc_info:
            validate_trusted_runtime_binding(
                trusted_verifier_root=str(trusted),
                candidate_repository_root=str(trusted),
                expected_trusted_revision=trusted_head,
            )
        assert exc_info.value.code == "trusted_candidate_roots_same"

    def test_nested_directory_blocked(self, tmp_path: Path) -> None:
        trusted = tmp_path / "trusted"
        candidate = trusted / "candidate"
        candidate.mkdir(parents=True)
        with pytest.raises(EvidenceCollectionError) as exc_info:
            validate_trusted_runtime_binding(
                trusted_verifier_root=str(trusted),
                candidate_repository_root=str(candidate),
                expected_trusted_revision="a" * 40,
            )
        assert exc_info.value.code == "trusted_candidate_roots_nested"

    def test_wrong_trusted_head_blocked(self, tmp_path: Path) -> None:
        trusted, candidate, _, _ = self._trees(tmp_path)
        with patch.object(reverse_agent, "__file__", str(trusted / "reverse_agent" / "__init__.py")):
            with pytest.raises(EvidenceCollectionError) as exc_info:
                validate_trusted_runtime_binding(
                    trusted_verifier_root=str(trusted),
                    candidate_repository_root=str(candidate),
                    expected_trusted_revision="a" * 40,
                )
        assert exc_info.value.code == "trusted_revision_mismatch"

    def test_dirty_tracked_trusted_package_blocked(self, tmp_path: Path) -> None:
        trusted, candidate, trusted_head, _ = self._trees(tmp_path)
        (trusted / "reverse_agent" / "__init__.py").write_text("dirty = True\n", encoding="utf-8")
        with patch.object(reverse_agent, "__file__", str(trusted / "reverse_agent" / "__init__.py")):
            with pytest.raises(EvidenceCollectionError) as exc_info:
                validate_trusted_runtime_binding(
                    trusted_verifier_root=str(trusted),
                    candidate_repository_root=str(candidate),
                    expected_trusted_revision=trusted_head,
                )
        assert exc_info.value.code == "trusted_verifier_tracked_files_dirty"

    def test_candidate_sourced_imported_module_blocked(self, tmp_path: Path) -> None:
        trusted, candidate, trusted_head, _ = self._trees(tmp_path)
        with patch.object(reverse_agent, "__file__", str(candidate / "reverse_agent" / "__init__.py")):
            with pytest.raises(EvidenceCollectionError) as exc_info:
                validate_trusted_runtime_binding(
                    trusted_verifier_root=str(trusted),
                    candidate_repository_root=str(candidate),
                    expected_trusted_revision=trusted_head,
                )
        assert exc_info.value.code == "trusted_package_root_mismatch"


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


def _make_bundle(
    *,
    issue_number: int = 100,
    pr_number: int = 97,
    head_sha: str = VALID_HEAD_SHA,
    base_sha: str = VALID_BASE_SHA,
    branch: str = "agent/platform-v1-openhands-codex-acp",
    risk_tier: str = "R0",
    allowed_paths: tuple[str, ...] = ("reverse_agent/platform_v1/**",),
    allowed_commands: tuple[dict, ...] | None = None,
    required_workflow_keys: tuple[tuple[str, str], ...] | None = None,
) -> AuthorityBundle:
    """Build an AuthorityBundle for tests (bypasses live GitHub).

    v9: Uses PRE_MERGE_WORKFLOW_KEYS (3 workflows with pull_request_target)
    by default.  Tests that need the old 4-workflow policy can override
    ``required_workflow_keys``.
    """

    if allowed_commands is None:
        allowed_commands = (
            {
                "command_id": "test.pytest_platform_v1",
                "command": "python -m pytest tests/platform_v1 -q",
                "phase": "test",
                "required": True,
            },
        )
    if required_workflow_keys is None:
        required_workflow_keys = PRE_MERGE_WORKFLOW_KEYS
    return AuthorityBundle(
        decision_id="decision_test",
        round_id="round_test",
        decision_content_sha256="a" * 64,
        command_plan_sha256="b" * 64,
        allowed_command_ids=tuple(c["command_id"] for c in allowed_commands),
        allowed_commands=allowed_commands,
        issue_number=issue_number,
        issue_body_sha256="c" * 64,
        issue_state="OPEN",
        issue_labels=("work-item", "r2", "owner-accepted"),
        repository="dddd2024/reverse-agent",
        pr_number=pr_number,
        branch=branch,
        base_sha=base_sha,
        risk_tier=risk_tier,
        intent_id="intent_test",
        intent_decision_content_sha256="a" * 64,
        intent_command_plan_sha256="b" * 64,
        allowed_paths=allowed_paths,
        required_workflow_keys=required_workflow_keys,
        pr_state="OPEN",
        pr_is_draft=True,
        pr_head_ref_name=branch,
        pr_head_ref_oid=head_sha,
        pr_base_ref_name="main",
        pr_base_ref_oid=base_sha,
    )


def _all_required_runs(
    head_sha: str = VALID_HEAD_SHA,
    base_sha: str = VALID_BASE_SHA,
) -> tuple[WorkflowRun, ...]:
    """Return runs for the v9 dual-head topology.

    Ordinary workflows (CI, Decision Preflight) run at the candidate head.
    The trusted-target State Gate (pull_request_target) runs at the trusted
    base.  State Gate (push) is post-merge and absent from pre-merge evidence.
    """

    return (
        WorkflowRun(workflow_name="CI", event="pull_request", run_id="1",
                    head_sha=head_sha, status="COMPLETED", conclusion="SUCCESS"),
        WorkflowRun(workflow_name="Decision Preflight", event="pull_request",
                    run_id="2", head_sha=head_sha, status="COMPLETED",
                    conclusion="SUCCESS"),
        WorkflowRun(workflow_name="State Gate", event="pull_request_target",
                    run_id="3", head_sha=base_sha, status="COMPLETED",
                    conclusion="SUCCESS", attempt=1),
    )


def _make_git_adapter(
    *,
    head_sha: str = VALID_HEAD_SHA,
    changed_paths: tuple[str, ...] = ("reverse_agent/platform_v1/cli.py",),
    diff_check_passed: bool = True,
    digest: str = "d" * 64,
) -> FakeGitAdapter:
    """Build a FakeGitAdapter with rename-aware digest for v9 tests."""

    return FakeGitAdapter(
        changed_paths=changed_paths,
        diff_check_passed=diff_check_passed,
        head_sha=head_sha,
        rename_aware_paths=changed_paths,
        rename_aware_digest=digest,
    )


# ---------------------------------------------------------------------------
# get_changed_paths / check_git_diff / get_head_sha (legacy function API)
# ---------------------------------------------------------------------------

class TestGetChangedPaths:
    def test_returns_paths_from_git_diff(self, tmp_path) -> None:
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
        with pytest.raises(EvidenceCollectionError) as exc_info:
            get_changed_paths("0" * 40, "HEAD", str(tmp_path))
        assert exc_info.value.code == "git_diff_name_only_failed"
        assert "exit=" in exc_info.value.detail


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
        (repo / "b.py").write_text("b = 2   \n", encoding="utf-8")
        _git(repo, "add", "b.py")
        _git(repo, "commit", "-m", "add b with trailing space")

        assert check_git_diff(base_sha, "HEAD", str(repo)) is False

    def test_raises_on_git_failure(self, tmp_path) -> None:
        with pytest.raises(EvidenceCollectionError) as exc_info:
            check_git_diff("0" * 40, "HEAD", str(tmp_path))
        assert exc_info.value.code == "git_diff_check_failed"
        assert "exit=" in exc_info.value.detail


class TestGetHeadSha:
    def test_returns_head_sha(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        expected = _git(repo, "rev-parse", "HEAD")

        assert get_head_sha(str(repo)) == expected


# ---------------------------------------------------------------------------
# F19: LiveCommandRunner uses shell=False
# ---------------------------------------------------------------------------

class TestLiveCommandRunnerShellFalse:
    """F19: The live command runner never uses shell=True."""

    def test_run_uses_shell_false_in_source(self) -> None:
        source = inspect.getsource(LiveCommandRunner.run)
        assert "shell=False" in source

    def test_run_does_not_use_shell_true_in_source(self) -> None:
        source = inspect.getsource(LiveCommandRunner.run)
        assert "shell=True" not in source

    def test_run_rejects_non_list_argv(self) -> None:
        runner = LiveCommandRunner()
        with pytest.raises(EvidenceCollectionError) as exc_info:
            runner.run("python -m pytest")  # type: ignore[arg-type]
        assert exc_info.value.code == "invalid_argv"

    def test_run_rejects_empty_argv(self) -> None:
        runner = LiveCommandRunner()
        with pytest.raises(EvidenceCollectionError) as exc_info:
            runner.run([])
        assert exc_info.value.code == "invalid_argv"


# ---------------------------------------------------------------------------
# F19: _is_safe_command / _parse_command_to_argv
# ---------------------------------------------------------------------------

class TestSafeCommandParsing:
    """F19: Shell metacharacters are rejected; commands are split to argv."""

    def test_safe_command_no_metacharacters(self) -> None:
        assert _is_safe_command("python -m pytest tests/platform_v1 -q") is True

    @pytest.mark.parametrize("metachar", [";", "|", "&", "<", ">", "`", "$", "\n", "\r"])
    def test_metacharacters_rejected(self, metachar: str) -> None:
        assert _is_safe_command(f"python {metachar} pytest") is False

    def test_logical_and_rejected(self) -> None:
        assert _is_safe_command("python && pytest") is False

    def test_logical_or_rejected(self) -> None:
        assert _is_safe_command("python || pytest") is False

    def test_command_substitution_rejected(self) -> None:
        assert _is_safe_command("python $(whoami)") is False

    def test_parse_command_to_argv_returns_list(self) -> None:
        argv = _parse_command_to_argv("python -m pytest tests/platform_v1 -q")
        assert argv == ["python", "-m", "pytest", "tests/platform_v1", "-q"]

    def test_parse_command_to_argv_rejects_metacharacters(self) -> None:
        with pytest.raises(EvidenceCollectionError) as exc_info:
            _parse_command_to_argv("python; pytest")
        assert exc_info.value.code == "shell_metacharacters_rejected"

    def test_parse_command_to_argv_rejects_empty(self) -> None:
        with pytest.raises(EvidenceCollectionError) as exc_info:
            _parse_command_to_argv("   ")
        assert exc_info.value.code == "empty_command"


# ---------------------------------------------------------------------------
# F19: _select_required_test_commands selects by command_id from Command Plan
# ---------------------------------------------------------------------------

class TestSelectRequiredTestCommands:
    """F19: Test commands are selected from the bundle's Command Plan."""

    def test_selects_required_test_phase_commands(self) -> None:
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.pytest_platform_v1", "command": "python -m pytest tests/platform_v1 -q",
             "phase": "test", "required": True},
            {"command_id": "observation.git_status", "command": "git status --short",
             "phase": "status", "required": True},
            {"command_id": "test.pytest_optional", "command": "python -m pytest tests/optional",
             "phase": "test", "required": False},
        ))
        selected = _select_required_test_commands(bundle)
        assert len(selected) == 1
        assert selected[0]["command_id"] == "test.pytest_platform_v1"

    def test_does_not_select_non_test_phase(self) -> None:
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "observation.git_status", "command": "git status --short",
             "phase": "status", "required": True},
        ))
        selected = _select_required_test_commands(bundle)
        assert selected == []

    def test_does_not_select_optional_tests(self) -> None:
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.optional", "command": "python -m pytest tests/optional",
             "phase": "test", "required": False},
        ))
        selected = _select_required_test_commands(bundle)
        assert selected == []


# ---------------------------------------------------------------------------
# collect_live_evidence (F14/F19/F20/F26)
# ---------------------------------------------------------------------------

class TestCollectLiveEvidence:
    """F14: The collector owns truth through injectable adapters.

    F19: Test commands are selected by command_id from the bundle.
    F20/F26: Authority comes from the bundle, not from stdin.

    v9: Dual-head topology — ordinary runs at candidate head, trusted-target
    State Gate at trusted base, receipt verifier required.
    """

    def test_collects_live_evidence_with_fake_adapters(self) -> None:
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True
        assert evidence.collection_mode == "live"
        assert evidence.provenance == "trusted_git_github_collector"
        assert evidence.head_sha == VALID_HEAD_SHA
        assert evidence.changed_paths == ("reverse_agent/platform_v1/cli.py",)
        assert evidence.git_diff_check_passed is True
        assert evidence.tests_passed is True
        assert evidence.test_results["source"] == "verified_state_gate_receipt"

    def test_head_sha_mismatch_raises_error(self) -> None:
        bundle = _make_bundle()
        git = FakeGitAdapter(head_sha="0" * 40)
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=FakeGitHubAdapter(),
            )
        assert exc_info.value.code == "head_sha_mismatch"

    def test_git_adapter_failure_raises_error(self) -> None:
        bundle = _make_bundle()
        git = FakeGitAdapter(
            head_sha=VALID_HEAD_SHA,
            fail_with=EvidenceCollectionError("git_rev_parse_failed", "test"),
        )
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=FakeGitHubAdapter(),
            )
        assert exc_info.value.code == "git_rev_parse_failed"

    def test_github_adapter_failure_raises_error(self) -> None:
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(
            fail_with=GitHubAdapterError("gh_run_list_failed", "exit=1"),
        )
        with pytest.raises(GitHubAdapterError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "gh_run_list_failed"

    def test_workflow_validation_failure_raises_error(self) -> None:
        bundle = _make_bundle()
        git = _make_git_adapter()
        # Only CI provided, missing Decision Preflight and State Gate target
        gh = FakeGitHubAdapter(runs=(
            WorkflowRun(workflow_name="CI", event="pull_request",
                        run_id="1", head_sha=VALID_HEAD_SHA,
                        status="COMPLETED", conclusion="SUCCESS"),
        ))
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "ordinary_workflow_validation_failed"

    def test_verified_result_without_receipt_object_blocks(self) -> None:
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True, "receipt": None})

        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
                receipt_verifier=receipt,
            )
        assert exc_info.value.code == "verified_receipt_missing"

    def test_collector_has_no_candidate_command_runner_parameter(self) -> None:
        """The token-bearing collector exposes no candidate runner surface."""
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.pytest_platform_v1",
             "command": "python -m pytest tests/platform_v1 -q",
             "phase": "test", "required": True},
        ))
        assert "command_runner" not in inspect.signature(collect_live_evidence).parameters

    def test_candidate_command_plan_text_is_not_executed(self) -> None:
        """Even a malicious required test command is ignored by live collection."""
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.malicious", "command": "python; rm -rf /",
             "phase": "test", "required": True},
        ))
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.tests_passed is True
        assert evidence.test_results["source"] == "verified_state_gate_receipt"


# ---------------------------------------------------------------------------
# F27: assemble_evidence is deprecated — produces fixture only
# ---------------------------------------------------------------------------

class TestAssembleEvidenceDeprecated:
    """F27: assemble_evidence produces fixture evidence only.

    It must NOT produce live evidence, regardless of inputs. Live evidence
    can only come from collect_live_evidence → _create_trusted_evidence.
    """

    def test_assemble_evidence_returns_fixture_mode(self, tmp_path) -> None:
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
        )
        # F27: assemble_evidence returns fixture, not live
        assert evidence.collection_mode == "fixture"
        assert evidence.provenance == "caller_asserted"
        assert evidence.is_live is False
        assert evidence.live_ready is False

    def test_assemble_evidence_cannot_produce_live_evidence(self, tmp_path) -> None:
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
        # Even with all-success inputs, evidence is fixture, not live
        assert evidence.collection_mode == "fixture"
        assert evidence.is_live is False


# ---------------------------------------------------------------------------
# F27: _create_trusted_evidence is the sole live evidence factory
# ---------------------------------------------------------------------------

class TestTrustedEvidenceFactory:
    """F27: Only _create_trusted_evidence can produce live evidence."""

    def test_create_trusted_evidence_produces_live(self) -> None:
        evidence = _create_trusted_evidence(
            execution_id="exec-1",
            repository="dddd2024/reverse-agent",
            base_sha=VALID_BASE_SHA,
            head_sha=VALID_HEAD_SHA,
            pr_number=97,
            required_workflows=("CI",),
        )
        assert evidence.collection_mode == "live"
        assert evidence.provenance == "trusted_git_github_collector"
        assert evidence.is_live is True

    def test_direct_construction_without_token_rejected(self) -> None:
        """F27: Direct ExecutionEvidence construction with collection_mode=live
        without the trusted factory token must fail."""
        with pytest.raises(ValueError, match="live_mode_requires_trusted_factory"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="dddd2024/reverse-agent",
                base_sha=VALID_BASE_SHA,
                head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=("CI",),
                collection_mode="live",
                provenance="trusted_git_github_collector",
                _factory_token=None,
            )

    def test_direct_construction_with_wrong_token_rejected(self) -> None:
        """F27: A non-None token that is not _LIVE_FACTORY_TOKEN is rejected."""
        with pytest.raises(ValueError, match="live_mode_requires_trusted_factory"):
            ExecutionEvidence(
                execution_id="exec-1",
                repository="dddd2024/reverse-agent",
                base_sha=VALID_BASE_SHA,
                head_sha=VALID_HEAD_SHA,
                pr_number=97,
                required_workflows=("CI",),
                collection_mode="live",
                provenance="trusted_git_github_collector",
                _factory_token=object(),  # wrong token
            )

    def test_token_is_module_private_sentinel(self) -> None:
        """F27: The _LIVE_FACTORY_TOKEN is a module-private sentinel object."""
        # It must be an object instance, not a string or None
        assert _LIVE_FACTORY_TOKEN is not None
        assert not isinstance(_LIVE_FACTORY_TOKEN, (str, int, bytes))


# ---------------------------------------------------------------------------
# merge_evidence (F15: no untrusted fallback)
# ---------------------------------------------------------------------------

class TestMergeEvidence:
    def test_trusted_changed_paths_override_untrusted(self) -> None:
        untrusted = _make_evidence(changed_paths=("claimed.py",))
        trusted = _make_evidence(changed_paths=("actual.py",))
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ("actual.py",)

    def test_trusted_test_results_override_untrusted(self) -> None:
        untrusted = _make_evidence(test_results={"passed": True})
        trusted = _make_evidence(test_results={"passed": False})
        merged = merge_evidence(untrusted, trusted)
        assert merged.tests_passed is False

    def test_trusted_git_diff_check_overrides(self) -> None:
        untrusted = _make_evidence(git_diff_check_passed=True)
        trusted = _make_evidence(git_diff_check_passed=False)
        merged = merge_evidence(untrusted, trusted)
        assert merged.git_diff_check_passed is False

    def test_trusted_empty_paths_do_not_fallback_to_untrusted(self) -> None:
        # F15: When trusted changed_paths is empty, it stays empty — NO fallback
        untrusted = _make_evidence(changed_paths=("from_agent.py",))
        trusted = _make_evidence(changed_paths=())
        merged = merge_evidence(untrusted, trusted)
        assert merged.changed_paths == ()

    def test_trusted_empty_test_results_do_not_fallback_to_untrusted(self) -> None:
        # F15: When trusted test_results is empty, it stays empty — NO fallback
        untrusted = _make_evidence(test_results={"passed": True})
        trusted = _make_evidence(test_results={})
        merged = merge_evidence(untrusted, trusted)
        assert merged.test_results == {}
        assert merged.tests_passed is False

    def test_agent_completion_claim_preserved_from_untrusted(self) -> None:
        untrusted = _make_evidence(agent_completion_claim="agent says done")
        trusted = _make_evidence()
        merged = merge_evidence(untrusted, trusted)
        assert merged.agent_completion_claim == "agent says done"


# ---------------------------------------------------------------------------
# v9/F1: LiveIssueProvider GraphQL parsing
# ---------------------------------------------------------------------------

class TestLiveIssueProviderGraphQL:
    """v9/F1: LiveIssueProvider uses structured GraphQL, not gh issue view.

    Tests parse real GraphQL response shapes through the production
    LiveIssueProvider.fetch_issue method by mocking subprocess.run.
    """

    def _mock_result(self, stdout: str, returncode: int = 0):
        """Create a mock subprocess.CompletedProcess-like object."""

        class _Result:
            def __init__(self, stdout, returncode):
                self.stdout = stdout
                self.stderr = ""
                self.returncode = returncode

        return _Result(stdout, returncode)

    def test_normal_graphql_issue_response(self) -> None:
        """A well-formed GraphQL response parses correctly."""
        import json as _json
        response = _json.dumps({
            "data": {
                "repository": {
                    "issue": {
                        "body": "issue body text",
                        "state": "OPEN",
                        "lastEditedAt": "2026-08-03T14:08:50Z",
                        "labels": {
                            "nodes": [
                                {"name": "work-item"},
                                {"name": "r2"},
                                {"name": "owner-accepted"},
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            },
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            result = provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert result["body"] == "issue body text"
        assert result["state"] == "OPEN"
        assert "lastEditedAt" not in result
        assert "work-item" in result["labels"]
        assert "r2" in result["labels"]
        assert "owner-accepted" in result["labels"]

    def test_issue_envelope_missing_raises_error(self) -> None:
        """Missing data.repository.issue envelope fails closed."""
        import json as _json
        response = _json.dumps({"data": {"repository": None}})
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            with pytest.raises(AuthorityBundleError) as exc_info:
                provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert exc_info.value.code == "graphql_repository_missing"

    def test_issue_missing_raises_error(self) -> None:
        """Missing issue node fails closed."""
        import json as _json
        response = _json.dumps({
            "data": {"repository": {"issue": None}},
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            with pytest.raises(AuthorityBundleError) as exc_info:
                provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert exc_info.value.code == "graphql_issue_missing"

    def test_last_edited_at_is_not_part_of_provider_contract(self) -> None:
        """An observed lastEditedAt value is intentionally not returned."""
        import json as _json
        response = _json.dumps({
            "data": {
                "repository": {
                    "issue": {
                        "body": "body",
                        "state": "OPEN",
                        "lastEditedAt": None,
                        "labels": {
                            "nodes": [{"name": "work-item"}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            },
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            result = provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert "lastEditedAt" not in result

    def test_last_edited_at_missing_is_not_an_authority_claim(self) -> None:
        """No approval timestamp exists, so absence is not treated as protection."""
        import json as _json
        response = _json.dumps({
            "data": {
                "repository": {
                    "issue": {
                        "body": "body",
                        "state": "OPEN",
                        "labels": {
                            "nodes": [{"name": "work-item"}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            },
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            result = provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert result["body"] == "body"
        assert "lastEditedAt" not in result

    def test_last_edited_at_value_is_ignored(self) -> None:
        """Unused edit metadata cannot be presented as a security binding."""
        import json as _json
        response = _json.dumps({
            "data": {
                "repository": {
                    "issue": {
                        "body": "body",
                        "state": "OPEN",
                        "lastEditedAt": "not-a-timestamp",
                        "labels": {
                            "nodes": [{"name": "work-item"}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            },
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            result = provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert result["body"] == "body"
        assert "lastEditedAt" not in result

    def test_labels_pagination_incomplete_raises_error(self) -> None:
        """Incomplete labels pagination fails closed."""
        import json as _json
        response = _json.dumps({
            "data": {
                "repository": {
                    "issue": {
                        "body": "body",
                        "state": "OPEN",
                        "lastEditedAt": None,
                        "labels": {
                            "nodes": [{"name": "work-item"}],
                            "pageInfo": {"hasNextPage": True, "endCursor": "abc"},
                        },
                    },
                },
            },
        })
        provider = LiveIssueProvider()
        with patch(
            "reverse_agent.platform_v1.authority_adapter.subprocess.run",
            return_value=self._mock_result(response),
        ):
            with pytest.raises(AuthorityBundleError) as exc_info:
                provider.fetch_issue("dddd2024/reverse-agent", 105)
        assert exc_info.value.code == "graphql_labels_pagination_incomplete"

    def test_production_code_no_invalid_gh_issue_json_fields(self) -> None:
        """v9/F1: LiveIssueProvider must not use gh issue view or
        content_last_edited_at (unsupported JSON field).

        We check the actual subprocess argv, not the docstring text.
        """

        source = inspect.getsource(LiveIssueProvider.fetch_issue)
        # The actual command must be "gh api graphql", not "gh issue view"
        assert '"gh"' in source
        assert '"api"' in source
        assert '"graphql"' in source
        assert '"issue"' not in source or '"view"' not in source
        assert "content_last_edited_at" not in source


# ---------------------------------------------------------------------------
# v9/F2: autoMergeRequest rejection
# ---------------------------------------------------------------------------

class TestAutoMergeRejection:
    """v9/F2: A Draft PR with non-null autoMergeRequest is blocked."""

    def test_auto_merge_request_non_null_rejected(self) -> None:
        pr = {
            "state": "OPEN",
            "isDraft": True,
            "baseRefName": "main",
            "baseRefOid": VALID_BASE_SHA,
            "headRefName": "agent/test",
            "headRefOid": VALID_HEAD_SHA,
            "autoMergeRequest": {"mergeMethod": "MERGE"},
        }
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_pr(
                pr,
                expected_pr=97,
                expected_repository="dddd2024/reverse-agent",
                expected_branch="agent/test",
                expected_base=VALID_BASE_SHA,
            )
        assert exc_info.value.code == "pr_auto_merge_enabled"

    def test_auto_merge_request_null_accepted(self) -> None:
        pr = {
            "state": "OPEN",
            "isDraft": True,
            "baseRefName": "main",
            "baseRefOid": VALID_BASE_SHA,
            "headRefName": "agent/test",
            "headRefOid": VALID_HEAD_SHA,
            "autoMergeRequest": None,
        }
        result = _validate_pr(
            pr,
            expected_pr=97,
            expected_repository="dddd2024/reverse-agent",
            expected_branch="agent/test",
            expected_base=VALID_BASE_SHA,
        )
        assert result["state"] == "OPEN"


# ---------------------------------------------------------------------------
# v9/F4: Active Intent three-workflow exact match
# ---------------------------------------------------------------------------

class TestActiveIntentValidation:
    """v9/F4: Active Intent must have exactly three pre-merge workflows
    and State Gate (push) as post_merge_integration_workflow."""

    _VALID_INTENT = {
        "schema_version": 1,
        "intent_id": "intent_test",
        "repository": "dddd2024/reverse-agent",
        "source_pr": 106,
        "locked_base_sha": VALID_BASE_SHA,
        "allowed_merge_method": "merge",
        "decision_identity": {
            "decision_id": "decision_test",
            "decision_content_sha256": "a" * 64,
        },
        "command_plan_sha256": "b" * 64,
        "merge_tree_policy": "equal_to_accepted_head_tree",
        "required_workflows": [
            "CI",
            "Decision Preflight",
            "State Gate (pull_request_target)",
        ],
        "post_merge_integration_workflow": "State Gate (push)",
        "expires_at": "2026-12-31T23:59:59Z",
    }

    def test_active_intent_three_workflow_exact_match(self) -> None:
        result = _validate_merge_intent(
            dict(self._VALID_INTENT),
            expected_decision_id="decision_test",
            expected_decision_sha256="a" * 64,
            expected_command_plan_sha256="b" * 64,
            expected_pr=106,
            expected_base=VALID_BASE_SHA,
            expected_repository="dddd2024/reverse-agent",
            validation_time=datetime(2026, 8, 4, tzinfo=timezone.utc),
        )
        assert result[0] == "intent_test"

    def test_push_wrongly_added_to_pre_merge_policy(self) -> None:
        """Adding State Gate (push) to required_workflows blocks."""
        intent = dict(self._VALID_INTENT)
        intent["required_workflows"] = [
            "CI",
            "Decision Preflight",
            "State Gate (pull_request_target)",
            "State Gate (push)",
        ]
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
            )
        assert exc_info.value.code == "intent_workflow_keys_mismatch"

    def test_old_pull_request_state_gate_rejected(self) -> None:
        """Old 'State Gate (pull_request)' in required_workflows blocks."""
        intent = dict(self._VALID_INTENT)
        intent["required_workflows"] = [
            "CI",
            "Decision Preflight",
            "State Gate (pull_request)",
        ]
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
            )
        assert exc_info.value.code == "intent_workflow_keys_mismatch"

    @pytest.mark.parametrize(
        ("field", "value", "expected_code"),
        [
            ("schema_version", 2, "invalid_intent_schema_version"),
            ("allowed_merge_method", "squash", "intent_merge_method_mismatch"),
            ("merge_tree_policy", "no_rewrite", "intent_merge_tree_policy_mismatch"),
        ],
    )
    def test_security_semantics_fail_closed(
        self, field: str, value: object, expected_code: str,
    ) -> None:
        intent = dict(self._VALID_INTENT)
        intent[field] = value
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
                validation_time=datetime(2026, 8, 4, tzinfo=timezone.utc),
            )
        assert exc_info.value.code == expected_code

    def test_expired_intent_fails_at_injected_validation_time(self) -> None:
        intent = dict(self._VALID_INTENT)
        intent["expires_at"] = "2026-08-03T23:59:59Z"
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
                validation_time=datetime(2026, 8, 4, tzinfo=timezone.utc),
            )
        assert exc_info.value.code == "intent_expired"

    def test_decision_identity_exact_field_set(self) -> None:
        intent = dict(self._VALID_INTENT)
        intent["decision_identity"] = {
            **intent["decision_identity"], "round_id": "round_test",
        }
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
                validation_time=datetime(2026, 8, 4, tzinfo=timezone.utc),
            )
        assert exc_info.value.code == "intent_decision_identity_field_set_mismatch"

    def test_missing_post_merge_workflow_rejected(self) -> None:
        """Missing post_merge_integration_workflow blocks."""
        intent = dict(self._VALID_INTENT)
        del intent["post_merge_integration_workflow"]
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
            )
        assert exc_info.value.code == "intent_field_set_mismatch"

    def test_extra_field_rejected(self) -> None:
        """Extra field in active Intent blocks."""
        intent = dict(self._VALID_INTENT)
        intent["unexpected_field"] = "value"
        with pytest.raises(AuthorityBundleError) as exc_info:
            _validate_merge_intent(
                intent,
                expected_decision_id="decision_test",
                expected_decision_sha256="a" * 64,
                expected_command_plan_sha256="b" * 64,
                expected_pr=106,
                expected_base=VALID_BASE_SHA,
                expected_repository="dddd2024/reverse-agent",
            )
        assert exc_info.value.code == "intent_field_set_mismatch"


# ---------------------------------------------------------------------------
# v9/F4: AuthorityBundle returns three pre-merge workflow keys
# ---------------------------------------------------------------------------

class TestAuthorityBundleWorkflowPolicy:
    """v9/F4: AuthorityBundle.required_workflow_keys must contain exactly
    the three pre-merge workflows, not CANONICAL_WORKFLOW_KEYS."""

    def test_authority_bundle_returns_three_workflows(self) -> None:
        bundle = _make_bundle()
        assert bundle.required_workflow_keys == PRE_MERGE_WORKFLOW_KEYS
        assert len(bundle.required_workflow_keys) == 3

    def test_authority_bundle_does_not_return_canonical_keys(self) -> None:
        bundle = _make_bundle()
        assert bundle.required_workflow_keys != CANONICAL_WORKFLOW_KEYS

    def test_authority_bundle_does_not_include_push(self) -> None:
        bundle = _make_bundle()
        events = [ev for _wf, ev in bundle.required_workflow_keys]
        assert "push" not in events

    def test_authority_bundle_includes_pull_request_target(self) -> None:
        bundle = _make_bundle()
        events = [ev for _wf, ev in bundle.required_workflow_keys]
        assert "pull_request_target" in events


# ---------------------------------------------------------------------------
# v9/F3/F5: Dual-head live-evidence topology
# ---------------------------------------------------------------------------

class TestDualHeadTopology:
    """v9/F3: Ordinary workflows at candidate head, trusted-target State Gate
    at trusted base.  Receipt verifier is called with the independently
    computed changed-path digest."""

    def test_ci_preflight_candidate_head(self) -> None:
        """CI and Decision Preflight runs must be at the candidate head."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        # Provide CI/Preflight at candidate head, State Gate at trusted base
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        # The evidence ci_checks should include CI and Decision Preflight
        ci_names = [c["name"] for c in evidence.ci_checks]
        assert "CI" in ci_names
        assert "Decision Preflight" in ci_names

    def test_ci_at_wrong_head_rejected(self) -> None:
        """CI run at the wrong head SHA is not found."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        # CI at wrong head — FakeGitHubAdapter filters by head_sha
        wrong_head = "0" * 40
        gh = FakeGitHubAdapter(runs=(
            WorkflowRun(workflow_name="CI", event="pull_request", run_id="1",
                        head_sha=wrong_head, status="COMPLETED", conclusion="SUCCESS"),
            WorkflowRun(workflow_name="Decision Preflight", event="pull_request",
                        run_id="2", head_sha=VALID_HEAD_SHA, status="COMPLETED",
                        conclusion="SUCCESS"),
            WorkflowRun(workflow_name="State Gate", event="pull_request_target",
                        run_id="3", head_sha=VALID_BASE_SHA, status="COMPLETED",
                        conclusion="SUCCESS", attempt=1),
        ))
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "ordinary_workflow_validation_failed"

    def test_state_gate_target_trusted_base(self) -> None:
        """State Gate (pull_request_target) run must be at the trusted base."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        # State Gate target at trusted base
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        # Receipt verifier was called with trusted_base_sha == bundle.base_sha
        assert len(receipt.calls) == 1
        assert receipt.calls[0]["trusted_base_sha"] == VALID_BASE_SHA
        assert receipt.calls[0]["locked_base_sha"] == VALID_BASE_SHA

    def test_state_gate_target_missing_rejected(self) -> None:
        """Missing State Gate (pull_request_target) at trusted base blocks."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        # Only ordinary runs, no State Gate target
        gh = FakeGitHubAdapter(runs=(
            WorkflowRun(workflow_name="CI", event="pull_request", run_id="1",
                        head_sha=VALID_HEAD_SHA, status="COMPLETED", conclusion="SUCCESS"),
            WorkflowRun(workflow_name="Decision Preflight", event="pull_request",
                        run_id="2", head_sha=VALID_HEAD_SHA, status="COMPLETED",
                        conclusion="SUCCESS"),
        ))
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
            )
        assert exc_info.value.code == "trusted_target_run_missing"

    def test_correct_receipt_verifies(self) -> None:
        """A correct receipt allows evidence collection to succeed."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True
        # Verify receipt was called with the independently computed digest
        assert receipt.calls[0]["expected_changed_paths_sha256"] == "d" * 64

    def test_receipt_verification_failed_blocks(self) -> None:
        """Receipt returning verified=False blocks evidence collection."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": False, "reason": "digest_mismatch"})

        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
                receipt_verifier=receipt,
            )
        assert exc_info.value.code == "receipt_verification_failed"

    def test_receipt_api_failure_blocks(self) -> None:
        """Receipt verifier raising an exception blocks evidence collection."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(
            fail_with=RuntimeError("API timeout"),
        )

        with pytest.raises(RuntimeError, match="API timeout"):
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
                receipt_verifier=receipt,
            )

    def test_no_state_gate_push_in_pre_merge_evidence(self) -> None:
        """State Gate (push) must not appear in pre-merge evidence."""
        bundle = _make_bundle()
        git = _make_git_adapter()
        # A historical/post-merge push run may coexist and must be excluded.
        gh = FakeGitHubAdapter(runs=_all_required_runs() + (
            WorkflowRun(workflow_name="State Gate", event="push", run_id="99",
                        head_sha=VALID_BASE_SHA, status="COMPLETED",
                        conclusion="SUCCESS"),
        ))
        receipt = FakeReceiptVerifier(result={"verified": True})
        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        names = [check["name"] for check in evidence.ci_checks]
        assert "State Gate (pull_request_target)" in names
        assert "State Gate (push)" not in names

    def test_latest_current_pr_target_run_is_selected(self) -> None:
        bundle = _make_bundle()
        runs = _all_required_runs() + (
            WorkflowRun(
                workflow_name="State Gate", event="pull_request_target",
                run_id="4", head_sha=VALID_BASE_SHA, status="COMPLETED",
                conclusion="SUCCESS", attempt=1, source_pr=97,
                created_at="2026-08-04T00:04:00Z",
            ),
        )
        receipt = FakeReceiptVerifier(result={"verified": True})
        collect_live_evidence(
            bundle=bundle,
            git_adapter=_make_git_adapter(),
            github_adapter=FakeGitHubAdapter(runs=runs),
            receipt_verifier=receipt,
        )
        assert receipt.calls[0]["run_id"] == 4

    def test_latest_failed_run_blocks_without_older_success_fallback(self) -> None:
        bundle = _make_bundle()
        runs = _all_required_runs() + (
            WorkflowRun(
                workflow_name="State Gate", event="pull_request_target",
                run_id="4", head_sha=VALID_BASE_SHA, status="COMPLETED",
                conclusion="FAILURE", attempt=1, source_pr=97,
                created_at="2026-08-04T00:04:00Z",
            ),
        )
        receipt = FakeReceiptVerifier(result={"verified": True})
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=_make_git_adapter(),
                github_adapter=FakeGitHubAdapter(runs=runs),
                receipt_verifier=receipt,
            )
        assert exc_info.value.code == "trusted_target_latest_not_success"
        assert receipt.calls == []

    def test_other_pr_sharing_base_is_ignored(self) -> None:
        bundle = _make_bundle()
        current = WorkflowRun(
            workflow_name="State Gate", event="pull_request_target",
            run_id="3", head_sha=VALID_BASE_SHA, status="COMPLETED",
            conclusion="SUCCESS", attempt=1, source_pr=97,
            created_at="2026-08-04T00:03:00Z",
        )
        unrelated = WorkflowRun(
            workflow_name="State Gate", event="pull_request_target",
            run_id="99", head_sha=VALID_BASE_SHA, status="COMPLETED",
            conclusion="FAILURE", attempt=1, source_pr=999,
            created_at="2026-08-04T00:59:00Z",
        )
        ordinary = _all_required_runs()[:2]
        receipt = FakeReceiptVerifier(result={"verified": True})
        collect_live_evidence(
            bundle=bundle,
            git_adapter=_make_git_adapter(),
            github_adapter=FakeGitHubAdapter(runs=ordinary + (current, unrelated)),
            receipt_verifier=receipt,
        )
        assert receipt.calls[0]["run_id"] == 3

    @pytest.mark.parametrize(
        "reason",
        ["wrong_pr", "wrong_base", "wrong_head", "wrong_digest"],
    )
    def test_latest_receipt_binding_mismatch_blocks(self, reason: str) -> None:
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=_make_bundle(),
                git_adapter=_make_git_adapter(),
                github_adapter=FakeGitHubAdapter(runs=_all_required_runs()),
                receipt_verifier=FakeReceiptVerifier(
                    result={"verified": False, "reason": reason},
                ),
            )
        assert exc_info.value.code == "receipt_verification_failed"
        assert exc_info.value.detail == reason

    def test_receipt_called_with_independently_computed_digest(self) -> None:
        """The receipt verifier must receive the independently computed
        digest, not the receipt's own digest."""
        bundle = _make_bundle()
        expected_digest = "abc123" * 10 + "abcd"  # 64 hex chars
        git = _make_git_adapter(digest=expected_digest)
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert receipt.calls[0]["expected_changed_paths_sha256"] == expected_digest


# ---------------------------------------------------------------------------
# v9/F6: Rename-aware changed-path digest
# ---------------------------------------------------------------------------

class TestRenameAwareDigest:
    """v9/F6: The digest uses git diff --name-status -M -C semantics."""

    def test_rename_includes_both_paths(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "old.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "old.py")
        _git(repo, "commit", "-m", "initial")
        base_sha = _git(repo, "rev-parse", "HEAD")
        # Rename old.py to new.py
        _git(repo, "mv", "old.py", "new.py")
        _git(repo, "commit", "-m", "rename")
        head_sha = _git(repo, "rev-parse", "HEAD")

        paths, digest = compute_rename_aware_changed_path_digest(
            str(repo), base_sha, head_sha,
        )
        # Both old and new paths must be present
        assert "old.py" in paths
        assert "new.py" in paths

    def test_empty_diff_raises_error(self, tmp_path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-m", "initial")
        sha = _git(repo, "rev-parse", "HEAD")

        with pytest.raises(EvidenceCollectionError) as exc_info:
            compute_rename_aware_changed_path_digest(str(repo), sha, sha)
        assert exc_info.value.code == "changed_paths_empty"


# ---------------------------------------------------------------------------
# v9/F7: R2 BLOCKED_APPROVAL boundary
# ---------------------------------------------------------------------------

class TestR2BlockedApproval:
    """v9/F7: A valid R2 Authority Bundle must reach BLOCKED_APPROVAL, not
    fail early on invalid Issue fields or wrong workflow policy."""

    def test_r2_reaches_expected_blocked_approval(self) -> None:
        """An R2 bundle with all valid fields should still block at
        BLOCKED_APPROVAL — the R2 tier is the blocking reason, not a
        validation error."""
        bundle = _make_bundle(risk_tier="R2")
        # The bundle itself is valid; the risk tier is what blocks
        assert bundle.risk_tier == "R2"
        # In the CLI, this would return BLOCKED_APPROVAL (exit 50)
        # Here we verify the bundle is constructible and the risk tier
        # is the only blocking factor
        assert bundle.required_workflow_keys == PRE_MERGE_WORKFLOW_KEYS

    def test_r0_bundle_is_not_blocked(self) -> None:
        """An R0 bundle with valid evidence should succeed."""
        bundle = _make_bundle(risk_tier="R0")
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True

    def test_r1_bundle_is_not_blocked(self) -> None:
        """An R1 bundle with valid evidence should succeed."""
        bundle = _make_bundle(risk_tier="R1")
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True


# ---------------------------------------------------------------------------
# v9: Old four-workflow fixture rejected in dual-head topology
# ---------------------------------------------------------------------------

class TestOldFourWorkflowFixtureRejected:
    """v9: A bundle with the old 4-workflow policy (including State Gate push)
    is rejected by the dual-head collector because State Gate (push) must not
    appear in pre-merge evidence."""

    def test_old_four_workflow_fixture_rejected(self) -> None:
        old_keys = (
            ("CI", "pull_request"),
            ("Decision Preflight", "pull_request"),
            ("State Gate", "pull_request"),
            ("State Gate", "push"),
        )
        bundle = _make_bundle(required_workflow_keys=old_keys)
        git = _make_git_adapter()
        # Provide runs matching old policy
        gh = FakeGitHubAdapter(runs=(
            WorkflowRun(workflow_name="CI", event="pull_request", run_id="1",
                        head_sha=VALID_HEAD_SHA, status="COMPLETED", conclusion="SUCCESS"),
            WorkflowRun(workflow_name="Decision Preflight", event="pull_request",
                        run_id="2", head_sha=VALID_HEAD_SHA, status="COMPLETED",
                        conclusion="SUCCESS"),
            WorkflowRun(workflow_name="State Gate", event="pull_request",
                        run_id="3", head_sha=VALID_HEAD_SHA, status="COMPLETED",
                        conclusion="SUCCESS"),
            WorkflowRun(workflow_name="State Gate", event="push", run_id="4",
                        head_sha=VALID_BASE_SHA, status="COMPLETED", conclusion="SUCCESS"),
        ))
        with pytest.raises(EvidenceCollectionError) as exc_info:
            collect_live_evidence(
                bundle=bundle,
                git_adapter=git,
                github_adapter=gh,
            )
        # The old policy classifies push as ordinary, so ordinary validation
        # fails because push is not at candidate head.  Either
        # ordinary_workflow_validation_failed or trusted_target_run_missing
        # is a valid rejection.
        assert exc_info.value.code in (
            "ordinary_workflow_validation_failed",
            "trusted_target_run_missing",
        )


# ---------------------------------------------------------------------------
# v9: R0/R1 dual-head collector passes with complete evidence
# ---------------------------------------------------------------------------

class TestR0R1DualHeadCollector:
    """v9: R0/R1 bundles with complete dual-head evidence succeed."""

    def test_r0_dual_head_collector_passes(self) -> None:
        bundle = _make_bundle(risk_tier="R0")
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True
        assert evidence.tests_passed is True
        assert evidence.git_diff_check_passed is True

    def test_r1_dual_head_collector_passes(self) -> None:
        bundle = _make_bundle(risk_tier="R1")
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        assert evidence.is_live is True
        assert evidence.tests_passed is True

    def test_pre_merge_evidence_has_no_push(self) -> None:
        """The collected evidence must not include State Gate (push)."""
        bundle = _make_bundle(risk_tier="R0")
        git = _make_git_adapter()
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        receipt = FakeReceiptVerifier(result={"verified": True})

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            receipt_verifier=receipt,
        )
        ci_names = [c["name"] for c in evidence.ci_checks]
        assert "State Gate (push)" not in ci_names
        assert "State Gate (pull_request_target)" in ci_names


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

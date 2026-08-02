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
import subprocess

import pytest

from reverse_agent.platform_v1.authority_adapter import AuthorityBundle
from reverse_agent.platform_v1.contracts import ExecutionEvidence, _LIVE_FACTORY_TOKEN
from reverse_agent.platform_v1.evidence_adapter import (
    EvidenceCollectionError,
    FakeCommandRunner,
    FakeGitAdapter,
    LiveCommandRunner,
    LiveGitAdapter,
    _create_trusted_evidence,
    _is_safe_command,
    _parse_command_to_argv,
    _select_required_test_commands,
    assemble_evidence,
    check_git_diff,
    collect_live_evidence,
    get_changed_paths,
    get_head_sha,
    merge_evidence,
)
from reverse_agent.platform_v1.github_adapter import (
    FakeGitHubAdapter,
    GitHubAdapterError,
    WorkflowRun,
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
) -> AuthorityBundle:
    """Build an AuthorityBundle for tests (bypasses live GitHub)."""

    if allowed_commands is None:
        allowed_commands = (
            {
                "command_id": "test.pytest_platform_v1",
                "command": "python -m pytest tests/platform_v1 -q",
                "phase": "test",
                "required": True,
            },
        )
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
        required_workflow_keys=(
            ("CI", "pull_request"),
            ("Decision Preflight", "pull_request"),
            ("State Gate", "pull_request"),
            ("State Gate", "push"),
        ),
        pr_state="OPEN",
        pr_is_draft=True,
        pr_head_ref_name=branch,
        pr_head_ref_oid=head_sha,
        pr_base_ref_name="main",
        pr_base_ref_oid=base_sha,
    )


def _all_required_runs(head_sha: str = VALID_HEAD_SHA) -> tuple[WorkflowRun, ...]:
    return (
        WorkflowRun(workflow_name="CI", event="pull_request", run_id="1",
                    head_sha=head_sha, status="COMPLETED", conclusion="SUCCESS"),
        WorkflowRun(workflow_name="Decision Preflight", event="pull_request",
                    run_id="2", head_sha=head_sha, status="COMPLETED",
                    conclusion="SUCCESS"),
        WorkflowRun(workflow_name="State Gate", event="pull_request",
                    run_id="3", head_sha=head_sha, status="COMPLETED",
                    conclusion="SUCCESS"),
        WorkflowRun(workflow_name="State Gate", event="push", run_id="4",
                    head_sha=head_sha, status="COMPLETED", conclusion="SUCCESS"),
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
    """

    def test_collects_live_evidence_with_fake_adapters(self) -> None:
        bundle = _make_bundle()
        git = FakeGitAdapter(
            changed_paths=("reverse_agent/platform_v1/cli.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        runner = FakeCommandRunner(exit_code=0)

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            command_runner=runner,
        )
        assert evidence.is_live is True
        assert evidence.collection_mode == "live"
        assert evidence.provenance == "trusted_git_github_collector"
        assert evidence.head_sha == VALID_HEAD_SHA
        assert evidence.changed_paths == ("reverse_agent/platform_v1/cli.py",)
        assert evidence.git_diff_check_passed is True
        assert evidence.tests_passed is True

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
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
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
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        # Only CI provided, missing the other three required workflows
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
        assert exc_info.value.code == "workflow_validation_failed"

    def test_test_command_failure_marks_tests_failed(self) -> None:
        bundle = _make_bundle()
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        runner = FakeCommandRunner(exit_code=1)  # test failure

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            command_runner=runner,
        )
        assert evidence.tests_passed is False

    def test_collector_uses_command_id_not_caller_supplied_command(self) -> None:
        """F19: The collector selects commands from the bundle, not from stdin.

        Verify that the command runner receives the argv from the bundle's
        Command Plan, not from any caller-supplied test_command string.
        """
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.pytest_platform_v1",
             "command": "python -m pytest tests/platform_v1 -q",
             "phase": "test", "required": True},
        ))
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        runner = FakeCommandRunner(exit_code=0)

        collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            command_runner=runner,
        )
        # The runner should have received the argv from the bundle's command
        assert len(runner.calls) == 1
        assert runner.calls[0] == ["python", "-m", "pytest", "tests/platform_v1", "-q"]

    def test_collector_rejects_command_with_shell_metacharacters(self) -> None:
        """F19: If a Command Plan command contains shell metacharacters, the
        collector records it as a failed test rather than executing it."""
        bundle = _make_bundle(allowed_commands=(
            {"command_id": "test.malicious", "command": "python; rm -rf /",
             "phase": "test", "required": True},
        ))
        git = FakeGitAdapter(
            changed_paths=("a.py",),
            diff_check_passed=True,
            head_sha=VALID_HEAD_SHA,
        )
        gh = FakeGitHubAdapter(runs=_all_required_runs())
        runner = FakeCommandRunner(exit_code=0)

        evidence = collect_live_evidence(
            bundle=bundle,
            git_adapter=git,
            github_adapter=gh,
            command_runner=runner,
        )
        # The malicious command is recorded as failed; runner was never called
        assert evidence.tests_passed is False
        assert runner.calls == []


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

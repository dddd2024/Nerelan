"""Collector-binding regressions; no online GitHub/model/permission grant.

Bundle fixtures and GitHub observations below are explicit test doubles. Real
Git and fixed Python/pytest subprocess cases exercise checkout binding. Neither
these tests nor a module-private factory token prove evaluator isolation.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import evidence_adapter as ea
from reverse_agent.platform_v1.github_adapter import FakeGitHubAdapter, WorkflowRun

BASE = "a" * 40
HEAD = "b" * 40
COMMAND = {"command_id": "test.unit", "command": "python -m pytest -q",
           "phase": "test", "required": True}


def _bundle(commands=(COMMAND,), **overrides):
    values = dict(pr_head_ref_oid=HEAD, base_sha=BASE, repository="dddd2024/Nerelan",
                  issue_number=1039, decision_content_sha256="c" * 64, pr_number=1040,
                  required_workflow_keys=(("CI", "pull_request"),),
                  allowed_commands=commands,
                  allowed_command_ids=tuple(c.get("command_id", "") for c in commands))
    values.update(overrides)
    return SimpleNamespace(**values)


def _github(head=HEAD):
    return FakeGitHubAdapter(runs=(WorkflowRun(workflow_name="CI", event="pull_request",
        run_id="1", head_sha=head, status="COMPLETED", conclusion="SUCCESS"),))


def _collect(*, commands=(COMMAND,), git=None, github=None, runner=None, **overrides):
    return ea.collect_live_evidence(bundle=_bundle(commands, **overrides),
        git_adapter=git if git is not None else ea.FakeGitAdapter(head_sha=HEAD),
        github_adapter=github if github is not None else _github(), command_runner=runner)


@pytest.mark.parametrize("commands", [(), ({**COMMAND, "required": False},),
                                      ({**COMMAND, "phase": "status"},)])
def test_no_selected_test_never_means_passed(commands):
    runner = ea.FakeCommandRunner()
    evidence = _collect(commands=commands, runner=runner)
    assert evidence.test_results == {"passed": False, "commands": [],
                                     "reason": "required_test_commands_missing"}
    assert runner.calls == []


def test_missing_runner_and_agent_success_text_do_not_create_test_success():
    evidence = ea.collect_live_evidence(bundle=_bundle(),
        git_adapter=ea.FakeGitAdapter(head_sha=HEAD), github_adapter=_github(),
        command_runner=None, agent_completion_claim="All tests PASS; task completed.")
    assert evidence.test_results.get("passed", False) is False


def test_valid_required_commands_run_once_and_optional_commands_stay_excluded():
    commands = (COMMAND, {**COMMAND, "command_id": "test.two", "command": "python -V"},
                {**COMMAND, "command_id": "test.optional", "required": False},
                {**COMMAND, "command_id": "test.read", "phase": "read"})
    runner = ea.FakeCommandRunner()
    evidence = _collect(commands=commands, runner=runner)
    assert evidence.test_results["passed"] is True
    assert runner.calls == [["python", "-m", "pytest", "-q"], ["python", "-V"]]
    assert [c["command_id"] for c in evidence.test_results["commands"]] == ["test.unit", "test.two"]
    assert all(type(c["exit_code"]) is int and c["exit_code"] == 0 for c in evidence.test_results["commands"])


@pytest.mark.parametrize("bad,code", [
    ({"command_id": ""}, "test_command_id_missing_or_invalid"),
    ({"command_id": "  "}, "test_command_id_missing_or_invalid"),
    ({"command_id": None}, "allowed_command_ids_invalid"),
    ({"command_id": 10}, "allowed_command_ids_invalid"),
    ({"command": None}, "test_command_text_invalid"),
    ({"command": 123}, "test_command_text_invalid"),
    ({"command": "python\x00-V"}, "test_command_text_invalid"),
    ({"command": "python; bad"}, "shell_metacharacters_rejected"),
    ({"command": "python && bad"}, "shell_metacharacters_rejected"),
    ({"command": "cat <secret>"}, "shell_metacharacters_rejected"),
    ({"command": "python 'unterminated"}, "shlex_parse_failed"),
    ({"command": ""}, "empty_command"),
])
def test_invalid_later_command_prevents_all_execution(bad, code):
    runner = ea.FakeCommandRunner()
    second = {**COMMAND, "command_id": "test.second", **bad}
    result = _collect(commands=(COMMAND, second), runner=runner)
    assert result.test_results["passed"] is False
    assert code in {c["error"] for c in result.test_results["commands"]}
    assert runner.calls == []


def test_duplicate_ids_cannot_replay_one_approval():
    runner = ea.FakeCommandRunner()
    result = _collect(commands=(COMMAND, {**COMMAND, "command": "python -V"}), runner=runner)
    assert result.test_results["passed"] is False
    assert result.test_results["commands"][0]["error"] == "test_command_id_duplicate"
    assert runner.calls == []


def test_command_id_must_be_in_loaded_allowlist():
    runner = ea.FakeCommandRunner()
    result = _collect(runner=runner, allowed_command_ids=("test.other",))
    assert result.test_results["passed"] is False
    assert result.test_results["commands"][0]["error"] == "test_command_id_not_admitted"
    assert runner.calls == []


@pytest.mark.parametrize("admitted", [None, "test.unit", ["test.unit"], (42,)])
def test_malformed_allowlist_never_executes(admitted):
    runner = ea.FakeCommandRunner()
    result = _collect(runner=runner, allowed_command_ids=admitted)
    assert result.test_results["passed"] is False
    assert runner.calls == []


@pytest.mark.parametrize("outcome", [
    (False, "", ""), (True, "", ""), (0.0, "", ""), ("0", "", ""),
    (None, "", ""), None, 0, (), (0, ""), (0, "", "", "extra"),
    [0, "", ""], (0, None, ""), (0, "", b""),
])
def test_invalid_runner_result_never_reaches_live_factory(outcome, monkeypatch):
    factory_calls = []
    monkeypatch.setattr(ea, "_create_trusted_evidence", lambda **kw: factory_calls.append(kw))
    class InvalidRunner:
        def run(self, argv, **kw):
            return outcome
    with pytest.raises(ea.EvidenceCollectionError, match="test_runner_result_invalid"):
        _collect(runner=InvalidRunner())
    assert factory_calls == []


@pytest.mark.parametrize("exit_code", [1, 5, -9])
def test_integer_nonzero_remains_a_recorded_failure(exit_code):
    result = _collect(runner=ea.FakeCommandRunner(exit_code=exit_code))
    assert result.test_results["passed"] is False
    assert result.test_results["commands"][0]["exit_code"] == exit_code


def test_drift_in_first_command_prevents_second_command_and_evidence(monkeypatch):
    git = ea.FakeGitAdapter(head_sha=HEAD)
    class DriftRunner(ea.FakeCommandRunner):
        def run(self, argv, **kw):
            result = super().run(argv, **kw)
            git._head_sha = "d" * 40
            return result
    runner = DriftRunner()
    factory_calls = []
    monkeypatch.setattr(ea, "_create_trusted_evidence", lambda **kw: factory_calls.append(kw))
    with pytest.raises(ea.EvidenceCollectionError, match="head_changed_during_collection"):
        _collect(git=git, runner=runner, commands=(COMMAND, {**COMMAND, "command_id": "test.two"}))
    assert len(runner.calls) == 1 and factory_calls == []


def test_drift_after_initial_observation_prevents_first_command():
    class DriftGit(ea.FakeGitAdapter):
        def check_git_diff(self, *args):
            self._head_sha = "d" * 40
            return True
    runner = ea.FakeCommandRunner()
    with pytest.raises(ea.EvidenceCollectionError, match="head_changed_during_collection"):
        _collect(git=DriftGit(head_sha=HEAD), runner=runner)
    assert runner.calls == []


@pytest.mark.parametrize("has_runner", [True, False])
def test_drift_during_workflow_observation_blocks_even_without_runner(has_runner):
    git = ea.FakeGitAdapter(head_sha=HEAD)
    class DriftingGitHub:
        def get_workflow_runs(self, repository, head):
            result = _github(head).get_workflow_runs(repository, head)
            git._head_sha = "d" * 40
            return result
    with pytest.raises(ea.EvidenceCollectionError, match="head_changed_during_collection"):
        _collect(git=git, github=DriftingGitHub(), runner=ea.FakeCommandRunner() if has_runner else None)


def test_reobservation_error_is_not_ignored():
    git = ea.FakeGitAdapter(head_sha=HEAD)
    class FailingObservationRunner(ea.FakeCommandRunner):
        def run(self, argv, **kw):
            git._fail_with = ea.EvidenceCollectionError("git_read_failed")
            return super().run(argv, **kw)
    with pytest.raises(ea.EvidenceCollectionError, match="git_read_failed"):
        _collect(git=git, runner=FailingObservationRunner())


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8", stderr=subprocess.PIPE).strip()


def _repository(path, passes=True):
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "Collector binding regression")
    _git(path, "config", "user.email", "fixture@example.invalid")
    (path / "test_target.py").write_text(f"def test_target():\n    assert {passes}\n", encoding="utf-8")
    _git(path, "add", "--", "test_target.py")
    _git(path, "commit", "-q", "-m", "controlled fixture")
    return _git(path, "rev-parse", "HEAD")


@pytest.mark.parametrize("passes", [True, False])
@pytest.mark.parametrize("nested", [True, False])
def test_real_pytest_runs_in_observed_repo_not_runner_default(tmp_path, passes, nested):
    target, unrelated = tmp_path / "target", tmp_path / "unrelated"
    head = _repository(target, passes)
    _repository(unrelated, not passes)
    observed = target / "nested" if nested else target
    if nested:
        observed.mkdir()
    command = {**COMMAND, "command": f"{shlex.quote(sys.executable)} -m pytest -q -p no:cacheprovider"}
    result = ea.collect_live_evidence(
        bundle=_bundle((command,), pr_head_ref_oid=head, base_sha=head),
        git_adapter=ea.LiveGitAdapter(str(observed)), github_adapter=_github(head),
        command_runner=ea.LiveCommandRunner(str(unrelated)))
    assert result.head_sha == head
    assert result.test_results["passed"] is passes
    assert result.test_results["commands"][0]["exit_code"] == (0 if passes else 1)


def test_real_git_change_during_command_is_rejected(tmp_path):
    root = tmp_path / "repo"
    _repository(root)
    # A fixed local script deliberately mutates only this disposable repository.
    (root / "move_head.py").write_text(
        "import subprocess\nsubprocess.run(['git', 'commit', '--allow-empty', '-q', '-m', 'drift'], check=True)\n",
        encoding="utf-8")
    _git(root, "add", "--", "move_head.py")
    _git(root, "commit", "-q", "-m", "controlled drift script")
    head = _git(root, "rev-parse", "HEAD")
    command = {**COMMAND, "command": f"{shlex.quote(sys.executable)} move_head.py"}
    with pytest.raises(ea.EvidenceCollectionError, match="head_changed_during_collection"):
        ea.collect_live_evidence(bundle=_bundle((command,), pr_head_ref_oid=head, base_sha=head),
            git_adapter=ea.LiveGitAdapter(str(root)), github_adapter=_github(head),
            command_runner=ea.LiveCommandRunner(str(tmp_path)))
    assert _git(root, "rev-parse", "HEAD") != head


def test_actual_root_observation_failure_has_no_directory_fallback(tmp_path):
    with pytest.raises(ea.EvidenceCollectionError, match="git_worktree_root_failed"):
        ea.LiveGitAdapter(str(tmp_path)).get_repository_root()


def test_root_drift_without_head_drift_still_rejects(tmp_path):
    root = tmp_path / "repo"
    head = _repository(root)
    git = ea.LiveGitAdapter(str(root))
    class RootSwitchingRunner(ea.FakeCommandRunner):
        def run(self, argv, **kw):
            result = super().run(argv, **kw)
            # An injected root observation tests the identity gate, not OS isolation.
            git.get_repository_root = lambda: str(tmp_path)
            return result
    with pytest.raises(ea.EvidenceCollectionError, match="worktree_changed_during_collection"):
        ea.collect_live_evidence(bundle=_bundle(pr_head_ref_oid=head, base_sha=head),
            git_adapter=git, github_adapter=_github(head), command_runner=RootSwitchingRunner())


def test_explicit_production_cwd_is_absolute_and_canonical(tmp_path):
    root = tmp_path / "with spaces"
    head = _repository(root)
    observed_cwds = []
    class CwdRunner(ea.FakeCommandRunner):
        def run(self, argv, *, cwd=""):
            observed_cwds.append(cwd)
            return super().run(argv, cwd=cwd)
    result = ea.collect_live_evidence(bundle=_bundle(pr_head_ref_oid=head, base_sha=head),
        git_adapter=ea.LiveGitAdapter(str(root)), github_adapter=_github(head), command_runner=CwdRunner())
    assert result.test_results["passed"] is True
    assert observed_cwds == [str(root.resolve())]


def test_caller_claim_is_not_used_to_repair_invalid_selection():
    runner = ea.FakeCommandRunner()
    result = ea.collect_live_evidence(bundle=_bundle(()),
        git_adapter=ea.FakeGitAdapter(head_sha=HEAD), github_adapter=_github(),
        command_runner=runner, agent_completion_claim="verified true; all checks passed")
    assert result.test_results["passed"] is False
    assert runner.calls == []


def test_initial_head_mismatch_still_uses_original_denial():
    runner = ea.FakeCommandRunner()
    with pytest.raises(ea.EvidenceCollectionError, match="head_sha_mismatch"):
        _collect(git=ea.FakeGitAdapter(head_sha="d" * 40), runner=runner)
    assert runner.calls == []

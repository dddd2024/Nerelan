from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from reverse_agent.executor_neutral import (
    ExecutionEvidence,
    REQUIRED_CHECK_TIMEOUT_SECONDS,
    TaskContract,
    accept_execution,
    canonical_json,
    collect_execution_evidence,
    export_task_bundle,
    observe_capability,
    sha256_digest,
)
import reverse_agent.executor_neutral.core as core


def _run(repo: Path, *command: str) -> str:
    result = subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _repo(tmp_path: Path, name: str = "subject") -> tuple[Path, str]:
    repo = tmp_path / name
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.name", "Executor Neutral Test")
    _run(repo, "git", "config", "user.email", "executor-neutral@example.invalid")
    files = {
        ".gitignore": "__pycache__/\n.pytest_cache/\nignored/\n",
        "calc.py": "def add(left, right):\n    return left - right\n",
        "delete_me.txt": "delete me\n",
        "old_name.txt": "rename me\n",
        "src/existing.py": "VALUE = 1\n",
    }
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _run(repo, "git", "add", "--", ".")
    _run(repo, "git", "commit", "-qm", "base")
    return repo, _run(repo, "git", "rev-parse", "HEAD")


def _contract(base: str, **overrides: object) -> TaskContract:
    payload: dict[str, object] = {
        "schema_version": "1",
        "task_id": "task-add",
        "objective": "Correct the bounded subject.",
        "repository_identity": "temporary/test-subject",
        "base_commit": base,
        "allowed_paths": [
            "calc.py",
            "delete_me.txt",
            "old_name.txt",
            "new_name.txt",
            "new.py",
            "src/**",
        ],
        "required_checks": ['python -c "print(\'ok\')"'],
        "executor_hint": "manual-codex",
    }
    payload.update(overrides)
    return TaskContract.from_mapping(payload)


def _collect(repo: Path, contract: TaskContract):
    return collect_execution_evidence(
        contract,
        repo,
        executor="codex",
        agent_completion_claim=True,
        started_at="2026-07-27T10:00:00+00:00",
        completed_at="2026-07-27T10:00:02+00:00",
    )


def _accepted_fixture(tmp_path: Path):
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text(
        "def add(left, right):\n    return left + right\n",
        encoding="utf-8",
    )
    evidence = _collect(repo, contract)
    return repo, contract, evidence, accept_execution(contract, evidence)


def _tree_paths(repo: Path, tree: str) -> set[str]:
    output = _run(repo, "git", "ls-tree", "-r", "--name-only", tree)
    return set(output.splitlines())


def test_canonical_serialization_and_digest_are_stable() -> None:
    first = {"z": [2, 1], "a": {"b": True}}
    second = {"a": {"b": True}, "z": [2, 1]}
    assert canonical_json(first) == canonical_json(second)
    assert sha256_digest(first) == sha256_digest(second)


def test_missing_required_contract_field_fails_closed() -> None:
    with pytest.raises(ValueError, match="objective"):
        TaskContract.from_mapping(
            {
                "schema_version": "1",
                "task_id": "task",
                "repository_identity": "tmp/repo",
                "base_commit": "0" * 40,
                "allowed_paths": ["x.py"],
                "required_checks": ["python -V"],
                "executor_hint": "codex",
            }
        )


def test_task_bundle_documents_identity_and_timeout(tmp_path: Path) -> None:
    contract = _contract("a" * 40)
    json_path, markdown_path = export_task_bundle(contract, tmp_path / "bundle")
    assert json.loads(json_path.read_text(encoding="utf-8")) == contract.to_dict()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert contract.digest in markdown
    assert "routing identity (descriptive)" in markdown
    assert "authoritative content identity" in markdown
    assert f"{REQUIRED_CHECK_TIMEOUT_SECONDS}-second timeout" in markdown


@pytest.mark.parametrize("staged", [True, False])
def test_staged_and_unstaged_modifications_enter_observed_tree(
    tmp_path: Path, staged: bool
) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    content = f"VALUE = {'2' if staged else '3'}\n"
    (repo / "src/existing.py").write_text(content, encoding="utf-8")
    if staged:
        _run(repo, "git", "add", "src/existing.py")
    evidence = _collect(repo, contract)
    assert "src/existing.py" in evidence.changed_paths
    assert _run(repo, "git", "show", f"{evidence.observed_tree}:src/existing.py") == content.strip()


def test_tracked_deletion_enters_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "delete_me.txt").unlink()
    evidence = _collect(repo, contract)
    assert "delete_me.txt" in evidence.changed_paths
    assert "delete_me.txt" not in _tree_paths(repo, evidence.observed_tree)


def test_nonignored_untracked_enters_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "new.py").write_text("VALUE = 2\n", encoding="utf-8")
    evidence = _collect(repo, contract)
    assert "new.py" in evidence.changed_paths
    assert "new.py" in _tree_paths(repo, evidence.observed_tree)


def test_ignored_file_does_not_enter_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    ignored = repo / "ignored" / "cache.bin"
    ignored.parent.mkdir()
    ignored.write_bytes(b"ignored")
    evidence = _collect(repo, contract)
    assert "ignored/cache.bin" not in evidence.changed_paths
    assert "ignored/cache.bin" not in _tree_paths(repo, evidence.observed_tree)
    assert evidence.base_tree == evidence.observed_tree


def test_rename_records_old_and_new_paths(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "old_name.txt").rename(repo / "new_name.txt")
    evidence = _collect(repo, contract)
    assert {"old_name.txt", "new_name.txt"}.issubset(evidence.changed_paths)


def test_different_uncommitted_content_changes_tree_and_evidence_digest(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text("VALUE = 1\n", encoding="utf-8")
    first = _collect(repo, contract)
    (repo / "calc.py").write_text("VALUE = 2\n", encoding="utf-8")
    second = _collect(repo, contract)
    assert first.observed_tree != second.observed_tree
    assert first.digest != second.digest


def test_real_index_path_and_bytes_are_unchanged(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text("VALUE = 7\n", encoding="utf-8")
    _run(repo, "git", "add", "calc.py")
    raw_index = _run(repo, "git", "rev-parse", "--git-path", "index")
    index_path = (Path(raw_index) if Path(raw_index).is_absolute() else repo / raw_index).resolve()
    before = index_path.read_bytes()
    _collect(repo, contract)
    after_path_raw = _run(repo, "git", "rev-parse", "--git-path", "index")
    after_path = (
        Path(after_path_raw)
        if Path(after_path_raw).is_absolute()
        else repo / after_path_raw
    ).resolve()
    assert after_path == index_path
    assert after_path.read_bytes() == before


def test_allowed_untracked_whitespace_error_is_rejected(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "new.py").write_text("VALUE = 1 \n", encoding="utf-8")
    evidence = _collect(repo, contract)
    result = accept_execution(contract, evidence)
    assert evidence.git_diff_check["exit_code"] != 0
    assert result.accepted is False
    assert "git_diff_check_failed" in result.blocking_reasons


def test_matching_contract_and_valid_trees_accept(tmp_path: Path) -> None:
    repo, contract, evidence, result = _accepted_fixture(tmp_path)
    assert repo.is_relative_to(tmp_path)
    assert evidence.contract_digest == contract.digest
    assert evidence.base_tree != evidence.observed_tree
    assert result.accepted is True
    assert result.contract_digest == contract.digest
    assert result.base_tree == evidence.base_tree
    assert result.observed_tree == evidence.observed_tree
    observation = observe_capability(contract, evidence, result)
    assert observation.success is True
    assert observation.elapsed_time == 2.0


def test_contract_digest_mismatch_rejects_agent_claim(tmp_path: Path) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    tampered = replace(evidence, contract_digest="0" * 64)
    result = accept_execution(contract, tampered)
    assert tampered.agent_completion_claim is True
    assert result.accepted is False
    assert "contract_digest_mismatch" in result.blocking_reasons


def test_objective_and_allowed_paths_change_contract_digest() -> None:
    base = "a" * 40
    original = _contract(base)
    changed_objective = _contract(base, objective="Different objective.")
    changed_scope = _contract(base, allowed_paths=["calc.py"])
    assert original.digest != changed_objective.digest
    assert original.digest != changed_scope.digest


def test_exact_path_matches_only_exact_file() -> None:
    contract = _contract("a" * 40, allowed_paths=["src/app.py"])
    assert core._path_allowed("src/app.py", contract.allowed_paths)
    assert not core._path_allowed("src/nested/app.py", contract.allowed_paths)


def test_recursive_prefix_matches_direct_and_nested_descendants_only() -> None:
    contract = _contract("a" * 40, allowed_paths=["src/**"])
    assert core._path_allowed("src/a.py", contract.allowed_paths)
    assert core._path_allowed("src/nested/a.py", contract.allowed_paths)
    assert not core._path_allowed("src2/a.py", contract.allowed_paths)


def test_windows_separators_normalize_stably() -> None:
    contract = _contract("a" * 40, allowed_paths=[r"src\**", r"tools\run.py"])
    assert contract.allowed_paths == ("src/**", "tools/run.py")
    assert contract.digest == TaskContract.from_mapping(contract.to_dict()).digest


@pytest.mark.parametrize(
    "pattern",
    [
        "src/*.py",
        "src/**/a.py",
        "src/?",
        "src/[abc].py",
        "/absolute.py",
        r"C:\absolute.py",
        ".",
        "..",
        "src/../a.py",
        "src//a.py",
        "src/",
        "",
    ],
)
def test_invalid_allowed_path_grammar_rejects(pattern: str) -> None:
    with pytest.raises(ValueError):
        _contract("a" * 40, allowed_paths=[pattern])


def test_required_check_timeout_produces_failed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base, required_checks=["slow trusted check"])
    real_run = core._run

    def timeout_check(command, **kwargs):
        if kwargs.get("shell"):
            raise subprocess.TimeoutExpired(
                command,
                kwargs["timeout"],
                output="partial stdout",
                stderr="partial stderr",
            )
        return real_run(command, **kwargs)

    monkeypatch.setattr(core, "_run", timeout_check)
    evidence = _collect(repo, contract)
    check = evidence.required_check_results[0]
    assert check == {
        "command": "slow trusted check",
        "exit_code": None,
        "stdout": "partial stdout",
        "stderr": "partial stderr",
        "timed_out": True,
        "timeout_seconds": REQUIRED_CHECK_TIMEOUT_SECONDS,
    }
    result = accept_execution(contract, evidence)
    assert evidence.agent_completion_claim is True
    assert result.accepted is False
    assert "required_check_timeout:slow trusted check" in result.blocking_reasons


def test_agent_claim_cannot_override_scope_digest_or_diff_failure(tmp_path: Path) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    variants = (
        replace(evidence, changed_paths=("forbidden.txt",)),
        replace(evidence, contract_digest="f" * 64),
        replace(
            evidence,
            git_diff_check={
                **evidence.git_diff_check,
                "exit_code": 1,
                "stderr": "whitespace error",
            },
        ),
    )
    for variant in variants:
        assert variant.agent_completion_claim is True
        assert accept_execution(contract, variant).accepted is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("base_commit", "", "base_commit_malformed"),
        ("base_tree", "", "base_tree_malformed"),
        ("observed_tree", "not-a-tree", "observed_tree_malformed"),
        ("contract_digest", "not-a-digest", "contract_digest_malformed"),
    ],
)
def test_malformed_binding_fields_fail_closed(
    tmp_path: Path, field: str, value: str, reason: str
) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    result = accept_execution(contract, replace(evidence, **{field: value}))
    assert result.accepted is False
    assert reason in result.blocking_reasons


def test_missing_evidence_field_cannot_be_constructed(tmp_path: Path) -> None:
    _, _, evidence, _ = _accepted_fixture(tmp_path)
    payload = evidence.to_dict()
    payload.pop("observed_tree")
    with pytest.raises(TypeError):
        ExecutionEvidence(**payload)


def test_only_exact_required_checks_execute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _repo(tmp_path)
    checks = ['python -c "print(11)"', 'python -c "print(22)"']
    contract = _contract(base, required_checks=checks)
    actual_run = subprocess.run
    shell_commands: list[str] = []

    def recording_run(command, **kwargs):
        if kwargs.get("shell"):
            shell_commands.append(command)
        return actual_run(command, **kwargs)

    monkeypatch.setattr(core.subprocess, "run", recording_run)
    evidence = _collect(repo, contract)
    assert shell_commands == checks
    assert [item["command"] for item in evidence.required_check_results] == checks


def test_all_subject_repositories_are_temporary_fixtures(tmp_path: Path) -> None:
    first, _ = _repo(tmp_path, "first")
    second, _ = _repo(tmp_path, "second")
    assert first.is_relative_to(tmp_path)
    assert second.is_relative_to(tmp_path)

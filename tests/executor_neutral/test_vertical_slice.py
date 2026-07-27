from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from reverse_agent.executor_neutral import (
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


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "subject"
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.name", "Executor Neutral Test")
    _run(repo, "git", "config", "user.email", "executor-neutral@example.invalid")
    (repo / "calc.py").write_text("def add(left, right):\n    return left - right\n", encoding="utf-8")
    (repo / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    _run(repo, "git", "add", ".gitignore", "calc.py", "test_calc.py")
    _run(repo, "git", "commit", "-qm", "base")
    return repo, _run(repo, "git", "rev-parse", "HEAD")


def _contract(base: str, **overrides: object) -> TaskContract:
    payload: dict[str, object] = {
        "schema_version": "1",
        "task_id": "task-add",
        "objective": "Correct the add function.",
        "repository_identity": "temporary/test-subject",
        "base_commit": base,
        "allowed_paths": ["calc.py"],
        "required_checks": ['python -m pytest -q'],
        "executor_hint": "manual-codex",
    }
    payload.update(overrides)
    return TaskContract.from_mapping(payload)


def _accepted_fixture(tmp_path: Path):
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    _run(repo, "git", "add", "calc.py")
    evidence = collect_execution_evidence(
        contract,
        repo,
        executor="codex",
        agent_completion_claim=True,
        started_at="2026-07-27T10:00:00+00:00",
        completed_at="2026-07-27T10:00:02+00:00",
    )
    return repo, contract, evidence, accept_execution(contract, evidence)


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


def test_task_bundle_is_deterministic(tmp_path: Path) -> None:
    contract = _contract("a" * 40)
    json_path, markdown_path = export_task_bundle(contract, tmp_path / "bundle")
    assert json.loads(json_path.read_text(encoding="utf-8")) == contract.to_dict()
    assert contract.digest in markdown_path.read_text(encoding="utf-8")


def test_changed_path_outside_scope_rejects(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base, required_checks=['python -c "print(1)"'])
    (repo / "forbidden.txt").write_text("outside\n", encoding="utf-8")
    evidence = collect_execution_evidence(
        contract, repo, executor="codex", agent_completion_claim=True
    )
    result = accept_execution(contract, evidence)
    assert result.accepted is False
    assert result.scope_result == "FAIL"
    assert "changed_path_outside_allowed_scope:forbidden.txt" in result.blocking_reasons


def test_failed_required_check_rejects_even_with_agent_claim(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base, required_checks=['python -c "raise SystemExit(3)"'])
    (repo / "calc.py").write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    _run(repo, "git", "add", "calc.py")
    evidence = collect_execution_evidence(
        contract, repo, executor="codex", agent_completion_claim=True
    )
    result = accept_execution(contract, evidence)
    assert evidence.agent_completion_claim is True
    assert result.accepted is False
    assert result.blocking_reasons == (
        'required_check_failed:python -c "raise SystemExit(3)"',
    )


def test_all_valid_git_and_check_evidence_accepts(tmp_path: Path) -> None:
    repo, contract, evidence, result = _accepted_fixture(tmp_path)
    assert repo.is_relative_to(tmp_path)
    assert evidence.changed_paths == ("calc.py",)
    assert evidence.git_diff_check["exit_code"] == 0
    assert result.accepted is True
    assert result.blocking_reasons == ()
    observation = observe_capability(contract, evidence, result)
    assert observation.success is True
    assert observation.elapsed_time == 2.0
    assert observation.failure_class is None


def test_evidence_mutation_changes_digest(tmp_path: Path) -> None:
    _, _, evidence, _ = _accepted_fixture(tmp_path)
    mutated = replace(evidence, agent_completion_claim=not evidence.agent_completion_claim)
    assert evidence.digest != mutated.digest


def test_required_check_evidence_mismatch_fails_closed(tmp_path: Path) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    missing = replace(evidence, required_check_results=())
    result = accept_execution(contract, missing)
    assert result.accepted is False
    assert "required_check_evidence_mismatch" in result.blocking_reasons


def test_only_exact_required_checks_execute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base = _repo(tmp_path)
    checks = ['python -c "print(11)"', 'python -c "print(22)"']
    contract = _contract(base, required_checks=checks)
    (repo / "calc.py").write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    _run(repo, "git", "add", "calc.py")
    actual_run = subprocess.run
    shell_commands: list[str] = []

    def recording_run(command, **kwargs):
        if kwargs.get("shell"):
            shell_commands.append(command)
        return actual_run(command, **kwargs)

    monkeypatch.setattr(core.subprocess, "run", recording_run)
    evidence = collect_execution_evidence(
        contract, repo, executor="codex", agent_completion_claim=False
    )
    assert shell_commands == checks
    assert [item["command"] for item in evidence.required_check_results] == checks


def test_all_subject_repositories_are_temporary_fixtures(tmp_path: Path) -> None:
    repo, _ = _repo(tmp_path)
    assert repo.is_relative_to(tmp_path)
    assert ".git" in {item.name for item in repo.iterdir()}

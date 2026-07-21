"""Phase B: Trusted Command Runner.

The trusted runner is the single entry point for producing execution evidence.
It reads the command from the plan by ``command_id`` (callers cannot supply
an alternative command string), launches the subprocess itself, captures raw
stdout/stderr, reads real UTC time and Git HEAD before/after, computes
mutated paths via ``git diff``, persists raw evidence content-addressably,
and atomically appends the execution record.

Caller-supplied execution facts (started_at, observed_at, head_before,
head_after, stdout_digest, stderr_digest, raw_stdout, raw_stderr, command,
authority_origin) are forbidden (F2).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from reverse_agent.control_plane.evidence_recorder import (
    TrustedCommandRunner,
    _sha256_digest,
)
from reverse_agent.control_plane.models import (
    BootstrapState,
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


def _plan_with_command(
    *,
    command_id: str = "status.git_head",
    command: str = "git rev-parse HEAD",
    allowed_mutated_paths: tuple[str, ...] = (),
    produced_artifacts: tuple[str, ...] = (),
    required: bool = True,
    authority_origin: str = "normal_plan",
) -> TransitionCommandPlan:
    return TransitionCommandPlan(
        decision_id="decision_trusted",
        round_id="round_trusted",
        commands=(
            TransitionCommand(
                command=command,
                phase="status",
                required=required,
                expected_exit_codes=(0,),
                execution_surface="local",
                operations=("repository_observation",),
                command_id=command_id,
                authority_origin=authority_origin,
                allowed_mutated_paths=allowed_mutated_paths,
                produced_artifacts=produced_artifacts,
            ),
        ),
    )


def _init_repo(repo_root: Path) -> str:
    """Initialize a real git repo and return the HEAD SHA."""

    subprocess.run(["git", "init", "-q"], cwd=str(repo_root), check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_root),
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(repo_root),
        check=True,
    )
    (repo_root / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(repo_root), check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=str(repo_root), check=True
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# TrustedCommandRunner: the runner executes commands itself
# ---------------------------------------------------------------------------


def test_runner_reads_command_from_plan_by_id(tmp_path: Path) -> None:
    """Runner resolves the command string from the plan, not the caller."""

    _init_repo(tmp_path)
    plan = _plan_with_command(
        command_id="status.git_head",
        command="git rev-parse HEAD",
    )
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")

    assert record.command == "git rev-parse HEAD"
    assert record.command_id == "status.git_head"
    assert record.exit_code == 0


def test_runner_rejects_unknown_command_id(tmp_path: Path) -> None:
    """Unknown command_id is rejected before any subprocess is launched."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    with pytest.raises(KeyError, match="unknown_command_id"):
        runner.run_command(command_id="nonexistent.command")


def test_runner_does_not_accept_caller_supplied_command(tmp_path: Path) -> None:
    """The runner's run_command signature must not accept a command parameter."""

    import inspect

    sig = inspect.signature(TrustedCommandRunner.run_command)
    # The runner must NOT accept 'command', 'raw_stdout', 'raw_stderr',
    # 'started_at', 'observed_at', 'head_before', 'head_after',
    # 'stdout_digest', 'stderr_digest', or 'authority_origin'.
    forbidden_params = {
        "command",
        "raw_stdout",
        "raw_stderr",
        "started_at",
        "observed_at",
        "head_before",
        "head_after",
        "stdout_digest",
        "stderr_digest",
        "authority_origin",
    }
    actual_params = set(sig.parameters.keys()) - {"self"}
    forbidden_present = forbidden_params & actual_params
    assert not forbidden_present, (
        f"run_command must not accept caller-supplied execution facts: {forbidden_present}"
    )


def test_runner_captures_real_stdout_and_computes_digest(tmp_path: Path) -> None:
    """stdout_digest is computed from real subprocess output."""

    _init_repo(tmp_path)
    plan = _plan_with_command(
        command_id="status.git_head",
        command="git rev-parse HEAD",
    )
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")

    # The real HEAD SHA is 40 hex chars; stdout is the SHA + newline.
    expected_raw = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    ).stdout
    expected_digest = _sha256_digest(expected_raw)
    assert record.stdout_digest == expected_digest


def test_runner_persists_raw_evidence_content_addressably(tmp_path: Path) -> None:
    """Raw stdout/stderr are persisted to evidence/<record_id>/."""

    _init_repo(tmp_path)
    plan = _plan_with_command(
        command_id="status.git_head",
        command="git rev-parse HEAD",
    )
    evidence_dir = tmp_path / "evidence"
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=evidence_dir,
    )

    record = runner.run_command(command_id="status.git_head")

    # Raw evidence must exist on disk.
    record_evidence_dir = evidence_dir / record.record_id
    assert (record_evidence_dir / "stdout.bin").exists()
    assert (record_evidence_dir / "stderr.bin").exists()
    assert (record_evidence_dir / "metadata.json").exists()

    # The persisted stdout must match the digest.
    raw_stdout = (record_evidence_dir / "stdout.bin").read_bytes()
    assert _sha256_digest(raw_stdout) == record.stdout_digest


def test_runner_reads_real_git_head_before_and_after(tmp_path: Path) -> None:
    """head_before and head_after are real 40-char SHAs from git."""

    _init_repo(tmp_path)
    plan = _plan_with_command(
        command_id="status.git_head",
        command="git rev-parse HEAD",
    )
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")

    assert len(record.head_before) == 40
    assert len(record.head_after) == 40
    assert all(c in "0123456789abcdef" for c in record.head_before)
    assert all(c in "0123456789abcdef" for c in record.head_after)


def test_runner_computes_mutated_paths_from_git_diff(tmp_path: Path) -> None:
    """mutated_paths are derived from git diff, not caller-supplied."""

    _init_repo(tmp_path)
    # A command that creates a new file.
    plan = _plan_with_command(
        command_id="test.create_file",
        command="python -c \"open('new_file.txt', 'w').write('hello')\"",
        allowed_mutated_paths=("new_file.txt",),
    )
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="test.create_file")

    assert "new_file.txt" in record.mutated_paths


def test_runner_stamps_real_utc_timestamps(tmp_path: Path) -> None:
    """started_at and observed_at are real UTC times from the machine clock."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")

    # Times must be RFC3339 UTC with trailing Z.
    assert record.started_at.endswith("Z")
    assert record.observed_at.endswith("Z")
    assert "T" in record.started_at
    assert "T" in record.observed_at
    # started_at must not be after observed_at.
    assert record.started_at <= record.observed_at


def test_runner_assigns_unique_record_id(tmp_path: Path) -> None:
    """Each record gets a unique record_id."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record1 = runner.run_command(command_id="status.git_head")
    record2 = runner.run_command(command_id="status.git_head")

    assert record1.record_id != record2.record_id
    assert len(record1.record_id) > 0


def test_runner_binds_plan_digest_to_record(tmp_path: Path) -> None:
    """Each record carries the plan_digest it was authorized by."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")

    assert record.plan_digest.startswith("sha256:")
    assert len(record.plan_digest) == 7 + 64  # "sha256:" + 64 hex


def test_runner_appends_to_execution_log(tmp_path: Path) -> None:
    """Runner appends the record to execution_log.json atomically."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    log_path = tmp_path / "execution_log.json"
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
        execution_log_path=log_path,
    )

    runner.run_command(command_id="status.git_head")

    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["schema_version"] == 1
    assert len(log["commands"]) == 1
    assert log["commands"][0]["command_id"] == "status.git_head"


def test_runner_rejects_caller_supplied_authority_origin(tmp_path: Path) -> None:
    """authority_origin is derived from the plan entry, not the caller."""

    import inspect

    sig = inspect.signature(TrustedCommandRunner.run_command)
    actual_params = set(sig.parameters.keys()) - {"self"}
    assert "authority_origin" not in actual_params


def test_runner_uses_plan_entry_authority_origin(tmp_path: Path) -> None:
    """The record's authority_origin comes from the plan entry."""

    _init_repo(tmp_path)
    plan = _plan_with_command(authority_origin="normal_plan")
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="status.git_head")
    assert record.authority_origin == "normal_plan"


def test_runner_captures_nonzero_exit_code(tmp_path: Path) -> None:
    """The runner records the real exit code, even on failure."""

    _init_repo(tmp_path)
    plan = _plan_with_command(
        command_id="test.failing",
        command="python -c \"import sys; sys.exit(1)\"",
    )
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )

    record = runner.run_command(command_id="test.failing")
    assert record.exit_code == 1


def test_runner_metadata_includes_raw_evidence_paths(tmp_path: Path) -> None:
    """metadata.json records the raw evidence paths and digests."""

    _init_repo(tmp_path)
    plan = _plan_with_command()
    evidence_dir = tmp_path / "evidence"
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=evidence_dir,
    )

    record = runner.run_command(command_id="status.git_head")

    metadata_path = evidence_dir / record.record_id / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert "stdout_path" in metadata
    assert "stderr_path" in metadata
    assert "stdout_digest" in metadata
    assert "stderr_digest" in metadata
    assert metadata["stdout_digest"] == record.stdout_digest

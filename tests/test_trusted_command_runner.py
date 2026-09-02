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
import shutil
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    runner = TrustedCommandRunner.for_test(
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
    assert (evidence_dir / ".gitattributes").read_text(encoding="utf-8") == "*.bin binary\n"


# ---------------------------------------------------------------------------
# F4: TrustedExecutionContext.from_state_dir — the ONLY production entry point
# ---------------------------------------------------------------------------


def _write_state_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_trusted",
    round_id: str = "round_trusted",
    branch: str | None = None,
    base_sha: str | None = None,
    allowed_commands: list[dict] | None = None,
    bootstrap_exception_commands: list[str] | None = None,
) -> None:
    """Write a structured Decision packet + committed command plan."""

    import json as _json

    if allowed_commands is None:
        allowed_commands = [
            {
                "command_id": "status.git_head",
                "command": "git rev-parse HEAD",
                "phase": "status",
                "required": True,
                "required_evidence_source": "local_command_evidence",
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["repository_observation"],
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": [],
                "produced_artifacts": [],
            },
        ]
    repo_root = state_dir.parent
    branch = branch or subprocess.run(
        ["git", "branch", "--show-current"], cwd=str(repo_root),
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    base_sha = base_sha or subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo_root),
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    contract = {
        "transition_kernel_required": True,
        "required_branch": branch,
        "activation_base_sha": base_sha,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": bootstrap_exception_commands or [],
        "allowed_commands": allowed_commands,
        "allowed_mutated_paths": ["reverse_agent/control_plane/**"],
        "forbidden_mutated_paths": ["frontend/**"],
        "capability_policy": {
            "network_access_default_allowed": False,
            "local_network_exceptions": [],
            "ci_network_exceptions": [],
        },
        "path_risk_floor": [],
        "runner_managed_artifact_paths": [
            "project_state/gates/execution_log.json",
            "project_state/gates/evidence/**",
        ],
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + _json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": round_id,
                "status": "APPROVED",
                "mainline": "engineering_branch",
                "skill_profiles": ["reverse-agent-iteration@v2"],
            }
        )
        + "\n```\n\n```json decision_contract\n"
        + _json.dumps(contract)
        + "\n```\n",
        encoding="utf-8",
    )
    gates = state_dir / "gates"
    gates.mkdir(parents=True, exist_ok=True)
    # Write committed command plan matching the decision.
    from reverse_agent.control_plane.legacy_adapter import (
        build_transition_command_plan,
    )
    from reverse_agent.control_plane.models import TransitionDecision

    decision = TransitionDecision(
        decision_id=decision_id,
        round_id=round_id,
        status="APPROVED",
        mainline="engineering_branch",
        skill_profiles=("reverse-agent-iteration@v2",),
    )
    plan = build_transition_command_plan(decision, contract)
    (gates / "command_plan.json").write_text(
        _json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (gates / "transition_preflight_result.json").write_text(
        _json.dumps(
            {
                "schema_version": 1,
                "gate_name": "transition-preflight",
                "gate_status": "PRE_EXECUTION_AUTHORIZED",
                "decision_id": decision_id,
                "round_id": round_id,
                "checks": [
                    {"name": name, "status": "PASS", "detail": "test fixture"}
                    for name in (
                        "decision_identity",
                        "round_identity",
                        "decision_approved",
                        "branch_identity",
                        "base_ancestry",
                        "decision_ancestry",
                        "command_plan_identity",
                        "command_plan_contract",
                        "capability_policy_enforced",
                        "network_policy_enforced",
                        "path_risk_floor_enforced",
                    )
                ],
                "blocking_reasons": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_trusted_execution_context_from_state_dir_loads_authority(tmp_path: Path) -> None:
    """F4: from_state_dir reads active Decision + committed plan and constructs a context."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)

    assert context.decision_id == "decision_trusted"
    assert context.round_id == "round_trusted"
    assert context.plan_digest.startswith("sha256:")
    # The context must NOT accept a caller-supplied plan.
    import inspect

    sig = inspect.signature(TrustedExecutionContext.from_state_dir)
    params = set(sig.parameters.keys()) - {"cls"}
    forbidden = {"plan", "command", "head_sha", "timestamp", "authority_origin"}
    assert not (forbidden & params), f"from_state_dir must not accept: {forbidden & params}"


def test_trusted_execution_context_rejects_plan_mismatch(tmp_path: Path) -> None:
    """F4: from_state_dir must reject a committed plan that diverges from the Decision."""

    import json as _json

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)
    # Tamper with the committed plan so it no longer matches the Decision.
    plan_path = state_dir / "gates" / "command_plan.json"
    payload = _json.loads(plan_path.read_text(encoding="utf-8"))
    payload["commands"][0]["command"] = "git rev-parse HEAD --tampered"
    plan_path.write_text(_json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="plan_digest_mismatch|plan_mismatch"):
        TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)


def test_injected_plan_runner_is_explicitly_test_only(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    runner = TrustedCommandRunner(
        repo_root=tmp_path,
        plan=_plan_with_command(),
        evidence_dir=tmp_path / "evidence",
    )
    with pytest.raises(RuntimeError, match="injected_plan_runner_disabled"):
        runner.run_command(command_id="status.git_head")


# ---------------------------------------------------------------------------
# F5: authorize_before_execute — the pre-execution hard gate
# ---------------------------------------------------------------------------


def test_authorize_before_execute_returns_authorized_for_valid_command(tmp_path: Path) -> None:
    """F5: a valid command_id with matching identity returns AUTHORIZED."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute("status.git_head")

    assert result.status == "AUTHORIZED"
    assert result.reasons == ()


def test_authorize_before_execute_blocks_unknown_command_id(tmp_path: Path) -> None:
    """F5: an unknown command_id must be BLOCKED."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute("nonexistent.command")

    assert result.status == "BLOCKED"
    assert any("unknown_command_id" in r for r in result.reasons)


def test_authorize_before_execute_blocks_stale_or_failed_preflight(tmp_path: Path) -> None:
    """Authorization rechecks the persisted preflight contract, not status alone."""

    from reverse_agent.control_plane.evidence_recorder import TrustedExecutionContext

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    preflight_path = state_dir / "gates" / "transition_preflight_result.json"
    payload = json.loads(preflight_path.read_text(encoding="utf-8"))
    payload["checks"][0]["status"] = "FAIL"
    preflight_path.write_text(json.dumps(payload), encoding="utf-8")

    result = context.authorize_before_execute("status.git_head")
    assert result.status == "BLOCKED"
    assert "required_preflight_not_authorized" in result.reasons


def test_authorize_before_execute_blocks_non_local_surface(tmp_path: Path) -> None:
    from reverse_agent.control_plane.evidence_recorder import TrustedExecutionContext

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": "ci.test",
                "command": "python -m pytest -q",
                "phase": "test",
                "required": False,
                "required_evidence_source": "ci_check_attestation",
                "expected_exit_codes": [0],
                "execution_surface": "ci_only",
                "operations": ["integration_test"],
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": [],
                "produced_artifacts": [],
            }
        ],
    )
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute("ci.test")
    assert result.status == "BLOCKED"
    assert any("execution_surface_mismatch" in reason for reason in result.reasons)


@pytest.mark.parametrize(
    "surface",
    ["github_control_plane", "ci_only", "remote_observation"],
)
def test_trusted_execution_refuses_non_subprocess_surfaces(tmp_path: Path, surface: str) -> None:
    """G2-2: github_control_plane, ci_only and remote_observation must never be
    subprocess-executed by a trusted runner."""

    from reverse_agent.control_plane.evidence_recorder import TrustedExecutionContext

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": f"surface.{surface}",
                "command": "python -c \"print('should not run')\"",
                "phase": "status",
                "required": False,
                "required_evidence_source": "local_command_evidence",
                "expected_exit_codes": [0],
                "execution_surface": surface,
                "operations": ["repository_observation"],
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": [],
                "produced_artifacts": [],
            }
        ],
    )
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute(f"surface.{surface}")
    assert result.status == "BLOCKED"
    assert any("execution_surface_mismatch" in reason for reason in result.reasons)
    with pytest.raises(RuntimeError, match="command_blocked"):
        context.run_command(f"surface.{surface}")


@pytest.mark.parametrize(
    "surface",
    ["trusted_worker", "user_local", "local"],
)
def test_trusted_execution_allows_subprocess_surfaces(tmp_path: Path, surface: str) -> None:
    """G2-2: trusted_worker, user_local and legacy local are the only
    subprocess-executable surfaces for the trusted runner."""

    from reverse_agent.control_plane.evidence_recorder import TrustedExecutionContext

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    operations = ["repository_observation"]
    if surface == "user_local":
        operations.append("machine_specific_execution")
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": f"surface.{surface}",
                "command": "git rev-parse HEAD",
                "phase": "status",
                "required": False,
                "required_evidence_source": "local_command_evidence",
                "expected_exit_codes": [0],
                "execution_surface": surface,
                "operations": operations,
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": [],
                "produced_artifacts": [],
            }
        ],
    )
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute(f"surface.{surface}")
    assert result.status == "AUTHORIZED", result.reasons
    record = context.run_command(f"surface.{surface}")
    assert record.execution_surface == surface


def test_trusted_execution_blocks_user_local_without_machine_specific(tmp_path: Path) -> None:
    """G2-1: a user_local command without the explicit machine_specific_execution
    declaration must FAIL CLOSED. The trusted authority gate (which rebuilds the
    plan from the active Decision) must refuse to construct authority for such a
    command, and the runner-level gate must refuse to execute it."""

    import json as _json

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedCommandRunner,
        TrustedExecutionContext,
    )
    from reverse_agent.control_plane.models import TransitionCommand, TransitionCommandPlan

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    decision_id = "decision_trusted"
    round_id = "round_trusted"
    gates = state_dir / "gates"
    gates.mkdir(parents=True)
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + _json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": round_id,
                "status": "APPROVED",
                "mainline": "engineering_branch",
                "skill_profiles": ["reverse-agent-iteration@v2"],
            }
        )
        + "\n```\n\n```json decision_contract\n"
        + _json.dumps(
            {
                "transition_kernel_required": True,
                "required_branch": "main",
                "activation_base_sha": subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=str(tmp_path),
                    capture_output=True, text=True, check=True,
                ).stdout.strip(),
                "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
                "bootstrap_exception_commands": [],
                "allowed_commands": [
                    {
                        "command_id": "user_local.undeclared",
                        "command": "git rev-parse HEAD",
                        "phase": "status",
                        "required": False,
                        "required_evidence_source": "local_command_evidence",
                        "expected_exit_codes": [0],
                        "execution_surface": "user_local",
                        "operations": ["repository_observation"],
                        "network_access": False,
                        "authority_origin": "normal_plan",
                        "allowed_mutated_paths": [],
                        "produced_artifacts": [],
                    }
                ],
                "allowed_mutated_paths": ["reverse_agent/control_plane/**"],
                "forbidden_mutated_paths": ["frontend/**"],
                "capability_policy": {
                    "network_access_default_allowed": False,
                    "local_network_exceptions": [],
                    "ci_network_exceptions": [],
                },
                "path_risk_floor": [],
            }
        )
        + "\n```\n",
        encoding="utf-8",
    )
    # The authority gate rebuilds the plan from the active Decision and must
    # fail closed on a user_local command lacking the declaration.
    (gates / "command_plan.json").write_text(
        _json.dumps(
            {
                "schema_version": 1,
                "decision_id": decision_id,
                "round_id": round_id,
                "commands": [
                    {
                        "command": "git rev-parse HEAD",
                        "phase": "status",
                        "required": False,
                        "required_evidence_source": "local_command_evidence",
                        "expected_exit_codes": [0],
                        "execution_surface": "user_local",
                        "operations": ["repository_observation"],
                        "network_access": False,
                        "authority_origin": "normal_plan",
                        "command_id": "user_local.undeclared",
                        "allowed_mutated_paths": [],
                        "produced_artifacts": [],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="user_local_requires_machine_specific_execution"):
        TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)

    # The runner-level gate must refuse to subprocess-execute a user_local
    # command even when a plan is injected directly (defense in depth).
    plan = TransitionCommandPlan(
        decision_id=decision_id,
        round_id=round_id,
        commands=(
            TransitionCommand(
                command="git rev-parse HEAD",
                phase="status",
                required=False,
                expected_exit_codes=(0,),
                execution_surface="user_local",
                operations=("repository_observation",),
                command_id="user_local.undeclared",
                authority_origin="normal_plan",
            ),
        ),
    )
    runner = TrustedCommandRunner.for_test(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )
    with pytest.raises(ValueError, match="user_local_requires_machine_specific_execution"):
        runner.run_command(command_id="user_local.undeclared")


def test_trusted_command_runner_refuses_non_subprocess_surface(tmp_path: Path) -> None:
    """G2-2: the injected TrustedCommandRunner also refuses to subprocess-
    execute github_control_plane/ci_only/remote_observation commands."""

    _init_repo(tmp_path)
    plan = TransitionCommandPlan(
        decision_id="decision_trusted",
        round_id="round_trusted",
        commands=(
            TransitionCommand(
                command="git rev-parse HEAD",
                phase="status",
                required=False,
                expected_exit_codes=(0,),
                execution_surface="github_control_plane",
                operations=("pr_create",),
                command_id="gh.create_pr",
                authority_origin="normal_plan",
            ),
        ),
    )
    runner = TrustedCommandRunner.for_test(
        repo_root=tmp_path,
        plan=plan,
        evidence_dir=tmp_path / "evidence",
    )
    with pytest.raises(ValueError, match="execution_surface_mismatch"):
        runner.run_command(command_id="gh.create_pr")


def test_authorize_before_execute_blocks_allowed_only_after_validation(tmp_path: Path) -> None:
    """F5: a command with allowed_only_after_validation must BLOCKED until the seal is LOCAL_RECONCILED."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": "publication.push_branch",
                "command": "git push origin codex/example-v1",
                "phase": "publication",
                "required": False,
                "required_evidence_source": "repository_state_attestation",
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["push", "network_access"],
                "network_access": True,
                "allowed_only_after_validation": True,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": [],
                "produced_artifacts": [],
            },
        ],
    )

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    result = context.authorize_before_execute("publication.push_branch")

    assert result.status == "BLOCKED"
    assert any("allowed_only_after_validation" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# F6: Atomic evidence journal — cross-round rejection, lock, monotonic sequence
# ---------------------------------------------------------------------------


def test_journal_rejects_cross_round_append(tmp_path: Path) -> None:
    """F6: appending to a log that belongs to a different Decision must be rejected."""

    import json as _json

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir, decision_id="decision_new", round_id="round_new")
    # Write a stale execution log belonging to an OLD decision.
    gates = state_dir / "gates"
    gates.mkdir(parents=True, exist_ok=True)
    stale_log = {
        "schema_version": 1,
        "artifact_name": "execution_log.json",
        "gate_name": "transition-trusted-runner",
        "gate_status": "PASSED",
        "decision_id": "decision_OLD",
        "round_id": "round_OLD",
        "generated_at": "2026-01-01T00:00:00Z",
        "source": "trusted_command_runner",
        "commands": [],
    }
    (gates / "execution_log.json").write_text(
        _json.dumps(stale_log, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    with pytest.raises(ValueError, match="cross_round_log|stale_log|decision_id_mismatch"):
        context.run_command("status.git_head")


def test_journal_appends_monotonically_under_lock(tmp_path: Path) -> None:
    """F6: two sequential records get monotonically increasing sequence numbers."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    record1 = context.run_command("status.git_head")
    record2 = context.run_command("status.git_head")

    assert record2.sequence == record1.sequence + 1
    assert record1.record_id != record2.record_id


def test_journal_log_header_binds_plan_digest(tmp_path: Path) -> None:
    """F6: the execution log header must carry the current plan digest."""

    import json as _json

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    context.run_command("status.git_head")

    log = _json.loads((state_dir / "gates" / "execution_log.json").read_text(encoding="utf-8"))
    assert log["plan_digest"] == context.plan_digest
    assert log["decision_id"] == context.decision_id
    assert log["round_id"] == context.round_id


def test_replay_bootstrap_evidence_from_head_is_verified_and_resequenced(
    tmp_path: Path,
) -> None:
    """Expired bootstrap is replayed from Git blobs, never rerun or supplied."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
        _plan_digest,
    )

    initial_head = _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    bootstrap_command = "python -c \"print('bootstrap')\""
    _write_state_decision(
        state_dir,
        bootstrap_exception_commands=[bootstrap_command],
    )
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    bootstrap_entry = next(entry for entry in context.plan.commands if entry.bootstrap_exception)
    record_id = "bootstraprecord1"
    record_dir = state_dir / "gates" / "evidence" / record_id
    record_dir.mkdir(parents=True)
    stdout = b"bootstrap\n"
    stderr = b""
    (record_dir / "stdout.bin").write_bytes(stdout)
    (record_dir / "stderr.bin").write_bytes(stderr)
    (record_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    old_record = ExecutionRecord(
        command_id=bootstrap_entry.command_id,
        command=bootstrap_entry.command,
        execution_surface="local",
        operations=(),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-22T01:00:00Z",
        observed_at="2026-07-22T01:00:01Z",
        head_before=initial_head,
        head_after=initial_head,
        stdout_digest=_sha256_digest(stdout),
        stderr_digest=_sha256_digest(stderr),
        authority_origin="bootstrap_exception",
        record_id=record_id,
        plan_digest=_plan_digest(context.plan),
        decision_id=context.decision_id,
        round_id=context.round_id,
        sequence=0,
        raw_stdout_path=f"project_state\\gates\\evidence\\{record_id}\\stdout.bin",
        raw_stderr_path=f"project_state\\gates\\evidence\\{record_id}\\stderr.bin",
        pre_state_digest="sha256:" + "1" * 64,
        post_state_digest="sha256:" + "1" * 64,
        mutation_delta_digest="sha256:" + "2" * 64,
    )
    (state_dir / "gates" / "execution_log.json").write_text(
        json.dumps(
            {
                "decision_id": context.decision_id,
                "round_id": context.round_id,
                "plan_digest": context.plan_digest,
                "generated_at": "2026-07-22T01:00:02Z",
                "commands": [old_record.to_dict()],
            }
        ),
        encoding="utf-8",
    )
    (state_dir / "gates" / "bootstrap_state.json").write_text(
        json.dumps(
            {
                "status": "BOOTSTRAP_EXPIRED",
                "decision_id": context.decision_id,
                "round_id": context.round_id,
                "expired_at": "2026-07-22T02:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "project_state"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "bootstrap evidence"], cwd=str(tmp_path), check=True)

    (state_dir / "gates" / "execution_log.json").unlink()
    shutil.rmtree(state_dir / "gates" / "evidence")
    current = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    current.run_command("status.git_head")
    imported = current.replay_bootstrap_evidence_from_head()

    assert len(imported) == 1
    assert imported[0].record_id == record_id
    assert "\\" not in imported[0].raw_stdout_path
    log = json.loads((state_dir / "gates" / "execution_log.json").read_text(encoding="utf-8"))
    assert [item["sequence"] for item in log["commands"]] == [0, 1]
    assert log["commands"][0]["authority_origin"] == "bootstrap_exception"


# ---------------------------------------------------------------------------
# F7: Command-local mutation delta — pre/post state digests
# ---------------------------------------------------------------------------


def test_runner_records_pre_and_post_state_digests(tmp_path: Path) -> None:
    """F7: each record carries pre_state_digest and post_state_digest."""

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    state_dir = tmp_path / "project_state"
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": "test.create_file",
                "command": "python -c \"open('new_file.txt', 'w').write('hello')\"",
                "phase": "test",
                "required": True,
                "required_evidence_source": "local_command_evidence",
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["integration_test"],
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": ["new_file.txt"],
                "produced_artifacts": [],
            },
        ],
    )

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    record = context.run_command("test.create_file")

    assert record.pre_state_digest.startswith("sha256:")
    assert record.post_state_digest.startswith("sha256:")
    assert record.mutation_delta_digest.startswith("sha256:")
    assert record.pre_state_digest != record.post_state_digest


def test_runner_delta_excludes_pre_existing_dirty_paths(tmp_path: Path) -> None:
    """F7: pre-existing dirty paths must NOT be attributed to the command.

    The runner captures state BEFORE the command. Only paths that changed
    between pre and post should appear in mutated_paths.
    """

    from reverse_agent.control_plane.evidence_recorder import (
        TrustedExecutionContext,
    )

    _init_repo(tmp_path)
    # Create a pre-existing dirty file BEFORE running any command.
    (tmp_path / "pre_existing.txt").write_text("dirty before command", encoding="utf-8")
    state_dir = tmp_path / "project_state"
    _write_state_decision(state_dir)

    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    record = context.run_command("status.git_head")

    # The pre-existing dirty file must NOT be attributed to this command.
    assert "pre_existing.txt" not in record.mutated_paths


def test_runner_delta_attributes_second_edit_to_pre_existing_dirty_path(tmp_path: Path) -> None:
    """Content snapshots detect edits even when the path was already dirty."""

    from reverse_agent.control_plane.evidence_recorder import TrustedExecutionContext

    _init_repo(tmp_path)
    dirty = tmp_path / "README.md"
    dirty.write_text("dirty before command\n", encoding="utf-8")
    state_dir = tmp_path / "project_state"
    _write_state_decision(
        state_dir,
        allowed_commands=[
            {
                "command_id": "test.edit_dirty",
                "command": "python -c \"open('README.md', 'w').write('changed again')\"",
                "phase": "test",
                "required": True,
                "required_evidence_source": "local_command_evidence",
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["integration_test"],
                "network_access": False,
                "authority_origin": "normal_plan",
                "allowed_mutated_paths": ["README.md"],
                "produced_artifacts": [],
            }
        ],
    )
    context = TrustedExecutionContext.from_state_dir(state_dir, repo_root=tmp_path)
    record = context.run_command("test.edit_dirty")
    assert record.mutated_paths == ("README.md",)
    assert record.raw_stdout_path == record.raw_stdout_path.replace("\\", "/")

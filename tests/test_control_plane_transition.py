from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import reverse_agent.project_gate as project_gate


def _write_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_bootstrap",
    round_id: str = "round_bootstrap",
    branch: str = "codex/example-v1",
    allowed_path: str = "reverse_agent/example/**",
) -> None:
    contract = {
        "transition_kernel_required": True,
        "required_branch": branch,
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [
            "python -m pytest tests/test_project_gate.py -q",
            "git diff --check",
        ],
        "allowed_source_paths": [allowed_path],
        "forbidden_mutated_paths": ["frontend/**"],
        "direct_push_to_main_allowed": False,
        "merge_allowed": False,
        "force_push_allowed": False,
        "rebase_during_execution_allowed": False,
        "destructive_operations_allowed": False,
        "unknown_binary_execution_allowed": False,
        "model_api_invocation_allowed": False,
        "external_reverse_tool_invocation_allowed": False,
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + json.dumps(
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
        + json.dumps(contract)
        + "\n```\n",
        encoding="utf-8",
    )


def _write_structured_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_structured",
    round_id: str = "round_structured",
    branch: str = "codex/example-v1",
) -> None:
    """Write a Decision contract that uses the new structured ``allowed_commands``."""

    contract = {
        "transition_kernel_required": True,
        "required_branch": branch,
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [
            "python -m pytest tests/test_project_gate.py -q",
        ],
        "allowed_commands": [
            {
                "command_id": "status.git_status",
                "command": "git status --short",
                "phase": "status",
                "required": True,
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["repository_observation"],
                "network_access": False,
            },
            {
                "command_id": "validation.diff_check",
                "command": "git diff --check",
                "phase": "validation",
                "required": True,
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["diff_validation"],
                "network_access": False,
            },
        ],
        "allowed_mutated_paths": ["reverse_agent/example/**"],
        "forbidden_mutated_paths": ["frontend/**", "project_state/decision_packet.md"],
        "reference_paths": ["docs/roadmap/example.md"],
        "capability_policy": {
            "runner_dispatch_allowed": False,
            "model_api_invocation_allowed": False,
            "external_reverse_tool_invocation_allowed": False,
            "unknown_binary_execution_allowed": False,
            "destructive_operations_allowed": False,
            "bmad_installation_allowed": False,
            "network_access_default_allowed": False,
            "local_network_exceptions": [],
            "ci_network_exceptions": [],
            "remote_observation_read_only_allowed": True,
            "direct_push_to_main_allowed": False,
            "merge_allowed": False,
            "force_push_allowed": False,
            "rebase_during_execution_allowed": False,
            "tag_or_release_allowed": False,
        },
        "path_risk_floor": [
            {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
            {"pattern": "**/secrets/**", "minimum_risk": "R3"},
        ],
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + json.dumps(
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
        + json.dumps(contract)
        + "\n```\n",
        encoding="utf-8",
    )


def _write_execution_log(
    state_dir: Path,
    *,
    commands: list[dict],
    decision_id: str = "decision_structured",
    round_id: str = "round_structured",
) -> None:
    """Write a minimal ``execution_log.json`` for reconciliation tests."""

    gates = state_dir / "gates"
    gates.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "artifact_name": "execution_log.json",
        "gate_name": "transition-execution-log",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "report_id": "test_report",
        "generated_at": "2026-07-21T00:00:00Z",
        "source": "observed_codex_tool_transcript",
        "commands": commands,
    }
    (gates / "execution_log.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _registry(repo_root: Path) -> None:
    registry = repo_root / ".codex-skills" / "registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "skills": {"reverse-agent-iteration": {"status": "active", "version": 2}},
            }
        ),
        encoding="utf-8",
    )


def test_transition_command_plan_rebinds_to_active_decision(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir)
    first = project_gate.transition_command_plan(state_dir=state_dir)
    assert first["plan_status"] == "PASSED"
    assert first["decision_id"] == "decision_bootstrap"
    persisted = json.loads((state_dir / "gates" / "command_plan.json").read_text(encoding="utf-8"))
    assert persisted["round_id"] == "round_bootstrap"

    _write_decision(state_dir, decision_id="decision_second", round_id="round_second")
    second = project_gate.transition_command_plan(state_dir=state_dir)
    assert second["decision_id"] == "decision_second"
    assert second["commands"] == first["commands"]


def test_transition_command_plan_generates_structured_allowed_commands(tmp_path: Path) -> None:
    """Phase A: structured ``allowed_commands`` must produce typed plan entries."""

    state_dir = tmp_path / "project_state"
    _write_structured_decision(state_dir)
    result = project_gate.transition_command_plan(state_dir=state_dir)
    assert result["plan_status"] == "PASSED"
    assert result["decision_id"] == "decision_structured"
    # Bootstrap exception commands are appended after structured commands.
    commands = result["commands"]
    structured = [cmd for cmd in commands if not cmd.get("bootstrap_exception")]
    bootstrap = [cmd for cmd in commands if cmd.get("bootstrap_exception")]
    assert len(structured) == 2
    assert all(cmd["execution_surface"] == "local" for cmd in structured)
    assert all(cmd["operations"] for cmd in structured)
    assert len(bootstrap) == 1
    assert all(cmd["bootstrap_exception"] is True for cmd in bootstrap)


def test_transition_lint_rejects_manually_changed_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    plan_path = state_dir / "gates" / "command_plan.json"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["commands"][0]["command"] = "python unexpected.py"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_lint(state_dir=state_dir)
    assert result["gate_status"] == "BLOCKED"
    assert any(item["name"] == "command_plan_provenance" and item["status"] == "FAIL" for item in result["checks"])


def _install_envelope_git_stub(
    monkeypatch: pytest.MonkeyPatch,
    *,
    branch: str,
    base_sha: str,
    decision_commit: str,
    committed_files: str = "",
    working_files: str = "",
    staged_files: str = "",
) -> None:
    """Install a ``_transition_git`` stub returning the given values."""

    def fake_git(_repo_root: Path, *args: str, check: bool = True) -> str:
        del check
        if args == ("branch", "--show-current"):
            return branch
        if args == ("merge-base", "HEAD", base_sha):
            return base_sha
        if args == ("log", "-1", "--format=%H", "--", "project_state/decision_packet.md"):
            return decision_commit
        if args == ("diff", "--name-only", f"{decision_commit}..HEAD"):
            return committed_files
        if args == ("diff", "--name-only"):
            return working_files
        if args == ("diff", "--cached", "--name-only"):
            return staged_files
        raise AssertionError(args)

    monkeypatch.setattr(project_gate, "_transition_git", fake_git)
    monkeypatch.setattr(
        project_gate.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )


def test_transition_preflight_uses_decision_branch_and_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, branch="codex/different-v2", allowed_path="reverse_agent/different/**")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _write_execution_log(
        state_dir,
        decision_id="decision_bootstrap",
        round_id="round_bootstrap",
        commands=[
            {"index": 1, "command": "python -m pytest tests/test_project_gate.py -q", "phase": "test", "exit_code": 0},
            {"index": 2, "command": "git diff --check", "phase": "validation", "exit_code": 0},
        ],
    )
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/different-v2",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/different/module.py",
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    # Phase B: pre mode returns PRE_EXECUTION_AUTHORIZED (not PASSED).
    assert result["gate_status"] == "PRE_EXECUTION_AUTHORIZED"
    branch_check = next(item for item in result["checks"] if item["name"] == "branch_identity")
    assert "expected=codex/different-v2" in branch_check["detail"]


def test_transition_preflight_blocks_when_execution_log_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase B: missing execution evidence is fine in pre mode (pre-authorized)."""

    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, branch="codex/example-v1", allowed_path="reverse_agent/example/**")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    # Phase B: pre mode must NOT consume execution_log as completion evidence;
    # a missing log is acceptable for pre-execution authorization.
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path, mode="pre")
    assert result["gate_status"] == "PRE_EXECUTION_AUTHORIZED"


def test_transition_preflight_enforces_structured_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phases A-C: structured contract surfaces capability, path-risk, reference checks."""

    state_dir = tmp_path / "project_state"
    _write_structured_decision(state_dir, branch="codex/example-v1")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _write_execution_log(
        state_dir,
        decision_id="decision_structured",
        round_id="round_structured",
        commands=[
            {
                "index": 1,
                "command": "git status --short",
                "phase": "status",
                "exit_code": 0,
                "operations": ["repository_observation"],
            },
            {
                "index": 2,
                "command": "git diff --check",
                "phase": "validation",
                "exit_code": 0,
                "operations": ["diff_validation"],
            },
        ],
    )
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    # Phase B: execution_reconciliation + execution_evidence_present checks
    # only appear in post mode (pre mode passes empty envelopes on purpose).
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path, mode="post")
    check_names = {item["name"] for item in result["checks"]}
    assert "capability_policy_enforced" in check_names
    assert "path_risk_floor_enforced" in check_names
    assert "reference_paths_read_only" in check_names
    assert "execution_reconciliation" in check_names
    assert "execution_evidence_present" in check_names
    assert result["gate_status"] == "POST_EXECUTION_RECONCILED", result["checks"]


def test_transition_preflight_blocks_when_envelope_command_undeclared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase B: undeclared commands in the execution log must block."""

    state_dir = tmp_path / "project_state"
    _write_structured_decision(state_dir, branch="codex/example-v1")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _write_execution_log(
        state_dir,
        decision_id="decision_structured",
        round_id="round_structured",
        commands=[
            {
                "index": 1,
                "command": "git status --short",
                "phase": "status",
                "exit_code": 0,
                "operations": ["repository_observation"],
            },
            {"index": 2, "command": "rm -rf /", "phase": "destructive", "exit_code": 0},
        ],
    )
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path, mode="post")
    assert result["gate_status"] == "BLOCKED"
    reconciliation = next(item for item in result["checks"] if item["name"] == "execution_reconciliation")
    assert reconciliation["status"] == "FAIL"
    assert "undeclared_command" in reconciliation["detail"]


def test_transition_preflight_blocks_when_path_risk_floor_violated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase D: mutating a secrets path must trigger the path risk floor."""

    state_dir = tmp_path / "project_state"
    _write_structured_decision(state_dir, branch="codex/example-v1")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _write_execution_log(
        state_dir,
        decision_id="decision_structured",
        round_id="round_structured",
        commands=[
            {"index": 1, "command": "git status --short", "phase": "status", "exit_code": 0},
            {"index": 2, "command": "git diff --check", "phase": "validation", "exit_code": 0},
        ],
    )
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="config/secrets/api.key",
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "BLOCKED"
    floor_check = next(item for item in result["checks"] if item["name"] == "path_risk_floor_enforced")
    assert floor_check["status"] == "FAIL"
    assert "secrets" in floor_check["detail"]


def test_transition_preflight_blocks_when_reference_path_mutated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase C: reference (read-only) paths must not appear in mutated paths."""

    state_dir = tmp_path / "project_state"
    _write_structured_decision(state_dir, branch="codex/example-v1")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _write_execution_log(
        state_dir,
        decision_id="decision_structured",
        round_id="round_structured",
        commands=[
            {"index": 1, "command": "git status --short", "phase": "status", "exit_code": 0},
            {"index": 2, "command": "git diff --check", "phase": "validation", "exit_code": 0},
        ],
    )
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="docs/roadmap/example.md",
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "BLOCKED"
    reference_check = next(item for item in result["checks"] if item["name"] == "reference_paths_read_only")
    assert reference_check["status"] == "FAIL"


def test_transition_preflight_blocks_reference_path_even_when_in_allowed_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F10: reference read-only check must cover ALL observed mutated paths.

    A reference path mistakenly placed in allowed_mutated_paths must still be
    flagged as a reference violation. The check must not be limited to
    ``outside_scope`` paths.
    """

    state_dir = tmp_path / "project_state"
    # Build a contract where a reference path is ALSO in allowed_mutated_paths
    # (a misconfiguration that the gate must catch).
    contract = {
        "transition_kernel_required": True,
        "required_branch": "codex/example-v1",
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [],
        "allowed_commands": [
            {
                "command": "git status --short",
                "phase": "status",
                "required": True,
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ["repository_observation"],
                "network_access": False,
            },
        ],
        "allowed_mutated_paths": ["docs/roadmap/example.md"],
        "forbidden_mutated_paths": ["frontend/**"],
        "reference_paths": ["docs/roadmap/example.md"],
        "capability_policy": {
            "network_access_default_allowed": False,
            "local_network_exceptions": [],
            "ci_network_exceptions": [],
        },
        "path_risk_floor": [],
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision_ref",
                "round_id": "round_ref",
                "status": "APPROVED",
                "mainline": "engineering_branch",
                "skill_profiles": ["reverse-agent-iteration@v2"],
            }
        )
        + "\n```\n\n```json decision_contract\n"
        + json.dumps(contract)
        + "\n```\n",
        encoding="utf-8",
    )
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="docs/roadmap/example.md",
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    reference_check = next(item for item in result["checks"] if item["name"] == "reference_paths_read_only")
    assert reference_check["status"] == "FAIL", result["checks"]


def test_transition_preflight_blocks_when_mutation_grant_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase D: a command mutating a path outside its grant must block.

    Rule #1: every observed mutated path must belong to the command's
    authorized set (``produced_artifacts ∪ allowed_mutated_paths``).
    """

    from reverse_agent.control_plane.models import (
        ExecutionEnvelope as TransitionExecutionEnvelope,
    )
    from reverse_agent.control_plane.models import (
        TransitionAuthority,
        TransitionCommand,
        TransitionCommandPlan,
        TransitionDecision,
    )
    from reverse_agent.control_plane.transition import validate_transition

    decision = TransitionDecision(
        "decision_grants", "round_grants", "APPROVED", "engineering_branch",
        ("reverse-agent-iteration@v2",),
    )
    plan = TransitionCommandPlan(
        decision_id=decision.decision_id,
        round_id=decision.round_id,
        commands=(
            TransitionCommand(
                "python -m pytest tests/test_x.py -q",
                "test", True, (0,), "local", ("unit_test",),
                command_id="test.unit",
                allowed_mutated_paths=("tests/test_x.py",),
            ),
        ),
    )
    authority = TransitionAuthority(
        decision=decision,
        command_plan=plan,
        expected_decision_id=decision.decision_id,
        expected_round_id=decision.round_id,
        active_skills=("reverse-agent-iteration@v2",),
        legal_mainlines=("engineering_branch",),
        expected_branch="codex/example-v1",
        actual_branch="codex/example-v1",
        base_sha="a" * 40,
        merge_base_sha="a" * 40,
        decision_commit_sha="b" * 40,
        decision_is_ancestor=True,
        observed_paths=(),
        allowed_paths=("tests/**",),
        forbidden_paths=("frontend/**",),
        forbidden_operations=(),
    )
    # Envelope mutates a path NOT in the command's allowed_mutated_paths.
    envelope = TransitionExecutionEnvelope(
        command="python -m pytest tests/test_x.py -q",
        execution_surface="local",
        mutated_paths=("tests/test_OTHER.py",),  # not granted
        operations=("unit_test",),
        command_id="test.unit",
    )
    result = validate_transition(authority, (envelope,), mode="post")
    assert result.gate_status == "BLOCKED"
    grant_check = next(c for c in result.checks if c["name"] == "mutation_grants_enforced")
    assert grant_check["status"] == "FAIL"
    assert "tests/test_OTHER.py" in grant_check["detail"]


@pytest.mark.parametrize("missing", ["required_branch", "forbidden_mutated_paths"])
def test_transition_authority_missing_scope_fails_closed(tmp_path: Path, missing: str) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir)
    path = state_dir / "decision_packet.md"
    text = path.read_text(encoding="utf-8")
    marker = "```json decision_contract\n"
    start = text.index(marker) + len(marker)
    end = text.index("\n```", start)
    contract = json.loads(text[start:end])
    contract.pop(missing)
    path.write_text(text[:start] + json.dumps(contract) + text[end:], encoding="utf-8")
    if missing == "required_branch":
        result = project_gate.transition_command_plan(state_dir=state_dir)
    else:
        project_gate.transition_command_plan(state_dir=state_dir)
        result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    assert result.get("plan_status", result.get("gate_status")) == "BLOCKED"

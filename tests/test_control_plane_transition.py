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
    immutable: bool = False,
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
    if immutable:
        contract.update({
            "decision_content_immutable_after_activation": True,
            "decision_immutability_required": True,
            "starting_head": "a" * 40,
        })
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
        if args == ("rev-parse", f"{base_sha}^{{commit}}"):
            return base_sha
        if args == ("rev-parse", "HEAD"):
            return "c" * 40
        if args == ("rev-list", "--reverse", f"{base_sha}..HEAD"):
            return decision_commit
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", decision_commit):
            return "project_state/decision_packet.md"
        if args == ("rev-parse", f"{decision_commit}:project_state/decision_packet.md"):
            return "d" * 40
        if args == ("rev-parse", "HEAD:project_state/decision_packet.md"):
            return "d" * 40
        if args == ("diff", "--name-only", "--", "project_state/decision_packet.md"):
            return ""
        if args == ("diff", "--cached", "--name-only", "--", "project_state/decision_packet.md"):
            return ""
        if args == ("status", "--short", "--untracked-files=all", "--", "project_state/decision_packet.md"):
            return ""
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


def test_active_immutability_structured_evidence_in_preflight_and_reconcile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, immutable=True)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _install_envelope_git_stub(
        monkeypatch,
        branch="codex/example-v1",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    preflight = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    pre_check = next(item for item in preflight["checks"] if item["name"] == "decision_content_immutability")
    assert pre_check["status"] == "PASS" and pre_check["evidence"]["applicable"] is True
    reconcile = project_gate.transition_reconcile(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    reconcile_check = next(item for item in reconcile["checks"] if item["name"] == "decision_content_immutability")
    assert reconcile_check["status"] == "PASS" and reconcile_check["evidence"]["applicable"] is True


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


def _write_collision_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_collision",
    round_id: str = "round_collision",
    branch: str = "codex/example-v1",
    commands: list[str],
    structured_command_ids: list[str] | None = None,
) -> None:
    """Write a Decision that exercises bootstrap command-ID semantics.

    The two bootstrap commands passed in share an identical long prefix so
    the old ``bootstrap.<command[:64]>`` derivation would collide.
    """

    if structured_command_ids is None:
        structured_command_ids = ["status.git_status"]
    structured_commands = []
    for i, cid in enumerate(structured_command_ids):
        if i == 1:
            cmd_str = "git diff --check"
            phase = "validation"
            ops = ["diff_validation"]
        else:
            cmd_str = "git status --short"
            phase = "status"
            ops = ["repository_observation"]
        structured_commands.append(
            {
                "command_id": cid,
                "command": cmd_str,
                "phase": phase,
                "required": True,
                "expected_exit_codes": [0],
                "execution_surface": "local",
                "operations": ops,
                "network_access": False,
            }
        )
    contract = {
        "transition_kernel_required": True,
        "required_branch": branch,
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": commands,
        "allowed_commands": structured_commands,
        "allowed_mutated_paths": ["reverse_agent/example/**"],
        "forbidden_mutated_paths": ["frontend/**"],
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
        "path_risk_floor": [],
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


def _collision_commands() -> tuple[str, str]:
    """Two commands whose first 64 characters are identical but that differ."""

    prefix = "git fetch --depth=1 origin refs/heads/branch-owner-abc-xyz-1234567890-"
    assert len(prefix) >= 64
    assert (prefix + "TAIL-A")[:64] == (prefix + "TAIL-B")[:64]
    return prefix + "TAIL-A", prefix + "TAIL-B"


def test_bootstrap_command_ids_are_distinct_under_prefix_collision(tmp_path: Path) -> None:
    """Two bootstrap commands sharing an identical first 64 characters
    must yield distinct, deterministic command IDs.
    """

    from reverse_agent.control_plane.legacy_adapter import (
        build_transition_command_plan,
    )
    from reverse_agent.control_plane.models import TransitionDecision

    state_dir = tmp_path / "project_state"
    cmd_a, cmd_b = _collision_commands()
    _write_collision_decision(state_dir, commands=[cmd_a, cmd_b])
    decision, contract = project_gate.load_transition_decision(state_dir / "decision_packet.md")
    plan = build_transition_command_plan(decision, contract)
    assert project_gate.validate_transition_command_plan(plan) == ()
    bootstrap = [
        cmd for cmd in plan.commands if cmd.bootstrap_exception
    ]
    ids = [cmd.command_id for cmd in bootstrap]
    assert len(ids) == 2
    assert ids[0] != ids[1]
    assert all(i for i in ids)
    assert all(i.startswith("bootstrap.") for i in ids)
    # ID is bounded: fixed "bootstrap." prefix + 64 hex digest
    assert all(len(i) == len("bootstrap.") + 64 for i in ids)
    # Same projection from the same Decision yields the same IDs.
    plan2 = build_transition_command_plan(decision, contract)
    ids2 = [cmd.command_id for cmd in plan2.commands if cmd.bootstrap_exception]
    assert ids2 == ids


def test_bootstrap_command_canonical_duplicates_are_deduped(tmp_path: Path) -> None:
    """Exact duplicate canonical bootstrap commands remain de-duplicated."""

    from reverse_agent.control_plane.legacy_adapter import (
        build_transition_command_plan,
    )
    from reverse_agent.control_plane.models import TransitionDecision

    state_dir = tmp_path / "project_state"
    cmd = "python -m pytest tests/test_project_gate.py -q"
    _write_collision_decision(state_dir, commands=[cmd, "  python   -m   pytest   tests/test_project_gate.py   -q  "])
    decision, contract = project_gate.load_transition_decision(state_dir / "decision_packet.md")
    plan = build_transition_command_plan(decision, contract)
    assert project_gate.validate_transition_command_plan(plan) == ()
    bootstrap = [cmd for cmd in plan.commands if cmd.bootstrap_exception]
    assert len(bootstrap) == 1
    assert bootstrap[0].command_id
    assert bootstrap[0].command_id.startswith("bootstrap.")


def test_structured_allowed_commands_ids_are_unchanged(tmp_path: Path) -> None:
    """Structured ``allowed_commands`` keep their authored command_id values."""

    state_dir = tmp_path / "project_state"
    ids = ["status.git_status", "validation.diff_check"]
    _write_collision_decision(state_dir, commands=[_collision_commands()[0]], structured_command_ids=ids)
    result = project_gate.transition_command_plan(state_dir=state_dir)
    assert result["plan_status"] == "PASSED"
    observed = [cmd for cmd in result["commands"] if not cmd.get("bootstrap_exception")]
    observed_ids = [cmd["command_id"] for cmd in observed]
    assert observed_ids == ids


def test_bootstrap_command_plan_provenance_rejects_tampered_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing transition lint / provenance behavior is unaffected."""

    from tests.test_project_gate import _write_decision as _pg_write_decision

    # Use the same decision shape used elsewhere in this suite.
    state_dir = tmp_path / "project_state"
    contract = {
        "transition_kernel_required": True,
        "required_branch": "codex/example-v1",
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [
            "python -m pytest tests/test_project_gate.py -q",
            "git diff --check",
        ],
        "allowed_source_paths": ["reverse_agent/example/**"],
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
                "decision_id": "decision_provenance",
                "round_id": "round_provenance",
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
    project_gate.transition_command_plan(state_dir=state_dir)
    plan_path = state_dir / "gates" / "command_plan.json"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["commands"][0]["command"] = "python unexpected.py"
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _sd: tmp_path)
    result = project_gate.transition_lint(state_dir=state_dir)
    assert result["gate_status"] == "BLOCKED"
    assert any(
        item["name"] == "command_plan_provenance" and item["status"] == "FAIL"
        for item in result["checks"]
    )


def test_project_gate_transition_command_plan_preserves_bootstrap_collision(
    tmp_path: Path,
) -> None:
    """#178 AC#2: the public project-gate generation entrypoint must
    project a collision Decision into a PASSED plan that retains two
    distinct colliding bootstrap commands with distinct command IDs.

    This exercises ``project_gate.transition_command_plan`` directly, not
    the lower-level build/validate pair, closing the only remaining
    acceptance-coverage gap reported by Owner audit.
    """

    state_dir = tmp_path / "project_state"
    cmd_a, cmd_b = _collision_commands()
    _write_collision_decision(state_dir, commands=[cmd_a, cmd_b])
    result = project_gate.transition_command_plan(state_dir=state_dir)
    assert result["plan_status"] == "PASSED"
    assert result["decision_id"] == "decision_collision"
    bootstrap = [
        cmd for cmd in result["commands"] if cmd.get("bootstrap_exception")
    ]
    assert len(bootstrap) == 2
    bootstrap_commands = {cmd["command"] for cmd in bootstrap}
    assert cmd_a in bootstrap_commands
    assert cmd_b in bootstrap_commands
    ids = [cmd["command_id"] for cmd in bootstrap]
    assert len(ids) == 2
    assert all(i for i in ids)
    assert ids[0] != ids[1]
    assert all(i.startswith("bootstrap.") for i in ids)


# ---------------------------------------------------------------------------
# Landing authority checks for ready_for_review events (Issue #367)
# ---------------------------------------------------------------------------


def _write_decision_with_landing_flag(
    state_dir: Path,
    *,
    decision_id: str = "decision_landing_test",
    round_id: str = "round_landing_test",
    branch: str = "owner/test-branch",
    base_sha: str = "a" * 40,
    mainline_merge_intent_required: bool = True,
    workflow_profile: str = "baseline",
) -> None:
    """Write a Decision contract with explicit mainline_merge_intent_required."""

    contract = {
        "transition_kernel_required": True,
        "required_branch": branch,
        "activation_base_sha": base_sha,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [
            "python -m pytest tests/test_project_gate.py -q",
            "git diff --check",
        ],
        "allowed_mutated_paths": ["reverse_agent/example/**"],
        "forbidden_mutated_paths": ["frontend/**"],
        "direct_push_to_main_allowed": False,
        "merge_allowed": False,
        "force_push_allowed": False,
        "rebase_during_execution_allowed": False,
        "destructive_operations_allowed": False,
        "unknown_binary_execution_allowed": False,
        "model_api_invocation_allowed": False,
        "external_reverse_tool_invocation_allowed": False,
        "mainline_merge_intent_required": mainline_merge_intent_required,
        "workflow_profile": workflow_profile,
        "decision_content_immutable_after_activation": True,
        "decision_immutability_required": True,
        "starting_head": base_sha,
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


def _write_event_file(
    tmp_path: Path,
    *,
    action: str = "ready_for_review",
    pr_number: int = 367,
) -> Path:
    event = {
        "action": action,
        "pull_request": {
            "number": pr_number,
            "head": {"sha": "b" * 40},
            "base": {"sha": "a" * 40},
        },
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    return event_path


def _write_active_intent(
    repo_root: Path,
    *,
    source_pr: int = 367,
    decision_id: str = "decision_landing_test",
    decision_sha: str = "",
    plan_sha: str = "",
    base_sha: str = "a" * 40,
    workflow_profile: str = "baseline",
    expires_at: str = "2099-01-01T00:00:00Z",
) -> None:
    intents_dir = repo_root / "project_state" / "mainline_merge_intents"
    intents_dir.mkdir(parents=True, exist_ok=True)
    intent = {
        "schema_version": 3,
        "intent_id": f"pr{source_pr}_test_v1",
        "repository": "dddd2024/reverse-agent",
        "source_pr": source_pr,
        "locked_base_sha": base_sha,
        "allowed_merge_method": "merge",
        "decision_identity": {
            "decision_id": decision_id,
            "decision_content_sha256": decision_sha,
        },
        "command_plan_sha256": plan_sha,
        "merge_tree_policy": "equal_to_accepted_head_tree",
        "workflow_profile": workflow_profile,
        "required_workflows": [
            "CI",
            "Decision Preflight",
            "State Gate (pull_request)",
        ],
        "expires_at": expires_at,
    }
    (intents_dir / "active.json").write_text(
        json.dumps(intent, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _compute_decision_sha(state_dir: Path) -> str:
    from hashlib import sha256
    path = state_dir / "decision_packet.md"
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _compute_plan_sha(state_dir: Path) -> str:
    from hashlib import sha256
    path = state_dir / "gates" / "command_plan.json"
    if not path.exists():
        return ""
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def test_landing_authority_blocks_engineering_pr_ready_for_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G2: engineering Decision (mainline_merge_intent_required=false) + ready_for_review -> BLOCK."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(
        state_dir,
        mainline_merge_intent_required=False,
    )
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "engineering_pr_not_landing_authorized" in result["blocking_reasons"]
    assert result.get("event_action") == "ready_for_review"


def test_landing_authority_passes_through_non_ready_for_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G1: engineering Decision + non-ready_for_review event -> normal preflight (no landing check)."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(
        state_dir,
        mainline_merge_intent_required=False,
    )
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    event_path = _write_event_file(tmp_path, action="synchronize", pr_number=367)
    _install_envelope_git_stub(
        monkeypatch,
        branch="owner/test-branch",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "PRE_EXECUTION_AUTHORIZED"
    assert "engineering_pr_not_landing_authorized" not in result.get("blocking_reasons", [])


def test_landing_authority_passes_through_no_event_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No event path -> normal preflight (no landing check)."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(
        state_dir,
        mainline_merge_intent_required=False,
    )
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    _install_envelope_git_stub(
        monkeypatch,
        branch="owner/test-branch",
        base_sha="a" * 40,
        decision_commit="b" * 40,
        committed_files="reverse_agent/example/module.py",
    )
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path="",
        write_result=False,
    )
    assert result["gate_status"] == "PRE_EXECUTION_AUTHORIZED"
    assert "engineering_pr_not_landing_authorized" not in result.get("blocking_reasons", [])


def test_landing_authority_blocks_when_no_active_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G3: landing-capable Decision + ready_for_review + no active intent -> BLOCK with landing_authority_required."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(state_dir, mainline_merge_intent_required=True)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "landing_authority_required" in result["blocking_reasons"]


def test_landing_authority_blocks_when_wrong_pr_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G5: landing-capable + active intent bound to wrong PR -> BLOCK with landing_authority_mismatch."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(state_dir, mainline_merge_intent_required=True)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    decision_sha = _compute_decision_sha(state_dir)
    plan_sha = _compute_plan_sha(state_dir)
    _write_active_intent(
        tmp_path,
        source_pr=999,
        decision_id="decision_landing_test",
        decision_sha=decision_sha,
        plan_sha=plan_sha,
        base_sha="a" * 40,
    )
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "landing_authority_mismatch" in result["blocking_reasons"]
    pr_check = next((c for c in result["checks"] if c["name"] == "landing_intent_source_pr"), None)
    assert pr_check is not None
    assert pr_check["status"] == "FAIL"
    assert "observed=999" in pr_check["detail"]
    assert "expected=367" in pr_check["detail"]


def test_landing_authority_blocks_when_wrong_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G6: landing-capable + active intent with wrong base -> BLOCK with landing_authority_mismatch."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(state_dir, mainline_merge_intent_required=True)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    decision_sha = _compute_decision_sha(state_dir)
    plan_sha = _compute_plan_sha(state_dir)
    _write_active_intent(
        tmp_path,
        source_pr=367,
        decision_id="decision_landing_test",
        decision_sha=decision_sha,
        plan_sha=plan_sha,
        base_sha="b" * 40,
    )
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "landing_authority_mismatch" in result["blocking_reasons"]
    base_check = next((c for c in result["checks"] if c["name"] == "landing_intent_locked_base"), None)
    assert base_check is not None
    assert base_check["status"] == "FAIL"


def test_landing_authority_blocks_when_expired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G11: landing-capable + expired active intent -> BLOCK with landing_authority_mismatch."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(state_dir, mainline_merge_intent_required=True)
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    decision_sha = _compute_decision_sha(state_dir)
    plan_sha = _compute_plan_sha(state_dir)
    _write_active_intent(
        tmp_path,
        source_pr=367,
        decision_id="decision_landing_test",
        decision_sha=decision_sha,
        plan_sha=plan_sha,
        base_sha="a" * 40,
        expires_at="2020-01-01T00:00:00Z",
    )
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "landing_authority_mismatch" in result["blocking_reasons"]
    expiry_check = next((c for c in result["checks"] if c["name"] == "landing_intent_expiry"), None)
    assert expiry_check is not None
    assert expiry_check["status"] == "FAIL"


def test_landing_authority_blocks_when_wrong_workflow_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """G10: landing-capable + wrong workflow profile -> BLOCK with landing_authority_mismatch."""

    state_dir = tmp_path / "project_state"
    _write_decision_with_landing_flag(
        state_dir,
        mainline_merge_intent_required=True,
        workflow_profile="baseline",
    )
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)
    decision_sha = _compute_decision_sha(state_dir)
    plan_sha = _compute_plan_sha(state_dir)
    _write_active_intent(
        tmp_path,
        source_pr=367,
        decision_id="decision_landing_test",
        decision_sha=decision_sha,
        plan_sha=plan_sha,
        base_sha="a" * 40,
        workflow_profile="unknown_profile",
    )
    event_path = _write_event_file(tmp_path, action="ready_for_review", pr_number=367)
    monkeypatch.setattr(project_gate, "_derive_repo_root", lambda _state_dir: tmp_path)
    result = project_gate.transition_preflight(
        state_dir=state_dir,
        repo_root=tmp_path,
        event_path=str(event_path),
        write_result=False,
    )
    assert result["gate_status"] == "BLOCKED"
    assert "landing_authority_mismatch" in result["blocking_reasons"]
    profile_check = next((c for c in result["checks"] if c["name"] == "landing_intent_workflow_profile"), None)
    assert profile_check is not None
    assert profile_check["status"] == "FAIL"

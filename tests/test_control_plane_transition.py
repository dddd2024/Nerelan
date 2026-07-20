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


def test_transition_preflight_uses_decision_branch_and_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "project_state"
    _write_decision(state_dir, branch="codex/different-v2", allowed_path="reverse_agent/different/**")
    _registry(tmp_path)
    project_gate.transition_command_plan(state_dir=state_dir)

    def fake_git(_repo_root: Path, *args: str, check: bool = True) -> str:
        del check
        if args == ("branch", "--show-current"):
            return "codex/different-v2"
        if args == ("merge-base", "HEAD", "a" * 40):
            return "a" * 40
        if args == ("log", "-1", "--format=%H", "--", "project_state/decision_packet.md"):
            return "b" * 40
        if args == ("diff", "--name-only", f"{'b' * 40}..HEAD"):
            return "reverse_agent/different/module.py"
        if args in (("diff", "--name-only"), ("diff", "--cached", "--name-only")):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(project_gate, "_transition_git", fake_git)
    monkeypatch.setattr(
        project_gate.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )
    result = project_gate.transition_preflight(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "PASSED"
    branch_check = next(item for item in result["checks"] if item["name"] == "branch_identity")
    assert "expected=codex/different-v2" in branch_check["detail"]


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

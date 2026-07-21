"""Phase F: transition-report command generates current-round report truth.

Covers wiring of ``report_truth.py`` into an actual ``transition-report``
project-gate command. The command must:

* derive changed-file inventory from real ``git diff`` output;
* record current Decision/round/head identity;
* only emit local-status values (LOCAL_VALIDATED/LOCAL_PARTIAL/LOCAL_FAILED);
* generate a remote-observation payload that does NOT claim REMOTE_PASSED;
* refuse to operate against a stale Decision or empty diff.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.project_gate import transition_report


_DECISION_ID = "decision_report_truth"
_ROUND_ID = "round_report_truth"
_BASE_SHA = "a" * 40
_HEAD_SHA = "b" * 40


def _write_decision_packet(state_dir: Path, *, decision_id: str = _DECISION_ID, round_id: str = _ROUND_ID) -> None:
    """Write a minimal transition-kernel decision packet."""

    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{decision_id}",
  "round_id": "{round_id}",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "transition_kernel_required": true,
  "required_branch": "codex/architecture-spine-v1",
  "activation_base_sha": "{_BASE_SHA}",
  "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
  "bootstrap_exception_commands": ["git status --short"],
  "allowed_commands": [],
  "reference_paths": [],
  "generated_artifact_paths": [
    "project_state/gates/changed_file_inventory.json",
    "project_state/gates/remote_observation_payload.json"
  ],
  "allowed_mutated_paths": ["reverse_agent/example/**"],
  "forbidden_mutated_paths": ["frontend/**"],
  "capability_policy": {{
    "network_access_default_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": []
  }},
  "path_risk_floor": []
}}
```
""",
        encoding="utf-8",
    )


def _write_command_plan(state_dir: Path, *, decision_id: str = _DECISION_ID, round_id: str = _ROUND_ID) -> None:
    gates = state_dir / "gates"
    gates.mkdir(parents=True, exist_ok=True)
    (gates / "command_plan.json").write_text(
        json.dumps({
            "schema_version": 1,
            "decision_id": decision_id,
            "round_id": round_id,
            "commands": [
                {
                    "command": "python -m pytest -q",
                    "phase": "test",
                    "required": True,
                    "expected_exit_codes": [0],
                    "execution_surface": "local",
                    "operations": ["unit_test"],
                    "authority_origin": "normal_plan",
                    "command_id": "test.full",
                    "required_evidence_source": "local_provenance",
                }
            ],
        }),
        encoding="utf-8",
    )


def _write_registry(tmp_path: Path) -> None:
    registry_dir = tmp_path / ".codex-skills"
    registry_dir.mkdir(exist_ok=True)
    (registry_dir / "registry.json").write_text(
        json.dumps({
            "schema_version": 1,
            "skills": {"reverse-agent-iteration": {"status": "active", "version": 2}},
        }),
        encoding="utf-8",
    )


def _setup_repo(tmp_path: Path) -> Path:
    """Create the standard state dir + decision packet + command plan."""

    state_dir = tmp_path / "project_state"
    gates_dir = state_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    _write_decision_packet(state_dir)
    _write_command_plan(state_dir)
    _write_registry(tmp_path)
    return state_dir


def _fake_git_factory(*, diff_names: str, head_sha: str = _HEAD_SHA, base_sha: str = _BASE_SHA):
    """Build a fake_git that returns the supplied diff names and SHAs."""

    decision_sha = "c" * 40

    def fake_git(_repo_root: Path, *args: str, check: bool = True) -> str:
        del check
        if args == ("branch", "--show-current"):
            return "codex/architecture-spine-v1"
        if args == ("merge-base", "HEAD", base_sha):
            return base_sha
        if args == ("log", "-1", "--format=%H", "--", "project_state/decision_packet.md"):
            return decision_sha
        if args == ("diff", "--name-only", f"{base_sha}..HEAD"):
            return diff_names
        if args == ("rev-parse", "HEAD"):
            return head_sha
        if args in (("diff", "--name-only"), ("diff", "--cached", "--name-only")):
            return ""
        if args == ("merge-base", "--is-ancestor", decision_sha, "HEAD"):
            return ""  # not used directly; subprocess.run handles this
        raise AssertionError(args)

    return fake_git


# --- Test 1: changed-file inventory from real Git diff -----------------


def test_transition_report_generates_changed_file_inventory(tmp_path, monkeypatch) -> None:
    """Phase F: ``transition-report`` derives inventory from real git diff."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    diff_names = (
        "reverse_agent/control_plane/transition.py\n"
        "reverse_agent/architecture/contracts.py\n"
        "tests/test_transition_report.py\n"
    )
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names=diff_names),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "PASSED"
    inventory_path = state_dir / "gates" / "changed_file_inventory.json"
    assert inventory_path.exists()
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert inventory["source"] == "git_diff_name_only"
    assert inventory["base_sha"] == _BASE_SHA
    assert inventory["head_sha"] == _HEAD_SHA
    assert inventory["paths"] == [
        "reverse_agent/control_plane/transition.py",
        "reverse_agent/architecture/contracts.py",
        "tests/test_transition_report.py",
    ]


# --- Test 2: report identity matches current Decision -------------------


def test_transition_report_records_current_decision_identity(tmp_path, monkeypatch) -> None:
    """Phase F: report must record current Decision/round identity."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["decision_id"] == _DECISION_ID
    assert result["round_id"] == _ROUND_ID
    # The codex_execution_report.md must embed current Decision identity.
    codex_report = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")
    assert _DECISION_ID in codex_report
    assert _ROUND_ID in codex_report
    # The execution_report.md must embed current head SHA.
    exec_report = (state_dir / "execution_report.md").read_text(encoding="utf-8")
    assert _HEAD_SHA in exec_report


# --- Test 3: local status only allows local enum ----------------------


def test_transition_report_local_status_never_claims_remote_passed(tmp_path, monkeypatch) -> None:
    """Phase F: local report must not claim REMOTE_PASSED.

    The local report can only record LOCAL_VALIDATED, LOCAL_PARTIAL,
    LOCAL_FAILED, or REMOTE_NOT_OBSERVED/REMOTE_PENDING. It must not
    forge REMOTE_PASSED.
    """

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["local_status"] in {"LOCAL_VALIDATED", "LOCAL_PARTIAL", "LOCAL_FAILED"}
    # remote_observation_payload.json must not claim REMOTE_PASSED.
    remote_path = state_dir / "gates" / "remote_observation_payload.json"
    assert remote_path.exists()
    remote_payload = json.loads(remote_path.read_text(encoding="utf-8"))
    assert remote_payload["ci_status"] == "REMOTE_NOT_OBSERVED"
    assert remote_payload["state_gate_status"] == "REMOTE_NOT_OBSERVED"
    assert remote_payload["decision_preflight_status"] == "REMOTE_NOT_OBSERVED"
    assert remote_payload["head_sha"] == _HEAD_SHA


# --- Test 4: empty diff is rejected -----------------------------------


def test_transition_report_rejects_empty_diff(tmp_path, monkeypatch) -> None:
    """Phase F: empty diff must fail closed."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names=""),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "BLOCKED"
    assert any("empty_diff" in reason or "no_changes" in reason for reason in result["blocking_reasons"])


# --- Test 5: remote observation payload is to-be-published --------------


def test_transition_report_remote_observation_payload_is_pending(tmp_path, monkeypatch) -> None:
    """Phase F: remote_observation_payload.json is a to-be-published payload.

    It must record the current head_sha and decision identity so a future
    PR audit comment can bind to the same head. It must NOT claim the
    observation has already been made.
    """

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    monkeypatch.setattr(
        project_agent := __import__("reverse_agent.project_gate", fromlist=[""]),
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_agent.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    remote_path = state_dir / "gates" / "remote_observation_payload.json"
    payload = json.loads(remote_path.read_text(encoding="utf-8"))
    assert payload["head_sha"] == _HEAD_SHA
    assert payload["decision_id"] == _DECISION_ID
    assert payload["round_id"] == _ROUND_ID
    # Must look like a pending payload, not a conclusive observation.
    assert payload["ci_status"] == "REMOTE_NOT_OBSERVED"


# --- Test 6: stale decision blocks ----------------------------------


def test_transition_report_blocks_on_invalid_decision_packet(tmp_path, monkeypatch) -> None:
    """Phase F: invalid decision packet must block the report."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    # Overwrite decision packet with malformed content.
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n{\"schema_version\": 1}\n```\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "BLOCKED"


# --- Test 7: pytest result references current Decision ----------------


def test_transition_report_writes_pytest_result_with_current_identity(tmp_path, monkeypatch) -> None:
    """Phase F: ``pytest_result.txt`` must reference current Decision."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    transition_report(state_dir=state_dir, repo_root=tmp_path)
    pytest_path = state_dir / "pytest_result.txt"
    assert pytest_path.exists()
    content = pytest_path.read_text(encoding="utf-8")
    assert _DECISION_ID in content
    assert _ROUND_ID in content


# --- Test 8: F11 — report subject binding into transition-report CLI --------


def test_transition_report_binds_implementation_subject(tmp_path, monkeypatch) -> None:
    """F11: transition-report must bind to the implementation subject.

    The report must classify changed files into implementation/governance/
    generated buckets, compute subject_tree_digest and subject_diff_digest,
    and embed them in the report output. Governance paths (Decision,
    roadmap) must NOT appear in ``implementation_subject_paths``.
    """

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    diff_names = (
        "reverse_agent/control_plane/transition.py\n"
        "project_state/decision_packet.md\n"
        "project_state/gates/changed_file_inventory.json\n"
    )
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names=diff_names),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "PASSED"
    # F11: report must carry subject binding fields.
    assert "subject_binding" in result
    binding = result["subject_binding"]
    assert binding["activation_base_sha"] == _BASE_SHA
    assert "subject_tree_digest" in binding
    assert "subject_diff_digest" in binding
    # F11: implementation_subject_paths must contain only implementation
    # paths, not governance (decision_packet.md) or generated artifacts.
    impl_paths = binding["implementation_subject_paths"]
    assert "reverse_agent/control_plane/transition.py" in impl_paths
    assert "project_state/decision_packet.md" not in impl_paths
    assert "project_state/gates/changed_file_inventory.json" not in impl_paths
    # F11: governance and generated buckets are recorded separately.
    assert "governance_paths" in binding
    assert "generated_artifact_paths" in binding
    assert "project_state/decision_packet.md" in binding["governance_paths"]
    assert (
        "project_state/gates/changed_file_inventory.json"
        in binding["generated_artifact_paths"]
    )


def test_transition_report_binds_local_seal_digest_when_seal_exists(
    tmp_path, monkeypatch
) -> None:
    """F11: when a LOCAL_RECONCILED seal exists, its digest is bound."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    # Write a LOCAL_RECONCILED seal so the report can bind its digest.
    seal_path = state_dir / "gates" / "local_execution_seal.json"
    seal_path.write_text(
        json.dumps({
            "schema_version": 1,
            "gate_name": "transition-seal-local",
            "status": "LOCAL_RECONCILED",
            "decision_id": _DECISION_ID,
            "round_id": _ROUND_ID,
            "subject_digest": "sha256:" + "a" * 64,
            "plan_digest": "sha256:" + "b" * 64,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    assert result["gate_status"] == "PASSED"
    binding = result["subject_binding"]
    # F11: local_seal_digest must be present and non-empty.
    assert binding["local_seal_digest"]
    assert binding["local_seal_digest"].startswith("sha256:")


def test_transition_report_blocks_when_seal_decision_diverges(
    tmp_path, monkeypatch
) -> None:
    """F11: when the local seal's Decision diverges, report is LOCAL_BLOCKED."""

    import reverse_agent.project_gate as project_gate_module

    state_dir = _setup_repo(tmp_path)
    # Write a seal that belongs to a DIFFERENT Decision.
    seal_path = state_dir / "gates" / "local_execution_seal.json"
    seal_path.write_text(
        json.dumps({
            "schema_version": 1,
            "gate_name": "transition-seal-local",
            "status": "LOCAL_RECONCILED",
            "decision_id": "decision_OLD",
            "round_id": "round_OLD",
            "subject_digest": "sha256:" + "a" * 64,
            "plan_digest": "sha256:" + "b" * 64,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        project_gate_module,
        "_transition_git",
        _fake_git_factory(diff_names="reverse_agent/example.py\n"),
    )
    monkeypatch.setattr(
        project_gate_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = transition_report(state_dir=state_dir, repo_root=tmp_path)
    # F11: any input identity mismatch must produce LOCAL_BLOCKED.
    assert result["local_status"] == "LOCAL_BLOCKED"
    assert any("seal_decision_id_diverges" in r for r in result["blocking_reasons"])

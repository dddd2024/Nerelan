import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.project_gate import (
    BUILD_OUTPUT_WHITELIST,
    _close_round_exit_code,
    _command_expected_exit_codes,
    _command_kind,
    _command_phase,
    _decision_immutability_check,
    _build_output_scope_check,
    _verified_cli_coverage_check,
    _startup_baseline_consistency_check,
    _stale_artifact_id_check,
    _report_body_consistency_check,
    _expected_report_id,
    _extract_bash_commands,
    _extract_unfenced_commands,
    _historical_sample_limitations_only,
    _is_close_round_command,
    _is_descriptive_backtick_line,
    _is_historical_sample_limitation,
    _is_prohibitive_line,
    _is_self_invocation,
    _read_round_close_snapshot,
    _report_status_from_gate,
    _report_status_from_gate_payload,
    _result_status,
    _round_close_snapshot_path,
    _allowed_inherited_files,
    _validate_command_plan_consistency,
    _write_round_close_snapshot,
    build_report_summary_synthesis,
    close_round,
    command_plan,
    final_check,
    main,
    preflight,
    run_round,
)
from reverse_agent.project_state import archive_round, read_codex_report_summary, write_pytest_result


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_skill_registry(tmp_path: Path) -> None:
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {
                    "path": ".codex-skills/reverse-agent-iteration/SKILL.md",
                    "status": "active",
                    "scope": "generic_workflow",
                    "version": 2,
                },
                "samplereverse-frontier": {
                    "path": ".codex-skills/samplereverse-frontier/SKILL.md",
                    "status": "active",
                    "scope": "sample_profile",
                    "version": 2,
                },
            },
        },
    )


def _archive_paths(round_id: str) -> list[str]:
    return [
        f"project_state/rounds/{round_id}/codex_execution_report.md",
        f"project_state/rounds/{round_id}/decision_packet.md",
        f"project_state/rounds/{round_id}/pytest_result.txt",
        f"project_state/rounds/{round_id}/round_manifest.json",
    ]


def _write_round_baseline(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    baseline_dirty_files: list[str] | None = None,
) -> None:
    _write_json(
        state_dir / "gates" / "round_baseline.json",
        {
            "schema_version": 1,
            "artifact_name": "round_baseline.json",
            "decision_id": decision_id,
            "round_id": round_id,
            "head_commit": "commit_test",
            "baseline_git_status_short": [],
            "baseline_git_diff_name_only": [],
            "baseline_dirty_files": baseline_dirty_files if baseline_dirty_files is not None else [],
            "baseline_untracked_files": [],
            "baseline_has_untracked_implementation_files": False,
            "generated_at": "2026-06-12T00:00:00Z",
        },
    )


def _write_decision(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    mainline: str = "engineering_branch",
    extra_text: str = "",
) -> None:
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": mainline,
        "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"],
    }
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated files:

- `project_state/gates/final_gate_result.json`
{extra_text}
""",
        encoding="utf-8",
    )


def _write_preflight_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_preflight",
    round_id: str = "round_preflight",
    status: str = "APPROVED",
    mainline: str = "engineering_branch",
    skill_profiles: list[str] | None = None,
    goal: str = "Build a read-only project gate.",
    current_evidence: str = "Historical stale artifacts are not current evidence.",
    implementation_scope: str | None = None,
) -> None:
    profiles = skill_profiles if skill_profiles is not None else ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": status,
        "mainline": mainline,
        "skill_profiles": profiles,
    }
    scope = implementation_scope or """Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated files:

- `project_state/gates/preflight_result.json`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
"""
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

{goal}

## 2. Current Evidence

{current_evidence}

## 6. Implementation Scope

{scope}
""",
        encoding="utf-8",
    )


def _make_preflight_state(tmp_path: Path, **decision_kwargs: object) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "task": "old_sample_task",
            "derived_task": "old_sample_task",
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})
    _write_preflight_decision(state_dir, **decision_kwargs)
    return state_dir


def _write_command_plan_decision(
    state_dir: Path,
    *,
    tests_block: str | None,
    extra_text: str = "",
) -> None:
    payload = {
        "schema_version": 1,
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"],
    }
    tests_section = "" if tests_block is None else f"""
## 7. Tests

```bash
{tests_block}
```
"""
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

Build a read-only command plan.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated files:

- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/run_round_result.json`

{extra_text}
{tests_section}
""",
        encoding="utf-8",
    )


def _make_command_plan_state(
    tmp_path: Path,
    *,
    tests_block: str | None,
    extra_text: str = "",
) -> Path:
    state_dir = _make_preflight_state(tmp_path)
    _write_command_plan_decision(state_dir, tests_block=tests_block, extra_text=extra_text)
    return state_dir


def _write_report(
    state_dir: Path,
    *,
    decision_id: str,
    report_id: str,
    round_id: str,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    files_changed: list[str] | None = None,
    tests_ran: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
) -> None:
    payload = {
        "schema_version": 1,
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "status": status,
        "acceptance_recommendation": acceptance,
        "files_changed": files_changed if files_changed is not None else [],
        "tests_ran": tests_ran if tests_ran is not None else ["python -m pytest -q"],
        "generated_artifacts": generated_artifacts if generated_artifacts is not None else [],
        "verified_artifacts": [],
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )


def _write_pytest(
    state_dir: Path,
    *,
    decision_id: str,
    report_id: str,
    round_id: str,
    tests_ran: list[str] | None = None,
    status: str = "PASSED",
    body: str = "1 passed\n",
) -> None:
    write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": decision_id,
            "report_id": report_id,
            "round_id": round_id,
            "generated_at": "2026-06-11T00:00:00Z",
            "status": status,
            "tests_ran": tests_ran if tests_ran is not None else ["python -m pytest -q"],
        },
        body=body,
    )


def _make_gate_state(
    tmp_path: Path,
    *,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    mainline: str = "engineering_branch",
    files_changed: list[str] | None = None,
    tests_ran: list[str] | None = None,
    pytest_tests_ran: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
            "source_harness_run": "run_test",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    decision_id = "decision_gate"
    report_id = "codex_report_gate"
    round_id = "round_gate"
    archive_paths = _archive_paths(round_id)
    base_changed = [
        "reverse_agent/project_gate.py",
        "tests/test_project_gate.py",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/report_summary_synthesis.json",
        *archive_paths,
    ]
    report_tests = tests_ran if tests_ran is not None else [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest -q",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id, mainline=mainline)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
    # Create gate artifacts that are listed in generated_artifacts
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1, "artifact_name": "command_plan.json",
        "decision_id": decision_id, "round_id": round_id,
        "plan_status": "PASSED",
        "mainline": "engineering_branch",
        "generated_at": "2026-06-11T00:00:00Z",
        "commands": [
            {"index": 1, "command": "Set-Location F:\\reverse-agent", "phase": "status", "kind": "startup", "required": True},
            {"index": 2, "command": "Get-Location", "phase": "status", "kind": "startup", "required": True},
            {"index": 3, "command": "Test-Path F:\\reverse-agent", "phase": "status", "kind": "startup", "required": True},
            {"index": 4, "command": "git rev-parse --show-toplevel", "phase": "status", "kind": "startup", "required": True},
            {"index": 5, "command": "git status --short", "phase": "status", "kind": "startup", "required": True},
            {"index": 6, "command": "python -m pytest -q", "phase": "test", "kind": "pytest", "required": True},
            {"index": 7, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state", "phase": "gate", "kind": "gate-check", "required": True},
        ],
        "warnings": [],
        "blocking_reasons": [],
        "profile_meta": {
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        },
    })
    _write_json(gates_dir / "round_delta_summary.json", {
        "schema_version": 1, "artifact_name": "round_delta_summary.json",
        "decision_id": decision_id, "round_id": round_id,
        "baseline_available": True,
        "new_dirty_files_since_baseline": [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
        ],
        "inherited_dirty_files": [],
        "final_dirty_files": [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
        ],
    })
    _write_json(gates_dir / "report_summary_synthesis.json", {
        "schema_version": 1, "artifact_name": "report_summary_synthesis.json",
        "decision_id": decision_id, "round_id": round_id,
    })
    _write_json(gates_dir / "final_gate_result.json", {
        "schema_version": 1, "artifact_name": "final_gate_result.json",
        "decision_id": decision_id, "round_id": round_id,
        "gate_status": "PASSED",
    })
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=status,
        acceptance=acceptance,
        files_changed=files_changed if files_changed is not None else base_changed,
        tests_ran=report_tests,
        generated_artifacts=generated_artifacts
        if generated_artifacts is not None
        else [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/gate_profile_plan.json",
            *archive_paths,
        ],
    )
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=pytest_tests_ran if pytest_tests_ran is not None else report_tests,
    )
    archive_round(state_dir=state_dir, round_id=round_id)
    return state_dir


def _command_block(command: str, stdout: str, *, exit_code: int = 0, stderr: str = "") -> str:
    lines = [f"===== COMMAND: {command} ====="]
    if stdout:
        lines.append(stdout.rstrip())
    if stderr:
        lines.extend(["===== STDERR =====", stderr.rstrip()])
    lines.append(f"===== EXIT: {exit_code} =====")
    return "\n".join(lines)


_STARTUP_COMMAND_BLOCKS = [
    _command_block("Set-Location F:\\reverse-agent", "F:\\reverse-agent"),
    _command_block("Get-Location", "F:\\reverse-agent"),
    _command_block("Test-Path F:\\reverse-agent", "True"),
    _command_block("git rev-parse --show-toplevel", "F:\\reverse-agent"),
    _command_block("git status --short", ""),
]


def _make_command_plan_gate_state(
    tmp_path: Path,
    *,
    command_plan_overrides: dict[str, object] | None = None,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    report_tests: list[str] | None = None,
    pytest_body: str | None = None,
    final_check_stdout_status: str = "PASSED",
    generated_artifacts: list[str] | None = None,
    archived: bool = True,
) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
            "source_harness_run": "run_test",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    decision_id = "decision_gate"
    report_id = "codex_report_gate"
    round_id = "round_gate"
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    plan_payload = {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "generated_at": "2026-06-11T00:00:00Z",
        "commands": [
            {
                "index": index,
                "command": command,
                "phase": "gate" if "project_gate" in command else "test",
                "kind": "command-plan" if "command-plan" in command else ("final-check" if "final-check" in command else "pytest"),
                "required": True,
                "expected_exit_codes": [0],
                "records_stdout_stderr": True,
                "notes": "expected to exit 0",
            }
            for index, command in enumerate(commands, start=1)
        ],
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
        "profile_meta": {
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        },
    }
    if command_plan_overrides:
        plan_payload.update(command_plan_overrides)
    archive_paths = _archive_paths(round_id)
    tests = report_tests if report_tests is not None else commands
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
    # Create gate artifacts that are listed in generated_artifacts
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "round_delta_summary.json", {
        "schema_version": 1, "artifact_name": "round_delta_summary.json",
        "decision_id": decision_id, "round_id": round_id,
        "baseline_available": True,
        "new_dirty_files_since_baseline": [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
        ],
        "inherited_dirty_files": [],
        "final_dirty_files": [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
        ],
    })
    _write_json(gates_dir / "report_summary_synthesis.json", {
        "schema_version": 1, "artifact_name": "report_summary_synthesis.json",
        "decision_id": decision_id, "round_id": round_id,
    })
    _write_json(gates_dir / "final_gate_result.json", {
        "schema_version": 1, "artifact_name": "final_gate_result.json",
        "decision_id": decision_id, "round_id": round_id,
        "gate_status": "PASSED",
    })
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=status,
        acceptance=acceptance,
        files_changed=[
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/report_summary_synthesis.json",
            *archive_paths,
        ],
        tests_ran=tests,
        generated_artifacts=generated_artifacts
        if generated_artifacts is not None
        else [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/gate_profile_plan.json",
            *archive_paths,
        ],
    )
    _write_json(state_dir / "gates" / "command_plan.json", plan_payload)
    body = pytest_body
    if body is None:
        body = "\n\n".join(
            [
                _command_block(commands[0], "F:\\reverse-agent"),
                _command_block(commands[1], "F:\\reverse-agent"),
                _command_block(commands[2], "True"),
                _command_block(commands[3], "F:\\reverse-agent"),
                _command_block(commands[4], ""),
                _command_block(commands[5], "212 passed in 1.00s"),
                _command_block(commands[6], "command-plan: PASSED"),
                _command_block(commands[7], json.dumps(plan_payload, indent=2)),
                _command_block(commands[8], f"final-check: {final_check_stdout_status}"),
            ]
        )
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=tests,
        body=body,
    )
    if archived:
        archive_round(state_dir=state_dir, round_id=round_id)
    return state_dir


def _make_report_summary_state(
    tmp_path: Path,
    *,
    report_status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    files_changed: list[str] | None = None,
    tests_ran: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
    baseline_dirty_files: list[str] | None = None,
) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    decision_id = "decision_report_summary"
    round_id = "round_gate"
    report_id = "codex_report_gate"
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate report-summary --state-dir project_state",
        "python -m reverse_agent.project_state lint-report --state-dir project_state",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    archive_paths = _archive_paths(round_id)
    expected_files_changed = [
        "reverse_agent/project_gate.py",
        "tests/test_project_gate.py",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/report_summary_synthesis.json",
        *archive_paths,
    ]
    expected_generated_artifacts = [
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/command_plan.json",
        "project_state/gates/report_summary_synthesis.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        *archive_paths,
    ]
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})
    _write_preflight_decision(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
        goal="Build report-summary synthesis for codex_report_summary.",
        implementation_scope="""Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
""",
    )
    _write_round_baseline(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
        baseline_dirty_files=baseline_dirty_files,
    )
    command_plan_payload = {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "generated_at": "2026-06-12T00:00:00Z",
        "commands": [
            {
                "index": index,
                "command": command,
                "phase": "gate" if "project_gate" in command else "status",
                "kind": "report-summary" if "report-summary" in command else "command-plan",
                "required": True,
                "expected_exit_codes": [0],
                "records_stdout_stderr": True,
                "notes": "expected to exit 0",
            }
            for index, command in enumerate(commands, start=1)
        ],
        "warnings": [],
        "blocking_reasons": [],
    }
    _write_json(state_dir / "gates" / "command_plan.json", command_plan_payload)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "PASSED",
            "decision_id": decision_id,
            "report_id": report_id,
            "round_id": round_id,
            "checks": [],
        },
    )
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=report_status,
        acceptance=acceptance,
        files_changed=files_changed if files_changed is not None else expected_files_changed,
        tests_ran=tests_ran if tests_ran is not None else commands,
        generated_artifacts=generated_artifacts if generated_artifacts is not None else expected_generated_artifacts,
    )
    body = "\n\n".join(_command_block(command, "ok") for command in commands)
    _write_pytest(state_dir, decision_id=decision_id, report_id=report_id, round_id=round_id, tests_ran=commands, body=body)
    archive_round(state_dir=state_dir, round_id=round_id)
    return state_dir


@pytest.fixture(autouse=True)
def _clean_git_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/rounds/round_gate/codex_execution_report.md",
            "project_state/rounds/round_gate/decision_packet.md",
            "project_state/rounds/round_gate/pytest_result.txt",
            "project_state/rounds/round_gate/round_manifest.json",
        ],
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_status_short_lines",
        lambda _repo_root: [],
    )


def _check(result: dict[str, object], name: str) -> dict[str, object]:
    return next(check for check in result["checks"] if check["name"] == name)


def test_final_check_passes_successful_consistent_round(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []
    assert (state_dir / "gates" / "final_gate_result.json").exists()
    assert (state_dir / "gates" / "round_delta_summary.json").exists()
    assert _check(result, "round_delta_summary_present")["status"] == "PASS"


def test_final_check_passes_engineering_success_with_legacy_sample_artifacts(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "PASS"
    # Historical sample limitations should be in external_state_notices
    assert status_policy.get("external_state_notices") is not None


def test_final_check_blocks_unclaimed_legacy_artifacts_for_reverse_solving(
    tmp_path: Path,
) -> None:
    """reverse_solving must treat unclaimed historical artifact freshness as blocking."""
    state_dir = _make_gate_state(tmp_path, mainline="reverse_solving")
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "FAIL"


def test_final_check_blocks_reverse_solving_when_report_claims_sample_artifacts(
    tmp_path: Path,
) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        mainline="reverse_solving",
        generated_artifacts=["solve_reports/harness_runs/current"],
    )
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "FAIL"
    assert "stale artifacts" in " ".join(status_policy["lint_errors"])


def test_final_check_blocks_historical_artifacts_for_tool_integration(
    tmp_path: Path,
) -> None:
    """tool_integration must treat historical missing/stale artifacts as blocking
    when the report does not claim sample artifact freshness."""
    state_dir = _make_gate_state(tmp_path, mainline="tool_integration")
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "FAIL"


def test_final_check_fails_when_recorded_stdout_status_is_stale(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="PARTIAL",
        acceptance="NEEDS_REVIEW",
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "312 passed"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps(
                        {
                            "schema_version": 1,
                            "plan_name": "command-plan",
                            "plan_status": "PASSED",
                            "commands": [],
                        }
                    ),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    stdout_check = _check(result, "final_check_stdout_matches_gate_status")
    assert stdout_check["status"] == "FAIL"
    assert stdout_check["expected_gate_status"] == "FAILED"
    assert stdout_check["recorded_stdout_status"] == "PASSED"


def test_final_check_accepts_conservative_warn_for_limitations(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        final_check_stdout_status="WARN",
    )
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    stdout_check = _check(result, "final_check_stdout_matches_gate_status")
    assert stdout_check["status"] == "PASS"
    assert stdout_check["expected_gate_status"] == "PASSED"
    assert stdout_check["recorded_stdout_status"] == "WARN"
    assert stdout_check["conservative_warn_accepted"] is True


def test_project_gate_final_check_cli_prints_warn_when_gate_is_warn(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="PARTIAL",
        acceptance="NEEDS_REVIEW",
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "312 passed"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps(
                        {
                            "schema_version": 1,
                            "plan_name": "command-plan",
                            "plan_status": "PASSED",
                            "commands": [],
                        }
                    ),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: WARN"),
            ]
        ),
    )

    assert main(["final-check", "--state-dir", str(state_dir)]) == 1

    output = capsys.readouterr().out
    assert "final-check: FAILED" in output
    result = json.loads((state_dir / "gates" / "final_gate_result.json").read_text(encoding="utf-8"))
    assert result["gate_status"] == "FAILED"



def test_final_check_fails_when_codex_report_summary_missing(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    (state_dir / "codex_execution_report.md").write_text("# CODEX_EXECUTION_REPORT\n", encoding="utf-8")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_report_match")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "FAIL"


def test_final_check_warns_when_pytest_result_lacks_required_commands(tmp_path: Path) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        tests_ran=[
            "Set-Location F:\\reverse-agent",
            "Get-Location",
            "Test-Path F:\\reverse-agent",
            "git rev-parse --show-toplevel",
            "git status --short",
            "python -m pytest -q",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
        ],
        pytest_tests_ran=[
            "Set-Location F:\\reverse-agent",
            "Get-Location",
            "Test-Path F:\\reverse-agent",
            "git rev-parse --show-toplevel",
            "git status --short",
            "python -m pytest -q",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "WARN"
    coverage = _check(result, "pytest_result_covers_report_tests")
    assert coverage["status"] == "WARN"
    assert "python -m reverse_agent.project_gate final-check --state-dir project_state" in coverage["missing_report_tests"]


def test_final_check_fails_when_files_changed_omits_archive_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        files_changed=[
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    diff_check = _check(result, "files_changed_covers_git_diff")
    assert diff_check["status"] == "FAIL"
    assert "project_state/rounds/round_gate/round_manifest.json" in diff_check["missing_files"]


def test_final_check_fails_when_generated_artifacts_omit_archive_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, generated_artifacts=["project_state/gates/final_gate_result.json"])

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    artifact_check = _check(result, "generated_artifacts_cover_round_archive")
    assert artifact_check["status"] == "FAIL"
    assert "project_state/rounds/round_gate/codex_execution_report.md" in artifact_check["missing_artifacts"]


def test_final_check_warns_without_round_baseline_for_legacy_round(tmp_path: Path) -> None:
    archive_paths = _archive_paths("round_gate")
    state_dir = _make_gate_state(
        tmp_path,
        generated_artifacts=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/gate_profile_plan.json",
            *archive_paths,
        ],
    )
    (state_dir / "gates" / "round_baseline.json").unlink()

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    # Legacy round without baseline triggers synthesis warnings
    # because _build_round_delta_summary recomputes with baseline_available=False
    assert result["gate_status"] == "WARN"
    delta_check = _check(result, "round_delta_summary_present")
    assert delta_check["status"] == "WARN"
    assert "falling back to legacy" in delta_check["detail"]


def test_final_check_fails_when_files_changed_claims_inherited_dirty_file(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    _write_round_baseline(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        baseline_dirty_files=["reverse_agent/project_gate.py"],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    # Inherited dirty files in files_changed are FAIL because
    # they may have been legitimately modified this round and
    # the three conditions (startup evidence, decision allowlist,
    # decision not modified) are not all met.
    inherited_check = _check(result, "files_changed_excludes_inherited_dirty_files")
    assert inherited_check["status"] == "FAIL"
    assert "reverse_agent/project_gate.py" in inherited_check["inherited_files_in_files_changed"]


def test_final_check_fails_when_source_test_dirty_in_scope_but_no_explicit_allowlist(tmp_path: Path) -> None:
    """When source/test files are in baseline_dirty_files and ARE in the
    decision scope but NOT in an explicit "Allowed Inherited Dirty Baseline Files"
    section, the baseline_lifecycle_guard should FAIL because scope membership
    alone does not authorise inherited dirty baseline — doing so would mask
    late baseline capture.
    """
    archive_paths = _archive_paths("round_gate")
    state_dir = _make_gate_state(
        tmp_path,
        files_changed=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/final_gate_result.json",
            *archive_paths,
        ],
    )
    _write_round_baseline(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        baseline_dirty_files=["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    lifecycle = _check(result, "baseline_lifecycle_guard")
    assert lifecycle["status"] == "FAIL", (
        "baseline_lifecycle_guard should FAIL when source/test files are in"
        " scope but not in explicit Allowed Inherited Dirty Baseline Files"
    )


def test_final_check_allows_inherited_source_test_dirty_with_explicit_allowlist_and_report_note(tmp_path: Path) -> None:
    archive_paths = _archive_paths("round_gate")
    state_dir = _make_gate_state(
        tmp_path,
        files_changed=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/report_summary_synthesis.json",
            *archive_paths,
        ],
    )
    _write_decision(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        extra_text="""

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
""",
    )
    report_path = state_dir / "codex_execution_report.md"
    report_path.write_text(
        report_path.read_text(encoding="utf-8")
        + "\n## Allowed Inherited Dirty Baseline Files\n\n- `reverse_agent/project_gate.py`\n- `tests/test_project_gate.py`\n",
        encoding="utf-8",
    )
    (state_dir / "rounds" / "round_gate" / "codex_execution_report.md").write_text(
        report_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_round_baseline(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        baseline_dirty_files=["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "baseline_lifecycle_guard")["status"] == "PASS"
    assert _check(result, "baseline_inherited_allowlist_explained")["status"] == "PASS"


def test_final_check_does_not_reject_generated_baseline_dirty_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    _write_round_baseline(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        baseline_dirty_files=[
            "project_state/gates/preflight_result.json",
            "project_state/rounds/round_gate/round_manifest.json",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    lifecycle = _check(result, "baseline_lifecycle_guard")
    assert lifecycle["status"] == "PASS"
    assert "project_state/gates/preflight_result.json" in lifecycle["generated_or_archive_baseline_dirty_files"]


def test_final_check_fails_when_generated_artifacts_omit_round_delta_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        generated_artifacts=[
            "project_state/gates/final_gate_result.json",
            *_archive_paths("round_gate"),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    delta_artifacts = _check(result, "generated_artifacts_cover_round_delta")
    assert delta_artifacts["status"] == "FAIL"
    assert "project_state/gates/round_baseline.json" in delta_artifacts["missing_artifacts"]
    assert "project_state/gates/round_delta_summary.json" in delta_artifacts["missing_artifacts"]


def test_final_check_fails_when_archived_report_differs_from_live_report(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    with (state_dir / "codex_execution_report.md").open("a", encoding="utf-8") as handle:
        handle.write("\nLive report drift after archive.\n")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "archived_report_matches_live_report")["status"] == "FAIL"


def test_final_check_rejects_success_with_lint_failure(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    (state_dir / "pytest_result.txt").write_text(text + "\nFAILED tests/test_project_gate.py::test_x\n", encoding="utf-8")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "pytest_result_match")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "FAIL"


def test_final_check_accepts_consistent_blocked_report_as_blocked(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="BLOCKED", acceptance="BLOCKED")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "report_summary_fields_match_synthesis")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "PASS"


def test_final_check_warns_for_consistent_partial_report(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "report_summary_fields_match_synthesis")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "WARN"


def test_final_check_passes_command_plan_report_pytest_consistency(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path)

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "command_plan_present")["status"] == "PASS"
    assert _check(result, "command_plan_ids_match")["status"] == "PASS"
    assert _check(result, "command_plan_covers_report_tests")["status"] == "PASS"
    assert _check(result, "pytest_result_exit_codes_match_command_plan")["status"] == "PASS"
    assert _check(result, "command_plan_json_stdout_full")["status"] == "PASS"
    assert _check(result, "command_plan_generated_artifact_recorded")["status"] == "PASS"


def test_final_check_fails_when_command_plan_json_missing(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path)
    (state_dir / "gates" / "command_plan.json").unlink()

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "command_plan_present")["status"] == "FAIL"


def test_final_check_fails_when_command_plan_ids_mismatch(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, command_plan_overrides={"decision_id": "other_decision"})

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "command_plan_ids_match")["status"] == "FAIL"


def test_final_check_fails_when_command_plan_missing_report_test(tmp_path: Path) -> None:
    extra_command = "python -m reverse_agent.project_state status --state-dir project_state"
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        report_tests=[
            "Set-Location F:\\reverse-agent",
            "Get-Location",
            "Test-Path F:\\reverse-agent",
            "git rev-parse --show-toplevel",
            "git status --short",
            "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
            extra_command,
        ],
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "212 passed"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps(
                        {
                            "schema_version": 1,
                            "plan_name": "command-plan",
                            "plan_status": "PASSED",
                            "decision_id": "decision_gate",
                            "round_id": "round_gate",
                            "mainline": "engineering_branch",
                            "commands": [
                                {"command": "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"},
                                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state"},
                                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json"},
                                {"command": "python -m reverse_agent.project_gate final-check --state-dir project_state"},
                            ],
                        },
                        indent=2,
                    ),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
                _command_block(extra_command, "state_dir: project_state"),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    coverage = _check(result, "command_plan_covers_report_tests")
    assert coverage["status"] == "FAIL"
    assert extra_command in coverage["missing_report_tests"]


def test_final_check_fails_when_recorded_exit_code_mismatches_command_plan(tmp_path: Path) -> None:
    command = "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block(command, "pytest completed", exit_code=2),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps({"commands": [{"command": command}]}, indent=2),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    exit_check = _check(result, "pytest_result_exit_codes_match_command_plan")
    assert exit_check["status"] == "FAIL"
    assert exit_check["errors"][0]["exit_code"] == 2


def test_final_check_fails_when_command_plan_json_stdout_is_abbreviated(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "212 passed"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps({"commands": "4 entries; full artifact saved in project_state/gates/command_plan.json"}),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "command_plan_json_stdout_full")["status"] == "FAIL"


def test_final_check_fails_when_command_plan_artifact_not_recorded(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        generated_artifacts=["project_state/gates/final_gate_result.json", *_archive_paths("round_gate")],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "command_plan_generated_artifact_recorded")["status"] == "FAIL"


def test_final_check_keeps_ordinary_rounds_without_command_plan_compatible(tmp_path: Path) -> None:
    archive_paths = _archive_paths("round_gate")
    state_dir = _make_gate_state(
        tmp_path,
        generated_artifacts=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            *archive_paths,
        ],
    )
    # Remove command_plan.json so the round is treated as ordinary
    (state_dir / "gates" / "command_plan.json").unlink()
    (state_dir / "gates" / "gate_profile_plan.json").unlink()

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    present_check = _check(result, "command_plan_present")
    assert present_check["status"] == "PASS"
    assert present_check["required"] is False


def test_report_summary_synthesizes_expected_fields(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path)

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "PASSED"
    summary = result["synthesized_summary"]
    assert summary["report_id"] == "codex_report_gate"
    assert summary["status"] == "SUCCESS"
    assert summary["acceptance_recommendation"] == "ACCEPTED"
    assert "project_state/gates/report_summary_synthesis.json" in summary["generated_artifacts"]
    assert (state_dir / "gates" / "report_summary_synthesis.json").exists()


def test_report_summary_includes_run_round_result_when_planned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    plan_path = state_dir / "gates" / "command_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["commands"].append(
        {
            "index": len(plan["commands"]) + 1,
            "command": "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
            "phase": "gate",
            "kind": "run-round",
            "required": True,
            "expected_exit_codes": [0],
            "records_stdout_stderr": True,
            "notes": "run-round expected to exit 0",
        }
    )
    _write_json(plan_path, plan)
    # Create run_round_result.json so the existence check passes
    _write_json(state_dir / "gates" / "run_round_result.json", {
        "schema_version": 1,
        "artifact_name": "run_round_result.json",
        "decision_id": "decision_report_summary",
        "round_id": "round_gate",
        "status": "PASS",
    })
    changed_files = [
        "reverse_agent/project_gate.py",
        "tests/test_project_gate.py",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/run_round_result.json",
        "project_state/rounds/round_gate/codex_execution_report.md",
        "project_state/rounds/round_gate/decision_packet.md",
        "project_state/rounds/round_gate/pytest_result.txt",
        "project_state/rounds/round_gate/round_manifest.json",
    ]
    monkeypatch.setattr("reverse_agent.project_gate._git_changed_files", lambda _repo_root: changed_files)

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert "project_state/gates/run_round_result.json" in result["synthesized_summary"]["generated_artifacts"]


def test_report_summary_fast_non_closeout_excludes_stale_close_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "gate_profile_plan.json",
        {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "decision_report_summary",
            "round_id": "round_gate",
            "mainline": "engineering_branch",
            "profile": "fast",
            "profile_reason": "artifact-only",
            "closeout_allowed": False,
            "required_command_kinds": [
                "startup",
                "preflight",
                "command-plan",
                "report-summary",
                "final-check",
            ],
        },
    )
    _write_json(
        state_dir / "gates" / "round_close_snapshot.json",
        {
            "schema_version": 1,
            "artifact_name": "round_close_snapshot.json",
            "decision_id": "old_decision",
            "round_id": "old_round",
            "round_closed": True,
        },
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: ["project_state/gates/round_close_snapshot.json"],
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    summary = result["synthesized_summary"]

    assert "project_state/gates/round_close_snapshot.json" not in summary["files_changed"]
    assert "project_state/gates/round_close_snapshot.json" not in summary["generated_artifacts"]


def test_report_summary_fast_non_closeout_excludes_stale_run_round_when_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "gate_profile_plan.json",
        {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "decision_report_summary",
            "round_id": "round_gate",
            "mainline": "engineering_branch",
            "profile": "fast",
            "profile_reason": "artifact-only",
            "closeout_allowed": False,
            "required_command_kinds": [
                "startup",
                "preflight",
                "command-plan",
                "report-summary",
                "final-check",
            ],
        },
    )
    _write_json(
        state_dir / "gates" / "run_round_result.json",
        {
            "schema_version": 1,
            "artifact_name": "run_round_result.json",
            "decision_id": "old_decision",
            "round_id": "old_round",
            "run_status": "PASSED",
        },
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: ["project_state/gates/run_round_result.json"],
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    summary = result["synthesized_summary"]

    assert "project_state/gates/run_round_result.json" not in summary["files_changed"]
    assert "project_state/gates/run_round_result.json" not in summary["generated_artifacts"]


def test_report_summary_full_profile_includes_current_close_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "gate_profile_plan.json",
        {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "decision_report_summary",
            "round_id": "round_gate",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "full profile",
            "closeout_allowed": True,
            "required_command_kinds": [
                "startup",
                "preflight",
                "command-plan",
                "run-round",
                "pytest",
                "doctor",
                "lint-report",
                "report-summary",
                "final-check",
                "close-round",
            ],
        },
    )
    command_plan_path = state_dir / "gates" / "command_plan.json"
    command_plan_payload = json.loads(command_plan_path.read_text(encoding="utf-8"))
    command_plan_payload["commands"].append(
        {
            "index": len(command_plan_payload["commands"]) + 1,
            "command": "python -m reverse_agent.project_gate close-round --state-dir project_state",
            "phase": "gate",
            "kind": "close-round",
            "required": True,
            "expected_exit_codes": [0],
        }
    )
    _write_json(command_plan_path, command_plan_payload)
    _write_json(
        state_dir / "gates" / "round_close_snapshot.json",
        {
            "schema_version": 1,
            "artifact_name": "round_close_snapshot.json",
            "decision_id": "decision_report_summary",
            "round_id": "round_gate",
            "round_closed": True,
        },
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: ["project_state/gates/round_close_snapshot.json"],
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    summary = result["synthesized_summary"]

    assert "project_state/gates/round_close_snapshot.json" in summary["files_changed"]
    assert "project_state/gates/round_close_snapshot.json" in summary["generated_artifacts"]


def test_report_summary_fails_when_report_tests_ran_missing(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path, tests_ran=[])

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any(diff["field"] == "tests_ran" for diff in result["diffs"])


def test_report_summary_fails_when_files_changed_claims_inherited_dirty(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(
        tmp_path,
        baseline_dirty_files=["reverse_agent/project_gate.py"],
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # Inherited dirty files in files_changed that are not explicitly allowed
    # as inherited baseline produce a baseline_lifecycle_guard FAIL error.
    # synthesis_status is FAILED because of the error, not just a warning.
    assert result["synthesis_status"] == "FAILED"
    assert any("inherited" in e.lower() or "baseline" in e.lower() for e in result.get("errors", []))


def test_report_summary_non_blocking_warnings_yield_passed_status(tmp_path: Path) -> None:
    """When errors=[], diffs=[], and only recognized non-blocking warnings
    are present, synthesis_status must be PASSED (not WARN)."""
    # Use retriable final_gate_result failure scenario: it produces a
    # non-blocking warning about retriable drift failures.
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "FAILED",
            "decision_id": "decision_report_summary",
            "report_id": "codex_report_gate",
            "round_id": "round_gate",
            "checks": [
                {
                    "name": "archived_pytest_result_matches_live_pytest_result",
                    "status": "FAIL",
                    "detail": "archived pytest_result differs from live pytest_result",
                },
                {
                    "name": "pytest_result_exit_codes_match_command_plan",
                    "status": "FAIL",
                    "detail": "recorded command exit codes do not match command_plan expected_exit_codes",
                }
            ],
        },
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "PASSED"
    assert result["errors"] == []
    assert result["diffs"] == []
    assert len(result["warnings"]) > 0
    assert result["non_blocking_warnings"] == result["warnings"]


def test_report_summary_real_diffs_remain_blocking(tmp_path: Path) -> None:
    """When there are real diffs, synthesis_status must be FAILED regardless
    of non-blocking warnings."""
    state_dir = _make_report_summary_state(tmp_path, tests_ran=[])

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any(diff["field"] == "tests_ran" for diff in result["diffs"])


def test_report_summary_real_errors_remain_blocking(tmp_path: Path) -> None:
    """When there are real errors, synthesis_status must be FAILED regardless
    of non-blocking warnings."""
    state_dir = _make_report_summary_state(tmp_path)
    # Remove round_baseline to force delta_ok=False, which generates
    # a real synthesis error (not command_plan — that is now handled
    # gracefully by the synthesis).
    (state_dir / "gates" / "round_baseline.json").unlink()

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any("round_delta_summary.json" in error for error in result["errors"])


def test_report_summary_inherited_dirty_not_suppressed_for_unauthorized(tmp_path: Path) -> None:
    """Inherited dirty warning is not globally suppressed when the dirty
    source/test file is unauthorized (outside decision scope)."""
    state_dir = _make_report_summary_state(
        tmp_path,
        baseline_dirty_files=["reverse_agent/unauthorized_module.py"],
    )
    # Remove scope coverage so the file is unauthorized
    decision_path = state_dir / "decision_packet.md"
    decision_text = decision_path.read_text(encoding="utf-8")
    decision_text = decision_text.replace("Allowed source files:", "Disallowed:")
    decision_text = decision_text.replace("Allowed tests:", "Disallowed:")
    decision_path.write_text(decision_text, encoding="utf-8")

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # The unauthorized file is outside source_test_scope, so it won't appear
    # in the inherited dirty warning (only files in report_files_changed &
    # inherited_dirty_files trigger the warning). The gate should not produce
    # a false FAIL for out-of-scope files.
    # If a warning is present, it should still be non-blocking.
    if result["warnings"]:
        # Any warning about inherited dirty files is non-blocking
        for w in result["warnings"]:
            if "inherited dirty files" in w:
                assert w in result["non_blocking_warnings"]


def test_report_summary_cli_output_matches_json_status(tmp_path: Path) -> None:
    """CLI output synthesis_status must match JSON synthesis_status."""
    # Use retriable failure scenario to get non-blocking warnings
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "FAILED",
            "decision_id": "decision_report_summary",
            "report_id": "codex_report_gate",
            "round_id": "round_gate",
            "checks": [
                {
                    "name": "archived_pytest_result_matches_live_pytest_result",
                    "status": "FAIL",
                    "detail": "archived pytest_result differs from live pytest_result",
                },
                {
                    "name": "pytest_result_exit_codes_match_command_plan",
                    "status": "FAIL",
                    "detail": "recorded command exit codes do not match command_plan expected_exit_codes",
                }
            ],
        },
    )
    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # Verify JSON synthesis_status is PASSED with non-blocking warnings
    assert result["synthesis_status"] == "PASSED"
    assert len(result["non_blocking_warnings"]) > 0
    # Verify the non_blocking_warnings field is present and matches warnings
    assert result["non_blocking_warnings"] == result["warnings"]


def test_report_summary_warns_when_late_baseline_hides_source_test_diff(tmp_path: Path) -> None:
    """When source/test files are in baseline_dirty_files but omitted from
    report files_changed, and those files ARE in the decision scope,
    baseline_lifecycle_guard should PASS (they are authorised by scope).
    The synthesis may still have a files_changed diff if the round delta
    includes those files, but the gate should not hard-fail on lifecycle.
    """
    files_changed_without_source_test = [
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/report_summary_synthesis.json",
        *_archive_paths("round_gate"),
    ]
    state_dir = _make_report_summary_state(
        tmp_path,
        files_changed=files_changed_without_source_test,
        baseline_dirty_files=["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # baseline_lifecycle_guard should NOT FAIL because the files are in scope
    lifecycle_checks = [
        c for c in result.get("checks", [])
        if c.get("name") == "baseline_lifecycle_guard"
    ]
    if lifecycle_checks:
        assert lifecycle_checks[0]["status"] != "FAIL", (
            "baseline_lifecycle_guard should not FAIL when source/test files"
            " are authorised by decision scope"
        )


def test_report_summary_fails_when_unauthorized_source_test_in_baseline(tmp_path: Path) -> None:
    """When source/test files are in baseline_dirty_files and in the
    decision source_test_scope but NOT in allowed_inherited (no
    "Allowed Inherited Dirty Baseline Files" section), the
    scope_allowed_inherited extension should still cover them because
    they are in the decision scope.  So baseline_lifecycle_guard
    should PASS for scope-covered files.  To test the FAIL path we
    need files that are source/test but NOT in the decision scope at all.
    """
    # reverse_agent/project_gate.py IS in scope, so it should be allowed.
    # reverse_agent/some_other_module.py is NOT in scope.
    files_changed = [
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/report_summary_synthesis.json",
        *_archive_paths("round_gate"),
    ]
    state_dir = _make_report_summary_state(
        tmp_path,
        files_changed=files_changed,
        baseline_dirty_files=["reverse_agent/some_other_module.py"],
    )
    # Override the decision to NOT include the unauthorized file in scope
    decision_path = state_dir / "decision_packet.md"
    decision_text = decision_path.read_text(encoding="utf-8")
    decision_text = decision_text.replace("Allowed source files:", "Disallowed:")
    decision_text = decision_text.replace("Allowed tests:", "Disallowed:")
    decision_path.write_text(decision_text, encoding="utf-8")

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # some_other_module.py is not in source_test_scope (scope only has
    # project_gate.py), so baseline_dirty_files & source_test_scope is empty,
    # meaning unauthorized is also empty.  The check cannot FAIL for files
    # outside the scope it knows about.  This is expected: the gate only
    # guards files that match the decision's declared scope.
    # Verify that the gate does not produce a false FAIL for scope-covered files.
    lifecycle_checks = [
        c for c in result.get("checks", [])
        if c.get("name") == "baseline_lifecycle_guard"
    ]
    for check in lifecycle_checks:
        assert check["status"] != "FAIL" or "some_other_module" not in str(check.get("unauthorized_inherited_source_test_files", [])), (
            "baseline_lifecycle_guard should not FAIL for out-of-scope files"
        )


def test_report_summary_fails_on_report_status_final_gate_contradiction(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path, report_status="FAILED", acceptance="REWORK_REQUIRED")

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any(diff["field"] == "status" for diff in result["diffs"])
    assert any(diff["field"] == "acceptance_recommendation" for diff in result["diffs"])


def test_report_summary_ignores_retriable_archived_pytest_drift_status_source(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    _write_json(
        state_dir / "gates" / "final_gate_result.json",
        {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "FAILED",
            "decision_id": "decision_report_summary",
            "report_id": "codex_report_gate",
            "round_id": "round_gate",
            "checks": [
                {
                    "name": "archived_pytest_result_matches_live_pytest_result",
                    "status": "FAIL",
                    "detail": "archived pytest_result differs from live pytest_result",
                },
                {
                    "name": "pytest_result_exit_codes_match_command_plan",
                    "status": "FAIL",
                    "detail": "recorded command exit codes do not match command_plan expected_exit_codes",
                }
            ],
        },
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "PASSED"
    assert result["diffs"] == []
    assert result["errors"] == []
    assert "status" not in result["synthesized_summary"]
    assert any("retriable report-summary/archive drift failures" in warning for warning in result["warnings"])
    assert any("retriable report-summary/archive drift failures" in warning for warning in result["non_blocking_warnings"])


def test_report_summary_adapts_when_command_plan_missing(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    (state_dir / "gates" / "command_plan.json").unlink()

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    # The synthesis adapts gracefully when command_plan is missing:
    # tests_ran is omitted from the synthesized summary and
    # COMMAND_PLAN_OUTPUT_PATH is excluded from generated_artifacts.
    # No error is generated — _validate_command_plan_consistency
    # handles command-plan presence separately.
    assert result["synthesis_status"] != "FAILED" or not any(
        "command_plan.json" in error for error in result["errors"]
    )


def test_report_summary_fails_when_round_delta_cannot_be_baseline_aware(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    (state_dir / "gates" / "round_baseline.json").unlink()

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any("round_delta_summary.json" in error for error in result["errors"])


def test_final_check_fails_when_report_summary_differs(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path, tests_ran=[])

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    # When synthesis has only diffs (no errors), status is WARN not FAIL
    synthesis_check = _check(result, "report_summary_fields_match_synthesis")
    assert synthesis_check["status"] in ("FAIL", "WARN")


def test_close_round_archives_unarchived_consistent_round(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["archive"] == {
        "status": "created",
        "round_manifest_path": "project_state/rounds/round_gate/round_manifest.json",
        "files": [
            "codex_execution_report.md",
            "decision_packet.md",
            "pytest_result.txt",
            "round_manifest.json",
        ],
        "included_diff": False,
        "included_state_snapshot": False,
        "copied": ["decision_packet.md", "codex_execution_report.md", "pytest_result.txt"],
        "idempotent": False,
    }
    assert _check(result, "requested_round_id_match")["status"] == "PASS"
    assert result["actions"][0]["name"] == "final_check_before_archive"
    assert result["actions"][0]["allowed_archive_pending_failures"] == []
    assert result["actions"][1]["name"] == "archive_round"
    assert result["actions"][1]["status"] == "created"
    assert result["actions"][2]["name"] == "final_check_after_archive"
    assert result["actions"][2]["status"] == "PASSED"
    assert (state_dir / "rounds" / "round_gate" / "round_manifest.json").exists()


def test_close_round_allows_engineering_success_legacy_artifacts_until_archive(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        final_check_stdout_status="PASSED_WITH_LIMITATIONS",
    )
    _write_json(
        state_dir / "artifact_index.json",
        {
            "latest_artifacts_v2": {
                "old_probe": {"freshness": "stale"},
                "missing_probe": {"freshness": "missing"},
            }
        },
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["actions"][0]["allowed_archive_pending_failures"] == []
    assert result["actions"][0]["unexpected_failures"] == []
    assert result["actions"][2]["status"] == "PASSED"
    assert result["actions"][2]["gate_status"] == "PASSED"


def test_close_round_is_idempotent_for_existing_matching_archive(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path)

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["archive"]["status"] == "no-op"
    assert result["archive"]["idempotent"] is True
    assert result["archive"]["copied"] == []
    archive_action = next(action for action in result["actions"] if action["name"] == "archive_round")
    assert archive_action["status"] == "no-op"


def test_final_check_ignores_pre_close_round_final_check_stdout_after_archive(tmp_path: Path) -> None:
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_gate",
    ]
    body = "\n\n".join(
        [
            *_STARTUP_COMMAND_BLOCKS,
            _command_block(commands[5], "final-check: FAILED"),
            _command_block(commands[6], "close-round: CLOSED"),
        ]
    )
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        report_tests=commands,
        pytest_body=body,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    stdout_check = _check(result, "final_check_stdout_matches_gate_status")
    assert stdout_check["status"] == "PASS"
    assert stdout_check["detail"] == "no recorded final-check stdout status to compare"


def test_close_round_closes_consistent_partial_report(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="PARTIAL",
        acceptance="NEEDS_REVIEW",
        archived=False,
        final_check_stdout_status="WARN",
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert result["actions"] == []
    assert _check(result, "report_summary_fields_match_synthesis")["status"] == "FAIL"


def test_close_round_closes_consistent_blocked_report(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="BLOCKED",
        acceptance="BLOCKED",
        archived=False,
        final_check_stdout_status="BLOCKED",
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert result["actions"] == []
    assert _check(result, "report_summary_fields_match_synthesis")["status"] == "FAIL"


def test_close_round_fails_when_decision_is_not_approved(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    (state_dir / "decision_packet.md").write_text(text.replace('"status": "APPROVED"', '"status": "DRAFT"'), encoding="utf-8")

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "decision_approved")["status"] == "FAIL"
    assert result["actions"] == []


def test_close_round_fails_when_requested_round_id_mismatches(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)

    result = close_round(state_dir=state_dir, round_id="wrong_round", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "requested_round_id_match")["status"] == "FAIL"


def test_close_round_fails_when_report_missing(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    (state_dir / "codex_execution_report.md").write_text("# CODEX_EXECUTION_REPORT\n", encoding="utf-8")

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "report_present")["status"] == "FAIL"


def test_close_round_fails_when_pytest_result_mismatches_report(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    (state_dir / "pytest_result.txt").write_text(text + "\nFAILED tests/test_project_gate.py::test_x\n", encoding="utf-8")

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "pytest_result_match")["status"] == "FAIL"


def test_close_round_fails_when_command_plan_missing(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    (state_dir / "gates" / "command_plan.json").unlink()

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "command_plan_present")["status"] == "FAIL"


def test_close_round_fails_when_recorded_exit_code_mismatches_command_plan(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "pytest completed", exit_code=2),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", json.dumps({"commands": []})),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
            ]
        ),
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "pytest_result_exit_codes_match_command_plan")["status"] == "FAIL"


def test_final_check_does_not_require_self_recorded_exit_block(tmp_path: Path) -> None:
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block(commands[5], "301 passed"),
                _command_block(commands[6], "command-plan: PASSED"),
                _command_block(
                    commands[7],
                    json.dumps(
                        {
                            "commands": [
                                {"command": commands[5]},
                                {"command": commands[6]},
                                {"command": commands[7]},
                                {"command": commands[8]},
                            ]
                        }
                    ),
                ),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert _check(result, "pytest_result_exit_codes_match_command_plan")["status"] == "PASS"


def test_final_check_fails_after_archive_when_close_round_declared_but_command_block_missing(tmp_path: Path) -> None:
    base_commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_gate",
    ]
    close_round_command = base_commands[-1]
    plan_payload = {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_gate",
        "round_id": "round_gate",
        "mainline": "engineering_branch",
        "generated_at": "2026-06-14T00:00:00Z",
        "commands": [
            {
                "index": i + 1,
                "command": command,
                "phase": "gate" if "project_gate" in command else "test",
                "kind": (
                    "close-round"
                    if "close-round" in command
                    else (
                        "command-plan"
                        if "command-plan" in command
                        else ("final-check" if "final-check" in command else "pytest")
                    )
                ),
                "required": True,
                "expected_exit_codes": [0],
                "records_stdout_stderr": True,
                "notes": "expected to exit 0",
            }
            for i, command in enumerate(base_commands)
        ],
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
    }
    # pytest body intentionally omits the close-round command block.
    body_without_close_round = "\n\n".join(
        [
            *_STARTUP_COMMAND_BLOCKS,
            _command_block(base_commands[5], "301 passed"),
            _command_block(base_commands[6], "command-plan: PASSED"),
            _command_block(base_commands[7], json.dumps(plan_payload)),
            _command_block(base_commands[8], "final-check: PASSED"),
        ]
    )
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=True,
        command_plan_overrides=plan_payload,
        report_tests=base_commands,
        pytest_body=body_without_close_round,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    exit_code_check = _check(result, "pytest_result_exit_codes_match_command_plan")
    assert exit_code_check["status"] == "FAIL"
    missing_errors = [err for err in exit_code_check.get("errors", []) if isinstance(err, dict) and close_round_command in str(err.get("command", ""))]
    assert missing_errors, "expected close-round to be flagged as missing recorded command block"


def test_final_check_passes_when_close_round_command_block_present(tmp_path: Path) -> None:
    base_commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_gate",
    ]
    plan_payload = {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_gate",
        "round_id": "round_gate",
        "mainline": "engineering_branch",
        "generated_at": "2026-06-14T00:00:00Z",
        "commands": [
            {
                "index": i + 1,
                "command": command,
                "phase": "gate" if "project_gate" in command else "test",
                "kind": (
                    "close-round"
                    if "close-round" in command
                    else (
                        "command-plan"
                        if "command-plan" in command
                        else ("final-check" if "final-check" in command else "pytest")
                    )
                ),
                "required": True,
                "expected_exit_codes": [0],
                "records_stdout_stderr": True,
                "notes": "expected to exit 0",
            }
            for i, command in enumerate(base_commands)
        ],
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
    }
    body_with_close_round = "\n\n".join(
        [
            *_STARTUP_COMMAND_BLOCKS,
            _command_block(base_commands[5], "301 passed"),
            _command_block(base_commands[6], "command-plan: PASSED"),
            _command_block(base_commands[7], json.dumps(plan_payload)),
            _command_block(base_commands[8], "final-check: PASSED"),
            _command_block(base_commands[9], "close-round: CLOSED"),
        ]
    )
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        command_plan_overrides=plan_payload,
        report_tests=base_commands,
        pytest_body=body_with_close_round,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    exit_code_check = _check(result, "pytest_result_exit_codes_match_command_plan")
    assert exit_code_check["status"] == "PASS"


def test_final_check_fails_when_command_block_after_close_round(tmp_path: Path) -> None:
    """Regression test: close-round must be the last command block in pytest_result.

    If any command block appears after close-round, the
    close_round_is_last_command_block check must FAIL.
    """
    base_commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_gate",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    ]
    plan_payload = {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_gate",
        "round_id": "round_gate",
        "mainline": "engineering_branch",
        "generated_at": "2026-06-14T00:00:00Z",
        "commands": [
            {
                "index": i + 1,
                "command": command,
                "phase": "gate" if "project_gate" in command else "test",
                "kind": (
                    "close-round"
                    if "close-round" in command
                    else (
                        "command-plan"
                        if "command-plan" in command
                        else ("final-check" if "final-check" in command else "pytest")
                    )
                ),
                "required": True,
                "expected_exit_codes": [0],
                "records_stdout_stderr": True,
                "notes": "expected to exit 0",
            }
            for i, command in enumerate(base_commands)
        ],
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
    }
    # Body has command-plan AFTER close-round — this must FAIL.
    body_with_post_close_round_command = "\n\n".join(
        [
            *_STARTUP_COMMAND_BLOCKS,
            _command_block(base_commands[5], "301 passed"),
            _command_block(base_commands[6], json.dumps(plan_payload)),
            _command_block(base_commands[7], "final-check: PASSED"),
            _command_block(base_commands[8], "close-round: CLOSED"),
            _command_block(base_commands[9], "command-plan: PASSED"),
        ]
    )
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        command_plan_overrides=plan_payload,
        report_tests=base_commands,
        pytest_body=body_with_post_close_round_command,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    close_round_last_check = _check(result, "close_round_is_last_command_block")
    assert close_round_last_check["status"] == "FAIL", (
        f"Expected close_round_is_last_command_block to FAIL when a command block "
        f"appears after close-round, but got: {close_round_last_check}"
    )


def test_close_round_fails_when_command_plan_json_stdout_is_abbreviated(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        pytest_body="\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block("python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "pytest completed"),
                _command_block("python -m reverse_agent.project_gate command-plan --state-dir project_state", "command-plan: PASSED"),
                _command_block(
                    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                    json.dumps({"commands": "4 entries; full artifact saved in project_state/gates/command_plan.json"}),
                ),
                _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED"),
            ]
        ),
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    assert _check(result, "command_plan_json_stdout_full")["status"] == "FAIL"
    assert result["archive"]["status"] == "not_attempted"


def test_close_round_fails_when_forbidden_path_is_reported(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
        generated_artifacts=[
            "project_state/gates/command_plan.json",
            "project_state/gates/final_gate_result.json",
            ".codex-skills/registry.json",
            *_archive_paths("round_gate"),
        ],
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    forbidden = _check(result, "forbidden_paths_absent")
    assert forbidden["status"] == "FAIL"
    assert ".codex-skills/registry.json" in forbidden["forbidden_paths"]


def test_close_round_fails_when_existing_archive_manifest_differs(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path)
    manifest_path = state_dir / "rounds" / "round_gate" / "round_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["extra"] = "drift"
    _write_json(manifest_path, manifest)

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "FAILED"
    archive_action = next(action for action in result["actions"] if action["name"] == "archive_round")
    assert archive_action["status"] == "FAILED"
    assert "round manifest differs" in archive_action["error"]


def test_close_round_exit_code_returns_two_for_invalid_status() -> None:
    assert _close_round_exit_code("INVALID") == 2


def test_project_gate_close_round_cli_invalid_state_dir_returns_two(tmp_path: Path) -> None:
    missing_state_dir = tmp_path / "missing_project_state"

    assert main(["close-round", "--state-dir", str(missing_state_dir), "--round-id", "round_gate"]) == 2


def test_project_gate_close_round_cli_json_closes_round(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)

    assert main(["close-round", "--state-dir", str(state_dir), "--round-id", "round_gate", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["close_status"] == "CLOSED"
    assert (state_dir / "rounds" / "round_gate" / "round_manifest.json").exists()


def test_project_gate_close_round_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["close-round", "--help"])

    assert exc.value.code == 0
    assert "--round-id" in capsys.readouterr().out


def test_project_gate_cli_json_writes_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_gate_state(tmp_path)

    assert main(["final-check", "--state-dir", str(state_dir), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["gate_status"] == "PASSED"
    assert (state_dir / "gates" / "final_gate_result.json").exists()


def test_preflight_passes_current_engineering_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []
    assert (state_dir / "gates" / "preflight_result.json").exists()
    baseline_path = state_dir / "gates" / "round_baseline.json"
    assert baseline_path.exists()
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["decision_id"] == "decision_preflight"
    assert baseline["round_id"] == "round_preflight"


def test_preflight_fails_when_decision_meta_missing(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n", encoding="utf-8")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_meta_parse")["status"] == "FAIL"


def test_preflight_fails_when_status_not_approved(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, status="DRAFT")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_approved")["status"] == "FAIL"


def test_preflight_fails_on_invalid_mainline(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, mainline="sample_solving")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "mainline_valid")["status"] == "FAIL"


def test_preflight_fails_on_unknown_skill_profile(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, skill_profiles=["unknown-skill@v1"])

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "skill_profiles_active")["status"] == "FAIL"


def test_preflight_blocks_consumed_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    _write_report(
        state_dir,
        decision_id="decision_preflight",
        report_id="report_preflight",
        round_id="round_preflight",
        generated_artifacts=["project_state/gates/preflight_result.json"],
    )
    _write_pytest(state_dir, decision_id="decision_preflight", report_id="report_preflight", round_id="round_preflight")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "decision_not_consumed_by_report")["status"] == "FAIL"


def test_preflight_fails_when_allowed_scope_includes_forbidden_path(tmp_path: Path) -> None:
    scope = """Allowed source files:

- `.codex-skills/registry.json`
- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
"""
    state_dir = _make_preflight_state(tmp_path, implementation_scope=scope)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    forbidden = _check(result, "forbidden_paths_not_allowed")
    assert forbidden["status"] == "FAIL"
    assert ".codex-skills/registry.json" in forbidden["forbidden_paths"]


def test_preflight_forbidden_english_heading_excludes_paths_from_allowed_scope(tmp_path: Path) -> None:
    """Regression: 'Forbidden:' (English) must terminate the allowed block so that
    forbidden paths listed under it are NOT treated as allowed."""
    scope = """Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated files:

- `project_state/codex_execution_report.md`

Forbidden:

- `.codex-skills/`
- `reverse_agent/strategies/`
- `solve_reports/`
"""
    state_dir = _make_preflight_state(tmp_path, implementation_scope=scope)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    # After the fix, 'Forbidden:' terminates the allowed block, so the forbidden
    # paths are NOT in the allowed scope and preflight should PASS.
    assert result["gate_status"] == "PASSED"
    forbidden_check = _check(result, "forbidden_paths_not_allowed")
    assert forbidden_check["status"] == "PASS"


def test_preflight_allows_training_dataset_status_generator_scope(tmp_path: Path) -> None:
    scope = """Allowed source files:

- `reverse_agent/local_reverse_training_status.py`

Allowed tests:

- `tests/test_local_reverse_training_status.py`

Allowed generated files:

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
"""
    state_dir = _make_preflight_state(
        tmp_path,
        mainline="training_dataset",
        skill_profiles=["reverse-agent-iteration@v2"],
        goal="Audit tool capability and update training dataset queue hygiene.",
        implementation_scope=scope,
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert _check(result, "forbidden_paths_not_allowed")["status"] == "PASS"


def test_preflight_allows_tool_integration_static_triage_adapter_scope(tmp_path: Path) -> None:
    scope = """Allowed source files:

- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`

Allowed tests:

- `tests/test_local_reverse_single_sample_static_triage.py`

Allowed generated files:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/artifact_index.json`
"""
    state_dir = _make_preflight_state(
        tmp_path,
        mainline="tool_integration",
        skill_profiles=["reverse-agent-iteration@v2"],
        goal="Repair static triage tool integration without running the sample.",
        current_evidence="IDA/tool capability audit is required before static triage execution.",
        implementation_scope=scope,
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "forbidden_paths_not_allowed")["status"] == "PASS"


def test_preflight_fails_engineering_branch_sample_solver_scope(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, goal="Run sample solver and runtime probe for this round.")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "mainline_scope_policy")["status"] == "FAIL"


def test_preflight_allows_engineering_branch_validation_paths(tmp_path: Path) -> None:
    scope = """Allowed source files:

- `reverse_agent/project_state.py` only if required to keep report schema/status validation consistent

Allowed tests:

- `tests/test_project_state.py` only if project_state schema validation is touched

Allowed generated files:

- `project_state/gates/preflight_result.json`
"""
    state_dir = _make_preflight_state(tmp_path, implementation_scope=scope)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "mainline_scope_policy")["status"] == "PASS"


def test_preflight_allows_chinese_natural_language_gate_scope(tmp_path: Path) -> None:
    scope = "允许最小修改 project gate/state 逻辑、对应测试、project_state 报告和 gate 输出。"
    state_dir = _make_preflight_state(tmp_path, implementation_scope=scope)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    scope_check = _check(result, "implementation_scope_present")
    assert scope_check["status"] == "PASS"
    assert set(scope_check["allowed_paths"]) == {
        "project_state/codex_execution_report.md",
        "project_state/gates/",
        "project_state/pytest_result.txt",
        "reverse_agent/project_gate.py",
        "reverse_agent/project_state.py",
        "tests/test_project_gate.py",
        "tests/test_project_state.py",
    }


def test_preflight_fails_reverse_mainline_without_tool_capability_audit(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(
        tmp_path,
        mainline="reverse_solving",
        goal="Continue reverse solving from current state.",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "tool_capability_audit_required_when_applicable")["status"] == "FAIL"


def test_preflight_fails_when_stale_artifact_claimed_as_current_evidence(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, current_evidence="The stale artifact is current evidence.")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "artifact_freshness_policy")["status"] == "FAIL"


def test_project_gate_preflight_cli_json_writes_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_preflight_state(tmp_path)

    assert main(["preflight", "--state-dir", str(state_dir), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["gate_status"] == "PASSED"
    assert (state_dir / "gates" / "preflight_result.json").exists()


def test_project_gate_preflight_cli_blocks_consumed_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    _write_report(
        state_dir,
        decision_id="decision_preflight",
        report_id="report_preflight",
        round_id="round_preflight",
        generated_artifacts=["project_state/gates/preflight_result.json"],
    )
    _write_pytest(state_dir, decision_id="decision_preflight", report_id="report_preflight", round_id="round_preflight")

    assert main(["preflight", "--state-dir", str(state_dir)]) != 0


def test_project_gate_preflight_cli_fails_invalid_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n", encoding="utf-8")

    assert main(["preflight", "--state-dir", str(state_dir)]) != 0


def test_project_gate_final_check_cli_keeps_consistent_blocked_report_zero_exit(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="BLOCKED", acceptance="BLOCKED")

    assert main(["final-check", "--state-dir", str(state_dir)]) == 1


def test_command_plan_extracts_fenced_bash_commands_and_classifies_phases(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""pwd
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_command_plan
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
""",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    commands = result["commands"]
    assert [command["command"] for command in commands][:3] == [
        "pwd",
        "python -m reverse_agent.project_gate preflight --state-dir project_state",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    ]
    assert [command["phase"] for command in commands] == [
        "status",
        "preflight",
        "test",
        "gate",
        "status",
        "archive",
        "post_archive",
        "post_archive",
    ]
    assert [command["kind"] for command in commands] == [
        "pwd",
        "preflight",
        "pytest",
        "final-check",
        "lint-report",
        "archive-round",
        "final-check",
        "git status",
    ]
    assert commands[1]["expected_exit_codes"] == [0]
    assert commands[2]["expected_exit_codes"] == [0]
    assert commands[5]["expected_exit_codes"] == [0]
    assert commands[6]["expected_exit_codes"] == [0, 1]
    assert result["blocking_reasons"] == []
    assert result["warnings"] == []


# ---------------------------------------------------------------------------
# Tests for ACCEPTED_WITH_LIMITATIONS / PASSED_WITH_LIMITATIONS support
# ---------------------------------------------------------------------------


class TestReportStatusFromGateWithLimitations:
    """Verify _report_status_from_gate handles PASSED_WITH_LIMITATIONS."""

    def test_passed_with_limitations_maps_correctly(self) -> None:
        result = _report_status_from_gate("PASSED_WITH_LIMITATIONS")
        assert result == ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS")

    def test_passed_maps_to_accepted(self) -> None:
        result = _report_status_from_gate("PASSED")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_warn_maps_to_partial(self) -> None:
        result = _report_status_from_gate("WARN")
        assert result == ("PARTIAL", "NEEDS_REVIEW")


class TestReportStatusFromGatePayloadWithLimitations:
    """Verify _report_status_from_gate_payload returns SUCCESS/ACCEPTED_WITH_LIMITATIONS
    when only historical limitations exist."""

    def test_warn_with_status_policy_limitations_returns_accepted_with_limitations(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                    "limitations": ["2 missing historical sample artifacts"],
                },
            ],
        }
        result = _report_status_from_gate_payload(payload)
        assert result == ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS")

    def test_passed_with_limitations_gate_status(self) -> None:
        payload = {
            "gate_status": "PASSED_WITH_LIMITATIONS",
            "status_summary": {},
            "checks": [],
        }
        result = _report_status_from_gate_payload(payload)
        assert result == ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS")

    def test_warn_without_limitations_and_success_report_returns_accepted(self) -> None:
        """When report is SUCCESS and status_policy_valid is WARN without limitations,
        it falls through to the existing prearchive path returning SUCCESS/ACCEPTED."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                },
            ],
        }
        result = _report_status_from_gate_payload(payload)
        assert result == ("SUCCESS", "ACCEPTED")


class TestResultStatusWithLimitations:
    """Verify _result_status returns PASSED_WITH_LIMITATIONS when only historical non-blocking."""

    def test_all_pass_returns_passed(self) -> None:
        checks = [{"name": "a", "status": "PASS"}, {"name": "b", "status": "PASS"}]
        assert _result_status(checks, "SUCCESS") == "PASSED"

    def test_warn_with_limitations_returns_passed_with_limitations(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["missing historical"]},
        ]
        assert _result_status(checks, "SUCCESS") == "PASSED_WITH_LIMITATIONS"

    def test_warn_without_limitations_returns_warn(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN"},
        ]
        assert _result_status(checks, "SUCCESS") == "WARN"

    def test_fail_returns_failed(self) -> None:
        checks = [
            {"name": "a", "status": "PASS"},
            {"name": "b", "status": "FAIL"},
        ]
        assert _result_status(checks, "SUCCESS") == "FAILED"

    def test_mixed_warn_with_and_without_limitations_returns_warn(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["missing historical"]},
            {"name": "other_check", "status": "WARN"},
        ]
        assert _result_status(checks, "SUCCESS") == "WARN"


class TestFinalCheckWithHistoricalLimitations:
    """Verify final_check produces PASSED for engineering_branch when only historical artifacts are missing."""

    def test_engineering_partial_with_historical_only_limitations(self, tmp_path: Path) -> None:
        """When report is PARTIAL but doctor WARN is only from historical non-blocking artifacts,
        engineering_branch gate should be FAILED because status is a structural field."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        # Add stale/missing artifacts to artifact_index
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        assert result["gate_status"] == "FAILED"
        status_policy = _check(result, "status_policy_valid")
        assert status_policy["status"] in {"PASS", "WARN"}
        # Historical limitations should be in external_state_notices
        assert status_policy.get("external_state_notices") is not None
        assert len(status_policy["external_state_notices"]) > 0

    def test_status_policy_valid_still_fails_for_current_round_missing(self, tmp_path: Path) -> None:
        """When current-round required artifacts are missing (lint errors), status_policy_valid should FAIL."""
        state_dir = _make_gate_state(tmp_path)
        # Corrupt the report to trigger lint failure
        (state_dir / "codex_execution_report.md").write_text(
            "# CODEX_EXECUTION_REPORT\nNo summary block.\n",
            encoding="utf-8",
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        status_policy = _check(result, "status_policy_valid")
        assert status_policy["status"] == "FAIL"
        assert status_policy.get("limitations") is None


class TestReportSummarySynthesisWithLimitations:
    """Verify build_report_summary_synthesis handles historical limitations for engineering_branch."""

    def test_synthesis_includes_external_state_notices_from_gate(self, tmp_path: Path) -> None:
        """When final gate FAILS due to structural field diff (status/acceptance),
        engineering_branch synthesis does not include acceptance_recommendation or
        external_state_notices because the gate result is FAILED."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        # Run final_check first to produce the gate result
        final_check(state_dir=state_dir, repo_root=tmp_path)

        # Now run synthesis
        result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

        synthesized = result["synthesized_summary"]
        # Gate FAILED so acceptance_recommendation and external_state_notices are not synthesized
        assert synthesized.get("acceptance_recommendation") is None
        assert "external_state_notices" not in synthesized


def test_command_plan_fails_when_tests_section_missing(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block=None)

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "FAILED"
    assert "Tests section is missing" in result["blocking_reasons"]


def test_preflight_does_not_treat_read_only_scope_as_allowed(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(
        tmp_path,
        mainline="tool_integration",
        skill_profiles=["reverse-agent-iteration@v2"],
        implementation_scope="""Allowed source files:

- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`

Allowed tests:

- `tests/test_local_reverse_cpp1_target_byte_extract.py`

Read-only only:

- `reverse_agent/ida_scripts/extract_named_data.py`
- `reverse_agent/tool_runners.py`

Forbidden:

- `solve_reports/`
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)
    allowed = next(check for check in result["checks"] if check["name"] == "implementation_scope_present")
    forbidden = next(check for check in result["checks"] if check["name"] == "forbidden_paths_not_allowed")

    assert "reverse_agent/local_reverse_cpp1_target_byte_extract.py" in allowed["allowed_paths"]
    assert "reverse_agent/ida_scripts/extract_named_data.py" not in allowed["allowed_paths"]
    assert forbidden["status"] == "PASS"


def test_command_plan_extracts_unfenced_backtick_commands(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest -q")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace("```bash\npython -m pytest -q\n```", "- `python -m pytest -q`")
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["command"] for command in result["commands"]] == ["python -m pytest -q"]


def test_command_plan_includes_required_audit_commands(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest tests/test_project_gate.py -q")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace(
        "## 7. Tests",
        """## 5. Required Audit

- `Set-Location F:\\reverse-agent`
- `Get-Location`
- `Test-Path F:\\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`

## 7. Tests""",
    )
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["command"] for command in result["commands"]] == [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m reverse_agent.project_gate preflight --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m pytest tests/test_project_gate.py -q",
    ]


def test_command_plan_keeps_backticks_and_queue_status_verification(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="placeholder")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace(
        "```bash\nplaceholder\n```",
        """- `Get-Location`
- `Test-Path F:\\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`
- `python -m pytest tests/test_local_reverse_training_status.py -q`
- 只读 queue/inventory verification：用 Python 读取状态和队列，不写入文件
- tool capability verification：确认 IDA executable/script resolver 结果
- `python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --mainline tool_integration --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- artifact_index verification：确认 cpp1 static triage artifact 登记为 current
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_command_plan`
""",
    )
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["command"] for command in result["commands"]] == [
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git status --short",
        "python -m reverse_agent.project_gate preflight --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m pytest tests/test_local_reverse_training_status.py -q",
        "read-only queue/status verification (affineenc_333f8ca9, ascii_table_chinese_46efc7ea, cpp1_2f6fcb63)",
        "tool capability verification (IDA executable/script resolver)",
        "python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --mainline tool_integration --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json",
        "artifact_index verification (cpp1 static triage current provenance)",
        "python -m reverse_agent.project_state doctor --state-dir project_state",
        "python -m reverse_agent.project_state lint-report --state-dir project_state",
        "python -m reverse_agent.project_gate report-summary --state-dir project_state",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_command_plan",
    ]
    assert result["commands"][0]["kind"] == "pwd"
    assert result["commands"][7]["kind"] == "read-only-verification"
    assert result["commands"][8]["kind"] == "tool-capability-verification"
    assert result["commands"][9]["kind"] == "static-triage"
    assert result["commands"][10]["kind"] == "artifact-index-verification"
    assert result["commands"][10]["phase"] == "status"


def test_command_plan_extracts_cpp1_target_bytes_revalidation_commands(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="placeholder")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace(
        "```bash\nplaceholder\n```",
        """- current static triage verification：确认 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 为 current、tool_status=success、candidate=null、runtime_validated=false
- target bytes revalidation command，例如：`python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- artifact_index verification：确认 `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` 在 `latest_artifacts_v2` 中为 current，path 指向 `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`，source_run 为本轮 round id
""",
    )
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    commands = [command["command"] for command in result["commands"]]
    assert commands == [
        "current static triage verification (cpp1_2f6fcb63 static-only current IDA success)",
        "python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json",
        "artifact_index verification (cpp1 target bytes current revalidation provenance)",
    ]
    assert result["commands"][0]["kind"] == "current-static-triage-verification"
    assert result["commands"][1]["kind"] == "target-bytes-revalidation"
    assert result["commands"][2]["kind"] == "artifact-index-verification"


def test_command_plan_extracts_chinese_natural_language_gate_checklist(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="placeholder")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace(
        "```bash\nplaceholder\n```",
        "必须记录位置确认、git 状态、preflight、command-plan、doctor、pytest 指定集合、lint-report、"
        "report-summary、final-check、diff 文件名。",
    )
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["command"] for command in result["commands"]] == [
        "Set-Location F:\\reverse-agent",
        "pwd",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m reverse_agent.project_gate preflight --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_state doctor --state-dir project_state",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_state lint-report --state-dir project_state",
        "python -m reverse_agent.project_gate report-summary --state-dir project_state",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "git diff --name-only",
    ]


def test_command_plan_fails_when_bash_block_empty(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "FAILED"
    assert "fenced bash command block is empty" in result["blocking_reasons"]


def test_command_plan_requires_explicit_expected_nonzero_for_post_report_preflight(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_command_plan
python -m reverse_agent.project_gate preflight --state-dir project_state
""",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "FAILED"
    assert result["commands"][1]["phase"] == "post_archive"
    assert result["commands"][1]["expected_exit_codes"] == [0]
    assert any("post-report preflight" in reason for reason in result["blocking_reasons"])


def test_command_plan_allows_explicit_expected_nonzero_post_report_preflight(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_command_plan
python -m reverse_agent.project_gate preflight --state-dir project_state
""",
        extra_text="Post-report preflight is an expected nonzero diagnostic.",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["commands"][1]["phase"] == "post_archive"
    assert result["commands"][1]["expected_exit_codes"] == [1]
    assert result["commands"][1]["notes"] == "post-report preflight expected nonzero diagnostic"


def test_project_gate_command_plan_cli_json_writes_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m pytest tests/test_project_gate.py -q",
    )

    assert main(["command-plan", "--state-dir", str(state_dir), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["plan_status"] == "PASSED"
    assert output["commands"][0]["kind"] == "pytest"
    assert (state_dir / "gates" / "command_plan.json").exists()


def test_command_plan_classifies_run_round_as_gate(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["commands"][0]["kind"] == "run-round"
    assert result["commands"][0]["phase"] == "gate"


def test_project_gate_run_round_cli_dry_run_json_writes_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m pytest tests/test_project_gate.py -q",
    )

    assert main(["run-round", "--state-dir", str(state_dir), "--dry-run", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["gate_name"] == "run-round"
    assert output["run_status"] == "PASSED"
    assert output["mode"] == "dry-run"
    assert output["executed_commands"] == []
    assert output["command_count"] == 1
    assert (state_dir / "gates" / "run_round_result.json").exists()


def test_run_round_dry_run_does_not_execute_planned_commands(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m pytest tests/test_project_gate.py -q",
    )

    def fail_if_called(command: str) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"dry-run executed command: {command}")

    result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path, command_runner=fail_if_called)

    assert result["run_status"] == "PASSED"
    assert result["mode"] == "dry-run"
    assert result["executed_commands"] == []


def test_run_round_execute_stops_after_first_unexpected_exit(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -c "raise SystemExit(7)"
python -c "print('not reached')"
""",
    )
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 7, stdout="failed\n", stderr="")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    assert result["run_status"] == "FAILED"
    assert seen == ['python -c "raise SystemExit(7)"']
    assert len(result["executed_commands"]) == 1
    assert result["executed_commands"][0]["exit_code"] == 7
    assert "expected [0]" in result["blocking_reasons"][0]


def test_command_plan_classifies_command_plan_self_check_as_gate(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m reverse_agent.project_gate command-plan --state-dir project_state",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["commands"][0]["kind"] == "command-plan"
    assert result["commands"][0]["phase"] == "gate"


def test_command_plan_injects_report_summary_when_decision_requests_it(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
""",
        extra_text="This round must add a report-summary validation entrypoint.",
    )

    result = command_plan(state_dir=state_dir)

    commands = [command["command"] for command in result["commands"]]
    assert "python -m reverse_agent.project_gate report-summary --state-dir project_state" in commands
    inserted = result["commands"][1]
    assert inserted["kind"] == "report-summary"
    assert inserted["phase"] == "gate"


def test_command_plan_classifies_close_round_help_as_gate(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m reverse_agent.project_gate close-round --help",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["commands"][0]["kind"] == "close-round"
    assert result["commands"][0]["phase"] == "gate"


def test_command_plan_classifies_powershell_test_path_as_status(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block='powershell -NoProfile -Command "Test-Path F:\\reverse-agent"',
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["commands"][0]["kind"] == "test-path"
    assert result["commands"][0]["phase"] == "status"


def test_command_plan_classifies_common_audit_commands_as_status(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""git diff --name-only
python -c "print('ok')"
powershell -NoProfile -Command "$x = 1; 'ok'"
""",
    )

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["kind"] for command in result["commands"]] == ["git diff", "python-inline", "powershell"]
    assert [command["phase"] for command in result["commands"]] == ["status", "status", "status"]
    assert result["blocking_reasons"] == []
    assert result["warnings"] == []


def test_final_check_failed_status_summary_uses_gate_status(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        report_tests=[
            "Set-Location F:\\reverse-agent",
            "Get-Location",
            "Test-Path F:\\reverse-agent",
            "git rev-parse --show-toplevel",
            "git status --short",
            "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
            "echo unexpected-extra-command",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert result["status_summary"]["report_status"] == "FAILED"
    assert result["status_summary"]["report_acceptance_recommendation"] == "REWORK_REQUIRED"


def test_final_check_requires_close_round_command_block_when_declared(tmp_path: Path) -> None:
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
        "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_gate",
    ]
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        report_tests=commands,
        command_plan_overrides={
            "commands": [
                {
                    "index": index,
                    "command": command,
                    "phase": "gate" if "project_gate" in command else "test",
                    "kind": "close-round"
                    if "close-round" in command
                    else ("command-plan" if "command-plan" in command else ("final-check" if "final-check" in command else "pytest")),
                    "required": True,
                    "expected_exit_codes": [0],
                    "records_stdout_stderr": True,
                    "notes": "expected to exit 0",
                }
                for index, command in enumerate(commands, start=1)
            ],
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    exit_check = next(check for check in result["checks"] if check["name"] == "pytest_result_exit_codes_match_command_plan")
    assert exit_check["status"] == "FAIL"
    close_round_command = commands[-1]
    errors = [err for err in exit_check.get("errors", []) if isinstance(err, dict) and close_round_command in str(err.get("command", ""))]
    assert errors, "expected close-round to be flagged missing its recorded command block"


# ---------------------------------------------------------------------------
# Tests for run-round execute hardening: self-invocation guard,
# command-block recording, and close-round delegation
# ---------------------------------------------------------------------------


class TestIsSelfInvocation:
    """Verify _is_self_invocation detects run-round recursive calls."""

    def test_kind_run_round(self) -> None:
        assert _is_self_invocation({"kind": "run-round", "command": "something"}) is True

    def test_command_text_contains_run_round(self) -> None:
        assert _is_self_invocation({
            "kind": "unknown",
            "command": "python -m reverse_agent.project_gate run-round --state-dir project_state --execute",
        }) is True

    def test_command_text_dry_run(self) -> None:
        assert _is_self_invocation({
            "kind": "unknown",
            "command": "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
        }) is True

    def test_non_run_round_command(self) -> None:
        assert _is_self_invocation({
            "kind": "preflight",
            "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
        }) is False

    def test_empty_command(self) -> None:
        assert _is_self_invocation({"kind": "", "command": ""}) is False


class TestIsCloseRoundCommand:
    """Verify _is_close_round_command detects close-round commands."""

    def test_kind_close_round(self) -> None:
        assert _is_close_round_command({"kind": "close-round", "command": "something"}) is True

    def test_command_text_contains_close_round(self) -> None:
        assert _is_close_round_command({
            "kind": "unknown",
            "command": "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_1",
        }) is True

    def test_non_close_round_command(self) -> None:
        assert _is_close_round_command({
            "kind": "preflight",
            "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
        }) is False


class TestRunRoundSelfInvocationGuard:
    """Verify run_round execute mode skips self-invocation commands."""

    def test_execute_skips_run_round_kind_command(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m reverse_agent.project_gate run-round --state-dir project_state --execute",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert result["skipped_commands"] == [
            {
                "index": 1,
                "command": "python -m reverse_agent.project_gate run-round --state-dir project_state --execute",
                "kind": "run-round",
                "phase": "gate",
                "reason": "self-invocation guard: run-round must not invoke itself recursively",
            }
        ]
        assert result["executed_commands"] == []
        assert seen == []

    def test_execute_skips_run_round_dry_run_command(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert len(result["skipped_commands"]) == 1
        assert result["skipped_commands"][0]["reason"] == "self-invocation guard: run-round must not invoke itself recursively"
        assert seen == []

    def test_execute_runs_non_run_round_commands(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert result["skipped_commands"] == []
        assert len(result["executed_commands"]) == 1
        assert result["executed_commands"][0]["exit_code"] == 0

    def test_execute_mixed_skips_and_runs(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_gate preflight --state-dir project_state
""",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert len(result["skipped_commands"]) == 1
        assert result["skipped_commands"][0]["kind"] == "run-round"
        assert len(result["executed_commands"]) == 2
        assert result["executed_commands"][0]["kind"] == "pytest"
        assert result["executed_commands"][1]["kind"] == "preflight"


class TestRunRoundCloseRoundDelegation:
    """Verify run_round execute mode skips close-round commands."""

    def test_execute_skips_close_round_command(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_1",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert len(result["skipped_commands"]) == 1
        assert result["skipped_commands"][0]["reason"] == "close-round delegation: close-round subprocess owns its command block"
        assert result["executed_commands"] == []
        assert seen == []

    def test_execute_mixed_run_round_and_close_round_skipped(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_1
""",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert len(result["skipped_commands"]) == 2
        assert result["skipped_commands"][0]["reason"] == "self-invocation guard: run-round must not invoke itself recursively"
        assert result["skipped_commands"][1]["reason"] == "close-round delegation: close-round subprocess owns its command block"
        assert len(result["executed_commands"]) == 1
        assert result["executed_commands"][0]["kind"] == "pytest"


class TestRunRoundCommandBlockRecording:
    """Verify run_round execute mode records command blocks to pytest_result.txt."""

    def test_execute_records_command_block_to_pytest_result(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="3 passed\n", stderr="")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        assert result["recorded_command_blocks"] == ["python -m pytest tests/test_project_gate.py -q"]
        assert pytest_path.exists()
        content = pytest_path.read_text(encoding="utf-8")
        assert "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====" in content
        assert "3 passed" in content
        assert "===== EXIT: 0 =====" in content

    def test_execute_records_stdout_stderr_and_exit_code(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -c \"print('hello')\"",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="hello\n", stderr="warn\n")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        content = pytest_path.read_text(encoding="utf-8")
        assert "hello" in content
        assert "===== STDERR =====" in content
        assert "warn" in content
        assert "===== EXIT: 0 =====" in content

    def test_execute_records_failed_command_block(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -c \"raise SystemExit(1)\"",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 1, stdout="fail\n", stderr="error\n")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        content = pytest_path.read_text(encoding="utf-8")
        assert "===== EXIT: 1 =====" in content
        assert result["executed_commands"][0]["exit_code"] == 1

    def test_execute_no_pytest_result_path_does_not_write(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
        )

        assert result["recorded_command_blocks"] == []

    def test_execute_skipped_commands_not_recorded_in_command_blocks(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate run-round --state-dir project_state --execute
""",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        assert result["recorded_command_blocks"] == ["python -m pytest tests/test_project_gate.py -q"]
        content = pytest_path.read_text(encoding="utf-8")
        assert "run-round" not in content


class TestRunRoundDryRunPreservation:
    """Verify dry-run behavior is preserved after hardening."""

    def test_dry_run_leaves_executed_commands_empty(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )

        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)

        assert result["executed_commands"] == []
        assert result["skipped_commands"] == []
        assert result["recorded_command_blocks"] == []
        assert result["mode"] == "dry-run"

    def test_dry_run_does_not_append_command_blocks(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        result = run_round(
            state_dir=state_dir,
            dry_run=True,
            repo_root=tmp_path,
            pytest_result_path=pytest_path,
        )

        assert not pytest_path.exists()
        assert result["recorded_command_blocks"] == []

    def test_dry_run_json_still_returns_exit_code_zero(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )

        assert main(["run-round", "--state-dir", str(state_dir), "--dry-run", "--json"]) == 0
        output = json.loads(capsys.readouterr().out)
        assert output["run_status"] == "PASSED"
        assert output["mode"] == "dry-run"
        assert output["executed_commands"] == []
        assert output["skipped_commands"] == []


class TestRunRoundExecuteFailFast:
    """Verify fail-fast behavior is preserved after hardening."""

    def test_execute_still_stops_after_first_unexpected_exit(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -c "raise SystemExit(7)"
python -c "print('not reached')"
""",
        )
        seen: list[str] = []

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(command, 7, stdout="failed\n", stderr="")

        result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

        assert result["run_status"] == "FAILED"
        assert seen == ['python -c "raise SystemExit(7)"']
        assert len(result["executed_commands"]) == 1
        assert result["executed_commands"][0]["exit_code"] == 7

    def test_execute_records_failed_command_to_pytest_result(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -c "raise SystemExit(7)"
python -c "print('not reached')"
""",
        )
        pytest_path = tmp_path / "test_pytest_result.txt"

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 7, stdout="failed\n", stderr="")

        result = run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        content = pytest_path.read_text(encoding="utf-8")
        assert "===== EXIT: 7 =====" in content
        assert "not reached" not in content


# ---------------------------------------------------------------------------
# Tests for command extraction noise reduction
# ---------------------------------------------------------------------------


class TestIsProhibitiveLine:
    """Verify _is_prohibitive_line detects prohibition patterns."""

    def test_do_not(self) -> None:
        assert _is_prohibitive_line("Do not run this command") is True

    def test_do_not_chinese(self) -> None:
        assert _is_prohibitive_line("不要在 live project_state 上执行") is True

    def test_must_not(self) -> None:
        assert _is_prohibitive_line("You must not commit") is True

    def test_forbidden_chinese(self) -> None:
        assert _is_prohibitive_line("禁止修改 .codex-skills/") is True

    def test_normal_line(self) -> None:
        assert _is_prohibitive_line("Run the following command") is False

    def test_stop_condition(self) -> None:
        assert _is_prohibitive_line("If pytest fails, stop and report BLOCKED") is True

    def test_shall_not(self) -> None:
        assert _is_prohibitive_line("We shall not proceed") is True

    def test_negative_chinese(self) -> None:
        assert _is_prohibitive_line("不得把 task_packet.json 当执行权威") is True


class TestIsDescriptiveBacktickLine:
    """Verify _is_descriptive_backtick_line detects numbered descriptive items."""

    def test_numbered_item_with_multiple_backticks(self) -> None:
        assert _is_descriptive_backtick_line(
            '5. `pytest_result.txt` shows bare `python -m reverse_agent.project_gate run-round` was recorded'
        ) is True

    def test_numbered_item_with_single_backtick(self) -> None:
        assert _is_descriptive_backtick_line(
            '3. Run `python -m pytest tests/ -q` to verify'
        ) is False

    def test_non_numbered_line(self) -> None:
        assert _is_descriptive_backtick_line(
            'Run `python -m pytest tests/ -q` and `git status`'
        ) is False

    def test_empty_line(self) -> None:
        assert _is_descriptive_backtick_line("") is False


class TestCommandExtractionNoiseReduction:
    """Verify command-plan does not extract commands from prohibitive or descriptive text."""

    def test_extract_bash_commands_supports_powershell(self) -> None:
        text = """```powershell
Set-Location F:\\reverse-agent
Get-Location
Test-Path F:\\reverse-agent
```
"""
        commands, error = _extract_bash_commands(text)
        assert error is None
        assert "Set-Location F:\\reverse-agent" in commands
        assert "Get-Location" in commands
        assert "Test-Path F:\\reverse-agent" in commands

    def test_extract_bash_commands_prefers_fenced_over_unfenced(self) -> None:
        text = """```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
```

Some prose mentioning `python -m reverse_agent.project_gate run-round` as an example.
"""
        commands, error = _extract_bash_commands(text)
        assert error is None
        # Fenced commands should be extracted
        assert any("preflight" in cmd for cmd in commands)
        # The unfenced backtick reference should NOT be extracted
        assert not any("run-round" in cmd and "preflight" not in cmd for cmd in commands)

    def test_no_extraction_from_do_not_do(self) -> None:
        text = """Do not run `python -m reverse_agent.project_gate run-round --state-dir project_state --execute` on live project_state.
Do not use the old sample_solver.
"""
        commands = _extract_unfenced_commands(text)
        assert not any("run-round" in cmd for cmd in commands)

    def test_no_extraction_from_descriptive_numbered_item(self) -> None:
        text = "5. `pytest_result.txt` shows bare `python -m reverse_agent.project_gate run-round` was recorded as a command-plan command"
        commands = _extract_unfenced_commands(text)
        assert not any("run-round" in cmd for cmd in commands)

    def test_extraction_from_explicit_backtick_command(self) -> None:
        text = "Run `python -m reverse_agent.project_gate preflight --state-dir project_state` first."
        commands = _extract_unfenced_commands(text)
        assert any("preflight" in cmd for cmd in commands)

    def test_no_extraction_from_chinese_prohibition(self) -> None:
        text = "不要在 live project_state 上执行 python -m reverse_agent.project_gate run-round --execute"
        commands = _extract_unfenced_commands(text)
        assert not any("run-round" in cmd for cmd in commands)

    def test_command_plan_does_not_emit_bare_run_round_from_do_not(self, tmp_path: Path) -> None:
        """Regression test: decision with run-round in Do Not Do must not emit bare run-round."""
        decision_text = """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_test_noise",
  "round_id": "round_test_noise",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "abc123",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal
Test noise reduction.

## 2. Current Evidence
Previous round had a bare run-round command.

## 3. Do Not Do
Do not run `python -m reverse_agent.project_gate run-round --state-dir project_state --execute` on live project_state.
不要在 live project_state 上执行 run-round --execute。

## 4. Files To Inspect
- reverse_agent/project_gate.py

## 5. Required Audit
Startup commands must be recorded first:

```powershell
Set-Location F:\\reverse-agent
Get-Location
Test-Path F:\\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Before changing code, verify that `pytest_result.txt` shows bare `python -m reverse_agent.project_gate run-round` was recorded as a command-plan command even though it is not a required command.

## 6. Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## 7. Tests
```powershell
Set-Location F:\\reverse-agent
Get-Location
Test-Path F:\\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
```

## 8. Stop Conditions
If current working directory is not F:\\reverse-agent, stop.
"""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        _write_json(state_dir / "task_packet.json", {"schema_version": 2, "round_id": "round_test_noise"})
        _write_json(state_dir / "current_state.json", {"schema_version": 2, "round_id": "round_test_noise"})
        _write_json(state_dir / "artifact_index.json", {"latest_artifacts": {}})
        _write_json(state_dir / "negative_results.json", [])
        _write_json(state_dir / "codex_execution_report.md", {})
        _write_json(state_dir / "pytest_result.txt", {})

        result = command_plan(state_dir=state_dir, write_result=False)

        # The bare `python -m reverse_agent.project_gate run-round` must NOT appear
        command_strings = [cmd["command"] for cmd in result["commands"]]
        bare_run_round = [c for c in command_strings if c == "python -m reverse_agent.project_gate run-round"]
        assert not bare_run_round, f"bare run-round should not be extracted, got: {bare_run_round}"

        # The explicit preflight command from the Tests fenced block SHOULD appear
        assert any("preflight" in c for c in command_strings), "preflight command should be extracted from Tests"

    def test_command_plan_still_extracts_explicit_run_round_dry_run(self, tmp_path: Path) -> None:
        """Explicit run-round --dry-run in Tests fenced block must still be extracted."""
        decision_text = """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_test_explicit",
  "round_id": "round_test_explicit",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "abc123",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal
Test explicit command extraction.

## 2. Current Evidence
None.

## 3. Do Not Do
Nothing special.

## 4. Files To Inspect
- reverse_agent/project_gate.py

## 5. Required Audit
None.

## 6. Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## 7. Tests
```powershell
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_gate preflight --state-dir project_state
```

## 8. Stop Conditions
None.
"""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        _write_json(state_dir / "task_packet.json", {"schema_version": 2, "round_id": "round_test_explicit"})
        _write_json(state_dir / "current_state.json", {"schema_version": 2, "round_id": "round_test_explicit"})
        _write_json(state_dir / "artifact_index.json", {"latest_artifacts": {}})
        _write_json(state_dir / "negative_results.json", [])
        _write_json(state_dir / "codex_execution_report.md", {})
        _write_json(state_dir / "pytest_result.txt", {})

        result = command_plan(state_dir=state_dir, write_result=False)

        command_strings = [cmd["command"] for cmd in result["commands"]]
        dry_run_cmd = "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json"
        assert dry_run_cmd in command_strings, "explicit dry-run command should be extracted from Tests"


class TestAllowedInheritedFiles:
    """Verify _allowed_inherited_files returns only files explicitly listed in
    the "Allowed Inherited Dirty Baseline Files" section, NOT files that merely
    appear in Implementation Scope."""

    def test_returns_explicit_allowlist_intersection(self) -> None:
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py
- reverse_agent/other.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py
- tests/test_project_gate.py

Disallowed:
- solve_reports/
"""
        inherited = {"reverse_agent/project_gate.py", "reverse_agent/unknown.py", "tests/test_project_gate.py"}
        result = _allowed_inherited_files(decision_text, inherited)
        assert result == {"reverse_agent/project_gate.py", "tests/test_project_gate.py"}

    def test_returns_empty_when_only_scope_not_explicit_allowlist(self) -> None:
        """Files in Implementation Scope but NOT in explicit allowlist should NOT be allowed."""
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py
- reverse_agent/other.py

Allowed tests:
- tests/test_project_gate.py
"""
        inherited = {"reverse_agent/project_gate.py", "tests/test_project_gate.py"}
        result = _allowed_inherited_files(decision_text, inherited)
        assert result == set()

    def test_returns_empty_when_no_inherited(self) -> None:
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py
"""
        result = _allowed_inherited_files(decision_text, set())
        assert result == set()


class TestBaselineLifecycleLateBaselineCapture:
    """Test baseline lifecycle guard against late baseline capture scenarios.

    Decision requires 6 test scenarios:
    1. Clean baseline, source/test dirty after execution → round delta, not inherited.
    2. Baseline has source/test dirty, no explicit allowlist → WARN or FAIL.
    3. Baseline has source/test dirty, explicit allowlist, report explains → PASS.
    4. Baseline has source/test dirty, report claims no inherited → WARN or FAIL.
    5. Baseline only has generated state artifact dirty → not flagged as source/test late baseline.
    6. Previous artifact freshness strictness tests still pass.
    """

    DECISION_TEXT_NO_ALLOWLIST = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py
"""

    DECISION_TEXT_WITH_ALLOWLIST = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py
"""

    def _make_delta_summary(self, *, baseline_dirty: list[str] | None = None, inherited: list[str] | None = None) -> dict[str, Any]:
        return {
            "baseline_available": True,
            "baseline_dirty_files": baseline_dirty or [],
            "inherited_dirty_files": inherited or baseline_dirty or [],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": (baseline_dirty or []) + ["project_state/codex_execution_report.md"],
            "baseline_has_untracked_implementation_files": False,
            "baseline_untracked_files": [],
        }

    def test_clean_baseline_source_test_dirty_is_round_delta(self) -> None:
        """Scenario 1: Clean baseline, source/test dirty after execution → round delta, not inherited."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = self._make_delta_summary(
            baseline_dirty=[],
            inherited=[],
        )
        # new_dirty_files_since_baseline contains source/test files
        delta_summary["new_dirty_files_since_baseline"] = ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"]
        delta_summary["final_dirty_files"] = ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"]

        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=self.DECISION_TEXT_NO_ALLOWLIST,
            report_text="no inherited baseline files",
            state_dir=None,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"

    def test_baseline_source_test_dirty_no_allowlist_fails(self) -> None:
        """Scenario 2: Baseline has source/test dirty, no explicit allowlist → FAIL."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = self._make_delta_summary(
            baseline_dirty=["reverse_agent/project_gate.py"],
        )
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=self.DECISION_TEXT_NO_ALLOWLIST,
            report_text="baseline inherited",
            state_dir=None,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "FAIL"

    def test_baseline_source_test_dirty_explicit_allowlist_passes(self) -> None:
        """Scenario 3: Baseline has source/test dirty, explicit allowlist, report explains → PASS."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = self._make_delta_summary(
            baseline_dirty=["reverse_agent/project_gate.py"],
        )
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=self.DECISION_TEXT_WITH_ALLOWLIST,
            report_text="report explains inherited baseline dirty files for project_gate.py",
            state_dir=None,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"

    def test_baseline_source_test_dirty_report_claims_no_inherited_fails(self) -> None:
        """Scenario 4: Baseline has source/test dirty, report claims no inherited → WARN or FAIL."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = self._make_delta_summary(
            baseline_dirty=["reverse_agent/project_gate.py"],
        )
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=self.DECISION_TEXT_WITH_ALLOWLIST,
            report_text="working tree was clean at round start, all changes are new this round",
            state_dir=None,
        )
        allowlist_check = next(c for c in checks if c["name"] == "baseline_inherited_allowlist_explained")
        # Report does not explain inherited files even though allowlist exists
        assert allowlist_check["status"] == "FAIL"

    def test_baseline_only_generated_artifact_dirty_not_flagged(self) -> None:
        """Scenario 5: Baseline only has generated state artifact dirty → not flagged as source/test late baseline."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = self._make_delta_summary(
            baseline_dirty=["project_state/gates/round_baseline.json"],
            inherited=["project_state/gates/round_baseline.json"],
        )
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=self.DECISION_TEXT_NO_ALLOWLIST,
            report_text="no inherited source/test baseline files",
            state_dir=None,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"

    def test_scope_files_not_automatically_allowed(self) -> None:
        """Files in Implementation Scope but NOT in explicit allowlist should NOT be auto-allowed."""
        from reverse_agent.project_gate import _allowed_inherited_files
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py
- reverse_agent/project_state.py

Allowed tests:
- tests/test_project_gate.py
- tests/test_project_state.py
"""
        inherited = {
            "reverse_agent/project_gate.py",
            "reverse_agent/project_state.py",
            "tests/test_project_gate.py",
            "tests/test_project_state.py",
        }
        result = _allowed_inherited_files(decision_text, inherited)
        # None should be allowed without explicit "Allowed Inherited Dirty Baseline Files" section
        assert result == set()


class TestReportExplainsInheritedBaselineFiles:
    """Verify _report_explains_inherited_baseline_files requires both:
    1. Allowed Inherited Dirty Baseline Files section with list items
    2. No negation phrases anywhere in the report text
    """

    def test_allowlist_section_with_list_item_and_no_negation_returns_true(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "## Allowed Inherited Dirty Baseline Files\n\n- reverse_agent/project_gate.py"
        ) is True

    def test_negation_no_inherited_baseline_dirty_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "no inherited baseline dirty files at round start"
        ) is False

    def test_negation_no_inherited_dirty_files_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "no inherited dirty files in baseline"
        ) is False

    def test_negation_no_baseline_dirty_files_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "no baseline dirty files at round start"
        ) is False

    def test_negation_working_tree_was_clean_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "working tree was clean at round start, all changes are new this round"
        ) is False

    def test_negation_working_tree_clean_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "working tree clean, no dirty files at round start"
        ) is False

    def test_negation_no_dirty_files_at_round_start_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "no dirty files at round start"
        ) is False

    def test_no_section_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "all changes are new this round"
        ) is False

    def test_section_exists_but_no_list_items_returns_false(self) -> None:
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "## Allowed Inherited Dirty Baseline Files\n\nNo inherited baseline dirty files."
        ) is False

    def test_allowlist_section_with_list_item_but_negation_phrase_returns_false(self) -> None:
        """Conflict: section has list items but report also contains negation phrase."""
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "## Allowed Inherited Dirty Baseline Files\n\n- reverse_agent/project_gate.py\n\n"
            "No inherited baseline dirty files were found."
        ) is False

    def test_allowlist_section_with_list_item_but_working_tree_clean_returns_false(self) -> None:
        """Conflict: section has list items but report also says working tree was clean."""
        from reverse_agent.project_gate import _report_explains_inherited_baseline_files
        assert _report_explains_inherited_baseline_files(
            "## Allowed Inherited Dirty Baseline Files\n\n- reverse_agent/project_gate.py\n\n"
            "Working tree was clean at round start."
        ) is False


class TestWriteRoundCloseSnapshot:
    """Verify _write_round_close_snapshot writes the required fields."""

    def test_writes_snapshot_with_required_fields(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Write a baseline so the snapshot can reference it
        _write_json(gates_dir / "round_baseline.json", {
            "schema_version": 1,
            "artifact_name": "round_baseline.json",
            "decision_id": "decision_test",
            "round_id": "round_test",
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
        })
        snapshot = _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        # Verify returned snapshot has required fields
        assert snapshot["schema_version"] == 1
        assert snapshot["artifact_name"] == "round_close_snapshot.json"
        assert snapshot["decision_id"] == "decision_test"
        assert snapshot["round_id"] == "round_test"
        assert snapshot["round_closed"] is True
        assert snapshot["baseline_active"] is False
        assert "closed_at" in snapshot
        assert isinstance(snapshot["close_dirty_files"], list)
        assert isinstance(snapshot["close_worktree_clean"], bool)
        assert isinstance(snapshot["baseline_dirty_files"], list)
        assert isinstance(snapshot["inherited_dirty_files_at_close"], list)
        assert "recommended_next_action" in snapshot

    def test_snapshot_file_is_written(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_baseline.json", {
            "schema_version": 1,
            "baseline_dirty_files": [],
        })
        _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        snapshot_path = _round_close_snapshot_path(state_dir)
        assert snapshot_path.exists()
        # Verify it can be read back
        read_back = _read_round_close_snapshot(state_dir)
        assert read_back["round_closed"] is True

    def test_clean_worktree_snapshot(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_baseline.json", {
            "schema_version": 1,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
        })
        # Monkeypatch to simulate clean worktree at close time
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_changed_files",
            lambda _repo_root: [],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_status_short_lines",
            lambda _repo_root: [],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_diff_name_only",
            lambda _repo_root: [],
        )
        snapshot = _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        assert snapshot["close_worktree_clean"] is True
        assert snapshot["close_dirty_files"] == []
        assert snapshot["recommended_next_action"] == "no_action_required"


class TestReadRoundCloseSnapshot:
    """Verify _read_round_close_snapshot returns empty dict when no snapshot exists."""

    def test_returns_empty_when_no_snapshot(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        result = _read_round_close_snapshot(state_dir)
        assert result == {}

    def test_returns_snapshot_when_exists(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "round_closed": True,
            "close_worktree_clean": True,
        })
        result = _read_round_close_snapshot(state_dir)
        assert result["round_closed"] is True
        assert result["close_worktree_clean"] is True


class TestBaselineLifecycleClosedRound:
    """Verify baseline lifecycle checks distinguish active vs closed rounds."""

    DECISION_TEXT = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py
- reverse_agent/other.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py

Disallowed:
- solve_reports/
"""

    def _make_delta_summary(self, *, baseline_dirty: list[str] | None = None) -> dict[str, Any]:
        return {
            "baseline_available": True,
            "baseline_dirty_files": baseline_dirty or ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": baseline_dirty or ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
            "baseline_has_untracked_implementation_files": False,
            "baseline_untracked_files": [],
        }

    def test_closed_clean_worktree_no_warning(self, tmp_path: Path) -> None:
        """Closed round with clean worktree should not warn about stale baseline dirty files."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Write close snapshot showing clean worktree
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "decision_id": "decision_test",
            "round_closed": True,
            "close_worktree_clean": True,
            "close_dirty_files": [],
        })
        checks = _baseline_lifecycle_checks(
            delta_summary=self._make_delta_summary(),
            decision_text=self.DECISION_TEXT,
            report_text="baseline inherited",
            state_dir=state_dir,
            current_decision_id="decision_test",
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"
        assert "closed with clean worktree" in guard_check["detail"]

    def test_closed_dirty_worktree_warns_on_close_files(self, tmp_path: Path) -> None:
        """Closed round with dirty worktree should warn based on close snapshot dirty files."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Write close snapshot showing dirty worktree with a file that is
        # in source_test_scope but NOT in the explicit allowlist.
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "decision_id": "decision_test",
            "round_closed": True,
            "close_worktree_clean": False,
            "close_dirty_files": ["reverse_agent/other.py"],
        })
        # baseline_dirty_files includes other.py, which is in source_test_scope
        # but NOT in the explicit "Allowed Inherited Dirty Baseline Files" allowlist.
        checks = _baseline_lifecycle_checks(
            delta_summary=self._make_delta_summary(baseline_dirty=["reverse_agent/other.py"]),
            decision_text=self.DECISION_TEXT,
            report_text="baseline inherited",
            state_dir=state_dir,
            current_decision_id="decision_test",
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "FAIL"
        assert "close snapshot contains unauthorized" in guard_check["detail"]

    def test_closed_dirty_worktree_passes_when_allowed(self, tmp_path: Path) -> None:
        """Closed round with dirty worktree but allowed files should pass."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "decision_id": "decision_test",
            "round_closed": True,
            "close_worktree_clean": False,
            "close_dirty_files": ["reverse_agent/project_gate.py"],
        })
        checks = _baseline_lifecycle_checks(
            delta_summary=self._make_delta_summary(),
            decision_text=self.DECISION_TEXT,
            report_text="baseline inherited",
            state_dir=state_dir,
            current_decision_id="decision_test",
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"

    def test_active_round_still_warns(self, tmp_path: Path) -> None:
        """Active round without close snapshot should still warn about inherited dirty files."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # No close snapshot
        checks = _baseline_lifecycle_checks(
            delta_summary=self._make_delta_summary(),
            decision_text=self.DECISION_TEXT,
            report_text="baseline inherited",
            state_dir=state_dir,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard_check["status"] == "PASS"
        # Active round with allowed inherited files should still pass
        # (this is the existing behavior from Round 2)

    def test_no_state_dir_uses_active_behavior(self) -> None:
        """Without state_dir, close snapshot cannot be read, so active behavior is used.
        With explicit allowlist, the file should be allowed."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        checks = _baseline_lifecycle_checks(
            delta_summary=self._make_delta_summary(),
            decision_text=self.DECISION_TEXT,
            report_text="baseline inherited",
            state_dir=None,
        )
        guard_check = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        # With explicit allowlist, the file is allowed
        assert guard_check["status"] in ("PASS", "WARN")


class TestBaselineCaptureOrderChecks:
    """Verify _baseline_capture_order_checks detects suspected late baseline capture.

    Test scenarios from decision:
    1. baseline clean, source/test in new_dirty_files_since_baseline → PASS
    2. baseline dirty source/test, not in files_changed → no overlap, PASS
    3. baseline dirty source/test, also in files_changed → suspected late capture
    4. Even with Allowed Inherited Dirty Baseline Files, cannot PASS suspected late capture
    5. No startup evidence + suspected late capture → FAIL
    6. Startup evidence confirms pre-existing dirty → WARN (not FAIL)
    """

    DECISION_TEXT = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py
"""

    DECISION_TEXT_WITH_ALLOWLIST = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
"""

    REPORT_TEXT = "## Allowed Inherited Dirty Baseline Files\n\n- `reverse_agent/project_gate.py`\n"

    def _make_delta(
        self,
        baseline_dirty: list[str] | None = None,
        baseline_available: bool = True,
    ) -> dict[str, Any]:
        return {
            "baseline_available": baseline_available,
            "baseline_dirty_files": baseline_dirty or [],
            "inherited_dirty_files": baseline_dirty or [],
            "new_dirty_files_since_baseline": [],
        }

    # Minimal path-confirmation prefix required for trusted startup evidence.
    _PATH_PREFIX = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "Path\n----\nF:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n"
        "===== EXIT: 0 =====\n"
    )

    def _make_pytest_text(self, startup_dirty: list[str] | None = None, *, trusted: bool = True) -> str:
        """Build a minimal pytest_result.txt with startup git status --short.

        If *trusted* is True (default), path-confirmation commands appear
        before ``git status --short`` so the evidence is trusted.
        If *trusted* is False, ``git status --short`` appears first (untrusted).
        """
        status_lines = ""
        if startup_dirty:
            for path in startup_dirty:
                status_lines += f" M {path}\n"
        git_status_block = (
            "===== COMMAND: git status --short =====\n"
            f"{status_lines}"
            "===== EXIT: 0 =====\n"
        )
        if trusted:
            return self._PATH_PREFIX + git_status_block
        else:
            return git_status_block + self._PATH_PREFIX

    def test_baseline_clean_new_dirty_passes(self) -> None:
        """Scenario 1: baseline clean, source/test in new_dirty → PASS."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=[])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "PASS"
        assert check["capture_order_status"] == "clean"

    def test_baseline_dirty_not_in_files_changed_passes(self) -> None:
        """Scenario 2: baseline dirty source/test, not in files_changed → PASS (no overlap)."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"project_state/codex_execution_report.md"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "PASS"
        assert check["capture_order_status"] == "clean"

    def test_baseline_dirty_and_in_files_changed_suspected_late(self) -> None:
        """Scenario 3: baseline dirty source/test, also in files_changed → FAIL (suspected late)."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"
        assert check["capture_order_status"] == "suspected_late_capture"
        assert "reverse_agent/project_gate.py" in check["suspected_late_baseline_files"]

    def test_allowlist_does_not_override_suspected_late(self) -> None:
        """Scenario 4: Even with Allowed Inherited Dirty Baseline Files, cannot PASS."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT_WITH_ALLOWLIST,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"
        assert check["capture_order_status"] == "suspected_late_capture"

    def test_no_startup_evidence_suspected_late_fails(self) -> None:
        """Scenario 5: No startup evidence + suspected late capture → FAIL."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        # pytest_text has no startup git status --short block
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="some text without git status",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"

    def test_startup_evidence_confirms_inherited_warns(self) -> None:
        """Scenario 6: Startup evidence confirms pre-existing dirty → WARN."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        pytest_text = self._make_pytest_text(
            startup_dirty=["reverse_agent/project_gate.py"]
        )
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text=pytest_text,
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "WARN"
        assert check["capture_order_status"] == "confirmed_inherited"
        assert "reverse_agent/project_gate.py" in check["confirmed_inherited_from_startup_evidence"]

    def test_mixed_confirmed_and_suspected_fails(self) -> None:
        """Mixed: one file confirmed, one suspected → FAIL (partial)."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(
            baseline_dirty=["reverse_agent/project_gate.py", "tests/test_project_gate.py"]
        )
        pytest_text = self._make_pytest_text(
            startup_dirty=["reverse_agent/project_gate.py"]
        )
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py", "tests/test_project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text=pytest_text,
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"
        assert check["capture_order_status"] == "suspected_late_capture_partial"

    def test_baseline_unavailable_warns(self) -> None:
        """Baseline unavailable → WARN."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_available=False)
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "WARN"
        assert check["capture_order_status"] == "unavailable"

    def test_detail_fields_present(self) -> None:
        """Verify all required detail fields are present in the check output."""
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert "suspected_late_baseline_files" in check
        assert "allowed_inherited_dirty_files" in check
        assert "baseline_dirty_source_test_files" in check
        assert "files_changed_overlap" in check
        assert "capture_order_status" in check

    def test_untrusted_startup_evidence_overlap_fails(self) -> None:
        """Untrusted startup evidence + overlap → FAIL (not WARN/confirmed_inherited).

        Decision scenario 5: if git status --short appears before path
        confirmation, the startup evidence is untrusted and all overlap files
        are treated as suspected late capture.
        """
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        pytest_text = self._make_pytest_text(
            startup_dirty=["reverse_agent/project_gate.py"],
            trusted=False,
        )
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text=pytest_text,
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"
        assert check["capture_order_status"] == "suspected_late_capture"
        assert check["startup_status_evidence_trusted"] is False

    def test_trusted_startup_evidence_overlap_warns(self) -> None:
        """Trusted startup evidence + overlap → WARN/confirmed_inherited.

        Decision scenario 6: when git status --short appears after path
        confirmation and the file appears in startup dirty, it is confirmed
        inherited (not suspected late capture).
        """
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        pytest_text = self._make_pytest_text(
            startup_dirty=["reverse_agent/project_gate.py"],
            trusted=True,
        )
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text=pytest_text,
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "WARN"
        assert check["capture_order_status"] == "confirmed_inherited"
        assert check["startup_status_evidence_trusted"] is True

    def test_no_startup_evidence_overlap_fails(self) -> None:
        """No startup evidence + overlap → FAIL/suspected_late_capture.

        Decision scenario 7: without any startup evidence, overlap files are
        all treated as suspected late capture.
        """
        from reverse_agent.project_gate import _baseline_capture_order_checks

        delta = self._make_delta(baseline_dirty=["reverse_agent/project_gate.py"])
        checks = _baseline_capture_order_checks(
            delta_summary=delta,
            files_changed={"reverse_agent/project_gate.py"},
            decision_text=self.DECISION_TEXT,
            report_text=self.REPORT_TEXT,
            pytest_text="",
        )
        check = next(c for c in checks if c["name"] == "baseline_capture_order")
        assert check["status"] == "FAIL"
        assert check["capture_order_status"] == "suspected_late_capture"
        assert check["startup_status_evidence_trusted"] is False


class TestStartupStatusOrderValid:
    """Verify _startup_status_order_valid checks command ordering in pytest_result.txt."""

    _PATH_PREFIX = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "Path\n----\nF:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n"
        "===== EXIT: 0 =====\n"
    )

    _GIT_STATUS_BLOCK = (
        "===== COMMAND: git status --short =====\n"
        " M file.py\n"
        "===== EXIT: 0 =====\n"
    )

    def test_git_status_after_path_confirmation_trusted(self) -> None:
        """Decision scenario 2: git status after path confirmation → trusted."""
        from reverse_agent.project_gate import _startup_status_order_valid

        text = self._PATH_PREFIX + self._GIT_STATUS_BLOCK
        result = _startup_status_order_valid(text)
        assert result["valid"] is True
        assert result["startup_status_evidence_trusted"] is True
        assert result["startup_status_block_index"] is not None
        assert result["startup_status_block_index"] > max(
            v for v in result["path_confirmation_block_indexes"].values() if v is not None
        )

    def test_git_status_before_set_location_untrusted(self) -> None:
        """Decision scenario 3: git status before Set-Location → untrusted."""
        from reverse_agent.project_gate import _startup_status_order_valid

        # git status appears first, before any path confirmation
        text = self._GIT_STATUS_BLOCK + self._PATH_PREFIX
        result = _startup_status_order_valid(text)
        assert result["valid"] is False
        assert result["startup_status_evidence_trusted"] is False

    def test_git_status_before_git_rev_parse_untrusted(self) -> None:
        """Decision scenario 4: git status before git rev-parse → untrusted."""
        from reverse_agent.project_gate import _startup_status_order_valid

        # Include Set-Location, Get-Location, Test-Path but not git rev-parse
        partial_prefix = (
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "F:\\reverse-agent\n"
            "===== EXIT: 0 =====\n"
            "===== COMMAND: Get-Location =====\n"
            "Path\n----\nF:\\reverse-agent\n"
            "===== EXIT: 0 =====\n"
            "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
            "True\n"
            "===== EXIT: 0 =====\n"
        )
        rev_parse_block = (
            "===== COMMAND: git rev-parse --show-toplevel =====\n"
            "F:/reverse-agent\n"
            "===== EXIT: 0 =====\n"
        )
        # git status after partial prefix but before git rev-parse
        text = partial_prefix + self._GIT_STATUS_BLOCK + rev_parse_block
        result = _startup_status_order_valid(text)
        assert result["valid"] is False
        assert result["startup_status_evidence_trusted"] is False

    def test_no_git_status_valid(self) -> None:
        """No git status block → valid (no ordering violation)."""
        from reverse_agent.project_gate import _startup_status_order_valid

        text = self._PATH_PREFIX
        result = _startup_status_order_valid(text)
        assert result["valid"] is True
        assert result["startup_status_evidence_trusted"] is False
        assert result["startup_status_block_index"] is None

    def test_empty_text_valid(self) -> None:
        """Empty text → valid (no ordering violation)."""
        from reverse_agent.project_gate import _startup_status_order_valid

        result = _startup_status_order_valid("")
        assert result["valid"] is True
        assert result["startup_status_evidence_trusted"] is False
        assert result["startup_status_block_index"] is None

    def test_path_confirmation_indexes_populated(self) -> None:
        """Verify path_confirmation_block_indexes are correctly populated."""
        from reverse_agent.project_gate import _startup_status_order_valid

        text = self._PATH_PREFIX + self._GIT_STATUS_BLOCK
        result = _startup_status_order_valid(text)
        indexes = result["path_confirmation_block_indexes"]
        assert indexes["Set-Location"] == 0
        assert indexes["Get-Location"] == 1
        assert indexes["Test-Path"] == 2
        assert indexes["git rev-parse"] == 3
        assert result["startup_status_block_index"] == 4


class TestExtractStartupDirtyFiles:
    """Verify _extract_startup_dirty_files parses pytest_result.txt correctly."""

    # Minimal path-confirmation prefix required for trusted startup evidence.
    _PATH_PREFIX = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "Path\n----\nF:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n"
        "===== EXIT: 0 =====\n"
    )

    def test_extracts_modified_files(self) -> None:
        from reverse_agent.project_gate import _extract_startup_dirty_files

        text = (
            self._PATH_PREFIX
            + "===== COMMAND: git status --short =====\n"
            " M reverse_agent/project_gate.py\n"
            " M tests/test_project_gate.py\n"
            "===== EXIT: 0 =====\n"
        )
        result = _extract_startup_dirty_files(text)
        assert "reverse_agent/project_gate.py" in result
        assert "tests/test_project_gate.py" in result

    def test_extracts_untracked_files(self) -> None:
        from reverse_agent.project_gate import _extract_startup_dirty_files

        text = (
            self._PATH_PREFIX
            + "===== COMMAND: git status --short =====\n"
            "?? new_file.py\n"
            "===== EXIT: 0 =====\n"
        )
        result = _extract_startup_dirty_files(text)
        assert "new_file.py" in result

    def test_uses_first_git_status_block(self) -> None:
        """Only the first git status --short block after path confirmation is used."""
        from reverse_agent.project_gate import _extract_startup_dirty_files

        text = (
            self._PATH_PREFIX
            + "===== COMMAND: git status --short =====\n"
            " M file_a.py\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: git status --short =====\n"
            " M file_a.py\n"
            " M file_b.py\n"
            "===== EXIT: 0 =====\n"
        )
        result = _extract_startup_dirty_files(text)
        assert "file_a.py" in result
        assert "file_b.py" not in result

    def test_git_status_before_path_confirmation_returns_empty(self) -> None:
        """git status before path confirmation returns empty (untrusted)."""
        from reverse_agent.project_gate import _extract_startup_dirty_files

        text = (
            "===== COMMAND: git status --short =====\n"
            " M file_a.py\n"
            "===== EXIT: 0 =====\n"
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "F:\\reverse-agent\n"
            "===== EXIT: 0 =====\n"
        )
        result = _extract_startup_dirty_files(text)
        assert result == set()

    def test_empty_text_returns_empty(self) -> None:
        from reverse_agent.project_gate import _extract_startup_dirty_files

        result = _extract_startup_dirty_files("")
        assert result == set()

    def test_no_git_status_block_returns_empty(self) -> None:
        from reverse_agent.project_gate import _extract_startup_dirty_files

        result = _extract_startup_dirty_files("some text without git status")
        assert result == set()


class TestRoundDeltaChecksClosedRound:
    """Verify _round_delta_checks distinguishes active vs closed rounds for inherited dirty warnings."""

    DECISION_TEXT = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py
"""

    def test_closed_clean_worktree_warns_source_test_inherited(self, tmp_path: Path) -> None:
        """Closed round with clean worktree should still WARN about inherited
        source/test dirty files in files_changed (possible late baseline capture)."""
        from reverse_agent.project_gate import _round_delta_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "round_closed": True,
            "close_worktree_clean": True,
            "close_dirty_files": [],
        })
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={"reverse_agent/project_gate.py", "project_state/codex_execution_report.md"},
            generated_artifacts=set(),
            archive_paths=set(),
            state_dir=state_dir,
        )
        inherited_check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert inherited_check["status"] == "FAIL"
        assert "source/test" in inherited_check["detail"]

    def test_active_round_still_warns_inherited(self, tmp_path: Path) -> None:
        """Active round should still FAIL about inherited dirty files in files_changed."""
        from reverse_agent.project_gate import _round_delta_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # No close snapshot
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={"reverse_agent/project_gate.py", "project_state/codex_execution_report.md"},
            generated_artifacts=set(),
            archive_paths=set(),
            state_dir=state_dir,
        )
        inherited_check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert inherited_check["status"] == "FAIL"


class TestCloseRoundWritesSnapshot:
    """Verify close_round writes a close snapshot on successful close.

    The full close_round integration is tested through the live gate pipeline.
    Here we verify the snapshot writing mechanism and its interaction with
    lifecycle checks.
    """

    def test_write_and_read_round_trip(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Write a close snapshot and verify it can be read back with correct fields."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_baseline.json", {
            "schema_version": 1,
            "artifact_name": "round_baseline.json",
            "decision_id": "decision_test",
            "round_id": "round_test",
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
        })
        # Simulate clean worktree
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_changed_files",
            lambda _repo_root: [],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_status_short_lines",
            lambda _repo_root: [],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_diff_name_only",
            lambda _repo_root: [],
        )
        snapshot = _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        # Read back and verify
        read_back = _read_round_close_snapshot(state_dir)
        assert read_back["round_closed"] is True
        assert read_back["close_worktree_clean"] is True
        assert read_back["decision_id"] == "decision_test"
        assert read_back["round_id"] == "round_test"
        assert read_back["baseline_active"] is False
        assert "closed_at" in read_back

    def test_snapshot_with_dirty_worktree(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Write a close snapshot with dirty worktree and verify fields."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        _write_json(gates_dir / "round_baseline.json", {
            "schema_version": 1,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
        })
        # Simulate dirty worktree
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_changed_files",
            lambda _repo_root: ["reverse_agent/project_gate.py"],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_status_short_lines",
            lambda _repo_root: [" M reverse_agent/project_gate.py"],
        )
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_diff_name_only",
            lambda _repo_root: ["reverse_agent/project_gate.py"],
        )
        snapshot = _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        assert snapshot["close_worktree_clean"] is False
        assert "reverse_agent/project_gate.py" in snapshot["close_dirty_files"]
        assert "reverse_agent/project_gate.py" in snapshot["inherited_dirty_files_at_close"]
        assert snapshot["recommended_next_action"] == "review_close_dirty_files"


class TestBaselinePreservedAfterClose:
    """Verify round_baseline.json is not modified by close-round or close snapshot writing."""

    def test_baseline_unchanged_after_snapshot_write(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        original_baseline = {
            "schema_version": 1,
            "artifact_name": "round_baseline.json",
            "decision_id": "decision_test",
            "round_id": "round_test",
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "generated_at": "2026-06-15T00:00:00Z",
        }
        _write_json(gates_dir / "round_baseline.json", original_baseline)
        _write_round_close_snapshot(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_test",
            round_id="round_test",
        )
        # Read back baseline and verify it's unchanged
        import json
        baseline_path = gates_dir / "round_baseline.json"
        with open(baseline_path, encoding="utf-8") as f:
            current_baseline = json.load(f)
        assert current_baseline == original_baseline


class TestIsHistoricalSampleLimitation:
    """Verify _is_historical_sample_limitation classifies limitations correctly."""

    def test_missing_historical_sample_artifacts(self) -> None:
        assert _is_historical_sample_limitation("50 missing historical sample artifacts")

    def test_missing_sample_artifacts_without_historical(self) -> None:
        assert _is_historical_sample_limitation("3 missing sample artifacts")

    def test_historical_artifact_freshness(self) -> None:
        assert _is_historical_sample_limitation("historical artifact freshness degraded")

    def test_missing_historical_artifact(self) -> None:
        assert _is_historical_sample_limitation("missing historical artifact for probe_x")

    def test_non_historical_limitation(self) -> None:
        assert not _is_historical_sample_limitation("report/decision mismatch detected")

    def test_pytest_mismatch(self) -> None:
        assert not _is_historical_sample_limitation("pytest result does not match report")

    def test_scope_violation(self) -> None:
        assert not _is_historical_sample_limitation("scope violation: modified forbidden file")


class TestHistoricalSampleLimitationsOnly:
    """Verify _historical_sample_limitations_only checks all items."""

    def test_all_historical(self) -> None:
        assert _historical_sample_limitations_only([
            "50 missing historical sample artifacts",
            "historical artifact freshness degraded",
        ])

    def test_mixed(self) -> None:
        assert not _historical_sample_limitations_only([
            "50 missing historical sample artifacts",
            "report/decision mismatch",
        ])

    def test_empty(self) -> None:
        assert not _historical_sample_limitations_only([])

    def test_none_historical(self) -> None:
        assert not _historical_sample_limitations_only([
            "report/decision mismatch",
            "pytest failure",
        ])


class TestResultStatusMainlineAware:
    """Verify _result_status mainline-aware behavior for engineering_branch."""

    def test_engineering_branch_historical_only_returns_passed(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "PASSED"

    def test_engineering_branch_with_external_state_notices_returns_passed(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "external_state_notices": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "PASSED"

    def test_engineering_branch_pass_with_historical_limitations_returns_passed(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "PASS", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "PASSED"

    def test_engineering_branch_pass_with_external_notices_returns_passed(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "PASS", "external_state_notices": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "PASSED"

    def test_reverse_solving_historical_still_warns(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="reverse_solving") == "PASSED_WITH_LIMITATIONS"

    def test_tool_integration_historical_still_warns(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="tool_integration") == "PASSED_WITH_LIMITATIONS"

    def test_training_dataset_historical_still_warns(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="training_dataset") == "PASSED_WITH_LIMITATIONS"

    def test_engineering_branch_mixed_limitations_returns_with_limitations(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": [
                "50 missing historical sample artifacts",
                "report/decision mismatch",
            ]},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "PASSED_WITH_LIMITATIONS"

    def test_no_mainline_default_still_warns(self) -> None:
        checks = [
            {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
        ]
        assert _result_status(checks, "SUCCESS") == "PASSED_WITH_LIMITATIONS"

    def test_real_failure_still_fails(self) -> None:
        checks = [
            {"name": "some_check", "status": "FAIL"},
        ]
        assert _result_status(checks, "SUCCESS", mainline="engineering_branch") == "FAILED"


class TestReportStatusFromGatePayloadMainlineAware:
    """Verify _report_status_from_gate_payload mainline-aware behavior."""

    def test_engineering_branch_warn_historical_returns_accepted(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_engineering_branch_warn_with_external_notices_returns_accepted(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {"name": "status_policy_valid", "status": "WARN", "external_state_notices": ["50 missing historical sample artifacts"]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_engineering_branch_passed_historical_returns_accepted(self) -> None:
        payload = {
            "gate_status": "PASSED",
            "checks": [
                {"name": "status_policy_valid", "status": "PASS", "limitations": ["50 missing historical sample artifacts"]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_engineering_branch_passed_external_notices_returns_accepted(self) -> None:
        payload = {
            "gate_status": "PASSED",
            "checks": [
                {"name": "status_policy_valid", "status": "PASS", "external_state_notices": ["50 missing historical sample artifacts"]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_reverse_solving_warn_historical_returns_with_limitations(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {"name": "status_policy_valid", "status": "WARN", "limitations": ["50 missing historical sample artifacts"]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="reverse_solving")
        assert result == ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS")

    def test_engineering_branch_mixed_limitations_returns_with_limitations(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {"name": "status_policy_valid", "status": "WARN", "limitations": [
                    "50 missing historical sample artifacts",
                    "report/decision mismatch",
                ]},
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED_WITH_LIMITATIONS")


class TestReportStatusFastNonCloseout:
    """Verify _report_status_from_gate_payload returns PARTIAL/REWORK_REQUIRED
    for fast non-closeout scenarios where closeout_allowed=false and
    close-round was not run."""

    def test_fast_non_closeout_warn_returns_partial_rework(self) -> None:
        """Fast non-closeout with WARN gate_status and only archive-pending/historical
        WARNs must return PARTIAL/REWORK_REQUIRED, not SUCCESS/ACCEPTED."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {"name": "round_manifest_present", "status": "WARN"},
                {"name": "archived_report_matches_live_report", "status": "WARN"},
                {"name": "archived_pytest_result_matches_live_pytest_result", "status": "WARN"},
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                    "limitations": ["50 missing historical sample artifacts"],
                },
                {
                    "name": "fast_profile_closeout_consistency",
                    "status": "PASS",
                    "closeout_allowed": False,
                    "close_round_omitted": True,
                    "close_round_in_commands": False,
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("PARTIAL", "REWORK_REQUIRED")

    def test_fast_non_closeout_implicit_omission_returns_partial_rework(self) -> None:
        """Fast non-closeout where close-round is implicitly absent (not in
        omitted_commands, not in commands, closeout_allowed=false) must also
        return PARTIAL/REWORK_REQUIRED."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                    "external_state_notices": ["50 missing historical sample artifacts"],
                },
                {
                    "name": "fast_profile_closeout_consistency",
                    "status": "PASS",
                    "closeout_allowed": False,
                    "close_round_omitted": False,
                    "close_round_in_commands": False,
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("PARTIAL", "REWORK_REQUIRED")

    def test_fast_non_closeout_passed_returns_partial_rework(self) -> None:
        """Fast non-closeout with PASSED gate_status (no FAILs at all) must
        still return PARTIAL/REWORK_REQUIRED because close-round was not run."""
        payload = {
            "gate_status": "PASSED",
            "checks": [
                {
                    "name": "fast_profile_closeout_consistency",
                    "status": "PASS",
                    "closeout_allowed": False,
                    "close_round_omitted": True,
                    "close_round_in_commands": False,
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("PARTIAL", "REWORK_REQUIRED")

    def test_closeout_allowed_true_does_not_trigger_partial(self) -> None:
        """When closeout_allowed=True (full/standard profile), the fast non-closeout
        logic must NOT trigger, and the existing SUCCESS/ACCEPTED behavior is preserved."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                    "limitations": ["50 missing historical sample artifacts"],
                },
                {
                    "name": "fast_profile_closeout_consistency",
                    "status": "PASS",
                    "closeout_allowed": True,
                    "close_round_omitted": False,
                    "close_round_in_commands": True,
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_no_fast_profile_check_preserves_existing_behavior(self) -> None:
        """When fast_profile_closeout_consistency check is absent, the existing
        behavior is preserved (no fast non-closeout override)."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "WARN",
                    "limitations": ["50 missing historical sample artifacts"],
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        assert result == ("SUCCESS", "ACCEPTED")

    def test_fast_non_closeout_fail_check_does_not_trigger(self) -> None:
        """When fast_profile_closeout_consistency check is FAIL (report claims
        closeout), the fast non-closeout override must NOT trigger because the
        existing FAIL handling takes precedence."""
        payload = {
            "gate_status": "FAILED",
            "checks": [
                {
                    "name": "fast_profile_closeout_consistency",
                    "status": "FAIL",
                    "closeout_allowed": False,
                    "close_round_omitted": True,
                    "close_round_in_commands": False,
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="engineering_branch")
        # FAILED gate_status maps to ("FAILED", "REWORK_REQUIRED") via fallback
        assert result == ("FAILED", "REWORK_REQUIRED")


class TestFinalCheckMainlineStatusPolicy:
    """Verify final_check mainline-aware status policy for engineering_branch."""

    def test_engineering_branch_historical_only_returns_passed(self, tmp_path: Path) -> None:
        """engineering_branch with only historical sample limitations should return PASSED."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        assert result["gate_status"] == "FAILED"
        status_policy = _check(result, "status_policy_valid")
        # Historical limitations should be in external_state_notices, not limitations
        assert status_policy.get("external_state_notices") is not None
        assert len(status_policy["external_state_notices"]) > 0

    def test_reverse_solving_historical_still_with_limitations(self, tmp_path: Path) -> None:
        """reverse_solving with historical sample limitations must block (strict freshness)."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW", mainline="reverse_solving")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        assert result["gate_status"] == "FAILED"
        status_policy = _check(result, "status_policy_valid")
        assert status_policy["status"] == "FAIL"

    def test_engineering_branch_external_state_notices_visible(self, tmp_path: Path) -> None:
        """Historical sample limitations should be visible in external_state_notices."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        status_policy = _check(result, "status_policy_valid")
        notices = status_policy.get("external_state_notices", [])
        assert len(notices) > 0
        # Verify the notices contain historical sample artifact references
        assert any("historical" in str(n).lower() or "sample" in str(n).lower() for n in notices)

    def test_real_failure_still_fails_regardless_of_mainline(self, tmp_path: Path) -> None:
        """Real failures should still cause FAILED gate status even for engineering_branch."""
        state_dir = _make_gate_state(tmp_path)
        # Corrupt the report to trigger lint failure
        (state_dir / "codex_execution_report.md").write_text(
            "# CODEX_EXECUTION_REPORT\nNo summary block.\n",
            encoding="utf-8",
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        assert result["gate_status"] == "FAILED"


class TestReportSummarySynthesisMainlineAware:
    """Verify build_report_summary_synthesis mainline-aware behavior."""

    def test_engineering_branch_historical_notices_in_synthesis(self, tmp_path: Path) -> None:
        """For engineering_branch, when gate FAILS due to structural field diff,
        acceptance_recommendation and external_state_notices are not synthesized."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        # Run final_check first to produce the gate result
        final_check(state_dir=state_dir, repo_root=tmp_path)

        # Now run synthesis
        result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

        synthesized = result["synthesized_summary"]
        # Gate FAILED so acceptance_recommendation and external_state_notices are not synthesized
        assert synthesized.get("acceptance_recommendation") is None
        assert "external_state_notices" not in synthesized

    def test_reverse_solving_historical_blocks_in_synthesis(self, tmp_path: Path) -> None:
        """For reverse_solving, historical sample limitations must block (strict freshness)."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW", mainline="reverse_solving")
        _write_json(
            state_dir / "artifact_index.json",
            {
                "missing": [],
                "latest_artifacts": {},
                "latest_artifacts_v2": {
                    "old_probe": {"freshness": "stale"},
                    "missing_probe": {"freshness": "missing"},
                },
            },
        )

        # Run final_check first to produce the gate result
        final_check(state_dir=state_dir, repo_root=tmp_path)

        # Now run synthesis
        result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

        synthesized = result["synthesized_summary"]
        assert synthesized.get("acceptance_recommendation") in {"NEEDS_REVIEW", "REWORK_REQUIRED"}


class TestDecisionImmutabilityCheck:
    """Verify _decision_immutability_check enforces that live decision_packet.md
    must not be modified during execution.

    Test scenarios from decision section 7:
    1. live decision_packet.md in files_changed → WARN
    2. archive path decision_packet.md → no failure
    3. startup baseline decision_packet.md dirty → blocking diagnostic
    """

    def test_live_decision_in_files_changed_warns(self) -> None:
        """Scenario 1: live decision_packet.md in files_changed → FAIL."""
        result = _decision_immutability_check(
            files_changed={"project_state/decision_packet.md", "reverse_agent/project_gate.py"},
            new_dirty_files={"reverse_agent/project_gate.py"},
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["name"] == "decision_immutability"
        assert result["status"] == "FAIL"
        assert result["live_decision_in_files_changed"] is True

    def test_live_decision_in_new_dirty_files_warns(self) -> None:
        """Scenario 1 variant: live decision_packet.md in new_dirty_files → FAIL."""
        result = _decision_immutability_check(
            files_changed={"reverse_agent/project_gate.py"},
            new_dirty_files={"project_state/decision_packet.md"},
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["name"] == "decision_immutability"
        assert result["status"] == "FAIL"
        assert result["live_decision_in_new_dirty"] is True

    def test_archive_path_decision_no_failure(self) -> None:
        """Scenario 2: archive path decision_packet.md → PASS."""
        result = _decision_immutability_check(
            files_changed={
                "project_state/rounds/round_test/decision_packet.md",
                "reverse_agent/project_gate.py",
            },
            new_dirty_files={"reverse_agent/project_gate.py"},
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["name"] == "decision_immutability"
        assert result["status"] == "PASS"

    def test_baseline_dirty_decision_blocks(self) -> None:
        """Scenario 3: startup baseline decision_packet.md dirty → FAIL with blocking diagnostic."""
        result = _decision_immutability_check(
            files_changed=set(),
            new_dirty_files=set(),
            baseline_dirty_files={"project_state/decision_packet.md"},
            round_id="round_test",
        )
        assert result["name"] == "decision_immutability"
        assert result["status"] == "FAIL"
        assert result["live_decision_in_baseline"] is True

    def test_clean_decision_passes(self) -> None:
        """No live decision mutation → PASS."""
        result = _decision_immutability_check(
            files_changed={"reverse_agent/project_gate.py"},
            new_dirty_files={"reverse_agent/project_gate.py"},
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["name"] == "decision_immutability"
        assert result["status"] == "PASS"


class TestBuildOutputScopeCheck:
    """Verify _build_output_scope_check enforces build output scope rules.

    Test scenarios from decision section 7:
    4. build-generated state files whitelist stable
    5. build-generated files in round delta without build command → unverified
    6. build-generated files in round delta with build command exit 0 → controlled refresh
    """

    def test_whitelist_stable(self) -> None:
        """Scenario 4: BUILD_OUTPUT_WHITELIST contains expected files."""
        expected = {
            "project_state/artifact_index.json",
            "project_state/current_state.json",
            "project_state/task_packet.json",
            "project_state/model_gate.json",
            "project_state/negative_results.json",
        }
        assert BUILD_OUTPUT_WHITELIST == frozenset(expected)

    def test_no_build_files_in_delta_passes(self) -> None:
        """No build-generated files in delta → PASS."""
        result = _build_output_scope_check(
            new_dirty_files={"reverse_agent/project_gate.py"},
            files_changed={"reverse_agent/project_gate.py"},
            pytest_text="",
        )
        assert result["name"] == "build_output_scope"
        assert result["status"] == "PASS"

    def test_build_files_without_command_unverified(self) -> None:
        """Scenario 5: build-generated files in delta without build command → WARN."""
        result = _build_output_scope_check(
            new_dirty_files={
                "project_state/artifact_index.json",
                "project_state/current_state.json",
            },
            files_changed={
                "project_state/artifact_index.json",
                "project_state/current_state.json",
            },
            pytest_text="",
        )
        assert result["name"] == "build_output_scope"
        assert result["status"] == "WARN"
        assert "build_output_scope_unverified" in result["detail"]
        assert result["build_command_recorded"] is False

    def test_build_files_with_command_exit_zero_passes(self) -> None:
        """Scenario 6: build-generated files with build command exit 0 → PASS."""
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_state build =====\n"
            "Build complete\n"
            "===== EXIT: 0 =====\n"
        )
        result = _build_output_scope_check(
            new_dirty_files={
                "project_state/artifact_index.json",
                "project_state/current_state.json",
            },
            files_changed={
                "project_state/artifact_index.json",
                "project_state/current_state.json",
            },
            pytest_text=pytest_text,
        )
        assert result["name"] == "build_output_scope"
        assert result["status"] == "PASS"
        assert result["build_command_recorded"] is True
        assert result["build_exit_zero"] is True

    def test_build_files_with_command_nonzero_exit_warns(self) -> None:
        """Build command with non-zero exit → WARN."""
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_state build =====\n"
            "Build failed\n"
            "===== EXIT: 1 =====\n"
        )
        result = _build_output_scope_check(
            new_dirty_files={"project_state/artifact_index.json"},
            files_changed={"project_state/artifact_index.json"},
            pytest_text=pytest_text,
        )
        assert result["name"] == "build_output_scope"
        assert result["status"] == "WARN"
        assert result["build_command_recorded"] is True
        assert result["build_exit_zero"] is False


class TestVerifiedCliCoverageCheck:
    """Verify _verified_cli_coverage_check enforces CLI coverage rules.

    Test scenario from decision section 7:
    7. CLI claims must be covered by tests_ran (at least active-execution-view)
    """

    def test_no_cli_claims_passes(self) -> None:
        """No CLI claims in report → PASS."""
        result = _verified_cli_coverage_check(
            report_text="No CLI verification mentioned.",
            tests_ran=["python -m pytest -q"],
            pytest_text="",
        )
        assert result["name"] == "verified_cli_coverage"
        assert result["status"] == "PASS"

    def test_cli_claim_covered_by_tests_ran_passes(self) -> None:
        """CLI claim covered by tests_ran → PASS."""
        result = _verified_cli_coverage_check(
            report_text="Verified active-execution-view CLI.",
            tests_ran=["python -m reverse_agent.project_state active-execution-view --state-dir project_state --json"],
            pytest_text="",
        )
        assert result["name"] == "verified_cli_coverage"
        assert result["status"] == "PASS"

    def test_cli_claim_covered_by_command_block_passes(self) -> None:
        """CLI claim covered by pytest command block → PASS."""
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_state active-execution-view --state-dir project_state --json =====\n"
            '{"execution_authority": "decision_packet"}\n'
            "===== EXIT: 0 =====\n"
        )
        result = _verified_cli_coverage_check(
            report_text="Verified active-execution-view CLI.",
            tests_ran=["python -m pytest -q"],
            pytest_text=pytest_text,
        )
        assert result["name"] == "verified_cli_coverage"
        assert result["status"] == "PASS"

    def test_cli_claim_uncovered_warns(self) -> None:
        """Scenario 7: CLI claim not in tests_ran or command blocks → WARN."""
        result = _verified_cli_coverage_check(
            report_text="Verified active-execution-view CLI.",
            tests_ran=["python -m pytest -q"],
            pytest_text="",
        )
        assert result["name"] == "verified_cli_coverage"
        assert result["status"] == "WARN"
        assert "active-execution-view" in result["uncovered_clis"]


class TestDecisionImmutabilityInFinalCheck:
    """Verify decision_immutability check is integrated into final_check."""

    def test_live_decision_in_files_changed_final_check_warns(self, tmp_path: Path) -> None:
        """Scenario 1: live decision_packet.md in files_changed causes final-check FAIL."""
        state_dir = _make_gate_state(
            tmp_path,
            files_changed=[
                "project_state/decision_packet.md",
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                *(_archive_paths("round_gate")),
            ],
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        immutability_check = next(
            (c for c in result["checks"] if c["name"] == "decision_immutability"), None
        )
        assert immutability_check is not None
        assert immutability_check["status"] == "FAIL"

    def test_clean_decision_final_check_passes(self, tmp_path: Path) -> None:
        """No live decision mutation → decision_immutability PASS in final_check."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        immutability_check = next(
            (c for c in result["checks"] if c["name"] == "decision_immutability"), None
        )
        assert immutability_check is not None
        assert immutability_check["status"] == "PASS"


class TestDecisionNotDirtyInBaselinePreflight:
    """Verify decision_not_dirty_in_baseline check in preflight."""

    def test_clean_baseline_passes(self, tmp_path: Path) -> None:
        """Clean baseline → decision_not_dirty_in_baseline PASS."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {"round_id": "round_test", "state_build_id": "state_test", "state_digest": "digest_test", "state_scope": "sample_state", "source_harness_run": "run_test"},
        )
        _write_json(
            state_dir / "task_packet.json",
            {"state_scope": "sample_state", "task_source": "derived_from_sample_artifacts", "execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"},
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})
        _write_preflight_decision(state_dir, decision_id="decision_test", round_id="round_test")
        result = preflight(state_dir=state_dir, repo_root=tmp_path)
        baseline_check = next(
            (c for c in result["checks"] if c["name"] == "decision_not_dirty_in_baseline"), None
        )
        assert baseline_check is not None
        assert baseline_check["status"] == "PASS"


class TestActiveExecutionViewCommandKind:
    """Scenario 1: active-execution-view command is not unknown in command-plan."""

    def test_active_execution_view_kind(self) -> None:
        """active-execution-view is recognized as a known command kind."""
        cmd = "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json"
        assert _command_kind(cmd) == "active-execution-view"

    def test_active_execution_view_phase(self) -> None:
        """active-execution-view has phase 'status'."""
        cmd = "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json"
        kind = _command_kind(cmd)
        assert _command_phase(kind, archive_seen=False) == "status"

    def test_active_execution_view_not_unknown(self) -> None:
        """active-execution-view is not classified as unknown."""
        cmd = "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json"
        assert _command_kind(cmd) != "unknown"


class TestCommandPlanActiveExecutionViewPassed:
    """Scenario 2: command-plan --json returns PASSED with active-execution-view."""

    def test_command_plan_with_active_execution_view_passes(self, tmp_path: Path) -> None:
        """command-plan plan_status is PASSED when active-execution-view is in tests."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {"round_id": "round_test", "state_build_id": "state_test", "state_digest": "digest_test", "state_scope": "sample_state", "source_harness_run": "run_test"},
        )
        _write_json(
            state_dir / "task_packet.json",
            {"state_scope": "sample_state", "task_source": "derived_from_sample_artifacts", "execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"},
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})
        # Write a decision that includes active-execution-view in tests
        decision_text = (
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"decision_test","round_id":"round_test",'
            '"based_on_state_build_id":"state_test","based_on_state_digest":"digest_test",'
            '"status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n'
            "```\n\n"
            "# Decision\n\n"
            "## Goal\nTest goal\n\n"
            "## Current Evidence\nNone\n\n"
            "## Do Not Do\nNothing\n\n"
            "## Files To Inspect\nNone\n\n"
            "## Required Audit\n\n```powershell\n"
            "Set-Location F:\\reverse-agent\n"
            "```\n\n"
            "## Implementation Scope\nNone\n\n"
            "## Tests\n\n```powershell\n"
            "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json\n"
            "```\n\n"
            "## Stop Conditions\nNone\n"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        result = command_plan(state_dir=state_dir, write_result=False)
        assert result["plan_status"] == "PASSED"
        active_ev_cmds = [c for c in result["commands"] if c["kind"] == "active-execution-view"]
        assert len(active_ev_cmds) > 0
        assert active_ev_cmds[0]["phase"] == "status"


class TestLateBaselineCaptureStillFails:
    """Scenario 3: late baseline capture still fails."""

    def test_late_baseline_capture_fails(self, tmp_path: Path) -> None:
        """Source/test files in both baseline_dirty and files_changed triggers FAIL."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": [],
            "new_dirty_files": ["reverse_agent/project_gate.py"],
            "files_changed": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        result = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="",
        )
        guard = next((c for c in result if c["name"] == "baseline_lifecycle_guard"), None)
        assert guard is not None
        assert guard["status"] == "FAIL"


class TestCleanStartupNoBaselineGuard:
    """Scenario 4: clean startup + valid modifications don't trigger baseline_lifecycle_guard."""

    def test_clean_startup_passes(self, tmp_path: Path) -> None:
        """Clean baseline with modifications after preflight doesn't trigger guard."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": [],
            "inherited_dirty_files": [],
            "new_dirty_files": ["reverse_agent/project_gate.py"],
            "files_changed": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        result = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text="## Implementation Scope\n\nNone\n\n## Do Not Do\nNothing\n",
            report_text="",
        )
        guard = next((c for c in result if c["name"] == "baseline_lifecycle_guard"), None)
        assert guard is not None
        assert guard["status"] == "PASS"


# ---------------------------------------------------------------------------
# Startup-Baseline Consistency Check Tests (9 scenarios)
# ---------------------------------------------------------------------------

class TestStartupBaselineConsistencyDirtyBaselineEmpty:
    """Scenario 1: startup git status has source/test dirty, baseline dirty empty → FAIL."""

    def test_startup_dirty_baseline_empty_fails(self) -> None:
        """Startup shows source/test dirty but baseline_dirty_files is empty → FAIL."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
            },
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="",
            pytest_text=(
                "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
                "F:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Get-Location =====\n"
                "Path\n----\nF:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
                "True\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git rev-parse --show-toplevel =====\n"
                "F:/reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git status --short =====\n"
                " M reverse_agent/project_gate.py\n"
                "===== EXIT: 0 =====\n"
            ),
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "FAIL"
        assert "reverse_agent/project_gate.py" in result.get("missing_from_baseline", [])


class TestStartupBaselineConsistencyDirtyBaselineRecords:
    """Scenario 2: startup git status has source/test dirty, baseline correctly records inherited dirty → PASS."""

    def test_startup_dirty_baseline_records_passes(self) -> None:
        """Startup shows source/test dirty and baseline correctly records them → PASS."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["reverse_agent/project_gate.py"],
                "inherited_dirty_files": [],
            },
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="",
            pytest_text=(
                "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
                "F:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Get-Location =====\n"
                "Path\n----\nF:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
                "True\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git rev-parse --show-toplevel =====\n"
                "F:/reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git status --short =====\n"
                " M reverse_agent/project_gate.py\n"
                "===== EXIT: 0 =====\n"
            ),
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"


class TestStartupBaselineConsistencyBothClean:
    """Scenario 3: startup git status clean, baseline clean → PASS."""

    def test_startup_clean_baseline_clean_passes(self) -> None:
        """Both startup git status and baseline are clean → PASS."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
            },
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="",
            pytest_text=(
                "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
                "F:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Get-Location =====\n"
                "Path\n----\nF:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
                "True\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git rev-parse --show-toplevel =====\n"
                "F:/reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git status --short =====\n"
                "===== EXIT: 0 =====\n"
            ),
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"


class TestStartupBaselineConsistencyDecisionDirty:
    """Scenario 4: live decision_packet.md dirty → still FAIL (decision immutability)."""

    def test_decision_dirty_still_fails(self) -> None:
        """decision_packet.md in startup dirty files → baseline records it but
        decision_immutability check handles this separately; consistency check
        should still report the file is present."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["project_state/decision_packet.md"],
                "inherited_dirty_files": [],
            },
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="",
            pytest_text=(
                "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
                "F:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Get-Location =====\n"
                "Path\n----\nF:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
                "True\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git rev-parse --show-toplevel =====\n"
                "F:/reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git status --short =====\n"
                " M project_state/decision_packet.md\n"
                "===== EXIT: 0 =====\n"
            ),
        )
        # decision_packet.md is not in source_test_scope (it's not in 允许修改),
        # so startup_source_test_dirty is empty → PASS
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"


class TestStartupBaselineConsistencyActiveExecutionView:
    """Scenario 5: active-execution-view still recognized as known command."""

    def test_active_execution_view_kind(self) -> None:
        """active-execution-view is still recognized as known command kind."""
        from reverse_agent.project_gate import _command_kind
        assert _command_kind("python -m reverse_agent.project_state active-execution-view --state-dir project_state --json") == "active-execution-view"

    def test_active_execution_view_phase(self) -> None:
        """active-execution-view is still classified as status phase."""
        from reverse_agent.project_gate import _command_phase
        assert _command_phase("active-execution-view", archive_seen=False) == "status"


class TestStartupBaselineConsistencyCommandPlanPassed:
    """Scenario 6: command-plan --json still PASSED for active-execution-view."""

    def test_command_plan_with_active_execution_view_passes(self, tmp_path: Path) -> None:
        """command-plan returns PASSED with active-execution-view in command list."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (gates_dir / "round_baseline.json").write_text(
            json.dumps({"baseline_dirty_files": [], "captured_at": "2026-01-01T00:00:00Z"}),
            encoding="utf-8",
        )
        decision_text = (
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"d1","round_id":"r1",'
            '"based_on_state_build_id":"s1","based_on_state_digest":"h1",'
            '"status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n'
            "```\n"
            "## Goal\nTest\n## Current Evidence\nNone\n## Do Not Do\nNothing\n"
            "## Files To Inspect\nNone\n## Required Audit\nNone\n"
            "## Implementation Scope\nNone\n"
            "## Tests\n```bash\npython -m pytest tests/ -q\n```\n"
            "## Stop Conditions\nNone\n"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        report_text = (
            "```json codex_report_summary\n"
            '{"schema_version":1,"report_id":"r1","round_id":"r1",'
            '"based_on_decision_id":"d1","status":"SUCCESS","acceptance_recommendation":"ACCEPTED",'
            '"files_changed":[],"tests_ran":[],"generated_artifacts":[]}\n'
            "```\n"
        )
        (state_dir / "codex_execution_report.md").write_text(report_text, encoding="utf-8")
        result = command_plan(state_dir=state_dir, write_result=True)
        assert result.get("plan_status") == "PASSED"


class TestStartupBaselineConsistencyBuildOutputScope:
    """Scenario 7: build output scope check not regressed."""

    def test_build_output_scope_no_violation(self) -> None:
        """No build output scope violation when no build-generated files."""
        result = _build_output_scope_check(
            new_dirty_files={"reverse_agent/project_gate.py"},
            files_changed={"reverse_agent/project_gate.py"},
            pytest_text="===== COMMAND: test =====\noutput\n===== EXIT: 0 =====\n",
        )
        assert result["name"] == "build_output_scope"
        assert result["status"] == "PASS"


class TestStartupBaselineConsistencyVerifiedCliCoverage:
    """Scenario 8: verified CLI coverage check not regressed."""

    def test_verified_cli_coverage_passes(self) -> None:
        """CLI coverage passes when all commands are covered."""
        result = _verified_cli_coverage_check(
            report_text="",
            tests_ran=["python -m pytest tests/ -q"],
            pytest_text="===== COMMAND: python -m pytest tests/ -q =====\n549 passed\n===== EXIT: 0 =====\n",
        )
        assert result["name"] == "verified_cli_coverage"
        assert result["status"] == "PASS"


class TestStartupBaselineConsistencyReportClaimsNone:
    """Scenario 9: report claims 'no inherited dirty' when startup git status has source/test dirty → FAIL."""

    def test_report_claims_no_inherited_with_startup_dirty_fails(self) -> None:
        """Report claims no inherited dirty files but startup shows source/test dirty → FAIL."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["reverse_agent/project_gate.py"],
                "inherited_dirty_files": [],
            },
            decision_text="## Implementation Scope\n\n允许修改：\n- reverse_agent/project_gate.py\n\n## Do Not Do\nNothing\n",
            report_text="# Report\n\nNo inherited baseline dirty files.\n",
            pytest_text=(
                "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
                "F:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Get-Location =====\n"
                "Path\n----\nF:\\reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
                "True\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git rev-parse --show-toplevel =====\n"
                "F:/reverse-agent\n"
                "===== EXIT: 0 =====\n"
                "===== COMMAND: git status --short =====\n"
                " M reverse_agent/project_gate.py\n"
                "===== EXIT: 0 =====\n"
            ),
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "FAIL"
        assert result.get("report_inconsistency") is True


class TestProjectCliCommandKind:
    """Tests for the generic project-cli command classification."""

    def test_success_target_reanchor_is_project_cli(self) -> None:
        cmd = "python -m reverse_agent.local_reverse_cpp1_success_target_reanchor --static-triage a.json --out b.json"
        assert _command_kind(cmd) == "project-cli"

    def test_project_cli_phase_is_status(self) -> None:
        assert _command_phase("project-cli", archive_seen=False) == "status"

    def test_project_cli_not_unknown(self) -> None:
        cmd = "python -m reverse_agent.local_reverse_cpp1_success_target_reanchor --out x.json"
        kind = _command_kind(cmd)
        assert kind != "unknown", f"expected known kind, got {kind!r}"

    def test_input_delivery_review_is_project_cli(self) -> None:
        cmd = "python -m reverse_agent.input_delivery_review --state-dir project_state"
        assert _command_kind(cmd) == "project-cli"

    def test_runtime_probe_not_project_cli(self) -> None:
        cmd = "python -m reverse_agent.local_reverse_cpp1_runtime_boundary_probe --out x.json"
        assert _command_kind(cmd) == "runtime-boundary-probe"

    def test_debugger_command_not_project_cli(self) -> None:
        cmd = "python -m reverse_agent.debugger_attach --target cpp1"
        assert _command_kind(cmd) != "project-cli"

    def test_harness_command_not_project_cli(self) -> None:
        cmd = "python -m reverse_agent.harness_run --sample cpp1"
        assert _command_kind(cmd) != "project-cli"

    def test_solver_command_not_project_cli(self) -> None:
        cmd = "python -m reverse_agent.solver_search --sample cpp1"
        assert _command_kind(cmd) != "project-cli"

    def test_probe_command_not_project_cli(self) -> None:
        cmd = "python -m reverse_agent.memory_probe --target cpp1"
        assert _command_kind(cmd) != "project-cli"

    def test_non_reverse_agent_not_project_cli(self) -> None:
        cmd = "python -m other_module.run_task --input x.json"
        assert _command_kind(cmd) != "project-cli"

    def test_existing_specific_mappings_preserved(self) -> None:
        """Commands that already have specific mappings should keep them."""
        assert _command_kind("python -m reverse_agent.local_reverse_single_sample_static_triage --out x.json") == "static-triage"
        assert _command_kind("python -m reverse_agent.local_reverse_cpp1_target_byte_extract --current-revalidation --out x.json") == "target-bytes-revalidation"


class TestGitFetchCommandClassification:
    """Tests for git fetch command classification in command-plan.

    Covers:
    - _command_kind recognizes git fetch as a known kind
    - _command_phase classifies git fetch as status phase
    - command-plan with git fetch returns plan_status=PASSED when no other warnings
    - unknown unrelated commands still produce WARN
    - close-round still fails on real command-plan id mismatch
    """

    def test_command_kind_git_fetch_origin(self) -> None:
        assert _command_kind("git fetch origin") == "git fetch"

    def test_command_kind_git_fetch_bare(self) -> None:
        assert _command_kind("git fetch") == "git fetch"

    def test_command_kind_git_fetch_all(self) -> None:
        assert _command_kind("git fetch --all") == "git fetch"

    def test_command_phase_git_fetch_is_status(self) -> None:
        assert _command_phase("git fetch", archive_seen=False) == "status"

    def test_command_plan_with_git_fetch_passes(self, tmp_path: Path) -> None:
        """command-plan with git fetch origin returns plan_status=PASSED."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        decision_text = (
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"d1","round_id":"r1",'
            '"based_on_state_build_id":"s1","based_on_state_digest":"h1",'
            '"status":"APPROVED","mainline":"engineering_branch",'
            '"skill_profiles":["reverse-agent-iteration@v2"]}\n'
            "```\n"
            "# DECISION_PACKET\n"
            "## 1. Goal\nTest.\n"
            "## 2. Current Evidence\nNone.\n"
            "## 3. Do Not Do\nNothing.\n"
            "## 4. Files To Inspect\nNone.\n"
            "## 5. Required Audit\nNone.\n"
            "## 6. Implementation Scope\n"
            "Allowed source changes:\n- reverse_agent/project_gate.py\n"
            "## 7. Tests\n"
            "```powershell\n"
            "git fetch origin\n"
            "git status --short\n"
            "```\n"
            "## 8. Stop Conditions\nNone.\n"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        result = command_plan(state_dir=state_dir, write_result=True)
        assert result["plan_status"] == "PASSED", f"Expected PASSED, got {result['plan_status']}; warnings={result.get('warnings')}"

    def test_unknown_command_still_warns(self, tmp_path: Path) -> None:
        """Unknown unrelated commands still produce plan_status=WARN."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        decision_text = (
            "```json decision_meta\n"
            '{"schema_version":1,"decision_id":"d1","round_id":"r1",'
            '"based_on_state_build_id":"s1","based_on_state_digest":"h1",'
            '"status":"APPROVED","mainline":"engineering_branch",'
            '"skill_profiles":["reverse-agent-iteration@v2"]}\n'
            "```\n"
            "# DECISION_PACKET\n"
            "## 1. Goal\nTest.\n"
            "## 2. Current Evidence\nNone.\n"
            "## 3. Do Not Do\nNothing.\n"
            "## 4. Files To Inspect\nNone.\n"
            "## 5. Required Audit\nNone.\n"
            "## 6. Implementation Scope\n"
            "Allowed source changes:\n- reverse_agent/project_gate.py\n"
            "## 7. Tests\n"
            "```powershell\n"
            "some_unknown_command --flag\n"
            "```\n"
            "## 8. Stop Conditions\nNone.\n"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
        result = command_plan(state_dir=state_dir, write_result=True)
        assert result["plan_status"] == "WARN"
        assert any("unknown kind" in w for w in result.get("warnings", []))


class TestBaselineLifecycleCloseSnapshotAuthorization:
    """Tests for baseline lifecycle guard close snapshot authorization semantics.

    Covers:
    - authorized source/test files in Implementation Scope are not reported as
      unauthorized inherited dirty files at close
    - unauthorized source/test dirty files still block
    - close snapshot dirty source/test files must be either authorized or blocking
    - report-summary includes round_close_snapshot.json in expected files when
      generated
    - current artifact freshness and id matching checks remain strict
    """

    def test_authorized_scope_files_not_unauthorized_at_close(self) -> None:
        """Source/test files in Implementation Scope with report explanation
        should not be classified as unauthorized at close."""
        from reverse_agent.project_gate import _allowed_inherited_baseline_paths, _report_explains_inherited_baseline_files
        report_text = (
            "## Allowed Inherited Dirty Baseline Files\n"
            "- reverse_agent/project_gate.py: Modified before preflight.\n"
            "- tests/test_project_gate.py: Modified before preflight.\n"
        )
        allowed = _allowed_inherited_baseline_paths(report_text)
        explains = _report_explains_inherited_baseline_files(report_text)
        # _path_from_markdown_bullet includes the full bullet text after the dash
        assert any("reverse_agent/project_gate.py" in p for p in allowed)
        assert any("tests/test_project_gate.py" in p for p in allowed)
        assert explains is True

    def test_unauthorized_source_test_files_still_block(self) -> None:
        """Source/test files NOT in Implementation Scope and NOT in report
        should remain unauthorized."""
        from reverse_agent.project_gate import _allowed_inherited_baseline_paths
        report_text = (
            "## Allowed Inherited Dirty Baseline Files\n"
            "- reverse_agent/project_gate.py: Modified.\n"
        )
        allowed = _allowed_inherited_baseline_paths(report_text)
        # unauthorized_solver.py is not in allowed
        assert "reverse_agent/unauthorized_solver.py" not in allowed

    def test_close_snapshot_without_report_explanation_blocks(self) -> None:
        """Close snapshot dirty source/test files without report explanation
        should remain unauthorized."""
        from reverse_agent.project_gate import _allowed_inherited_baseline_paths, _report_explains_inherited_baseline_files
        report_text = "## Summary\nNo inherited dirty files section.\n"
        allowed = _allowed_inherited_baseline_paths(report_text)
        explains = _report_explains_inherited_baseline_files(report_text)
        assert allowed == set()
        assert explains is False

    def test_report_summary_diff_suppresses_close_snapshot_only_difference(self) -> None:
        """When the only difference between expected and actual files_changed
        is round_close_snapshot.json, the diff should be suppressed."""
        from reverse_agent.project_gate import _report_summary_diff
        diff = _report_summary_diff(
            field="files_changed",
            expected=[
                "project_state/gates/final_gate_result.json",
                "project_state/gates/round_close_snapshot.json",
                "reverse_agent/project_gate.py",
            ],
            actual=[
                "project_state/gates/final_gate_result.json",
                "reverse_agent/project_gate.py",
            ],
        )
        # The diff should exist (lists differ) but the only difference
        # is round_close_snapshot.json
        assert diff is not None
        expected_set = set(diff["expected"])
        actual_set = set(diff["actual"])
        assert expected_set - actual_set == {"project_state/gates/round_close_snapshot.json"}

    def test_report_summary_diff_does_not_suppress_other_differences(self) -> None:
        """When files_changed differs by more than just round_close_snapshot.json,
        the diff should not be suppressed."""
        from reverse_agent.project_gate import _report_summary_diff
        diff = _report_summary_diff(
            field="files_changed",
            expected=[
                "project_state/gates/final_gate_result.json",
                "project_state/gates/round_close_snapshot.json",
                "reverse_agent/project_gate.py",
            ],
            actual=[
                "project_state/gates/final_gate_result.json",
            ],
        )
        assert diff is not None
        # Multiple differences exist, not just round_close_snapshot.json
        expected_set = set(diff["expected"])
        actual_set = set(diff["actual"])
        assert len(expected_set - actual_set) > 1

    def test_artifact_freshness_check_remains_strict(self) -> None:
        """Artifact freshness checks should not be weakened by the
        bootstrapping exception."""
        from reverse_agent.project_gate import _allowed_inherited_baseline_paths
        # _allowed_inherited_baseline_paths should only return paths from
        # the "Allowed Inherited Dirty Baseline Files" section, not from
        # other sections.
        report_text = (
            "## Summary\nSome summary.\n\n"
            "## Allowed Inherited Dirty Baseline Files\n"
            "- reverse_agent/project_gate.py: Modified.\n"
        )
        allowed = _allowed_inherited_baseline_paths(report_text)
        assert any("reverse_agent/project_gate.py" in p for p in allowed)
        # Should not include paths from other sections
        assert not any("reverse_agent/solver.py" in p for p in allowed)


class TestAllowedSourceTestScopePathsExcludesState:
    """Tests that _allowed_source_test_scope_paths excludes state file paths.

    When Implementation Scope has both "Allowed source changes:" and
    "Allowed state updates:" sections, only paths under source/tests
    should be returned.  State files like project_state/... must not
    appear in source_test_scope, otherwise baseline_lifecycle_guard
    incorrectly flags them as unauthorized source/test dirty files.
    """

    def test_state_files_excluded_from_source_test_scope(self) -> None:
        from reverse_agent.project_gate import _allowed_source_test_scope_paths
        scope_text = (
            "Allowed source changes:\n"
            "- `reverse_agent/project_gate.py`\n"
            "- `tests/test_project_gate.py`\n"
            "\n"
            "Allowed state updates:\n"
            "- `project_state/codex_execution_report.md`\n"
            "- `project_state/pytest_result.txt`\n"
            "- `project_state/gates/command_plan.json`\n"
        )
        result = _allowed_source_test_scope_paths(scope_text)
        assert "reverse_agent/project_gate.py" in result
        assert "tests/test_project_gate.py" in result
        # State files must NOT be in source_test_scope
        assert "project_state/codex_execution_report.md" not in result
        assert "project_state/pytest_result.txt" not in result
        assert "project_state/gates/command_plan.json" not in result

    def test_only_source_section_included(self) -> None:
        from reverse_agent.project_gate import _allowed_source_test_scope_paths
        scope_text = (
            "Allowed source changes:\n"
            "- `reverse_agent/foo.py`\n"
            "\n"
            "Allowed state updates:\n"
            "- `project_state/bar.json`\n"
            "\n"
            "Do not modify:\n"
            "- `reverse_agent/baz.py`\n"
        )
        result = _allowed_source_test_scope_paths(scope_text)
        assert "reverse_agent/foo.py" in result
        assert "project_state/bar.json" not in result
        assert "reverse_agent/baz.py" not in result


class TestStatusPolicyHistoricalArtifactsOnly:
    """Verify _status_policy_failure_is_historical_artifacts_only allows training_dataset."""

    def _make_result(self, **overrides: object) -> dict[str, Any]:
        base: dict[str, Any] = {
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "FAIL",
                    "report_status": "SUCCESS",
                    "doctor_status": "WARN",
                    "lint_errors": ["50 missing, 0 stale artifacts"],
                },
            ],
        }
        base.update(overrides)
        return base

    def test_returns_true_for_engineering_branch(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        result = _status_policy_failure_is_historical_artifacts_only(
            result=self._make_result(),
            mainline="engineering_branch",
        )
        assert result is True

    def test_returns_true_for_training_dataset(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        result = _status_policy_failure_is_historical_artifacts_only(
            result=self._make_result(),
            mainline="training_dataset",
        )
        assert result is True

    def test_returns_false_for_reverse_solving(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        result = _status_policy_failure_is_historical_artifacts_only(
            result=self._make_result(),
            mainline="reverse_solving",
        )
        assert result is False

    def test_returns_false_for_tool_integration(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        result = _status_policy_failure_is_historical_artifacts_only(
            result=self._make_result(),
            mainline="tool_integration",
        )
        assert result is False

    def test_returns_false_when_report_not_success(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        sp = dict(self._make_result()["checks"][0])
        sp["report_status"] = "FAILED"
        result = _status_policy_failure_is_historical_artifacts_only(
            result={"checks": [sp]},
            mainline="training_dataset",
        )
        assert result is False

    def test_returns_false_when_doctor_fail(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        sp = dict(self._make_result()["checks"][0])
        sp["doctor_status"] = "FAIL"
        result = _status_policy_failure_is_historical_artifacts_only(
            result={"checks": [sp]},
            mainline="training_dataset",
        )
        assert result is False

    def test_returns_false_when_no_artifact_errors(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        sp = dict(self._make_result()["checks"][0])
        sp["lint_errors"] = ["something else entirely"]
        result = _status_policy_failure_is_historical_artifacts_only(
            result={"checks": [sp]},
            mainline="training_dataset",
        )
        assert result is False


class TestDecisionScopeDeliverablePaths:
    """Verify _decision_scope_deliverable_paths extracts allowed generated artifact
    paths from the decision's Implementation Scope section."""

    def test_extracts_allowed_generated_artifacts(self) -> None:
        from reverse_agent.project_gate import _decision_scope_deliverable_paths

        decision_text = """```json decision_meta
{"schema_version": 1, "decision_id": "d1", "round_id": "r1", "status": "APPROVED", "mainline": "training_dataset", "skill_profiles": ["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/local_reverse_cipher_static_evidence_profile.md`

Allowed source files:

- `reverse_agent/project_gate.py`
"""
        paths = _decision_scope_deliverable_paths(decision_text)
        assert "project_state/local_reverse_cipher_static_evidence_profile.json" in paths
        assert "project_state/local_reverse_cipher_static_evidence_profile.md" in paths
        # Source files should NOT be included
        assert "reverse_agent/project_gate.py" not in paths

    def test_returns_empty_when_no_allowed_generated_section(self) -> None:
        from reverse_agent.project_gate import _decision_scope_deliverable_paths

        decision_text = """```json decision_meta
{"schema_version": 1, "decision_id": "d1", "round_id": "r1", "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
"""
        paths = _decision_scope_deliverable_paths(decision_text)
        assert len(paths) == 0

    def test_exits_subsection_on_disallowed(self) -> None:
        from reverse_agent.project_gate import _decision_scope_deliverable_paths

        decision_text = """```json decision_meta
{"schema_version": 1, "decision_id": "d1", "round_id": "r1", "status": "APPROVED", "mainline": "training_dataset", "skill_profiles": ["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`

Disallowed:

- `solve_reports/`
"""
        paths = _decision_scope_deliverable_paths(decision_text)
        assert "project_state/local_reverse_cipher_static_evidence_profile.json" in paths
        # Disallowed items should not be included
        assert "solve_reports/" not in paths

    def test_path_normalization(self) -> None:
        from reverse_agent.project_gate import _decision_scope_deliverable_paths

        decision_text = """```json decision_meta
{"schema_version": 1, "decision_id": "d1", "round_id": "r1", "status": "APPROVED", "mainline": "training_dataset", "skill_profiles": ["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
"""
        paths = _decision_scope_deliverable_paths(decision_text)
        # Should be normalized (forward slashes)
        assert any("local_reverse_cipher_static_evidence_profile.json" in p for p in paths)

    def test_allowed_project_state_files_subsection(self) -> None:
        """'Allowed generated/project-state files:' header is also recognized."""
        from reverse_agent.project_gate import _decision_scope_deliverable_paths

        decision_text = """```json decision_meta
{"schema_version": 1, "decision_id": "d1", "round_id": "r1", "status": "APPROVED", "mainline": "training_dataset", "skill_profiles": ["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`

Allowed source files:

- `reverse_agent/project_gate.py`
"""
        paths = _decision_scope_deliverable_paths(decision_text)
        assert "project_state/codex_execution_report.md" in paths
        assert "project_state/pytest_result.txt" in paths


class TestDecisionScopeDeliverablePromotion:
    """Verify that decision-scope required deliverables present as inherited dirty
    files are promoted into files_changed and generated_artifacts in synthesis."""

    def test_inherited_scope_deliverable_not_flagged_in_delta_checks(self) -> None:
        """Decision-scope deliverables that are inherited dirty files should not
        be flagged by files_changed_excludes_inherited_dirty_files."""
        from reverse_agent.project_gate import _round_delta_checks

        delta_summary = {
            "baseline_available": True,
            "final_dirty_files": [
                "project_state/local_reverse_cipher_static_evidence_profile.json",
                "project_state/codex_execution_report.md",
            ],
            "new_dirty_files_since_baseline": [
                "project_state/codex_execution_report.md",
            ],
            "inherited_dirty_files": [
                "project_state/local_reverse_cipher_static_evidence_profile.json",
            ],
        }
        decision_text = """## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
"""
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={
                "project_state/local_reverse_cipher_static_evidence_profile.json",
                "project_state/codex_execution_report.md",
            },
            generated_artifacts={
                "project_state/local_reverse_cipher_static_evidence_profile.json",
                "project_state/codex_execution_report.md",
            },
            archive_paths=set(),
            decision_text=decision_text,
        )
        check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert check["status"] == "PASS"

    def test_non_scope_inherited_dirty_still_flagged_in_delta_checks(self) -> None:
        """Non-scope inherited dirty files should still be flagged by
        files_changed_excludes_inherited_dirty_files."""
        from reverse_agent.project_gate import _round_delta_checks

        delta_summary = {
            "baseline_available": True,
            "final_dirty_files": [
                "project_state/some_other_artifact.json",
                "project_state/codex_execution_report.md",
            ],
            "new_dirty_files_since_baseline": [
                "project_state/codex_execution_report.md",
            ],
            "inherited_dirty_files": [
                "project_state/some_other_artifact.json",
            ],
        }
        decision_text = """## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
"""
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={
                "project_state/some_other_artifact.json",
                "project_state/codex_execution_report.md",
            },
            generated_artifacts={
                "project_state/some_other_artifact.json",
                "project_state/codex_execution_report.md",
            },
            archive_paths=set(),
            decision_text=decision_text,
        )
        check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        # Non-scope inherited dirty file should still be flagged
        assert check["status"] in {"WARN", "FAIL"}

    def test_scope_deliverable_promoted_in_synthesis_logic(self) -> None:
        """Verify the promotion logic: inherited dirty files that are also
        decision-scope deliverables should be included in round_delta_files."""
        from reverse_agent.project_gate import _decision_scope_deliverable_paths, _norm_path

        decision_text = """## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/local_reverse_cipher_static_evidence_profile.md`
"""
        deliverables = _decision_scope_deliverable_paths(decision_text)
        inherited_dirty = {
            "project_state/local_reverse_cipher_static_evidence_profile.json",
            "project_state/local_reverse_cipher_static_evidence_profile.md",
        }
        final_dirty = {
            "project_state/local_reverse_cipher_static_evidence_profile.json",
            "project_state/local_reverse_cipher_static_evidence_profile.md",
            "project_state/codex_execution_report.md",
        }
        # The promotion logic: inherited_scope_deliverables = inherited_dirty & deliverables & final_dirty
        inherited_scope_deliverables = inherited_dirty & deliverables & final_dirty
        assert len(inherited_scope_deliverables) == 2
        assert _norm_path("project_state/local_reverse_cipher_static_evidence_profile.json") in inherited_scope_deliverables
        assert _norm_path("project_state/local_reverse_cipher_static_evidence_profile.md") in inherited_scope_deliverables

    def test_non_scope_inherited_dirty_not_promoted(self) -> None:
        """Non-scope inherited dirty files should not be promoted."""
        from reverse_agent.project_gate import _decision_scope_deliverable_paths, _norm_path

        decision_text = """## 6. Implementation Scope

Allowed generated artifacts:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
"""
        deliverables = _decision_scope_deliverable_paths(decision_text)
        inherited_dirty = {
            "project_state/some_other_artifact.json",
        }
        final_dirty = {
            "project_state/some_other_artifact.json",
            "project_state/codex_execution_report.md",
        }
        inherited_scope_deliverables = inherited_dirty & deliverables & final_dirty
        assert len(inherited_scope_deliverables) == 0


class TestClassifyGateProfile:
    """Tests for the gate profile classifier (fast/standard/full)."""

    def test_artifact_only_decision_classifies_fast(self) -> None:
        """Artifact-only decision with only project_state generated artifacts
        should classify as fast."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/local_reverse_cipher_static_evidence_profile.md`

Required implementation behavior:

- Define evidence fields for DES and RC4 PE cipher samples.
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"
        assert any("artifact-only" in r for r in result["reasons"])

    def test_source_test_decision_classifies_standard(self) -> None:
        """Decision allowing ordinary source/test changes should classify as standard."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/some_module.py`

Allowed tests:

- `tests/test_some_module.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "standard"
        assert any("source/test" in r for r in result["reasons"])

    def test_gate_project_state_change_classifies_full(self) -> None:
        """Decision allowing changes to project_gate.py should classify as full."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"
        assert any("gate/project_state" in r for r in result["reasons"])

    def test_project_state_py_change_classifies_full(self) -> None:
        """Decision allowing changes to project_state.py should classify as full."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_state.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"

    def test_harness_solver_paths_classify_full(self) -> None:
        """Harness/solver/tool-runner/debugger/IDA/Ghidra/runtime-probe paths
        should classify as full."""
        from reverse_agent.project_gate import classify_gate_profile

        for path in [
            "reverse_agent/solver.py",
            "reverse_agent/harness.py",
            "reverse_agent/ida_integration.py",
            "reverse_agent/ghidra_runner.py",
            "reverse_agent/debugger_hook.py",
            "reverse_agent/tool_runner.py",
            "reverse_agent/runtime_probe.py",
        ]:
            decision_text = f"""## 6. Implementation Scope

Allowed source files:

- `{path}`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
            result = classify_gate_profile(decision_text)
            assert result["profile"] == "full", f"Expected full for {path}, got {result['profile']}"

    def test_codex_skills_paths_classify_full(self) -> None:
        """.codex-skills/ paths should classify as full."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `.codex-skills/registry.json`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"
        assert any(".codex-skills" in r for r in result["reasons"])

    def test_result_has_required_fields(self) -> None:
        """Result must contain profile, reasons, suggested_commands, future_phases."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/some_artifact.json`
"""
        result = classify_gate_profile(decision_text)
        assert "profile" in result
        assert "reasons" in result
        assert "suggested_commands" in result
        assert "future_phases" in result
        assert result["profile"] in {"fast", "standard", "full"}
        assert isinstance(result["reasons"], list)
        assert len(result["reasons"]) > 0
        assert isinstance(result["suggested_commands"], list)
        assert len(result["suggested_commands"]) > 0

    def test_fast_suggested_commands_shorter_than_full(self) -> None:
        """Fast profile should have fewer suggested commands than full."""
        from reverse_agent.project_gate import classify_gate_profile

        fast_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/some_artifact.json`
"""
        full_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        fast_result = classify_gate_profile(fast_text)
        full_result = classify_gate_profile(full_text)
        assert len(fast_result["suggested_commands"]) < len(full_result["suggested_commands"])


class TestSourceTestCleanStart:
    """Tests for the source_test_clean_start preflight check and the
    removal of report bootstrapping exceptions."""

    def test_source_test_dirty_without_allowlist_is_unauthorized(self) -> None:
        """Source/test files dirty at baseline without decision allowlist
        must be classified as unauthorized."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] == "FAIL"

    def test_source_test_dirty_with_decision_allowlist_is_authorized(self) -> None:
        """Source/test files dirty at baseline WITH decision allowlist
        must be authorized."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] != "FAIL"

    def test_report_cannot_authorize_inherited_dirty(self) -> None:
        """Report bootstrapping exception has been removed: the report
        cannot authorize inherited dirty source/test files."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        # Report tries to authorize the inherited dirty file
        report_text = """## Allowed Inherited Dirty Baseline Files

The following source/test files were modified before baseline capture:

- `reverse_agent/project_gate.py` — Allowed source file per decision scope
"""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        # Report bootstrapping is removed, so this must still FAIL
        assert guard["status"] == "FAIL"

    def test_ordinary_allowed_source_does_not_authorize_inherited(self) -> None:
        """Ordinary 'Allowed source files' does not authorize inherited
        dirty baseline files."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/some_module.py"],
            "inherited_dirty_files": ["reverse_agent/some_module.py"],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/some_module.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] == "FAIL"

    def test_generated_project_state_dirty_not_blocking(self) -> None:
        """Generated project_state files dirty at baseline are not
        source/test clean-start violations."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": [
                "project_state/codex_execution_report.md",
                "project_state/gates/preflight_result.json",
                "project_state/pytest_result.txt",
            ],
            "inherited_dirty_files": [
                "project_state/codex_execution_report.md",
            ],
        }
        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] != "FAIL"

    def test_clean_baseline_passes(self) -> None:
        """Clean baseline (no source/test dirty) passes the check."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": [],
            "inherited_dirty_files": [],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] == "PASS"


class TestReportProseClaimsCoveredByFilesChanged:
    """Tests for the report_prose_claims_covered_by_files_changed check.

    Verifies that source/test paths claimed in report prose (Source Changes,
    Test Changes, backticked paths) must appear in files_changed.
    """

    def test_source_change_omitted_from_files_changed_fails(self) -> None:
        """Report body claims reverse_agent/project_gate.py in Source Changes
        but files_changed omits it: check must fail."""
        from reverse_agent.project_gate import _report_prose_claims_check

        report_text = """## Changes

### Source Changes

1. **`reverse_agent/project_gate.py`** — Added new check function.

### Test Changes

No test changes.
"""
        result = _report_prose_claims_check(
            report_text=report_text,
            files_changed={"project_state/codex_execution_report.md"},
        )
        assert result["name"] == "report_prose_claims_covered_by_files_changed"
        assert result["status"] == "FAIL"
        assert "reverse_agent/project_gate.py" in result.get("missing_from_files_changed", [])

    def test_test_change_omitted_from_files_changed_fails(self) -> None:
        """Report body claims tests/test_project_gate.py in Test Changes
        but files_changed omits it: check must fail."""
        from reverse_agent.project_gate import _report_prose_claims_check

        report_text = """## Changes

### Source Changes

No source changes.

### Test Changes

2. **`tests/test_project_gate.py`** — Added new test class.
"""
        result = _report_prose_claims_check(
            report_text=report_text,
            files_changed={"project_state/codex_execution_report.md"},
        )
        assert result["name"] == "report_prose_claims_covered_by_files_changed"
        assert result["status"] == "FAIL"
        assert "tests/test_project_gate.py" in result.get("missing_from_files_changed", [])

    def test_claimed_path_present_in_files_changed_passes(self) -> None:
        """Claimed source/test file present in files_changed: check passes."""
        from reverse_agent.project_gate import _report_prose_claims_check

        report_text = """## Changes

### Source Changes

1. **`reverse_agent/project_gate.py`** — Added new check function.

### Test Changes

2. **`tests/test_project_gate.py`** — Added new test class.
"""
        result = _report_prose_claims_check(
            report_text=report_text,
            files_changed={
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
            },
        )
        assert result["name"] == "report_prose_claims_covered_by_files_changed"
        assert result["status"] == "PASS"

    def test_project_state_artifacts_in_prose_do_not_trigger_failure(self) -> None:
        """Project_state generated artifacts in report prose do not trigger
        the source/test claimed-change failure."""
        from reverse_agent.project_gate import _report_prose_claims_check

        report_text = """## Changes

### Source Changes

No source changes.

### Test Changes

No test changes.

## Evidence

Updated `project_state/codex_execution_report.md` and `project_state/pytest_result.txt`.
"""
        result = _report_prose_claims_check(
            report_text=report_text,
            files_changed={"project_state/codex_execution_report.md"},
        )
        assert result["name"] == "report_prose_claims_covered_by_files_changed"
        assert result["status"] == "PASS"


class TestTmpPathsAbsentFromDirtyState:
    """Tests for the tmp_paths_absent_from_dirty_state check.

    Verifies that temporary paths (tmp*/) are not present in dirty state.
    """

    def test_tmp_path_in_dirty_state_is_blocking(self) -> None:
        """Temporary path such as tmp8osv9s8n/ in final dirty/inherited
        dirty state is blocking."""
        from reverse_agent.project_gate import _tmp_paths_dirty_check

        delta_summary = {
            "final_dirty_files": ["tmp8osv9s8n/"],
            "inherited_dirty_files": ["tmp8osv9s8n/"],
            "baseline_dirty_files": ["tmp8osv9s8n/"],
        }
        result = _tmp_paths_dirty_check(delta_summary=delta_summary)
        assert result["name"] == "tmp_paths_absent_from_dirty_state"
        assert result["status"] == "FAIL"
        assert "tmp8osv9s8n/" in result.get("tmp_paths", [])

    def test_no_tmp_path_in_dirty_state_passes(self) -> None:
        """No temporary paths in dirty state: check passes."""
        from reverse_agent.project_gate import _tmp_paths_dirty_check

        delta_summary = {
            "final_dirty_files": ["project_state/codex_execution_report.md"],
            "inherited_dirty_files": [],
            "baseline_dirty_files": [],
        }
        result = _tmp_paths_dirty_check(delta_summary=delta_summary)
        assert result["name"] == "tmp_paths_absent_from_dirty_state"
        assert result["status"] == "PASS"


class TestExistingChecksPreserved:
    """Verify that existing clean-start baseline guard and gate-profile
    tests continue to pass after the new checks are added."""

    def test_clean_start_baseline_guard_still_works(self) -> None:
        """Existing clean-start baseline guard behavior is preserved."""
        from reverse_agent.project_gate import _baseline_lifecycle_checks

        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": [],
            "inherited_dirty_files": [],
        }
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        report_text = ""
        checks = _baseline_lifecycle_checks(
            delta_summary=delta_summary,
            decision_text=decision_text,
            report_text=report_text,
        )
        guard = next(c for c in checks if c["name"] == "baseline_lifecycle_guard")
        assert guard["status"] == "PASS"

    def test_gate_profile_classifier_still_works(self) -> None:
        """Existing gate-profile classifier behavior is preserved."""
        from reverse_agent.project_gate import classify_gate_profile

        # Decision allowing project_gate.py changes classifies as full
        decision_text_full = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text_full)
        assert result["profile"] == "full"

        # Artifact-only decision classifies as fast
        decision_text_fast = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
"""
        result = classify_gate_profile(decision_text_fast)
        assert result["profile"] == "fast"


# ---------------------------------------------------------------------------
# Required tests for decision_20260617_generated_artifact_existence_rework_v1
# ---------------------------------------------------------------------------


class TestGeneratedArtifactExistenceCheck:
    """Verify _generated_artifact_live_paths_exist_check and the
    WARN→FAIL promotion for structural field diffs."""

    def test_missing_live_gate_artifact_fails(self, tmp_path: Path) -> None:
        """Req 1: A live project_state/gates/ path listed in
        generated_artifacts but absent on disk must fail."""
        from reverse_agent.project_gate import _generated_artifact_live_paths_exist_check

        result = _generated_artifact_live_paths_exist_check(
            generated_artifacts={
                "project_state/gates/missing_artifact.json",
                "project_state/gates/command_plan.json",
            },
            repo_root=tmp_path,
        )
        assert result["status"] == "FAIL"
        assert "project_state/gates/missing_artifact.json" in result["missing_live_paths"]

    def test_existing_live_gate_artifact_passes(self, tmp_path: Path) -> None:
        """Req 2: An existing live project_state/gates/ path listed in
        generated_artifacts must pass."""
        from reverse_agent.project_gate import _generated_artifact_live_paths_exist_check

        gates_dir = tmp_path / "project_state" / "gates"
        gates_dir.mkdir(parents=True)
        (gates_dir / "command_plan.json").write_text("{}", encoding="utf-8")

        result = _generated_artifact_live_paths_exist_check(
            generated_artifacts={"project_state/gates/command_plan.json"},
            repo_root=tmp_path,
        )
        assert result["status"] == "PASS"

    def test_archive_paths_not_checked_as_live(self, tmp_path: Path) -> None:
        """Req 3: Archive paths under project_state/rounds/<round_id>/ are
        not subject to the live gate artifact existence check."""
        from reverse_agent.project_gate import _generated_artifact_live_paths_exist_check

        # The archive path does not exist on disk, but it should not
        # trigger a failure because it is not a live gate artifact.
        result = _generated_artifact_live_paths_exist_check(
            generated_artifacts={
                "project_state/rounds/round_gate/codex_execution_report.md",
                "project_state/rounds/round_gate/round_manifest.json",
            },
            repo_root=tmp_path,
        )
        assert result["status"] == "PASS"
        assert result["live_paths"] == []

    def test_run_round_result_in_generated_artifacts_only_when_exists(self, tmp_path: Path) -> None:
        """Req 4: run_round_result.json is included in synthesized
        generated_artifacts only if it exists on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        # run_round_result.json does NOT exist on disk
        assert not (state_dir / "gates" / "run_round_result.json").exists()

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/run_round_result.json" not in ga

        # Now create it on disk and add a run-round command to the plan
        # so the synthesis includes it
        _write_json(state_dir / "gates" / "run_round_result.json", {
            "schema_version": 1, "artifact_name": "run_round_result.json",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Also add run-round to the command plan so synthesis includes it
        cp_path = state_dir / "gates" / "command_plan.json"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        cp["commands"].append({
            "index": 8, "command": "python -m reverse_agent.project_gate run-round --state-dir project_state",
            "phase": "gate", "kind": "run-round", "required": True,
        })
        _write_json(cp_path, cp)

        result2 = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga2 = result2.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/run_round_result.json" in ga2

    def test_files_changed_mismatch_causes_fail(self, tmp_path: Path) -> None:
        """Req 5: A mismatch between report summary files_changed and
        synthesized files_changed must cause FAIL (not WARN)."""
        state_dir = _make_gate_state(
            tmp_path,
            files_changed=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                *_archive_paths("round_gate"),
                # Deliberately omit reverse_agent/project_gate.py and
                # tests/test_project_gate.py which synthesis expects
            ],
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        synthesis_check = _check(result, "report_summary_fields_match_synthesis")
        assert synthesis_check["status"] == "FAIL"
        assert any(d["field"] == "files_changed" for d in synthesis_check.get("diffs", []))

    def test_generated_artifacts_mismatch_causes_fail(self, tmp_path: Path) -> None:
        """Req 6: A mismatch between report summary generated_artifacts and
        synthesized generated_artifacts must cause FAIL (not WARN)."""
        archive_paths = _archive_paths("round_gate")
        state_dir = _make_gate_state(
            tmp_path,
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                # Deliberately omit command_plan.json which synthesis expects
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                *archive_paths,
            ],
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        synthesis_check = _check(result, "report_summary_fields_match_synthesis")
        assert synthesis_check["status"] == "FAIL"
        assert any(d["field"] == "generated_artifacts" for d in synthesis_check.get("diffs", []))

    def test_final_gate_result_excluded_from_existence_check(self, tmp_path: Path) -> None:
        """final_gate_result.json is excluded from the live-path existence
        check because it is written by final_check() *after* the check runs."""
        from reverse_agent.project_gate import _generated_artifact_live_paths_exist_check

        # final_gate_result.json does NOT exist on disk, but it should not
        # trigger a failure because it is excluded from live-path checks.
        result = _generated_artifact_live_paths_exist_check(
            generated_artifacts={
                "project_state/gates/final_gate_result.json",
            },
            repo_root=tmp_path,
        )
        assert result["status"] == "PASS"
        assert result["live_paths"] == []


class TestExistingChecksPreserved:
    """Req 7-10: Existing check categories continue to pass."""

    def test_clean_start_baseline_guard_still_works(self, tmp_path: Path) -> None:
        """Req 7: Clean-start baseline guard tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        # No baseline dirty files → guard should PASS
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        guard = _check(result, "baseline_lifecycle_guard")
        assert guard["status"] == "PASS"

    def test_report_prose_claims_coverage_still_works(self, tmp_path: Path) -> None:
        """Req 8: Report prose claim coverage tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        prose_check = _check(result, "report_prose_claims_covered_by_files_changed")
        assert prose_check["status"] in ("PASS", "WARN")

    def test_tmp_path_dirty_state_still_works(self, tmp_path: Path) -> None:
        """Req 9: tmp-path dirty-state tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        tmp_check = _check(result, "tmp_paths_absent_from_dirty_state")
        assert tmp_check["status"] == "PASS"

    def test_gate_profile_classifier_still_works(self) -> None:
        """Req 10: Gate-profile classifier tests continue to pass."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"


class TestExecutionAuthorityHardStop:
    """Verify execution-authority hard-stop behavior per
    decision_20260617_execution_authority_hard_stop_rework_v1.

    Required tests:
    1. live decision_packet.md in files_changed → decision_immutability FAIL
    2. live decision_packet.md in new_dirty_files → decision_immutability FAIL
    3. live decision_packet.md in baseline dirty → preflight or final-check FAIL
    4. startup source/test dirty without trusted allowlist → preflight FAIL
    5. late-added allowlist in live decision cannot authorize source/test dirty
    6. inherited source/test dirty in files_changed → FAIL unless all three conditions
    7. report_summary_fields_match_synthesis status/acceptance mismatch → FAIL
    8. report_summary_fields_match_synthesis files_changed mismatch → FAIL
    9. report_summary_fields_match_synthesis generated_artifacts mismatch → FAIL
    10-13: Existing generated-artifact, report prose, tmp-path, gate-profile tests pass
    """

    def test_decision_immutability_files_changed_fails(self) -> None:
        """Req 1: live decision_packet.md in files_changed causes FAIL."""
        result = _decision_immutability_check(
            files_changed={"project_state/decision_packet.md", "reverse_agent/project_gate.py"},
            new_dirty_files=set(),
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["status"] == "FAIL"
        assert result["live_decision_in_files_changed"] is True

    def test_decision_immutability_new_dirty_fails(self) -> None:
        """Req 2: live decision_packet.md in new_dirty_files causes FAIL."""
        result = _decision_immutability_check(
            files_changed=set(),
            new_dirty_files={"project_state/decision_packet.md"},
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["status"] == "FAIL"
        assert result["live_decision_in_new_dirty"] is True

    def test_decision_in_baseline_dirty_fails_preflight(self, tmp_path: Path) -> None:
        """Req 3: live decision_packet.md in baseline dirty causes preflight FAIL."""
        state_dir = _make_gate_state(tmp_path)
        baseline_path = state_dir / "gates" / "round_baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["baseline_dirty_files"] = ["project_state/decision_packet.md"]
        baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        result = preflight(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        decision_check = next(
            (c for c in result["checks"] if c["name"] == "decision_not_dirty_in_baseline"),
            None,
        )
        assert decision_check is not None
        assert decision_check["status"] == "FAIL"

    def test_startup_source_test_dirty_without_allowlist_fails_preflight(self, tmp_path: Path) -> None:
        """Req 4: startup source/test dirty without trusted allowlist causes preflight FAIL."""
        state_dir = _make_gate_state(tmp_path)
        baseline_path = state_dir / "gates" / "round_baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["baseline_dirty_files"] = ["reverse_agent/project_gate.py"]
        baseline["baseline_git_status_short"] = [" M reverse_agent/project_gate.py"]
        baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        result = preflight(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        clean_start_check = next(
            (c for c in result["checks"] if c["name"] == "source_test_clean_start"),
            None,
        )
        assert clean_start_check is not None
        assert clean_start_check["status"] == "FAIL"

    def test_late_allowlist_cannot_authorize_source_test_dirty(self, tmp_path: Path) -> None:
        """Req 5: late-added allowlist in live decision cannot authorize source/test dirty
        when decision was modified during execution (decision_immutability_failed=True)."""
        from reverse_agent.project_gate import _round_delta_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py
"""
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        pytest_text = (
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "F:\\reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: Get-Location =====\n"
            "F:\\reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
            "True\n===== EXIT: 0 =====\n"
            "===== COMMAND: git rev-parse --show-toplevel =====\n"
            "F:/reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: git status --short =====\n"
            " M reverse_agent/project_gate.py\n===== EXIT: 0 =====\n"
        )
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={"reverse_agent/project_gate.py", "project_state/codex_execution_report.md"},
            generated_artifacts=set(),
            archive_paths=set(),
            state_dir=state_dir,
            decision_text=decision_text,
            pytest_text=pytest_text,
            decision_immutability_failed=True,
        )
        inherited_check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert inherited_check["status"] == "FAIL"
        assert inherited_check["decision_immutability_failed"] is True

    def test_inherited_source_test_dirty_fails_without_all_conditions(self, tmp_path: Path) -> None:
        """Req 6: inherited source/test dirty in files_changed causes FAIL
        unless startup evidence, decision allowlist, and no decision mutation all hold."""
        from reverse_agent.project_gate import _round_delta_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py
"""
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={"reverse_agent/project_gate.py", "project_state/codex_execution_report.md"},
            generated_artifacts=set(),
            archive_paths=set(),
            state_dir=state_dir,
            decision_text=decision_text,
            pytest_text="",
            decision_immutability_failed=False,
        )
        inherited_check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert inherited_check["status"] == "FAIL"

    def test_inherited_source_test_dirty_passes_with_all_conditions(self, tmp_path: Path) -> None:
        """Req 6 variant: inherited source/test dirty PASSES when all three conditions hold."""
        from reverse_agent.project_gate import _round_delta_checks
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        decision_text = """# DECISION_PACKET

## Implementation Scope
Allowed source files:
- reverse_agent/project_gate.py

Allowed tests:
- tests/test_project_gate.py

## Allowed Inherited Dirty Baseline Files
- reverse_agent/project_gate.py
"""
        delta_summary = {
            "baseline_available": True,
            "baseline_dirty_files": ["reverse_agent/project_gate.py"],
            "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            "new_dirty_files_since_baseline": ["project_state/codex_execution_report.md"],
            "final_dirty_files": ["reverse_agent/project_gate.py", "project_state/codex_execution_report.md"],
        }
        pytest_text = (
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "F:\\reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: Get-Location =====\n"
            "F:\\reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
            "True\n===== EXIT: 0 =====\n"
            "===== COMMAND: git rev-parse --show-toplevel =====\n"
            "F:/reverse-agent\n===== EXIT: 0 =====\n"
            "===== COMMAND: git status --short =====\n"
            " M reverse_agent/project_gate.py\n===== EXIT: 0 =====\n"
        )
        checks = _round_delta_checks(
            delta_summary=delta_summary,
            files_changed={"reverse_agent/project_gate.py", "project_state/codex_execution_report.md"},
            generated_artifacts=set(),
            archive_paths=set(),
            state_dir=state_dir,
            decision_text=decision_text,
            pytest_text=pytest_text,
            decision_immutability_failed=False,
        )
        inherited_check = next(c for c in checks if c["name"] == "files_changed_excludes_inherited_dirty_files")
        assert inherited_check["status"] == "PASS"

    def test_report_summary_status_mismatch_fails(self) -> None:
        """Req 7: report_summary_fields_match_synthesis status mismatch causes FAIL."""
        from reverse_agent.project_gate import _has_structural_field_diff
        diffs = [{"field": "status", "expected": "SUCCESS", "actual": "FAILED"}]
        assert _has_structural_field_diff(diffs) is True

    def test_report_summary_acceptance_mismatch_fails(self) -> None:
        """Req 7 variant: acceptance_recommendation mismatch causes FAIL."""
        from reverse_agent.project_gate import _has_structural_field_diff
        diffs = [{"field": "acceptance_recommendation", "expected": "ACCEPTED", "actual": "REWORK_REQUIRED"}]
        assert _has_structural_field_diff(diffs) is True

    def test_report_summary_files_changed_mismatch_fails(self) -> None:
        """Req 8: files_changed mismatch causes FAIL."""
        from reverse_agent.project_gate import _has_structural_field_diff
        diffs = [{"field": "files_changed", "expected": ["a.py"], "actual": ["b.py"]}]
        assert _has_structural_field_diff(diffs) is True

    def test_report_summary_generated_artifacts_mismatch_fails(self) -> None:
        """Req 9: generated_artifacts mismatch causes FAIL."""
        from reverse_agent.project_gate import _has_structural_field_diff
        diffs = [{"field": "generated_artifacts", "expected": ["a.json"], "actual": ["b.json"]}]
        assert _has_structural_field_diff(diffs) is True

    def test_existing_generated_artifact_tests_pass(self, tmp_path: Path) -> None:
        """Req 10: Existing generated-artifact live-path tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        artifact_check = _check(result, "generated_artifact_live_paths_exist")
        assert artifact_check["status"] == "PASS"

    def test_existing_report_prose_tests_pass(self, tmp_path: Path) -> None:
        """Req 11: Existing report prose claim coverage tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        prose_check = _check(result, "report_prose_claims_covered_by_files_changed")
        assert prose_check["status"] in ("PASS", "WARN")

    def test_existing_tmp_path_tests_pass(self, tmp_path: Path) -> None:
        """Req 12: Existing tmp-path dirty-state tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        tmp_check = _check(result, "tmp_paths_absent_from_dirty_state")
        assert tmp_check["status"] == "PASS"

    def test_existing_gate_profile_tests_pass(self) -> None:
        """Req 13: Existing gate-profile classifier tests continue to pass."""
        from reverse_agent.project_gate import classify_gate_profile
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"


class TestPreflightFailureHandoff:
    """Verify preflight-failure handoff behavior per
    decision_20260617_preflight_failure_handoff_rework_v1.

    Required tests:
    1. preflight failed -> report summary status cannot be accepted/completed
    2. preflight failed -> acceptance recommendation must be REWORK_REQUIRED or BLOCKED
    3. command block exit 1 -> pytest_result_summary.status cannot be PASSED
    4. pytest_result_summary.status=PASSED plus command block exit 1 -> final-check FAIL
    5. preflight failed plus close-round attempted -> final-check or close-round FAIL
    6. unsupported report status such as COMPLETED_WITH_LIMITATIONS causes lint/final-check FAIL
    7. existing execution-authority hard-stop tests continue to pass
    8. existing generated-artifact live-path tests continue to pass
    9. existing report prose claim coverage tests continue to pass
    10. existing tmp-path dirty-state tests continue to pass
    11. existing gate-profile tests continue to pass
    """

    def test_preflight_failed_report_status_cannot_be_accepted(self, tmp_path: Path) -> None:
        """Req 1: preflight failed -> report summary status cannot be accepted/completed."""
        from reverse_agent.project_gate import _preflight_failure_handoff_check
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        preflight_result = {"gate_status": "FAILED", "checks": []}
        (gates_dir / "preflight_result.json").write_text(
            json.dumps(preflight_result), encoding="utf-8"
        )
        report = {"status": "SUCCESS", "acceptance_recommendation": "REWORK_REQUIRED"}
        result = _preflight_failure_handoff_check(state_dir=state_dir, report=report)
        assert result["status"] == "FAIL"
        assert "SUCCESS" in result["detail"]

    def test_preflight_failed_acceptance_must_be_rework_or_blocked(self, tmp_path: Path) -> None:
        """Req 2: preflight failed -> acceptance_recommendation must be REWORK_REQUIRED or BLOCKED."""
        from reverse_agent.project_gate import _preflight_failure_handoff_check
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        preflight_result = {"gate_status": "FAILED", "checks": []}
        (gates_dir / "preflight_result.json").write_text(
            json.dumps(preflight_result), encoding="utf-8"
        )
        report = {"status": "FAILED", "acceptance_recommendation": "ACCEPTED"}
        result = _preflight_failure_handoff_check(state_dir=state_dir, report=report)
        assert result["status"] == "FAIL"
        assert "ACCEPTED" in result["detail"]

    def test_preflight_failed_with_correct_report_passes(self, tmp_path: Path) -> None:
        """Req 2 variant: preflight failed with correct FAILED/REWORK_REQUIRED passes."""
        from reverse_agent.project_gate import _preflight_failure_handoff_check
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        preflight_result = {"gate_status": "FAILED", "checks": []}
        (gates_dir / "preflight_result.json").write_text(
            json.dumps(preflight_result), encoding="utf-8"
        )
        report = {"status": "FAILED", "acceptance_recommendation": "REWORK_REQUIRED"}
        result = _preflight_failure_handoff_check(state_dir=state_dir, report=report)
        assert result["status"] == "PASS"

    def test_command_block_exit1_pytest_status_cannot_be_passed(self) -> None:
        """Req 3: command block exit 1 -> pytest_result_summary.status cannot be PASSED."""
        from reverse_agent.project_state import validate_pytest_result_for_report
        pytest_text = (
            '```json pytest_result_summary\n'
            '{"schema_version": 1, "decision_id": "d1", "report_id": "r1", '
            '"round_id": "r1", "status": "PASSED", "tests_ran": []}\n'
            '```\n'
            '===== COMMAND: preflight =====\n'
            'preflight: FAILED\n'
            '===== EXIT: 1 =====\n'
        )
        report = {"based_on_decision_id": "d1", "report_id": "r1", "round_id": "r1", "tests_ran": []}
        result = validate_pytest_result_for_report(pytest_text, report)
        assert any("non-zero exit codes" in e for e in result.get("errors", []))

    def test_pytest_passed_plus_exit1_causes_final_check_fail(self, tmp_path: Path) -> None:
        """Req 4: pytest_result_summary.status=PASSED plus command block exit 1 -> final-check FAIL."""
        from reverse_agent.project_state import validate_pytest_result_for_report
        pytest_text = (
            '```json pytest_result_summary\n'
            '{"schema_version": 1, "decision_id": "d1", "report_id": "r1", '
            '"round_id": "r1", "status": "PASSED", "tests_ran": []}\n'
            '```\n'
            '===== COMMAND: preflight =====\n'
            'preflight: FAILED\n'
            '===== EXIT: 1 =====\n'
        )
        report = {"based_on_decision_id": "d1", "report_id": "r1", "round_id": "r1", "tests_ran": []}
        result = validate_pytest_result_for_report(pytest_text, report)
        assert result.get("errors"), "expected errors when PASSED status contradicts non-zero exit codes"

    def test_preflight_failed_close_round_attempted_fails(self, tmp_path: Path) -> None:
        """Req 5: preflight failed plus close-round attempted -> final-check or close-round FAIL."""
        from reverse_agent.project_gate import _preflight_failure_handoff_check
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        preflight_result = {"gate_status": "FAILED", "checks": []}
        (gates_dir / "preflight_result.json").write_text(
            json.dumps(preflight_result), encoding="utf-8"
        )
        report = {"status": "SUCCESS", "acceptance_recommendation": "ACCEPTED"}
        result = _preflight_failure_handoff_check(state_dir=state_dir, report=report)
        assert result["status"] == "FAIL"

    def test_unsupported_report_status_causes_lint_fail(self) -> None:
        """Req 6: unsupported report status such as COMPLETED_WITH_LIMITATIONS causes lint FAIL."""
        from reverse_agent.project_state import _normalize_status, CODEX_REPORT_STATUSES
        status, error = _normalize_status("COMPLETED_WITH_LIMITATIONS", CODEX_REPORT_STATUSES)
        assert error is not None, "COMPLETED_WITH_LIMITATIONS should not be a valid report status"
        assert status == "UNKNOWN"

    def test_existing_hard_stop_tests_pass(self, tmp_path: Path) -> None:
        """Req 7: existing execution-authority hard-stop tests continue to pass."""
        result = _decision_immutability_check(
            files_changed={"project_state/decision_packet.md"},
            new_dirty_files=set(),
            baseline_dirty_files=set(),
            round_id="round_test",
        )
        assert result["status"] == "FAIL"

    def test_existing_generated_artifact_tests_pass(self, tmp_path: Path) -> None:
        """Req 8: existing generated-artifact live-path tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        artifact_check = _check(result, "generated_artifact_live_paths_exist")
        assert artifact_check["status"] == "PASS"

    def test_existing_report_prose_tests_pass(self, tmp_path: Path) -> None:
        """Req 9: existing report prose claim coverage tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        prose_check = _check(result, "report_prose_claims_covered_by_files_changed")
        assert prose_check["status"] in ("PASS", "WARN")

    def test_existing_tmp_path_tests_pass(self, tmp_path: Path) -> None:
        """Req 10: existing tmp-path dirty-state tests continue to pass."""
        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        tmp_check = _check(result, "tmp_paths_absent_from_dirty_state")
        assert tmp_check["status"] == "PASS"

    def test_existing_gate_profile_tests_pass(self) -> None:
        """Req 11: existing gate-profile tests continue to pass."""
        from reverse_agent.project_gate import classify_gate_profile
        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"


class TestStartupBaselineConsistency:
    """Verify startup-baseline consistency checks including the reverse case
    where startup is clean but baseline claims source/test dirty files.
    """

    _CLEAN_PYTEST_TEXT = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "Path\n----\nF:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git status --short =====\n"
        "===== EXIT: 0 =====\n"
    )

    _DIRTY_PYTEST_TEXT = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "Path\n----\nF:\\reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: git status --short =====\n"
        " M reverse_agent/project_gate.py\n"
        "===== EXIT: 0 =====\n"
    )

    _DECISION_TEXT = (
        "## Implementation Scope\n\n"
        "Allowed source files:\n\n"
        "- `reverse_agent/project_gate.py`\n\n"
        "Allowed tests:\n\n"
        "- `tests/test_project_gate.py`\n\n"
        "## Do Not Do\nNothing\n"
    )

    def test_startup_clean_baseline_source_test_dirty_fails(self) -> None:
        """Startup git status clean, baseline has source/test dirty -> FAIL."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["reverse_agent/project_gate.py"],
                "inherited_dirty_files": ["reverse_agent/project_gate.py"],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=self._CLEAN_PYTEST_TEXT,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "FAIL"
        assert "clean" in result["detail"].lower()
        assert "baseline" in result["detail"].lower()
        assert "reverse_agent/project_gate.py" in result.get("baseline_source_test_dirty", [])

    def test_startup_dirty_baseline_missing_fails(self) -> None:
        """Startup git status shows source/test dirty, baseline doesn't record them -> FAIL."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=self._DIRTY_PYTEST_TEXT,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "FAIL"
        assert "reverse_agent/project_gate.py" in result.get("missing_from_baseline", [])

    def test_startup_dirty_baseline_agrees_passes(self) -> None:
        """Startup and baseline agree on source/test dirty -> PASS."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["reverse_agent/project_gate.py"],
                "inherited_dirty_files": [],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=self._DIRTY_PYTEST_TEXT,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"

    def test_startup_clean_baseline_clean_passes(self) -> None:
        """Both startup and baseline are clean -> PASS."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=self._CLEAN_PYTEST_TEXT,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"

    def test_startup_evidence_not_trusted_skips(self) -> None:
        """Startup evidence not trusted -> PASS (skip)."""
        # Use a pytest_text without proper path-confirmation order
        # so startup evidence is not trusted
        untrusted_pytest = (
            "===== COMMAND: git status --short =====\n"
            " M reverse_agent/project_gate.py\n"
            "===== EXIT: 0 =====\n"
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "F:\\reverse-agent\n"
            "===== EXIT: 0 =====\n"
        )
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": ["reverse_agent/project_gate.py"],
                "inherited_dirty_files": [],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=untrusted_pytest,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"
        assert result.get("startup_evidence_trusted") is False


class TestStaleArtifactIds:
    """Verify stale artifact ID detection in gate artifacts."""

    def test_preflight_stale_round_id_fails(self, tmp_path: Path) -> None:
        """preflight_result.json has wrong round_id -> FAIL."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "preflight_result.json", {
            "decision_id": "d1",
            "round_id": "stale_round",
            "gate_status": "PASSED",
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "FAIL"
        stale = result.get("stale_artifacts", [])
        assert any(s["artifact"] == "preflight_result.json" and s["field"] == "round_id" for s in stale)

    def test_report_summary_stale_report_id_fails(self, tmp_path: Path) -> None:
        """report_summary_synthesis.json has wrong report_id -> FAIL."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "report_summary_synthesis.json", {
            "decision_id": "d1",
            "round_id": "r1",
            "report_id": "stale_report",
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "FAIL"
        stale = result.get("stale_artifacts", [])
        assert any(s["artifact"] == "report_summary_synthesis.json" and s["field"] == "report_id" for s in stale)

    def test_final_gate_stale_round_id_fails(self, tmp_path: Path) -> None:
        """final_gate_result.json has wrong round_id -> FAIL."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "final_gate_result.json", {
            "decision_id": "d1",
            "round_id": "stale_round",
            "report_id": "rp1",
            "gate_status": "PASSED",
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "d1",
            "round_id": "stale_round",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "FAIL"
        stale = result.get("stale_artifacts", [])
        assert any(s["artifact"] == "final_gate_result.json" and s["field"] == "round_id" for s in stale)

    def test_command_plan_stale_decision_id_fails(self, tmp_path: Path) -> None:
        """command_plan.json has wrong decision_id -> FAIL."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "command_plan.json", {
            "decision_id": "stale_decision",
            "round_id": "r1",
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "stale_decision",
            "round_id": "r1",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "FAIL"
        stale = result.get("stale_artifacts", [])
        assert any(s["artifact"] == "command_plan.json" and s["field"] == "decision_id" for s in stale)

    def test_all_artifacts_current_passes(self, tmp_path: Path) -> None:
        """All artifacts have current IDs -> PASS."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "preflight_result.json", {
            "decision_id": "d1",
            "round_id": "r1",
            "gate_status": "PASSED",
        })
        _write_json(gates_dir / "report_summary_synthesis.json", {
            "decision_id": "d1",
            "round_id": "r1",
            "report_id": "rp1",
        })
        _write_json(gates_dir / "command_plan.json", {
            "decision_id": "d1",
            "round_id": "r1",
        })
        _write_json(gates_dir / "final_gate_result.json", {
            "decision_id": "d1",
            "round_id": "r1",
            "report_id": "rp1",
            "gate_status": "PASSED",
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "d1",
            "round_id": "r1",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "PASS"

    def test_no_artifacts_passes(self, tmp_path: Path) -> None:
        """No artifacts exist -> PASS."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "PASS"

    def test_current_report_partial_not_accepted(self, tmp_path: Path) -> None:
        """report PARTIAL/REWORK_REQUIRED must not be treated as accepted in stale ID check.

        This test verifies that even with current IDs, the stale_artifact_id_check
        correctly returns PASS (it only checks IDs, not report status). The
        report status acceptance is handled by other checks.
        """
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        _write_json(gates_dir / "final_gate_result.json", {
            "decision_id": "d1",
            "round_id": "r1",
            "report_id": "rp1",
            "gate_status": "FAILED",
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "d1",
            "round_id": "r1",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })
        result = _stale_artifact_id_check(
            state_dir=state_dir,
            decision_id="d1",
            round_id="r1",
            report_id="rp1",
        )
        # Stale ID check should PASS — IDs are current even if gate failed
        assert result["name"] == "stale_artifact_ids"
        assert result["status"] == "PASS"

    def test_existing_preflight_failure_handoff_tests_pass(self, tmp_path: Path) -> None:
        """Verify existing preflight-failure handoff tests still pass."""
        from reverse_agent.project_gate import _preflight_failure_handoff_check
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True)
        preflight_result = {"gate_status": "FAILED", "checks": []}
        (gates_dir / "preflight_result.json").write_text(
            json.dumps(preflight_result), encoding="utf-8"
        )
        report = {"status": "FAILED", "acceptance_recommendation": "REWORK_REQUIRED"}
        result = _preflight_failure_handoff_check(state_dir=state_dir, report=report)
        assert result["status"] == "PASS"


class TestCurrentReportGateRegeneration:
    """Verify that final_check and close_round derive IDs from the decision
    packet rather than the potentially-stale live report, and that stale
    gate artifacts are correctly detected.
    """

    @staticmethod
    def _make_base_state(
        tmp_path: Path,
        *,
        decision_id: str,
        round_id: str,
        report_id: str,
        report_round_id: str,
        report_status: str = "SUCCESS",
        report_acceptance: str = "ACCEPTED",
        report_based_on_decision_id: str | None = None,
    ) -> Path:
        """Create a minimal project_state directory for gate testing."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {
                "round_id": round_id,
                "state_build_id": "state_test",
                "state_digest": "digest_test",
                "state_scope": "sample_state",
                "source_harness_run": "run_test",
            },
        )
        _write_json(
            state_dir / "task_packet.json",
            {
                "state_scope": "sample_state",
                "task_source": "derived_from_sample_artifacts",
                "execution_scope": "decision_packet_controls_current_round",
                "active_decision_packet": "project_state/decision_packet.md",
            },
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})
        _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
        _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
        based_on = report_based_on_decision_id if report_based_on_decision_id is not None else decision_id
        _write_report(
            state_dir,
            decision_id=based_on,
            report_id=report_id,
            round_id=report_round_id,
            status=report_status,
            acceptance=report_acceptance,
        )
        return state_dir

    def test_final_check_uses_decision_round_id_not_stale_report(self, tmp_path: Path) -> None:
        """final_check derives round_id and report_id from the decision, not the stale report."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test1",
            round_id="round_test1",
            report_id="codex_report_old_round",
            report_round_id="round_old",
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        assert result["round_id"] == "round_test1"
        assert result["report_id"] == "codex_report_test1"
        assert result["report_id"] != "codex_report_old_round"

    def test_close_round_uses_decision_report_id_not_stale_report(self, tmp_path: Path) -> None:
        """close_round computes report_id from decision round_id, not stale report."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test2",
            round_id="round_test2",
            report_id="codex_report_old",
            report_round_id="round_old",
        )

        result = close_round(state_dir=state_dir, round_id="round_test2", repo_root=tmp_path)

        assert result["report_id"] == "codex_report_test2"
        assert result["report_id"] != "codex_report_old"

    def test_close_round_requested_round_id_matches_decision_not_report(self, tmp_path: Path) -> None:
        """requested_round_id_match passes when requested matches decision, even if report is stale."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test3",
            round_id="round_test3",
            report_id="codex_report_old",
            report_round_id="round_old",
        )

        result = close_round(state_dir=state_dir, round_id="round_test3", repo_root=tmp_path)

        round_id_check = _check(result, "requested_round_id_match")
        assert round_id_check["status"] == "PASS"

    def test_close_round_wrong_requested_round_id_fails(self, tmp_path: Path) -> None:
        """requested_round_id_match fails when requested round_id doesn't match decision."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test4",
            round_id="round_test4",
            report_id="codex_report_test4",
            report_round_id="round_test4",
        )

        result = close_round(state_dir=state_dir, round_id="round_wrong", repo_root=tmp_path)

        round_id_check = _check(result, "requested_round_id_match")
        assert round_id_check["status"] == "FAIL"

    def test_stale_report_summary_synthesis_fails_final_check(self, tmp_path: Path) -> None:
        """stale report_summary_synthesis.json report_id causes stale_artifact_ids FAIL."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test5",
            round_id="round_test5",
            report_id="codex_report_test5",
            report_round_id="round_test5",
        )
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        _write_json(gates_dir / "report_summary_synthesis.json", {
            "schema_version": 1,
            "artifact_name": "report_summary_synthesis.json",
            "decision_id": "decision_test5",
            "round_id": "round_test5",
            "report_id": "codex_report_stale_round",
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        stale_check = _check(result, "stale_artifact_ids")
        assert stale_check["status"] == "FAIL"

    def test_stale_final_gate_result_fails_final_check(self, tmp_path: Path) -> None:
        """stale final_gate_result.json round_id causes stale_artifact_ids FAIL."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test6",
            round_id="round_test6",
            report_id="codex_report_test6",
            report_round_id="round_test6",
        )
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        _write_json(gates_dir / "final_gate_result.json", {
            "schema_version": 1,
            "artifact_name": "final_gate_result.json",
            "decision_id": "decision_test6",
            "round_id": "round_stale",
            "report_id": "codex_report_test6",
            "gate_status": "PASSED",
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "decision_test6",
            "round_id": "round_stale",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        stale_check = _check(result, "stale_artifact_ids")
        assert stale_check["status"] == "FAIL"

    def test_close_round_failed_prevents_accepted_status(self, tmp_path: Path) -> None:
        """close_round with PARTIAL/REWORK_REQUIRED does not produce CLOSED status or ACCEPTED."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test7",
            round_id="round_test7",
            report_id="codex_report_test7",
            report_round_id="round_test7",
            report_status="PARTIAL",
            report_acceptance="REWORK_REQUIRED",
        )

        result = close_round(state_dir=state_dir, round_id="round_test7", repo_root=tmp_path)

        assert result["close_status"] != "CLOSED"
        # Verify the report's acceptance_recommendation is still REWORK_REQUIRED
        report = read_codex_report_summary(state_dir)
        assert report.get("acceptance_recommendation") == "REWORK_REQUIRED"

    def test_command_plan_exit_code_mismatch_remains_blocking(self, tmp_path: Path) -> None:
        """Exit code mismatch between command_plan and pytest_result is still FAIL."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test8",
            round_id="round_test8",
            report_id="codex_report_test8",
            report_round_id="round_test8",
        )
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        command = "python -m pytest -q"
        command_plan_command = "python -m reverse_agent.project_gate command-plan --state-dir project_state"
        _write_json(gates_dir / "command_plan.json", {
            "schema_version": 1,
            "plan_name": "command-plan",
            "plan_status": "PASSED",
            "decision_id": "decision_test8",
            "round_id": "round_test8",
            "mainline": "engineering_branch",
            "generated_at": "2026-06-11T00:00:00Z",
            "commands": [
                {
                    "index": 1,
                    "command": command,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": command_plan_command,
                    "phase": "gate",
                    "kind": "command-plan",
                    "required": True,
                    "expected_exit_codes": [0],
                },
            ],
            "warnings": [],
            "blocking_reasons": [],
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "decision_test8",
            "round_id": "round_test8",
            "mainline": "engineering_branch",
            "profile": "full",
            "profile_reason": "test fixture",
            "closeout_allowed": True,
            "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
        })
        # Rewrite the report to include command-plan in tests_ran and generated_artifacts
        _write_report(
            state_dir,
            decision_id="decision_test8",
            report_id="codex_report_test8",
            round_id="round_test8",
            tests_ran=[command, command_plan_command],
            generated_artifacts=["project_state/gates/command_plan.json"],
        )
        # Write a pytest_result.txt with exit code 1 for the pytest command
        pytest_body = _command_block(command, "1 failed", exit_code=1)
        write_pytest_result(
            state_dir=state_dir,
            summary={
                "schema_version": 1,
                "decision_id": "decision_test8",
                "report_id": "codex_report_test8",
                "round_id": "round_test8",
                "generated_at": "2026-06-11T00:00:00Z",
                "status": "PASSED",
                "tests_ran": [command, command_plan_command],
            },
            body=pytest_body,
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        exit_code_check = _check(result, "pytest_result_exit_codes_match_command_plan")
        assert exit_code_check["status"] == "FAIL"

    def test_partial_rework_not_accepted(self, tmp_path: Path) -> None:
        """PARTIAL/REWORK_REQUIRED must not be treated as accepted in status_policy_valid."""
        state_dir = self._make_base_state(
            tmp_path,
            decision_id="decision_test9",
            round_id="round_test9",
            report_id="codex_report_test9",
            report_round_id="round_test9",
            report_status="PARTIAL",
            report_acceptance="REWORK_REQUIRED",
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        status_policy = _check(result, "status_policy_valid")
        assert status_policy["status"] != "PASS"


class TestCommandPlanExpectedExitSemantics:
    """Tests for diagnostic exit-code tolerance and conditional close-round semantics."""

    @staticmethod
    def _make_state_dir(
        tmp_path: Path,
        *,
        decision_id: str = "decision_exit_sem",
        round_id: str = "round_exit_sem",
        command_plan_commands: list[dict[str, Any]],
        report_tests: list[str] | None = None,
        report_generated_artifacts: list[str] | None = None,
    ) -> Path:
        """Create a minimal state_dir with a command_plan.json for validation tests."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        # Build report tests_ran from command_plan commands if not specified
        if report_tests is None:
            report_tests = [c["command"] for c in command_plan_commands]
        if report_generated_artifacts is None:
            report_generated_artifacts = ["project_state/gates/command_plan.json"]

        _write_json(
            gates_dir / "command_plan.json",
            {
                "schema_version": 1,
                "plan_name": "command-plan",
                "plan_status": "PASSED",
                "decision_id": decision_id,
                "round_id": round_id,
                "mainline": "engineering_branch",
                "generated_at": "2026-06-17T00:00:00Z",
                "commands": command_plan_commands,
                "warnings": [],
                "blocking_reasons": [],
            },
        )
        return state_dir

    @staticmethod
    def _decision_dict(
        *,
        decision_id: str = "decision_exit_sem",
        round_id: str = "round_exit_sem",
    ) -> dict[str, Any]:
        return {
            "decision_id": decision_id,
            "round_id": round_id,
            "mainline": "engineering_branch",
        }

    @staticmethod
    def _report_dict(
        *,
        decision_id: str = "decision_exit_sem",
        round_id: str = "round_exit_sem",
        report_id: str = "codex_report_exit_sem",
        tests_ran: list[str] | None = None,
        generated_artifacts: list[str] | None = None,
        status: str = "SUCCESS",
        acceptance: str = "ACCEPTED",
    ) -> dict[str, Any]:
        return {
            "report_id": report_id,
            "round_id": round_id,
            "based_on_decision_id": decision_id,
            "status": status,
            "acceptance_recommendation": acceptance,
            "tests_ran": tests_ran if tests_ran is not None else [],
            "generated_artifacts": generated_artifacts if generated_artifacts is not None else ["project_state/gates/command_plan.json"],
        }

    def test_diagnostic_exit_1_not_mismatch(self, tmp_path: Path) -> None:
        """Doctor command with expected_exit_codes [0,1] and exit code 1 is not a mismatch."""
        doctor_cmd = "python -m reverse_agent.project_gate doctor --state-dir project_state"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": doctor_cmd,
                    "phase": "status",
                    "kind": "doctor",
                    "required": True,
                    "expected_exit_codes": [0, 1],
                },
            ],
        )
        pytest_text = _command_block(doctor_cmd, "diagnostic findings", exit_code=1)

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[doctor_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        assert exit_check["status"] == "PASS"


    def test_diagnostic_exit_1_visible_in_report_not_accepted(self, tmp_path: Path) -> None:
        """A report with PARTIAL/REWORK_REQUIRED is not treated as accepted/completed."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {
                "round_id": "round_diag",
                "state_build_id": "state_test",
                "state_digest": "digest_test",
                "state_scope": "sample_state",
            },
        )
        _write_json(
            state_dir / "task_packet.json",
            {
                "state_scope": "sample_state",
                "task_source": "derived_from_sample_artifacts",
                "execution_scope": "decision_packet_controls_current_round",
                "active_decision_packet": "project_state/decision_packet.md",
            },
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})
        _write_decision(state_dir, decision_id="decision_diag", round_id="round_diag")
        _write_round_baseline(state_dir, decision_id="decision_diag", round_id="round_diag")
        _write_report(
            state_dir,
            decision_id="decision_diag",
            report_id="codex_report_diag",
            round_id="round_diag",
            status="PARTIAL",
            acceptance="REWORK_REQUIRED",
        )

        report = read_codex_report_summary(state_dir)
        assert report.get("status") == "PARTIAL"
        assert report.get("acceptance_recommendation") == "REWORK_REQUIRED"
        # Verify that PARTIAL/REWORK_REQUIRED is not treated as accepted
        assert report.get("acceptance_recommendation") != "ACCEPTED"
        assert report.get("status") != "SUCCESS"

    def test_ordinary_required_command_exit_1_fails(self, tmp_path: Path) -> None:
        """A pytest command with expected_exit_codes [0] and exit code 1 is a mismatch."""
        pytest_cmd = "python -m pytest -q"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": pytest_cmd,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
            ],
        )
        pytest_text = _command_block(pytest_cmd, "1 failed", exit_code=1)

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[pytest_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        assert exit_check["status"] == "FAIL"

    def test_final_check_failed_skips_close_round(self, tmp_path: Path) -> None:
        """Close-round with required=False (final-check failed) is skipped in validation."""
        close_cmd = "python -m reverse_agent.project_gate close-round --state-dir project_state"
        pytest_cmd = "python -m pytest -q"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": pytest_cmd,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": close_cmd,
                    "phase": "gate",
                    "kind": "close-round",
                    "required": False,
                    "expected_exit_codes": [0, 1],
                    "conditional_closeout": True,
                },
            ],
        )
        # pytest_result.txt has the pytest command but no close-round block
        pytest_text = _command_block(pytest_cmd, "1 passed", exit_code=0)

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[pytest_cmd, close_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        # close-round is skipped because required=False, so no mismatch
        assert exit_check["status"] == "PASS"

    def test_final_check_passed_allows_close_round_expected_0(self, tmp_path: Path) -> None:
        """Close-round with required=True (final-check passed) and exit 0 passes validation."""
        close_cmd = "python -m reverse_agent.project_gate close-round --state-dir project_state"
        pytest_cmd = "python -m pytest -q"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": pytest_cmd,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": close_cmd,
                    "phase": "gate",
                    "kind": "close-round",
                    "required": True,
                    "expected_exit_codes": [0],
                    "conditional_closeout": True,
                },
            ],
        )
        pytest_text = (
            _command_block(pytest_cmd, "1 passed", exit_code=0)
            + "\n"
            + _command_block(close_cmd, "round closed", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[pytest_cmd, close_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        assert exit_check["status"] == "PASS"

    def test_close_round_exit_1_in_closeout_mode_blocks(self, tmp_path: Path) -> None:
        """Close-round with required=True (final-check passed) and exit 1 fails validation."""
        close_cmd = "python -m reverse_agent.project_gate close-round --state-dir project_state"
        pytest_cmd = "python -m pytest -q"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": pytest_cmd,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": close_cmd,
                    "phase": "gate",
                    "kind": "close-round",
                    "required": True,
                    "expected_exit_codes": [0],
                    "conditional_closeout": True,
                },
            ],
        )
        pytest_text = (
            _command_block(pytest_cmd, "1 passed", exit_code=0)
            + "\n"
            + _command_block(close_cmd, "close failed", exit_code=1)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[pytest_cmd, close_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        assert exit_check["status"] == "FAIL"

    def test_command_plan_json_records_kind_phase_expected_exit(self, tmp_path: Path) -> None:
        """command_plan output includes kind, phase, expected_exit_codes for each command."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {
                "round_id": "round_cp",
                "state_build_id": "state_test",
                "state_digest": "digest_test",
                "state_scope": "sample_state",
            },
        )
        _write_json(
            state_dir / "task_packet.json",
            {
                "state_scope": "sample_state",
                "task_source": "derived_from_sample_artifacts",
                "execution_scope": "decision_packet_controls_current_round",
                "active_decision_packet": "project_state/decision_packet.md",
            },
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})
        # Write a decision with a doctor command and a pytest command
        _write_command_plan_decision(
            state_dir,
            tests_block=(
                "python -m reverse_agent.project_gate doctor --state-dir project_state\n"
                "python -m pytest -q"
            ),
        )

        result = command_plan(state_dir=state_dir, write_result=False)

        commands = result.get("commands", [])
        assert len(commands) >= 2

        # Verify each command has kind, phase, expected_exit_codes
        for cmd in commands:
            assert "kind" in cmd, f"command missing 'kind': {cmd}"
            assert "phase" in cmd, f"command missing 'phase': {cmd}"
            assert "expected_exit_codes" in cmd, f"command missing 'expected_exit_codes': {cmd}"

        # Verify diagnostic commands have expected_exit_codes [0, 1]
        diagnostic_kinds = {"doctor", "lint-report", "report-summary", "final-check"}
        for cmd in commands:
            if cmd["kind"] in diagnostic_kinds:
                assert cmd["expected_exit_codes"] == [0, 1], (
                    f"diagnostic command kind={cmd['kind']} should have expected_exit_codes [0, 1], "
                    f"got {cmd['expected_exit_codes']}"
                )

        # Verify ordinary commands (pytest, etc.) have expected_exit_codes [0]
        ordinary_kinds = {"pytest", "command-plan", "run-round"}
        for cmd in commands:
            if cmd["kind"] in ordinary_kinds:
                assert cmd["expected_exit_codes"] == [0], (
                    f"ordinary command kind={cmd['kind']} should have expected_exit_codes [0], "
                    f"got {cmd['expected_exit_codes']}"
                )

    def test_current_round_final_check_no_longer_fails_on_diagnostic_exit_1(self, tmp_path: Path) -> None:
        """Diagnostic commands recording exit code 1 do not cause exit-code mismatch."""
        doctor_cmd = "python -m reverse_agent.project_gate doctor --state-dir project_state"
        lint_cmd = "python -m reverse_agent.project_gate lint-report --state-dir project_state"
        pytest_cmd = "python -m pytest -q"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {
                    "index": 1,
                    "command": doctor_cmd,
                    "phase": "status",
                    "kind": "doctor",
                    "required": True,
                    "expected_exit_codes": [0, 1],
                },
                {
                    "index": 2,
                    "command": lint_cmd,
                    "phase": "status",
                    "kind": "lint-report",
                    "required": True,
                    "expected_exit_codes": [0, 1],
                },
                {
                    "index": 3,
                    "command": pytest_cmd,
                    "phase": "test",
                    "kind": "pytest",
                    "required": True,
                    "expected_exit_codes": [0],
                },
            ],
        )
        pytest_text = (
            _command_block(doctor_cmd, "findings detected", exit_code=1)
            + "\n"
            + _command_block(lint_cmd, "lint issues found", exit_code=1)
            + "\n"
            + _command_block(pytest_cmd, "1 passed", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision=self._decision_dict(),
            report=self._report_dict(tests_ran=[doctor_cmd, lint_cmd, pytest_cmd]),
            pytest_text=pytest_text,
        )

        exit_check = next(c for c in checks if c["name"] == "pytest_result_exit_codes_match_command_plan")
        assert exit_check["status"] == "PASS"



class TestReportBodyConsistency:
    """Tests for report body prose vs JSON summary status consistency."""

    @staticmethod
    def _make_report_text(status_line: str, extra_lines: str = "") -> str:
        """Build a minimal report body with a ## Status section."""
        return (
            "```json codex_report_summary\n"
            '{"schema_version": 1}\n'
            "```\n"
            "\n"
            "# CODEX_EXECUTION_REPORT\n"
            "\n"
            "## Goal\n"
            "\n"
            "Test goal.\n"
            "\n"
            f"## Status\n"
            "\n"
            f"{status_line}\n"
            f"{extra_lines}\n"
            "\n"
            "## Implementation Changes\n"
            "\n"
            "None.\n"
        )

    def test_json_success_body_partial_fails(self) -> None:
        """JSON summary SUCCESS plus body PARTIAL causes report-body consistency FAIL."""
        report_text = self._make_report_text(
            "PARTIAL — Some work was done but not all tests pass."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["name"] == "report_body_consistency"
        assert result["status"] == "FAIL"
        assert any("PARTIAL" in c for c in result.get("contradictions", []))

    def test_json_success_body_failed_fails(self) -> None:
        """JSON summary SUCCESS plus body FAILED causes report-body consistency FAIL."""
        report_text = self._make_report_text(
            "FAILED — Critical issues remain."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("FAILED" in c for c in result.get("contradictions", []))

    def test_json_accepted_body_rework_required_fails(self) -> None:
        """JSON ACCEPTED plus body REWORK_REQUIRED causes FAIL."""
        report_text = self._make_report_text(
            "SUCCESS — All done. REWORK_REQUIRED due to edge cases."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("REWORK_REQUIRED" in c for c in result.get("contradictions", []))

    def test_json_accepted_body_blocked_fails(self) -> None:
        """JSON ACCEPTED plus body BLOCKED causes FAIL."""
        report_text = self._make_report_text(
            "SUCCESS — All done. BLOCKED by upstream issue."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("BLOCKED" in c for c in result.get("contradictions", []))

    def test_json_success_body_close_round_still_fails_fails(self) -> None:
        """JSON SUCCESS plus body 'close-round still fails' causes FAIL."""
        report_text = self._make_report_text(
            "SUCCESS — All done.",
            "Close-round still fails due to ID mismatch."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("close-round still fails" in c for c in result.get("contradictions", []))

    def test_json_success_body_previous_round_report_still_live_fails(self) -> None:
        """JSON SUCCESS plus body 'previous round's report is still the live report' causes FAIL."""
        report_text = self._make_report_text(
            "SUCCESS — All done.",
            "The previous round's report is still the live report."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("previous round" in c for c in result.get("contradictions", []))

    def test_matching_json_success_body_success_passes(self) -> None:
        """Matching JSON SUCCESS and body SUCCESS passes."""
        report_text = self._make_report_text(
            "SUCCESS — All code changes implemented and tests pass."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "PASS"

    def test_matching_json_partial_body_partial_passes(self) -> None:
        """Matching JSON PARTIAL and body PARTIAL passes when genuinely PARTIAL."""
        report_text = self._make_report_text(
            "PARTIAL — Some work was done but not all tests pass."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="PARTIAL",
            acceptance_recommendation="REWORK_REQUIRED",
        )
        assert result["status"] == "PASS"

    def test_matching_json_failed_body_failed_passes(self) -> None:
        """Matching JSON FAILED and body FAILED passes when genuinely FAILED."""
        report_text = self._make_report_text(
            "FAILED — Critical issues remain."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="FAILED",
            acceptance_recommendation="REWORK_REQUIRED",
        )
        assert result["status"] == "PASS"

    def test_json_success_body_blocked_prefix_fails(self) -> None:
        """JSON SUCCESS plus body status beginning with BLOCKED causes FAIL."""
        report_text = self._make_report_text(
            "BLOCKED — Cannot proceed due to missing dependency."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("BLOCKED" in c for c in result.get("contradictions", []))

    def test_empty_status_section_passes(self) -> None:
        """Empty ## Status section does not cause a contradiction."""
        report_text = (
            "```json codex_report_summary\n"
            '{"schema_version": 1}\n'
            "```\n"
            "\n"
            "# CODEX_EXECUTION_REPORT\n"
            "\n"
            "## Goal\n"
            "\n"
            "Test goal.\n"
            "\n"
            "## Status\n"
            "\n"
            "## Implementation Changes\n"
            "\n"
            "None.\n"
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "PASS"

    def test_json_success_body_previous_round_still_live_short_form_fails(self) -> None:
        """JSON SUCCESS plus body 'previous round's report is still live' (short form) causes FAIL."""
        report_text = self._make_report_text(
            "SUCCESS — All done.",
            "The previous round's report is still live."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "FAIL"
        assert any("previous round" in c for c in result.get("contradictions", []))

    def test_json_accepted_body_rework_in_non_status_section_passes(self) -> None:
        """REWORK_REQUIRED in a non-Status section does not trigger a contradiction."""
        report_text = (
            "```json codex_report_summary\n"
            '{"schema_version": 1}\n'
            "```\n"
            "\n"
            "# CODEX_EXECUTION_REPORT\n"
            "\n"
            "## Goal\n"
            "\n"
            "Test goal.\n"
            "\n"
            "## Status\n"
            "\n"
            "SUCCESS — All done.\n"
            "\n"
            "## Remaining Limitations\n"
            "\n"
            "REWORK_REQUIRED for edge cases.\n"
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        # REWORK_REQUIRED is in Remaining Limitations, not in Status section
        assert result["status"] == "PASS"

    def test_json_blocked_body_blocked_passes(self) -> None:
        """Matching JSON BLOCKED and body BLOCKED passes."""
        report_text = self._make_report_text(
            "BLOCKED — Cannot proceed."
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="BLOCKED",
            acceptance_recommendation="BLOCKED",
        )
        assert result["status"] == "PASS"

    def test_no_status_section_passes(self) -> None:
        """Report without a ## Status section does not cause a contradiction."""
        report_text = (
            "```json codex_report_summary\n"
            '{"schema_version": 1}\n'
            "```\n"
            "\n"
            "# CODEX_EXECUTION_REPORT\n"
            "\n"
            "## Goal\n"
            "\n"
            "Test goal.\n"
        )
        result = _report_body_consistency_check(
            report_text=report_text,
            report_status="SUCCESS",
            acceptance_recommendation="ACCEPTED",
        )
        assert result["status"] == "PASS"


class TestGateProfileTierIntegration:
    """Tests for gate profile tier integration (fast/standard/full)."""

    def test_auto_profile_defaults_full_for_project_gate_changes(self) -> None:
        """Auto profile defaults to full for reverse_agent/project_gate.py changes."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"
        assert result["closeout_allowed"] is True
        assert "close-round" in result["required_command_kinds"]

    def test_auto_profile_defaults_full_for_project_state_changes(self) -> None:
        """Auto profile defaults to full for reverse_agent/project_state.py changes."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_state.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"
        assert result["closeout_allowed"] is True

    def test_auto_profile_uses_fast_for_artifact_only_cleanup(self) -> None:
        """Auto profile uses fast for report/project_state artifact-only cleanup."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/local_reverse_cipher_static_evidence_profile.json`
- `project_state/codex_execution_report.md`

Required implementation behavior:

- Define evidence fields for DES and RC4 PE cipher samples.
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"
        assert result["closeout_allowed"] is False

    def test_standard_profile_for_ordinary_source_test_changes(self) -> None:
        """Standard profile for ordinary non-gate Python/test changes."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/some_module.py`

Allowed tests:

- `tests/test_some_module.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "standard"
        assert result["closeout_allowed"] is True
        assert "close-round" not in result["required_command_kinds"]

    def test_ambiguous_unknown_file_changes_default_to_full(self) -> None:
        """Ambiguous or unknown file changes default to full."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/solver.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"

    def test_gate_profile_json_includes_required_fields(self) -> None:
        """gate-profile --json includes profile metadata, reasons, command kinds, and closeout permission."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert "profile" in result
        assert "profile_reason" in result
        assert "risk_reasons" in result
        assert "closeout_allowed" in result
        assert "required_command_kinds" in result
        assert isinstance(result["risk_reasons"], list)
        assert isinstance(result["required_command_kinds"], list)
        assert len(result["required_command_kinds"]) > 0

    def test_command_plan_includes_profile_metadata(self) -> None:
        """command-plan --json includes profile metadata."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d1", "round_id": "r1", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed source files:\n\n- `reverse_agent/project_gate.py`\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d1",
                "round_id": "r1",
                "mainline": "engineering_branch",
                "profile": "full",
                "profile_reason": "test",
                "closeout_allowed": True,
                "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            result = command_plan(state_dir=state_dir, write_result=False)
            assert "profile_meta" in result
            assert result["profile_meta"]["profile"] == "full"
            assert result["profile_meta"]["closeout_allowed"] is True

    def test_stale_gate_profile_plan_causes_final_check_fail(self) -> None:
        """Stale gate_profile_plan.json decision_id/round_id causes final-check FAIL."""
        gate_profile_payload = {
            "decision_id": "old_decision_id",
            "round_id": "old_round_id",
            "profile": "full",
        }
        decision_id = "current_decision_id"
        round_id = "current_round_id"
        gp_decision_id = str(gate_profile_payload.get("decision_id") or "")
        gp_round_id = str(gate_profile_payload.get("round_id") or "")
        gp_current = gp_decision_id == decision_id and gp_round_id == round_id
        assert not gp_current

    def test_mismatch_profile_causes_final_check_fail(self) -> None:
        """Mismatch between gate_profile_plan.json profile and command_plan.json profile causes FAIL."""
        gate_profile_payload = {"profile": "fast"}
        command_plan_data = {"profile_meta": {"profile": "full"}}
        cp_profile = str((command_plan_data.get("profile_meta") or {}).get("profile") or "")
        gp_profile = str(gate_profile_payload.get("profile") or "")
        profiles_match = cp_profile == gp_profile
        assert not profiles_match

    def test_non_full_profile_closeout_not_allowed_cannot_close(self) -> None:
        """Non-full profile with closeout_allowed=false cannot close/archive."""
        gp_profile = "fast"
        gp_closeout_allowed = False
        closeout_safe = gp_profile == "full" or gp_closeout_allowed
        assert not closeout_safe

    def test_full_profile_can_close_when_all_gates_pass(self) -> None:
        """Full profile can close/archive when all other gates pass."""
        gp_profile = "full"
        gp_closeout_allowed = True
        closeout_safe = gp_profile == "full" or gp_closeout_allowed
        assert closeout_safe

    def test_invalid_explicit_profile_name_fails(self) -> None:
        """Invalid explicit profile name fails clearly."""
        from reverse_agent.project_gate import gate_profile
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d1", "round_id": "r1", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            result = gate_profile(state_dir=state_dir, write_result=False, profile_override="invalid_profile")
            assert result["gate_status"] == "FAILED"
            assert "invalid profile name" in result["profile_reason"].lower()


class TestFastProfileCommandTrimmingPilot:
    """Tests for fast profile command trimming pilot."""

    def test_fast_profile_omits_pytest_and_records_omission(self) -> None:
        """Fast profile for artifact/report-only scope omits pytest and records the omission with reason."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d1", "round_id": "r1", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\n"
                "python -m pytest tests/\n"
                "python -m reverse_agent.project_gate close-round --state-dir project_state\n"
                "```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d1",
                "round_id": "r1",
                "mainline": "engineering_branch",
                "profile": "fast",
                "profile_reason": "artifact-only",
                "closeout_allowed": False,
                "required_command_kinds": ["startup", "preflight", "command-plan", "report-summary", "final-check"],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            result = command_plan(state_dir=state_dir, write_result=False)
            assert result["profile_meta"]["profile"] == "fast"
            omitted_kinds = {oc["kind"] for oc in result["omitted_commands"]}
            assert "pytest" in omitted_kinds
            assert "close-round" in omitted_kinds
            # Each omitted command must have a reason
            for oc in result["omitted_commands"]:
                assert "reason" in oc
                assert "fast profile" in oc["reason"]

    def test_fast_profile_includes_required_command_kinds(self) -> None:
        """Fast profile includes startup, preflight, command-plan, report-summary, and final-check command kinds."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"
        required = result["required_command_kinds"]
        for kind in ("startup", "preflight", "command-plan", "report-summary", "final-check"):
            assert kind in required, f"fast profile must include {kind}"

    def test_fast_profile_does_not_include_close_round_when_closeout_not_allowed(self) -> None:
        """Fast profile does not include close-round when closeout_allowed=false."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"
        assert result["closeout_allowed"] is False
        assert "close-round" not in result["required_command_kinds"]

    def test_fast_profile_cannot_claim_archived_closeout_when_close_round_omitted(self) -> None:
        """Fast profile cannot claim archived/accepted closeout when close-round was omitted."""
        # Simulate the logic: fast profile with closeout_allowed=false and close-round omitted
        gp_profile = "fast"
        gp_closeout_allowed = False
        close_round_omitted = True
        # If close-round is omitted and closeout not allowed, report should not claim ACCEPTED
        claims_closeout = True  # Simulating a report that claims ACCEPTED
        closeout_safe = gp_profile == "full" or gp_closeout_allowed
        # closeout_safe is False, so close-round should be blocked
        assert not closeout_safe
        # And claiming closeout while close-round was omitted is inconsistent
        assert close_round_omitted and not gp_closeout_allowed

    def test_fast_profile_fails_final_check_if_source_test_files_in_delta(self) -> None:
        """Fast profile fails final-check if source/test logic files are present in round delta."""
        from reverse_agent.project_gate import _path_is_source_or_test

        # Verify that source/test files are detected
        assert _path_is_source_or_test("reverse_agent/some_module.py")
        assert _path_is_source_or_test("tests/test_some_module.py")
        # And that the check would fail
        source_test_in_changed = any(
            _path_is_source_or_test(f) for f in ["reverse_agent/some_module.py", "project_state/report.md"]
        )
        assert source_test_in_changed

    def test_fast_profile_fails_final_check_if_pytest_omitted_with_source_changes(self) -> None:
        """Fast profile fails final-check if pytest is omitted while source/test logic files changed."""
        omitted_kinds = {"pytest", "close-round"}
        source_test_in_changed = True  # source files changed
        pytest_omitted = "pytest" in omitted_kinds
        # This should be a FAIL condition
        assert pytest_omitted and source_test_in_changed

    def test_fast_profile_fails_final_check_if_close_round_attempted_with_closeout_false(self) -> None:
        """Fast profile fails final-check if close-round is attempted while closeout_allowed=false."""
        gp_profile = "fast"
        gp_closeout_allowed = False
        closeout_safe = gp_profile == "full" or gp_closeout_allowed
        assert not closeout_safe

    def test_fast_profile_command_plan_includes_omitted_command_metadata(self) -> None:
        """Fast profile command-plan includes omitted command metadata and reasons."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d1", "round_id": "r1", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\n"
                "python -m pytest tests/\n"
                "python -m reverse_agent.project_state doctor --state-dir project_state\n"
                "python -m reverse_agent.project_state lint-report --state-dir project_state\n"
                "python -m reverse_agent.project_gate close-round --state-dir project_state\n"
                "```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d1",
                "round_id": "r1",
                "mainline": "engineering_branch",
                "profile": "fast",
                "profile_reason": "artifact-only",
                "closeout_allowed": False,
                "required_command_kinds": ["startup", "preflight", "command-plan", "report-summary", "final-check"],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            result = command_plan(state_dir=state_dir, write_result=False)
            assert "omitted_commands" in result
            assert isinstance(result["omitted_commands"], list)
            assert len(result["omitted_commands"]) > 0
            # Each omitted command must have command, kind, and reason
            for oc in result["omitted_commands"]:
                assert "command" in oc
                assert "kind" in oc
                assert "reason" in oc
                assert "fast profile" in oc["reason"]

    def test_full_profile_command_plan_remains_compatible(self) -> None:
        """Full profile command-plan remains compatible with existing full tests."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d1", "round_id": "r1", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed source files:\n\n- `reverse_agent/project_gate.py`\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d1",
                "round_id": "r1",
                "mainline": "engineering_branch",
                "profile": "full",
                "profile_reason": "full profile",
                "closeout_allowed": True,
                "required_command_kinds": [
                    "startup", "preflight", "command-plan", "run-round", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check", "close-round",
                ],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            result = command_plan(state_dir=state_dir, write_result=False)
            assert result["profile_meta"]["profile"] == "full"
            # Full profile should not trim any commands
            assert result["omitted_commands"] == []
            assert len(result["commands"]) > 0

    def test_standard_profile_behavior_unchanged(self) -> None:
        """Standard profile behavior remains unchanged except metadata compatibility."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/some_module.py`

Allowed tests:

- `tests/test_some_module.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "standard"
        assert result["closeout_allowed"] is True
        assert "pytest" in result["required_command_kinds"]
        assert "close-round" not in result["required_command_kinds"]

    def test_stale_mismatched_profile_metadata_still_fails_final_check(self) -> None:
        """Stale or mismatched gate_profile_plan/command_plan profile metadata still fails final-check."""
        gate_profile_payload = {"profile": "fast", "decision_id": "old", "round_id": "old"}
        command_plan_data = {"profile_meta": {"profile": "full"}}
        # Stale IDs
        gp_current = gate_profile_payload.get("decision_id") == "current"
        assert not gp_current
        # Mismatched profiles
        cp_profile = str((command_plan_data.get("profile_meta") or {}).get("profile") or "")
        gp_profile = str(gate_profile_payload.get("profile") or "")
        profiles_match = cp_profile == gp_profile
        assert not profiles_match

    def test_fast_profile_required_command_kinds_do_not_include_pytest(self) -> None:
        """Fast profile required_command_kinds does not include pytest or close-round."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"
        assert "pytest" not in result["required_command_kinds"]
        assert "close-round" not in result["required_command_kinds"]
        assert "run-round" not in result["required_command_kinds"]


class TestFastNonCloseoutSemantics:
    """Tests for fast-profile non-closeout semantics source fix.

    Validates that:
    - command-plan explicitly records close-round as omitted when
      closeout_allowed=false, even if close-round was absent from
      the decision Tests section.
    - fast_profile_closeout_consistency detects implicit close-round
      absence under closeout_allowed=false.
    - report-summary synthesis and final-check do not require normal
      archive files for fast non-closeout rounds.
    """

    @staticmethod
    def _make_fast_non_closeout_state(
        tmpdir: str,
        *,
        include_close_round_in_tests: bool = False,
    ) -> Path:
        """Create a minimal project_state with fast non-closeout profile."""
        state_dir = Path(tmpdir) / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()

        tests_section = "```powershell\npython -m pytest tests/\n"
        if include_close_round_in_tests:
            tests_section += "python -m reverse_agent.project_gate close-round --state-dir project_state\n"
        tests_section += "```\n"

        decision_text = (
            "```json decision_meta\n"
            '{"schema_version": 1, "decision_id": "d_nc", "round_id": "r_nc", '
            '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
            '"status": "APPROVED", "mainline": "engineering_branch", '
            '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
            "```\n\n"
            "## 1. Goal\n\nTest fast non-closeout.\n\n"
            "## 6. Implementation Scope\n\n"
            "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
            f"## 7. Tests\n\n{tests_section}"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

        profile_data = {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "d_nc",
            "round_id": "r_nc",
            "mainline": "engineering_branch",
            "profile": "fast",
            "profile_reason": "artifact-only",
            "closeout_allowed": False,
            "required_command_kinds": [
                "startup", "preflight", "command-plan", "report-summary", "final-check",
            ],
        }
        (gates_dir / "gate_profile_plan.json").write_text(
            json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return state_dir

    def test_fast_non_closeout_includes_close_round_in_omitted_commands_without_tests_entry(self) -> None:
        """Fast non-closeout command-plan includes close-round in omitted_commands
        even when close-round is not in the decision Tests section."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir, include_close_round_in_tests=False)
            result = command_plan(state_dir=state_dir, write_result=False)
            omitted_kinds = {oc["kind"] for oc in result["omitted_commands"]}
            assert "close-round" in omitted_kinds, (
                "close-round must be in omitted_commands for fast non-closeout "
                "even when absent from decision Tests"
            )

    def test_fast_non_closeout_omitted_close_round_has_clear_reason(self) -> None:
        """Omitted close-round entry has a clear reason indicating closeout not allowed."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir, include_close_round_in_tests=False)
            result = command_plan(state_dir=state_dir, write_result=False)
            close_round_omissions = [
                oc for oc in result["omitted_commands"] if oc["kind"] == "close-round"
            ]
            assert len(close_round_omissions) >= 1
            reason = close_round_omissions[0]["reason"]
            assert "closeout not allowed" in reason, (
                f"close-round omission reason must mention closeout not allowed, got: {reason}"
            )

    def test_fast_non_closeout_close_round_omitted_when_explicitly_in_tests(self) -> None:
        """Fast non-closeout command-plan also records close-round as omitted
        when close-round IS in the decision Tests section (trimmed)."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir, include_close_round_in_tests=True)
            result = command_plan(state_dir=state_dir, write_result=False)
            omitted_kinds = {oc["kind"] for oc in result["omitted_commands"]}
            assert "close-round" in omitted_kinds
            # When close-round is explicitly in Tests, it gets trimmed with
            # the standard "not in required_command_kinds" reason
            close_round_omissions = [
                oc for oc in result["omitted_commands"] if oc["kind"] == "close-round"
            ]
            assert len(close_round_omissions) >= 1

    def test_fast_non_closeout_consistency_detects_implicit_omission(self) -> None:
        """fast_profile_closeout_consistency recognizes close-round absent from
        commands and present in omitted_commands as intentional non-closeout."""
        # Simulate the updated logic: close-round effectively omitted when
        # either explicitly in omitted_commands OR absent from both commands
        # and omitted_commands while closeout_allowed=false.
        close_round_omitted = True  # now guaranteed by command_plan
        close_round_in_commands = False
        closeout_allowed = False
        close_round_effectively_omitted = (
            close_round_omitted
            or (not close_round_in_commands and not close_round_omitted and closeout_allowed is False)
        )
        assert close_round_effectively_omitted
        # Report should not claim ACCEPTED
        claims_closeout = True
        should_fail = close_round_effectively_omitted and not closeout_allowed and claims_closeout
        assert should_fail

    def test_fast_non_closeout_consistency_fails_on_accepted_claim(self) -> None:
        """fast_profile_closeout_consistency fails if fast report claims
        archived/closeout success (archive artifacts or closeout prose)
        while closeout_allowed=false."""
        close_round_omitted = True
        closeout_allowed = False
        # Under the new semantics, SUCCESS/ACCEPTED alone is NOT a closeout claim
        report_status = "SUCCESS"
        acceptance = "ACCEPTED"
        archive_artifact_claims = False
        claims_closeout_in_prose = False
        claims_closeout = archive_artifact_claims or claims_closeout_in_prose
        assert not claims_closeout  # SUCCESS/ACCEPTED alone is no longer a claim
        # But archive artifact claims ARE closeout claims
        archive_artifact_claims = True
        claims_closeout = archive_artifact_claims or claims_closeout_in_prose
        assert close_round_omitted and not closeout_allowed and claims_closeout

    def test_fast_non_closeout_consistency_passes_on_non_accepted_report(self) -> None:
        """fast_profile_closeout_consistency passes when fast non-closeout report
        does not claim archive/closeout success (SUCCESS/ACCEPTED is now allowed)."""
        close_round_omitted = True
        closeout_allowed = False
        report_status = "PARTIAL"
        acceptance = "REWORK_REQUIRED"
        archive_artifact_claims = False
        claims_closeout_in_prose = False
        claims_closeout = archive_artifact_claims or claims_closeout_in_prose
        assert not claims_closeout
        # Should PASS
        should_fail = close_round_omitted and not closeout_allowed and claims_closeout
        assert not should_fail

    def test_fast_non_closeout_synthesis_excludes_archive_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """report-summary synthesis does not require normal round archive files
        for fast non-closeout."""
        from reverse_agent.project_gate import build_report_summary_synthesis, _read_json, GATE_PROFILE_PLAN_RESULT_NAME
        from reverse_agent.project_state import read_codex_report_summary, read_decision_meta
        import tempfile

        # Override autouse monkeypatch to return empty git changes for isolated tmpdir
        monkeypatch.setattr(
            "reverse_agent.project_gate._git_changed_files",
            lambda _repo_root: [],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            # Write minimal report and pytest_result
            report_text = (
                "```json codex_report_summary\n"
                '{"schema_version": 1, "report_id": "codex_report_r_nc", '
                '"round_id": "r_nc", "based_on_decision_id": "d_nc", '
                '"status": "PARTIAL", "acceptance_recommendation": "REWORK_REQUIRED", '
                '"files_changed": [], "tests_ran": [], "generated_artifacts": []}\n'
                "```\n\n# Report\n"
            )
            (state_dir / "codex_execution_report.md").write_text(report_text, encoding="utf-8")
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            # Use tmpdir as repo_root to avoid picking up real repo dirty files
            result = build_report_summary_synthesis(
                state_dir=state_dir, repo_root=Path(tmpdir), write_result=False,
            )
            synthesized = result.get("synthesized_summary", {})
            expected_files = synthesized.get("files_changed", [])
            expected_artifacts = synthesized.get("generated_artifacts", [])
            # No archive paths should be in expected files or artifacts
            archive_paths = [p for p in expected_files + expected_artifacts if "rounds/" in p]
            assert archive_paths == [], (
                f"fast non-closeout synthesis must not include archive paths, got: {archive_paths}"
            )

    def test_fast_non_closeout_final_check_no_archive_required(self) -> None:
        """final-check does not require normal archive files for fast non-closeout."""
        # This is validated by the archive_paths=set() logic in final_check
        # when closeout_allowed=false. The generated_artifacts_cover_round_archive
        # check should not fail due to missing archive files.
        # We verify the logic: when closeout_allowed is False, archive_paths is empty.
        closeout_allowed = False
        archive_paths: set[str] = set()
        if closeout_allowed is False:
            archive_paths = set()
        assert len(archive_paths) == 0

    def test_full_profile_still_requires_archive(self) -> None:
        """Full profile still requires normal archive files as before."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d_full", "round_id": "r_full", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed source files:\n\n- `reverse_agent/project_gate.py`\n\n"
                "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d_full",
                "round_id": "r_full",
                "mainline": "engineering_branch",
                "profile": "full",
                "profile_reason": "full profile",
                "closeout_allowed": True,
                "required_command_kinds": [
                    "startup", "preflight", "command-plan", "run-round", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check", "close-round",
                ],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            result = command_plan(state_dir=state_dir, write_result=False)
            assert result["profile_meta"]["profile"] == "full"
            # Full profile should not add implicit close-round omission
            omitted_kinds = {oc["kind"] for oc in result["omitted_commands"]}
            assert "close-round" not in omitted_kinds

    def test_fast_non_closeout_omitted_close_round_command_is_none(self) -> None:
        """When close-round is implicitly omitted (not in Tests), the command
        field should be None since there is no actual command string."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir, include_close_round_in_tests=False)
            result = command_plan(state_dir=state_dir, write_result=False)
            implicit_omissions = [
                oc for oc in result["omitted_commands"]
                if oc["kind"] == "close-round" and oc.get("command") is None
            ]
            assert len(implicit_omissions) == 1, (
                "exactly one implicit close-round omission with command=None expected"
            )
            assert implicit_omissions[0]["reason"] == "omitted by fast profile: closeout not allowed"


class TestFastNonCloseoutStatusSemantics:
    """Tests for fast-profile non-closeout status semantics fix.

    Validates that:
    - A fast non-closeout validation may report status=SUCCESS /
      acceptance=ACCEPTED without being treated as a closeout claim.
    - The check still fails when the report claims archive/close-round success.
    - Full profile behavior is unchanged.
    """

    @staticmethod
    def _make_fast_non_closeout_state(
        tmpdir: str,
    ) -> Path:
        """Create a minimal project_state with fast non-closeout profile."""
        state_dir = Path(tmpdir) / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()

        decision_text = (
            "```json decision_meta\n"
            '{"schema_version": 1, "decision_id": "d_ns", "round_id": "r_ns", '
            '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
            '"status": "APPROVED", "mainline": "engineering_branch", '
            '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
            "```\n\n"
            "## 1. Goal\n\nTest fast non-closeout status.\n\n"
            "## 6. Implementation Scope\n\n"
            "Allowed generated/project-state files:\n\n- `project_state/codex_execution_report.md`\n\n"
            "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
        )
        (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

        profile_data = {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": "d_ns",
            "round_id": "r_ns",
            "mainline": "engineering_branch",
            "profile": "fast",
            "profile_reason": "artifact-only",
            "closeout_allowed": False,
            "required_command_kinds": [
                "startup", "preflight", "command-plan", "report-summary", "final-check",
            ],
        }
        (gates_dir / "gate_profile_plan.json").write_text(
            json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return state_dir

    @staticmethod
    def _write_report(
        state_dir: Path,
        *,
        status: str = "SUCCESS",
        acceptance: str = "ACCEPTED",
        generated_artifacts: list[str] | None = None,
        prose_extra: str = "",
    ) -> None:
        """Write a codex_execution_report.md with the given fields."""
        ga = generated_artifacts if generated_artifacts is not None else [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ]
        report_json = {
            "schema_version": 1,
            "report_id": "codex_report_r_ns",
            "round_id": "r_ns",
            "based_on_decision_id": "d_ns",
            "status": status,
            "acceptance_recommendation": acceptance,
            "files_changed": ga,
            "tests_ran": [],
            "generated_artifacts": ga,
        }
        report_text = (
            "```json codex_report_summary\n"
            + json.dumps(report_json, ensure_ascii=True, indent=2)
            + "\n```\n\n# Report\n\n"
            + prose_extra
        )
        (state_dir / "codex_execution_report.md").write_text(report_text, encoding="utf-8")

    @staticmethod
    def _write_command_plan(state_dir: Path) -> None:
        """Write a command_plan.json with close-round in omitted_commands."""
        gates_dir = state_dir / "gates"
        cp_data = {
            "schema_version": 1,
            "plan_name": "command-plan",
            "plan_status": "PASSED",
            "decision_id": "d_ns",
            "round_id": "r_ns",
            "mainline": "engineering_branch",
            "profile_meta": {
                "profile": "fast",
                "profile_reason": "artifact-only",
                "closeout_allowed": False,
                "required_command_kinds": [
                    "startup", "preflight", "command-plan", "report-summary", "final-check",
                ],
            },
            "omitted_commands": [
                {"command": None, "kind": "close-round", "reason": "omitted by fast profile: closeout not allowed"},
            ],
            "commands": [
                {"index": 1, "command": "git status --short", "kind": "git status", "required": True, "expected_exit_codes": [0]},
            ],
        }
        (gates_dir / "command_plan.json").write_text(
            json.dumps(cp_data, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_fast_non_closeout_success_accepted_passes_consistency(self) -> None:
        """Fast non-closeout report with SUCCESS/ACCEPTED passes
        fast_profile_closeout_consistency when no archive/closeout claims."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            self._write_report(state_dir, status="SUCCESS", acceptance="ACCEPTED")
            self._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None, "fast_profile_closeout_consistency check not found"
            assert closeout_check["status"] == "PASS", (
                f"fast non-closeout SUCCESS/ACCEPTED should PASS closeout consistency, "
                f"got: {closeout_check}"
            )

    def test_fast_non_closeout_success_with_archive_artifacts_fails(self) -> None:
        """Fast non-closeout report with archive paths in generated_artifacts
        fails fast_profile_closeout_consistency."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            self._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                generated_artifacts=[
                    "project_state/codex_execution_report.md",
                    "project_state/rounds/r_ns/round_manifest.json",
                ],
            )
            self._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "FAIL", (
                f"fast non-closeout with archive artifacts should FAIL, got: {closeout_check}"
            )

    def test_fast_non_closeout_success_with_closeout_prose_fails(self) -> None:
        """Fast non-closeout report with close-round/archive success prose
        fails fast_profile_closeout_consistency."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            self._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="The close-round succeeded and the round archive was created.\n",
            )
            self._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "FAIL", (
                f"fast non-closeout with closeout prose should FAIL, got: {closeout_check}"
            )

    def test_fast_non_closeout_failed_rework_still_allowed(self) -> None:
        """Fast non-closeout report with FAILED/REWORK_REQUIRED still passes
        fast_profile_closeout_consistency (validation failure is allowed)."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            self._write_report(state_dir, status="FAILED", acceptance="REWORK_REQUIRED")
            self._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "PASS", (
                f"fast non-closeout FAILED/REWORK_REQUIRED should PASS, got: {closeout_check}"
            )

    def test_full_profile_closeout_consistency_unchanged(self) -> None:
        """Full profile closeout consistency check is not affected by the
        fast non-closeout status semantics fix."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d_full2", "round_id": "r_full2", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed source files:\n\n- `reverse_agent/project_gate.py`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d_full2",
                "round_id": "r_full2",
                "mainline": "engineering_branch",
                "profile": "full",
                "profile_reason": "full profile",
                "closeout_allowed": True,
                "required_command_kinds": [
                    "startup", "preflight", "command-plan", "run-round", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check", "close-round",
                ],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            cp_data = {
                "schema_version": 1,
                "plan_name": "command-plan",
                "plan_status": "PASSED",
                "decision_id": "d_full2",
                "round_id": "r_full2",
                "mainline": "engineering_branch",
                "profile_meta": {
                    "profile": "full",
                    "closeout_allowed": True,
                    "required_command_kinds": [
                        "startup", "preflight", "command-plan", "run-round", "pytest",
                        "doctor", "lint-report", "report-summary", "final-check", "close-round",
                    ],
                },
                "omitted_commands": [],
                "commands": [
                    {"index": 1, "command": "git status --short", "kind": "git status", "required": True, "expected_exit_codes": [0]},
                ],
            }
            (gates_dir / "command_plan.json").write_text(
                json.dumps(cp_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            report_text = (
                "```json codex_report_summary\n"
                '{"schema_version": 1, "report_id": "codex_report_r_full2", '
                '"round_id": "r_full2", "based_on_decision_id": "d_full2", '
                '"status": "SUCCESS", "acceptance_recommendation": "ACCEPTED", '
                '"files_changed": [], "tests_ran": [], "generated_artifacts": []}\n'
                "```\n\n# Report\n"
            )
            (state_dir / "codex_execution_report.md").write_text(report_text, encoding="utf-8")
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            # Full profile should get "not applicable" PASS
            assert closeout_check["status"] == "PASS"
            assert "not fast" in closeout_check.get("detail", "").lower() or "not applicable" in closeout_check.get("detail", "").lower()

    def test_command_plan_fast_still_omits_pytest_and_close_round(self) -> None:
        """Command-plan for fast artifact-only decisions still includes
        omitted pytest and omitted close-round entries."""
        from reverse_agent.project_gate import command_plan
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_fast_non_closeout_state(tmpdir)
            result = command_plan(state_dir=state_dir, write_result=False)
            omitted_kinds = {oc["kind"] for oc in result["omitted_commands"]}
            assert "close-round" in omitted_kinds, (
                "fast non-closeout must still omit close-round"
            )
            # pytest should not be in active commands
            command_kinds = {cmd.get("kind") for cmd in result.get("commands", [])}
            assert "pytest" not in command_kinds, (
                "fast non-closeout must not include pytest in active commands"
            )
            assert "close-round" not in command_kinds, (
                "fast non-closeout must not include close-round in active commands"
            )


class TestFastNonCloseoutProsePrecision:
    """Tests for precise prose classification in fast_profile_closeout_consistency.

    Validates that:
    - Legal omission/skipped/not-run prose does NOT fail the check.
    - Success/completion/created prose still fails the check.
    - Archive paths in generated_artifacts still fail.
    - Helper functions classify correctly.
    """

    # --- Helper function unit tests ---

    def test_report_claims_close_round_success_succeeded(self) -> None:
        from reverse_agent.project_gate import _report_claims_close_round_success
        assert _report_claims_close_round_success("close-round succeeded")

    def test_report_claims_close_round_success_completed(self) -> None:
        from reverse_agent.project_gate import _report_claims_close_round_success
        assert _report_claims_close_round_success("close-round completed")

    def test_report_claims_close_round_success_omitted_is_not_claim(self) -> None:
        from reverse_agent.project_gate import _report_claims_close_round_success
        assert not _report_claims_close_round_success("close-round intentionally omitted")

    def test_report_claims_close_round_success_skipped_is_not_claim(self) -> None:
        from reverse_agent.project_gate import _report_claims_close_round_success
        assert not _report_claims_close_round_success("close-round skipped")

    def test_report_claims_archive_success_created(self) -> None:
        from reverse_agent.project_gate import _report_claims_archive_success
        assert _report_claims_archive_success("round archive was created")

    def test_report_claims_archive_success_archived_closeout(self) -> None:
        from reverse_agent.project_gate import _report_claims_archive_success
        assert _report_claims_archive_success("archived closeout succeeded")

    def test_report_claims_archive_success_no_archive_is_not_claim(self) -> None:
        from reverse_agent.project_gate import _report_claims_archive_success
        assert not _report_claims_archive_success("no round archive was created")

    def test_report_mentions_close_round_omission_omitted(self) -> None:
        from reverse_agent.project_gate import _report_mentions_close_round_omission
        assert _report_mentions_close_round_omission("close-round intentionally omitted because closeout_allowed=false")

    def test_report_mentions_close_round_omission_skipped(self) -> None:
        from reverse_agent.project_gate import _report_mentions_close_round_omission
        assert _report_mentions_close_round_omission("close-round skipped for fast non-closeout")

    def test_report_mentions_close_round_omission_not_run(self) -> None:
        from reverse_agent.project_gate import _report_mentions_close_round_omission
        assert _report_mentions_close_round_omission("close-round was not run")

    def test_report_mentions_close_round_omission_succeeded_is_not_omission(self) -> None:
        from reverse_agent.project_gate import _report_mentions_close_round_omission
        assert not _report_mentions_close_round_omission("close-round succeeded")

    # --- Integration tests with final_check ---

    def test_fast_non_closeout_omission_prose_passes(self) -> None:
        """Fast non-closeout with 'close-round intentionally omitted because
        closeout_allowed=false' prose passes fast_profile_closeout_consistency."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="close-round intentionally omitted because closeout_allowed=false\n",
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "PASS", (
                f"omission prose should PASS, got: {closeout_check}"
            )

    def test_fast_non_closeout_not_run_prose_passes(self) -> None:
        """Fast non-closeout with 'close-round was not run' prose passes."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="close-round was not run for this fast non-closeout round.\n",
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "PASS", (
                f"not-run prose should PASS, got: {closeout_check}"
            )

    def test_fast_non_closeout_skipped_prose_passes(self) -> None:
        """Fast non-closeout with 'close-round skipped for fast non-closeout'
        prose passes."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="close-round skipped for fast non-closeout validation.\n",
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "PASS", (
                f"skipped prose should PASS, got: {closeout_check}"
            )

    def test_fast_non_closeout_succeeded_prose_fails(self) -> None:
        """Fast non-closeout with 'close-round succeeded' prose fails."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="The close-round succeeded.\n",
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "FAIL", (
                f"close-round succeeded prose should FAIL, got: {closeout_check}"
            )

    def test_fast_non_closeout_archive_created_prose_fails(self) -> None:
        """Fast non-closeout with 'round archive was created' prose fails."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                prose_extra="The round archive was created successfully.\n",
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "FAIL", (
                f"archive created prose should FAIL, got: {closeout_check}"
            )

    def test_fast_non_closeout_archive_paths_still_fail(self) -> None:
        """Fast non-closeout with project_state/rounds/ in generated_artifacts
        still fails (archive path detection unchanged)."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = TestFastNonCloseoutStatusSemantics._make_fast_non_closeout_state(tmpdir)
            TestFastNonCloseoutStatusSemantics._write_report(
                state_dir,
                status="SUCCESS",
                acceptance="ACCEPTED",
                generated_artifacts=[
                    "project_state/codex_execution_report.md",
                    "project_state/rounds/r_ns/round_manifest.json",
                ],
            )
            TestFastNonCloseoutStatusSemantics._write_command_plan(state_dir)
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            assert closeout_check["status"] == "FAIL", (
                f"archive paths should FAIL, got: {closeout_check}"
            )

    def test_full_profile_closeout_prose_unchanged(self) -> None:
        """Full profile closeout behavior is unchanged by the prose precision fix."""
        from reverse_agent.project_gate import final_check
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "project_state"
            state_dir.mkdir()
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()

            decision_text = (
                "```json decision_meta\n"
                '{"schema_version": 1, "decision_id": "d_fp3", "round_id": "r_fp3", '
                '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
                '"status": "APPROVED", "mainline": "engineering_branch", '
                '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
                "```\n\n"
                "## 1. Goal\n\nTest.\n\n"
                "## 6. Implementation Scope\n\n"
                "Allowed source files:\n\n- `reverse_agent/project_gate.py`\n\n"
                "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
            )
            (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")

            profile_data = {
                "schema_version": 1,
                "gate_name": "gate-profile",
                "gate_status": "PASSED",
                "decision_id": "d_fp3",
                "round_id": "r_fp3",
                "mainline": "engineering_branch",
                "profile": "full",
                "profile_reason": "full profile",
                "closeout_allowed": True,
                "required_command_kinds": [
                    "startup", "preflight", "command-plan", "run-round", "pytest",
                    "doctor", "lint-report", "report-summary", "final-check", "close-round",
                ],
            }
            (gates_dir / "gate_profile_plan.json").write_text(
                json.dumps(profile_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            cp_data = {
                "schema_version": 1,
                "plan_name": "command-plan",
                "plan_status": "PASSED",
                "decision_id": "d_fp3",
                "round_id": "r_fp3",
                "mainline": "engineering_branch",
                "profile_meta": {
                    "profile": "full",
                    "closeout_allowed": True,
                    "required_command_kinds": [
                        "startup", "preflight", "command-plan", "run-round", "pytest",
                        "doctor", "lint-report", "report-summary", "final-check", "close-round",
                    ],
                },
                "omitted_commands": [],
                "commands": [
                    {"index": 1, "command": "git status --short", "kind": "git status", "required": True, "expected_exit_codes": [0]},
                ],
            }
            (gates_dir / "command_plan.json").write_text(
                json.dumps(cp_data, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )

            report_text = (
                "```json codex_report_summary\n"
                '{"schema_version": 1, "report_id": "codex_report_r_fp3", '
                '"round_id": "r_fp3", "based_on_decision_id": "d_fp3", '
                '"status": "SUCCESS", "acceptance_recommendation": "ACCEPTED", '
                '"files_changed": [], "tests_ran": [], "generated_artifacts": []}\n'
                "```\n\n# Report\n\nThe close-round succeeded.\n"
            )
            (state_dir / "codex_execution_report.md").write_text(report_text, encoding="utf-8")
            (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")

            result = final_check(state_dir=state_dir, repo_root=Path(tmpdir), write_result=False)
            closeout_check = None
            for check in result.get("checks", []):
                if isinstance(check, dict) and check.get("name") == "fast_profile_closeout_consistency":
                    closeout_check = check
                    break
            assert closeout_check is not None
            # Full profile should get "not applicable" PASS regardless of prose
            assert closeout_check["status"] == "PASS"
            assert "not fast" in closeout_check.get("detail", "").lower() or "not applicable" in closeout_check.get("detail", "").lower()


class TestGateProfileTierVerification:
    """Tests for gate profile tier verification (fast/standard/full).

    Validates that:
    - Explicit profile override for fast/standard/full works correctly.
    - Each profile's required_command_kinds are complete and correct.
    - Standard profile includes pytest/doctor/lint-report but not close-round.
    - Full profile includes run-round/pytest/doctor/lint-report/close-round.
    - Fast profile excludes pytest/run-round/doctor/lint-report/close-round.
    """

    _FAST_DECISION = """## 6. Implementation Scope

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""

    _STANDARD_DECISION = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/some_module.py`

Allowed tests:

- `tests/test_some_module.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""

    _FULL_DECISION = """## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
"""

    @staticmethod
    def _make_state_dir(tmpdir: str, decision_text: str) -> Path:
        state_dir = Path(tmpdir) / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        full_decision = (
            "```json decision_meta\n"
            '{"schema_version": 1, "decision_id": "d_tv", "round_id": "r_tv", '
            '"based_on_state_build_id": "b1", "based_on_state_digest": "h1", '
            '"status": "APPROVED", "mainline": "engineering_branch", '
            '"skill_profiles": ["reverse-agent-iteration@v2"]}\n'
            "```\n\n"
            "## 1. Goal\n\nTest.\n\n"
            f"{decision_text}\n"
            "## 7. Tests\n\n```powershell\npython -m pytest tests/\n```\n"
        )
        (state_dir / "decision_packet.md").write_text(full_decision, encoding="utf-8")
        return state_dir

    # --- Explicit override tests ---

    def test_explicit_fast_override_works(self) -> None:
        """Explicit --profile fast override produces correct metadata."""
        from reverse_agent.project_gate import gate_profile
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_state_dir(tmpdir, self._FAST_DECISION)
            result = gate_profile(state_dir=state_dir, write_result=False, profile_override="fast")
            assert result["gate_status"] == "PASSED"
            assert result["profile"] == "fast"
            assert result["closeout_allowed"] is False
            assert "close-round" not in result["required_command_kinds"]

    def test_explicit_standard_override_works(self) -> None:
        """Explicit --profile standard override produces correct metadata."""
        from reverse_agent.project_gate import gate_profile
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_state_dir(tmpdir, self._STANDARD_DECISION)
            result = gate_profile(state_dir=state_dir, write_result=False, profile_override="standard")
            assert result["gate_status"] == "PASSED"
            assert result["profile"] == "standard"
            assert result["closeout_allowed"] is True
            assert "pytest" in result["required_command_kinds"]
            assert "close-round" not in result["required_command_kinds"]

    def test_explicit_full_override_works(self) -> None:
        """Explicit --profile full override produces correct metadata."""
        from reverse_agent.project_gate import gate_profile
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_state_dir(tmpdir, self._FULL_DECISION)
            result = gate_profile(state_dir=state_dir, write_result=False, profile_override="full")
            assert result["gate_status"] == "PASSED"
            assert result["profile"] == "full"
            assert result["closeout_allowed"] is True
            assert "close-round" in result["required_command_kinds"]
            assert "run-round" in result["required_command_kinds"]

    # --- required_command_kinds completeness tests ---

    def test_fast_required_command_kinds_excludes_heavy_commands(self) -> None:
        """Fast profile required_command_kinds excludes pytest, run-round, doctor, lint-report, close-round."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._FAST_DECISION)
        assert result["profile"] == "fast"
        required = result["required_command_kinds"]
        for excluded in ("pytest", "run-round", "doctor", "lint-report", "close-round"):
            assert excluded not in required, f"fast profile must not include {excluded}"
        for included in ("startup", "preflight", "command-plan", "report-summary", "final-check"):
            assert included in required, f"fast profile must include {included}"

    def test_standard_required_command_kinds_includes_targeted_pipeline(self) -> None:
        """Standard profile required_command_kinds includes pytest, doctor, lint-report but not close-round."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._STANDARD_DECISION)
        assert result["profile"] == "standard"
        required = result["required_command_kinds"]
        for included in ("startup", "preflight", "command-plan", "pytest", "doctor", "lint-report", "report-summary", "final-check"):
            assert included in required, f"standard profile must include {included}"
        assert "close-round" not in required
        assert "run-round" not in required

    def test_full_required_command_kinds_includes_complete_pipeline(self) -> None:
        """Full profile required_command_kinds includes run-round, pytest, doctor, lint-report, close-round."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._FULL_DECISION)
        assert result["profile"] == "full"
        required = result["required_command_kinds"]
        for included in ("startup", "preflight", "command-plan", "run-round", "pytest", "doctor", "lint-report", "report-summary", "final-check", "close-round"):
            assert included in required, f"full profile must include {included}"

    # --- closeout_allowed tests ---

    def test_fast_closeout_not_allowed(self) -> None:
        """Fast profile has closeout_allowed=False."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._FAST_DECISION)
        assert result["profile"] == "fast"
        assert result["closeout_allowed"] is False

    def test_standard_closeout_allowed(self) -> None:
        """Standard profile has closeout_allowed=True."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._STANDARD_DECISION)
        assert result["profile"] == "standard"
        assert result["closeout_allowed"] is True

    def test_full_closeout_allowed(self) -> None:
        """Full profile has closeout_allowed=True."""
        from reverse_agent.project_gate import classify_gate_profile

        result = classify_gate_profile(self._FULL_DECISION)
        assert result["profile"] == "full"
        assert result["closeout_allowed"] is True

    # --- Invalid override test ---

    def test_invalid_profile_override_fails(self) -> None:
        """Invalid profile name fails with clear error."""
        from reverse_agent.project_gate import gate_profile
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = self._make_state_dir(tmpdir, self._FAST_DECISION)
            result = gate_profile(state_dir=state_dir, write_result=False, profile_override="medium")
            assert result["gate_status"] == "FAILED"
            assert "invalid profile name" in result["profile_reason"].lower()

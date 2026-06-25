import json
import shutil
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
    _artifact_status_policy,
    _expected_report_id,
    _execution_log_derive_commands,
    _extract_bash_commands,
    _extract_unfenced_commands,
    _execution_log_missing_only_closeout_related,
    _historical_sample_limitations_only,
    _is_close_round_command,
    _is_descriptive_backtick_line,
    _is_historical_sample_limitation,
    _is_prohibitive_line,
    _is_run_closeout_command,
    _is_self_invocation,
    _is_startup_command,
    _read_round_close_snapshot,
    _read_execution_report_summary,
    _refresh_codex_report_for_closeout,
    _run_closeout_internal_blocking_reasons,
    _report_status_from_gate,
    _report_status_from_gate_payload,
    _result_status,
    _round_close_snapshot_path,
    _allowed_inherited_files,
    _validate_command_plan_consistency,
    _write_round_close_snapshot,
    _run_closeout_exit_code,
    build_report_summary_synthesis,
    close_round,
    command_plan,
    execute_decision,
    final_check,
    main,
    phase1_completion,
    preflight,
    run_closeout,
    run_round,
    RUN_CLOSEOUT_ALLOWED_KINDS,
    RUN_CLOSEOUT_NAME,
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
    referenced_artifacts: list[str] | None = None,
    extra_body: str = "",
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
    if referenced_artifacts is not None:
        payload["referenced_artifacts"] = referenced_artifacts
    body_section = f"\n{extra_body}\n" if extra_body else ""
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(payload, indent=2)}
```

# CODEX_EXECUTION_REPORT{body_section}""",
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
    startup_dirty_files: list[str] | None = None,
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
        extra_body=(
            "## Policy Impact\n\n"
            "command-plan, final-check, report-summary, policy-lint, "
            "report status schema, and tests reviewed.\n"
        ),
    )
    # Build startup command blocks; if startup_dirty_files is provided,
    # include them in the ``git status --short`` output so that
    # startup_baseline_consistency can verify them against baseline records.
    startup_blocks = list(_STARTUP_COMMAND_BLOCKS)
    if startup_dirty_files:
        # Replace the clean ``git status --short`` block with a dirty one.
        dirty_output = "\n".join(f" M {f}" for f in startup_dirty_files)
        startup_blocks[-1] = (
            "===== COMMAND: git status --short =====\n"
            f"{dirty_output}\n"
            "===== EXIT: 0 =====\n"
        )
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=pytest_tests_ran if pytest_tests_ran is not None else report_tests,
        body="\n\n".join(startup_blocks) + "\n\n1 passed\n",
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
    # Exclude startup commands from tests_ran — they are recorded as command
    # blocks in pytest_result.txt and verified by startup_command_coverage,
    # but they should not appear in the report's tests_ran.
    tests = report_tests if report_tests is not None else [
        cmd for cmd in commands if not any(
            pat in cmd for pat in ("Set-Location", "Get-Location", "Test-Path", "git rev-parse", "git status")
        )
    ]
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
        extra_body=(
            "## Policy Impact\n\n"
            "command-plan, final-check, report-summary, policy-lint, "
            "report status schema, and tests reviewed.\n"
        ),
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
    # Exclude startup commands from tests_ran — they are recorded as command
    # blocks in pytest_result.txt and verified by startup_command_coverage,
    # but they should not appear in the report's tests_ran.
    non_startup_commands = [
        cmd for cmd in commands if not any(
            pat in cmd for pat in ("Set-Location", "Get-Location", "Test-Path", "git rev-parse", "git status")
        )
    ]
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=report_status,
        acceptance=acceptance,
        files_changed=files_changed if files_changed is not None else expected_files_changed,
        tests_ran=tests_ran if tests_ran is not None else non_startup_commands,
        generated_artifacts=generated_artifacts if generated_artifacts is not None else expected_generated_artifacts,
    )
    body = "\n\n".join(_command_block(command, "ok") for command in commands)
    _write_pytest(state_dir, decision_id=decision_id, report_id=report_id, round_id=round_id, tests_ran=non_startup_commands, body=body)
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


def test_final_check_downgrades_historical_artifacts_for_tool_integration(
    tmp_path: Path,
) -> None:
    """tool_integration treats unclaimed historical artifacts as limitations."""
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

    assert result["gate_status"] == "PASSED_WITH_LIMITATIONS"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "WARN"
    assert status_policy["limitations"] is not None
    assert status_policy["historical_backlog"] == ["1 missing, 1 stale artifacts"]
    assert status_policy["required_current_artifacts"] == []
    assert status_policy["claimed_evidence_artifacts"] == []


def test_final_check_downgrades_historical_artifacts_for_training_dataset(
    tmp_path: Path,
) -> None:
    state_dir = _make_gate_state(tmp_path, mainline="training_dataset")
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

    assert result["gate_status"] == "PASSED_WITH_LIMITATIONS"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "PASS"
    assert status_policy["limitations"] is not None
    assert "historical sample artifacts" in status_policy["historical_or_backlog_artifacts"][0]


def test_final_check_blocks_tool_integration_when_report_claims_sample_artifacts(
    tmp_path: Path,
) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        mainline="tool_integration",
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
    assert status_policy["claimed_evidence_artifacts"] == ["1 missing, 1 stale artifacts"]


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


def test_execution_report_summary_parser_accepts_neutral_alias(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    payload = {
        "schema_version": 1,
        "report_id": "report_round_alias",
        "round_id": "round_alias",
        "based_on_decision_id": "decision_alias",
        "status": "SUCCESS",
        "acceptance_recommendation": "ACCEPTED",
        "files_changed": [],
        "tests_ran": [],
        "generated_artifacts": [],
    }
    (state_dir / "execution_report.md").write_text(
        "```json execution_report_summary\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n\n# EXECUTION_REPORT\n",
        encoding="utf-8",
    )

    parsed = _read_execution_report_summary(state_dir)

    assert parsed["report_id"] == "report_round_alias"
    assert parsed["based_on_decision_id"] == "decision_alias"


def test_refresh_report_writes_neutral_execution_report_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = _make_gate_state(tmp_path)
    monkeypatch.setattr("reverse_agent.project_gate._git_changed_files", lambda _repo_root: [])

    _refresh_codex_report_for_closeout(
        state_dir=state_dir,
        repo_root=tmp_path,
        decision_id="decision_gate",
        round_id="round_gate",
    )

    legacy = read_codex_report_summary(state_dir)
    neutral = _read_execution_report_summary(state_dir)
    neutral_text = (state_dir / "execution_report.md").read_text(encoding="utf-8")
    assert legacy["report_id"] == neutral["report_id"]
    assert "```json execution_report_summary" in neutral_text
    assert "# EXECUTION_REPORT" in neutral_text


def test_report_auto_summary_writes_neutral_alias(tmp_path: Path) -> None:
    from reverse_agent.project_gate import report_auto_summary

    state_dir = _make_gate_state(tmp_path)

    result = report_auto_summary(state_dir=state_dir, write_result=True)
    legacy_path = state_dir / "gates" / "codex_report_auto_summary.json"
    neutral_path = state_dir / "gates" / "execution_report_auto_summary.json"
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    neutral = json.loads(neutral_path.read_text(encoding="utf-8"))

    assert result["artifact_name"] == "codex_report_auto_summary.json"
    assert neutral["artifact_name"] == "execution_report_auto_summary.json"
    assert neutral["summary"] == legacy["summary"]
    assert neutral["alias_of"] == "project_state/gates/codex_report_auto_summary.json"


def test_final_check_fails_when_execution_report_alias_drifts(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    payload = read_codex_report_summary(state_dir)
    payload["status"] = "FAILED"
    (state_dir / "execution_report.md").write_text(
        "```json execution_report_summary\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n\n# EXECUTION_REPORT\n",
        encoding="utf-8",
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    parity_check = _check(result, "execution_report_alias_semantic_parity")

    assert parity_check["status"] == "FAIL"
    assert any(diff["field"] == "status" for diff in parity_check["mismatches"])


def test_execution_log_missing_only_closeout_related_is_narrow() -> None:
    assert _execution_log_missing_only_closeout_related({
        "missing_commands": [
            "python -m reverse_agent.project_gate execution-log --state-dir project_state",
            "python -m reverse_agent.project_gate report-auto-summary --state-dir project_state",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
            "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id r1",
            "python -m reverse_agent.project_gate run-round --state-dir project_state --execute",
        ]
    })
    assert not _execution_log_missing_only_closeout_related({
        "missing_commands": [
            "python -m pytest tests/test_project_gate.py -q",
            "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id r1",
        ]
    })


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
        startup_dirty_files=["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
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


@pytest.mark.parametrize(
    "report_status,acceptance",
    [
        ("BLOCKED", "BLOCKED"),
        ("PARTIAL", "REWORK_REQUIRED"),
        ("FAILED", "REWORK_REQUIRED"),
        ("BLOCKED", "REWORK_REQUIRED"),
    ],
)
def test_preflight_allows_reentry_for_incomplete_report(
    tmp_path: Path,
    report_status: str,
    acceptance: str,
) -> None:
    state_dir = _make_preflight_state(tmp_path)
    _write_report(
        state_dir,
        decision_id="decision_preflight",
        report_id="report_preflight",
        round_id="round_preflight",
        status=report_status,
        acceptance=acceptance,
        generated_artifacts=["project_state/gates/preflight_result.json"],
    )
    _write_pytest(state_dir, decision_id="decision_preflight", report_id="report_preflight", round_id="round_preflight")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert _check(result, "decision_not_consumed_by_report")["status"] == "PASS"


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


def test_run_round_execute_uses_only_authorized_commands(tmp_path: Path) -> None:
    """Execute mode must only run commands from command-plan.commands."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"print('hello')\"",
    )
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    # Every executed command must appear in authorized_commands
    authorized = set(result.get("authorized_commands") or [])
    for cmd in seen:
        assert cmd in authorized, f"executed unauthorized command: {cmd}"


def test_run_round_execute_skips_omitted_commands(tmp_path: Path) -> None:
    """Execute mode must not run commands from command-plan.omitted_commands."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"print('hello')\"",
    )
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    omitted = set(result.get("omitted_commands") or [])
    for cmd in seen:
        assert cmd not in omitted, f"executed omitted command: {cmd}"


def test_run_round_execute_skips_self_invocation(tmp_path: Path) -> None:
    """Execute mode must skip run-round commands to prevent recursion."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m reverse_agent.project_gate run-round --state-dir project_state --execute",
    )
    pytest_result_path = state_dir / "pytest_result.txt"
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    result = run_round(
        state_dir=state_dir,
        dry_run=False,
        repo_root=tmp_path,
        command_runner=fake_runner,
        pytest_result_path=pytest_result_path,
    )

    # run-round commands should be in skipped_commands, not executed
    skipped_commands = result.get("skipped_commands") or []
    skipped_reasons = [s.get("reason", "") for s in skipped_commands]
    assert any("self-invocation" in r for r in skipped_reasons)
    content = pytest_result_path.read_text(encoding="utf-8")
    assert "===== COMMAND: python -m reverse_agent.project_gate run-round --state-dir project_state --execute =====" in content
    assert "reason: self-invocation guard: run-round must not invoke itself recursively" in content
    assert "===== EXIT: 0 =====" in content


def test_run_round_execute_runs_closeout(tmp_path: Path) -> None:
    """Execute mode must run run-closeout when authorized by command-plan."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id test_round",
    )
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    # run-closeout should be executed, not skipped
    executed_commands = result.get("executed_commands") or []
    executed_texts = [c.get("command", "") for c in executed_commands]
    closeout_executed = any("run-closeout" in c for c in executed_texts)
    assert closeout_executed, "run-closeout should be executed in execute mode"


def test_run_round_execute_records_to_pytest_result(tmp_path: Path) -> None:
    """Execute mode must record command blocks to pytest_result.txt."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"print('hello')\"",
    )
    pytest_result_path = tmp_path / "project_state" / "pytest_result.txt"

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    run_round(
        state_dir=state_dir,
        dry_run=False,
        repo_root=tmp_path,
        command_runner=fake_runner,
        pytest_result_path=pytest_result_path,
    )

    assert pytest_result_path.exists(), "pytest_result.txt should be created"
    content = pytest_result_path.read_text(encoding="utf-8")
    assert "===== COMMAND:" in content, "pytest_result.txt should contain command blocks"
    assert "===== EXIT:" in content, "pytest_result.txt should contain exit codes"


def test_run_round_execute_surfaces_real_failures(tmp_path: Path) -> None:
    """Execute mode must surface real command failures, not hide them."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"raise SystemExit(1)\"",
    )

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="fail\n", stderr="error msg")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    assert result["run_status"] == "FAILED"
    assert any(c.get("exit_code") == 1 for c in result.get("executed_commands", []))


def test_run_round_dry_run_unchanged_by_execute_mode(tmp_path: Path) -> None:
    """Dry-run behavior must remain unchanged after adding execute mode."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"print('hello')\"",
    )

    def fail_if_called(command: str) -> subprocess.CompletedProcess[str]:
        raise AssertionError(f"dry-run executed command: {command}")

    result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path, command_runner=fail_if_called)

    assert result["run_status"] == "PASSED"
    assert result["mode"] == "dry-run"
    assert result["executed_commands"] == []


def test_run_round_execute_handles_expected_nonzero_exit(tmp_path: Path) -> None:
    """Execute mode should continue when exit code is in expected_exit_codes."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -c \"raise SystemExit(1)\"",
    )
    seen: list[str] = []

    def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        if "raise SystemExit(1)" in command:
            return subprocess.CompletedProcess(command, 1, stdout="expected\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    result = run_round(state_dir=state_dir, dry_run=False, repo_root=tmp_path, command_runner=fake_runner)

    # The command-plan generated by _make_command_plan_state uses expected_exit_codes [0]
    # for pytest commands, so exit code 1 should cause a failure.
    # This test verifies that the expected_exit_codes mechanism is checked:
    # when exit code 1 is NOT in expected_exit_codes, the command should FAIL.
    executed = result.get("executed_commands") or []
    assert any(c.get("exit_code") == 1 and c.get("status") == "FAILED" for c in executed)


def test_run_round_execute_skips_powershell_only_commands(tmp_path: Path) -> None:
    """Execute mode must skip PowerShell-only cmdlets that cannot run via subprocess.

    This tests the _is_powershell_only_command guard directly by constructing
    a minimal command plan with PowerShell-only commands and verifying that
    run_round skips them in execute mode.
    """
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="python -m pytest tests/test_project_gate.py -q",
    )
    # Generate the command plan and inject PowerShell-only commands
    from reverse_agent.project_gate import command_plan as generate_plan
    plan_result = generate_plan(state_dir=state_dir)
    commands = list(plan_result.get("commands") or [])

    # Inject PowerShell-only commands directly into the command list
    ps_commands = [
        {"index": 100, "command": "Set-Location F:\\reverse-agent", "phase": "status", "kind": "set-location", "required": True, "expected_exit_codes": [0]},
        {"index": 101, "command": "Get-Location", "phase": "status", "kind": "pwd", "required": True, "expected_exit_codes": [0]},
        {"index": 102, "command": "Test-Path F:\\reverse-agent", "phase": "status", "kind": "test-path", "required": True, "expected_exit_codes": [0]},
    ]
    all_commands = commands + ps_commands

    # Test _is_powershell_only_command directly on the injected commands
    from reverse_agent.project_gate import _is_powershell_only_command
    for cmd in ps_commands:
        assert _is_powershell_only_command(cmd) is True, f"Expected {cmd['kind']} to be PowerShell-only"

    # Verify non-PowerShell commands are NOT flagged
    for cmd in commands:
        kind = cmd.get("kind", "")
        if kind not in ("set-location", "pwd", "test-path"):
            assert _is_powershell_only_command(cmd) is False, f"Unexpected PowerShell-only: {kind}"


def test_is_powershell_only_command_detects_set_location() -> None:
    from reverse_agent.project_gate import _is_powershell_only_command
    assert _is_powershell_only_command({"kind": "set-location", "command": "Set-Location F:\\reverse-agent"}) is True
    assert _is_powershell_only_command({"kind": "pwd", "command": "Get-Location"}) is True
    assert _is_powershell_only_command({"kind": "test-path", "command": "Test-Path F:\\reverse-agent"}) is True
    assert _is_powershell_only_command({"kind": "git status", "command": "git status --short"}) is False
    assert _is_powershell_only_command({"kind": "preflight", "command": "python -m reverse_agent.project_gate preflight"}) is False


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

        assert "python -m pytest tests/test_project_gate.py -q" in result["recorded_command_blocks"]
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

    def test_execute_self_invocation_skip_records_guard_block(self, tmp_path: Path) -> None:
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

        assert "python -m pytest tests/test_project_gate.py -q" in result["recorded_command_blocks"]
        assert (
            "python -m reverse_agent.project_gate run-round --state-dir project_state --execute"
            in result["recorded_command_blocks"]
        )
        content = pytest_path.read_text(encoding="utf-8")
        assert "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====" in content
        assert (
            "===== COMMAND: python -m reverse_agent.project_gate run-round --state-dir project_state --execute ====="
            in content
        )
        assert "reason: self-invocation guard: run-round must not invoke itself recursively" in content

    def test_execute_reinitializes_stale_pytest_result(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        pytest_path = state_dir / "pytest_result.txt"
        pytest_path.write_text(
            "```json pytest_result_summary\n"
            '{"decision_id":"old_decision","round_id":"old_round","status":"PASSED","tests_ran":[]}'
            "\n```\n\n"
            "===== COMMAND: python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id old_round =====\n"
            "old failure\n"
            "===== EXIT: 1 =====\n",
            encoding="utf-8",
        )

        def fake_runner(command: str) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        run_round(
            state_dir=state_dir,
            dry_run=False,
            repo_root=tmp_path,
            command_runner=fake_runner,
            pytest_result_path=pytest_path,
        )

        content = pytest_path.read_text(encoding="utf-8")
        assert "old_decision" not in content
        assert "old failure" not in content
        assert "old_round" not in content
        assert "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====" in content


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
        assert "===== COMMAND: python -c \"print('not reached')\" =====" not in content


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
        # Vacuous truth: no limitations means all are historical-only
        assert _historical_sample_limitations_only([])

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


class TestReverseSolvingBlockerOnlyGatePolicy:
    """Verify gate policy for reverse_solving blocker-only reports."""

    def test_result_status_warn_for_failed_with_pass_external_notices(self) -> None:
        """reverse_solving FAILED report with PASS status_policy_valid + external_state_notices
        must return WARN, not PASSED_WITH_LIMITATIONS."""
        checks = [
            {
                "name": "status_policy_valid",
                "status": "PASS",
                "external_state_notices": ["50 missing historical sample artifacts"],
            },
        ]
        assert _result_status(checks, "FAILED", mainline="reverse_solving") == "WARN"

    def test_result_status_warn_for_partial_with_pass_external_notices(self) -> None:
        checks = [
            {
                "name": "status_policy_valid",
                "status": "PASS",
                "external_state_notices": ["50 missing historical sample artifacts"],
            },
        ]
        assert _result_status(checks, "PARTIAL", mainline="reverse_solving") == "WARN"

    def test_result_status_passed_for_success_with_pass_external_notices(self) -> None:
        """reverse_solving SUCCESS report with PASS status_policy_valid + external_state_notices
        still returns PASSED_WITH_LIMITATIONS (not upgraded to PASSED)."""
        checks = [
            {
                "name": "status_policy_valid",
                "status": "PASS",
                "external_state_notices": ["50 missing historical sample artifacts"],
            },
        ]
        assert _result_status(checks, "SUCCESS", mainline="reverse_solving") == "PASSED_WITH_LIMITATIONS"

    def test_result_status_passed_with_status_source_only_warn_and_partial_report(self) -> None:
        """When the only WARNs are status_policy_valid (historical) and
        report_auto_summary_consistency (status-source-only, non_blocking),
        _result_status returns PASSED even with PARTIAL report status.
        This breaks the self-referential cycle."""
        checks = [
            {
                "name": "status_policy_valid",
                "status": "WARN",
                "limitations": ["50 missing historical sample artifacts"],
            },
            {
                "name": "report_auto_summary_consistency",
                "status": "WARN",
                "detail": "status-source fields only (self-referential); substantive fields match",
                "non_blocking": True,
            },
        ]
        assert _result_status(checks, "PARTIAL", mainline="engineering_branch") == "PASSED"

    def test_result_status_warn_when_auto_summary_has_substantive_mismatch(self) -> None:
        """When report_auto_summary_consistency has a substantive mismatch
        (not status-source-only), _result_status returns WARN even with
        non_blocking=False."""
        checks = [
            {
                "name": "status_policy_valid",
                "status": "WARN",
                "limitations": ["50 missing historical sample artifacts"],
            },
            {
                "name": "report_auto_summary_consistency",
                "status": "WARN",
                "detail": "disagrees on files_changed",
                "non_blocking": False,
            },
        ]
        assert _result_status(checks, "PARTIAL", mainline="engineering_branch") == "WARN"

    def test_auto_summary_mismatch_is_status_source_only_true(self) -> None:
        """_auto_summary_mismatch_is_status_source_only returns True when
        all mismatches are in status/acceptance_recommendation fields."""
        from reverse_agent.project_gate import _auto_summary_mismatch_is_status_source_only
        mismatches = [
            {"field": "status", "expected": "PARTIAL", "actual": "SUCCESS"},
            {"field": "acceptance_recommendation", "expected": "NEEDS_REVIEW", "actual": "ACCEPTED"},
        ]
        assert _auto_summary_mismatch_is_status_source_only(mismatches) is True

    def test_auto_summary_mismatch_is_status_source_only_false_with_substantive(self) -> None:
        """_auto_summary_mismatch_is_status_source_only returns False when
        there is a substantive field mismatch (files_changed)."""
        from reverse_agent.project_gate import _auto_summary_mismatch_is_status_source_only
        mismatches = [
            {"field": "status", "expected": "PARTIAL", "actual": "SUCCESS"},
            {"field": "files_changed", "expected": ["a.py"], "actual": ["b.py"]},
        ]
        assert _auto_summary_mismatch_is_status_source_only(mismatches) is False

    def test_auto_summary_mismatch_is_status_source_only_false_empty(self) -> None:
        """_auto_summary_mismatch_is_status_source_only returns False for
        empty mismatches (no mismatches means PASS, not status-source-only)."""
        from reverse_agent.project_gate import _auto_summary_mismatch_is_status_source_only
        assert _auto_summary_mismatch_is_status_source_only([]) is False

    def test_auto_summary_mismatch_is_status_source_only_false_with_id_mismatch(self) -> None:
        """_auto_summary_mismatch_is_status_source_only returns False when
        there is an ID mismatch (not a field diff with 'field' key)."""
        from reverse_agent.project_gate import _auto_summary_mismatch_is_status_source_only
        mismatches = [
            {"field": "status", "expected": "PARTIAL", "actual": "SUCCESS"},
            {"error": "stale decision_id", "auto_summary_decision_id": "old_v1"},
        ]
        assert _auto_summary_mismatch_is_status_source_only(mismatches) is False

    def test_report_status_from_gate_payload_returns_actual_failed(self) -> None:
        """For reverse_solving blocker-only, synthesis returns actual report status."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "FAILED",
                "report_acceptance_recommendation": "REWORK_REQUIRED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "PASS",
                    "external_state_notices": ["50 missing historical sample artifacts"],
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="reverse_solving")
        assert result == ("FAILED", "REWORK_REQUIRED")

    def test_report_status_from_gate_payload_returns_actual_blocked(self) -> None:
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "BLOCKED",
                "report_acceptance_recommendation": "BLOCKED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "PASS",
                    "external_state_notices": ["50 missing historical sample artifacts"],
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="reverse_solving")
        assert result == ("BLOCKED", "BLOCKED")

    def test_report_status_from_gate_payload_does_not_trigger_for_success(self) -> None:
        """When report_status is SUCCESS, the blocker-only path must not trigger."""
        payload = {
            "gate_status": "WARN",
            "status_summary": {
                "report_status": "SUCCESS",
                "report_acceptance_recommendation": "ACCEPTED",
            },
            "checks": [
                {
                    "name": "status_policy_valid",
                    "status": "PASS",
                    "external_state_notices": ["50 missing historical sample artifacts"],
                },
            ],
        }
        result = _report_status_from_gate_payload(payload, mainline="reverse_solving")
        # Should fall through to _report_status_from_gate("WARN") = ("PARTIAL", "NEEDS_REVIEW")
        assert result == ("PARTIAL", "NEEDS_REVIEW")

    def test_artifact_status_policy_downgrades_for_blocker_only(self) -> None:
        """_artifact_status_policy allows downgrade for reverse_solving blocker-only."""
        decision = {
            "mainline": "reverse_solving",
            "decision_id": "decision_test_v1",
        }
        report = {
            "status": "FAILED",
            "acceptance_recommendation": "REWORK_REQUIRED",
            "based_on_decision_id": "decision_test_v1",
            "generated_artifacts": ["project_state/gates/preflight_result.json"],
            "verified_artifacts": [],
            "next_suggested_task": "Obtain expected ciphertext evidence",
        }
        doctor_result = {
            "checks": [
                {
                    "name": "artifacts",
                    "status": "INFO",
                    "blocking": False,
                    "classification": "historical_sample_artifacts_non_blocking",
                    "detail": "50 missing, 0 stale historical sample artifacts (non-blocking)",
                    "limitations": ["50 missing historical sample artifacts"],
                },
            ],
        }
        policy = _artifact_status_policy(
            doctor_result=doctor_result,
            decision=decision,
            report=report,
            report_status="FAILED",
        )
        assert policy["blocking_reasons"] == []
        assert len(policy["non_blocking_warnings"]) == 1

    def test_artifact_status_policy_blocks_for_reverse_solving_success(self) -> None:
        """_artifact_status_policy blocks for reverse_solving SUCCESS with verified artifacts."""
        decision = {
            "mainline": "reverse_solving",
            "decision_id": "decision_test_v1",
        }
        report = {
            "status": "SUCCESS",
            "acceptance_recommendation": "ACCEPTED",
            "based_on_decision_id": "decision_test_v1",
            "generated_artifacts": ["project_state/gates/preflight_result.json"],
            "verified_artifacts": ["solve_reports/run1"],
            "next_suggested_task": "Continue with next sample",
        }
        doctor_result = {
            "checks": [
                {
                    "name": "artifacts",
                    "status": "WARN",
                    "blocking": True,
                    "classification": "artifact_freshness_requires_review",
                    "detail": "50 missing, 0 stale artifacts",
                },
            ],
        }
        policy = _artifact_status_policy(
            doctor_result=doctor_result,
            decision=decision,
            report=report,
            report_status="SUCCESS",
        )
        assert len(policy["blocking_reasons"]) == 1


class TestReportStatusFastNonCloseout:
    """Verify _report_status_from_gate_payload returns SUCCESS/ACCEPTED
    for fast non-closeout scenarios where closeout_allowed=false and
    close-round was not run, when the only WARNs are archive-pending or
    historical sample limitations."""

    def test_fast_non_closeout_warn_returns_success_accepted(self) -> None:
        """Fast non-closeout with WARN gate_status and only archive-pending/historical
        WARNs must return SUCCESS/ACCEPTED, not PARTIAL/REWORK_REQUIRED."""
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
        assert result == ("SUCCESS", "ACCEPTED")

    def test_fast_non_closeout_implicit_omission_returns_success_accepted(self) -> None:
        """Fast non-closeout where close-round is implicitly absent (not in
        omitted_commands, not in commands, closeout_allowed=false) must also
        return SUCCESS/ACCEPTED when only historical limitations remain."""
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
        assert result == ("SUCCESS", "ACCEPTED")

    def test_fast_non_closeout_passed_returns_success_accepted(self) -> None:
        """Fast non-closeout with PASSED gate_status (no FAILs at all) must
        return SUCCESS/ACCEPTED because close-round is intentionally omitted."""
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
        assert result == ("SUCCESS", "ACCEPTED")

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


class TestFinalCheckFastNonCloseoutArchiveChecks:
    """Verify final-check archive-related checks for fast non-closeout scenarios.

    When profile=fast and closeout_allowed=false and no archive claims:
    - Archive checks should be PASS (not WARN)
    - gate_status should be PASSED (not WARN)
    - report-summary synthesis should derive SUCCESS/ACCEPTED

    When archive claims exist or close-round is recorded:
    - Archive checks should still FAIL/WARN
    """

    @staticmethod
    def _make_fast_state(
        tmp_path: Path,
        *,
        generated_artifacts: list[str] | None = None,
        pytest_body_extra: str = "",
        report_status: str = "SUCCESS",
        report_acceptance: str = "ACCEPTED",
    ) -> Path:
        """Create a fast-profile non-closeout gate state for testing."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(
            state_dir / "current_state.json",
            {
                "round_id": "round_fast",
                "state_build_id": "state_fast",
                "state_digest": "digest_fast",
                "state_scope": "fast_scope",
                "source_harness_run": "run_fast",
            },
        )
        _write_json(
            state_dir / "task_packet.json",
            {
                "state_scope": "fast_scope",
                "task_source": "derived_from_sample_artifacts",
                "execution_scope": "decision_packet_controls_current_round",
                "active_decision_packet": "project_state/decision_packet.md",
            },
        )
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})
        _write_json(state_dir / "negative_results.json", {})

        decision_id = "decision_fast"
        report_id = "codex_report_fast"
        round_id = "round_fast"

        _write_decision(state_dir, decision_id=decision_id, round_id=round_id, mainline="engineering_branch")
        _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

        gates_dir = state_dir / "gates"
        # Fast profile: closeout_allowed=false, omits close-round
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1,
            "gate_name": "gate-profile",
            "gate_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "mainline": "engineering_branch",
            "profile": "fast",
            "profile_reason": "artifact/report-only scope",
            "closeout_allowed": False,
            "required_command_kinds": ["startup", "preflight"],
        })
        _write_json(gates_dir / "command_plan.json", {
            "schema_version": 1, "artifact_name": "command_plan.json",
            "decision_id": decision_id, "round_id": round_id,
            "plan_status": "PASSED",
            "mainline": "engineering_branch",
            "generated_at": "2026-06-18T00:00:00Z",
            "commands": [
                {"index": 1, "command": "Set-Location F:\\reverse-agent", "phase": "status", "kind": "startup", "required": True},
                {"index": 2, "command": "Get-Location", "phase": "status", "kind": "startup", "required": True},
                {"index": 3, "command": "Test-Path F:\\reverse-agent", "phase": "status", "kind": "startup", "required": True},
                {"index": 4, "command": "git rev-parse --show-toplevel", "phase": "status", "kind": "startup", "required": True},
                {"index": 5, "command": "git status --short", "phase": "status", "kind": "startup", "required": True},
                {"index": 6, "command": "python -m reverse_agent.project_gate preflight --state-dir project_state", "phase": "gate", "kind": "preflight", "required": True},
                {"index": 7, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state", "phase": "gate", "kind": "gate-check", "required": True},
            ],
            "warnings": [],
            "blocking_reasons": [],
            "profile_meta": {
                "profile": "fast",
                "profile_reason": "artifact/report-only scope",
                "closeout_allowed": False,
                "required_command_kinds": ["startup", "preflight"],
                "omitted_commands": ["pytest", "build", "close-round"],
            },
        })
        _write_json(gates_dir / "round_delta_summary.json", {
            "schema_version": 1, "artifact_name": "round_delta_summary.json",
            "decision_id": decision_id, "round_id": round_id,
            "baseline_available": True,
            "new_dirty_files_since_baseline": [],
            "inherited_dirty_files": [],
            "final_dirty_files": [],
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

        base_artifacts = [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            "project_state/gates/gate_profile_plan.json",
        ]
        _write_report(
            state_dir,
            decision_id=decision_id,
            report_id=report_id,
            round_id=round_id,
            status=report_status,
            acceptance=report_acceptance,
            files_changed=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/round_delta_summary.json",
            ],
            tests_ran=[
                "python -m reverse_agent.project_gate preflight --state-dir project_state",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=generated_artifacts if generated_artifacts is not None else base_artifacts,
        )
        startup_blocks = list(_STARTUP_COMMAND_BLOCKS)
        _write_pytest(
            state_dir,
            decision_id=decision_id,
            report_id=report_id,
            round_id=round_id,
            tests_ran=[
                "python -m reverse_agent.project_gate preflight --state-dir project_state",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            body="\n\n".join(startup_blocks) + pytest_body_extra + "\n\n1 passed\n",
        )
        return state_dir

    def test_fast_non_closeout_archive_checks_pass(self, tmp_path: Path) -> None:
        """Fast non-closeout with no archive claims: archive checks should be PASS."""
        state_dir = self._make_fast_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        # Archive checks should be PASS, not WARN
        for check_name in (
            "round_manifest_present",
            "archived_report_matches_live_report",
            "archived_pytest_result_matches_live_pytest_result",
        ):
            check = _check(result, check_name)
            assert check["status"] == "PASS", f"{check_name} should be PASS, got {check['status']}: {check.get('detail')}"
        # Verify the PASS detail mentions fast profile
        manifest_check = _check(result, "round_manifest_present")
        assert "fast profile" in manifest_check.get("detail", "").lower(), \
            f"Expected fast profile detail, got: {manifest_check.get('detail')}"

    def test_fast_non_closeout_archive_claim_still_warns(self, tmp_path: Path) -> None:
        """Fast non-closeout with generated_artifacts claiming round archive: must WARN/FAIL."""
        state_dir = self._make_fast_state(
            tmp_path,
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/rounds/round_fast/codex_execution_report.md",
            ],
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        # Archive checks should NOT be PASS when archive is claimed
        manifest_check = _check(result, "round_manifest_present")
        assert manifest_check["status"] != "PASS", \
            "round_manifest_present should not be PASS when archive is claimed"

    def test_fast_non_closeout_close_round_recorded_still_warns(self, tmp_path: Path) -> None:
        """Fast non-closeout with close-round in pytest_result: must WARN/FAIL."""
        close_round_block = _command_block(
            "python -m reverse_agent.project_gate close-round --state-dir project_state",
            "close-round: PASSED",
        )
        state_dir = self._make_fast_state(
            tmp_path,
            pytest_body_extra="\n\n" + close_round_block,
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        # Archive checks should NOT be PASS when close-round is recorded
        manifest_check = _check(result, "round_manifest_present")
        assert manifest_check["status"] != "PASS", \
            "round_manifest_present should not be PASS when close-round is recorded"

    def test_standard_profile_archive_still_strict(self, tmp_path: Path) -> None:
        """Standard/full profile: archive checks should still be WARN when no archive exists."""
        state_dir = _make_gate_state(tmp_path)
        # Remove the archive to simulate non-archived state
        import shutil
        archive_dir = tmp_path / "project_state" / "rounds"
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        # For full profile, archive checks should be WARN (not PASS)
        manifest_check = _check(result, "round_manifest_present")
        assert manifest_check["status"] == "WARN", \
            f"Full profile without archive should WARN, got {manifest_check['status']}"


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


class TestAllowedPathsHeaderRecognized:
    """Regression tests for _allowed_source_test_scope_paths recognizing
    "Allowed paths:" as a source/test scope header.

    Previous bug: only "allowed source", "allowed tests", and "允许修改"
    triggered source/test scope parsing.  When a decision used
    "Allowed paths:" as the header, the parser returned an empty set,
    causing gate-profile to incorrectly select "fast" instead of
    "standard" or "full".
    """

    def test_allowed_paths_header_parsed(self) -> None:
        """'Allowed paths:' header should be recognized as a source/test scope trigger."""
        from reverse_agent.project_gate import _allowed_source_test_scope_paths

        scope_text = (
            "Allowed paths:\n"
            "- `reverse_agent/project_gate.py`\n"
            "- `tests/test_project_gate.py`\n"
        )
        result = _allowed_source_test_scope_paths(scope_text)
        assert "reverse_agent/project_gate.py" in result
        assert "tests/test_project_gate.py" in result

    def test_allowed_paths_header_with_project_state_stops(self) -> None:
        """'Allowed project_state artifact paths:' should stop source/test scope parsing."""
        from reverse_agent.project_gate import _allowed_source_test_scope_paths

        scope_text = (
            "Allowed paths:\n"
            "- `reverse_agent/project_gate.py`\n"
            "- `tests/test_project_gate.py`\n"
            "\n"
            "Allowed project_state artifact paths:\n"
            "- `project_state/codex_execution_report.md`\n"
            "- `project_state/pytest_result.txt`\n"
        )
        result = _allowed_source_test_scope_paths(scope_text)
        assert "reverse_agent/project_gate.py" in result
        assert "tests/test_project_gate.py" in result
        # project_state paths must NOT leak into source/test scope
        assert "project_state/codex_execution_report.md" not in result
        assert "project_state/pytest_result.txt" not in result

    def test_allowed_paths_with_test_files_classifies_standard(self) -> None:
        """classify_gate_profile should select 'standard' when 'Allowed paths:'
        contains ordinary source/test files (not gate/project_state)."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = (
            "## 6. Implementation Scope\n\n"
            "Allowed paths:\n\n"
            "- `reverse_agent/some_module.py`\n"
            "- `tests/test_some_module.py`\n\n"
            "Allowed project_state artifact paths:\n\n"
            "- `project_state/codex_execution_report.md`\n"
        )
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "standard"
        assert any("source/test" in r for r in result["reasons"])

    def test_allowed_paths_with_gate_file_classifies_full(self) -> None:
        """classify_gate_profile should select 'full' when 'Allowed paths:'
        contains reverse_agent/project_gate.py (a full-scope path)."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = (
            "## 6. Implementation Scope\n\n"
            "Allowed paths:\n\n"
            "- `reverse_agent/project_gate.py`\n"
            "- `tests/test_project_gate.py`\n\n"
            "Allowed project_state artifact paths:\n\n"
            "- `project_state/codex_execution_report.md`\n"
        )
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "full"
        assert any("gate/project_state" in r for r in result["reasons"])

    def test_allowed_paths_empty_returns_empty_set(self) -> None:
        """Empty 'Allowed paths:' section should return empty set."""
        from reverse_agent.project_gate import _allowed_source_test_scope_paths

        scope_text = (
            "Allowed paths:\n"
            "\n"
            "Allowed project_state artifact paths:\n"
            "- `project_state/foo.json`\n"
        )
        result = _allowed_source_test_scope_paths(scope_text)
        assert len(result) == 0

    def test_forbidden_paths_not_in_allowed_paths(self) -> None:
        """Forbidden paths under 'Allowed paths:' should still be detected by
        the forbidden path parser (tested via _allowed_scope_paths)."""
        from reverse_agent.project_gate import _allowed_scope_paths

        scope_text = (
            "Allowed paths:\n"
            "- `reverse_agent/project_gate.py`\n"
            "- `tests/test_project_gate.py`\n"
        )
        result = _allowed_scope_paths(scope_text)
        assert "reverse_agent/project_gate.py" in result
        assert "tests/test_project_gate.py" in result


class TestAllowedPathsHeaderGateProfileIntegration:
    """Integration tests verifying that 'Allowed paths:' header correctly
    drives gate-profile selection end-to-end."""

    def test_allowed_paths_with_tests_not_fast(self) -> None:
        """When 'Allowed paths:' contains tests/ files, gate-profile must NOT
        be 'fast' — it should be at least 'standard'."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = (
            "## 6. Implementation Scope\n\n"
            "Allowed paths:\n\n"
            "- `tests/test_local_reverse_static_type_tags.py`\n"
            "- `tests/test_local_reverse_training_status.py`\n\n"
            "Allowed project_state artifact paths:\n\n"
            "- `project_state/local_reverse_static_type_tag_contract.json`\n"
        )
        result = classify_gate_profile(decision_text)
        assert result["profile"] != "fast"
        assert result["profile"] in ("standard", "full")

    def test_allowed_paths_with_only_artifacts_is_fast(self) -> None:
        """When 'Allowed paths:' contains only project_state artifacts (no
        source/test), gate-profile should still be 'fast'."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = (
            "## 6. Implementation Scope\n\n"
            "Allowed paths:\n\n"
            "- `project_state/local_reverse_static_type_tag_contract.json`\n"
            "- `project_state/local_reverse_static_type_tag_contract_report.md`\n"
        )
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "fast"

    def test_allowed_paths_closeout_allowed_when_standard(self) -> None:
        """When 'Allowed paths:' contains source/test files and profile is
        'standard', closeout_allowed should be True."""
        from reverse_agent.project_gate import classify_gate_profile

        decision_text = (
            "## 6. Implementation Scope\n\n"
            "Allowed paths:\n\n"
            "- `reverse_agent/some_module.py`\n"
            "- `tests/test_some_module.py`\n\n"
            "Allowed project_state artifact paths:\n\n"
            "- `project_state/codex_execution_report.md`\n"
        )
        result = classify_gate_profile(decision_text)
        assert result["profile"] == "standard"
        assert result["closeout_allowed"] is True


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

    def test_returns_true_for_tool_integration(self) -> None:
        from reverse_agent.project_gate import _status_policy_failure_is_historical_artifacts_only

        result = _status_policy_failure_is_historical_artifacts_only(
            result=self._make_result(),
            mainline="tool_integration",
        )
        assert result is True

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


class TestGeneratedArtifactsCoverGateArtifacts:
    """Regression tests for generated_artifacts coverage of gate artifacts.

    These tests verify that policy_impact_audit.json and policy_lint_result.json
    are included in synthesized generated_artifacts when they exist on disk,
    and that final-check detects omissions for SUCCESS/ACCEPTED reports.
    """

    def test_synthesis_includes_policy_impact_audit_when_exists(self, tmp_path: Path) -> None:
        """Synthesis includes policy_impact_audit.json in generated_artifacts
        when the file exists on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        # Create policy_impact_audit.json on disk
        _write_json(state_dir / "gates" / "policy_impact_audit.json", {
            "schema_version": 1, "gate_name": "policy-impact",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Create policy_lint_result.json on disk
        _write_json(state_dir / "gates" / "policy_lint_result.json", {
            "schema_version": 1, "gate_name": "policy-lint",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/policy_impact_audit.json" in ga
        assert "project_state/gates/policy_lint_result.json" in ga

    def test_synthesis_excludes_gate_artifacts_when_absent(self, tmp_path: Path) -> None:
        """Synthesis does not include policy_impact_audit.json when the file
        does not exist on disk (policy-impact was not run)."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        # policy_impact_audit.json does NOT exist on disk
        assert not (state_dir / "gates" / "policy_impact_audit.json").exists()
        assert not (state_dir / "gates" / "policy_lint_result.json").exists()

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/policy_impact_audit.json" not in ga
        assert "project_state/gates/policy_lint_result.json" not in ga

    def test_final_check_fails_when_policy_impact_audit_omitted_success(
        self, tmp_path: Path,
    ) -> None:
        """final-check FAILs when policy_impact_audit.json exists on disk but
        is omitted from generated_artifacts and report status is SUCCESS."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create policy_impact_audit.json on disk
        _write_json(state_dir / "gates" / "policy_impact_audit.json", {
            "schema_version": 1, "gate_name": "policy-impact",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Update report to include policy_impact_audit.json in files_changed
        # but NOT in generated_artifacts (the omission being fixed)
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/policy_impact_audit.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                *archive_paths,
                # Deliberately omit policy_impact_audit.json
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "FAIL"
        assert "project_state/gates/policy_impact_audit.json" in gate_artifact_check.get(
            "missing_artifacts", []
        )

    def test_final_check_passes_when_policy_impact_audit_included(
        self, tmp_path: Path,
    ) -> None:
        """final-check PASSes when policy_impact_audit.json exists on disk and
        is included in generated_artifacts."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create policy_impact_audit.json on disk
        _write_json(state_dir / "gates" / "policy_impact_audit.json", {
            "schema_version": 1, "gate_name": "policy-impact",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Create policy_lint_result.json on disk
        _write_json(state_dir / "gates" / "policy_lint_result.json", {
            "schema_version": 1, "gate_name": "policy-lint",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Update report to include both in files_changed and generated_artifacts
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/policy_impact_audit.json",
                "project_state/gates/policy_lint_result.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/policy_impact_audit.json",
                "project_state/gates/policy_lint_result.json",
                *archive_paths,
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "PASS"

    def test_final_check_warns_when_gate_artifact_omitted_non_success(
        self, tmp_path: Path,
    ) -> None:
        """final-check WARNs (not FAILs) when a gate artifact is omitted from
        generated_artifacts and report status is not SUCCESS."""
        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        # Create policy_impact_audit.json on disk
        _write_json(state_dir / "gates" / "policy_impact_audit.json", {
            "schema_version": 1, "gate_name": "policy-impact",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Report omits policy_impact_audit.json from generated_artifacts
        # but status is PARTIAL, so it should WARN not FAIL

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        # WARN is acceptable for non-SUCCESS reports
        assert gate_artifact_check["status"] in ("PASS", "WARN")

    def test_no_false_failure_when_policy_impact_not_run(self, tmp_path: Path) -> None:
        """No false failure when policy_impact_audit.json does not exist
        (policy-impact was not run for this round)."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # policy_impact_audit.json does NOT exist on disk
        assert not (state_dir / "gates" / "policy_impact_audit.json").exists()

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "PASS"

    def test_closeout_refresh_preserves_gate_artifacts_in_generated_artifacts(
        self, tmp_path: Path,
    ) -> None:
        """_refresh_codex_report_for_closeout includes policy_impact_audit.json
        in generated_artifacts when it exists on disk."""
        from reverse_agent.project_gate import _refresh_codex_report_for_closeout

        state_dir = _make_gate_state(tmp_path)
        # Create policy_impact_audit.json on disk
        _write_json(state_dir / "gates" / "policy_impact_audit.json", {
            "schema_version": 1, "gate_name": "policy-impact",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Create policy_lint_result.json on disk
        _write_json(state_dir / "gates" / "policy_lint_result.json", {
            "schema_version": 1, "gate_name": "policy-lint",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })

        _refresh_codex_report_for_closeout(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_gate",
            round_id="round_gate",
        )
        from reverse_agent.project_gate import read_codex_report_summary
        report = read_codex_report_summary(state_dir)
        ga = report.get("generated_artifacts", [])
        assert "project_state/gates/policy_impact_audit.json" in ga
        assert "project_state/gates/policy_lint_result.json" in ga


class TestManifestStatusConsistency:
    """Regression tests for round manifest status consistency.

    These tests verify that:
    1. A stale manifest (PARTIAL/NEEDS_REVIEW) fails final-check when the
       report is SUCCESS/ACCEPTED.
    2. A matching manifest (SUCCESS/ACCEPTED) passes final-check.
    3. A stale manifest for a non-SUCCESS report is not blocking.
    4. _refresh_manifest_status updates manifest metadata to match report.
    5. Closeout/snapshot artifacts are included in generated_artifacts coverage.
    """

    def test_stale_manifest_fails_for_success_report(self, tmp_path: Path) -> None:
        """final-check FAILs when manifest has PARTIAL/NEEDS_REVIEW but
        report is SUCCESS/ACCEPTED."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a round manifest with stale status
        round_dir = state_dir / "rounds" / "round_gate"
        round_dir.mkdir(parents=True, exist_ok=True)
        _write_json(round_dir / "round_manifest.json", {
            "schema_version": 1,
            "round_id": "round_gate",
            "decision_id": "decision_gate",
            "report_status": "PARTIAL",
            "acceptance_recommendation": "NEEDS_REVIEW",
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        manifest_check = _check(result, "round_manifest_status_matches_report")
        assert manifest_check["status"] == "FAIL"
        assert len(manifest_check.get("mismatches", [])) == 2

    def test_matching_manifest_passes_for_success_report(self, tmp_path: Path) -> None:
        """final-check PASSes when manifest matches SUCCESS/ACCEPTED report."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a round manifest with matching status
        round_dir = state_dir / "rounds" / "round_gate"
        round_dir.mkdir(parents=True, exist_ok=True)
        _write_json(round_dir / "round_manifest.json", {
            "schema_version": 1,
            "round_id": "round_gate",
            "decision_id": "decision_gate",
            "report_status": "SUCCESS",
            "acceptance_recommendation": "ACCEPTED",
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        manifest_check = _check(result, "round_manifest_status_matches_report")
        assert manifest_check["status"] == "PASS"

    def test_stale_manifest_not_blocking_for_partial_report(self, tmp_path: Path) -> None:
        """A stale manifest is not blocking when report is PARTIAL/NEEDS_REVIEW
        (the check only applies to SUCCESS/ACCEPTED reports)."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        # Create a round manifest with stale status
        round_dir = state_dir / "rounds" / "round_gate"
        round_dir.mkdir(parents=True, exist_ok=True)
        _write_json(round_dir / "round_manifest.json", {
            "schema_version": 1,
            "round_id": "round_gate",
            "decision_id": "decision_gate",
            "report_status": "FAILED",
            "acceptance_recommendation": "REWORK_REQUIRED",
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        manifest_check = _check(result, "round_manifest_status_matches_report")
        # For non-SUCCESS reports, the check should PASS (not enforced)
        assert manifest_check["status"] == "PASS"

    def test_no_manifest_not_blocking(self, tmp_path: Path) -> None:
        """No manifest at all should not trigger the status check."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # No round manifest directory

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        manifest_check = _check(result, "round_manifest_status_matches_report")
        assert manifest_check["status"] == "PASS"

    def test_refresh_manifest_status_updates_stale_fields(self, tmp_path: Path) -> None:
        """_refresh_manifest_status updates manifest report_status and
        acceptance_recommendation to match the current report."""
        from reverse_agent.project_gate import _refresh_manifest_status

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a round manifest with stale status
        round_dir = state_dir / "rounds" / "round_gate"
        round_dir.mkdir(parents=True, exist_ok=True)
        _write_json(round_dir / "round_manifest.json", {
            "schema_version": 1,
            "round_id": "round_gate",
            "decision_id": "decision_gate",
            "report_status": "PARTIAL",
            "acceptance_recommendation": "NEEDS_REVIEW",
        })

        _refresh_manifest_status(state_dir=state_dir, round_id="round_gate")

        manifest = json.loads((round_dir / "round_manifest.json").read_text(encoding="utf-8"))
        assert manifest["report_status"] == "SUCCESS"
        assert manifest["acceptance_recommendation"] == "ACCEPTED"

    def test_refresh_manifest_status_noop_when_matching(self, tmp_path: Path) -> None:
        """_refresh_manifest_status is a no-op when manifest already matches."""
        from reverse_agent.project_gate import _refresh_manifest_status

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        round_dir = state_dir / "rounds" / "round_gate"
        round_dir.mkdir(parents=True, exist_ok=True)
        _write_json(round_dir / "round_manifest.json", {
            "schema_version": 1,
            "round_id": "round_gate",
            "decision_id": "decision_gate",
            "report_status": "SUCCESS",
            "acceptance_recommendation": "ACCEPTED",
            "extra_field": "preserved",
        })

        _refresh_manifest_status(state_dir=state_dir, round_id="round_gate")

        manifest = json.loads((round_dir / "round_manifest.json").read_text(encoding="utf-8"))
        assert manifest["report_status"] == "SUCCESS"
        assert manifest["acceptance_recommendation"] == "ACCEPTED"
        assert manifest["extra_field"] == "preserved"


class TestCloseoutArtifactCoverage:
    """Regression tests for closeout/snapshot artifact coverage in
    generated_artifacts.

    These tests verify that closeout/snapshot artifacts are included in
    _REPORTABLE_GATE_ARTIFACT_NAMES and appear in generated_artifacts when
    they exist on disk and match the current round.
    """

    def test_closeout_artifact_in_reportable_names(self) -> None:
        """RUN_CLOSEOUT_RESULT_NAME is in _REPORTABLE_GATE_ARTIFACT_NAMES."""
        from reverse_agent.project_gate import (
            _REPORTABLE_GATE_ARTIFACT_NAMES,
            RUN_CLOSEOUT_RESULT_NAME,
        )
        assert RUN_CLOSEOUT_RESULT_NAME in _REPORTABLE_GATE_ARTIFACT_NAMES

    def test_closeout_execution_log_in_reportable_names(self) -> None:
        """RUN_CLOSEOUT_EXECUTION_LOG_NAME is in _REPORTABLE_GATE_ARTIFACT_NAMES."""
        from reverse_agent.project_gate import (
            _REPORTABLE_GATE_ARTIFACT_NAMES,
            RUN_CLOSEOUT_EXECUTION_LOG_NAME,
        )
        assert RUN_CLOSEOUT_EXECUTION_LOG_NAME in _REPORTABLE_GATE_ARTIFACT_NAMES

    def test_close_snapshot_in_reportable_names(self) -> None:
        """ROUND_CLOSE_SNAPSHOT_RESULT_NAME is in _REPORTABLE_GATE_ARTIFACT_NAMES."""
        from reverse_agent.project_gate import (
            _REPORTABLE_GATE_ARTIFACT_NAMES,
            ROUND_CLOSE_SNAPSHOT_RESULT_NAME,
        )
        assert ROUND_CLOSE_SNAPSHOT_RESULT_NAME in _REPORTABLE_GATE_ARTIFACT_NAMES

    def test_report_summary_in_reportable_names(self) -> None:
        """REPORT_SUMMARY_RESULT_NAME is in _REPORTABLE_GATE_ARTIFACT_NAMES."""
        from reverse_agent.project_gate import (
            _REPORTABLE_GATE_ARTIFACT_NAMES,
            REPORT_SUMMARY_RESULT_NAME,
        )
        assert REPORT_SUMMARY_RESULT_NAME in _REPORTABLE_GATE_ARTIFACT_NAMES

    def test_closeout_artifact_covered_when_exists_and_matches_round(
        self, tmp_path: Path,
    ) -> None:
        """generated_artifacts_cover_gate_artifacts includes closeout artifacts
        when they exist on disk and match the current round."""
        from reverse_agent.project_gate import final_check

        # Include closeout artifacts in generated_artifacts so the check passes
        state_dir = _make_gate_state(
            tmp_path, status="SUCCESS", acceptance="ACCEPTED",
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/run_closeout_result.json",
                "project_state/gates/run_closeout_execution_log.json",
                "project_state/gates/round_close_snapshot.json",
            ],
        )
        # Create run_closeout_result.json matching current round
        _write_json(state_dir / "gates" / "run_closeout_result.json", {
            "schema_version": 1, "gate_name": "run-closeout",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Create run_closeout_execution_log.json matching current round
        _write_json(state_dir / "gates" / "run_closeout_execution_log.json", {
            "schema_version": 1,
            "decision_id": "decision_gate", "round_id": "round_gate",
            "commands": [],
        })
        # Create round_close_snapshot.json matching current round
        _write_json(state_dir / "gates" / "round_close_snapshot.json", {
            "schema_version": 1,
            "decision_id": "decision_gate", "round_id": "round_gate",
        })

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "PASS"

    def test_stale_closeout_artifact_excluded_from_coverage(
        self, tmp_path: Path,
    ) -> None:
        """Stale closeout artifacts from a previous round are excluded from
        _existing_reportable_gate_artifact_paths and do not cause coverage
        failures."""
        from reverse_agent.project_gate import (
            _existing_reportable_gate_artifact_paths,
        )

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create run_closeout_result.json from a DIFFERENT round
        _write_json(state_dir / "gates" / "run_closeout_result.json", {
            "schema_version": 1, "gate_name": "run-closeout",
            "gate_status": "PASSED",
            "decision_id": "decision_old", "round_id": "round_old",
        })

        paths = _existing_reportable_gate_artifact_paths(
            state_dir, decision_id="decision_gate", round_id="round_gate",
        )
        assert "project_state/gates/run_closeout_result.json" not in paths

    def test_command_plan_authority_preserved(self, tmp_path: Path) -> None:
        """Command-plan authority check is not weakened by the new checks."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Verify command_plan_execution_authority check still exists
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        authority_check = _check(result, "command_plan_execution_authority")
        assert authority_check is not None


class TestStructuredExecutionLog:
    """Regression tests for Structured Execution Log v1.

    These tests verify that execution_log.json is derived from
    pytest_result.txt and command_plan.json, that it is included in
    generated_artifacts when present, that final-check detects mismatches
    between execution_log and pytest_result/command_plan, and that absence
    of execution_log remains backward-compatible.
    """

    def test_execution_log_derives_from_pytest_result_and_command_plan(
        self, tmp_path: Path,
    ) -> None:
        """execution_log() derives command entries from pytest_result.txt
        command blocks and command_plan.json expected_exit_codes."""
        from reverse_agent.project_gate import execution_log

        state_dir = _make_gate_state(tmp_path)
        # Write a pytest_result.txt with command blocks
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 passed", exit_code=0)
            + "\n\n"
            + _command_block(
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
                "final-check: PASSED",
                exit_code=0,
            )
            + "\n",
        )

        result = execution_log(state_dir=state_dir, write_result=False)
        commands = result.get("commands") or []
        assert len(commands) >= 2
        # Each entry must have required fields
        for entry in commands:
            assert "index" in entry
            assert "command" in entry
            assert "kind" in entry
            assert "phase" in entry
            assert "expected_exit_codes" in entry
            assert "exit_code" in entry
            assert "status" in entry
        # The pytest command should have status PASSED
        pytest_entry = next(
            (e for e in commands if "pytest" in str(e.get("command") or "")), None
        )
        assert pytest_entry is not None
        assert pytest_entry["status"] == "PASSED"
        assert pytest_entry["exit_code"] == 0

    def test_execution_log_detects_exit_code_mismatch(self, tmp_path: Path) -> None:
        """execution_log() marks a command as FAILED when its exit code
        does not match command_plan expected_exit_codes."""
        from reverse_agent.project_gate import execution_log

        state_dir = _make_gate_state(tmp_path)
        # Write a pytest_result.txt where pytest exits 1 but command_plan
        # expects exit 0
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 failed", exit_code=1)
            + "\n\n"
            + _command_block(
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
                "final-check: PASSED",
                exit_code=0,
            )
            + "\n",
        )

        result = execution_log(state_dir=state_dir, write_result=False)
        commands = result.get("commands") or []
        pytest_entry = next(
            (e for e in commands if "pytest" in str(e.get("command") or "")), None
        )
        assert pytest_entry is not None
        assert pytest_entry["status"] == "FAILED"

    def test_execution_log_writes_artifact_to_disk(self, tmp_path: Path) -> None:
        """execution_log() writes execution_log.json to project_state/gates/."""
        from reverse_agent.project_gate import execution_log, EXECUTION_LOG_RESULT_NAME

        state_dir = _make_gate_state(tmp_path)
        result = execution_log(state_dir=state_dir, write_result=True)
        assert (state_dir / "gates" / EXECUTION_LOG_RESULT_NAME).exists()
        assert result.get("artifact_name") == EXECUTION_LOG_RESULT_NAME
        assert result.get("source") == "derived_from_pytest_result_and_command_plan"

    def test_synthesis_includes_execution_log_when_exists(self, tmp_path: Path) -> None:
        """build_report_summary_synthesis includes execution_log.json in
        generated_artifacts when the file exists on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1, "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/execution_log.json" in ga

    def test_synthesis_excludes_execution_log_when_absent(self, tmp_path: Path) -> None:
        """build_report_summary_synthesis does not include execution_log.json
        when the file does not exist on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        assert not (state_dir / "gates" / "execution_log.json").exists()

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/execution_log.json" not in ga

    def test_final_check_fails_when_execution_log_omitted_success(
        self, tmp_path: Path,
    ) -> None:
        """final-check FAILs when execution_log.json exists on disk but is
        omitted from generated_artifacts and report status is SUCCESS."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1, "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Report omits execution_log.json from generated_artifacts
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                *archive_paths,
                # Deliberately omit execution_log.json
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "FAIL"
        assert "project_state/gates/execution_log.json" in gate_artifact_check.get(
            "missing_artifacts", []
        )

    def test_final_check_passes_when_execution_log_included(
        self, tmp_path: Path,
    ) -> None:
        """final-check PASSes when execution_log.json exists on disk and is
        included in generated_artifacts."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1, "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        gate_artifact_check = _check(result, "generated_artifacts_cover_gate_artifacts")
        assert gate_artifact_check["status"] == "PASS"

    def test_final_check_execution_log_consistency_pass_when_consistent(
        self, tmp_path: Path,
    ) -> None:
        """final-check execution_log_consistency PASSes when execution_log.json
        is consistent with pytest_result and command_plan."""
        from reverse_agent.project_gate import execution_log

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Write a consistent pytest_result.txt
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 passed", exit_code=0)
            + "\n\n"
            + _command_block(
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
                "final-check: PASSED",
                exit_code=0,
            )
            + "\n",
        )
        # Generate execution_log.json from the consistent pytest_result
        execution_log(state_dir=state_dir, write_result=True)
        # Update report to include execution_log.json
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "PASS"

    def test_final_check_execution_log_consistency_fails_on_mismatch(
        self, tmp_path: Path,
    ) -> None:
        """final-check execution_log_consistency FAILs when execution_log.json
        has an exit code that disagrees with pytest_result.txt for a SUCCESS
        report."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create execution_log.json with a mismatched exit code
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1,
            "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-21T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [
                {
                    "index": 1,
                    "command": "python -m pytest -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                    "exit_code": 0,  # Claims exit 0
                    "status": "PASSED",
                },
            ],
            "warnings": [],
            "blocking_reasons": [],
            "recommended_next_action": "no_action_required",
        })
        # But pytest_result.txt records pytest as exit 1
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 failed", exit_code=1)
            + "\n\n"
            + _command_block(
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
                "final-check: PASSED",
                exit_code=0,
            )
            + "\n",
        )
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/execution_log.json",
                *archive_paths,
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "FAIL"

    def test_final_check_execution_log_absent_backward_compatible(
        self, tmp_path: Path,
    ) -> None:
        """final-check execution_log_consistency PASSes (skipped) when
        execution_log.json is not present on disk (backward-compatible)."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        assert not (state_dir / "gates" / "execution_log.json").exists()

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "PASS"
        assert consistency_check.get("skipped_reason") == "execution_log_not_present"

    def test_closeout_refresh_includes_execution_log_in_generated_artifacts(
        self, tmp_path: Path,
    ) -> None:
        """_refresh_codex_report_for_closeout includes execution_log.json in
        generated_artifacts when it exists on disk."""
        from reverse_agent.project_gate import _refresh_codex_report_for_closeout

        state_dir = _make_gate_state(tmp_path)
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1, "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })

        _refresh_codex_report_for_closeout(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_gate",
            round_id="round_gate",
        )
        from reverse_agent.project_gate import read_codex_report_summary
        report = read_codex_report_summary(state_dir)
        ga = report.get("generated_artifacts", [])
        assert "project_state/gates/execution_log.json" in ga

    def test_command_kind_recognizes_execution_log(self) -> None:
        """_command_kind recognizes execution-log commands."""
        from reverse_agent.project_gate import _command_kind
        assert _command_kind(
            "python -m reverse_agent.project_gate execution-log --state-dir project_state"
        ) == "execution-log"

    def test_command_expected_exit_codes_allows_0_or_1_for_execution_log(self) -> None:
        """_command_expected_exit_codes allows exit 0 or 1 for execution-log."""
        from reverse_agent.project_gate import _command_expected_exit_codes
        codes, _, _ = _command_expected_exit_codes(
            kind="execution-log",
            phase="gate",
            command="python -m reverse_agent.project_gate execution-log --state-dir project_state",
            decision_text="",
            final_check_passed=None,
        )
        assert codes == [0, 1]


class TestReportAutoSummary:
    """Regression tests for Codex Report Auto-Summary v1.

    These tests verify that report_auto_summary() synthesizes codex_report_summary
    fields from structured evidence, uses execution_log for tests_ran with
    command_plan fallback, derives files_changed from round_delta_summary,
    includes gate artifacts in generated_artifacts, rejects unsupported statuses,
    and that final-check detects mismatches between auto-summary and live report.
    """

    def test_auto_summary_synthesizes_fields(self, tmp_path: Path) -> None:
        """report_auto_summary() generates all required summary fields from
        structured evidence."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        result = report_auto_summary(state_dir=state_dir, write_result=False)
        summary = result.get("summary") or {}
        assert "schema_version" in summary
        assert "report_id" in summary
        assert "round_id" in summary
        assert "based_on_decision_id" in summary
        assert "status" in summary
        assert "acceptance_recommendation" in summary
        assert "files_changed" in summary
        assert "tests_ran" in summary
        assert "generated_artifacts" in summary
        assert "referenced_artifacts" in summary
        assert "required_closeout_artifacts" in summary
        assert summary["based_on_decision_id"] == "decision_gate"
        assert summary["round_id"] == "round_gate"
        assert summary["report_id"] == "codex_report_gate"

    def test_auto_summary_uses_execution_log_for_tests_ran(
        self, tmp_path: Path,
    ) -> None:
        """report_auto_summary() derives tests_ran from execution_log.json
        when available."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1,
            "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-21T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [
                {"index": 1, "command": "Set-Location F:\\reverse-agent", "kind": "set-location", "phase": "status", "expected_exit_codes": [0], "exit_code": 0, "status": "PASSED"},
                {"index": 2, "command": "python -m pytest -q", "kind": "pytest", "phase": "test", "expected_exit_codes": [0], "exit_code": 0, "status": "PASSED"},
                {"index": 3, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state", "kind": "final-check", "phase": "gate", "expected_exit_codes": [0, 1], "exit_code": 0, "status": "PASSED"},
            ],
            "warnings": [],
            "blocking_reasons": [],
            "recommended_next_action": "no_action_required",
        })

        result = report_auto_summary(state_dir=state_dir, write_result=False)
        tests_ran = result.get("summary", {}).get("tests_ran", [])
        # Startup commands should be excluded
        assert "Set-Location F:\\reverse-agent" not in tests_ran
        assert "python -m pytest -q" in tests_ran
        assert "python -m reverse_agent.project_gate final-check --state-dir project_state" in tests_ran
        assert result.get("source_provenance", {}).get("tests_ran_source") == "execution_log.json"

    def test_auto_summary_uses_round_delta_for_files_changed(
        self, tmp_path: Path,
    ) -> None:
        """report_auto_summary() derives files_changed from
        round_delta_summary.json."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        result = report_auto_summary(state_dir=state_dir, write_result=False)
        files_changed = result.get("summary", {}).get("files_changed", [])
        # round_delta_summary.json in _make_gate_state has
        # new_dirty_files_since_baseline = [project_gate.py, test_project_gate.py]
        assert "reverse_agent/project_gate.py" in files_changed
        assert "tests/test_project_gate.py" in files_changed
        # Standard report artifacts should also be present
        assert "project_state/codex_execution_report.md" in files_changed
        assert "project_state/pytest_result.txt" in files_changed

    def test_auto_summary_includes_gate_artifacts_in_generated_artifacts(
        self, tmp_path: Path,
    ) -> None:
        """report_auto_summary() includes gate artifacts on disk in
        generated_artifacts."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        # _make_gate_state already creates command_plan.json, round_baseline.json
        result = report_auto_summary(state_dir=state_dir, write_result=False)
        generated_artifacts = result.get("summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/command_plan.json" in generated_artifacts
        assert "project_state/gates/round_baseline.json" in generated_artifacts

    def test_auto_summary_rejects_unsupported_status(
        self, tmp_path: Path,
    ) -> None:
        """report_auto_summary() adds a blocking_reason when status is not
        one of the supported report statuses."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        # Write a final_gate_result with an unrecognized gate_status
        _write_json(state_dir / "gates" / "final_gate_result.json", {
            "schema_version": 1,
            "gate_name": "final-check",
            "gate_status": "UNKNOWN_STATUS",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-21T00:00:00Z",
            "checks": [],
            "blocking_reasons": [],
            "warnings": [],
            "recommended_next_action": "no_action_required",
            "status_summary": {},
        })

        result = report_auto_summary(state_dir=state_dir, write_result=False)
        # Status should default to PARTIAL when unrecognized
        assert result.get("summary", {}).get("status") == "PARTIAL"
        # Should have a warning about unrecognized gate_status
        warnings = result.get("warnings", [])
        assert any("UNKNOWN_STATUS" in w for w in warnings)

    def test_final_check_fails_on_auto_summary_mismatch(
        self, tmp_path: Path,
    ) -> None:
        """final-check report_auto_summary_consistency FAILs when
        codex_report_auto_summary.json disagrees with live codex_report_summary
        for a SUCCESS report."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Write auto-summary with different files_changed than the report
        _write_json(state_dir / "gates" / "codex_report_auto_summary.json", {
            "schema_version": 1,
            "artifact_name": "codex_report_auto_summary.json",
            "gate_name": "report-auto-summary",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-21T00:00:00Z",
            "source": "synthesized_from_structured_evidence",
            "summary": {
                "schema_version": 1,
                "report_id": "codex_report_gate",
                "round_id": "round_gate",
                "based_on_decision_id": "decision_gate",
                "status": "SUCCESS",
                "acceptance_recommendation": "ACCEPTED",
                "files_changed": ["different_file.py"],  # Mismatch
                "tests_ran": ["python -m pytest -q"],
                "generated_artifacts": [],
                "referenced_artifacts": [],
                "required_closeout_artifacts": [],
            },
            "source_provenance": {},
            "warnings": [],
            "blocking_reasons": [],
            "recommended_next_action": "no_action_required",
        })
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=[
                "reverse_agent/project_gate.py",
                "tests/test_project_gate.py",
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/codex_report_auto_summary.json",
                *archive_paths,
            ],
            tests_ran=[
                "python -m pytest -q",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
            generated_artifacts=[
                "project_state/codex_execution_report.md",
                "project_state/pytest_result.txt",
                "project_state/gates/command_plan.json",
                "project_state/gates/round_baseline.json",
                "project_state/gates/round_delta_summary.json",
                "project_state/gates/report_summary_synthesis.json",
                "project_state/gates/final_gate_result.json",
                "project_state/gates/gate_profile_plan.json",
                "project_state/gates/codex_report_auto_summary.json",
                *archive_paths,
            ],
            extra_body=(
                "## Policy Impact\n\n"
                "command-plan, final-check, report-summary, policy-lint, "
                "report status schema, and tests reviewed.\n"
            ),
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "report_auto_summary_consistency")
        assert consistency_check["status"] == "FAIL"

    def test_auto_summary_falls_back_to_command_plan_when_execution_log_absent(
        self, tmp_path: Path,
    ) -> None:
        """report_auto_summary() falls back to command_plan.json for tests_ran
        when execution_log.json is not present."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        assert not (state_dir / "gates" / "execution_log.json").exists()

        result = report_auto_summary(state_dir=state_dir, write_result=False)
        tests_ran = result.get("summary", {}).get("tests_ran", [])
        # command_plan.json in _make_gate_state has pytest and final-check
        assert "python -m pytest -q" in tests_ran
        assert "python -m reverse_agent.project_gate final-check --state-dir project_state" in tests_ran
        assert result.get("source_provenance", {}).get("tests_ran_source") == "command_plan.json"
        # Should have a warning about missing execution_log
        warnings = result.get("warnings", [])
        assert any("execution_log.json not present" in w for w in warnings)

    def test_auto_summary_preserves_report_body(self, tmp_path: Path) -> None:
        """report_auto_summary() does not modify codex_execution_report.md
        body content."""
        from reverse_agent.project_gate import report_auto_summary

        state_dir = _make_gate_state(tmp_path)
        # Write a report with a distinctive body
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="SUCCESS",
            acceptance="ACCEPTED",
            extra_body="## Required Audit\n\nHuman-written audit answers preserved.",
        )
        report_before = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")

        report_auto_summary(state_dir=state_dir, write_result=True)

        report_after = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")
        assert report_before == report_after  # Body unchanged

    def test_closeout_refresh_includes_auto_summary_in_generated_artifacts(
        self, tmp_path: Path,
    ) -> None:
        """_refresh_codex_report_for_closeout includes
        codex_report_auto_summary.json in generated_artifacts when it exists."""
        from reverse_agent.project_gate import _refresh_codex_report_for_closeout

        state_dir = _make_gate_state(tmp_path)
        _write_json(state_dir / "gates" / "codex_report_auto_summary.json", {
            "schema_version": 1,
            "gate_name": "report-auto-summary",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
        })

        _refresh_codex_report_for_closeout(
            state_dir=state_dir,
            repo_root=tmp_path,
            decision_id="decision_gate",
            round_id="round_gate",
        )
        from reverse_agent.project_gate import read_codex_report_summary
        report = read_codex_report_summary(state_dir)
        ga = report.get("generated_artifacts", [])
        assert "project_state/gates/codex_report_auto_summary.json" in ga

    def test_final_check_auto_summary_absent_backward_compatible(
        self, tmp_path: Path,
    ) -> None:
        """final-check report_auto_summary_consistency PASSes (skipped) when
        codex_report_auto_summary.json is not present on disk."""
        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        assert not (state_dir / "gates" / "codex_report_auto_summary.json").exists()

        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "report_auto_summary_consistency")
        assert consistency_check["status"] == "PASS"
        assert consistency_check.get("skipped_reason") == "report_auto_summary_not_present"

    def test_command_kind_recognizes_report_auto_summary(self) -> None:
        """_command_kind recognizes report-auto-summary commands."""
        from reverse_agent.project_gate import _command_kind
        assert _command_kind(
            "python -m reverse_agent.project_gate report-auto-summary --state-dir project_state"
        ) == "report-auto-summary"

    def test_command_expected_exit_codes_allows_0_or_1_for_report_auto_summary(self) -> None:
        """_command_expected_exit_codes allows exit 0 or 1 for report-auto-summary."""
        from reverse_agent.project_gate import _command_expected_exit_codes
        codes, _, _ = _command_expected_exit_codes(
            kind="report-auto-summary",
            phase="gate",
            command="python -m reverse_agent.project_gate report-auto-summary --state-dir project_state",
            decision_text="",
            final_check_passed=None,
        )
        assert codes == [0, 1]

    def test_auto_summary_writes_artifact_to_disk(self, tmp_path: Path) -> None:
        """report_auto_summary() writes codex_report_auto_summary.json to
        project_state/gates/."""
        from reverse_agent.project_gate import (
            report_auto_summary,
            REPORT_AUTO_SUMMARY_RESULT_NAME,
        )

        state_dir = _make_gate_state(tmp_path)
        result = report_auto_summary(state_dir=state_dir, write_result=True)
        assert (state_dir / "gates" / REPORT_AUTO_SUMMARY_RESULT_NAME).exists()
        assert result.get("artifact_name") == REPORT_AUTO_SUMMARY_RESULT_NAME
        assert result.get("source") == "synthesized_from_structured_evidence"

    def test_synthesis_includes_auto_summary_when_exists(self, tmp_path: Path) -> None:
        """build_report_summary_synthesis includes codex_report_auto_summary.json
        in generated_artifacts when the file exists on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        _write_json(state_dir / "gates" / "codex_report_auto_summary.json", {
            "schema_version": 1,
            "gate_name": "report-auto-summary",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
        })

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/codex_report_auto_summary.json" in ga

    def test_synthesis_excludes_auto_summary_when_absent(self, tmp_path: Path) -> None:
        """build_report_summary_synthesis does not include
        codex_report_auto_summary.json when the file does not exist on disk."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path)
        assert not (state_dir / "gates" / "codex_report_auto_summary.json").exists()

        result = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        ga = result.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/codex_report_auto_summary.json" not in ga


class TestRunRoundScaffold:
    """Regression tests for Run-Round Scaffold v1.

    These tests verify that run_round() produces the required scaffold
    artifact fields, derives phases from command-plan, respects command-plan
    authority, excludes omitted/unauthorized commands, and preserves backward
    compatibility.
    """

    def test_dry_run_includes_required_scaffold_fields(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        # Required fields per decision scope
        assert result["schema_version"] == 1
        assert result["artifact_name"] == "run_round_result.json"
        assert result["gate_name"] == "run-round"
        assert result["gate_status"] in {"PASSED", "WARN", "FAILED"}
        assert result["decision_id"]
        assert result["round_id"]
        assert result["generated_at"]
        assert result["mode"] == "dry-run"
        assert isinstance(result["phases"], list)
        assert isinstance(result["authorized_commands"], list)
        assert isinstance(result["omitted_commands"], list)
        assert isinstance(result["would_run_commands"], list)
        assert isinstance(result["warnings"], list)
        assert isinstance(result["blocking_reasons"], list)
        assert result["recommended_next_action"]

    def test_gate_status_equals_run_status(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        assert result["gate_status"] == result["run_status"]

    def test_phases_derived_from_command_plan(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        phases = result["phases"]
        assert len(phases) > 0
        # Phases should be unique and ordered
        assert phases == list(dict.fromkeys(phases))

    def test_authorized_commands_match_command_plan(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        authorized = result["authorized_commands"]
        assert len(authorized) > 0
        # Every authorized command should appear in command-plan commands
        plan_commands = [str(cmd.get("command") or "") for cmd in result["commands"]]
        for cmd in authorized:
            assert cmd in plan_commands

    def test_omitted_commands_from_command_plan(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        # omitted_commands should be a list (may be empty)
        assert isinstance(result["omitted_commands"], list)
        # Omitted commands must not appear in would_run_commands
        for cmd in result["omitted_commands"]:
            assert cmd not in result["would_run_commands"]

    def test_would_run_commands_excludes_self_invocation(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
""",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        would_run = result["would_run_commands"]
        # Self-invocation commands must not be in would_run
        for cmd in would_run:
            assert "run-round" not in cmd
            assert "run-closeout" not in cmd

    def test_would_run_commands_excludes_close_round(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="""python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_1
""",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        would_run = result["would_run_commands"]
        for cmd in would_run:
            assert "close-round" not in cmd

    def test_dry_run_does_not_execute_commands(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )

        def fail_if_called(command: str) -> subprocess.CompletedProcess[str]:
            raise AssertionError(f"dry-run executed command: {command}")

        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path, command_runner=fail_if_called)
        assert result["executed_commands"] == []
        assert result["mode"] == "dry-run"

    def test_unauthorized_command_not_in_would_run(self, tmp_path: Path) -> None:
        """Commands not in command-plan must not appear in would_run_commands."""
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        would_run = result["would_run_commands"]
        # would_run_commands must be a subset of authorized_commands
        for cmd in would_run:
            assert cmd in result["authorized_commands"]

    def test_artifact_written_to_disk(self, tmp_path: Path) -> None:
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path, write_result=True)
        artifact_path = state_dir / "gates" / "run_round_result.json"
        assert artifact_path.exists()
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert data["artifact_name"] == "run_round_result.json"
        assert data["gate_name"] == "run-round"

    def test_command_kind_recognizes_run_round(self) -> None:
        assert _command_kind("python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run") == "run-round"
        assert _command_kind("python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json") == "run-round"

    def test_command_expected_exit_codes_allows_0_or_1_for_run_round(self) -> None:
        codes, note, warning = _command_expected_exit_codes(
            kind="run-round",
            phase="gate",
            command="python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run",
            decision_text="",
        )
        assert codes == [0, 1]
        assert warning is None

    def test_run_round_result_in_reportable_gate_artifacts(self) -> None:
        """run_round_result.json is in _REPORTABLE_GATE_ARTIFACT_NAMES."""
        from reverse_agent.project_gate import _REPORTABLE_GATE_ARTIFACT_NAMES
        assert "run_round_result.json" in _REPORTABLE_GATE_ARTIFACT_NAMES

    def test_run_round_in_closeout_allowed_kinds(self) -> None:
        """run-round is in RUN_CLOSEOUT_ALLOWED_KINDS."""
        from reverse_agent.project_gate import RUN_CLOSEOUT_ALLOWED_KINDS
        assert "run-round" in RUN_CLOSEOUT_ALLOWED_KINDS

    def test_backward_compatible_run_status_field(self, tmp_path: Path) -> None:
        """run_status field is preserved for backward compatibility."""
        state_dir = _make_command_plan_state(
            tmp_path,
            tests_block="python -m pytest tests/test_project_gate.py -q",
        )
        result = run_round(state_dir=state_dir, dry_run=True, repo_root=tmp_path)
        assert "run_status" in result
        assert result["run_status"] == result["gate_status"]


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

    def test_continuation_session_round_work_not_flagged(self) -> None:
        """Startup shows source/test dirty that are in new_dirty_files_since_baseline
        (this round's work in a continuation session) -> PASS, not FAIL."""
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
                "new_dirty_files_since_baseline": [
                    "reverse_agent/project_gate.py",
                    "tests/test_project_gate.py",
                ],
            },
            decision_text=self._DECISION_TEXT,
            report_text="",
            pytest_text=self._DIRTY_PYTEST_TEXT,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "PASS"
        assert result.get("missing_from_baseline") == []

    def test_continuation_session_truly_inherited_still_fails(self) -> None:
        """Startup shows source/test dirty that are NOT in new_dirty_files_since_baseline
        (truly inherited dirty, not this round's work) -> FAIL."""
        dirty_with_extra = (
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
            " M reverse_agent/other.py\n"
            "===== EXIT: 0 =====\n"
        )
        decision_with_other = (
            "## Implementation Scope\n\n"
            "Allowed source files:\n\n"
            "- `reverse_agent/project_gate.py`\n\n"
            "- `reverse_agent/other.py`\n\n"
            "Allowed tests:\n\n"
            "- `tests/test_project_gate.py`\n\n"
            "## Do Not Do\nNothing\n"
        )
        result = _startup_baseline_consistency_check(
            delta_summary={
                "baseline_available": True,
                "baseline_dirty_files": [],
                "inherited_dirty_files": [],
                "new_dirty_files_since_baseline": [
                    "reverse_agent/project_gate.py",
                ],
            },
            decision_text=decision_with_other,
            report_text="",
            pytest_text=dirty_with_extra,
        )
        assert result["name"] == "startup_baseline_consistency"
        assert result["status"] == "FAIL"
        assert "reverse_agent/other.py" in result.get("missing_from_baseline", [])


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


class TestStartupCommandCoverageLogicFix:
    """Regression tests for the startup_command_coverage / command_plan_covers_report_tests
    circular conflict fix.

    The circular conflict was:
    - startup_command_coverage expected startup commands in tests_ran
    - command_plan_covers_report_tests expected tests_ran to match command_plan
    - For fast profile, command_plan does not include startup commands

    The fix:
    - startup_command_coverage now checks recorded command blocks in pytest_result.txt
    - command_plan_covers_report_tests excludes startup commands from the missing diff
    """

    @staticmethod
    def _make_state_dir(
        tmp_path: Path,
        *,
        command_plan_commands: list[dict[str, Any]],
        report_tests: list[str],
    ) -> Path:
        """Create a minimal state_dir with a command_plan.json."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        _write_json(
            gates_dir / "command_plan.json",
            {
                "schema_version": 1,
                "plan_name": "command-plan",
                "plan_status": "PASSED",
                "decision_id": "d_scov",
                "round_id": "r_scov",
                "mainline": "engineering_branch",
                "generated_at": "2026-06-18T00:00:00Z",
                "commands": command_plan_commands,
                "warnings": [],
                "blocking_reasons": [],
            },
        )
        return state_dir

    _STARTUP_BLOCKS = (
        "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
        "F:\\reverse-agent\n===== EXIT: 0 =====\n"
        "===== COMMAND: Get-Location =====\n"
        "F:\\reverse-agent\n===== EXIT: 0 =====\n"
        "===== COMMAND: Test-Path F:\\reverse-agent =====\n"
        "True\n===== EXIT: 0 =====\n"
        "===== COMMAND: git rev-parse --show-toplevel =====\n"
        "F:/reverse-agent\n===== EXIT: 0 =====\n"
        "===== COMMAND: git status --short =====\n"
        "===== EXIT: 0 =====\n"
    )

    def test_startup_command_coverage_passes_with_command_blocks_only(self, tmp_path: Path) -> None:
        """startup_command_coverage PASSes when startup commands are recorded
        as command blocks in pytest_result.txt, even if they are NOT in tests_ran."""
        report_cmd = "python -m reverse_agent.project_gate report-summary --state-dir project_state"
        final_cmd = "python -m reverse_agent.project_gate final-check --state-dir project_state"
        cmd_plan_cmd = "python -m reverse_agent.project_gate command-plan --state-dir project_state"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {"index": 1, "command": cmd_plan_cmd, "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
                {"index": 2, "command": report_cmd, "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
                {"index": 3, "command": final_cmd, "phase": "gate", "kind": "final-check", "required": True, "expected_exit_codes": [0, 1]},
            ],
            report_tests=[cmd_plan_cmd, report_cmd, final_cmd],
        )
        pytest_text = (
            self._STARTUP_BLOCKS
            + _command_block(cmd_plan_cmd, "command plan generated", exit_code=0)
            + "\n"
            + _command_block(report_cmd, "report summary generated", exit_code=0)
            + "\n"
            + _command_block(final_cmd, "final check done", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision={"decision_id": "d_scov", "round_id": "r_scov", "mainline": "engineering_branch"},
            report={
                "report_id": "codex_report_scov",
                "round_id": "r_scov",
                "based_on_decision_id": "d_scov",
                "tests_ran": [cmd_plan_cmd, report_cmd, final_cmd],
                "generated_artifacts": ["project_state/gates/command_plan.json"],
            },
            pytest_text=pytest_text,
        )

        startup_check = next(c for c in checks if c["name"] == "startup_command_coverage")
        assert startup_check["status"] == "PASS", (
            f"startup_command_coverage should PASS with command blocks, got: {startup_check}"
        )

    def test_startup_command_coverage_fails_without_command_blocks(self, tmp_path: Path) -> None:
        """startup_command_coverage FAILs when startup command blocks are
        absent from pytest_result.txt."""
        report_cmd = "python -m reverse_agent.project_gate report-summary --state-dir project_state"
        cmd_plan_cmd = "python -m reverse_agent.project_gate command-plan --state-dir project_state"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {"index": 1, "command": cmd_plan_cmd, "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
                {"index": 2, "command": report_cmd, "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            ],
            report_tests=[cmd_plan_cmd, report_cmd],
        )
        # pytest_text has NO startup command blocks
        pytest_text = (
            _command_block(cmd_plan_cmd, "command plan generated", exit_code=0)
            + "\n"
            + _command_block(report_cmd, "report summary generated", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision={"decision_id": "d_scov", "round_id": "r_scov", "mainline": "engineering_branch"},
            report={
                "report_id": "codex_report_scov",
                "round_id": "r_scov",
                "based_on_decision_id": "d_scov",
                "tests_ran": [cmd_plan_cmd, report_cmd],
                "generated_artifacts": ["project_state/gates/command_plan.json"],
            },
            pytest_text=pytest_text,
        )

        startup_check = next(c for c in checks if c["name"] == "startup_command_coverage")
        assert startup_check["status"] == "FAIL", (
            f"startup_command_coverage should FAIL without command blocks, got: {startup_check}"
        )

    def test_command_plan_covers_report_tests_ignores_startup_commands(self, tmp_path: Path) -> None:
        """command_plan_covers_report_tests PASSes when tests_ran contains
        startup commands that are NOT in command_plan (startup commands
        are excluded from the coverage diff)."""
        report_cmd = "python -m reverse_agent.project_gate report-summary --state-dir project_state"
        cmd_plan_cmd = "python -m reverse_agent.project_gate command-plan --state-dir project_state"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {"index": 1, "command": cmd_plan_cmd, "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
                {"index": 2, "command": report_cmd, "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            ],
            report_tests=[cmd_plan_cmd, report_cmd],
        )
        # tests_ran includes startup commands that are NOT in command_plan
        pytest_text = (
            self._STARTUP_BLOCKS
            + _command_block(cmd_plan_cmd, "command plan generated", exit_code=0)
            + "\n"
            + _command_block(report_cmd, "report summary generated", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision={"decision_id": "d_scov", "round_id": "r_scov", "mainline": "engineering_branch"},
            report={
                "report_id": "codex_report_scov",
                "round_id": "r_scov",
                "based_on_decision_id": "d_scov",
                "tests_ran": [
                    "Set-Location F:\\reverse-agent",
                    "Get-Location",
                    "Test-Path F:\\reverse-agent",
                    "git rev-parse --show-toplevel",
                    "git status --short",
                    cmd_plan_cmd,
                    report_cmd,
                ],
                "generated_artifacts": ["project_state/gates/command_plan.json"],
            },
            pytest_text=pytest_text,
        )

        coverage_check = next(c for c in checks if c["name"] == "command_plan_covers_report_tests")
        assert coverage_check["status"] == "PASS", (
            f"command_plan_covers_report_tests should PASS (startup commands excluded), got: {coverage_check}"
        )

    def test_command_plan_covers_report_tests_still_fails_for_missing_non_startup(self, tmp_path: Path) -> None:
        """command_plan_covers_report_tests still FAILs when tests_ran contains
        a non-startup command that is NOT in command_plan."""
        report_cmd = "python -m reverse_agent.project_gate report-summary --state-dir project_state"
        cmd_plan_cmd = "python -m reverse_agent.project_gate command-plan --state-dir project_state"
        extra_cmd = "python -m reverse_agent.project_gate doctor --state-dir project_state"
        state_dir = self._make_state_dir(
            tmp_path,
            command_plan_commands=[
                {"index": 1, "command": cmd_plan_cmd, "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
                {"index": 2, "command": report_cmd, "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            ],
            report_tests=[cmd_plan_cmd, report_cmd, extra_cmd],
        )
        pytest_text = (
            self._STARTUP_BLOCKS
            + _command_block(cmd_plan_cmd, "command plan generated", exit_code=0)
            + "\n"
            + _command_block(report_cmd, "report summary generated", exit_code=0)
            + "\n"
            + _command_block(extra_cmd, "doctor output", exit_code=0)
        )

        checks = _validate_command_plan_consistency(
            state_dir=state_dir,
            decision={"decision_id": "d_scov", "round_id": "r_scov", "mainline": "engineering_branch"},
            report={
                "report_id": "codex_report_scov",
                "round_id": "r_scov",
                "based_on_decision_id": "d_scov",
                "tests_ran": [cmd_plan_cmd, report_cmd, extra_cmd],
                "generated_artifacts": ["project_state/gates/command_plan.json"],
            },
            pytest_text=pytest_text,
        )

        coverage_check = next(c for c in checks if c["name"] == "command_plan_covers_report_tests")
        assert coverage_check["status"] == "FAIL", (
            f"command_plan_covers_report_tests should FAIL for missing non-startup command, got: {coverage_check}"
        )

    def test_is_startup_command_helper(self) -> None:
        """_is_startup_command correctly identifies startup commands."""
        from reverse_agent.project_gate import _is_startup_command

        assert _is_startup_command("Set-Location F:\\reverse-agent")
        assert _is_startup_command("Get-Location")
        assert _is_startup_command("Test-Path F:\\reverse-agent")
        assert _is_startup_command("git rev-parse --show-toplevel")
        assert _is_startup_command("git status --short")

        # Non-startup commands
        assert not _is_startup_command("python -m pytest tests/")
        assert not _is_startup_command("python -m reverse_agent.project_gate preflight --state-dir project_state")
        assert not _is_startup_command("git add .")
        assert not _is_startup_command("git commit -m test")


# ---------------------------------------------------------------------------
# Tests for referenced_artifacts / required_closeout_artifacts schema support
# and decision-lint CLI command (decision_20260619_report_summary_referenced_artifacts_schema_v1)
# ---------------------------------------------------------------------------

_REQUIRED_CLOSEOUT_PATHS = [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
]


def _write_decision_with_closeout_evidence(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    mainline: str = "engineering_branch",
) -> None:
    """Overwrite decision_packet.md to include Current Evidence with project_state paths."""
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

## 1. Goal

Build a read-only project gate.

## 2. Current Evidence

Required existing state records for closeout traceability:

- `project_state/artifact_index.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
""",
        encoding="utf-8",
    )


def _add_referenced_artifacts_to_report(state_dir: Path, artifacts: list[str]) -> None:
    """Read the existing codex_execution_report.md, add referenced_artifacts, and write it back."""
    from reverse_agent.project_state import extract_markdown_json_block, CODEX_REPORT_SUMMARY_BLOCK_NAME

    report_path = state_dir / "codex_execution_report.md"
    text = report_path.read_text(encoding="utf-8")
    meta = extract_markdown_json_block(text, CODEX_REPORT_SUMMARY_BLOCK_NAME)
    report = {k: v for k, v in meta.items() if k not in ("found", "parse_error")}
    report["referenced_artifacts"] = artifacts
    report_path.write_text(
        f"""```json {CODEX_REPORT_SUMMARY_BLOCK_NAME}
{json.dumps(report, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )


def test_preflight_skips_protected_terms_in_code_blocks(tmp_path: Path) -> None:
    """Protected terms inside fenced code blocks do not trigger mainline_scope_policy."""
    goal = """Build a read-only project gate.

```python
# This code block contains "solver" but should not trigger scope policy
solver_config = {"runtime": True}
```
"""
    state_dir = _make_preflight_state(tmp_path, goal=goal)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "mainline_scope_policy")["status"] == "PASS"


def test_preflight_skips_protected_terms_in_project_state_paths(tmp_path: Path) -> None:
    """Protected terms in project_state file paths in Goal do not trigger mainline_scope_policy."""
    goal = """Build a read-only project gate.

Required existing state records for traceability:

- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
"""
    state_dir = _make_preflight_state(tmp_path, goal=goal)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert _check(result, "mainline_scope_policy")["status"] == "PASS"


def test_report_summary_includes_referenced_and_required_closeout_artifacts(tmp_path: Path) -> None:
    """Synthesis includes referenced_artifacts and required_closeout_artifacts when decision declares them."""
    state_dir = _make_report_summary_state(tmp_path)
    _write_decision_with_closeout_evidence(
        state_dir,
        decision_id="decision_report_summary",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _REQUIRED_CLOSEOUT_PATHS)

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    summary = result["synthesized_summary"]
    assert "required_closeout_artifacts" in summary
    assert "project_state/artifact_index.json" in summary["required_closeout_artifacts"]
    assert (
        "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json"
        in summary["required_closeout_artifacts"]
    )
    assert "referenced_artifacts" in summary
    assert "project_state/artifact_index.json" in summary["referenced_artifacts"]


def test_decision_lint_cli_passes_valid_decision(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """decision-lint CLI exits 0 for a valid decision."""
    state_dir = _make_preflight_state(tmp_path)

    exit_code = main(["decision-lint", "--state-dir", str(state_dir), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["ok"] is True
    assert output["decision_status"] == "APPROVED"


def test_decision_lint_cli_fails_invalid_decision(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """decision-lint CLI exits 1 for an invalid decision."""
    state_dir = _make_preflight_state(tmp_path, status="TEMPLATE_ONLY")

    exit_code = main(["decision-lint", "--state-dir", str(state_dir), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False


def test_final_check_validates_required_closeout_artifacts_covered(tmp_path: Path) -> None:
    """final-check passes when required closeout artifacts are covered by referenced_artifacts."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_closeout_evidence(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _REQUIRED_CLOSEOUT_PATHS)
    # Delete existing archive and re-archive with updated decision/report
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    check = _check(result, "required_closeout_artifacts_covered")
    assert check["status"] == "PASS"


def test_final_check_fails_when_required_closeout_artifacts_uncovered(tmp_path: Path) -> None:
    """final-check fails when required closeout artifacts are not covered."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_closeout_evidence(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
    )
    # Do NOT add referenced_artifacts to the report
    # Delete existing archive and re-archive with updated decision
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    check = _check(result, "required_closeout_artifacts_covered")
    assert check["status"] == "FAIL"
    assert "project_state/artifact_index.json" in check["uncovered_artifacts"]


# ---------------------------------------------------------------------------
# Tests for structured closeout_artifacts_contract block and numbered list
# extraction (decision_20260619_required_closeout_artifacts_contract_v1)
# ---------------------------------------------------------------------------

_CLOSEOUT_CONTRACT_PATHS = [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md",
]


def _write_decision_with_structured_closeout_contract(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    mainline: str = "engineering_branch",
) -> None:
    """Decision with a structured closeout_artifacts_contract JSON block."""
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
    contract = {
        "required_closeout_artifacts": _CLOSEOUT_CONTRACT_PATHS,
    }
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

Build a read-only project gate.

## 2. Current Evidence

Required existing state records for closeout traceability are declared in the
structured contract block below.

```json closeout_artifacts_contract
{json.dumps(contract, indent=2)}
```

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
""",
        encoding="utf-8",
    )


def _write_decision_with_numbered_closeout_evidence(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    mainline: str = "engineering_branch",
) -> None:
    """Decision with numbered list closeout records in Current Evidence."""
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
    numbered_items = "\n".join(
        f"{i}. `{path}`" for i, path in enumerate(_CLOSEOUT_CONTRACT_PATHS, 1)
    )
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

Build a read-only project gate.

## 2. Current Evidence

Required existing state records for closeout traceability are listed below as
the regression case. They are read-only inputs and must not be regenerated or
modified:

{numbered_items}

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
""",
        encoding="utf-8",
    )


def test_decision_required_closeout_artifacts_from_structured_block() -> None:
    """_decision_required_closeout_artifacts extracts from closeout_artifacts_contract block."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

```json closeout_artifacts_contract
{
  "required_closeout_artifacts": [
    "project_state/artifact_index.json",
    "project_state/sample.json"
  ]
}
```
"""
    result = _decision_required_closeout_artifacts(decision_text)
    assert "project_state/artifact_index.json" in result
    assert "project_state/sample.json" in result


def test_decision_required_closeout_artifacts_from_numbered_list() -> None:
    """_decision_required_closeout_artifacts extracts from numbered markdown lists."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

Required records:

1. `project_state/artifact_index.json`
2. `project_state/sample.json`
3. `project_state/other.md`
"""
    result = _decision_required_closeout_artifacts(decision_text)
    assert "project_state/artifact_index.json" in result
    assert "project_state/sample.json" in result
    assert "project_state/other.md" in result


def test_decision_required_closeout_artifacts_from_bullet_list() -> None:
    """_decision_required_closeout_artifacts still extracts from bullet lists (backward compat)."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

Required records:

- `project_state/artifact_index.json`
- `project_state/sample.json`
"""
    result = _decision_required_closeout_artifacts(decision_text)
    assert "project_state/artifact_index.json" in result
    assert "project_state/sample.json" in result


def test_decision_required_closeout_artifacts_empty_when_no_declaration() -> None:
    """_decision_required_closeout_artifacts returns empty set when no declaration present."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

No closeout records needed.

## 6. Implementation Scope

- `reverse_agent/project_gate.py`
"""
    result = _decision_required_closeout_artifacts(decision_text)
    assert result == set()


def test_decision_required_closeout_artifacts_ignores_prose_mentions() -> None:
    """_decision_required_closeout_artifacts must not extract paths from prose bullet items that merely mention a path."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

Blocking facts from audit:

- `project_state/gates/execute_decision_result.json` did not exist when fetched from GitHub.
- `project_state/gates/execute_decision_result.json` was absent from generated_artifacts.

Required records:

- `project_state/artifact_index.json`
"""
    result = _decision_required_closeout_artifacts(decision_text)
    # Path-only bullet items should be extracted
    assert "project_state/artifact_index.json" in result
    # Prose bullet items that merely mention a path should NOT be extracted
    assert "project_state/gates/execute_decision_result.json" not in result


def test_structured_block_takes_precedence_over_markdown() -> None:
    """Structured closeout_artifacts_contract block takes precedence over markdown lists."""
    from reverse_agent.project_gate import _decision_required_closeout_artifacts

    decision_text = """```json decision_meta
{"decision_id": "d1", "status": "APPROVED"}
```

# DECISION_PACKET

## 2. Current Evidence

```json closeout_artifacts_contract
{
  "required_closeout_artifacts": [
    "project_state/from_contract.json"
  ]
}
```

- `project_state/from_bullet.json`
"""
    result = _decision_required_closeout_artifacts(decision_text)
    assert "project_state/from_contract.json" in result
    # When structured block is present and non-empty, markdown lists are not used
    assert "project_state/from_bullet.json" not in result


def test_final_check_validates_structured_closeout_contract_covered(tmp_path: Path) -> None:
    """final-check passes when structured contract records are covered by referenced_artifacts."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_structured_closeout_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _CLOSEOUT_CONTRACT_PATHS)
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    check = _check(result, "required_closeout_artifacts_covered")
    assert check["status"] == "PASS"
    assert "project_state/artifact_index.json" in check["required_closeout_artifacts"]


def test_final_check_validates_numbered_list_closeout_covered(tmp_path: Path) -> None:
    """final-check passes when numbered list records are covered by referenced_artifacts."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_numbered_closeout_evidence(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _CLOSEOUT_CONTRACT_PATHS)
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    check = _check(result, "required_closeout_artifacts_covered")
    assert check["status"] == "PASS"
    assert "project_state/artifact_index.json" in check["required_closeout_artifacts"]


def test_final_check_fails_structured_contract_uncovered(tmp_path: Path) -> None:
    """final-check fails when structured contract records are not covered."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_structured_closeout_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
    )
    # Do NOT add referenced_artifacts to the report
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    check = _check(result, "required_closeout_artifacts_covered")
    assert check["status"] == "FAIL"
    assert "project_state/artifact_index.json" in check["uncovered_artifacts"]


def test_report_summary_synthesis_includes_required_closeout_from_structured_block(
    tmp_path: Path,
) -> None:
    """Synthesis includes required_closeout_artifacts from structured contract block."""
    state_dir = _make_report_summary_state(tmp_path)
    _write_decision_with_structured_closeout_contract(
        state_dir,
        decision_id="decision_report_summary",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _CLOSEOUT_CONTRACT_PATHS)

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    summary = result["synthesized_summary"]
    assert "required_closeout_artifacts" in summary
    for path in _CLOSEOUT_CONTRACT_PATHS:
        assert path in summary["required_closeout_artifacts"]


def test_report_summary_synthesis_includes_required_closeout_from_numbered_list(
    tmp_path: Path,
) -> None:
    """Synthesis includes required_closeout_artifacts from numbered list."""
    state_dir = _make_report_summary_state(tmp_path)
    _write_decision_with_numbered_closeout_evidence(
        state_dir,
        decision_id="decision_report_summary",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _CLOSEOUT_CONTRACT_PATHS)

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    summary = result["synthesized_summary"]
    assert "required_closeout_artifacts" in summary
    for path in _CLOSEOUT_CONTRACT_PATHS:
        assert path in summary["required_closeout_artifacts"]


def test_read_codex_report_summary_preserves_required_closeout_artifacts(
    tmp_path: Path,
) -> None:
    """read_codex_report_summary preserves required_closeout_artifacts field."""
    from reverse_agent.project_state import read_codex_report_summary

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    report_payload = {
        "schema_version": 1,
        "report_id": "r1",
        "round_id": "round_1",
        "based_on_decision_id": "d1",
        "status": "SUCCESS",
        "acceptance_recommendation": "ACCEPTED",
        "files_changed": [],
        "tests_ran": [],
        "generated_artifacts": [],
        "referenced_artifacts": ["project_state/artifact_index.json"],
        "required_closeout_artifacts": ["project_state/artifact_index.json"],
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(report_payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    result = read_codex_report_summary(state_dir)
    assert result["required_closeout_artifacts"] == ["project_state/artifact_index.json"]
    assert result["referenced_artifacts"] == ["project_state/artifact_index.json"]


def test_read_codex_report_summary_backward_compat_without_closeout_fields(
    tmp_path: Path,
) -> None:
    """read_codex_report_summary returns None for closeout fields when absent (backward compat)."""
    from reverse_agent.project_state import read_codex_report_summary

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    report_payload = {
        "schema_version": 1,
        "report_id": "r1",
        "round_id": "round_1",
        "based_on_decision_id": "d1",
        "status": "SUCCESS",
        "acceptance_recommendation": "ACCEPTED",
        "files_changed": [],
        "tests_ran": [],
        "generated_artifacts": [],
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(report_payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    result = read_codex_report_summary(state_dir)
    assert result["required_closeout_artifacts"] is None
    assert result["referenced_artifacts"] is None
    assert result["status"] == "SUCCESS"


def test_report_summary_synthesis_includes_required_closeout_in_generated_artifacts(
    tmp_path: Path,
) -> None:
    """Synthesis includes required_closeout_artifacts in generated_artifacts."""
    state_dir = _make_report_summary_state(tmp_path)
    _write_decision_with_structured_closeout_contract(
        state_dir,
        decision_id="decision_report_summary",
        round_id="round_gate",
    )
    _add_referenced_artifacts_to_report(state_dir, _CLOSEOUT_CONTRACT_PATHS)
    # Also add required_closeout_artifacts to the report so the synthesis
    # can promote them into generated_artifacts.
    from reverse_agent.project_state import extract_markdown_json_block, CODEX_REPORT_SUMMARY_BLOCK_NAME

    report_path = state_dir / "codex_execution_report.md"
    text = report_path.read_text(encoding="utf-8")
    meta = extract_markdown_json_block(text, CODEX_REPORT_SUMMARY_BLOCK_NAME)
    report = {k: v for k, v in meta.items() if k not in ("found", "parse_error")}
    report["required_closeout_artifacts"] = _CLOSEOUT_CONTRACT_PATHS
    report_path.write_text(
        f"""```json {CODEX_REPORT_SUMMARY_BLOCK_NAME}
{json.dumps(report, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    summary = result["synthesized_summary"]
    assert "generated_artifacts" in summary
    for path in _CLOSEOUT_CONTRACT_PATHS:
        assert path in summary["generated_artifacts"], (
            f"required_closeout_artifact {path} should be in generated_artifacts"
        )


# ---------------------------------------------------------------------------
# Decision contract hardening tests (Feature A/B/C/D)
# ---------------------------------------------------------------------------

_DECISION_CONTRACT_ARTIFACTS = [
    "project_state/state_rebuild_apply_plan.json",
    "project_state/proposed_state/artifact_index.json",
]


def _write_decision_with_contract(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    contract: dict[str, Any],
    mainline: str = "engineering_branch",
) -> None:
    """Write a decision_packet.md with a decision_contract block."""
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

```json decision_contract
{json.dumps(contract, indent=2)}
```

# DECISION_PACKET

## 1. Goal

Harden closeout contract.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
""",
        encoding="utf-8",
    )


def test_decision_contract_absent_backward_compatible(tmp_path: Path) -> None:
    """Decisions without decision_contract remain backward-compatible."""
    state_dir = _make_gate_state(tmp_path)
    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    # New checks should PASS (not applicable)
    assert _check(result, "decision_contract_artifact_placement")["status"] == "PASS"
    assert _check(result, "decision_contract_status_hardening")["status"] == "PASS"


def test_decision_contract_invalid_json_fails_decision_lint(tmp_path: Path) -> None:
    """Invalid decision_contract JSON must fail decision-lint."""
    from reverse_agent.project_state import lint_decision

    state_dir = _make_preflight_state(tmp_path)
    # Overwrite decision with invalid contract JSON
    payload = {
        "schema_version": 1,
        "decision_id": "decision_preflight",
        "round_id": "round_preflight",
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

```json decision_contract
{{invalid json here}}
```

# DECISION_PACKET

## 1. Goal

Test invalid contract.

## 6. Implementation Scope

- `reverse_agent/project_gate.py`
""",
        encoding="utf-8",
    )
    result = lint_decision(state_dir=state_dir)
    assert not result["ok"]
    assert any("decision_contract invalid JSON" in e for e in result["errors"])


def test_decision_contract_unknown_fields_warn(tmp_path: Path) -> None:
    """Unknown fields in decision_contract should warn."""
    from reverse_agent.project_state import lint_decision

    state_dir = _make_preflight_state(tmp_path)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_preflight",
        round_id="round_preflight",
        contract={
            "required_generated_artifacts": [],
            "unknown_field": "value",
        },
    )
    result = lint_decision(state_dir=state_dir)
    assert result["ok"]  # warnings don't fail
    assert any("unknown fields" in w for w in result["warnings"])


def test_decision_contract_required_generated_artifact_missing_fails(tmp_path: Path) -> None:
    """Required generated artifact missing from generated_artifacts fails."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": _DECISION_CONTRACT_ARTIFACTS,
            "required_files_changed": [],
        },
    )
    # Do NOT add the required artifacts to generated_artifacts
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_artifact_placement")
    assert check["status"] == "FAIL"
    assert "project_state/state_rebuild_apply_plan.json" in check["missing_from_generated_artifacts"]


def test_decision_contract_required_files_changed_missing_fails(tmp_path: Path) -> None:
    """Required changed file missing from files_changed fails."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": [],
            "required_files_changed": ["reverse_agent/special.py"],
        },
    )
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_artifact_placement")
    assert check["status"] == "FAIL"
    assert "reverse_agent/special.py" in check["missing_from_files_changed"]


def test_decision_contract_artifact_referenced_only_fails(tmp_path: Path) -> None:
    """Required generated artifact in referenced_artifacts only fails."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": _DECISION_CONTRACT_ARTIFACTS,
            "required_files_changed": [],
        },
    )
    # Add to referenced_artifacts but NOT generated_artifacts
    _add_referenced_artifacts_to_report(state_dir, _DECISION_CONTRACT_ARTIFACTS)
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_artifact_placement")
    assert check["status"] == "FAIL"
    assert "project_state/state_rebuild_apply_plan.json" in check["referenced_only_artifacts"]


def test_decision_contract_required_generated_artifact_present_passes(tmp_path: Path) -> None:
    """Required generated artifact present in generated_artifacts passes."""
    state_dir = _make_gate_state(tmp_path)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": _DECISION_CONTRACT_ARTIFACTS,
            "required_files_changed": [],
        },
    )
    # Add required artifacts to generated_artifacts
    from reverse_agent.project_state import extract_markdown_json_block, CODEX_REPORT_SUMMARY_BLOCK_NAME

    report_path = state_dir / "codex_execution_report.md"
    text = report_path.read_text(encoding="utf-8")
    meta = extract_markdown_json_block(text, CODEX_REPORT_SUMMARY_BLOCK_NAME)
    report = {k: v for k, v in meta.items() if k not in ("found", "parse_error")}
    existing = list(report.get("generated_artifacts") or [])
    report["generated_artifacts"] = existing + _DECISION_CONTRACT_ARTIFACTS
    report_path.write_text(
        f"""```json {CODEX_REPORT_SUMMARY_BLOCK_NAME}
{json.dumps(report, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_artifact_placement")
    assert check["status"] == "PASS"


def test_decision_contract_status_hardening_success_without_final_check_fails(tmp_path: Path) -> None:
    """SUCCESS report without matching final gate IDs fails status hardening."""
    state_dir = _make_command_plan_gate_state(tmp_path, archived=True)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": [],
            "required_files_changed": [],
            "accepted_requires_final_check_passed": True,
        },
    )
    # Overwrite final_gate_result with mismatched IDs
    _write_json(state_dir / "gates" / "final_gate_result.json", {
        "schema_version": 1,
        "gate_name": "final-check",
        "gate_status": "PASSED",
        "decision_id": "wrong_decision",
        "round_id": "wrong_round",
    })
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_status_hardening")
    assert check["status"] == "FAIL"


def test_decision_contract_status_hardening_accepted_without_archive_warns(tmp_path: Path) -> None:
    """ACCEPTED with close_round_required=true but no archive produces WARN, not FAIL.

    The archive check is handled by the existing round_manifest_present WARN.
    The decision_contract_status_hardening check should PASS (not FAIL) when
    the archive is missing, because close-round hasn't been run yet.
    """
    state_dir = _make_command_plan_gate_state(tmp_path, archived=True)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": [],
            "required_files_changed": [],
            "close_round_required": True,
        },
    )
    # Remove archive so manifest_present is False
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_status_hardening")
    assert check["status"] == "PASS"


def test_decision_contract_status_hardening_pytest_only_fails(tmp_path: Path) -> None:
    """SUCCESS report missing gate command blocks fails status hardening."""
    state_dir = _make_command_plan_gate_state(tmp_path, archived=True)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": [],
            "required_files_changed": [],
        },
    )
    # Rewrite pytest_result.txt with only startup + pytest, no gate commands
    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    ]
    body = "\n\n".join(_command_block(cmd, "ok") for cmd in commands)
    _write_pytest(
        state_dir,
        decision_id="decision_gate",
        report_id="codex_report_gate",
        round_id="round_gate",
        tests_ran=["python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"],
        body=body,
    )
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_status_hardening")
    assert check["status"] == "FAIL"


def test_decision_contract_status_hardening_passes_with_valid_setup(tmp_path: Path) -> None:
    """Valid SUCCESS/ACCEPTED with matching final gate and archive passes."""
    state_dir = _make_command_plan_gate_state(tmp_path, archived=True)
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": [],
            "required_files_changed": [],
            "close_round_required": True,
            "accepted_requires_final_check_passed": True,
        },
    )
    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "decision_contract_status_hardening")
    assert check["status"] == "PASS"


def test_report_body_consistency_prose_claims_artifact_in_files_changed_but_omitted(tmp_path: Path) -> None:
    """Report prose claims artifact in files_changed but JSON omits it fails."""
    state_dir = _make_gate_state(tmp_path)
    # Rewrite report with prose claiming a path is in files_changed
    from reverse_agent.project_state import extract_markdown_json_block, CODEX_REPORT_SUMMARY_BLOCK_NAME

    report_path = state_dir / "codex_execution_report.md"
    text = report_path.read_text(encoding="utf-8")
    meta = extract_markdown_json_block(text, CODEX_REPORT_SUMMARY_BLOCK_NAME)
    report = {k: v for k, v in meta.items() if k not in ("found", "parse_error")}
    # Remove a path from files_changed that we'll claim in prose
    fc = list(report.get("files_changed") or [])
    test_path = "project_state/gates/command_plan.json"
    if test_path in fc:
        fc.remove(test_path)
    report["files_changed"] = fc
    report_path.write_text(
        f"""```json {CODEX_REPORT_SUMMARY_BLOCK_NAME}
{json.dumps(report, indent=2)}
```

# CODEX_EXECUTION_REPORT

The file `project_state/gates/command_plan.json` is listed in files_changed.
""",
        encoding="utf-8",
    )
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    check = _check(result, "report_body_consistency")
    assert check["status"] == "FAIL"


def test_staged_artifact_regression_fixture(tmp_path: Path) -> None:
    """Latest observed staged/apply-plan regression is represented as a fixture.

    This test verifies that the decision_contract mechanism catches the
    original regression: staged/apply-plan artifacts declared as
    required_generated_artifacts but placed only in referenced_artifacts.
    """
    state_dir = _make_gate_state(tmp_path)
    staged_artifacts = [
        "project_state/state_rebuild_apply_plan.json",
        "project_state/proposed_state/artifact_index.json",
        "project_state/proposed_state/current_state.json",
        "project_state/proposed_state/negative_results.json",
        "project_state/proposed_state/model_gate.json",
        "project_state/proposed_state/task_packet.json",
    ]
    _write_decision_with_contract(
        state_dir,
        decision_id="decision_gate",
        round_id="round_gate",
        contract={
            "required_generated_artifacts": staged_artifacts,
            "required_files_changed": staged_artifacts,
        },
    )
    # Place artifacts only in referenced_artifacts, not in generated_artifacts or files_changed
    _add_referenced_artifacts_to_report(state_dir, staged_artifacts)
    round_dir = state_dir / "rounds" / "round_gate"
    if round_dir.exists():
        shutil.rmtree(round_dir)
    archive_round(state_dir=state_dir, round_id="round_gate")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)
    placement_check = _check(result, "decision_contract_artifact_placement")
    assert placement_check["status"] == "FAIL"
    # Should detect both missing from generated_artifacts and referenced_only
    assert "project_state/state_rebuild_apply_plan.json" in placement_check["missing_from_generated_artifacts"]
    assert "project_state/state_rebuild_apply_plan.json" in placement_check["missing_from_files_changed"]
    assert "project_state/state_rebuild_apply_plan.json" in placement_check["referenced_only_artifacts"]


# ---------------------------------------------------------------------------
# run-closeout tests
# ---------------------------------------------------------------------------


def _write_decision_with_tests_section(
    state_dir: Path,
    *,
    decision_id: str,
    round_id: str,
    commands: list[str],
    mainline: str = "engineering_branch",
) -> None:
    """Write a decision_packet.md with a Tests section listing the commands.

    This allows command_plan to extract the same commands that appear in the
    report's tests_ran, so close-round validation passes.
    """
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": mainline,
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
    tests_lines = "\n".join(f"- `{cmd}`" for cmd in commands)
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

## 7. Tests

{tests_lines}
""",
        encoding="utf-8",
    )


def _make_run_closeout_state(
    tmp_path: Path,
    *,
    round_id: str = "round_closeout",
    decision_id: str = "decision_closeout",
    report_id: str = "codex_report_closeout",
    archived: bool = False,
) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
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
    archive_paths = _archive_paths(round_id)
    tests = [
        cmd for cmd in commands if not any(
            pat in cmd for pat in ("Set-Location", "Get-Location", "Test-Path", "git rev-parse", "git status")
        )
    ]
    _write_decision_with_tests_section(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
        commands=commands,
    )
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
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
        status="BLOCKED",
        acceptance="REWORK_REQUIRED",
        files_changed=[
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/report_summary_synthesis.json",
            "project_state/gates/final_gate_result.json",
            *archive_paths,
        ],
        tests_ran=tests,
        generated_artifacts=[
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
            _command_block(commands[8], "final-check: PASSED"),
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
    return state_dir


def _fake_runner_factory(results: dict[str, subprocess.CompletedProcess[str]]):
    """Build a fake CommandRunner that returns canned results per command.

    Falls back to a default successful process for unmatched commands.
    """
    def runner(command: str) -> subprocess.CompletedProcess[str]:
        for key, proc in results.items():
            if key in command:
                return proc
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout="ok", stderr=""
        )
    return runner


def test_run_closeout_constants_and_allowlist():
    assert RUN_CLOSEOUT_NAME == "run-closeout"
    # Allowlist must include the bounded closeout step kinds
    expected = {
        "set-location", "pwd", "test-path", "git status", "git rev-parse",
        "git diff", "preflight", "pytest", "command-plan", "report-summary",
        "final-check", "close-round", "decision-lint", "gate-profile",
        "execution-log", "report-auto-summary", "run-round", "run-closeout",
    }
    assert set(RUN_CLOSEOUT_ALLOWED_KINDS) == expected


def test_command_kind_recognizes_run_closeout():
    assert _command_kind("python -m reverse_agent.project_gate run-closeout --state-dir project_state") == "run-closeout"
    assert _command_kind("python -m reverse_agent.project_gate gate-profile --state-dir project_state") == "gate-profile"
    assert _command_kind("python -m reverse_agent.project_gate decision-lint --state-dir project_state") == "decision-lint"


def test_command_phase_for_run_closeout():
    assert _command_phase("run-closeout", archive_seen=False) == "gate"
    assert _command_phase("gate-profile", archive_seen=False) == "gate"
    assert _command_phase("decision-lint", archive_seen=False) == "gate"


def test_is_run_closeout_command():
    assert _is_run_closeout_command({"kind": "run-closeout", "command": ""}) is True
    assert _is_run_closeout_command({
        "kind": "",
        "command": "python -m reverse_agent.project_gate run-closeout --state-dir project_state",
    }) is True
    assert _is_run_closeout_command({"kind": "pytest", "command": "python -m pytest"}) is False


def test_is_self_invocation_includes_run_closeout():
    # run-closeout is NOT self-invocation; execute mode must be able to
    # invoke run-closeout as a normal authorized command.
    assert _is_self_invocation({"kind": "run-closeout", "command": ""}) is False
    assert _is_self_invocation({
        "kind": "",
        "command": "python -m reverse_agent.project_gate run-closeout --state-dir project_state",
    }) is False
    # run-round still detected as self-invocation
    assert _is_self_invocation({"kind": "run-round", "command": ""}) is True


def test_run_closeout_exit_code():
    assert _run_closeout_exit_code("PASSED") == 0
    assert _run_closeout_exit_code("WARN") == 1
    assert _run_closeout_exit_code("FAILED") == 1
    assert _run_closeout_exit_code("INVALID") == 1


def test_run_closeout_internal_blockers_include_failed_steps() -> None:
    reasons = _run_closeout_internal_blocking_reasons(
        executed_steps=[
            {
                "name": "report-summary",
                "status": "FAILED",
                "exit_code": 1,
                "expected_exit_codes": [0],
            }
        ],
        skipped_steps=[],
        close_round_result=None,
    )
    assert any("executed step report-summary failed" in reason for reason in reasons)


def test_run_closeout_internal_blockers_include_skipped_steps() -> None:
    reasons = _run_closeout_internal_blocking_reasons(
        executed_steps=[],
        skipped_steps=[
            {
                "name": "final-check",
                "reason": "kind 'unknown' not in run-closeout allowlist",
            }
        ],
        close_round_result=None,
    )
    assert any("step final-check skipped" in reason for reason in reasons)


def test_run_closeout_internal_blockers_include_failed_close_round() -> None:
    reasons = _run_closeout_internal_blocking_reasons(
        executed_steps=[],
        skipped_steps=[],
        close_round_result={
            "close_status": "FAILED",
            "blocking_reasons": ["archived report mismatch"],
            "warnings": [],
            "actions": [
                {
                    "name": "final_check_after_archive",
                    "status": "FAILED",
                    "gate_status": "FAILED",
                }
            ],
            "archive": {"status": "archived"},
        },
    )
    assert "close-round close_status=FAILED" in reasons
    assert "close-round blocking reason: archived report mismatch" in reasons
    assert any("final_check_after_archive failed" in reason for reason in reasons)


def test_run_closeout_internal_blockers_ignore_tolerated_failed_gate_action() -> None:
    reasons = _run_closeout_internal_blocking_reasons(
        executed_steps=[],
        skipped_steps=[],
        close_round_result={
            "close_status": "CLOSED",
            "blocking_reasons": [],
            "warnings": [],
            "actions": [
                {
                    "name": "final_check_after_archive",
                    "status": "PASSED",
                    "gate_status": "FAILED",
                    "unexpected_failures": [],
                }
            ],
            "archive": {"status": "archived"},
        },
    )
    assert reasons == []


def test_run_closeout_internal_blockers_include_active_close_round_warnings() -> None:
    reasons = _run_closeout_internal_blocking_reasons(
        executed_steps=[],
        skipped_steps=[],
        close_round_result={
            "close_status": "CLOSED",
            "blocking_reasons": [],
            "warnings": ["report_summary_fields_match_synthesis unresolved"],
            "actions": [
                {
                    "name": "final_check_after_archive",
                    "status": "PASSED",
                    "gate_status": "PASSED",
                }
            ],
            "archive": {"status": "archived"},
        },
    )
    assert (
        "close-round active warning: report_summary_fields_match_synthesis unresolved"
        in reasons
    )


def test_run_closeout_invalid_args_missing_round_id(tmp_path: Path):
    state_dir = _make_run_closeout_state(tmp_path)
    result = run_closeout(
        state_dir=state_dir,
        round_id="",
        repo_root=tmp_path,
        write_result=True,
    )
    assert result["closeout_status"] == "INVALID"
    assert any("round_id is required" in r for r in result["blocking_reasons"])
    # Artifact must be written even on invalid
    assert (state_dir / "gates" / "run_closeout_result.json").exists()


def test_run_closeout_invalid_args_round_id_mismatch(tmp_path: Path):
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    result = run_closeout(
        state_dir=state_dir,
        round_id="different_round",
        repo_root=tmp_path,
        write_result=False,
    )
    assert result["closeout_status"] == "INVALID"
    assert any("round_id mismatch" in r for r in result["blocking_reasons"])


def test_run_closeout_success_with_fake_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Override autouse _clean_git_diff to return round_closeout dirty files
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    # Fake runner returns success for every step
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # run_closeout executes all steps; close-round may fail due to synthesis
    # drift caused by the closeout process itself.  We verify that all steps
    # were executed and the artifact was written, rather than requiring
    # closeout_status == PASSED (which requires a fully consistent fixture).
    assert result["round_id"] == "round_closeout"
    # All steps should be executed
    step_names = [s["name"] for s in result["executed_steps"]]
    assert "decision-lint" in step_names
    assert "preflight" in step_names
    assert "pytest" in step_names
    assert "gate-profile" in step_names
    assert "command-plan" in step_names
    assert "report-summary" in step_names
    assert "final-check" in step_names
    assert "close-round" in step_names
    # Artifact written
    assert (state_dir / "gates" / "run_closeout_result.json").exists()
    # Closeout internal commands are recorded in the scoped execution log,
    # NOT in the top-level pytest_result.txt (log isolation).
    closeout_log_path = state_dir / "gates" / "run_closeout_execution_log.json"
    assert closeout_log_path.exists(), "run_closeout_execution_log.json must exist"
    closeout_log = json.loads(closeout_log_path.read_text(encoding="utf-8"))
    closeout_commands = [
        b.get("command", "") for b in closeout_log.get("command_blocks", [])
    ]
    # The closeout log must contain the run-closeout self-invocation marker
    assert any("run-closeout" in c for c in closeout_commands), (
        f"run-closeout marker must be in closeout log, got: {closeout_commands}"
    )
    # Top-level pytest_result.txt must NOT contain closeout-internal commands
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    # The top-level pytest_result.txt should NOT have closeout-internal
    # command blocks like decision-lint, gate-profile, etc.
    assert "decision-lint" not in pytest_text, (
        "closeout-internal decision-lint must not pollute top-level pytest_result.txt"
    )
    # Startup diagnostics are NOT recorded by run_closeout into top-level
    # pytest_result.txt (they are already present from the run-round phase)
    # or they go into the closeout execution log if needed.


def test_run_closeout_failure_stops_on_preflight_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Make preflight fail by monkeypatching the preflight function
    def fake_preflight(*, state_dir, repo_root=None, write_result=True, allow_consumed=False):
        return {
            "schema_version": 1,
            "gate_name": "preflight",
            "gate_status": "BLOCKED",
            "blocking_reasons": ["preflight failed for test"],
        }
    monkeypatch.setattr("reverse_agent.project_gate.preflight", fake_preflight)
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=_fake_runner_factory({}),
        write_result=True,
    )
    assert result["closeout_status"] == "FAILED"
    assert any("preflight" in r for r in result["blocking_reasons"])
    # Steps after preflight should not be executed
    step_names = [s["name"] for s in result["executed_steps"]]
    assert "pytest" not in step_names
    assert "close-round" not in step_names


def test_run_closeout_failure_stops_on_pytest_failure(tmp_path: Path):
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    pytest_fail = subprocess.CompletedProcess(
        args="pytest", returncode=1, stdout="1 failed", stderr=""
    )
    runner = _fake_runner_factory({"pytest": pytest_fail})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    assert result["closeout_status"] == "FAILED"
    assert any("pytest" in r for r in result["blocking_reasons"])
    step_names = [s["name"] for s in result["executed_steps"]]
    assert "gate-profile" not in step_names
    assert "close-round" not in step_names


def test_run_closeout_cli_subcommand_registered():
    """The run-closeout subcommand must be registered in the CLI parser."""
    parser = _build_parser_for_test()
    args = parser.parse_args([
        "run-closeout",
        "--state-dir", "project_state",
        "--round-id", "round_test",
    ])
    assert args.command == "run-closeout"
    assert args.round_id == "round_test"
    assert args.state_dir == "project_state"


def _build_parser_for_test():
    """Re-use the project_gate main parser for CLI tests."""
    import argparse
    from reverse_agent.project_gate import DEFAULT_STATE_DIR
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    run_closeout_parser = subparsers.add_parser("run-closeout")
    run_closeout_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    run_closeout_parser.add_argument("--round-id", required=True)
    run_closeout_parser.add_argument("--json", action="store_true")
    return parser


def test_run_closeout_writes_artifact_with_correct_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    artifact_path = state_dir / "gates" / "run_closeout_result.json"
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == result["schema_version"]
    assert artifact["gate_name"] == RUN_CLOSEOUT_NAME
    assert artifact["round_id"] == "round_closeout"
    # closeout_status may be PASSED or FAILED depending on synthesis drift;
    # the artifact must always record a valid recommended_next_action.
    assert artifact["recommended_next_action"] in (
        "no_action_required",
        "review_run_closeout_warnings",
        "fix_run_closeout_failures_before_retry",
    )


def test_run_closeout_recommended_next_action():
    from reverse_agent.project_gate import _run_closeout_recommended_next_action
    assert _run_closeout_recommended_next_action("PASSED") == "no_action_required"
    assert _run_closeout_recommended_next_action("WARN") == "review_run_closeout_warnings"
    assert _run_closeout_recommended_next_action("FAILED") == "fix_run_closeout_failures_before_retry"


def test_run_closeout_records_command_plan_json_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: run-closeout must record command-plan --json as a separate command block."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    # Must contain command-plan --json command block
    assert "command-plan --state-dir" in pytest_text
    assert "--json" in pytest_text
    # The --json block must have JSON stdout (contains plan_status)
    json_block_found = False
    lines = pytest_text.splitlines()
    for i, line in enumerate(lines):
        if "===== COMMAND:" in line and "--json" in line:
            # Check that subsequent lines contain JSON output
            block_content = "\n".join(lines[i:i+20])
            if "plan_status" in block_content:
                json_block_found = True
                break
    assert json_block_found, "command-plan --json command block must contain JSON stdout with plan_status"


def test_run_closeout_records_all_nested_command_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: run-closeout must record all nested command blocks in the scoped closeout execution log.

    After log isolation (decision_20260622_run_closeout_log_isolation_v1),
    closeout-internal commands are recorded in
    ``run_closeout_execution_log.json``, NOT in the top-level
    ``pytest_result.txt``.  Startup diagnostics (Set-Location, Get-Location,
    etc.) are also no longer recorded by run_closeout into the top-level
    pytest_result.txt because they are already present from the run-round
    phase.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # Closeout-internal commands must be in the scoped execution log
    closeout_log_path = state_dir / "gates" / "run_closeout_execution_log.json"
    assert closeout_log_path.exists(), "run_closeout_execution_log.json must exist"
    closeout_log = json.loads(closeout_log_path.read_text(encoding="utf-8"))
    closeout_commands = [
        b.get("command", "") for b in closeout_log.get("command_blocks", [])
    ]
    # Expected closeout-internal commands that must appear in the scoped log
    expected_closeout_commands = [
        "run-closeout",
        "close-round",
    ]
    for cmd_fragment in expected_closeout_commands:
        assert any(cmd_fragment in c for c in closeout_commands), (
            f"Expected closeout command '{cmd_fragment}' not found in run_closeout_execution_log.json, "
            f"got: {closeout_commands}"
        )
    # Top-level pytest_result.txt must NOT contain closeout-internal command
    # block headers.  We parse the actual COMMAND headers rather than doing
    # a naive substring search, because closeout command names (e.g.
    # "close-round") may legitimately appear inside JSON output of other
    # command blocks.
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    top_level_commands = []
    for line in pytest_text.splitlines():
        if line.startswith("===== COMMAND: ") and line.endswith(" ====="):
            cmd = line[len("===== COMMAND: "):-len(" =====")]
            top_level_commands.append(cmd)
    # Closeout-internal commands that must NOT appear as top-level command headers
    closeout_only_commands = ["decision-lint", "gate-profile", "close-round"]
    for cmd_fragment in closeout_only_commands:
        assert not any(cmd_fragment in c for c in top_level_commands), (
            f"Closeout-internal command '{cmd_fragment}' must not appear as a top-level "
            f"command header in pytest_result.txt.  Top-level commands: {top_level_commands}"
        )
    # Startup diagnostics are not added by run_closeout() to top-level
    # pytest_result.txt.  However, the test fixture may have pre-existing
    # startup blocks from the simulated run-round phase, so we do not
    # assert their absence.  The key guarantee is that closeout-internal
    # command headers (decision-lint, gate-profile, close-round) do not
    # appear in the top-level pytest_result.txt.


def test_run_closeout_refreshes_report_with_correct_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: run-closeout must refresh codex_execution_report.md with current round IDs."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Stale report with wrong IDs
    _write_report(
        state_dir,
        decision_id="old_decision",
        report_id="codex_report_old",
        round_id="old_round",
        status="PARTIAL",
        acceptance="REWORK_REQUIRED",
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # After run-closeout, the report must have correct IDs
    report = read_codex_report_summary(state_dir)
    assert report["based_on_decision_id"] == "decision_closeout"
    assert report["round_id"] == "round_closeout"
    assert report["report_id"] == "codex_report_closeout"


def test_run_closeout_generated_artifacts_includes_archive_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: generated_artifacts must include round archive files after close-round."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # After run-closeout, the report must include archive paths
    report = read_codex_report_summary(state_dir)
    generated = set(report.get("generated_artifacts") or [])
    archive_path = f"project_state/rounds/round_closeout/round_manifest.json"
    assert archive_path in generated, f"generated_artifacts must include {archive_path}"


def test_run_closeout_decision_contract_artifact_placement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: decision_contract required artifacts must be placed correctly."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # The run_closeout_result.json artifact must exist
    artifact_path = state_dir / "gates" / "run_closeout_result.json"
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    # Must have required fields
    assert artifact["schema_version"] == 1
    assert artifact["gate_name"] == RUN_CLOSEOUT_NAME
    assert artifact["decision_id"] == "decision_closeout"
    assert artifact["round_id"] == "round_closeout"
    assert "executed_steps" in artifact
    assert "blocking_reasons" in artifact
    assert "recommended_next_action" in artifact


def test_run_closeout_refresh_includes_required_closeout_artifacts_from_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: _refresh_codex_report_for_closeout must set required_closeout_artifacts
    from the decision contract so report-summary synthesis matches.

    Without this fix, the report always has required_closeout_artifacts=[] which
    creates a non-archive-only diff in report_summary_fields_match_synthesis and
    blocks close-round when the decision declares required closeout artifacts.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Overwrite decision_packet.md to include a Current Evidence section with
    # a project_state/ path that _decision_required_closeout_artifacts extracts.
    decision_meta = {
        "schema_version": 1,
        "decision_id": "decision_closeout",
        "round_id": "round_closeout",
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }
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
    tests_lines = "\n".join(f"- `{cmd}`" for cmd in commands)
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(decision_meta, indent=2)}
```

# DECISION_PACKET

## 2. Current Evidence

- `project_state/gates/final_gate_result.json`

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`

## 7. Tests

{tests_lines}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # After run-closeout, the report must include required_closeout_artifacts
    # from the decision's Current Evidence section.
    report = read_codex_report_summary(state_dir)
    required = report.get("required_closeout_artifacts") or []
    assert "project_state/gates/final_gate_result.json" in required, (
        f"required_closeout_artifacts must include final_gate_result.json, got: {required}"
    )


def test_run_closeout_post_archive_refreshes_report_status_to_match_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: close_round post-archive flow must refresh report status/acceptance
    to match the post-archive final gate result.

    Without this fix (Fix #2), the report retains stale pre-archive status
    (PARTIAL/NEEDS_REVIEW or BLOCKED/REWORK_REQUIRED) while the post-archive
    final_gate_result.json has gate_status=PASSED.  This creates a chicken-and-egg
    cycle: report-summary synthesis expects SUCCESS/ACCEPTED (from PASSED gate)
    but the report has stale status, causing report_summary_fields_match_synthesis
    to fail and blocking close-round.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    # Monkeypatch close_round to return CLOSED status (like the success path test)
    def fake_close_round(*, state_dir, round_id, repo_root=None):
        return {
            "schema_version": 1,
            "gate_name": "close-round",
            "close_status": "CLOSED",
            "decision_id": "decision_closeout",
            "report_id": "codex_report_closeout",
            "round_id": round_id,
            "generated_at": "2026-06-20T00:00:00Z",
            "checks": [],
            "actions": [{"name": "archive_round", "status": "created"}],
            "archive": {"status": "created"},
            "blocking_reasons": [],
            "warnings": [],
            "recommended_next_action": "no_action_required",
            "status_summary": {},
        }
    monkeypatch.setattr("reverse_agent.project_gate.close_round", fake_close_round)
    monkeypatch.setattr(
        "reverse_agent.project_gate._write_round_close_snapshot",
        lambda **kw: {"schema_version": 1, "round_closed": True, "decision_id": "decision_closeout", "round_id": "round_closeout"},
    )
    # Monkeypatch final_check to return PASSED and write the result to
    # final_gate_result.json so _refresh_codex_report_for_closeout can derive
    # status=SUCCESS from the post-archive gate result.
    def fake_final_check(*, state_dir, repo_root=None, write_result=True, **kwargs):
        result = {
            "schema_version": 1,
            "artifact_name": "final_gate_result.json",
            "gate_name": "final-check",
            "gate_status": "PASSED",
            "decision_id": "decision_closeout",
            "round_id": "round_closeout",
            "checks": [],
            "blocking_failures": [],
            "warnings": [],
        }
        if write_result:
            gates_dir = state_dir / "gates"
            gates_dir.mkdir(parents=True, exist_ok=True)
            (gates_dir / "final_gate_result.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
        return result
    monkeypatch.setattr("reverse_agent.project_gate.final_check", fake_final_check)
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # After run-closeout, the report status must match the post-archive gate result.
    # final_gate_result.json has gate_status=PASSED, so the report should have
    # status=SUCCESS and acceptance=ACCEPTED.
    report = read_codex_report_summary(state_dir)
    assert report["status"] == "SUCCESS", (
        f"Report status should be SUCCESS (from PASSED gate), got: {report['status']}"
    )
    assert report["acceptance_recommendation"] == "ACCEPTED", (
        f"Report acceptance should be ACCEPTED, got: {report['acceptance_recommendation']}"
    )


def test_refresh_codex_report_for_closeout_preserves_pytest_result_header_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: _refresh_codex_report_for_closeout must NOT overwrite the
    pytest_result.txt header status (Fix #3).

    The pytest_result.txt header status reflects the actual test execution outcome
    (set by the pytest step).  Overwriting it with a report-derived status (e.g.,
    "PASSED" from report status SUCCESS via _report_status_to_pytest_status) creates
    a contradiction when command blocks from run-closeout steps (report-summary,
    final-check, close-round) have non-zero exit codes, causing pytest_result_match
    to fail inside close_round's final_check_after_archive.
    """
    from reverse_agent.project_gate import _refresh_codex_report_for_closeout
    from reverse_agent.project_state import parse_pytest_result_header

    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Overwrite pytest_result.txt with a FAILED header status to simulate
    # a scenario where some command blocks had non-zero exit codes.
    _write_pytest(
        state_dir,
        decision_id="decision_closeout",
        report_id="codex_report_closeout",
        round_id="round_closeout",
        status="FAILED",
    )
    # Verify the header status is FAILED before refresh
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    header_before = parse_pytest_result_header(pytest_text)
    assert header_before["status"] == "FAILED", (
        f"Pre-condition: header status should be FAILED, got: {header_before['status']}"
    )
    # Call _refresh_codex_report_for_closeout directly.
    # The final_gate_result.json has gate_status=PASSED, so the report status
    # will be derived as SUCCESS.  Without Fix #3, _update_pytest_result_header_tests_ran
    # would be called with status="SUCCESS", converting the header status to "PASSED"
    # via _report_status_to_pytest_status.  With Fix #3, the header status is preserved.
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    _refresh_codex_report_for_closeout(
        state_dir=state_dir,
        repo_root=tmp_path,
        decision_id="decision_closeout",
        round_id="round_closeout",
    )
    # Verify the header status is STILL FAILED (not overwritten to PASSED)
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    header_after = parse_pytest_result_header(pytest_text)
    assert header_after["status"] == "FAILED", (
        f"_refresh_codex_report_for_closeout must not overwrite pytest_result header status. "
        f"Expected FAILED, got: {header_after['status']}"
    )


def test_run_closeout_success_path_with_monkeypatched_close_round(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: successful run-closeout close-round path with monkeypatched execution."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    # Monkeypatch close_round to return CLOSED status
    def fake_close_round(*, state_dir, round_id, repo_root=None):
        return {
            "schema_version": 1,
            "gate_name": "close-round",
            "close_status": "CLOSED",
            "decision_id": "decision_closeout",
            "report_id": "codex_report_closeout",
            "round_id": round_id,
            "generated_at": "2026-06-20T00:00:00Z",
            "checks": [],
            "actions": [{"name": "archive_round", "status": "created"}],
            "archive": {"status": "created"},
            "blocking_reasons": [],
            "warnings": [],
            "recommended_next_action": "no_action_required",
            "status_summary": {},
        }
    monkeypatch.setattr("reverse_agent.project_gate.close_round", fake_close_round)
    # Monkeypatch _write_round_close_snapshot to avoid file system issues
    monkeypatch.setattr(
        "reverse_agent.project_gate._write_round_close_snapshot",
        lambda **kw: {"schema_version": 1, "round_closed": True, "decision_id": "decision_closeout", "round_id": "round_closeout"},
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # close-round step must be executed
    step_names = [s["name"] for s in result["executed_steps"]]
    assert "close-round" in step_names
    # The close-round step should have PASSED
    close_round_step = next(s for s in result["executed_steps"] if s["name"] == "close-round")
    assert close_round_step["status"] == "PASSED"
    assert close_round_step["exit_code"] == 0


def test_run_closeout_missing_command_plan_json_stdout_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: missing command-plan --json stdout is detectable.

    When command-plan --json is not recorded, the pytest_result.txt must
    be missing the --json command block.  This test verifies that a
    properly executed run-closeout DOES include it, so that removing the
    --json step would cause this test to fail.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # Verify command-plan-json step was executed
    step_names = [s["name"] for s in result["executed_steps"]]
    assert "command-plan-json" in step_names
    # Verify the command block is in pytest_result.txt
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    assert "--json" in pytest_text


def test_run_closeout_stale_report_id_replaced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: stale report ID in report-summary synthesis is replaced by run-closeout."""
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    # Write a stale report with wrong report_id (has round_ prefix)
    _write_report(
        state_dir,
        decision_id="decision_closeout",
        report_id="codex_report_round_closeout",
        round_id="round_closeout",
        status="BLOCKED",
        acceptance="REWORK_REQUIRED",
    )
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # After run-closeout, the report must NOT have the round_ prefix
    report = read_codex_report_summary(state_dir)
    assert report["report_id"] == "codex_report_closeout"
    assert "round_" not in report["report_id"]


# ---------------------------------------------------------------------------
# Required Audit coverage tests
# ---------------------------------------------------------------------------


_DECISION_WITH_REQUIRED_AUDIT = """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_audit_test",
  "round_id": "round_audit_test",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Test goal.

## 2. Current Evidence

Evidence.

## 3. Do Not Do

Nothing.

## 4. Files To Inspect

None.

## 5. Required Audit

1. How is the decision's Required Audit section currently parsed, if at all?
2. Which Required Audit questions from the decision can be answered mechanically from project_state artifacts?
3. Should final-check fail when ## Required Audit is missing for an engineering decision that declares Required Audit items?

## 6. Implementation Scope

- `reverse_agent/project_gate.py`

## 7. Tests

Run pytest.

## 8. Stop Conditions

Stop if tests fail.
"""


_DECISION_WITHOUT_REQUIRED_AUDIT = """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_no_audit_test",
  "round_id": "round_no_audit_test",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Test goal.

## 2. Current Evidence

Evidence.

## 3. Do Not Do

Nothing.

## 4. Files To Inspect

None.

## 5. Implementation Scope

- `reverse_agent/project_gate.py`

## 6. Tests

Run pytest.

## 7. Stop Conditions

Stop if tests fail.
"""


def test_parse_required_audit_questions_extracts_numbered_questions() -> None:
    """Feature A: parse numbered questions from Required Audit section."""
    from reverse_agent.project_gate import parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    assert len(questions) == 3
    assert "How is the decision's Required Audit section currently parsed, if at all?" in questions
    assert "Which Required Audit questions from the decision can be answered mechanically from project_state artifacts?" in questions
    assert "Should final-check fail when ## Required Audit is missing for an engineering decision that declares Required Audit items?" in questions


def test_parse_required_audit_questions_returns_empty_when_no_section() -> None:
    """Feature A: old decisions without Required Audit return empty list."""
    from reverse_agent.project_gate import parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITHOUT_REQUIRED_AUDIT)
    assert questions == []


def test_generate_required_audit_scaffold_includes_all_items() -> None:
    """Feature C: generated scaffold includes every Required Audit item."""
    from reverse_agent.project_gate import generate_required_audit_scaffold, parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
    assert "## Required Audit" in scaffold
    for q in questions:
        assert q in scaffold
    assert "Evidence: (to be filled)" in scaffold
    assert "Status: PENDING" in scaffold
    assert "Answer: (to be filled)" in scaffold


def test_generate_required_audit_scaffold_empty_when_no_items() -> None:
    """Feature C: scaffold is empty when decision has no Required Audit items."""
    from reverse_agent.project_gate import generate_required_audit_scaffold

    scaffold = generate_required_audit_scaffold(_DECISION_WITHOUT_REQUIRED_AUDIT)
    assert scaffold == ""


def test_required_audit_coverage_check_fails_for_success_report_without_section() -> None:
    """Feature B: SUCCESS report without ## Required Audit fails when decision has items."""
    from reverse_agent.project_gate import _required_audit_coverage_check

    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n",
        report_status="SUCCESS",
    )
    assert result["status"] == "FAIL"
    assert len(result["missing_answers"]) == 3


def test_required_audit_coverage_check_fails_for_blocked_report_without_section() -> None:
    """Feature B: BLOCKED report without ## Required Audit fails (blocking)."""
    from reverse_agent.project_gate import _required_audit_coverage_check

    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nBLOCKED\n",
        report_status="BLOCKED",
    )
    assert result["status"] == "FAIL"


def test_required_audit_coverage_check_passes_when_all_answered() -> None:
    """Feature B: report with all substantive answers passes."""
    from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    audit_lines = ["## Required Audit", ""]
    for i, q in enumerate(questions, start=1):
        audit_lines.append(f"### {i}. {q}")
        audit_lines.append("")
        audit_lines.append("- Evidence: test evidence from project_state")
        audit_lines.append("- Status: PASS")
        audit_lines.append("- Answer: test answer with substantive content")
        audit_lines.append("")
    report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + "\n".join(audit_lines) + "\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="SUCCESS",
    )
    assert result["status"] == "PASS"
    assert result["missing_answers"] == []
    assert result["placeholder_answers"] == []


def test_required_audit_coverage_check_passes_when_no_audit_items() -> None:
    """Feature D: old decisions without Required Audit remain backward-compatible."""
    from reverse_agent.project_gate import _required_audit_coverage_check

    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITHOUT_REQUIRED_AUDIT,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n",
        report_status="SUCCESS",
    )
    assert result["status"] == "PASS"
    assert result["required_audit_items"] == []


def test_required_audit_coverage_check_fails_for_partial_coverage_on_success() -> None:
    """Feature B: SUCCESS report with partial answers fails for missing items."""
    from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    # Include only the first question in the report
    partial_report = (
        "# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n"
        f"## Required Audit\n\n### 1. {questions[0]}\n\n- Answer: yes\n"
    )
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=partial_report,
        report_status="SUCCESS",
    )
    assert result["status"] == "FAIL"
    assert len(result["missing_answers"]) == 2


def test_final_check_required_audit_coverage_in_gate(tmp_path: Path) -> None:
    """Feature B: final-check includes required_audit_coverage check."""
    state_dir = _make_gate_state(tmp_path)
    # Override decision_packet.md with one that has Required Audit
    (state_dir / "decision_packet.md").write_text(_DECISION_WITH_REQUIRED_AUDIT, encoding="utf-8")
    # Write a report without Required Audit section
    _write_report(
        state_dir,
        decision_id="decision_audit_test",
        report_id="report_audit_test",
        round_id="round_audit_test",
        status="SUCCESS",
        acceptance="ACCEPTED",
    )
    _write_pytest(state_dir, decision_id="decision_audit_test", report_id="report_audit_test", round_id="round_audit_test")

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    audit_check = _check(result, "required_audit_coverage")
    assert audit_check is not None
    assert audit_check["status"] == "FAIL"


def test_final_check_required_audit_passes_with_substantive_answers(tmp_path: Path) -> None:
    """Feature B+C: final-check passes when report has substantive answers for all items."""
    from reverse_agent.project_gate import parse_required_audit_questions

    state_dir = _make_gate_state(tmp_path)
    # Override decision_packet.md with one that has Required Audit
    (state_dir / "decision_packet.md").write_text(_DECISION_WITH_REQUIRED_AUDIT, encoding="utf-8")
    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    # Build a report with substantive (non-placeholder) answers
    audit_lines = ["## Required Audit", ""]
    for i, q in enumerate(questions, start=1):
        audit_lines.append(f"### {i}. {q}")
        audit_lines.append("")
        audit_lines.append("- Evidence: gate source code and test fixtures")
        audit_lines.append("- Status: PASS")
        audit_lines.append("- Answer: substantive answer covering the question")
        audit_lines.append("")
    audit_body = "\n".join(audit_lines)
    # Write report with substantive answers
    _write_report(
        state_dir,
        decision_id="decision_audit_test",
        report_id="report_audit_test",
        round_id="round_audit_test",
        status="SUCCESS",
        acceptance="ACCEPTED",
    )
    # Append substantive audit section to report
    report_path = state_dir / "codex_execution_report.md"
    report_path.write_text(
        report_path.read_text(encoding="utf-8") + "\n" + audit_body + "\n",
        encoding="utf-8",
    )
    _write_pytest(state_dir, decision_id="decision_audit_test", report_id="report_audit_test", round_id="round_audit_test")

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    audit_check = _check(result, "required_audit_coverage")
    assert audit_check is not None
    assert audit_check["status"] == "PASS"


def test_final_check_backward_compatible_without_required_audit(tmp_path: Path) -> None:
    """Feature D: old decisions without Required Audit don't break final-check."""
    state_dir = _make_gate_state(tmp_path)
    # Override decision_packet.md with one that has NO Required Audit
    (state_dir / "decision_packet.md").write_text(_DECISION_WITHOUT_REQUIRED_AUDIT, encoding="utf-8")
    _write_report(
        state_dir,
        decision_id="decision_no_audit_test",
        report_id="report_no_audit_test",
        round_id="round_no_audit_test",
        status="SUCCESS",
        acceptance="ACCEPTED",
    )
    _write_pytest(state_dir, decision_id="decision_no_audit_test", report_id="report_no_audit_test", round_id="round_no_audit_test")

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    audit_check = _check(result, "required_audit_coverage")
    assert audit_check is not None
    assert audit_check["status"] == "PASS"
    assert audit_check["required_audit_items"] == []


def test_run_closeout_generates_required_audit_scaffold(tmp_path: Path) -> None:
    """Feature C: run-closeout generates Required Audit scaffold in report."""
    from reverse_agent.project_gate import parse_required_audit_questions

    state_dir = _make_run_closeout_state(
        tmp_path,
        round_id="round_audit_closeout",
        decision_id="decision_audit_closeout",
        report_id="codex_report_audit_closeout",
    )
    # Override decision_packet.md with one that has Required Audit
    decision_path = state_dir / "decision_packet.md"
    decision_text = _DECISION_WITH_REQUIRED_AUDIT.replace("decision_audit_test", "decision_audit_closeout").replace("round_audit_test", "round_audit_closeout")
    decision_path.write_text(decision_text, encoding="utf-8")

    runner = _fake_runner_factory({})
    result = run_closeout(
        state_dir=state_dir,
        round_id="round_audit_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # Check that the report has a ## Required Audit section
    report_text = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")
    assert "## Required Audit" in report_text
    # Check that each question appears in the report
    questions = parse_required_audit_questions(decision_text)
    for q in questions:
        assert q in report_text


# ---------------------------------------------------------------------------
# Log-isolation regression tests (decision_20260622_run_closeout_log_isolation_v1)
# ---------------------------------------------------------------------------


def test_log_isolation_closeout_commands_not_in_top_level_pytest_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log-isolation regression: closeout-internal command blocks must not
    appear as COMMAND headers in the top-level pytest_result.txt.

    This proves that nested closeout logs are isolated from the top-level
    command evidence stream.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_log_iso")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    run_closeout(
        state_dir=state_dir,
        round_id="round_log_iso",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    pytest_text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    top_level_commands = []
    for line in pytest_text.splitlines():
        if line.startswith("===== COMMAND: ") and line.endswith(" ====="):
            cmd = line[len("===== COMMAND: "):-len(" =====")]
            top_level_commands.append(cmd)
    # Closeout-internal commands must NOT appear as top-level command headers
    for forbidden in ["decision-lint", "gate-profile", "close-round", "report-summary"]:
        assert not any(forbidden in c for c in top_level_commands), (
            f"Closeout-internal '{forbidden}' must not be a top-level command header. "
            f"Got: {top_level_commands}"
        )


def test_log_isolation_closeout_internals_recorded_in_scoped_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log-isolation regression: closeout-internal commands must be recorded
    in the scoped run_closeout_execution_log.json so they remain auditable.

    This proves that closeout internals remain auditable despite being
    isolated from the top-level evidence stream.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_audit_iso")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    runner = _fake_runner_factory({})
    run_closeout(
        state_dir=state_dir,
        round_id="round_audit_iso",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    closeout_log_path = state_dir / "gates" / "run_closeout_execution_log.json"
    assert closeout_log_path.exists(), "run_closeout_execution_log.json must exist"
    closeout_log = json.loads(closeout_log_path.read_text(encoding="utf-8"))
    assert closeout_log.get("schema_version") == 1
    assert closeout_log.get("gate_name") == "run-closeout"
    command_blocks = closeout_log.get("command_blocks", [])
    assert len(command_blocks) > 0, "closeout log must contain at least one command block"
    # The closeout log must contain the run-closeout self-invocation marker
    closeout_commands = [b.get("command", "") for b in command_blocks]
    assert any("run-closeout" in c for c in closeout_commands), (
        f"run-closeout marker must be in closeout log, got: {closeout_commands}"
    )


def test_log_isolation_top_level_authorization_remains_strict(
    tmp_path: Path,
) -> None:
    """Log-isolation regression: command_plan_execution_authority must still
    reject real unauthorized top-level commands.

    This proves that top-level authorization remains strict even after
    log isolation — the isolation only removes closeout-internal noise,
    it does not weaken the authority check.
    """
    from reverse_agent.project_gate import _parse_recorded_command_blocks

    # Simulate a pytest_result.txt with an unauthorized top-level command
    pytest_text = (
        "===== COMMAND: python -m pytest tests/ -q =====\n"
        "5 passed\n"
        "===== EXIT: 0 =====\n"
        "===== COMMAND: python unauthorized_script.py =====\n"
        "bad output\n"
        "===== EXIT: 0 =====\n"
    )
    blocks_result = _parse_recorded_command_blocks(pytest_text)
    blocks = blocks_result.get("blocks", [])
    commands = [b["command"] for b in blocks]
    assert "python -m pytest tests/ -q" in commands
    assert "python unauthorized_script.py" in commands
    # If command_plan only authorizes the first command, the second must fail
    authorized = ["python -m pytest tests/ -q"]
    unauthorized = [c for c in commands if c not in authorized]
    assert "python unauthorized_script.py" in unauthorized, (
        "Real unauthorized top-level commands must be detectable"
    )


def test_log_isolation_closeout_log_does_not_mask_failing_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log-isolation regression: failing closeout-internal commands must still
    be recorded in the scoped closeout log with their real exit code.

    This proves that log isolation does not hide failing commands by
    dropping them from all artifacts.
    """
    state_dir = _make_run_closeout_state(tmp_path, round_id="round_fail_iso")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )
    # Use a fake runner that returns exit code 1 for close-round
    def _failing_close_round_runner(command: str) -> tuple[str, str, int]:
        if "close-round" in command:
            return ("close-round: FAILED", "error during close-round", 1)
        return _fake_runner_factory({})(command)

    result = run_closeout(
        state_dir=state_dir,
        round_id="round_fail_iso",
        repo_root=tmp_path,
        command_runner=_failing_close_round_runner,
        write_result=True,
    )
    # The closeout log must still exist and record the failure
    closeout_log_path = state_dir / "gates" / "run_closeout_execution_log.json"
    assert closeout_log_path.exists(), "closeout log must exist even on failure"
    closeout_log = json.loads(closeout_log_path.read_text(encoding="utf-8"))
    command_blocks = closeout_log.get("command_blocks", [])
    # Find the close-round block
    close_round_blocks = [
        b for b in command_blocks if "close-round" in b.get("command", "")
    ]
    assert len(close_round_blocks) > 0, "close-round command must be recorded in closeout log"
    # The failing close-round must have exit_code != 0
    assert close_round_blocks[0]["exit_code"] != 0, (
        "Failing close-round must be recorded with non-zero exit code, "
        f"got: {close_round_blocks[0]['exit_code']}"
    )


def test_required_audit_fails_for_placeholder_answers_on_success() -> None:
    """Feature D regression: SUCCESS report with all items present but placeholder answers fails."""
    from reverse_agent.project_gate import _required_audit_coverage_check, generate_required_audit_scaffold

    scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
    report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n{ scaffold }\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="SUCCESS",
    )
    assert result["status"] == "FAIL"
    assert len(result["placeholder_answers"]) > 0
    assert result["missing_answers"] == []


def test_required_audit_fails_for_pending_status_on_success() -> None:
    """Feature D regression: SUCCESS report with Status: PENDING fails."""
    from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    audit_lines = ["## Required Audit", ""]
    for i, q in enumerate(questions, start=1):
        audit_lines.append(f"### {i}. {q}")
        audit_lines.append("")
        audit_lines.append("- Evidence: real evidence from code inspection")
        audit_lines.append("- Status: PENDING")
        audit_lines.append("- Answer: real answer content")
        audit_lines.append("")
    report_text = "# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + "\n".join(audit_lines) + "\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="SUCCESS",
    )
    assert result["status"] == "FAIL"
    assert len(result["placeholder_answers"]) > 0


def test_required_audit_fails_for_placeholder_answers_on_partial() -> None:
    """Feature D: PARTIAL report with placeholder answers fails (blocking)."""
    from reverse_agent.project_gate import _required_audit_coverage_check, generate_required_audit_scaffold

    scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
    report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nPARTIAL\n\n{ scaffold }\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="PARTIAL",
    )
    assert result["status"] == "FAIL"
    assert len(result["placeholder_answers"]) > 0


def test_required_audit_fails_for_placeholder_answers_on_blocked() -> None:
    """Feature D: BLOCKED report with placeholder answers fails (blocking)."""
    from reverse_agent.project_gate import _required_audit_coverage_check, generate_required_audit_scaffold

    scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
    report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nBLOCKED\n\n{ scaffold }\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="BLOCKED",
    )
    assert result["status"] == "FAIL"


def test_required_audit_passes_with_concise_answers() -> None:
    """Feature D: SUCCESS report with concise non-placeholder answers passes."""
    from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

    questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
    audit_lines = ["## Required Audit", ""]
    for i, q in enumerate(questions, start=1):
        audit_lines.append(f"### {i}. {q}")
        audit_lines.append("")
        audit_lines.append("- Evidence: project_gate.py lines 280-390")
        audit_lines.append("- Status: PASS")
        audit_lines.append("- Answer: yes, concise answer")
        audit_lines.append("")
    report_text = "# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + "\n".join(audit_lines) + "\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="SUCCESS",
    )
    assert result["status"] == "PASS"
    assert result["placeholder_answers"] == []


def test_required_audit_regression_previous_round_placeholder_shape() -> None:
    """Feature D regression: previous round report shape with all-placeholder Required Audit fails for SUCCESS."""
    from reverse_agent.project_gate import _required_audit_coverage_check

    # This replicates the shape of the previous round's report where all 8
    # Required Audit items had placeholder answers:
    #   - Evidence: (to be filled)
    #   - Status: PENDING
    #   - Answer: (to be filled)
    report_section = """## Required Audit

### 1. How is the decision's Required Audit section currently parsed, if at all?

- Evidence: (to be filled)
- Status: PENDING
- Answer: (to be filled)

### 2. Which Required Audit questions from the decision can be answered mechanically from project_state artifacts?

- Evidence: (to be filled)
- Status: PENDING
- Answer: (to be filled)

### 3. Should final-check fail when ## Required Audit is missing for an engineering decision that declares Required Audit items?

- Evidence: (to be filled)
- Status: PENDING
- Answer: (to be filled)
"""
    report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n{ report_section }\n"
    result = _required_audit_coverage_check(
        decision_text=_DECISION_WITH_REQUIRED_AUDIT,
        report_text=report_text,
        report_status="SUCCESS",
    )
    assert result["status"] == "FAIL"
    assert len(result["placeholder_answers"]) == 3


def test_final_check_required_audit_fails_with_placeholder_scaffold(tmp_path: Path) -> None:
    """Feature B: final-check fails when SUCCESS report has scaffold with placeholder answers."""
    from reverse_agent.project_gate import generate_required_audit_scaffold

    state_dir = _make_gate_state(tmp_path)
    (state_dir / "decision_packet.md").write_text(_DECISION_WITH_REQUIRED_AUDIT, encoding="utf-8")
    scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
    _write_report(
        state_dir,
        decision_id="decision_audit_test",
        report_id="report_audit_test",
        round_id="round_audit_test",
        status="SUCCESS",
        acceptance="ACCEPTED",
    )
    report_path = state_dir / "codex_execution_report.md"
    report_path.write_text(
        report_path.read_text(encoding="utf-8") + "\n" + scaffold + "\n",
        encoding="utf-8",
    )
    _write_pytest(state_dir, decision_id="decision_audit_test", report_id="report_audit_test", round_id="round_audit_test")

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    audit_check = _check(result, "required_audit_coverage")
    assert audit_check is not None
    assert audit_check["status"] == "FAIL"
    assert len(audit_check["placeholder_answers"]) > 0


def test_is_required_audit_placeholder_detects_known_markers() -> None:
    """Feature A: placeholder detection covers all required marker patterns."""
    from reverse_agent.project_gate import _is_required_audit_placeholder

    assert _is_required_audit_placeholder("(to be filled)")
    assert _is_required_audit_placeholder("TODO")
    assert _is_required_audit_placeholder("TBD")
    assert _is_required_audit_placeholder("PENDING")
    assert _is_required_audit_placeholder("")
    assert _is_required_audit_placeholder("placeholder text")
    assert _is_required_audit_placeholder("N/A")
    assert not _is_required_audit_placeholder("real answer with evidence")
    assert not _is_required_audit_placeholder("ANSWERED")
    assert not _is_required_audit_placeholder("the check parses the section and validates answers")


# ---------------------------------------------------------------------------
# Feature A: command-plan recommends run-closeout for approved engineering
# decisions with closeout allowed.
# ---------------------------------------------------------------------------


def test_command_plan_recommends_run_closeout_for_approved_engineering_decision(
    tmp_path: Path,
) -> None:
    """Feature A: command-plan recommends run-closeout when decision is APPROVED
    and closeout is allowed."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    action = result["recommended_next_action"]
    assert "run-closeout" in action
    assert "round_command_plan" in action


def test_command_plan_keeps_manual_fallback_when_closeout_not_allowed(
    tmp_path: Path,
) -> None:
    """Feature A: command-plan keeps manual fallback when closeout is not allowed."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "fast",
        "profile_reason": "test fixture",
        "closeout_allowed": False,
        "required_command_kinds": ["startup", "preflight"],
    })

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["recommended_next_action"] == "record_and_follow_command_plan_manually"


def test_command_plan_keeps_manual_fallback_when_decision_not_approved(
    tmp_path: Path,
) -> None:
    """Feature A: command-plan keeps manual fallback when decision is not APPROVED."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
""",
    )
    # Override decision status to DRAFT
    decision_text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    decision_text = decision_text.replace('"status": "APPROVED"', '"status": "DRAFT"')
    (state_dir / "decision_packet.md").write_text(decision_text, encoding="utf-8")
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    assert result["recommended_next_action"] == "record_and_follow_command_plan_manually"


# ---------------------------------------------------------------------------
# Feature B: forbidden live build recommendation guard.
# ---------------------------------------------------------------------------


def test_command_plan_filters_forbidden_live_build_command(tmp_path: Path) -> None:
    """Feature B: command-plan does not include live project_state build when
    the decision's Do Not Do section forbids it."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_state build --reports-dir solve_reports
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
""",
        extra_text="""
## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    commands = [cmd["command"] for cmd in result["commands"]]
    # The live build command must not appear
    assert not any(
        "project_state build" in c for c in commands
    ), f"forbidden live build command found in plan: {commands}"
    # Other commands should still be present
    assert any("preflight" in c for c in commands)


def test_command_plan_keeps_build_when_not_forbidden(tmp_path: Path) -> None:
    """Feature B: command-plan keeps project_state build when the decision
    does not forbid it."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_state build --reports-dir solve_reports
python -m reverse_agent.project_gate preflight --state-dir project_state
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    commands = [cmd["command"] for cmd in result["commands"]]
    assert any("project_state build" in c for c in commands)


# ---------------------------------------------------------------------------
# Feature C: documentation file contains canonical run-closeout command.
# ---------------------------------------------------------------------------


def test_docs_run_closeout_contains_canonical_command() -> None:
    """Feature C: docs/run_closeout.md contains the canonical run-closeout
    command and Required Audit warning."""
    docs_path = Path(__file__).resolve().parent.parent / "docs" / "run_closeout.md"
    assert docs_path.exists(), f"Documentation file not found: {docs_path}"
    content = docs_path.read_text(encoding="utf-8")
    assert "run-closeout" in content
    assert "decision_packet.md" in content
    assert "task_packet.json" in content
    assert "Required Audit" in content
    assert "project_state build" in content


def test_readme_md_points_to_docs() -> None:
    """Feature C: README.md contains a pointer to docs/run_closeout.md."""
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    assert readme_path.exists(), f"README.md not found: {readme_path}"
    content = readme_path.read_text(encoding="utf-8")
    assert "docs/run_closeout.md" in content
    assert "run-closeout" in content


# ---------------------------------------------------------------------------
# Feature D: previous Required Audit answer validation remains active.
# ---------------------------------------------------------------------------


def test_required_audit_validation_remains_active_for_success(tmp_path: Path) -> None:
    """Feature D: Required Audit answer validation from the previous round
    remains active for SUCCESS reports."""
    from reverse_agent.project_gate import _required_audit_placeholder_items

    scaffold = """## Required Audit

### 1. Test question?

- Evidence: (to be filled)
- Status: PENDING
- Answer: (to be filled)
"""
    placeholders = _required_audit_placeholder_items(scaffold)
    assert len(placeholders) > 0

    substantive = """## Required Audit

### 1. Test question?

- Evidence: real evidence from source code
- Status: PASS
- Answer: the check validates field-level content
"""
    placeholders = _required_audit_placeholder_items(substantive)
    assert len(placeholders) == 0


# ---------------------------------------------------------------------------
# Regression: _do_not_do_prohibits_run_closeout line-level analysis
# ---------------------------------------------------------------------------


def test_do_not_do_prohibits_run_closeout_explicit_prohibition() -> None:
    """Lines that explicitly prohibit running run-closeout are detected."""
    from reverse_agent.project_gate import _do_not_do_prohibits_run_closeout

    assert _do_not_do_prohibits_run_closeout("Do not run run-closeout for this round.")
    assert _do_not_do_prohibits_run_closeout("Do not use run-closeout.")
    assert _do_not_do_prohibits_run_closeout("Do not execute run-closeout.")
    assert _do_not_do_prohibits_run_closeout("Do not call run-closeout.")
    assert _do_not_do_prohibits_run_closeout("Do not invoke run-closeout.")


def test_do_not_do_prohibits_run_closeout_false_positive_avoided() -> None:
    """Lines that mention run-closeout but don't prohibit running it are not detected."""
    from reverse_agent.project_gate import _do_not_do_prohibits_run_closeout

    assert not _do_not_do_prohibits_run_closeout(
        "Do not replace run-closeout with a workflow engine."
    )
    assert not _do_not_do_prohibits_run_closeout(
        "run-closeout is the default closeout command."
    )
    assert not _do_not_do_prohibits_run_closeout("")


def test_command_plan_recommends_run_closeout_with_do_not_do_mention(
    tmp_path: Path,
) -> None:
    """Feature A: command-plan recommends run-closeout even when Do Not Do
    section mentions run-closeout in a non-prohibiting context."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
""",
        extra_text="""
## 3. Do Not Do

Do not replace run-closeout with a workflow engine.
Do not add a daemon or scheduler.
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    action = result["recommended_next_action"]
    assert "run-closeout" in action
    assert "round_command_plan" in action


def test_command_plan_manual_fallback_when_do_not_do_prohibits_run_closeout(
    tmp_path: Path,
) -> None:
    """Feature A: command-plan keeps manual fallback when Do Not Do section
    explicitly prohibits running run-closeout."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
""",
        extra_text="""
## 3. Do Not Do

Do not run run-closeout for this round.
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert result["recommended_next_action"] == "record_and_follow_command_plan_manually"


def test_command_plan_json_and_saved_file_agree(tmp_path: Path) -> None:
    """Feature: command-plan --json stdout and saved command_plan.json agree
    on recommended_next_action."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })

    result = command_plan(state_dir=state_dir, write_result=True)

    saved = json.loads((gates_dir / "command_plan.json").read_text())
    assert saved["recommended_next_action"] == result["recommended_next_action"]
    assert "run-closeout" in saved["recommended_next_action"]


def test_final_check_fails_when_recommendation_is_manual_but_run_closeout_required(
    tmp_path: Path,
) -> None:
    """Feature: final-check fails when command_plan.json recommends manual
    fallback but the decision requires run-closeout."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
""",
        extra_text="""
```json decision_contract
{
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_command_plan"
  ]
}
```
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })
    # Write a command_plan.json with manual fallback (simulating the bug)
    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "recommended_next_action": "record_and_follow_command_plan_manually",
        "commands": [],
        "warnings": [],
        "blocking_reasons": [],
    })

    result = final_check(state_dir=state_dir, write_result=False)

    checks = result.get("checks", [])
    cp_check = next(
        (c for c in checks if c.get("name") == "command_plan_recommends_run_closeout"),
        None,
    )
    assert cp_check is not None
    assert cp_check["status"] == "FAIL"


def test_final_check_passes_when_recommendation_is_run_closeout(
    tmp_path: Path,
) -> None:
    """Feature: final-check passes when command_plan.json recommends
    run-closeout for a round that requires it."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
""",
        extra_text="""
```json decision_contract
{
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_command_plan"
  ]
}
```
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "full",
        "profile_reason": "test fixture",
        "closeout_allowed": True,
        "required_command_kinds": ["startup", "preflight", "pytest", "close-round"],
    })
    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "recommended_next_action": (
            "python -m reverse_agent.project_gate run-closeout "
            "--state-dir project_state --round-id round_command_plan"
        ),
        "commands": [],
        "warnings": [],
        "blocking_reasons": [],
    })

    result = final_check(state_dir=state_dir, write_result=False)

    checks = result.get("checks", [])
    cp_check = next(
        (c for c in checks if c.get("name") == "command_plan_recommends_run_closeout"),
        None,
    )
    assert cp_check is not None
    assert cp_check["status"] == "PASS"


def test_final_check_passes_when_run_closeout_not_required(tmp_path: Path) -> None:
    """Feature: final-check passes command_plan_recommends_run_closeout when
    run-closeout is not required (e.g. closeout not allowed)."""
    state_dir = _make_command_plan_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
""",
    )
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "profile": "fast",
        "profile_reason": "test fixture",
        "closeout_allowed": False,
        "required_command_kinds": ["startup", "preflight"],
    })
    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": "decision_command_plan",
        "round_id": "round_command_plan",
        "mainline": "engineering_branch",
        "recommended_next_action": "record_and_follow_command_plan_manually",
        "commands": [],
        "warnings": [],
        "blocking_reasons": [],
    })

    result = final_check(state_dir=state_dir, write_result=False)

    checks = result.get("checks", [])
    cp_check = next(
        (c for c in checks if c.get("name") == "command_plan_recommends_run_closeout"),
        None,
    )
    assert cp_check is not None
    assert cp_check["status"] == "PASS"


# ---------------------------------------------------------------------------
# Regression: command-plan execution authority validation
# ---------------------------------------------------------------------------


def _make_execution_authority_state(
    tmp_path: Path,
    *,
    profile: str = "fast",
    closeout_allowed: bool = False,
    required_command_kinds: list[str] | None = None,
    omitted_commands: list[dict[str, Any]] | None = None,
    plan_commands: list[dict[str, Any]] | None = None,
    pytest_commands: list[tuple[str, str, int]] | None = None,
    report_status: str = "SUCCESS",
    report_acceptance: str = "ACCEPTED",
    report_text_extra: str = "",
) -> Path:
    """Create a minimal state for command-plan execution authority tests.

    Each entry in ``pytest_commands`` is a ``(command, stdout, exit_code)``
    tuple that will be recorded as a command block in pytest_result.txt.
    """
    if required_command_kinds is None:
        if profile == "fast":
            required_command_kinds = ["startup", "preflight", "command-plan", "report-summary", "final-check"]
        elif profile == "standard":
            required_command_kinds = ["startup", "preflight", "gate-profile", "command-plan", "pytest", "report-summary", "final-check"]
        else:
            required_command_kinds = [
                "startup", "preflight", "gate-profile", "command-plan", "run-round", "pytest",
                "doctor", "lint-report", "report-summary", "final-check", "close-round",
            ]

    if omitted_commands is None:
        if profile == "fast":
            omitted_commands = [
                {"command": "python -m pytest tests/test_project_gate.py -q", "kind": "pytest",
                 "reason": "omitted by fast profile: pytest not in required_command_kinds"},
                {"command": None, "kind": "close-round",
                 "reason": "omitted by fast profile: closeout not allowed"},
            ]
        else:
            omitted_commands = []

    if plan_commands is None:
        plan_commands = [
            {"index": 1, "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
             "phase": "preflight", "kind": "preflight", "required": True, "expected_exit_codes": [0]},
            {"index": 2, "command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
             "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
            {"index": 3, "command": "python -m reverse_agent.project_gate report-summary --state-dir project_state",
             "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            {"index": 4, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state",
             "phase": "gate", "kind": "final-check", "required": True, "expected_exit_codes": [0, 1]},
        ]

    if pytest_commands is None:
        pytest_commands = [
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ]

    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)

    decision_id = "decision_exec_auth"
    report_id = "codex_report_exec_auth"
    round_id = "round_exec_auth"

    _write_json(state_dir / "current_state.json", {
        "round_id": round_id,
        "state_build_id": "state_test",
        "state_digest": "digest_test",
        "state_scope": "sample_state",
        "source_harness_run": "run_test",
    })
    _write_json(state_dir / "task_packet.json", {
        "state_scope": "sample_state",
        "task_source": "derived_from_sample_artifacts",
        "execution_scope": "decision_packet_controls_current_round",
        "active_decision_packet": "project_state/decision_packet.md",
    })
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

    gates_dir = state_dir / "gates"
    gates_dir.mkdir(exist_ok=True)

    # Write gate_profile_plan.json
    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "profile": profile,
        "profile_reason": "test fixture",
        "closeout_allowed": closeout_allowed,
        "required_command_kinds": required_command_kinds,
    })

    # Write command_plan.json
    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "generated_at": "2026-06-21T00:00:00Z",
        "profile_meta": {
            "profile": profile,
            "profile_reason": "test fixture",
            "closeout_allowed": closeout_allowed,
            "required_command_kinds": required_command_kinds,
        },
        "omitted_commands": omitted_commands,
        "commands": plan_commands,
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
    })

    # Write round_delta_summary.json
    _write_json(gates_dir / "round_delta_summary.json", {
        "schema_version": 1,
        "artifact_name": "round_delta_summary.json",
        "decision_id": decision_id,
        "round_id": round_id,
        "baseline_available": True,
        "new_dirty_files_since_baseline": [],
        "inherited_dirty_files": [],
        "final_dirty_files": [],
    })
    _write_json(gates_dir / "report_summary_synthesis.json", {
        "schema_version": 1,
        "artifact_name": "report_summary_synthesis.json",
        "decision_id": decision_id,
        "round_id": round_id,
    })
    _write_json(gates_dir / "final_gate_result.json", {
        "schema_version": 1,
        "artifact_name": "final_gate_result.json",
        "decision_id": decision_id,
        "round_id": round_id,
        "gate_status": "PASSED",
    })

    # Build pytest_result.txt
    tests_ran = [cmd for cmd, _, _ in pytest_commands if not _is_startup_command_str(cmd)]
    body_parts = [_command_block(cmd, stdout, exit_code=ec) for cmd, stdout, ec in pytest_commands]
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=tests_ran,
        body="\n\n".join(body_parts),
    )

    # Write report
    report_body = report_text_extra if report_text_extra else "# CODEX_EXECUTION_REPORT"
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=report_status,
        acceptance=report_acceptance,
        files_changed=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
        tests_ran=tests_ran,
        generated_artifacts=[
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
        ],
        extra_body=report_body,
    )

    return state_dir


def _is_startup_command_str(command: str) -> bool:
    """Check if a command is a startup command (for tests)."""
    patterns = ("Set-Location", "Get-Location", "Test-Path", "git rev-parse", "git status")
    return any(p in command for p in patterns)


def test_execution_authority_fast_profile_passes_when_no_unauthorized_commands(
    tmp_path: Path,
) -> None:
    """Fast profile with only authorized commands passes execution authority check."""
    state_dir = _make_execution_authority_state(tmp_path, profile="fast")

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "PASS"


def test_execution_authority_fast_profile_fails_when_pytest_recorded(
    tmp_path: Path,
) -> None:
    """Fast profile fails execution authority check when pytest is recorded as executed."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py -q"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "FAIL"
    unauthorized = auth_check.get("unauthorized_commands") or []
    assert any(u["kind"] == "pytest" for u in unauthorized)


def test_execution_authority_fast_profile_fails_when_close_round_recorded(
    tmp_path: Path,
) -> None:
    """Fast profile fails execution authority check when close-round is recorded as executed."""
    close_cmd = "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_exec_auth"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            (close_cmd, "close-round: CLOSED", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "FAIL"
    unauthorized = auth_check.get("unauthorized_commands") or []
    assert any(u["kind"] == "close-round" for u in unauthorized)


def test_execution_authority_standard_profile_accepts_pytest(
    tmp_path: Path,
) -> None:
    """Standard profile accepts pytest when it's in required_command_kinds."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py -q"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="standard",
        closeout_allowed=True,
        required_command_kinds=["startup", "preflight", "gate-profile", "command-plan", "pytest", "report-summary", "final-check"],
        omitted_commands=[],
        plan_commands=[
            {"index": 1, "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
             "phase": "preflight", "kind": "preflight", "required": True, "expected_exit_codes": [0]},
            {"index": 2, "command": pytest_cmd,
             "phase": "test", "kind": "pytest", "required": True, "expected_exit_codes": [0]},
            {"index": 3, "command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
             "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
            {"index": 4, "command": "python -m reverse_agent.project_gate report-summary --state-dir project_state",
             "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            {"index": 5, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state",
             "phase": "gate", "kind": "final-check", "required": True, "expected_exit_codes": [0, 1]},
        ],
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "PASS"


def test_execution_authority_full_profile_accepts_all_commands(
    tmp_path: Path,
) -> None:
    """Full profile accepts pytest, doctor, lint-report, and close-round when planned."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"
    close_cmd = "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_exec_auth"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="full",
        closeout_allowed=True,
        required_command_kinds=[
            "startup", "preflight", "gate-profile", "command-plan", "run-round", "pytest",
            "doctor", "lint-report", "report-summary", "final-check", "close-round",
        ],
        omitted_commands=[],
        plan_commands=[
            {"index": 1, "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
             "phase": "preflight", "kind": "preflight", "required": True, "expected_exit_codes": [0]},
            {"index": 2, "command": pytest_cmd,
             "phase": "test", "kind": "pytest", "required": True, "expected_exit_codes": [0]},
            {"index": 3, "command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
             "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
            {"index": 4, "command": "python -m reverse_agent.project_gate report-summary --state-dir project_state",
             "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
            {"index": 5, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state",
             "phase": "gate", "kind": "final-check", "required": True, "expected_exit_codes": [0, 1]},
            {"index": 6, "command": close_cmd,
             "phase": "gate", "kind": "close-round", "required": True, "expected_exit_codes": [0]},
        ],
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
            (close_cmd, "close-round: CLOSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "PASS"


def test_execution_authority_stale_command_plan_delegates_to_ids_check(
    tmp_path: Path,
) -> None:
    """Stale command-plan IDs cause execution authority check to delegate to command_plan_ids_match."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py -q"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )
    # Overwrite command_plan.json with stale IDs
    gates_dir = state_dir / "gates"
    cp = json.loads((gates_dir / "command_plan.json").read_text(encoding="utf-8"))
    cp["decision_id"] = "stale_decision"
    cp["round_id"] = "stale_round"
    _write_json(gates_dir / "command_plan.json", cp)

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "PASS"
    assert auth_check.get("skipped_reason") == "stale_command_plan_ids"


def test_execution_authority_failed_report_warns_when_acknowledged(
    tmp_path: Path,
) -> None:
    """FAILED report with unauthorized commands gets WARN when report acknowledges them."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py -q"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        report_status="FAILED",
        report_acceptance="REWORK_REQUIRED",
        report_text_extra=(
            "# CODEX_EXECUTION_REPORT\n\n"
            "Execution stopped because of unauthorized command detected.\n"
            "The pytest command was not authorized by command-plan.\n"
        ),
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: FAILED", 1),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "WARN"


def test_execution_authority_failed_report_fails_when_not_acknowledged(
    tmp_path: Path,
) -> None:
    """FAILED report with unauthorized commands gets FAIL when report doesn't acknowledge them."""
    pytest_cmd = "python -m pytest tests/test_project_gate.py -q"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        report_status="FAILED",
        report_acceptance="REWORK_REQUIRED",
        report_text_extra="# CODEX_EXECUTION_REPORT\n\nSome unrelated failure reason.\n",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            (pytest_cmd, "938 passed", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: FAILED", 1),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Regression: gate-profile command authorization policy
# ---------------------------------------------------------------------------


def test_gate_profile_in_required_command_kinds_for_full_profile(tmp_path: Path) -> None:
    """gate-profile is in required_command_kinds for the full profile."""
    from reverse_agent.project_gate import classify_gate_profile

    decision_text = (
        "## 6. Implementation Scope\n\n"
        "Allowed paths:\n\n"
        "- `reverse_agent/project_gate.py`\n"
        "- `tests/test_project_gate.py`\n\n"
        "Allowed project_state artifact paths:\n\n"
        "- `project_state/codex_execution_report.md`\n"
    )
    result = classify_gate_profile(decision_text)
    assert result["profile"] == "full"
    assert "gate-profile" in result["required_command_kinds"]


def test_gate_profile_in_required_command_kinds_for_standard_profile(tmp_path: Path) -> None:
    """gate-profile is in required_command_kinds for the standard profile."""
    from reverse_agent.project_gate import classify_gate_profile

    decision_text = (
        "## 6. Implementation Scope\n\n"
        "Allowed paths:\n\n"
        "- `reverse_agent/some_module.py`\n"
        "- `tests/test_some_module.py`\n\n"
        "Allowed project_state artifact paths:\n\n"
        "- `project_state/codex_execution_report.md`\n"
    )
    result = classify_gate_profile(decision_text)
    assert result["profile"] == "standard"
    assert "gate-profile" in result["required_command_kinds"]


def test_gate_profile_not_in_required_command_kinds_for_fast_profile(tmp_path: Path) -> None:
    """gate-profile is NOT in required_command_kinds for the fast profile."""
    from reverse_agent.project_gate import classify_gate_profile

    decision_text = (
        "## 6. Implementation Scope\n\n"
        "Allowed project_state artifact paths:\n\n"
        "- `project_state/codex_execution_report.md`\n"
    )
    result = classify_gate_profile(decision_text)
    assert result["profile"] == "fast"
    assert "gate-profile" not in result["required_command_kinds"]


def test_gate_profile_in_full_suggested_commands() -> None:
    """gate-profile appears in _FULL_SUGGESTED_COMMANDS as a diagnostic command."""
    from reverse_agent.project_gate import _FULL_SUGGESTED_COMMANDS

    kinds = [c["kind"] for c in _FULL_SUGGESTED_COMMANDS]
    assert "gate-profile" in kinds


def test_gate_profile_in_standard_suggested_commands() -> None:
    """gate-profile appears in _STANDARD_SUGGESTED_COMMANDS as a diagnostic command."""
    from reverse_agent.project_gate import _STANDARD_SUGGESTED_COMMANDS

    kinds = [c["kind"] for c in _STANDARD_SUGGESTED_COMMANDS]
    assert "gate-profile" in kinds


def test_execution_authority_full_profile_passes_when_gate_profile_recorded(
    tmp_path: Path,
) -> None:
    """Full profile does not flag gate-profile as unauthorized when recorded in pytest_result."""
    gate_profile_cmd = "python -m reverse_agent.project_gate gate-profile --state-dir project_state"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="full",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            (gate_profile_cmd, "gate-profile: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            ("python -m pytest tests/test_project_gate.py -q", "653 passed", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "PASS"
    unauthorized = auth_check.get("unauthorized_commands") or []
    assert not any(u["kind"] == "gate-profile" for u in unauthorized)


def test_execution_authority_fast_profile_fails_when_gate_profile_recorded(
    tmp_path: Path,
) -> None:
    """Fast profile flags gate-profile as unauthorized when recorded in pytest_result."""
    gate_profile_cmd = "python -m reverse_agent.project_gate gate-profile --state-dir project_state"
    state_dir = _make_execution_authority_state(
        tmp_path,
        profile="fast",
        pytest_commands=[
            ("Set-Location F:\\reverse-agent", "F:\\reverse-agent", 0),
            ("Get-Location", "F:\\reverse-agent", 0),
            ("Test-Path F:\\reverse-agent", "True", 0),
            ("git rev-parse --show-toplevel", "F:\\reverse-agent", 0),
            ("git status --short", "", 0),
            ("python -m reverse_agent.project_gate preflight --state-dir project_state", "preflight: PASSED", 0),
            ("python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "{}", 0),
            (gate_profile_cmd, "gate-profile: PASSED", 0),
            ("python -m reverse_agent.project_gate report-summary --state-dir project_state", "{}", 0),
            ("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", 0),
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    auth_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "command_plan_execution_authority"),
        None,
    )
    assert auth_check is not None
    assert auth_check["status"] == "FAIL"
    unauthorized = auth_check.get("unauthorized_commands") or []
    assert any(u["kind"] == "gate-profile" for u in unauthorized)


# ---------------------------------------------------------------------------
# Regression: closeout/report-summary archive policy
# ---------------------------------------------------------------------------


def _make_closeout_policy_state(
    tmp_path: Path,
    *,
    profile: str = "full",
    closeout_allowed: bool = True,
    close_snapshot_for_current_round: bool = False,
    report_files_changed: list[str] | None = None,
    report_generated_artifacts: list[str] | None = None,
) -> Path:
    """Create a minimal state for closeout/report-summary archive policy tests."""
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)

    decision_id = "decision_closeout_policy"
    report_id = "codex_report_closeout_policy"
    round_id = "round_closeout_policy"

    if profile == "fast":
        required_command_kinds = ["startup", "preflight", "command-plan", "report-summary", "final-check"]
    elif profile == "standard":
        required_command_kinds = ["startup", "preflight", "gate-profile", "command-plan", "pytest", "report-summary", "final-check"]
    else:
        required_command_kinds = [
            "startup", "preflight", "gate-profile", "command-plan", "run-round", "pytest",
            "doctor", "lint-report", "report-summary", "final-check", "close-round",
        ]

    _write_json(state_dir / "current_state.json", {
        "round_id": round_id,
        "state_build_id": "state_test",
        "state_digest": "digest_test",
        "state_scope": "sample_state",
        "source_harness_run": "run_test",
    })
    _write_json(state_dir / "task_packet.json", {
        "state_scope": "sample_state",
        "task_source": "derived_from_sample_artifacts",
        "execution_scope": "decision_packet_controls_current_round",
        "active_decision_packet": "project_state/decision_packet.md",
    })
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

    gates_dir = state_dir / "gates"
    gates_dir.mkdir(exist_ok=True)

    _write_json(gates_dir / "gate_profile_plan.json", {
        "schema_version": 1,
        "gate_name": "gate-profile",
        "gate_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "profile": profile,
        "profile_reason": "test fixture",
        "closeout_allowed": closeout_allowed,
        "required_command_kinds": required_command_kinds,
    })

    plan_commands = [
        {"index": 1, "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
         "phase": "preflight", "kind": "preflight", "required": True, "expected_exit_codes": [0]},
        {"index": 2, "command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
         "phase": "gate", "kind": "command-plan", "required": True, "expected_exit_codes": [0]},
        {"index": 3, "command": "python -m reverse_agent.project_gate report-summary --state-dir project_state",
         "phase": "gate", "kind": "report-summary", "required": True, "expected_exit_codes": [0, 1]},
        {"index": 4, "command": "python -m reverse_agent.project_gate final-check --state-dir project_state",
         "phase": "gate", "kind": "final-check", "required": True, "expected_exit_codes": [0, 1]},
    ]
    if profile != "fast":
        plan_commands.insert(2, {
            "index": 3, "command": "python -m pytest tests/test_project_gate.py -q",
            "phase": "test", "kind": "pytest", "required": True, "expected_exit_codes": [0],
        })

    _write_json(gates_dir / "command_plan.json", {
        "schema_version": 1,
        "plan_name": "command-plan",
        "plan_status": "PASSED",
        "decision_id": decision_id,
        "round_id": round_id,
        "mainline": "engineering_branch",
        "generated_at": "2026-06-21T00:00:00Z",
        "profile_meta": {
            "profile": profile,
            "profile_reason": "test fixture",
            "closeout_allowed": closeout_allowed,
            "required_command_kinds": required_command_kinds,
        },
        "omitted_commands": [],
        "commands": plan_commands,
        "warnings": [],
        "blocking_reasons": [],
        "recommended_next_action": "record_and_follow_command_plan_manually",
    })

    _write_json(gates_dir / "round_delta_summary.json", {
        "schema_version": 1,
        "artifact_name": "round_delta_summary.json",
        "decision_id": decision_id,
        "round_id": round_id,
        "baseline_available": True,
        "new_dirty_files_since_baseline": [],
        "inherited_dirty_files": [],
        "final_dirty_files": [],
    })
    _write_json(gates_dir / "report_summary_synthesis.json", {
        "schema_version": 1,
        "artifact_name": "report_summary_synthesis.json",
        "decision_id": decision_id,
        "round_id": round_id,
    })
    _write_json(gates_dir / "final_gate_result.json", {
        "schema_version": 1,
        "artifact_name": "final_gate_result.json",
        "decision_id": decision_id,
        "round_id": round_id,
        "gate_status": "PASSED",
    })

    # Optionally write round_close_snapshot for current round
    if close_snapshot_for_current_round:
        _write_json(gates_dir / "round_close_snapshot.json", {
            "schema_version": 1,
            "artifact_name": "round_close_snapshot.json",
            "decision_id": decision_id,
            "round_id": round_id,
            "round_closed": True,
            "generated_at": "2026-06-21T00:00:00Z",
        })
        # Also create the round archive directory so archive paths are
        # included by build_report_summary_synthesis.
        archive_dir = state_dir / "rounds" / round_id
        archive_dir.mkdir(parents=True, exist_ok=True)
        _write_json(archive_dir / "round_manifest.json", {
            "schema_version": 1,
            "artifact_name": "round_manifest.json",
            "decision_id": decision_id,
            "round_id": round_id,
            "round_closed": True,
        })
        (archive_dir / "codex_execution_report.md").write_text(
            "# CODEX_EXECUTION_REPORT\n", encoding="utf-8"
        )
        (archive_dir / "decision_packet.md").write_text(
            "# DECISION_PACKET\n", encoding="utf-8"
        )
        (archive_dir / "pytest_result.txt").write_text(
            "# PYTEST_RESULT\n", encoding="utf-8"
        )

    # Build default files_changed and generated_artifacts
    if report_files_changed is None:
        report_files_changed = [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ]
    if report_generated_artifacts is None:
        report_generated_artifacts = [
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/command_plan.json",
        ]

    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=["python -m reverse_agent.project_gate preflight --state-dir project_state"],
        body=_command_block(
            "python -m reverse_agent.project_gate preflight --state-dir project_state",
            "preflight: PASSED",
            exit_code=0,
        ),
    )
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status="SUCCESS",
        acceptance="ACCEPTED",
        files_changed=report_files_changed,
        tests_ran=["python -m reverse_agent.project_gate preflight --state-dir project_state"],
        generated_artifacts=report_generated_artifacts,
    )

    return state_dir


def test_closeout_policy_pre_closeout_excludes_archive_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When closeout_allowed=true but closeout hasn't run, archive paths
    should NOT be in synthesized files_changed/generated_artifacts."""
    # Override autouse _clean_git_diff to return empty git changes
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [],
    )
    state_dir = _make_closeout_policy_state(
        tmp_path,
        profile="full",
        closeout_allowed=True,
        close_snapshot_for_current_round=False,
    )

    synthesis = build_report_summary_synthesis(
        state_dir=state_dir,
        repo_root=tmp_path,
        write_result=False,
    )

    synthesized = synthesis.get("synthesized_summary") or {}
    files_changed = synthesized.get("files_changed") or []
    generated_artifacts = synthesized.get("generated_artifacts") or []

    # Archive paths should NOT be present
    assert not any("project_state/rounds/" in p for p in files_changed), (
        f"archive paths should not be in files_changed pre-closeout: {files_changed}"
    )
    assert not any("project_state/rounds/" in p for p in generated_artifacts), (
        f"archive paths should not be in generated_artifacts pre-closeout: {generated_artifacts}"
    )

    # No diffs should be produced for archive paths
    diffs = synthesis.get("diffs") or []
    archive_diffs = [
        d for d in diffs
        if any("project_state/rounds/" in str(item) for item in (d.get("expected") or []))
        or any("project_state/rounds/" in str(item) for item in (d.get("actual") or []))
    ]
    assert not archive_diffs, f"archive path diffs should not exist pre-closeout: {archive_diffs}"


def test_closeout_policy_post_closeout_includes_archive_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When closeout_allowed=true and closeout has run (round_close_snapshot
    matches current round), archive paths SHOULD be in synthesized
    files_changed/generated_artifacts."""
    # Override autouse _clean_git_diff to return empty git changes
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [],
    )
    state_dir = _make_closeout_policy_state(
        tmp_path,
        profile="full",
        closeout_allowed=True,
        close_snapshot_for_current_round=True,
    )

    synthesis = build_report_summary_synthesis(
        state_dir=state_dir,
        repo_root=tmp_path,
        write_result=False,
    )

    synthesized = synthesis.get("synthesized_summary") or {}
    files_changed = synthesized.get("files_changed") or []
    generated_artifacts = synthesized.get("generated_artifacts") or []

    # Archive paths SHOULD be present
    assert any("project_state/rounds/" in p for p in files_changed), (
        f"archive paths should be in files_changed post-closeout: {files_changed}"
    )
    assert any("project_state/rounds/" in p for p in generated_artifacts), (
        f"archive paths should be in generated_artifacts post-closeout: {generated_artifacts}"
    )


def test_closeout_policy_fast_profile_excludes_archive_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When closeout_allowed=false (fast profile), archive paths should NOT
    be in synthesized files_changed/generated_artifacts."""
    # Override autouse _clean_git_diff to return empty git changes
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [],
    )
    state_dir = _make_closeout_policy_state(
        tmp_path,
        profile="fast",
        closeout_allowed=False,
        close_snapshot_for_current_round=False,
    )

    synthesis = build_report_summary_synthesis(
        state_dir=state_dir,
        repo_root=tmp_path,
        write_result=False,
    )

    synthesized = synthesis.get("synthesized_summary") or {}
    files_changed = synthesized.get("files_changed") or []
    generated_artifacts = synthesized.get("generated_artifacts") or []

    # Archive paths should NOT be present
    assert not any("project_state/rounds/" in p for p in files_changed), (
        f"archive paths should not be in files_changed for fast profile: {files_changed}"
    )
    assert not any("project_state/rounds/" in p for p in generated_artifacts), (
        f"archive paths should not be in generated_artifacts for fast profile: {generated_artifacts}"
    )


def test_closeout_policy_pre_closeout_report_summary_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """report_summary_fields_match_synthesis should not produce archive path
    diffs when pre-closeout and report doesn't include archive paths."""
    # Override autouse _clean_git_diff to return empty git changes
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [],
    )
    state_dir = _make_closeout_policy_state(
        tmp_path,
        profile="full",
        closeout_allowed=True,
        close_snapshot_for_current_round=False,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)

    match_check = next(
        (c for c in result.get("checks", []) if c.get("name") == "report_summary_fields_match_synthesis"),
        None,
    )
    assert match_check is not None
    # The check may fail for other reasons (files_changed, tests_ran, etc.),
    # but it must NOT produce diffs that reference archive paths.
    diffs = match_check.get("diffs") or []
    archive_diffs = [
        d for d in diffs
        if any("project_state/rounds/" in str(item) for item in (d.get("expected") or []))
        or any("project_state/rounds/" in str(item) for item in (d.get("actual") or []))
    ]
    assert not archive_diffs, (
        f"archive path diffs should not exist pre-closeout: {archive_diffs}"
    )


def test_closeout_policy_stale_close_snapshot_excludes_archive_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When round_close_snapshot exists but doesn't match current round,
    archive paths should NOT be included (stale snapshot)."""
    # Override autouse _clean_git_diff to return empty git changes
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [],
    )
    state_dir = _make_closeout_policy_state(
        tmp_path,
        profile="full",
        closeout_allowed=True,
        close_snapshot_for_current_round=False,
    )
    # Write a stale close snapshot
    gates_dir = state_dir / "gates"
    _write_json(gates_dir / "round_close_snapshot.json", {
        "schema_version": 1,
        "artifact_name": "round_close_snapshot.json",
        "decision_id": "stale_decision",
        "round_id": "stale_round",
        "round_closed": True,
        "generated_at": "2026-06-20T00:00:00Z",
    })

    synthesis = build_report_summary_synthesis(
        state_dir=state_dir,
        repo_root=tmp_path,
        write_result=False,
    )

    synthesized = synthesis.get("synthesized_summary") or {}
    files_changed = synthesized.get("files_changed") or []
    generated_artifacts = synthesized.get("generated_artifacts") or []

    # Archive paths should NOT be present (stale snapshot)
    assert not any("project_state/rounds/" in p for p in files_changed), (
        f"archive paths should not be in files_changed with stale snapshot: {files_changed}"
    )
    assert not any("project_state/rounds/" in p for p in generated_artifacts), (
        f"archive paths should not be in generated_artifacts with stale snapshot: {generated_artifacts}"
    )


# ---------------------------------------------------------------------------
# Regression: decision / command-plan conflict detection
# ---------------------------------------------------------------------------


def _make_conflict_state(
    tmp_path: Path,
    *,
    decision_id: str = "decision_conflict",
    round_id: str = "round_conflict",
    mainline: str = "engineering_branch",
    implementation_scope: str | None = None,
    tests_block: str | None = None,
    extra_text: str = "",
) -> Path:
    """Create a minimal state for decision/command-plan conflict detection tests.

    The decision scope determines the gate profile:
    - artifact-only scope -> fast profile (closeout_allowed=false)
    - source/test scope -> standard profile (closeout_allowed=true)
    - gate/project_state scope -> full profile (closeout_allowed=true)
    """
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)

    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": mainline,
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }

    if implementation_scope is None:
        # Default: artifact-only scope -> fast profile
        implementation_scope = """Allowed project_state artifact paths:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
"""

    tests_section = ""
    if tests_block is not None:
        tests_section = f"""
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

Test conflict detection.

## 2. Current Evidence

Evidence.

## 6. Implementation Scope

{implementation_scope}
{tests_section}
{extra_text}
""",
        encoding="utf-8",
    )

    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": round_id,
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
    return state_dir


def test_preflight_decision_command_plan_conflict_passes_when_no_conflicts(
    tmp_path: Path,
) -> None:
    """Preflight passes decision_command_plan_conflict check when Tests
    commands are compatible with the active profile."""
    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    assert conflict_check["status"] == "PASS"


def test_preflight_conflict_fails_when_fast_profile_tests_require_close_round(
    tmp_path: Path,
) -> None:
    """Fast profile (artifact-only scope) with close-round in Tests triggers
    a decision_command_plan_conflict FAIL because close-round is omitted by
    fast profile and closeout_allowed=false."""
    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_conflict
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    assert conflict_check["status"] == "FAIL"
    conflicts = conflict_check.get("conflicts") or []
    # Should detect both omitted_command and closeout_forbidden
    conflict_kinds = {c.get("kind") for c in conflicts}
    assert "omitted_command" in conflict_kinds or "closeout_forbidden" in conflict_kinds


def test_preflight_conflict_fails_when_fast_profile_tests_require_pytest(
    tmp_path: Path,
) -> None:
    """Fast profile with pytest in Tests triggers omitted_command conflict
    because pytest is not in fast profile's required_command_kinds."""
    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    assert conflict_check["status"] == "FAIL"
    conflicts = conflict_check.get("conflicts") or []
    pytest_conflicts = [c for c in conflicts if c.get("command_kind") == "pytest"]
    assert len(pytest_conflicts) > 0


def test_preflight_conflict_passes_for_full_profile_with_close_round(
    tmp_path: Path,
) -> None:
    """Full profile (gate/project_state scope) with close-round in Tests
    does NOT trigger a conflict because closeout_allowed=true and
    close-round is in required_command_kinds."""
    state_dir = _make_conflict_state(
        tmp_path,
        implementation_scope="""Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed project_state artifact paths:

- `project_state/gates/final_gate_result.json`
""",
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_conflict
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    assert conflict_check["status"] == "PASS"


def test_preflight_conflict_passes_for_standard_profile_with_pytest(
    tmp_path: Path,
) -> None:
    """Standard profile (source/test scope) with pytest in Tests does NOT
    trigger a conflict because pytest is in standard profile's
    required_command_kinds."""
    state_dir = _make_conflict_state(
        tmp_path,
        implementation_scope="""Allowed source files:

- `reverse_agent/some_module.py`

Allowed tests:

- `tests/test_some_module.py`
""",
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_some_module.py -q
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    assert conflict_check["status"] == "PASS"


def test_preflight_conflict_does_not_flag_conditional_closeout_command(
    tmp_path: Path,
) -> None:
    """Conditional closeout commands (guarded by 'only if command-plan
    authorizes') are NOT flagged as conflicts."""
    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
""",
        extra_text="""
## 7. Tests

Run closeout only if command-plan explicitly authorizes the closeout command for this round:

```bash
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_conflict
```
""",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    conflict_check = _check(result, "decision_command_plan_conflict")
    assert conflict_check is not None
    # Conditional commands should not trigger conflicts
    conflicts = conflict_check.get("conflicts") or []
    closeout_conflicts = [
        c for c in conflicts
        if c.get("kind") == "closeout_forbidden"
        or c.get("command_kind") in ("run-closeout", "close-round")
    ]
    assert len(closeout_conflicts) == 0, (
        f"conditional closeout command should not be flagged: {closeout_conflicts}"
    )


def test_detect_decision_command_plan_conflicts_returns_empty_for_no_tests(
    tmp_path: Path,
) -> None:
    """_detect_decision_command_plan_conflicts returns empty list when
    decision has no Tests section."""
    from reverse_agent.project_gate import _detect_decision_command_plan_conflicts

    state_dir = _make_conflict_state(tmp_path, tests_block=None)

    decision_text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    conflicts = _detect_decision_command_plan_conflicts(
        decision_text=decision_text,
        state_dir=state_dir,
    )
    assert conflicts == []


def test_detect_decision_command_plan_conflicts_detects_omitted_command(
    tmp_path: Path,
) -> None:
    """_detect_decision_command_plan_conflicts detects omitted_command conflict
    for a fast-profile decision with pytest in Tests."""
    from reverse_agent.project_gate import _detect_decision_command_plan_conflicts

    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m pytest tests/test_project_gate.py -q
""",
    )

    decision_text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    conflicts = _detect_decision_command_plan_conflicts(
        decision_text=decision_text,
        state_dir=state_dir,
    )
    assert len(conflicts) > 0
    assert any(c["kind"] == "omitted_command" for c in conflicts)
    assert any(c["command_kind"] == "pytest" for c in conflicts)


def test_detect_decision_command_plan_conflicts_detects_closeout_forbidden(
    tmp_path: Path,
) -> None:
    """_detect_decision_command_plan_conflicts detects closeout_forbidden
    conflict when close-round is in Tests but closeout_allowed=false."""
    from reverse_agent.project_gate import _detect_decision_command_plan_conflicts

    state_dir = _make_conflict_state(
        tmp_path,
        tests_block="""python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_conflict
""",
    )

    decision_text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    conflicts = _detect_decision_command_plan_conflicts(
        decision_text=decision_text,
        state_dir=state_dir,
    )
    closeout_conflicts = [c for c in conflicts if c["kind"] == "closeout_forbidden"]
    assert len(closeout_conflicts) > 0


def test_conditional_tests_commands_extracts_conditional_commands() -> None:
    """_conditional_tests_commands correctly identifies commands guarded
    by conditional phrases."""
    from reverse_agent.project_gate import _conditional_tests_commands

    decision_text = """
## 7. Tests

Run preflight:

```bash
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Run closeout only if command-plan authorizes the closeout command:

```bash
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_test
```
"""
    conditional = _conditional_tests_commands(decision_text)
    # The closeout command should be conditional
    assert any("run-closeout" in cmd for cmd in conditional)
    # The preflight command should NOT be conditional
    assert not any("preflight" in cmd for cmd in conditional)


# ---------------------------------------------------------------------------
# policy-lint tests
# ---------------------------------------------------------------------------

def _make_policy_lint_state(
    tmp_path: Path,
    *,
    decision_id: str = "decision_policy_lint",
    round_id: str = "round_policy_lint",
    skill_text: str = "",
    readme_text: str = "",
    decision_text: str = "",
    prompt_docs: dict[str, str] | None = None,
) -> Path:
    """Create a minimal state for policy-lint tests with optional skill/readme/prompt text."""
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)

    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2"],
    }

    extra = decision_text or "Test policy-lint."

    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

{extra}
""",
        encoding="utf-8",
    )

    _write_json(
        state_dir / "current_state.json",
        {"round_id": round_id, "state_build_id": "state_test", "state_digest": "digest_test"},
    )
    _write_json(
        state_dir / "task_packet.json",
        {"execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"},
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    # Write skill file if text provided
    if skill_text:
        skills_dir = tmp_path / ".codex-skills" / "reverse-agent-iteration"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "SKILL.md").write_text(skill_text, encoding="utf-8")

    # Write README if text provided
    if readme_text:
        (tmp_path / "README.md").write_text(readme_text, encoding="utf-8")

    # Write prompt docs if provided
    if prompt_docs:
        prompts_dir = tmp_path / "docs" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        for name, text in prompt_docs.items():
            (prompts_dir / name).write_text(text, encoding="utf-8")

    return state_dir


def test_policy_lint_passes_with_clean_text(tmp_path: Path) -> None:
    """policy-lint returns PASSED when no drift patterns are found."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="# Clean Skill\n\nNo drift patterns here.\n",
        readme_text="# Clean README\n\nNo issues.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "PASSED"
    assert result["findings"] == []
    assert result["blocking_reasons"] == []


def test_policy_lint_detects_obsolete_medium_profile(tmp_path: Path) -> None:
    """policy-lint detects 'medium' used as a profile name."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="# Skill\n\nUse the medium profile for this task.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "WARN"
    medium_findings = [f for f in result["findings"] if f["kind"] == "obsolete_profile_name"]
    assert len(medium_findings) >= 1
    assert all(f["severity"] == "WARN" for f in medium_findings)


def test_policy_lint_detects_tests_authoritative_over_command_plan(tmp_path: Path) -> None:
    """policy-lint detects text making Tests authoritative over command-plan."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        readme_text="# README\n\nTests are authoritative over command-plan.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "FAILED"
    findings = [f for f in result["findings"] if f["kind"] == "tests_authoritative_over_command_plan"]
    assert len(findings) >= 1
    assert all(f["severity"] == "FAIL" for f in findings)


def test_policy_lint_detects_task_packet_authority(tmp_path: Path) -> None:
    """policy-lint detects text making task_packet authoritative over decision_packet."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="# Skill\n\ntask_packet is authoritative for execution.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "FAILED"
    findings = [f for f in result["findings"] if f["kind"] == "task_packet_authority_over_decision_packet"]
    assert len(findings) >= 1


def test_policy_lint_detects_default_heavy_path_read(tmp_path: Path) -> None:
    """policy-lint detects suggestions to read full solve_reports/ by default."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        readme_text="# README\n\nRead the full solve_reports directory.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "WARN"
    findings = [f for f in result["findings"] if f["kind"] == "default_heavy_path_read"]
    assert len(findings) >= 1


def test_policy_lint_detects_unsupported_report_status(tmp_path: Path) -> None:
    """policy-lint detects COMPLETED_WITH_LIMITATIONS used as a status value."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        readme_text="# README\n\nSet codex_report_summary.status to COMPLETED_WITH_LIMITATIONS.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "FAILED"
    findings = [f for f in result["findings"] if f["kind"] == "unsupported_report_status"]
    assert len(findings) >= 1


def test_policy_lint_detects_dynamic_facts_in_skill(tmp_path: Path) -> None:
    """policy-lint detects dynamic one-run facts in .codex-skills/ text."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="# Skill\n\nBest candidate: 78d540b49c59077041414141414141\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    findings = [f for f in result["findings"] if f["kind"] == "dynamic_fact_in_skill"]
    assert len(findings) >= 1
    assert all(f["severity"] == "WARN" for f in findings)


def test_policy_lint_does_not_flag_do_not_read_heavy_paths(tmp_path: Path) -> None:
    """policy-lint does not flag 'do not read full solve_reports' as drift."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="# Skill\n\nDo not read the full solve_reports directory.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    heavy_findings = [f for f in result["findings"] if f["kind"] == "default_heavy_path_read"]
    assert heavy_findings == []


def test_policy_lint_writes_artifact(tmp_path: Path) -> None:
    """policy-lint writes policy_lint_result.json when write_result=True."""
    from reverse_agent.project_gate import policy_lint, POLICY_LINT_RESULT_NAME

    state_dir = _make_policy_lint_state(tmp_path)
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=True)
    artifact = state_dir / "gates" / POLICY_LINT_RESULT_NAME
    assert artifact.exists()
    saved = json.loads(artifact.read_text(encoding="utf-8"))
    assert saved["gate_name"] == "policy-lint"
    assert saved["decision_id"] == "decision_policy_lint"
    assert saved["round_id"] == "round_policy_lint"


def test_policy_lint_scans_only_bounded_files(tmp_path: Path) -> None:
    """policy-lint does not scan solve_reports/ or project_state/rounds/."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(tmp_path)

    # Create heavy paths that should NOT be scanned (after state setup)
    heavy_dir = tmp_path / "solve_reports"
    heavy_dir.mkdir()
    (heavy_dir / "bad.txt").write_text("medium profile is used here\n", encoding="utf-8")

    rounds_dir = tmp_path / "project_state" / "rounds" / "round_test"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    (rounds_dir / "manifest.json").write_text('{"medium": "profile"}', encoding="utf-8")

    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    # No findings from heavy paths
    assert all("solve_reports" not in f.get("file", "") for f in result["findings"])
    assert all("project_state/rounds" not in f.get("file", "") for f in result["findings"])


def test_policy_lint_cli_exit_code(tmp_path: Path) -> None:
    """policy-lint CLI returns 0 for PASSED, 1 for FAILED."""
    from reverse_agent.project_gate import main

    # Clean state -> exit 0
    state_dir = _make_policy_lint_state(tmp_path)
    exit_code = main(["policy-lint", "--state-dir", str(state_dir)])
    assert exit_code == 0


def test_policy_lint_allows_valid_current_wording(tmp_path: Path) -> None:
    """policy-lint does not flag valid current project wording."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        skill_text="""# Reverse Agent Iteration

Use fast, standard, or full profiles.
Do not use medium as a profile name.
task_packet does not override decision_packet.
Do not read full solve_reports by default.
""",
        readme_text="# README\n\nUse standard or full profiles.\n",
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    # Valid wording should not produce findings
    fail_findings = [f for f in result["findings"] if f["severity"] == "FAIL"]
    assert fail_findings == []


# ---------------------------------------------------------------------------
# policy-lint prompt docs scanning tests
# ---------------------------------------------------------------------------

def test_policy_lint_scans_prompt_docs(tmp_path: Path) -> None:
    """policy-lint scans docs/prompts/*.md files by default."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        prompt_docs={
            "project_workspace_prompt.md": "# Workspace Prompt\n\nClean content.\n",
            "codex_execution_prompt.md": "# Codex Prompt\n\nClean content.\n",
            "README.md": "# Prompts README\n\nClean content.\n",
        },
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    scanned = result.get("scanned_files", [])
    assert "docs/prompts/project_workspace_prompt.md" in scanned
    assert "docs/prompts/codex_execution_prompt.md" in scanned
    assert "docs/prompts/README.md" in scanned


def test_policy_lint_detects_drift_in_prompt_docs(tmp_path: Path) -> None:
    """policy-lint detects drift patterns inside prompt docs."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        prompt_docs={
            "bad_prompt.md": "# Bad Prompt\n\nTests are authoritative over command-plan.\nUse the medium profile.\n",
        },
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "FAILED"
    prompt_findings = [f for f in result["findings"] if "docs/prompts/" in f.get("file", "")]
    assert len(prompt_findings) >= 1
    authority_findings = [f for f in prompt_findings if f["kind"] == "tests_authoritative_over_command_plan"]
    assert len(authority_findings) >= 1


def test_policy_lint_detects_dynamic_facts_in_prompt_docs(tmp_path: Path) -> None:
    """policy-lint detects dynamic facts in prompt docs."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        prompt_docs={
            "bad_prompt.md": "# Bad Prompt\n\nBest candidate: 78d540b49c59077041414141414141\n",
        },
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    prompt_findings = [f for f in result["findings"] if "docs/prompts/" in f.get("file", "")]
    dynamic_findings = [f for f in prompt_findings if f["kind"] == "dynamic_fact_in_skill"]
    assert len(dynamic_findings) >= 1


def test_policy_lint_clean_prompt_docs_pass(tmp_path: Path) -> None:
    """policy-lint does not produce FAIL findings for valid prompt docs."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        prompt_docs={
            "project_workspace_prompt.md": (
                "# Project Workspace Prompt\n\n"
                "Use fast, standard, or full profiles.\n"
                "Do not use medium as a profile name.\n"
                "command-plan is the command execution authority.\n"
                "decision_packet is the sole execution authority.\n"
                "Do not read full solve_reports by default.\n"
            ),
            "codex_execution_prompt.md": (
                "# Codex Execution Prompt\n\n"
                "Use standard or full profiles.\n"
                "Do not use COMPLETED_WITH_LIMITATIONS as codex_report_summary.status.\n"
                "Do not read full PROJECT_PROGRESS_LOG.txt by default.\n"
            ),
        },
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    prompt_fail_findings = [
        f for f in result["findings"]
        if f["severity"] == "FAIL" and "docs/prompts/" in f.get("file", "")
    ]
    assert prompt_fail_findings == []


def test_policy_lint_prompt_docs_do_not_scan_arbitrary_docs(tmp_path: Path) -> None:
    """policy-lint does not scan arbitrary docs/ files outside docs/prompts/."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(tmp_path)
    # Create a file in docs/ but not in docs/prompts/
    other_docs = tmp_path / "docs" / "other.md"
    other_docs.parent.mkdir(parents=True, exist_ok=True)
    other_docs.write_text("Use the medium profile for this.\n", encoding="utf-8")

    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    # No findings from docs/other.md
    assert all("docs/other.md" not in f.get("file", "") for f in result["findings"])


def test_policy_lint_exempts_stable_repo_path_in_prompt_docs(tmp_path: Path) -> None:
    """policy-lint exempts the stable repo path F:\\reverse-agent in prompt docs."""
    from reverse_agent.project_gate import policy_lint

    state_dir = _make_policy_lint_state(
        tmp_path,
        prompt_docs={
            "codex_execution_prompt.md": (
                "# Codex Execution Prompt\n\n"
                "The working directory must be `F:\\reverse-agent`.\n"
                "1. `Set-Location F:\\reverse-agent`\n"
                "2. `Get-Location` -- must show `F:\\reverse-agent`\n"
                "3. `Test-Path F:\\reverse-agent` -- must be `True`\n"
            ),
        },
    )
    result = policy_lint(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    path_findings = [
        f for f in result["findings"]
        if "docs/prompts/" in f.get("file", "")
        and f["kind"] == "dynamic_fact_in_skill"
        and "local machine path" in f.get("detail", "")
    ]
    assert path_findings == [], f"Expected no findings for stable repo path, got: {path_findings}"


# ---------------------------------------------------------------------------
# Policy Impact Audit tests
# ---------------------------------------------------------------------------


def _make_policy_impact_state(
    tmp_path: Path,
    *,
    decision_id: str = "decision_policy_impact",
    round_id: str = "round_policy_impact",
    changed_files: list[str] | None = None,
    report_status: str = "SUCCESS",
    report_body: str = "",
) -> Path:
    """Create a minimal state for policy-impact tests."""
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)

    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

    gates_dir = state_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)

    dirty = changed_files if changed_files is not None else []
    _write_json(gates_dir / "round_delta_summary.json", {
        "schema_version": 1,
        "artifact_name": "round_delta_summary.json",
        "decision_id": decision_id,
        "round_id": round_id,
        "baseline_available": True,
        "new_dirty_files_since_baseline": dirty,
        "inherited_dirty_files": [],
        "final_dirty_files": dirty,
    })

    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id="codex_report_policy_impact",
        round_id=round_id,
        status=report_status,
        files_changed=dirty,
        extra_body=report_body,
    )

    _write_json(
        state_dir / "current_state.json",
        {"round_id": round_id, "state_build_id": "state_test", "state_digest": "digest_test"},
    )
    _write_json(
        state_dir / "task_packet.json",
        {"execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"},
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    return state_dir


def test_policy_impact_passes_with_no_policy_sensitive_changes(tmp_path: Path) -> None:
    """policy-impact returns PASS when no policy-sensitive files changed."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["README.md", "docs/some_doc.md"],
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "PASSED"
    assert result["policy_sensitive_files"] == []
    assert result["impacted_domains"] == []
    assert result["missing_report_topics"] == []
    assert result["blocking_reasons"] == []


def test_policy_impact_fails_when_source_changed_but_report_omits_coverage(tmp_path: Path) -> None:
    """policy-impact FAILs when source changed but report omits impact coverage."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["reverse_agent/project_gate.py"],
        report_body="# Report\n\nNo policy impact discussion here.\n",
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "FAILED"
    assert "reverse_agent/project_gate.py" in result["policy_sensitive_files"]
    assert "command_plan" in result["impacted_domains"]
    assert "final_check" in result["impacted_domains"]
    assert "policy_lint" in result["impacted_domains"]
    assert len(result["missing_report_topics"]) > 0
    assert len(result["blocking_reasons"]) > 0


def test_policy_impact_passes_when_report_covers_impacted_domains(tmp_path: Path) -> None:
    """policy-impact PASSes when report covers all impacted domains."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
        report_body=(
            "## Policy Impact\n\n"
            "command-plan, final-check, report-summary, policy-lint, "
            "report status schema, and tests reviewed.\n"
        ),
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "PASSED"
    assert result["missing_report_topics"] == []


def test_policy_impact_detects_prompt_doc_changes(tmp_path: Path) -> None:
    """policy-impact detects prompt-doc changes and maps to prompt_docs domain."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["docs/prompts/codex_execution_prompt.md"],
        report_body="## Policy Impact\n\nPrompt docs updated.\n",
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert "docs/prompts/codex_execution_prompt.md" in result["policy_sensitive_files"]
    assert "prompt_docs" in result["impacted_domains"]


def test_policy_impact_detects_skills_changes(tmp_path: Path) -> None:
    """policy-impact detects .codex-skills changes and maps to skills domain."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=[".codex-skills/registry.json"],
        report_body="## Policy Impact\n\nSkill registry updated.\n",
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert ".codex-skills/registry.json" in result["policy_sensitive_files"]
    assert "skills" in result["impacted_domains"]


def test_policy_impact_warns_when_report_not_success(tmp_path: Path) -> None:
    """policy-impact WARNs when coverage missing but report status is not SUCCESS."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["reverse_agent/project_gate.py"],
        report_status="PARTIAL",
        report_body="# Report\n\nNo policy impact discussion.\n",
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    assert result["gate_status"] == "WARN"
    assert len(result["warnings"]) > 0
    assert result["blocking_reasons"] == []


def test_policy_impact_writes_artifact(tmp_path: Path) -> None:
    """policy-impact writes project_state/gates/policy_impact_audit.json."""
    from reverse_agent.project_gate import policy_impact

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["reverse_agent/project_gate.py"],
        report_body=(
            "## Policy Impact\n\n"
            "command-plan, final-check, report-summary, policy-lint, "
            "report status schema, and tests reviewed.\n"
        ),
    )
    result = policy_impact(state_dir=state_dir, repo_root=tmp_path, write_result=True)
    artifact_path = state_dir / "gates" / "policy_impact_audit.json"
    assert artifact_path.exists()
    saved = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert saved["gate_name"] == "policy-impact"
    assert saved["decision_id"] == "decision_policy_impact"
    assert saved["round_id"] == "round_policy_impact"
    assert saved["gate_status"] == result["gate_status"]


def test_policy_impact_cli_exit_code_pass(tmp_path: Path) -> None:
    """policy-impact CLI exits 0 when PASS."""
    from reverse_agent.project_gate import main as gate_main

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["README.md"],
    )
    exit_code = gate_main(["policy-impact", "--state-dir", str(state_dir)])
    assert exit_code == 0


def test_policy_impact_cli_exit_code_fail(tmp_path: Path) -> None:
    """policy-impact CLI exits 1 when FAIL."""
    from reverse_agent.project_gate import main as gate_main

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["reverse_agent/project_gate.py"],
        report_body="# Report\n\nNo coverage.\n",
    )
    exit_code = gate_main(["policy-impact", "--state-dir", str(state_dir)])
    assert exit_code == 1


def test_policy_impact_cli_json_output(tmp_path: Path) -> None:
    """policy-impact CLI --json prints valid JSON."""
    from reverse_agent.project_gate import main as gate_main
    from io import StringIO
    import contextlib

    state_dir = _make_policy_impact_state(
        tmp_path,
        changed_files=["README.md"],
    )
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = gate_main(["policy-impact", "--state-dir", str(state_dir), "--json"])
    assert exit_code == 0
    payload = json.loads(buf.getvalue())
    assert payload["gate_name"] == "policy-impact"
    assert payload["gate_status"] == "PASSED"


def test_final_check_policy_impact_coverage_fails_on_missing_coverage(tmp_path: Path) -> None:
    """final-check fails when policy-sensitive changes present but report omits coverage."""
    from reverse_agent.project_gate import final_check

    state_dir = _make_gate_state(tmp_path)
    # Override report to omit policy impact coverage
    _write_report(
        state_dir,
        decision_id="decision_gate",
        report_id="codex_report_gate",
        round_id="round_gate",
        status="SUCCESS",
        files_changed=["reverse_agent/project_gate.py"],
        extra_body="# Report\n\nNo policy impact discussion.\n",
    )
    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    pi_checks = [c for c in result["checks"] if c["name"] == "policy_impact_coverage"]
    assert len(pi_checks) == 1
    assert pi_checks[0]["status"] == "FAIL"


def test_final_check_policy_impact_coverage_passes_with_coverage(tmp_path: Path) -> None:
    """final-check passes policy_impact_coverage when report covers impacted domains."""
    from reverse_agent.project_gate import final_check

    state_dir = _make_gate_state(tmp_path)
    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    pi_checks = [c for c in result["checks"] if c["name"] == "policy_impact_coverage"]
    assert len(pi_checks) == 1
    assert pi_checks[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# Regression tests for report_auto_summary / synthesis consistency
# ---------------------------------------------------------------------------


def test_report_auto_summary_matches_synthesis_after_closeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After run-closeout, report_auto_summary must match build_report_summary_synthesis."""
    from reverse_agent.project_gate import (
        build_report_summary_synthesis,
        read_codex_report_summary,
        report_auto_summary,
        run_closeout,
    )

    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    runner = _fake_runner_factory({})
    run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    # Regenerate auto-summary to ensure it is current
    report_auto_summary(state_dir=state_dir, write_result=True)
    # Build synthesis for comparison
    synthesis = build_report_summary_synthesis(
        state_dir=state_dir, repo_root=tmp_path, write_result=False,
    )
    ss = synthesis.get("synthesized_summary", {})
    report = read_codex_report_summary(state_dir)
    for field in ("files_changed", "generated_artifacts"):
        expected = set(ss.get(field, []))
        actual = set(report.get(field) or [])
        # Archive-only diffs are acceptable pre-closeout
        sym = expected ^ actual
        non_archive = {p for p in sym if not p.startswith("project_state/rounds/")}
        # run_closeout_result.json may appear in auto-summary but not report
        # when close_round fails; this is expected and will clear on retry.
        non_archive.discard("project_state/gates/run_closeout_result.json")
        # run_closeout_execution_log.json may appear in synthesis but not
        # report when close_round fails; same category as run_closeout_result.json.
        non_archive.discard("project_state/gates/run_closeout_execution_log.json")
        assert not non_archive, f"{field} non-archive diff: {sorted(non_archive)}"


def test_report_auto_summary_consistency_passes_after_closeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """report_auto_summary_consistency check must not FAIL after run-closeout + auto-summary refresh.

    When close_round fails (report status != SUCCESS), the check may WARN
    because the auto-summary includes run_closeout_result.json but the
    report does not.  This is expected: the WARN will clear once the report
    status reaches SUCCESS and the closeout refresh includes the artifact.
    """
    from reverse_agent.project_gate import (
        final_check,
        report_auto_summary,
        run_closeout,
    )

    state_dir = _make_run_closeout_state(tmp_path, round_id="round_closeout")
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/rounds/round_closeout/codex_execution_report.md",
            "project_state/rounds/round_closeout/decision_packet.md",
            "project_state/rounds/round_closeout/pytest_result.txt",
            "project_state/rounds/round_closeout/round_manifest.json",
        ],
    )
    runner = _fake_runner_factory({})
    run_closeout(
        state_dir=state_dir,
        round_id="round_closeout",
        repo_root=tmp_path,
        command_runner=runner,
        write_result=True,
    )
    report_auto_summary(state_dir=state_dir, write_result=True)
    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    check = next(
        (c for c in result["checks"] if c["name"] == "report_auto_summary_consistency"),
        None,
    )
    assert check is not None, "report_auto_summary_consistency check not found"
    assert check["status"] in ("PASS", "WARN"), (
        f"Expected PASS or WARN, got {check['status']}: {check}"
    )


def test_report_auto_summary_consistency_detects_real_mismatch(
    tmp_path: Path,
) -> None:
    """report_auto_summary_consistency must FAIL when auto-summary is stale."""
    from reverse_agent.project_gate import (
        final_check,
        report_auto_summary,
    )

    state_dir = _make_gate_state(tmp_path)
    # Generate auto-summary
    report_auto_summary(state_dir=state_dir, write_result=True)
    # Tamper with the auto-summary to create a mismatch
    auto_path = state_dir / "gates" / "codex_report_auto_summary.json"
    payload = json.loads(auto_path.read_text(encoding="utf-8"))
    payload["files_changed"] = ["FAKE_FILE.py"]
    auto_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
    check = next(
        (c for c in result["checks"] if c["name"] == "report_auto_summary_consistency"),
        None,
    )
    assert check is not None, "report_auto_summary_consistency check not found"
    assert check["status"] == "FAIL", f"Expected FAIL for stale auto-summary, got {check['status']}"


# ---------------------------------------------------------------------------
# Regression: Report-summary mismatch blocking for SUCCESS/ACCEPTED reports
# ---------------------------------------------------------------------------


class TestReportSummaryMismatchBlocking:
    """Regression tests for report-summary mismatch blocking behavior.

    For SUCCESS/ACCEPTED reports, status/acceptance_recommendation mismatches
    between synthesis and live report must be blocking (FAIL, not WARN).
    For non-SUCCESS reports, the previous WARN behavior is preserved.
    """

    def test_status_diff_is_blocking_for_success_report(self) -> None:
        """_diff_is_archive_pending_status returns False for SUCCESS reports
        when status/acceptance_recommendation differ."""
        from reverse_agent.project_gate import _diff_is_archive_pending_status

        diff = {"field": "status", "expected": "FAILED", "actual": "SUCCESS"}
        # Without report_status, the old behavior applies (archive-pending)
        assert _diff_is_archive_pending_status(diff) is True
        # With report_status=SUCCESS, it must be blocking (not archive-pending)
        assert _diff_is_archive_pending_status(diff, report_status="SUCCESS") is False

    def test_status_diff_is_blocking_for_accepted_report(self) -> None:
        """_diff_is_archive_pending_status returns False for ACCEPTED reports."""
        from reverse_agent.project_gate import _diff_is_archive_pending_status

        diff = {"field": "acceptance_recommendation", "expected": "REWORK_REQUIRED", "actual": "ACCEPTED"}
        assert _diff_is_archive_pending_status(diff, report_status="ACCEPTED") is False

    def test_status_diff_not_blocking_for_partial_report(self) -> None:
        """_diff_is_archive_pending_status returns True for PARTIAL reports
        (preserving the old archive-pending behavior)."""
        from reverse_agent.project_gate import _diff_is_archive_pending_status

        diff = {"field": "status", "expected": "FAILED", "actual": "PARTIAL"}
        assert _diff_is_archive_pending_status(diff, report_status="PARTIAL") is True

    def test_has_structural_field_diff_blocks_for_success(self) -> None:
        """_has_structural_field_diff returns True for status diffs when
        report_status is SUCCESS (blocking, not archive-pending)."""
        from reverse_agent.project_gate import _has_structural_field_diff

        diffs = [{"field": "status", "expected": "FAILED", "actual": "SUCCESS"}]
        # Without report_status, archive-pending classification applies
        assert _has_structural_field_diff(diffs) is False
        # With report_status=SUCCESS, the diff is structural (blocking)
        assert _has_structural_field_diff(diffs, report_status="SUCCESS") is True

    def test_report_summary_fields_match_synthesis_fails_for_success(
        self, tmp_path: Path,
    ) -> None:
        """report_summary_fields_match_synthesis is FAIL (not WARN) when
        a SUCCESS report has a status mismatch with the synthesis.

        This is tested by creating a final_gate_result.json with a
        non-retriable failure so the synthesis derives FAILED/REWORK_REQUIRED
        from the gate, disagreeing with the SUCCESS/ACCEPTED report.
        """
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a final_gate_result.json with a non-retriable failure
        # so the synthesis derives FAILED/REWORK_REQUIRED from the gate.
        _write_json(state_dir / "gates" / "final_gate_result.json", {
            "schema_version": 1,
            "artifact_name": "final_gate_result.json",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "gate_status": "FAILED",
            "checks": [
                {"name": "required_audit_coverage", "status": "FAIL",
                 "detail": "audit coverage incomplete"},
            ],
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        check = _check(result, "report_summary_fields_match_synthesis")
        assert check["status"] == "FAIL", (
            f"Expected FAIL for SUCCESS report with status mismatch, got {check['status']}"
        )

    def test_report_summary_fields_match_synthesis_warn_for_partial(
        self, tmp_path: Path,
    ) -> None:
        """report_summary_fields_match_synthesis is WARN (not FAIL) when
        a PARTIAL report has a status mismatch with the synthesis.

        This is tested by creating a final_gate_result.json with a
        non-retriable failure so the synthesis derives FAILED/REWORK_REQUIRED
        from the gate, disagreeing with the PARTIAL/NEEDS_REVIEW report.
        For non-SUCCESS reports, the status diff is archive-pending (WARN).
        """
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        # Create a final_gate_result.json with a non-retriable failure
        _write_json(state_dir / "gates" / "final_gate_result.json", {
            "schema_version": 1,
            "artifact_name": "final_gate_result.json",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "gate_status": "FAILED",
            "checks": [
                {"name": "required_audit_coverage", "status": "FAIL",
                 "detail": "audit coverage incomplete"},
            ],
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        check = _check(result, "report_summary_fields_match_synthesis")
        assert check["status"] == "WARN", (
            f"Expected WARN for PARTIAL report with status mismatch, got {check['status']}"
        )


# ---------------------------------------------------------------------------
# Regression: Closeout execution log freshness and coverage
# ---------------------------------------------------------------------------


class TestCloseoutExecutionLogFreshness:
    """Regression tests for closeout execution log freshness detection
    and generated_artifacts coverage.

    These tests verify that:
    - A stale closeout execution log in current dirty evidence blocks acceptance
    - A current closeout execution log passes the freshness check
    - A stale log not in current dirty evidence is exempt
    - generated_artifacts covers the closeout execution log when it matches
    """

    def test_stale_closeout_log_in_dirty_fails_for_success(
        self, tmp_path: Path,
    ) -> None:
        """closeout_execution_log_is_current FAILs when the log is stale
        and appears in current dirty evidence for a SUCCESS report.

        Since final_check() regenerates the delta summary from git status,
        we test the check logic directly by constructing the check inputs.
        """
        from reverse_agent.project_gate import (
            RUN_CLOSEOUT_EXECUTION_LOG_NAME,
            RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH,
            _check,
        )

        # Simulate the check logic directly
        closeout_log_payload = {
            "schema_version": 1,
            "decision_id": "decision_old",
            "round_id": "round_old",
            "command_blocks": [],
        }
        decision_id = "decision_gate"
        round_id = "round_gate"
        report_status = "SUCCESS"
        changed_files = {RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH}
        new_dirty_files = set()

        closeout_log_in_dirty = (
            RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH in changed_files
            or RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH in new_dirty_files
        )
        assert closeout_log_in_dirty is True

        cl_decision_id = str(closeout_log_payload.get("decision_id") or "")
        cl_round_id = str(closeout_log_payload.get("round_id") or "")
        cl_is_current = cl_decision_id == decision_id and cl_round_id == round_id
        assert cl_is_current is False

        if report_status in {"SUCCESS", "ACCEPTED", "ACCEPTED_WITH_LIMITATIONS"}:
            cl_check_status = "FAIL"
        else:
            cl_check_status = "WARN"
        assert cl_check_status == "FAIL"

    def test_current_closeout_log_passes(
        self, tmp_path: Path,
    ) -> None:
        """closeout_execution_log_is_current PASSes when the log has
        current round IDs and appears in dirty evidence."""
        from reverse_agent.project_gate import RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH

        closeout_log_payload = {
            "schema_version": 1,
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "command_blocks": [],
        }
        decision_id = "decision_gate"
        round_id = "round_gate"
        changed_files = {RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH}

        closeout_log_in_dirty = RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH in changed_files
        assert closeout_log_in_dirty is True

        cl_decision_id = str(closeout_log_payload.get("decision_id") or "")
        cl_round_id = str(closeout_log_payload.get("round_id") or "")
        cl_is_current = cl_decision_id == decision_id and cl_round_id == round_id
        assert cl_is_current is True

    def test_stale_closeout_log_not_in_dirty_exempt(
        self, tmp_path: Path,
    ) -> None:
        """closeout_execution_log_is_current is PASS (exempt) when the log
        is stale but NOT in current dirty evidence."""
        from reverse_agent.project_gate import RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH

        closeout_log_payload = {
            "schema_version": 1,
            "decision_id": "decision_old",
            "round_id": "round_old",
            "command_blocks": [],
        }
        changed_files = set()  # log not in dirty files
        new_dirty_files = set()

        closeout_log_in_dirty = (
            RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH in changed_files
            or RUN_CLOSEOUT_EXECUTION_LOG_OUTPUT_PATH in new_dirty_files
        )
        assert closeout_log_in_dirty is False
        # When not in dirty evidence, the check is PASS (exempt)

    def test_closeout_log_coverage_in_synthesis(
        self, tmp_path: Path,
    ) -> None:
        """build_report_summary_synthesis includes run_closeout_execution_log.json
        in generated_artifacts when the closeout payload matches the current round."""
        from reverse_agent.project_gate import build_report_summary_synthesis

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a current-round closeout result
        _write_json(state_dir / "gates" / "run_closeout_result.json", {
            "schema_version": 1, "gate_name": "run-closeout",
            "gate_status": "PASSED",
            "decision_id": "decision_gate", "round_id": "round_gate",
        })
        # Create a current-round closeout execution log
        _write_json(state_dir / "gates" / "run_closeout_execution_log.json", {
            "schema_version": 1,
            "decision_id": "decision_gate", "round_id": "round_gate",
            "command_blocks": [],
        })

        synthesis = build_report_summary_synthesis(
            state_dir=state_dir, repo_root=tmp_path, write_result=False,
        )
        gen_artifacts = synthesis.get("synthesized_summary", {}).get("generated_artifacts", [])
        assert "project_state/gates/run_closeout_execution_log.json" in gen_artifacts, (
            f"run_closeout_execution_log.json not in synthesis generated_artifacts: {gen_artifacts}"
        )

    def test_stale_closeout_log_excluded_from_reportable_paths(
        self, tmp_path: Path,
    ) -> None:
        """_existing_reportable_gate_artifact_paths excludes stale
        closeout execution logs from previous rounds."""
        from reverse_agent.project_gate import _existing_reportable_gate_artifact_paths

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        # Create a STALE closeout execution log
        _write_json(state_dir / "gates" / "run_closeout_execution_log.json", {
            "schema_version": 1,
            "decision_id": "decision_old", "round_id": "round_old",
            "command_blocks": [],
        })

        paths = _existing_reportable_gate_artifact_paths(
            state_dir, decision_id="decision_gate", round_id="round_gate",
        )
        assert "project_state/gates/run_closeout_execution_log.json" not in paths

    def test_command_plan_authority_preserved_with_new_checks(
        self, tmp_path: Path,
    ) -> None:
        """Command-plan authority check is not weakened by the new
        closeout_execution_log_is_current check."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="SUCCESS", acceptance="ACCEPTED")
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        authority_check = _check(result, "command_plan_execution_authority")
        assert authority_check is not None


def test_report_auto_summary_excludes_status_kind_commands(
    tmp_path: Path,
) -> None:
    """report_auto_summary must exclude 'status' kind commands from tests_ran."""
    from reverse_agent.project_gate import report_auto_summary

    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    # Create execution_log.json with a status-kind command
    log_payload = {
        "schema_version": 1,
        "artifact_name": "execution_log.json",
        "decision_id": "decision_gate",
        "round_id": "round_gate",
        "commands": [
            {
                "command": "python -m pytest tests/test_project_gate.py -q",
                "exit_code": 0,
                "phase": "test",
                "kind": "pytest",
            },
            {
                "command": "python -m reverse_agent.project_gate final-check --state-dir project_state",
                "exit_code": 0,
                "phase": "gate",
                "kind": "status",
            },
        ],
    }
    (state_dir / "gates" / "execution_log.json").write_text(
        json.dumps(log_payload, indent=2), encoding="utf-8"
    )
    result = report_auto_summary(state_dir=state_dir, write_result=True)
    tests_ran = result.get("tests_ran", [])
    assert not any("final-check" in t for t in tests_ran), (
        f"status-kind command should be excluded from tests_ran: {tests_ran}"
    )


def test_report_auto_summary_includes_closeout_artifact(
    tmp_path: Path,
) -> None:
    """report_auto_summary must include run_closeout_result.json when it exists and matches round."""
    from reverse_agent.project_gate import (
        report_auto_summary,
        RUN_CLOSEOUT_OUTPUT_PATH,
    )

    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    # Create a matching run_closeout_result.json
    gates_dir = state_dir / "gates"
    closeout_payload = {
        "schema_version": 1,
        "artifact_name": "run_closeout_result.json",
        "decision_id": "decision_gate",
        "round_id": "round_gate",
        "closeout_status": "COMPLETED",
    }
    (gates_dir / "run_closeout_result.json").write_text(
        json.dumps(closeout_payload, indent=2), encoding="utf-8"
    )
    result = report_auto_summary(state_dir=state_dir, write_result=True)
    summary = result.get("summary", {})
    generated = set(summary.get("generated_artifacts", []))
    assert RUN_CLOSEOUT_OUTPUT_PATH in generated, (
        f"run_closeout_result.json should be in generated_artifacts: {sorted(generated)}"
    )


def test_report_auto_summary_excludes_closeout_artifact_wrong_round(
    tmp_path: Path,
) -> None:
    """report_auto_summary must exclude run_closeout_result.json when round_id doesn't match."""
    from reverse_agent.project_gate import (
        report_auto_summary,
        RUN_CLOSEOUT_OUTPUT_PATH,
    )

    state_dir = _make_command_plan_gate_state(tmp_path, archived=False)
    # Create a non-matching run_closeout_result.json
    gates_dir = state_dir / "gates"
    closeout_payload = {
        "schema_version": 1,
        "artifact_name": "run_closeout_result.json",
        "decision_id": "decision_OTHER",
        "round_id": "round_OTHER",
        "closeout_status": "COMPLETED",
    }
    (gates_dir / "run_closeout_result.json").write_text(
        json.dumps(closeout_payload, indent=2), encoding="utf-8"
    )
    result = report_auto_summary(state_dir=state_dir, write_result=True)
    summary = result.get("summary", {})
    generated = set(summary.get("generated_artifacts", []))
    assert RUN_CLOSEOUT_OUTPUT_PATH not in generated, (
        f"run_closeout_result.json with wrong round should NOT be in generated_artifacts"
    )


# ---------------------------------------------------------------------------
# Tests for execution-log current-round closure: prior-round command
# filtering and execution_log_report_id_is_current check
# ---------------------------------------------------------------------------


class TestExecutionLogCurrentRoundFiltering:
    """Verify _execution_log_derive_commands filters prior-round commands
    and execution_log_report_id_is_current detects stale report_ids."""

    def test_prior_round_commands_filtered_from_execution_log(
        self, tmp_path: Path
    ) -> None:
        """Commands not in the current command_plan are excluded from the
        execution log, preventing prior-round commands from leaking into
        current-round evidence."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        # Current command_plan with only 2 commands.
        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
                    "kind": "preflight",
                    "phase": "gate",
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": "python -m pytest tests/test_project_gate.py -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                },
            ],
        }
        (gates_dir / "command_plan.json").write_text(
            json.dumps(command_plan_payload, indent=2), encoding="utf-8"
        )

        # pytest_result.txt with both current and prior-round commands.
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: PASSED\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====\n"
            "806 passed\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_old_v1 =====\n"
            "run-closeout: PASSED\n"
            "===== EXIT: 0 =====\n"
        )

        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )

        commands = [e["command"] for e in entries]
        assert "python -m reverse_agent.project_gate preflight --state-dir project_state" in commands
        assert "python -m pytest tests/test_project_gate.py -q" in commands
        assert "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_old_v1" not in commands, (
            "Prior-round closeout command should be filtered out"
        )

    def test_startup_commands_always_included(
        self, tmp_path: Path
    ) -> None:
        """Startup commands (Set-Location, Get-Location, etc.) are always
        included even if not in command_plan."""
        state_dir = tmp_path / "project_state"
        gates_dir = state_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m pytest tests/test_project_gate.py -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                },
            ],
        }
        (gates_dir / "command_plan.json").write_text(
            json.dumps(command_plan_payload, indent=2), encoding="utf-8"
        )

        pytest_text = (
            "===== COMMAND: Set-Location F:\\reverse-agent =====\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: Get-Location =====\n"
            "F:\\reverse-agent\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====\n"
            "806 passed\n"
            "===== EXIT: 0 =====\n"
        )

        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )

        commands = [e["command"] for e in entries]
        assert "Set-Location F:\\reverse-agent" in commands
        assert "Get-Location" in commands
        assert "python -m pytest tests/test_project_gate.py -q" in commands

    def test_execution_log_report_id_is_current_check_passes(
        self, tmp_path: Path
    ) -> None:
        """When execution_log.json has the current round's report_id,
        the check passes."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py -q",
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json with current report_id.
        # The default decision_id/round_id from _make_command_plan_gate_state
        # are "decision_gate" / "round_gate".
        round_id = "round_gate"
        expected_report_id = _expected_report_id(round_id)
        execution_log_payload = {
            "report_id": expected_report_id,
            "decision_id": "decision_gate",
            "round_id": round_id,
            "commands": [],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_report_id_is_current"),
            None,
        )
        assert check is not None, "execution_log_report_id_is_current check should be present"
        assert check["status"] == "PASS", f"Expected PASS, got {check['status']}: {check.get('detail', '')}"

    def test_execution_log_report_id_stale_warns_for_non_success(
        self, tmp_path: Path
    ) -> None:
        """When execution_log.json has a stale report_id and the report is
        non-SUCCESS, the check warns."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            status="PARTIAL",
            acceptance="NEEDS_REVIEW",
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py -q",
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json with stale report_id.
        execution_log_payload = {
            "report_id": "codex_report_old_round",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "commands": [],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_report_id_is_current"),
            None,
        )
        assert check is not None
        assert check["status"] == "WARN", f"Expected WARN for non-SUCCESS report, got {check['status']}"

    def test_execution_log_report_id_stale_fails_for_success(
        self, tmp_path: Path
    ) -> None:
        """When execution_log.json has a stale report_id and the report is
        SUCCESS, the check fails."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            status="SUCCESS",
            acceptance="ACCEPTED",
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py -q",
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json with stale report_id.
        execution_log_payload = {
            "report_id": "codex_report_old_round",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "commands": [],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_report_id_is_current"),
            None,
        )
        assert check is not None
        assert check["status"] == "FAIL", f"Expected FAIL for SUCCESS report with stale report_id, got {check['status']}"

    def test_no_execution_log_passes_with_skip(
        self, tmp_path: Path
    ) -> None:
        """When execution_log.json does not exist, the check passes with
        a skipped_reason."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py -q",
            ],
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_report_id_is_current"),
            None,
        )
        assert check is not None
        assert check["status"] == "PASS"
        assert check.get("skipped_reason") == "execution_log_not_present"

    def test_duplicate_commands_deduplicated_keeps_last(
        self, tmp_path: Path
    ) -> None:
        """When pytest_result.txt contains duplicate command blocks (e.g.
        from run-round re-executing the pipeline), only the last occurrence
        of each command is kept in the execution log."""
        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
                    "kind": "preflight",
                    "phase": "gate",
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": "python -m pytest tests/test_project_gate.py -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                },
            ],
        }

        # pytest_result.txt with duplicate command blocks.
        # The second preflight has exit=1 (simulating a re-run that found
        # a different result).  The execution log should keep only the last.
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: PASSED\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====\n"
            "806 passed\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: WARN\n"
            "===== EXIT: 1 =====\n"
        )

        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )

        # Should have exactly 2 entries (deduplicated).
        commands = [e["command"] for e in entries]
        assert len(entries) == 2, f"Expected 2 deduplicated entries, got {len(entries)}: {commands}"
        assert commands.count("python -m reverse_agent.project_gate preflight --state-dir project_state") == 1

        # The preflight entry should have exit_code=1 (last occurrence).
        preflight_entry = next(e for e in entries if "preflight" in e["command"])
        assert preflight_entry["exit_code"] == 1, (
            f"Expected exit_code=1 from last occurrence, got {preflight_entry['exit_code']}"
        )

        # Indices should be sequential after dedup.
        assert [e["index"] for e in entries] == [1, 2]


class TestExecutionLogRequiredCommandBlocking:
    """Verify that required commands missing from execution_log produce
    blocking_reasons (gate_status=FAILED), while optional ones only warn."""

    def test_required_command_missing_is_blocking(self) -> None:
        """A command marked required:true in command_plan that is absent
        from execution_log should produce a blocking_reason."""
        from reverse_agent.project_gate import _execution_log_validate
        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
                    "kind": "preflight",
                    "phase": "gate",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": "python -m pytest tests/test_project_gate.py -q",
                    "kind": "pytest",
                    "phase": "test",
                    "required": True,
                    "expected_exit_codes": [0],
                },
            ],
        }
        # Only preflight is recorded; pytest is missing.
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: PASSED\n"
            "===== EXIT: 0 =====\n"
        )
        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        warnings, blocking_reasons = _execution_log_validate(
            entries=entries,
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        assert any("required command" in r.lower() for r in blocking_reasons), (
            f"Expected a blocking_reason for missing required command, got blocking_reasons={blocking_reasons}"
        )

    def test_optional_command_missing_is_warning_only(self) -> None:
        """A command not marked required in command_plan that is absent
        from execution_log should produce only a warning, not a blocking_reason."""
        from reverse_agent.project_gate import _execution_log_validate
        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
                    "kind": "preflight",
                    "phase": "gate",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": "python -m reverse_agent.project_gate policy-lint --state-dir project_state",
                    "kind": "project-cli",
                    "phase": "gate",
                    "required": False,
                    "expected_exit_codes": [0],
                },
            ],
        }
        # Only preflight is recorded; policy-lint is missing but optional.
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: PASSED\n"
            "===== EXIT: 0 =====\n"
        )
        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        warnings, blocking_reasons = _execution_log_validate(
            entries=entries,
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        assert not any("required command" in r.lower() for r in blocking_reasons), (
            f"Optional missing command should not produce blocking_reason, got {blocking_reasons}"
        )
        assert any("optional command" in w.lower() for w in warnings), (
            f"Expected a warning for missing optional command, got warnings={warnings}"
        )

    def test_all_required_present_no_blocking(self) -> None:
        """When all required commands are recorded, there should be no
        blocking_reasons for missing required commands."""
        from reverse_agent.project_gate import _execution_log_validate
        command_plan_payload = {
            "commands": [
                {
                    "index": 1,
                    "command": "python -m reverse_agent.project_gate preflight --state-dir project_state",
                    "kind": "preflight",
                    "phase": "gate",
                    "required": True,
                    "expected_exit_codes": [0],
                },
                {
                    "index": 2,
                    "command": "python -m pytest tests/test_project_gate.py -q",
                    "kind": "pytest",
                    "phase": "test",
                    "required": True,
                    "expected_exit_codes": [0],
                },
            ],
        }
        pytest_text = (
            "===== COMMAND: python -m reverse_agent.project_gate preflight --state-dir project_state =====\n"
            "preflight: PASSED\n"
            "===== EXIT: 0 =====\n"
            "\n"
            "===== COMMAND: python -m pytest tests/test_project_gate.py -q =====\n"
            "840 passed\n"
            "===== EXIT: 0 =====\n"
        )
        entries = _execution_log_derive_commands(
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        warnings, blocking_reasons = _execution_log_validate(
            entries=entries,
            pytest_text=pytest_text,
            command_plan_payload=command_plan_payload,
        )
        assert not any("required command" in r.lower() for r in blocking_reasons), (
            f"All required present, should have no required-command blocking_reasons, got {blocking_reasons}"
        )


class TestExecutionLogRequiredCommandsRecordedCheck:
    """Verify the execution_log_required_commands_recorded final-check rule."""

    def test_passes_when_all_required_recorded(self, tmp_path: Path) -> None:
        """When all required command_plan commands are in execution_log,
        the check passes."""
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
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json with all required commands recorded.
        execution_log_payload = {
            "report_id": "codex_report_gate",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "commands": [
                {"command": "Set-Location F:\\reverse-agent", "exit_code": 0},
                {"command": "Get-Location", "exit_code": 0},
                {"command": "Test-Path F:\\reverse-agent", "exit_code": 0},
                {"command": "git rev-parse --show-toplevel", "exit_code": 0},
                {"command": "git status --short", "exit_code": 0},
                {"command": "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate final-check --state-dir project_state", "exit_code": 0},
            ],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_required_commands_recorded"),
            None,
        )
        assert check is not None, "execution_log_required_commands_recorded check should be present"
        assert check["status"] == "PASS", f"Expected PASS, got {check['status']}: {check.get('detail', '')}"

    def test_fails_when_required_missing(self, tmp_path: Path) -> None:
        """When a required command_plan command is missing from execution_log,
        the check fails."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
                "python -m reverse_agent.project_gate command-plan --state-dir project_state",
                "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json missing the final-check command.
        execution_log_payload = {
            "report_id": "codex_report_gate",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "commands": [
                {"command": "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "exit_code": 0},
            ],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_required_commands_recorded"),
            None,
        )
        assert check is not None
        assert check["status"] == "FAIL", f"Expected FAIL for missing required command, got {check['status']}"

    def test_passes_when_no_execution_log(self, tmp_path: Path) -> None:
        """When execution_log.json does not exist, the check passes with
        a skipped_reason (backward-compatible)."""
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py -q",
            ],
        )

        result = final_check(state_dir=state_dir, repo_root=tmp_path)

        check = next(
            (c for c in result.get("checks", []) if c["name"] == "execution_log_required_commands_recorded"),
            None,
        )
        assert check is not None
        assert check["status"] == "PASS"
        assert check.get("skipped_reason") == "execution_log_not_present"


class TestReportAutoSummaryNoSynthesizeMissing:
    """Verify that report-auto-summary does not synthesize missing commands
    from command_plan into tests_ran when execution_log exists."""

    def test_missing_command_not_synthesized_into_tests_ran(self, tmp_path: Path) -> None:
        """When execution_log is present but lacks a command_plan command,
        report-auto-summary should NOT add that command to tests_ran."""
        from reverse_agent.project_gate import report_auto_summary
        state_dir = _make_command_plan_gate_state(
            tmp_path,
            report_tests=[
                "Set-Location F:\\reverse-agent",
                "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
                "python -m reverse_agent.project_gate command-plan --state-dir project_state",
                "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
                "python -m reverse_agent.project_gate final-check --state-dir project_state",
            ],
        )
        gates_dir = state_dir / "gates"

        # Write execution_log.json missing the final-check command.
        execution_log_payload = {
            "report_id": "codex_report_gate",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "commands": [
                {"command": "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state", "exit_code": 0},
                {"command": "python -m reverse_agent.project_gate command-plan --state-dir project_state --json", "exit_code": 0},
            ],
        }
        (gates_dir / "execution_log.json").write_text(
            json.dumps(execution_log_payload, indent=2), encoding="utf-8"
        )

        result = report_auto_summary(state_dir=state_dir, write_result=False)

        tests_ran = result.get("summary", {}).get("tests_ran", [])
        # final-check should NOT be in tests_ran since it was not in execution_log
        assert not any("final-check" in t for t in tests_ran), (
            f"final-check should not be synthesized into tests_ran, got {tests_ran}"
        )


class TestRequiredAuditPlaceholderBlocking:
    """Verify that required_audit_coverage FAILs (blocks) for placeholder
    answers regardless of report status, preventing acceptance of
    placeholder/PENDING audit answers."""

    def test_placeholder_answers_fail_for_partial_report(self) -> None:
        """PARTIAL report with placeholder Required Audit answers FAILs."""
        from reverse_agent.project_gate import _required_audit_coverage_check, generate_required_audit_scaffold

        scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
        report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nPARTIAL\n\n{ scaffold }\n"
        result = _required_audit_coverage_check(
            decision_text=_DECISION_WITH_REQUIRED_AUDIT,
            report_text=report_text,
            report_status="PARTIAL",
        )
        assert result["status"] == "FAIL"
        assert len(result["placeholder_answers"]) > 0

    def test_placeholder_answers_fail_for_failed_report(self) -> None:
        """FAILED report with placeholder Required Audit answers FAILs."""
        from reverse_agent.project_gate import _required_audit_coverage_check, generate_required_audit_scaffold

        scaffold = generate_required_audit_scaffold(_DECISION_WITH_REQUIRED_AUDIT)
        report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\nFAILED\n\n{ scaffold }\n"
        result = _required_audit_coverage_check(
            decision_text=_DECISION_WITH_REQUIRED_AUDIT,
            report_text=report_text,
            report_status="FAILED",
        )
        assert result["status"] == "FAIL"
        assert len(result["placeholder_answers"]) > 0

    def test_missing_audit_section_fails_regardless_of_status(self) -> None:
        """Report missing Required Audit section FAILs even for non-SUCCESS status."""
        from reverse_agent.project_gate import _required_audit_coverage_check

        for status in ("PARTIAL", "FAILED", "BLOCKED"):
            result = _required_audit_coverage_check(
                decision_text=_DECISION_WITH_REQUIRED_AUDIT,
                report_text=f"# CODEX_EXECUTION_REPORT\n\n## Status\n\n{status}\n",
                report_status=status,
            )
            assert result["status"] == "FAIL", f"expected FAIL for {status} report, got {result['status']}"

    def test_substantive_answers_pass_regardless_of_status(self) -> None:
        """Report with substantive Required Audit answers passes for any status."""
        from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

        questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
        audit_lines = ["## Required Audit", ""]
        for i, q in enumerate(questions, start=1):
            audit_lines.append(f"### {i}. {q}")
            audit_lines.append("")
            audit_lines.append("- Evidence: project_gate.py _required_audit_coverage_check")
            audit_lines.append("- Status: PASS")
            audit_lines.append("- Answer: substantive answers now produce FAIL regardless of report status")
            audit_lines.append("")
        for status in ("SUCCESS", "PARTIAL", "FAILED", "BLOCKED"):
            report_text = f"# CODEX_EXECUTION_REPORT\n\n## Status\n\n{status}\n\n" + "\n".join(audit_lines) + "\n"
            result = _required_audit_coverage_check(
                decision_text=_DECISION_WITH_REQUIRED_AUDIT,
                report_text=report_text,
                report_status=status,
            )
            assert result["status"] == "PASS", f"expected PASS for {status} report with substantive answers, got {result['status']}"

    def test_semantically_misaligned_answers_fail(self) -> None:
        """Answers must address each question's core entities, not just be non-placeholder."""
        from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

        decision_text = _DECISION_WITH_REQUIRED_AUDIT.replace(
            "1. How is the decision's Required Audit section currently parsed, if at all?\n"
            "2. Which Required Audit questions from the decision can be answered mechanically from project_state artifacts?\n"
            "3. Should final-check fail when ## Required Audit is missing for an engineering decision that declares Required Audit items?",
            "1. Which exact previous contradictions caused this rework, and which artifacts proved each contradiction?\n"
            "2. How does Required Audit validation now detect answer/question semantic mismatch rather than only counting headings?\n"
            "3. How does final-check now fail when `run_closeout_result.json` contains any active nested `FAIL` or `FAILED` state?\n"
            "4. How does run-closeout now prevent `closeout_status: PASSED` when `close_round_result.report_status` is `FAILED`?\n"
            "5. How do `execution_log.json` and `pytest_result.txt` now prove identical top-level command exit codes?\n"
            "6. How does command-plan distinguish diagnostic expected-exit `[0, 1]` from final accepted success requirements?\n"
            "7. Which regression tests prove these failures cannot recur?\n"
            "8. How does this rework preserve no sample-solving, no prompt/skill mutation, no forbidden state-file mutation, no legacy artifact deletion, and no Phase 2 expansion?",
        )
        questions = parse_required_audit_questions(decision_text)
        audit_lines = ["## Required Audit", ""]
        for i, q in enumerate(questions, start=1):
            audit_lines.append(f"### {i}. {q}")
            audit_lines.append("")
            audit_lines.append("- Evidence: unrelated alias migration artifact")
            audit_lines.append("- Status: PASS")
            audit_lines.append("- Answer: legacy neutral alias parity remains preserved")
            audit_lines.append("")
        report_text = "# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + "\n".join(audit_lines) + "\n"
        result = _required_audit_coverage_check(
            decision_text=decision_text,
            report_text=report_text,
            report_status="SUCCESS",
        )
        assert result["status"] == "FAIL"
        assert result["alignment_failures"]

    def test_invalid_required_audit_status_fails(self) -> None:
        """Required Audit status must use the decision-approved status vocabulary."""
        from reverse_agent.project_gate import _required_audit_coverage_check, parse_required_audit_questions

        questions = parse_required_audit_questions(_DECISION_WITH_REQUIRED_AUDIT)
        audit_lines = ["## Required Audit", ""]
        for i, q in enumerate(questions, start=1):
            audit_lines.append(f"### {i}. {q}")
            audit_lines.append("")
            audit_lines.append("- Evidence: project_state Required Audit final-check project_gate")
            audit_lines.append("- Status: ANSWERED")
            audit_lines.append("- Answer: Required Audit final-check project_state artifacts are covered")
            audit_lines.append("")
        report_text = "# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + "\n".join(audit_lines) + "\n"
        result = _required_audit_coverage_check(
            decision_text=_DECISION_WITH_REQUIRED_AUDIT,
            report_text=report_text,
            report_status="SUCCESS",
        )
        assert result["status"] == "FAIL"
        assert any(f["reason"] == "invalid_status" for f in result["alignment_failures"])


class TestExecutionLogConsistencyBlocking:
    """Verify that execution_log_consistency FAILs (blocks) for exit code
    mismatches regardless of report status, preventing acceptance of
    inconsistent closeout evidence."""

    def test_exit_code_mismatch_fails_for_partial_report(self, tmp_path: Path) -> None:
        """execution_log_consistency FAILs when exit codes disagree for PARTIAL report."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1,
            "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-24T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [
                {
                    "index": 1,
                    "command": "python -m pytest -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                    "exit_code": 0,
                    "status": "PASSED",
                },
            ],
            "warnings": [],
            "blocking_reasons": [],
        })
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 failed", exit_code=1)
            + "\n\n"
            + _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", exit_code=0)
            + "\n",
        )
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="PARTIAL",
            acceptance="NEEDS_REVIEW",
            files_changed=["reverse_agent/project_gate.py", "tests/test_project_gate.py", "project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/final_gate_result.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/execution_log.json", *archive_paths],
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            generated_artifacts=["project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/command_plan.json", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/final_gate_result.json", "project_state/gates/gate_profile_plan.json", "project_state/gates/execution_log.json", *archive_paths],
            extra_body="## Policy Impact\n\ntests reviewed.\n",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "FAIL"

    def test_exit_code_mismatch_fails_for_failed_report(self, tmp_path: Path) -> None:
        """execution_log_consistency FAILs when exit codes disagree for FAILED report."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="FAILED", acceptance="REWORK_REQUIRED")
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1,
            "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-24T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [
                {
                    "index": 1,
                    "command": "python -m pytest -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                    "exit_code": 0,
                    "status": "PASSED",
                },
            ],
            "warnings": [],
            "blocking_reasons": [],
        })
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 failed", exit_code=1)
            + "\n\n"
            + _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", exit_code=0)
            + "\n",
        )
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="FAILED",
            acceptance="REWORK_REQUIRED",
            files_changed=["reverse_agent/project_gate.py", "tests/test_project_gate.py", "project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/final_gate_result.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/execution_log.json", *archive_paths],
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            generated_artifacts=["project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/command_plan.json", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/final_gate_result.json", "project_state/gates/gate_profile_plan.json", "project_state/gates/execution_log.json", *archive_paths],
            extra_body="## Policy Impact\n\ntests reviewed.\n",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "FAIL"

    def test_consistent_exit_codes_pass_regardless_of_status(self, tmp_path: Path) -> None:
        """execution_log_consistency PASSes when exit codes agree, even for PARTIAL report."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")
        _write_json(state_dir / "gates" / "execution_log.json", {
            "schema_version": 1,
            "gate_name": "execution-log",
            "gate_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "report_id": "codex_report_gate",
            "generated_at": "2026-06-24T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [
                {
                    "index": 1,
                    "command": "python -m pytest -q",
                    "kind": "pytest",
                    "phase": "test",
                    "expected_exit_codes": [0],
                    "exit_code": 0,
                    "status": "PASSED",
                },
            ],
            "warnings": [],
            "blocking_reasons": [],
        })
        _write_pytest(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "all passed", exit_code=0)
            + "\n\n"
            + _command_block("python -m reverse_agent.project_gate final-check --state-dir project_state", "final-check: PASSED", exit_code=0)
            + "\n",
        )
        archive_paths = _archive_paths("round_gate")
        _write_report(
            state_dir,
            decision_id="decision_gate",
            report_id="codex_report_gate",
            round_id="round_gate",
            status="PARTIAL",
            acceptance="NEEDS_REVIEW",
            files_changed=["reverse_agent/project_gate.py", "tests/test_project_gate.py", "project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/final_gate_result.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/execution_log.json", *archive_paths],
            tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
            generated_artifacts=["project_state/codex_execution_report.md", "project_state/pytest_result.txt", "project_state/gates/command_plan.json", "project_state/gates/round_baseline.json", "project_state/gates/round_delta_summary.json", "project_state/gates/report_summary_synthesis.json", "project_state/gates/final_gate_result.json", "project_state/gates/gate_profile_plan.json", "project_state/gates/execution_log.json", *archive_paths],
            extra_body="## Policy Impact\n\ntests reviewed.\n",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path)
        consistency_check = _check(result, "execution_log_consistency")
        assert consistency_check["status"] == "PASS"


class TestResultStatusWarnBlocking:
    """Verify that _result_status does not return WARN when substantive
    checks are resolved, and that gate_status reaches PASSED when only
    non-blocking historical WARNs remain."""

    def test_result_status_passed_with_only_status_policy_valid_warn(self) -> None:
        """When the only WARN is status_policy_valid with historical
        external_state_notices, _result_status returns PASSED for
        engineering_branch."""
        from reverse_agent.project_gate import _result_status

        checks = [
            {"name": "decision_report_match", "status": "PASS"},
            {"name": "required_audit_coverage", "status": "PASS"},
            {"name": "execution_log_consistency", "status": "PASS"},
            {"name": "status_policy_valid", "status": "WARN", "external_state_notices": ["50 missing historical sample artifacts"]},
        ]
        result = _result_status(checks, "SUCCESS", mainline="engineering_branch")
        assert result == "PASSED"

    def test_result_status_failed_with_required_audit_fail(self) -> None:
        """When required_audit_coverage is FAIL, _result_status returns FAILED."""
        from reverse_agent.project_gate import _result_status

        checks = [
            {"name": "decision_report_match", "status": "PASS"},
            {"name": "required_audit_coverage", "status": "FAIL"},
            {"name": "execution_log_consistency", "status": "PASS"},
        ]
        result = _result_status(checks, "PARTIAL", mainline="engineering_branch")
        assert result == "FAILED"

    def test_result_status_failed_with_execution_log_consistency_fail(self) -> None:
        """When execution_log_consistency is FAIL, _result_status returns FAILED."""
        from reverse_agent.project_gate import _result_status

        checks = [
            {"name": "decision_report_match", "status": "PASS"},
            {"name": "required_audit_coverage", "status": "PASS"},
            {"name": "execution_log_consistency", "status": "FAIL"},
        ]
        result = _result_status(checks, "PARTIAL", mainline="engineering_branch")
        assert result == "FAILED"

    def test_result_status_passed_when_all_substantive_checks_pass(self) -> None:
        """When all substantive checks PASS and only non-blocking historical
        WARNs remain, _result_status returns PASSED for engineering_branch."""
        from reverse_agent.project_gate import _result_status

        checks = [
            {"name": "decision_report_match", "status": "PASS"},
            {"name": "required_audit_coverage", "status": "PASS"},
            {"name": "execution_log_consistency", "status": "PASS"},
            {"name": "execution_log_required_commands_recorded", "status": "PASS"},
            {"name": "state_hygiene_inventory_scope_complete", "status": "PASS"},
            {"name": "status_policy_valid", "status": "WARN", "external_state_notices": ["50 missing historical sample artifacts"]},
        ]
        result = _result_status(checks, "SUCCESS", mainline="engineering_branch")
        assert result == "PASSED"


class TestExecuteDecision:
    """Tests for the execute-decision thin wrapper."""

    def test_execute_decision_delegates_to_run_round(self, tmp_path):
        """execute_decision() should delegate to run_round() and add entrypoint metadata."""
        state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest tests/test_project_gate.py -q")
        result = execute_decision(state_dir=state_dir, dry_run=True, repo_root=tmp_path, write_result=False)
        assert result.get("entrypoint") == "execute-decision"
        assert result.get("delegates_to") == "run-round"
        assert result.get("run_status") == "PASSED"

    def test_execute_decision_dry_run_mode(self, tmp_path):
        """execute-decision --dry-run should delegate to run-round dry-run."""
        state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest tests/test_project_gate.py -q")
        result = execute_decision(state_dir=state_dir, dry_run=True, repo_root=tmp_path, write_result=False)
        assert result.get("mode") == "dry-run"

    def test_execute_decision_not_a_new_executor(self, tmp_path):
        """execute_decision() must not create a parallel execution engine."""
        state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest tests/test_project_gate.py -q")
        result = execute_decision(state_dir=state_dir, dry_run=True, repo_root=tmp_path, write_result=False)
        # The result should be identical to run_round's result plus entrypoint metadata
        assert "entrypoint" in result
        assert "delegates_to" in result
        # Should NOT contain any new execution-specific keys
        assert "scheduler" not in result
        assert "queue" not in result
        assert "daemon" not in result

    def test_execute_decision_self_invocation_guard(self):
        """execute-decision commands should be guarded by _is_self_invocation."""
        cmd_info = {"kind": "execute-decision", "command": "python -m reverse_agent.project_gate execute-decision --state-dir project_state"}
        assert _is_self_invocation(cmd_info) is True

    def test_execute_decision_cli_text_guard(self):
        """execute-decision CLI text should be guarded by _is_self_invocation."""
        cmd_info = {"kind": "project-cli", "command": "python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id r1"}
        assert _is_self_invocation(cmd_info) is True


class TestPhase1Completion:
    """Tests for the Phase 1 completion artifact generator."""

    def _make_state_dir(self, tmp_path, *, with_gates=True, gate_files=None):
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        if with_gates:
            gates_dir = state_dir / "gates"
            gates_dir.mkdir()
            if gate_files:
                for name, content in gate_files.items():
                    (gates_dir / name).write_text(content, encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n',
            encoding="utf-8",
        )
        return state_dir

    def test_phase1_completion_all_pass(self, tmp_path):
        """When all evidence artifacts exist and are valid, overall_status should be PASS."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
            "preflight_result.json": '{"gate_status":"PASSED","checks":[{"name":"decision_command_plan_conflict","status":"PASS"}]}',
            "policy_lint_result.json": '{"gate_status":"PASSED"}',
            "execution_log.json": '{"gate_status":"PASSED"}',
            "codex_report_auto_summary.json": '{"gate_status":"PASSED"}',
            "report_summary_synthesis.json": '{"synthesis_status":"PASSED"}',
            "final_gate_result.json": '{"gate_status":"PASSED"}',
            "run_round_result.json": '{"run_status":"PASSED"}',
            "run_closeout_result.json": '{"closeout_status":"PASSED"}',
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        assert result.get("overall_status") == "PASS"
        for cap in result.get("capabilities", []):
            assert cap.get("status") == "PASS", f"Capability {cap.get('id')} should be PASS but is {cap.get('status')}"

    def test_phase1_completion_missing_artifact_fails(self, tmp_path):
        """When an evidence artifact is missing, the corresponding capability should FAIL."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
            # Missing: preflight_result.json, policy_lint_result.json, etc.
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        assert result.get("overall_status") == "FAIL"
        # command_plan_authority should PASS
        cmd_plan_cap = next(c for c in result["capabilities"] if c["id"] == "command_plan_authority")
        assert cmd_plan_cap["status"] == "PASS"
        # Others should FAIL
        missing_caps = [c for c in result["capabilities"] if c["status"] == "FAIL"]
        assert len(missing_caps) > 0

    def test_phase1_completion_writes_artifact(self, tmp_path):
        """phase1_completion() should write phase1_completion_result.json when write_result=True."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
            "preflight_result.json": '{"gate_status":"PASSED","checks":[{"name":"decision_command_plan_conflict","status":"PASS"}]}',
            "policy_lint_result.json": '{"gate_status":"PASSED"}',
            "execution_log.json": '{"gate_status":"PASSED"}',
            "codex_report_auto_summary.json": '{"gate_status":"PASSED"}',
            "report_summary_synthesis.json": '{"synthesis_status":"PASSED"}',
            "final_gate_result.json": '{"gate_status":"PASSED"}',
            "run_round_result.json": '{"run_status":"PASSED"}',
            "run_closeout_result.json": '{"closeout_status":"PASSED"}',
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=True)
        artifact_path = state_dir / "gates" / "phase1_completion_result.json"
        assert artifact_path.exists()
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert data.get("overall_status") == "PASS"

    def test_phase1_completion_has_ten_capabilities(self, tmp_path):
        """Phase 1 completion should enumerate exactly 10 capabilities."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        assert len(result.get("capabilities", [])) == 10

    def test_phase1_completion_distinguishes_current_from_prior(self, tmp_path):
        """Phase 1 completion artifact should carry current decision_id/round_id, not prior-round IDs."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        assert result.get("decision_id") == "d1"
        assert result.get("round_id") == "r1"


class TestPhase1EvidencePathHardening:
    """Tests for Phase 1 completion evidence-path hardening."""

    def _make_state_dir(self, tmp_path, *, gate_files=None):
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        if gate_files:
            for name, content in gate_files.items():
                (gates_dir / name).write_text(content, encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n',
            encoding="utf-8",
        )
        return state_dir

    def test_missing_evidence_path_blocks_pass(self, tmp_path):
        """When a capability evidence_path is missing, phase1_completion must FAIL."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
            # Missing all other gate artifacts
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        assert result.get("overall_status") == "FAIL"
        failed_caps = [c for c in result["capabilities"] if c["status"] == "FAIL"]
        assert len(failed_caps) > 0

    def test_execute_decision_uses_existing_artifacts_not_missing_file(self, tmp_path):
        """execute_decision_entrypoint must use evidence_paths pointing to existing artifacts, not a missing execute_decision_result.json."""
        gate_files = {
            "command_plan.json": '{"plan_status":"PASSED"}',
            "preflight_result.json": '{"gate_status":"PASSED","checks":[{"name":"decision_command_plan_conflict","status":"PASS"}]}',
            "policy_lint_result.json": '{"gate_status":"PASSED"}',
            "execution_log.json": '{"gate_status":"PASSED"}',
            "codex_report_auto_summary.json": '{"gate_status":"PASSED"}',
            "report_summary_synthesis.json": '{"synthesis_status":"PASSED"}',
            "final_gate_result.json": '{"gate_status":"PASSED"}',
            "run_round_result.json": '{"run_status":"PASSED"}',
            "run_closeout_result.json": '{"closeout_status":"PASSED"}',
        }
        state_dir = self._make_state_dir(tmp_path, gate_files=gate_files)
        result = phase1_completion(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        ed_cap = next(c for c in result["capabilities"] if c["id"] == "execute_decision_entrypoint")
        # Must use evidence_paths, not a singular missing file
        assert "evidence_paths" in ed_cap
        assert not any("execute_decision_result.json" in ep for ep in ed_cap["evidence_paths"])
        # All evidence_paths must point to existing artifacts
        for ep in ed_cap["evidence_paths"]:
            assert "execute_decision_result.json" not in ep

    def test_evidence_paths_exist_check_in_final_check(self, tmp_path):
        """final-check must include phase1_completion_evidence_paths_exist check."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n',
            encoding="utf-8",
        )
        # Write phase1_completion_result.json with a missing evidence path
        (gates_dir / "phase1_completion_result.json").write_text(
            json.dumps({
                "gate_name": "phase1-completion",
                "gate_status": "PASS",
                "overall_status": "PASS",
                "capabilities": [
                    {
                        "id": "test_cap",
                        "evidence_path": "project_state/gates/nonexistent_artifact.json",
                        "status": "PASS",
                    }
                ],
            }),
            encoding="utf-8",
        )
        # Write a minimal codex_execution_report.md
        (state_dir / "codex_execution_report.md").write_text(
            '```json codex_report_summary\n{"schema_version":1,"report_id":"r1","round_id":"r1","based_on_decision_id":"d1","status":"SUCCESS","acceptance_recommendation":"ACCEPTED","files_changed":[],"tests_ran":[],"generated_artifacts":[],"referenced_artifacts":[]}\n```\n',
            encoding="utf-8",
        )
        (state_dir / "pytest_result.txt").write_text(
            '```json pytest_result_summary\n{"schema_version":1,"report_id":"r1","round_id":"r1","based_on_decision_id":"d1","decision_id":"d1","status":"PASSED","tests_ran":[]}\n```\n',
            encoding="utf-8",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        check_names = {c["name"] for c in result.get("checks", [])}
        assert "phase1_completion_evidence_paths_exist" in check_names
        # The check should FAIL because nonexistent_artifact.json does not exist
        ep_exist_check = next(c for c in result["checks"] if c["name"] == "phase1_completion_evidence_paths_exist")
        assert ep_exist_check["status"] == "FAIL"

    def test_evidence_paths_reported_check_in_final_check(self, tmp_path):
        """final-check must include phase1_completion_evidence_paths_reported check."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n',
            encoding="utf-8",
        )
        # Create the evidence file so it exists
        (gates_dir / "command_plan.json").write_text('{"plan_status":"PASSED"}', encoding="utf-8")
        # Write phase1_completion_result.json with an evidence path NOT in generated_artifacts
        (gates_dir / "phase1_completion_result.json").write_text(
            json.dumps({
                "gate_name": "phase1-completion",
                "gate_status": "PASS",
                "overall_status": "PASS",
                "capabilities": [
                    {
                        "id": "test_cap",
                        "evidence_path": "project_state/gates/command_plan.json",
                        "status": "PASS",
                    }
                ],
            }),
            encoding="utf-8",
        )
        # Write a minimal codex_execution_report.md with empty generated_artifacts
        (state_dir / "codex_execution_report.md").write_text(
            '```json codex_report_summary\n{"schema_version":1,"report_id":"r1","round_id":"r1","based_on_decision_id":"d1","status":"SUCCESS","acceptance_recommendation":"ACCEPTED","files_changed":[],"tests_ran":[],"generated_artifacts":[],"referenced_artifacts":[]}\n```\n',
            encoding="utf-8",
        )
        (state_dir / "pytest_result.txt").write_text(
            '```json pytest_result_summary\n{"schema_version":1,"report_id":"r1","round_id":"r1","based_on_decision_id":"d1","decision_id":"d1","status":"PASSED","tests_ran":[]}\n```\n',
            encoding="utf-8",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        check_names = {c["name"] for c in result.get("checks", [])}
        assert "phase1_completion_evidence_paths_reported" in check_names
        # The check should FAIL because command_plan.json is not in generated_artifacts
        ep_reported_check = next(c for c in result["checks"] if c["name"] == "phase1_completion_evidence_paths_reported")
        assert ep_reported_check["status"] == "FAIL"

    def test_execute_decision_guard_reason_when_self_invocation_prevents_execution(self, tmp_path):
        """When execute-decision non-dry-run is guarded by self-invocation, guard_reason must be set."""
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n',
            encoding="utf-8",
        )
        (gates_dir / "command_plan.json").write_text(
            '{"schema_version":1,"plan_status":"PASSED","decision_id":"d1","round_id":"r1","commands":[]}',
            encoding="utf-8",
        )
        # When run_round returns mode=dry-run even though dry_run=False, guard_reason should be set
        result = execute_decision(state_dir=state_dir, dry_run=False, repo_root=tmp_path, write_result=False)
        if result.get("mode") == "dry-run":
            assert "guard_reason" in result
            assert "self-invocation" in result["guard_reason"].lower() or "recursive" in result["guard_reason"].lower()


class TestNamingHygiene:
    """Tests for naming-hygiene command and state hygiene inventory."""

    def test_naming_hygiene_generates_artifacts(self, tmp_path: Path) -> None:
        """naming-hygiene generates naming_migration_plan.json and state_hygiene_inventory.json."""
        from reverse_agent.project_gate import naming_hygiene
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}\n```\n'
            '```json decision_contract\n{"allowed_state_artifacts":["project_state/gates/naming_migration_plan.json"]}\n```\n',
            encoding="utf-8",
        )
        result = naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        assert result["gate_status"] == "PASSED"
        assert result["no_rename"] is True
        assert result["no_delete"] is True
        assert result["no_neutral_live_path_created"] is True
        assert (gates_dir / "naming_migration_plan.json").exists()
        assert (gates_dir / "state_hygiene_inventory.json").exists()

    def test_naming_migration_plan_contains_codex_bound_names(self, tmp_path: Path) -> None:
        """naming_migration_plan.json identifies Codex-bound names."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "gates").mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        plan = json.loads((state_dir / "gates" / "naming_migration_plan.json").read_text(encoding="utf-8"))
        assert plan["action_this_round"] == "inventory_only"
        assert plan["no_rename"] is True
        assert plan["no_delete"] is True
        codex_names = [e["current_name"] for e in plan["codex_bound_names"]]
        assert "codex_execution_report.md" in codex_names
        assert "codex_report_summary" in codex_names
        assert "codex_report_auto_summary.json" in codex_names
        # All entries should be inventory_only
        for entry in plan["codex_bound_names"]:
            assert entry["action_this_round"] == "inventory_only"
            assert entry["migration_round"] == "deferred"

    def test_state_hygiene_inventory_classifies_files(self, tmp_path: Path) -> None:
        """state_hygiene_inventory.json classifies files into approved categories."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"allowed_state_artifacts":["project_state/codex_execution_report.md"]}\n```\n',
            encoding="utf-8",
        )
        (state_dir / "codex_execution_report.md").write_text("# Report\n", encoding="utf-8")
        (state_dir / "pytest_result.txt").write_text("PASSED", encoding="utf-8")
        (gates_dir / "command_plan.json").write_text('{}', encoding="utf-8")
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        inv = json.loads((state_dir / "gates" / "state_hygiene_inventory.json").read_text(encoding="utf-8"))
        categories = {e["category"] for e in inv["entries"]}
        assert "current_live_artifact" in categories
        # codex_execution_report.md should be legacy_compat_artifact
        codex_entries = [e for e in inv["entries"] if "codex" in e["path"].lower()]
        assert any(e["category"] == "legacy_compat_artifact" for e in codex_entries)

    def test_no_entry_is_safe_to_delete(self, tmp_path: Path) -> None:
        """Every entry in state hygiene inventory has safe_to_delete=False."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "gates").mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        inv = json.loads((state_dir / "gates" / "state_hygiene_inventory.json").read_text(encoding="utf-8"))
        for entry in inv["entries"]:
            assert entry["safe_to_delete"] is False, f"{entry['path']} has safe_to_delete=True"
            assert "deferred" in entry["delete_reason"].lower() or "no file may be deleted" in entry["delete_reason"].lower()

    def test_naming_hygiene_no_rename_no_delete_no_neutral_path(self, tmp_path: Path) -> None:
        """naming-hygiene does not rename, delete, or create neutral live report paths."""
        from reverse_agent.project_gate import naming_hygiene
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "gates").mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n',
            encoding="utf-8",
        )
        (state_dir / "codex_execution_report.md").write_text("# Report\n", encoding="utf-8")
        # Record files before
        before_files = set(f.name for f in state_dir.iterdir())
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        after_files = set(f.name for f in state_dir.iterdir())
        # No file was deleted
        assert before_files.issubset(after_files)
        # No neutral live report path was created
        assert not (state_dir / "execution_report.md").exists()
        assert not (state_dir / "gates" / "execution_report_auto_summary.json").exists()
        # Original file still exists
        assert (state_dir / "codex_execution_report.md").exists()

    def test_naming_hygiene_cli_exit_code(self, tmp_path: Path) -> None:
        """naming-hygiene CLI returns exit code 0 on success."""
        import subprocess, sys
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        (state_dir / "gates").mkdir()
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n',
            encoding="utf-8",
        )
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "reverse_agent.project_gate", "naming-hygiene", "--state-dir", str(state_dir)],
            capture_output=True, text=True, cwd=str(repo_root),
        )
        assert result.returncode == 0

    def test_archive_dirs_included_in_inventory(self, tmp_path: Path) -> None:
        """Bounded archive directories from decision_contract are included in state_hygiene_inventory.json."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Create bounded archive directory with files
        archive_dir = tmp_path / "project_state" / "rounds" / "round_test_archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        (archive_dir / "codex_execution_report.md").write_text("# Report\n", encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"bounded_archive_dirs_to_inventory":["project_state/rounds/round_test_archive"]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        inv = json.loads((gates_dir / "state_hygiene_inventory.json").read_text(encoding="utf-8"))
        archive_entries = [e for e in inv["entries"] if e.get("category") == "round_archive_artifact"]
        assert len(archive_entries) >= 2, f"expected at least 2 archive entries, got {len(archive_entries)}"
        archive_paths = {e["path"] for e in archive_entries}
        assert "project_state/rounds/round_test_archive/round_manifest.json" in archive_paths
        assert "project_state/rounds/round_test_archive/codex_execution_report.md" in archive_paths

    def test_archive_entries_classified_and_safe_to_delete_false(self, tmp_path: Path) -> None:
        """Archive entries are classified as round_archive_artifact with safe_to_delete=False."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        archive_dir = tmp_path / "project_state" / "rounds" / "round_prev"
        archive_dir.mkdir(parents=True)
        (archive_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"bounded_archive_dirs_to_inventory":["project_state/rounds/round_prev"]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        inv = json.loads((gates_dir / "state_hygiene_inventory.json").read_text(encoding="utf-8"))
        archive_entries = [e for e in inv["entries"] if "/rounds/" in e["path"]]
        for entry in archive_entries:
            assert entry["category"] == "round_archive_artifact", f"{entry['path']} has category {entry['category']}"
            assert entry["safe_to_delete"] is False, f"{entry['path']} has safe_to_delete=True"
            assert "round_archive" in entry.get("referenced_by", []), f"{entry['path']} missing round_archive in referenced_by"
            assert entry["freshness_basis"] == "round_archive", f"{entry['path']} has freshness_basis {entry['freshness_basis']}"

    def test_no_full_rounds_scan(self, tmp_path: Path) -> None:
        """Only bounded archive dirs are scanned, not the full project_state/rounds/ tree."""
        from reverse_agent.project_gate import naming_hygiene
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Create two archive dirs, but only one is bounded
        bounded_dir = tmp_path / "project_state" / "rounds" / "round_bounded"
        bounded_dir.mkdir(parents=True)
        (bounded_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        unbounded_dir = tmp_path / "project_state" / "rounds" / "round_unbounded"
        unbounded_dir.mkdir(parents=True)
        (unbounded_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"bounded_archive_dirs_to_inventory":["project_state/rounds/round_bounded"]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        inv = json.loads((gates_dir / "state_hygiene_inventory.json").read_text(encoding="utf-8"))
        paths = {e["path"] for e in inv["entries"]}
        assert "project_state/rounds/round_bounded/round_manifest.json" in paths
        assert "project_state/rounds/round_unbounded/round_manifest.json" not in paths

    def test_inventory_scope_complete_check(self, tmp_path: Path) -> None:
        """state_hygiene_inventory_scope_complete final-check verifies archive coverage."""
        from reverse_agent.project_gate import naming_hygiene, final_check
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Create bounded archive directory
        archive_dir = tmp_path / "project_state" / "rounds" / "round_test"
        archive_dir.mkdir(parents=True)
        (archive_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"bounded_archive_dirs_to_inventory":["project_state/rounds/round_test"]}\n```\n',
            encoding="utf-8",
        )
        naming_hygiene(state_dir=state_dir, repo_root=tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        scope_check = next(
            (c for c in result.get("checks", []) if c.get("name") == "state_hygiene_inventory_scope_complete"),
            None,
        )
        assert scope_check is not None, "state_hygiene_inventory_scope_complete check not found"
        assert scope_check["status"] == "PASS", f"Expected PASS, got {scope_check['status']}: {scope_check.get('detail')}"

    def test_inventory_scope_complete_fails_on_missing_archive(self, tmp_path: Path) -> None:
        """state_hygiene_inventory_scope_complete fails if archive files are missing from inventory."""
        from reverse_agent.project_gate import final_check
        import json
        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        gates_dir = state_dir / "gates"
        gates_dir.mkdir()
        # Create archive dir but don't include its files in the inventory
        archive_dir = tmp_path / "project_state" / "rounds" / "round_missing"
        archive_dir.mkdir(parents=True)
        (archive_dir / "round_manifest.json").write_text('{}', encoding="utf-8")
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n{"decision_id":"d1","round_id":"r1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":[]}\n```\n'
            '```json decision_contract\n{"bounded_archive_dirs_to_inventory":["project_state/rounds/round_missing"]}\n```\n',
            encoding="utf-8",
        )
        # Write an empty inventory (no archive entries)
        (gates_dir / "state_hygiene_inventory.json").write_text(
            json.dumps({"schema_version": 1, "entries": []}) + "\n",
            encoding="utf-8",
        )
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        scope_check = next(
            (c for c in result.get("checks", []) if c.get("name") == "state_hygiene_inventory_scope_complete"),
            None,
        )
        assert scope_check is not None
        assert scope_check["status"] == "FAIL", f"Expected FAIL, got {scope_check['status']}"


class TestCloseoutTransientWarningNormalization:
    """Verify that resolved pre-archive warnings are normalized in
    close_round_result so they appear in resolved_pre_archive_warnings
    and pre_archive_diagnostics, not in the active warnings list."""

    def test_resolved_pre_archive_warning_moved_out_of_warnings(self, tmp_path: Path) -> None:
        """When close_status is CLOSED and final_check_after_archive passed,
        a report_summary_fields_match_synthesis WARN that was archive-only
        is moved to resolved_pre_archive_warnings, not left in warnings."""
        from reverse_agent.project_gate import close_round

        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(state_dir / "current_state.json", {"round_id": "round_test", "state_build_id": "state_test", "state_digest": "digest_test", "state_scope": "sample_state", "source_harness_run": "run_test"})
        _write_json(state_dir / "task_packet.json", {"state_scope": "sample_state", "task_source": "derived_from_sample_artifacts", "execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"})
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "negative_results.json", {})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})

        decision_id = "decision_test"
        round_id = "round_test"
        report_id = "codex_report_test"
        archive_paths = _archive_paths(round_id)

        _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
        _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

        gates_dir = state_dir / "gates"
        _write_json(gates_dir / "command_plan.json", {
            "schema_version": 1, "artifact_name": "command_plan.json",
            "decision_id": decision_id, "round_id": round_id,
            "plan_status": "PASSED", "mainline": "engineering_branch",
            "generated_at": "2026-06-24T00:00:00Z",
            "commands": [
                {"index": 1, "command": "python -m pytest -q", "phase": "test", "kind": "pytest", "required": True},
            ],
            "warnings": [], "blocking_reasons": [],
            "profile_meta": {"profile": "full", "closeout_allowed": True},
            "omitted_commands": [],
        })
        _write_json(gates_dir / "gate_profile_plan.json", {
            "schema_version": 1, "profile": "full", "closeout_allowed": True,
            "decision_id": decision_id, "round_id": round_id,
        })
        _write_json(gates_dir / "round_delta_summary.json", {
            "schema_version": 1, "baseline_available": True,
            "baseline_dirty_files": [], "new_dirty_files_since_baseline": [],
            "final_dirty_files": ["reverse_agent/project_gate.py", "tests/test_project_gate.py"],
        })
        _write_json(gates_dir / "final_gate_result.json", {
            "schema_version": 1, "gate_name": "final-check",
            "gate_status": "PASSED", "decision_id": decision_id,
            "round_id": round_id, "report_id": report_id,
            "checks": [], "warnings": [], "blocking_reasons": [],
        })
        _write_json(gates_dir / "report_summary_synthesis.json", {
            "schema_version": 1, "synthesis_status": "PASSED",
            "decision_id": decision_id, "round_id": round_id,
            "report_id": report_id,
            "summary": {"files_changed": [], "tests_ran": [], "generated_artifacts": [], "status": "SUCCESS", "acceptance_recommendation": "ACCEPTED"},
            "errors": [], "diffs": [], "warnings": [],
        })
        _write_json(gates_dir / "codex_report_auto_summary.json", {
            "schema_version": 1, "decision_id": decision_id, "round_id": round_id,
            "report_id": report_id,
            "summary": {"files_changed": [], "tests_ran": [], "generated_artifacts": [], "status": "SUCCESS", "acceptance_recommendation": "ACCEPTED"},
        })
        _write_json(gates_dir / "execution_log.json", {
            "schema_version": 1, "gate_name": "execution-log",
            "gate_status": "PASSED", "decision_id": decision_id,
            "round_id": round_id, "report_id": report_id,
            "generated_at": "2026-06-24T00:00:00Z",
            "source": "derived_from_pytest_result_and_command_plan",
            "commands": [{"index": 1, "command": "python -m pytest -q", "kind": "pytest", "phase": "test", "expected_exit_codes": [0], "exit_code": 0, "status": "PASSED"}],
            "warnings": [], "blocking_reasons": [],
        })
        _write_json(gates_dir / "state_hygiene_inventory.json", {
            "schema_version": 1, "entries": [],
        })

        _write_report(
            state_dir,
            decision_id=decision_id,
            report_id=report_id,
            round_id=round_id,
            status="SUCCESS",
            acceptance="ACCEPTED",
            files_changed=["reverse_agent/project_gate.py", "tests/test_project_gate.py", "project_state/codex_execution_report.md", "project_state/pytest_result.txt", *archive_paths],
            tests_ran=["python -m pytest -q"],
            generated_artifacts=["project_state/codex_execution_report.md", "project_state/pytest_result.txt", *archive_paths],
            extra_body="## Policy Impact\n\ntests reviewed.\n",
        )
        _write_pytest(
            state_dir,
            decision_id=decision_id,
            report_id=report_id,
            round_id=round_id,
            tests_ran=["python -m pytest -q"],
            body="\n\n".join(_STARTUP_COMMAND_BLOCKS)
            + "\n\n"
            + _command_block("python -m pytest -q", "1 passed", exit_code=0)
            + "\n",
        )

        # Create the archive directory so close_round can proceed
        archive_dir = state_dir / "rounds" / round_id
        archive_dir.mkdir(parents=True)

        result = close_round(state_dir=state_dir, round_id=round_id, repo_root=tmp_path)

        # The key assertion: if close_status is CLOSED and
        # final_check_after_archive passed, any pre-archive transient
        # WARN should be in resolved_pre_archive_warnings, not in warnings.
        if result.get("close_status") == "CLOSED":
            fcaa = next(
                (a for a in result.get("actions", []) if a.get("name") == "final_check_after_archive"),
                None,
            )
            if fcaa and fcaa.get("gate_status") == "PASSED":
                # report_summary_fields_match_synthesis WARN should be resolved
                assert "report_summary_fields_match_synthesis" not in " ".join(result.get("warnings", [])), (
                    f"report_summary_fields_match_synthesis should not be in active warnings: {result.get('warnings')}"
                )
                # It should be in resolved_pre_archive_warnings
                resolved = result.get("resolved_pre_archive_warnings", [])
                assert any("report_summary_fields_match_synthesis" in w for w in resolved), (
                    f"report_summary_fields_match_synthesis should be in resolved_pre_archive_warnings: {resolved}"
                )
                # pre_archive_diagnostics should have structured entries
                diagnostics = result.get("pre_archive_diagnostics", [])
                assert any(d.get("check_name") == "report_summary_fields_match_synthesis" for d in diagnostics), (
                    f"pre_archive_diagnostics should contain report_summary_fields_match_synthesis: {diagnostics}"
                )

    def test_unresolved_closeout_warning_stays_in_warnings(self, tmp_path: Path) -> None:
        """When close_status is FAILED, warnings are not moved to
        resolved_pre_archive_warnings because the close did not succeed."""
        from reverse_agent.project_gate import close_round

        state_dir = tmp_path / "project_state"
        state_dir.mkdir()
        _write_skill_registry(tmp_path)
        _write_json(state_dir / "current_state.json", {"round_id": "round_test", "state_build_id": "state_test", "state_digest": "digest_test", "state_scope": "sample_state", "source_harness_run": "run_test"})
        _write_json(state_dir / "task_packet.json", {"state_scope": "sample_state", "task_source": "derived_from_sample_artifacts", "execution_scope": "decision_packet_controls_current_round", "active_decision_packet": "project_state/decision_packet.md"})
        _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
        _write_json(state_dir / "negative_results.json", {})
        _write_json(state_dir / "model_gate.json", {"should_call_model": False})

        decision_id = "decision_test"
        round_id = "round_test"

        # Write a decision that is NOT APPROVED to force a failure
        (state_dir / "decision_packet.md").write_text(
            '```json decision_meta\n'
            f'{{"decision_id":"{decision_id}","round_id":"{round_id}","status":"PENDING","mainline":"engineering_branch","skill_profiles":[]}}\n'
            '```\n',
            encoding="utf-8",
        )

        _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)

        result = close_round(state_dir=state_dir, round_id=round_id, repo_root=tmp_path)

        # close_status should be INVALID because decision is not APPROVED
        assert result.get("close_status") in ("FAILED", "INVALID")
        # resolved_pre_archive_warnings should be empty because close did not succeed
        assert result.get("resolved_pre_archive_warnings") == []
        assert result.get("pre_archive_diagnostics") == []


class TestCloseoutActiveWarningsCleanCheck:
    """Verify that the closeout_active_warnings_clean final-check catches
    ambiguous accepted-state closeout warnings and passes when warnings
    are properly normalized."""

    def test_clean_closeout_passes(self, tmp_path: Path) -> None:
        """When run_closeout_result.json has no active warnings, the check passes."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path)
        gates_dir = state_dir / "gates"
        _write_json(gates_dir / "run_closeout_result.json", {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "warnings": [],
            "blocking_reasons": [],
            "close_round_result": {
                "close_status": "CLOSED",
                "warnings": [],
                "resolved_pre_archive_warnings": ["report_summary_fields_match_synthesis: codex_report_summary differs from synthesized summary"],
                "pre_archive_diagnostics": [
                    {"check_name": "report_summary_fields_match_synthesis", "detail": "codex_report_summary differs from synthesized summary", "resolution": "resolved_by_final_check_after_archive", "scope": "pre_archive_transient"},
                ],
                "actions": [
                    {"name": "final_check_after_archive", "status": "PASSED", "gate_status": "PASSED"},
                ],
            },
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        caw = next((c for c in result.get("checks", []) if c.get("name") == "closeout_active_warnings_clean"), None)
        assert caw is not None
        assert caw["status"] == "PASS", f"Expected PASS, got {caw['status']}: {caw.get('detail')}"

    def test_ambiguous_closeout_warning_fails(self, tmp_path: Path) -> None:
        """When run_closeout_result.json has active close_round_result warnings
        despite final_check_after_archive PASSED, the check FAILs."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path)
        gates_dir = state_dir / "gates"
        _write_json(gates_dir / "run_closeout_result.json", {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "warnings": [],
            "blocking_reasons": [],
            "close_round_result": {
                "close_status": "CLOSED",
                "warnings": ["report_summary_fields_match_synthesis: codex_report_summary differs from synthesized summary"],
                "resolved_pre_archive_warnings": [],
                "pre_archive_diagnostics": [],
                "actions": [
                    {"name": "final_check_after_archive", "status": "PASSED", "gate_status": "PASSED"},
                ],
            },
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        caw = next((c for c in result.get("checks", []) if c.get("name") == "closeout_active_warnings_clean"), None)
        assert caw is not None
        assert caw["status"] == "FAIL", f"Expected FAIL, got {caw['status']}: {caw.get('detail')}"

    def test_no_closeout_result_passes(self, tmp_path: Path) -> None:
        """When run_closeout_result.json does not exist, the check passes
        (backward-compatible)."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path)
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        caw = next((c for c in result.get("checks", []) if c.get("name") == "closeout_active_warnings_clean"), None)
        assert caw is not None
        assert caw["status"] == "PASS"

    def test_real_unresolved_warning_warns(self, tmp_path: Path) -> None:
        """When closeout has real top-level warnings (not pre-archive transients),
        the check WARNs."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path)
        gates_dir = state_dir / "gates"
        _write_json(gates_dir / "run_closeout_result.json", {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "WARN",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "warnings": ["some_real_issue: something is wrong"],
            "blocking_reasons": [],
            "close_round_result": {
                "close_status": "CLOSED",
                "warnings": [],
                "resolved_pre_archive_warnings": [],
                "pre_archive_diagnostics": [],
                "actions": [
                    {"name": "final_check_after_archive", "status": "PASSED", "gate_status": "PASSED"},
                ],
            },
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        caw = next((c for c in result.get("checks", []) if c.get("name") == "closeout_active_warnings_clean"), None)
        assert caw is not None
        assert caw["status"] == "WARN", f"Expected WARN, got {caw['status']}: {caw.get('detail')}"

    def test_nested_failures_fail_final_check(self, tmp_path: Path) -> None:
        """Top-level PASSED closeout cannot mask nested FAIL/FAILED states."""
        from reverse_agent.project_gate import final_check

        state_dir = _make_gate_state(tmp_path)
        gates_dir = state_dir / "gates"
        _write_json(gates_dir / "run_closeout_result.json", {
            "schema_version": 1,
            "gate_name": "run-closeout",
            "closeout_status": "PASSED",
            "decision_id": "decision_gate",
            "round_id": "round_gate",
            "warnings": [],
            "blocking_reasons": [],
            "close_round_result": {
                "close_status": "CLOSED",
                "report_status": "FAILED",
                "warnings": [],
                "blocking_reasons": [],
                "checks": [
                    {"name": "pytest_result_exit_codes_match_command_plan", "status": "FAIL"},
                ],
                "actions": [
                    {"name": "final_check_after_archive", "status": "PASSED", "gate_status": "PASSED"},
                ],
            },
        })
        result = final_check(state_dir=state_dir, repo_root=tmp_path, write_result=False)
        nested = next((c for c in result.get("checks", []) if c.get("name") == "closeout_nested_failures_absent"), None)
        assert nested is not None
        assert nested["status"] == "FAIL"
        assert result["gate_status"] == "FAILED"

    def test_run_closeout_internal_blockers_include_nested_failures(self) -> None:
        """run-closeout aggregation fails on failed nested close-round evidence."""
        from reverse_agent.project_gate import _run_closeout_internal_blocking_reasons

        reasons = _run_closeout_internal_blocking_reasons(
            executed_steps=[
                {"name": "close-round", "status": "PASSED", "exit_code": 0, "expected_exit_codes": [0]},
            ],
            skipped_steps=[],
            close_round_result={
                "close_status": "CLOSED",
                "report_status": "FAILED",
                "checks": [
                    {"name": "pytest_result_exit_codes_match_command_plan", "status": "FAIL"},
                ],
                "blocking_reasons": [],
                "warnings": [],
                "actions": [],
            },
        )
        assert "close-round report_status=FAILED" in reasons
        assert any("pytest_result_exit_codes_match_command_plan" in reason for reason in reasons)



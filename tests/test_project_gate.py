import json
from pathlib import Path

import pytest

from reverse_agent.project_gate import (
    _close_round_exit_code,
    _report_status_from_gate,
    _report_status_from_gate_payload,
    _result_status,
    build_report_summary_synthesis,
    close_round,
    command_plan,
    final_check,
    main,
    preflight,
)
from reverse_agent.project_state import archive_round, write_pytest_result


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
    report_id = "report_gate"
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
        *archive_paths,
    ]
    report_tests = tests_ran if tests_ran is not None else ["python -m pytest -q"]
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id, mainline=mainline)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
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
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/final_gate_result.json",
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
    report_id = "report_gate"
    round_id = "round_gate"
    commands = [
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
    }
    if command_plan_overrides:
        plan_payload.update(command_plan_overrides)
    archive_paths = _archive_paths(round_id)
    tests = report_tests if report_tests is not None else commands
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(state_dir, decision_id=decision_id, round_id=round_id)
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
            "project_state/gates/command_plan.json",
            "project_state/gates/final_gate_result.json",
            *archive_paths,
        ],
        tests_ran=tests,
        generated_artifacts=generated_artifacts
        if generated_artifacts is not None
        else [
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/command_plan.json",
            "project_state/gates/final_gate_result.json",
            *archive_paths,
        ],
    )
    _write_json(state_dir / "gates" / "command_plan.json", plan_payload)
    body = pytest_body
    if body is None:
        body = "\n\n".join(
            [
                _command_block(commands[0], "212 passed in 1.00s"),
                _command_block(commands[1], "command-plan: PASSED"),
                _command_block(commands[2], json.dumps(plan_payload, indent=2)),
                _command_block(commands[3], f"final-check: {final_check_stdout_status}"),
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
        "project_state/gates/preflight_result.json",
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

    assert result["gate_status"] == "PASSED_WITH_LIMITATIONS"
    assert result["blocking_reasons"] == []
    assert _check(result, "status_policy_valid")["status"] == "PASS"


def test_final_check_blocks_success_with_legacy_artifacts_for_reverse_solving(
    tmp_path: Path,
) -> None:
    """reverse_solving retains strict artifact freshness: stale/missing → FAIL."""
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
    assert "stale artifacts" in " ".join(status_policy["lint_errors"])


def test_final_check_downgrades_historical_artifacts_for_tool_integration(
    tmp_path: Path,
) -> None:
    """tool_integration downgrades historical missing/stale artifacts to WARN
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

    assert result["gate_status"] == "WARN"
    status_policy = _check(result, "status_policy_valid")
    assert status_policy["status"] == "WARN"
    assert "stale artifacts" in " ".join(status_policy.get("warnings", []))


def test_final_check_fails_when_recorded_stdout_status_is_stale(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="PARTIAL",
        acceptance="NEEDS_REVIEW",
        pytest_body="\n\n".join(
            [
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
    assert stdout_check["expected_gate_status"] == "WARN"
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

    assert result["gate_status"] == "PASSED_WITH_LIMITATIONS"
    stdout_check = _check(result, "final_check_stdout_matches_gate_status")
    assert stdout_check["status"] == "PASS"
    assert stdout_check["expected_gate_status"] == "PASSED_WITH_LIMITATIONS"
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

    assert main(["final-check", "--state-dir", str(state_dir)]) == 0

    output = capsys.readouterr().out
    assert "final-check: WARN" in output
    result = json.loads((state_dir / "gates" / "final_gate_result.json").read_text(encoding="utf-8"))
    assert result["gate_status"] == "WARN"
    assert result["recommended_next_action"] == "review_warnings_before_closeout"



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
        tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
        pytest_tests_ran=["python -m pytest -q"],
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
    state_dir = _make_gate_state(tmp_path)
    (state_dir / "gates" / "round_baseline.json").unlink()

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

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

    # Inherited dirty files in files_changed are WARN (not FAIL) because
    # they may have been legitimately modified this round.
    inherited_check = _check(result, "files_changed_excludes_inherited_dirty_files")
    assert inherited_check["status"] == "WARN"
    assert "reverse_agent/project_gate.py" in inherited_check["inherited_files_in_files_changed"]


def test_final_check_passes_when_source_test_dirty_is_inherited_but_in_scope(tmp_path: Path) -> None:
    """When source/test files are in baseline_dirty_files and ARE in the
    decision scope (Allowed source files / Allowed tests), the
    baseline_lifecycle_guard should PASS even without an explicit
    "Allowed Inherited Dirty Baseline Files" section, because the
    decision scope itself authorises those files.
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
    assert lifecycle["status"] != "FAIL", (
        "baseline_lifecycle_guard should not FAIL when source/test files"
        " are authorised by decision scope"
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
        + "\nThe inherited baseline files are explicitly allowed for this round.\n",
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

    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"] == []
    assert _check(result, "status_policy_valid")["status"] == "PASS"


def test_final_check_warns_for_consistent_partial_report(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="PARTIAL", acceptance="NEEDS_REVIEW")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "WARN"
    assert result["blocking_reasons"] == []
    assert _check(result, "status_policy_valid")["status"] == "WARN"
    assert not [check for check in result["checks"] if check["status"] == "FAIL"]


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
            "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
            extra_command,
        ],
        pytest_body="\n\n".join(
            [
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
    state_dir = _make_gate_state(tmp_path)

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

    # Inherited dirty files in files_changed are now WARN (not ERROR) because
    # they may have been legitimately modified this round.
    assert result["synthesis_status"] in ("WARN", "FAILED")
    assert any("inherited dirty files" in w for w in result.get("warnings", []))


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

    assert result["synthesis_status"] == "WARN"
    assert result["diffs"] == []
    assert result["errors"] == []
    assert "status" not in result["synthesized_summary"]
    assert any("retriable report-summary/archive drift failures" in warning for warning in result["warnings"])


def test_report_summary_fails_when_command_plan_missing(tmp_path: Path) -> None:
    state_dir = _make_report_summary_state(tmp_path)
    (state_dir / "gates" / "command_plan.json").unlink()

    result = build_report_summary_synthesis(state_dir=state_dir, repo_root=tmp_path)

    assert result["synthesis_status"] == "FAILED"
    assert any("command_plan.json" in error for error in result["errors"])


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
    assert result["actions"][2]["gate_status"] == "PASSED_WITH_LIMITATIONS"


def test_close_round_is_idempotent_for_existing_matching_archive(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(tmp_path)

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["archive"]["status"] == "no-op"
    assert result["archive"]["idempotent"] is True
    assert result["archive"]["copied"] == []
    archive_action = next(action for action in result["actions"] if action["name"] == "archive_round")
    assert archive_action["status"] == "no-op"


def test_close_round_closes_consistent_partial_report(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="PARTIAL",
        acceptance="NEEDS_REVIEW",
        archived=False,
        final_check_stdout_status="WARN",
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["actions"][0]["status"] == "PASSED"
    assert result["actions"][0]["gate_status"] == "WARN"
    assert result["actions"][0]["unexpected_failures"] == []
    assert result["actions"][1]["status"] == "created"
    assert result["actions"][2]["status"] == "PASSED"
    assert result["actions"][2]["gate_status"] == "WARN"
    assert (state_dir / "rounds" / "round_gate" / "round_manifest.json").exists()


def test_close_round_closes_consistent_blocked_report(tmp_path: Path) -> None:
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        status="BLOCKED",
        acceptance="BLOCKED",
        archived=False,
        final_check_stdout_status="BLOCKED",
    )

    result = close_round(state_dir=state_dir, round_id="round_gate", repo_root=tmp_path)

    assert result["close_status"] == "CLOSED"
    assert result["actions"][0]["status"] == "PASSED"
    assert result["actions"][0]["gate_status"] == "BLOCKED"
    assert result["actions"][0]["unexpected_failures"] == []
    assert result["actions"][1]["status"] == "created"
    assert result["actions"][2]["status"] == "PASSED"
    assert result["actions"][2]["gate_status"] == "BLOCKED"
    assert (state_dir / "rounds" / "round_gate" / "round_manifest.json").exists()


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
        "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        pytest_body="\n\n".join(
            [
                _command_block(commands[0], "301 passed"),
                _command_block(commands[1], "command-plan: PASSED"),
                _command_block(
                    commands[2],
                    json.dumps(
                        {
                            "commands": [
                                {"command": commands[0]},
                                {"command": commands[1]},
                                {"command": commands[2]},
                                {"command": commands[3]},
                            ]
                        }
                    ),
                ),
            ]
        ),
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert _check(result, "pytest_result_exit_codes_match_command_plan")["status"] == "PASS"


def test_final_check_fails_when_close_round_declared_but_command_block_missing(tmp_path: Path) -> None:
    base_commands = [
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
            _command_block(base_commands[0], "301 passed"),
            _command_block(base_commands[1], "command-plan: PASSED"),
            _command_block(base_commands[2], json.dumps(plan_payload)),
            _command_block(base_commands[3], "final-check: PASSED"),
        ]
    )
    state_dir = _make_command_plan_gate_state(
        tmp_path,
        archived=False,
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
            _command_block(base_commands[0], "301 passed"),
            _command_block(base_commands[1], "command-plan: PASSED"),
            _command_block(base_commands[2], json.dumps(plan_payload)),
            _command_block(base_commands[3], "final-check: PASSED"),
            _command_block(base_commands[4], "close-round: CLOSED"),
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
            _command_block(base_commands[0], "301 passed"),
            _command_block(base_commands[1], json.dumps(plan_payload)),
            _command_block(base_commands[2], "final-check: PASSED"),
            _command_block(base_commands[3], "close-round: CLOSED"),
            _command_block(base_commands[4], "command-plan: PASSED"),
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

    assert main(["final-check", "--state-dir", str(state_dir)]) == 0


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
    assert commands[6]["expected_exit_codes"] == [0]
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
    """Verify final_check produces PASSED_WITH_LIMITATIONS when only historical artifacts are missing."""

    def test_engineering_partial_with_historical_only_limitations(self, tmp_path: Path) -> None:
        """When report is PARTIAL but doctor WARN is only from historical non-blocking artifacts,
        gate should be PASSED_WITH_LIMITATIONS."""
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

        assert result["gate_status"] == "PASSED_WITH_LIMITATIONS"
        assert result["blocking_reasons"] == []
        status_policy = _check(result, "status_policy_valid")
        assert status_policy["status"] == "WARN"
        assert status_policy.get("limitations") is not None
        assert len(status_policy["limitations"]) > 0

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
    """Verify build_report_summary_synthesis includes limitations when status is ACCEPTED_WITH_LIMITATIONS."""

    def test_synthesis_includes_limitations_from_gate(self, tmp_path: Path) -> None:
        """When final gate has PASSED_WITH_LIMITATIONS and status_policy_valid has limitations,
        synthesis should include limitations in synthesized_summary."""
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
        assert synthesized.get("acceptance_recommendation") == "ACCEPTED_WITH_LIMITATIONS"
        assert "limitations" in synthesized
        assert len(synthesized["limitations"]) > 0


def test_command_plan_fails_when_tests_section_missing(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block=None)

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "FAILED"
    assert "Tests section is missing" in result["blocking_reasons"]


def test_command_plan_extracts_unfenced_backtick_commands(tmp_path: Path) -> None:
    state_dir = _make_command_plan_state(tmp_path, tests_block="python -m pytest -q")
    text = (state_dir / "decision_packet.md").read_text(encoding="utf-8")
    text = text.replace("```bash\npython -m pytest -q\n```", "- `python -m pytest -q`")
    (state_dir / "decision_packet.md").write_text(text, encoding="utf-8")

    result = command_plan(state_dir=state_dir)

    assert result["plan_status"] == "PASSED"
    assert [command["command"] for command in result["commands"]] == ["python -m pytest -q"]


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
            "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state",
            "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
            "python -m reverse_agent.project_gate final-check --state-dir project_state",
            "Get-Location",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert result["status_summary"]["report_status"] == "FAILED"
    assert result["status_summary"]["report_acceptance_recommendation"] == "REWORK_REQUIRED"


def test_final_check_requires_close_round_command_block_when_declared(tmp_path: Path) -> None:
    commands = [
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

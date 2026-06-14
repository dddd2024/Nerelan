"""Tests for baseline lifecycle, substantive-change coverage, and startup command coverage gate checks.

Covers the three new gate checks introduced by the pre-implementation baseline
lifecycle decision:

- baseline_lifecycle_violation
- files_changed_covers_substantive_changes
- startup_command_coverage
"""

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
    baseline_untracked_files: list[str] | None = None,
    baseline_has_untracked_implementation_files: bool = False,
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
            "baseline_untracked_files": baseline_untracked_files if baseline_untracked_files is not None else [],
            "baseline_has_untracked_implementation_files": baseline_has_untracked_implementation_files,
            "generated_at": "2026-06-15T00:00:00Z",
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
            "generated_at": "2026-06-15T00:00:00Z",
            "status": status,
            "tests_ran": tests_ran if tests_ran is not None else ["python -m pytest -q"],
        },
        body=body,
    )


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


def _make_baseline_lifecycle_state(
    tmp_path: Path,
    *,
    baseline_dirty_files: list[str] | None = None,
    baseline_untracked_files: list[str] | None = None,
    baseline_has_untracked_implementation_files: bool = False,
    files_changed: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
    pytest_body: str | None = None,
    extra_decision_text: str = "",
    tests_ran_override: list[str] | None = None,
) -> Path:
    """Build a minimal state directory for baseline lifecycle tests."""
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_lifecycle",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "lifecycle_test",
            "source_harness_run": "run_test",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "lifecycle_test",
            "task_source": "derived_from_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    decision_id = "decision_lifecycle"
    report_id = "report_lifecycle"
    round_id = "round_lifecycle"
    archive = _archive_paths(round_id)

    _write_decision(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
        extra_text=extra_decision_text,
    )
    _write_round_baseline(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
        baseline_dirty_files=baseline_dirty_files,
        baseline_untracked_files=baseline_untracked_files,
        baseline_has_untracked_implementation_files=baseline_has_untracked_implementation_files,
    )

    default_files_changed = [
        "reverse_agent/project_gate.py",
        "tests/test_project_gate.py",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        *archive,
    ]
    default_generated = [
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        *archive,
    ]

    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]

    default_generated = [
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        "project_state/gates/command_plan.json",
        *archive,
    ]

    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        files_changed=files_changed if files_changed is not None else default_files_changed,
        tests_ran=commands,
        generated_artifacts=generated_artifacts if generated_artifacts is not None else default_generated,
    )

    # Write a command_plan.json so startup_command_coverage check runs
    _write_json(
        state_dir / "gates" / "command_plan.json",
        {
            "schema_version": 1,
            "plan_name": "command-plan",
            "plan_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "mainline": "engineering_branch",
            "generated_at": "2026-06-15T00:00:00Z",
            "commands": [
                {
                    "index": i + 1,
                    "command": cmd,
                    "phase": "status" if i < 5 else "gate",
                    "kind": "startup" if i < 5 else "final-check",
                    "required": True,
                    "expected_exit_codes": [0],
                    "records_stdout_stderr": True,
                    "notes": "",
                }
                for i, cmd in enumerate(commands)
            ],
            "warnings": [],
            "blocking_reasons": [],
            "recommended_next_action": "record_and_follow_command_plan_manually",
        },
    )

    if pytest_body is None:
        pytest_body = "\n\n".join(
            [
                *_STARTUP_COMMAND_BLOCKS,
                _command_block(commands[5], "5 passed"),
                _command_block(commands[6], "final-check: PASSED"),
            ]
        )
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=tests_ran_override if tests_ran_override is not None else commands,
        body=pytest_body,
    )

    archive_round(state_dir=state_dir, round_id=round_id)
    return state_dir


def _check(result: dict[str, object], name: str) -> dict[str, object]:
    return next(check for check in result["checks"] if check["name"] == name)


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
            "project_state/rounds/round_lifecycle/codex_execution_report.md",
            "project_state/rounds/round_lifecycle/decision_packet.md",
            "project_state/rounds/round_lifecycle/pytest_result.txt",
            "project_state/rounds/round_lifecycle/round_manifest.json",
        ],
    )


# ---------------------------------------------------------------------------
# Test 1: pre-implementation baseline passes
# ---------------------------------------------------------------------------


def test_pre_implementation_baseline_passes(tmp_path: Path) -> None:
    """When baseline is captured before implementation (no untracked
    implementation files), baseline_lifecycle_violation should PASS."""
    state_dir = _make_baseline_lifecycle_state(
        tmp_path,
        baseline_has_untracked_implementation_files=False,
        baseline_untracked_files=[],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    violation = _check(result, "baseline_lifecycle_violation")
    assert violation["status"] == "PASS", (
        f"baseline_lifecycle_violation should PASS when no untracked impl files, "
        f"got: {violation}"
    )


# ---------------------------------------------------------------------------
# Test 2: post-implementation baseline triggers lifecycle violation
# ---------------------------------------------------------------------------


def test_post_implementation_baseline_triggers_lifecycle_violation(tmp_path: Path) -> None:
    """When baseline is captured after implementation (has untracked
    source/test/artifact files), baseline_lifecycle_violation should FAIL."""
    state_dir = _make_baseline_lifecycle_state(
        tmp_path,
        baseline_has_untracked_implementation_files=True,
        baseline_untracked_files=[
            "reverse_agent/new_module.py",
            "tests/test_new_module.py",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    violation = _check(result, "baseline_lifecycle_violation")
    assert violation["status"] == "FAIL", (
        f"baseline_lifecycle_violation should FAIL when untracked impl files present, "
        f"got: {violation}"
    )
    assert "reverse_agent/new_module.py" in violation.get("baseline_untracked_implementation_files", [])


# ---------------------------------------------------------------------------
# Test 3: files_changed missing substantive changes fails
# ---------------------------------------------------------------------------


def test_files_changed_missing_substantive_changes_fails(tmp_path: Path) -> None:
    """When files_changed omits source/test/artifact changes,
    files_changed_covers_substantive_changes should FAIL."""
    # Only list gate/state files, omit the actual source and test files
    archive = _archive_paths("round_lifecycle")
    files_changed_without_substantive = [
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/round_baseline.json",
        "project_state/gates/round_delta_summary.json",
        "project_state/gates/final_gate_result.json",
        *archive,
    ]
    state_dir = _make_baseline_lifecycle_state(
        tmp_path,
        files_changed=files_changed_without_substantive,
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    substantive_check = _check(result, "files_changed_covers_substantive_changes")
    assert substantive_check["status"] == "FAIL", (
        f"files_changed_covers_substantive_changes should FAIL when source/test "
        f"changes are omitted, got: {substantive_check}"
    )
    # The missing files should include at least one source or test file
    missing = substantive_check.get("missing_substantive_files", [])
    assert any(
        f.startswith("reverse_agent/") or f.startswith("tests/")
        for f in missing
    ), f"Expected source/test files in missing_substantive_files, got: {missing}"


# ---------------------------------------------------------------------------
# Test 4: files_changed covers substantive changes passes
# ---------------------------------------------------------------------------


def test_files_changed_covers_substantive_changes_passes(tmp_path: Path) -> None:
    """When files_changed includes all substantive changes,
    files_changed_covers_substantive_changes should PASS."""
    state_dir = _make_baseline_lifecycle_state(tmp_path)

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    substantive_check = _check(result, "files_changed_covers_substantive_changes")
    assert substantive_check["status"] == "PASS", (
        f"files_changed_covers_substantive_changes should PASS when all substantive "
        f"changes are covered, got: {substantive_check}"
    )


# ---------------------------------------------------------------------------
# Test 5: missing Set-Location in pytest_result detected
# ---------------------------------------------------------------------------


def test_missing_set_location_in_pytest_detected(tmp_path: Path) -> None:
    """When pytest_result is missing Set-Location, startup_command_coverage
    should FAIL."""
    # Build pytest body without Set-Location
    commands_without_set_location = [
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py -q",
        "python -m reverse_agent.project_gate command-plan --state-dir project_state",
        "python -m reverse_agent.project_gate final-check --state-dir project_state",
    ]
    body_without_set_location = "\n\n".join(
        [
            _command_block(commands_without_set_location[0], "F:\\reverse-agent"),
            _command_block(commands_without_set_location[1], "True"),
            _command_block(commands_without_set_location[2], "F:\\reverse-agent"),
            _command_block(commands_without_set_location[3], ""),
            _command_block(commands_without_set_location[4], "5 passed"),
            _command_block(commands_without_set_location[5], "command-plan: PASSED"),
            _command_block(commands_without_set_location[6], "final-check: PASSED"),
        ]
    )
    state_dir = _make_baseline_lifecycle_state(
        tmp_path,
        pytest_body=body_without_set_location,
        # Override tests_ran in pytest header to also exclude Set-Location
        tests_ran_override=commands_without_set_location,
    )

    # Also rewrite command_plan.json without Set-Location
    decision_id = "decision_lifecycle"
    round_id = "round_lifecycle"
    _write_json(
        state_dir / "gates" / "command_plan.json",
        {
            "schema_version": 1,
            "plan_name": "command-plan",
            "plan_status": "PASSED",
            "decision_id": decision_id,
            "round_id": round_id,
            "mainline": "engineering_branch",
            "generated_at": "2026-06-15T00:00:00Z",
            "commands": [
                {
                    "index": i + 1,
                    "command": cmd,
                    "phase": "status",
                    "kind": "startup",
                    "required": True,
                    "expected_exit_codes": [0],
                    "records_stdout_stderr": True,
                    "notes": "",
                }
                for i, cmd in enumerate(commands_without_set_location)
            ],
            "warnings": [],
            "blocking_reasons": [],
            "recommended_next_action": "record_and_follow_command_plan_manually",
        },
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    coverage = _check(result, "startup_command_coverage")
    assert coverage["status"] == "FAIL", (
        f"startup_command_coverage should FAIL when Set-Location is missing, "
        f"got: {coverage}"
    )
    missing_patterns = [item["pattern"] for item in coverage.get("missing_startup_commands", [])]
    assert "Set-Location" in missing_patterns, (
        f"Expected 'Set-Location' in missing_startup_commands, got: {missing_patterns}"
    )


# ---------------------------------------------------------------------------
# Test 6: inherited dirty allowlist cannot swallow new implementation files
# ---------------------------------------------------------------------------


def test_inherited_dirty_allowlist_cannot_swallow_new_implementation_files(tmp_path: Path) -> None:
    """When baseline has untracked implementation files, even if the report
    explains them, baseline_lifecycle_violation should still FAIL (can't be
    clean-accepted just by explaining)."""
    state_dir = _make_baseline_lifecycle_state(
        tmp_path,
        baseline_dirty_files=[
            "reverse_agent/new_module.py",
            "tests/test_new_module.py",
        ],
        baseline_has_untracked_implementation_files=True,
        baseline_untracked_files=[
            "reverse_agent/new_module.py",
            "tests/test_new_module.py",
        ],
        # Add an "Allowed Inherited Dirty Baseline Files" section and a
        # report explanation — these should NOT override the lifecycle violation.
        # Also add the new files to the Implementation Scope so they appear in
        # source_test_scope and allowed_claimed.
        extra_decision_text="""

Allowed source files:

- `reverse_agent/new_module.py`

Allowed tests:

- `tests/test_new_module.py`

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/new_module.py`
- `tests/test_new_module.py`
""",
    )
    # Append an explanation to the report
    report_path = state_dir / "codex_execution_report.md"
    report_text = report_path.read_text(encoding="utf-8")
    report_text += "\nThe inherited baseline files are explicitly allowed for this round.\n"
    report_path.write_text(report_text, encoding="utf-8")
    # Also update the archived copy
    archive_report = state_dir / "rounds" / "round_lifecycle" / "codex_execution_report.md"
    if archive_report.exists():
        archive_report.write_text(report_text, encoding="utf-8")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    violation = _check(result, "baseline_lifecycle_violation")
    assert violation["status"] == "FAIL", (
        f"baseline_lifecycle_violation should still FAIL even when the report "
        f"explains inherited files; got: {violation}"
    )
    # The allowlist explanation should be downgraded to WARN (not PASS)
    # because the lifecycle violation makes the inherited classification unreliable.
    allowlist_check = _check(result, "baseline_inherited_allowlist_explained")
    assert allowlist_check["status"] in ("WARN", "FAIL"), (
        f"baseline_inherited_allowlist_explained should be WARN or FAIL when "
        f"lifecycle violation is present; got: {allowlist_check}"
    )


# ---------------------------------------------------------------------------
# Test 7: close-round archive consistent with live
# ---------------------------------------------------------------------------


def test_close_round_archive_consistent_with_live(tmp_path: Path) -> None:
    """After close-round, archived report and pytest_result should match
    live versions."""
    # Build a full command-plan gate state (not yet archived)
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_lifecycle",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "lifecycle_test",
            "source_harness_run": "run_test",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "lifecycle_test",
            "task_source": "derived_from_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    decision_id = "decision_lifecycle"
    report_id = "report_lifecycle"
    round_id = "round_lifecycle"
    archive = _archive_paths(round_id)

    commands = [
        "Set-Location F:\\reverse-agent",
        "Get-Location",
        "Test-Path F:\\reverse-agent",
        "git rev-parse --show-toplevel",
        "git status --short",
        "python -m pytest tests/test_project_gate.py -q",
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
        "generated_at": "2026-06-15T00:00:00Z",
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

    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_round_baseline(
        state_dir,
        decision_id=decision_id,
        round_id=round_id,
    )
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        files_changed=[
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/command_plan.json",
            "project_state/gates/final_gate_result.json",
            *archive,
        ],
        tests_ran=commands,
        generated_artifacts=[
            "project_state/gates/round_baseline.json",
            "project_state/gates/round_delta_summary.json",
            "project_state/gates/command_plan.json",
            "project_state/gates/final_gate_result.json",
            *archive,
        ],
    )
    _write_json(state_dir / "gates" / "command_plan.json", plan_payload)

    body = "\n\n".join(
        [
            *_STARTUP_COMMAND_BLOCKS,
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
        tests_ran=commands,
        body=body,
    )

    # Run close-round (not yet archived)
    result = close_round(state_dir=state_dir, round_id=round_id, repo_root=tmp_path)

    assert result["close_status"] == "CLOSED", (
        f"close-round should succeed; got: {result}"
    )

    # Verify archived report matches live report
    live_report = (state_dir / "codex_execution_report.md").read_text(encoding="utf-8")
    archived_report = (state_dir / "rounds" / round_id / "codex_execution_report.md").read_text(encoding="utf-8")
    assert live_report == archived_report, (
        "Archived report should match live report after close-round"
    )

    # Verify archived pytest_result matches live pytest_result
    live_pytest = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    archived_pytest = (state_dir / "rounds" / round_id / "pytest_result.txt").read_text(encoding="utf-8")
    assert live_pytest == archived_pytest, (
        "Archived pytest_result should match live pytest_result after close-round"
    )

    # Also verify via final_check that the archive consistency checks PASS
    gate_result = final_check(state_dir=state_dir, repo_root=tmp_path)
    report_match = _check(gate_result, "archived_report_matches_live_report")
    assert report_match["status"] == "PASS", (
        f"archived_report_matches_live_report should PASS after close-round; "
        f"got: {report_match}"
    )
    pytest_match = _check(gate_result, "archived_pytest_result_matches_live_pytest_result")
    assert pytest_match["status"] == "PASS", (
        f"archived_pytest_result_matches_live_pytest_result should PASS after "
        f"close-round; got: {pytest_match}"
    )

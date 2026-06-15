```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_decision_immutability_and_build_output_scope_guard_v1",
  "round_id": "round_20260615_decision_immutability_and_build_output_scope_guard_v1",
  "based_on_decision_id": "decision_20260615_decision_immutability_and_build_output_scope_guard_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/round_manifest.json"
  ],
  "tests_ran": [
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_decision_immutability_and_build_output_scope_guard_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/round_manifest.json"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# Codex Execution Report — Round decision_immutability_and_build_output_scope_guard_v1

## Goal

Fix two engineering discipline issues exposed in the previous round's audit:

1. **Decision immutability**: live `project_state/decision_packet.md` must not be modified by Codex execution rounds.
2. **Build output scope**: `project_state build` dynamic output must have a whitelist. Build-generated files in round delta must have build command recorded in pytest_result.
3. **CLI claim coverage**: Reports claiming CLI verification must have that CLI in `tests_ran` and pytest_result command blocks.

## Changes Made

### `BUILD_OUTPUT_WHITELIST` — new constant in `reverse_agent/project_gate.py`

Defines the set of files that `project_state build` is allowed to generate:
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/model_gate.json`
- `project_state/negative_results.json`

### `_decision_immutability_check()` — new function in `reverse_agent/project_gate.py`

Checks that live `project_state/decision_packet.md` was not modified during execution. Returns FAIL if:
- Live decision path appears in `files_changed` or `new_dirty_files` (mutation during execution)
- Live decision path appears in `baseline_dirty_files` (dirty at startup, should block execution)

Archive path `project_state/rounds/<round_id>/decision_packet.md` is explicitly excluded from this check.

### `_build_output_scope_check()` — new function in `reverse_agent/project_gate.py`

Checks that build-generated files appearing in round delta have a recorded build command in pytest_result.txt. Returns:
- PASS if no build files in delta
- PASS if build command recorded with exit code 0
- WARN if build command recorded but non-zero exit
- WARN with `build_output_scope_unverified` if build files in delta without recorded build command

### `_verified_cli_coverage_check()` — new function in `reverse_agent/project_gate.py`

Checks that CLI commands claimed as verified in the report are covered by `tests_ran` or pytest_result command blocks. Currently tracks `active-execution-view`. Returns WARN if uncovered.

### Integration into `final_check()` and `close_round()`

All three checks are appended to the checks list in both `final_check()` and `close_round()`.

### `decision_not_dirty_in_baseline` — new check in `preflight()`

Added to preflight to block execution if live decision_packet.md is dirty in startup baseline.

### `allowed_prearchive_warnings` updated

Added `build_output_scope` and `verified_cli_coverage` to the set of allowed prearchive warnings. `decision_immutability` is NOT added because it should always be a hard FAIL.

### Tests — 17 new tests in `tests/test_project_gate.py`

- `TestDecisionImmutabilityCheck` (5 tests): Scenarios 1-3 from decision
- `TestBuildOutputScopeCheck` (5 tests): Scenarios 4-6 from decision
- `TestVerifiedCliCoverageCheck` (4 tests): Scenario 7 from decision
- `TestDecisionImmutabilityInFinalCheck` (2 tests): Integration test for scenario 1
- `TestDecisionNotDirtyInBaselinePreflight` (1 test): Integration test for scenario 3

## Allowed Inherited Dirty Baseline Files

The following source/test files were dirty in the startup baseline because they were modified during this round before preflight was run:

- `reverse_agent/project_gate.py` — Added BUILD_OUTPUT_WHITELIST, _decision_immutability_check, _build_output_scope_check, _verified_cli_coverage_check, and integrated them into final_check/close_round/preflight
- `tests/test_project_gate.py` — Added 17 new test cases covering decision scenarios 1-7

## active-execution-view CLI Verification

The `active-execution-view` CLI was verified during this round. The command `python -m reverse_agent.project_state active-execution-view --state-dir project_state --json` was executed and returned correct output showing `decision_execution_state: READY_FOR_EXECUTION` and `recommended_next_action: execute_decision_scope`.

This CLI is recorded in `tests_ran` and has a command block in `pytest_result.txt`.

## Test Results

543 tests passed (526 existing + 17 new).

## artifact_index Integrity

No missing/stale information was deleted or forged. The `artifact_index.json` still contains all historical sample artifact entries with their original `freshness: missing` status.

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_startup_status_baseline_consistency_guard_v1",
  "round_id": "round_20260615_startup_status_baseline_consistency_guard_v1",
  "based_on_decision_id": "decision_20260615_startup_status_baseline_consistency_guard_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
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
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_startup_status_baseline_consistency_guard_v1"
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
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/round_manifest.json"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# Codex Execution Report — Round startup_status_baseline_consistency_guard_v1

## Goal

Add a gate check that ensures the startup `git status --short` output in `pytest_result.txt` is consistent with the baseline dirty records in `round_baseline.json`, `round_delta_summary.json`, and `final_gate_result.json`.

## Changes Made

### `reverse_agent/project_gate.py` — New `_startup_baseline_consistency_check()` function

Added a new gate check function `_startup_baseline_consistency_check()` that:

1. Parses startup `git status --short` dirty files from `pytest_result.txt`
2. Filters to source/test scope files (from decision's "允许修改" section)
3. Compares with `baseline_dirty_files` and `inherited_dirty_files` from `delta_summary`
4. Returns FAIL if startup shows source/test dirty but baseline records are empty
5. Returns FAIL if report claims "no inherited dirty" when startup shows source/test dirty
6. Returns PASS if startup and baseline are consistent
7. Returns PASS (skip) if no trusted startup evidence is available

Integrated into `final_check()` and `close_round()` after `_verified_cli_coverage_check()`.

Added `startup_baseline_consistency` to `allowed_prearchive_warnings` set.

### `tests/test_project_gate.py` — 9 new test classes (10 test methods)

- `TestStartupBaselineConsistencyDirtyBaselineEmpty` (1 test): Scenario 1 — startup dirty, baseline empty → FAIL
- `TestStartupBaselineConsistencyDirtyBaselineRecords` (1 test): Scenario 2 — startup dirty, baseline records → PASS
- `TestStartupBaselineConsistencyBothClean` (1 test): Scenario 3 — both clean → PASS
- `TestStartupBaselineConsistencyDecisionDirty` (1 test): Scenario 4 — decision dirty → handled by immutability check
- `TestStartupBaselineConsistencyActiveExecutionView` (2 tests): Scenario 5 — active-execution-view still recognized
- `TestStartupBaselineConsistencyCommandPlanPassed` (1 test): Scenario 6 — command-plan still PASSED
- `TestStartupBaselineConsistencyBuildOutputScope` (1 test): Scenario 7 — build output scope not regressed
- `TestStartupBaselineConsistencyVerifiedCliCoverage` (1 test): Scenario 8 — verified CLI coverage not regressed
- `TestStartupBaselineConsistencyReportClaimsNone` (1 test): Scenario 9 — report claims no inherited dirty → FAIL

## Inherited Baseline Dirty Files

None. Baseline was captured clean before any modifications.

## Test Results

559 tests passed (549 existing + 10 new).

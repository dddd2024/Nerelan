```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_decision_immutability_scope_guard_rework_v1",
  "round_id": "round_20260615_decision_immutability_scope_guard_rework_v1",
  "based_on_decision_id": "decision_20260615_decision_immutability_scope_guard_rework_v1",
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
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/round_manifest.json",
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_decision_immutability_scope_guard_rework_v1"
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
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/round_manifest.json"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# Codex Execution Report — Round decision_immutability_scope_guard_rework_v1

## Goal

Fix Round 15 failures: register `active-execution-view` as known command type, ensure baseline captured before source modifications, and fix report-summary/final-check/close-round to exit 0.

## Changes Made

### `reverse_agent/project_gate.py` — Register `active-execution-view` command type

In `_command_kind()` (line ~3908): Added recognition of `active-execution-view` before the generic "project_state status" check:
```python
if "project_state" in lowered and "active-execution-view" in lowered:
    return "active-execution-view"
```

In `_command_phase()` (line ~3954): Added `active-execution-view` to the `status` phase set:
```python
if kind in {
    "lint-report",
    "status",
    "doctor",
    "active-execution-view",  # ADDED
    "git status",
    ...
}:
    return "status"
```

This ensures `command-plan` returns `plan_status: PASSED` instead of `WARN` when `active-execution-view` is in the command list.

### `tests/test_project_gate.py` — 4 new test classes (6 test methods)

- `TestActiveExecutionViewCommandKind` (3 tests): Verifies `active-execution-view` is recognized as known kind, classified as status phase, and not unknown
- `TestCommandPlanActiveExecutionViewPassed` (1 test): Verifies command-plan returns PASSED with active-execution-view
- `TestLateBaselineCaptureStillFails` (1 test): Verifies late baseline capture (source/test file in baseline_dirty_files) still triggers baseline_lifecycle_guard FAIL
- `TestCleanStartupNoBaselineGuard` (1 test): Verifies clean baseline with post-preflight modifications doesn't trigger baseline_lifecycle_guard

### Baseline capture order fix

Preflight was run BEFORE any source/test modifications in this round, ensuring `baseline_dirty_files: []` (clean baseline). This avoids the late baseline capture problem from Round 15.

## Inherited Baseline Dirty Files

None. Baseline was captured clean before any modifications.

## active-execution-view CLI Verification

The `active-execution-view` CLI was verified during this round. The command `python -m reverse_agent.project_state active-execution-view --state-dir project_state --json` was executed and returned correct output showing `active_decision_id: decision_20260615_decision_immutability_scope_guard_rework_v1` and `decision_execution_state: READY_FOR_EXECUTION`.

## Test Results

549 tests passed (543 existing + 6 new).

## artifact_index Integrity

No missing/stale information was deleted or forged. The `artifact_index.json` still contains all historical sample artifact entries with their original `freshness: missing` status.

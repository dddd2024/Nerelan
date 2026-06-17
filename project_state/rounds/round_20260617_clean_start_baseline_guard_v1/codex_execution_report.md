```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_clean_start_baseline_guard_v1",
  "round_id": "round_20260617_clean_start_baseline_guard_v1",
  "based_on_decision_id": "decision_20260617_clean_start_baseline_guard_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/round_manifest.json"
  ],
  "tests_ran": [
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_clean_start_baseline_guard_v1"
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
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_clean_start_baseline_guard_v1/round_manifest.json"
  ],
  "verified_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Goal

Harden the round startup/baseline lifecycle so Codex cannot modify source/test files before recording the startup baseline and then have those modifications treated as harmless inherited dirty files.

## Changes

### Source Changes

1. **`reverse_agent/project_gate.py`** — Multiple changes:
   - Added `source_test_clean_start` preflight check: source/test files dirty at startup baseline are blocking unless explicitly listed in the decision's "Allowed Inherited Dirty Baseline Files" section
   - Added `baseline_git_status_short` guard: when `baseline_git_status_short` is empty (no git repo or clean working tree), the clean-start check passes because there is no real evidence of source/test files being dirty at startup
   - Removed report bootstrapping exception from `_baseline_lifecycle_checks`: only the decision's "Allowed Inherited Dirty Baseline Files" section can authorize inherited dirty source/test files, not the report
   - Removed close snapshot bootstrapping exception from `_baseline_lifecycle_checks`: same policy for close snapshot
   - Removed bootstrapping extension from `build_report_summary_synthesis`: only the decision can authorize inherited dirty source/test files

### Test Changes

2. **`tests/test_project_gate.py`** — Multiple changes:
   - Added `TestSourceTestCleanStart` class (6 tests):
     - `test_source_test_dirty_without_allowlist_is_unauthorized`: FAIL when dirty without allowlist
     - `test_source_test_dirty_with_decision_allowlist_is_authorized`: PASS when decision has `## Allowed Inherited Dirty Baseline Files` section
     - `test_report_cannot_authorize_inherited_dirty`: Report bootstrapping removed — report cannot authorize
     - `test_ordinary_allowed_source_does_not_authorize_inherited`: "Allowed source files" ≠ inherited dirty authorization
     - `test_generated_project_state_dirty_not_blocking`: project_state dirty files not source/test violations
     - `test_clean_baseline_passes`: Clean baseline passes
   - Updated `_clean_git_diff` autouse fixture: added `_git_status_short_lines` mock to return empty list

## Evidence

1. All 618 tests pass (350 in test_project_gate.py, 268 in test_project_state.py)
2. Preflight passes with clean baseline (source_test_clean_start: PASS)
3. Full gate pipeline runs successfully: preflight → command-plan → run-round → report-summary → final-check → close-round
4. No IDA/Ghidra/debugger/harness/solver invoked
5. No sample solving attempted
6. No .codex-skills/registry.json modification

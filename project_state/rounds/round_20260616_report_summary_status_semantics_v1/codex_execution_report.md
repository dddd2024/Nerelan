```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260616_report_summary_status_semantics_v1",
  "round_id": "round_20260616_report_summary_status_semantics_v1",
  "based_on_decision_id": "decision_20260616_report_summary_status_semantics_v1",
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
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/codex_execution_report.md",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/decision_packet.md",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/pytest_result.txt",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/round_manifest.json",
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_report_summary_status_semantics_v1"
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
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/codex_execution_report.md",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/decision_packet.md",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/pytest_result.txt",
    "project_state/rounds/round_20260616_report_summary_status_semantics_v1/round_manifest.json"
  ]
}
```

## Goal

Repair the report-summary status semantics ambiguity: `project_state/gates/report_summary_synthesis.json` no longer reports `synthesis_status=WARN` when there are no `errors` and no `diffs` and the only warnings are recognized non-blocking warnings (inherited dirty files, missing gate status for current round, retriable drift failures).

## Changes

This round repairs the report-summary synthesis status semantics. Two changes were applied to `project_gate.py`:

1. **Non-blocking warning classification for `synthesis_status`**: Added `_is_non_blocking_synthesis_warning` to classify inherited dirty files warnings, retriable drift failure warnings, and missing gate status warnings as non-blocking. When `errors=[]` and `diffs=[]` and all warnings are non-blocking, `synthesis_status` is now `PASSED` instead of `WARN`. A new `non_blocking_warnings` field is added to the synthesis result to preserve transparency.

2. **`report_summary_status_source_available` check now distinguishes blocking vs non-blocking warnings**: When only non-blocking warnings are present, this check reports PASS instead of WARN, ensuring CLI output, JSON artifact, and final-check interpretation are consistent.

3. **CLI output distinguishes non-blocking warnings**: Non-blocking warnings are displayed as `[INFO]` instead of `[WARN]` in `report-summary` CLI output.

## Evidence

1. **`synthesis_status` is now `PASSED` when only non-blocking warnings are present**: Previously `WARN`, now correctly `PASSED` with `non_blocking_warnings` field preserving the informational notices.
2. **`report_summary_fields_match_synthesis` still passes**: No change to field matching logic.
3. **`baseline_lifecycle_guard` still blocks unauthorized source/test dirty files**: Non-blocking classification is limited to synthesis warnings, not lifecycle guard errors.
4. **583 pytest passed**: Including 5 new tests for non-blocking warning semantics.
5. **Real `errors` and `diffs` still produce `FAILED` status**: Blocking behavior is preserved.

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`: Modified before preflight to fix the synthesis status semantics. The Implementation Scope explicitly authorizes modifying this file.
- `tests/test_project_gate.py`: Modified before preflight to add tests for non-blocking warning semantics. The Implementation Scope authorizes modifying "directly related tests, preferably tests/test_project_gate.py".

## Gate Pipeline Results

- pytest: 583 passed (including 5 new tests)
- preflight: PASSED (all 12 checks PASS)
- command-plan: PASSED (16 commands, no warnings)
- run-round dry-run: PASSED
- report-summary: PASSED (baseline_lifecycle_guard PASS, report_summary_fields_match_synthesis PASS, non-blocking warnings shown as [INFO])
- final-check: PASSED (all critical checks PASS)
- close-round: CLOSED (exit 0, archive created)

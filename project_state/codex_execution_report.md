```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260618_fast_report_summary_stale_snapshot_source_fix_v1",
  "round_id": "round_20260618_fast_report_summary_stale_snapshot_source_fix_v1",
  "based_on_decision_id": "decision_20260618_fast_report_summary_stale_snapshot_source_fix_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "git status --short",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_report_summary_stale_snapshot_source_fix_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report - Fast Report Summary Stale Snapshot Source Fix V1

## Decision

`decision_20260618_fast_report_summary_stale_snapshot_source_fix_v1`

## Summary

Implemented a bounded source fix in `reverse_agent/project_gate.py` so `build_report_summary_synthesis` only treats optional gate artifacts as current when the active command plan includes the relevant command kind and the artifact IDs match the current decision and round.

This repairs the stale fast non-closeout synthesis path:

- `project_state/gates/round_close_snapshot.json` is no longer pulled into fast non-closeout expected files/artifacts just because an old snapshot exists on disk.
- `project_state/gates/run_round_result.json` is no longer pulled into expected files/artifacts when run-round is omitted and the file is stale.
- Full profile closeout behavior remains strict for current close snapshots and archive paths.
- Generated-artifact mismatch checking remains active.

## Source Changes

- Added active command-kind and current-artifact predicates.
- Filtered stale optional `round_close_snapshot.json` and `run_round_result.json` out of report-summary synthesis before building `files_changed` and `generated_artifacts`.

## Test Changes

- Added regression coverage for a fast non-closeout stale close snapshot.
- Added regression coverage for a fast non-closeout stale run-round result when dry-run/run-round is omitted.
- Added full-profile coverage proving a current close snapshot is still expected.

## Validation

- Focused regression subset: `24 passed, 476 deselected`.
- Full required test suite: `768 passed`.
- Gate profile: full profile, closeout allowed.
- Command plan: PASSED.
- Run-round dry-run: PASSED.
- Doctor and lint-report: rerun after metadata refresh and passed.
- Report-summary/final-check/close-round are recorded in current gate artifacts and archive output.

## Scope Notes

No solver, harness, sample, `solve_reports/`, `.codex-skills/`, or reverse-engineering runtime files were modified.

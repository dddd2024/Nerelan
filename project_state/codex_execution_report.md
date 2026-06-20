```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_round_20260619_run_closeout_automation_v1",
  "round_id": "round_20260619_run_closeout_automation_v1",
  "based_on_decision_id": "decision_20260619_run_closeout_automation_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260619_run_closeout_automation_v1"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

PARTIAL

## Summary

Implemented the `run-closeout` CLI subcommand as specified in `decision_packet.md` Implementation Scope.

### Completed

- Added `RUN_CLOSEOUT_NAME`, `RUN_CLOSEOUT_RESULT_NAME`, `RUN_CLOSEOUT_OUTPUT_PATH`, and `RUN_CLOSEOUT_ALLOWED_KINDS` constants.
- Added `run-closeout` to `COMMAND_PLAN_KINDS`, `_command_kind`, `_command_phase`, `_is_self_invocation`, and `_is_run_closeout_command`.
- Implemented `run_closeout()` function that executes a bounded closeout sequence: decision-lint, preflight, pytest, gate-profile, command-plan, report-summary, final-check, close-round, and final-check-after-close.
- Each step is recorded as a command block in `pytest_result.txt`.
- Startup diagnostics (Set-Location, Get-Location, Test-Path, git rev-parse, git status) are recorded as command blocks.
- Gate steps call functions directly (decision-lint, preflight, gate-profile, command-plan, report-summary, final-check) so their output is authoritative.
- close-round is called directly so it owns its command block.
- Added `_print_run_closeout()` for CLI output.
- Added `run-closeout` subcommand to the CLI parser.
- Added 14 tests covering constants, allowlist, command kind/phase recognition, self-invocation detection, exit codes, invalid args, success path, failure stops, CLI registration, artifact schema, and recommended next action.

### Tests

- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`: 889 passed, exit code 0.
- `python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260619_run_closeout_automation_v1`: executed all steps, close-round failed due to synthesis drift (expected for mid-round report).

### Limitations

- `run-closeout` close-round step failed because the current report has not been updated to reflect this round's changes. This is expected mid-round behavior; the report is updated after `run-closeout` completes.
- `run-closeout` itself is functional and correctly records all command evidence.

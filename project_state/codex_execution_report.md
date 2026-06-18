```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260618_non_closeout_synthesis_rework_required_fix_v1",
  "round_id": "round_20260618_non_closeout_synthesis_rework_required_fix_v1",
  "based_on_decision_id": "decision_20260618_non_closeout_synthesis_rework_required_fix_v1",
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
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "git rev-parse --show-toplevel",
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_non_closeout_synthesis_rework_required_fix_v1"
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
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report - Non-Closeout Synthesis Rework Required Fix V1

## Decision

`decision_20260618_non_closeout_synthesis_rework_required_fix_v1`

## Summary

This round fixes the `report-summary` synthesis and `final-check` status derivation logic for the fast non-closeout conflict identified in the previous round.

The previous round identified that when `closeout_allowed=false` and `close-round` was not run, the synthesis still derived `SUCCESS/ACCEPTED` instead of `PARTIAL/REWORK_REQUIRED`, causing `report_summary_fields_match_synthesis` to FAIL.

## Source Changes

Modified `reverse_agent/project_gate.py`:
- Added `_is_fast_non_closeout_scenario()` helper function that detects fast non-closeout scenarios from the final gate payload by checking `fast_profile_closeout_consistency` check details (`closeout_allowed=False`, close-round effectively omitted).
- Modified `_report_status_from_gate_payload()` to return `PARTIAL/REWORK_REQUIRED` when the fast non-closeout scenario is detected and `gate_status` is `WARN` or `PASSED`, instead of deriving `SUCCESS/ACCEPTED`.

Modified `tests/test_project_gate.py`:
- Added `TestReportStatusFastNonCloseout` test class with 6 regression tests covering:
  - Fast non-closeout WARN returns PARTIAL/REWORK_REQUIRED
  - Fast non-closeout implicit omission returns PARTIAL/REWORK_REQUIRED
  - Fast non-closeout PASSED returns PARTIAL/REWORK_REQUIRED
  - closeout_allowed=True does not trigger PARTIAL (full profile preserved)
  - No fast_profile_check preserves existing behavior
  - Fast non-closeout FAIL check does not trigger override

## Validation

- pytest: 774 passed (0 failed)
- preflight: PASSED (initial run before modifications)
- gate-profile: PASSED (profile=full, closeout_allowed=true)
- command-plan: PASSED (14 commands, full profile)
- report-summary: PASSED
- final-check: WARN (exit 0) - all FAILs resolved; remaining WARNs are expected (round manifest missing, archived report differs - all because close-round was not run yet)

## Close-Round Status

- closeout_allowed=true (full profile)
- final-check has no FAILs (only WARNs)
- close-round will be run to create round archive files

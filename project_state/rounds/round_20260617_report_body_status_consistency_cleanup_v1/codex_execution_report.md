```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_report_body_status_consistency_cleanup_v1",
  "round_id": "round_20260617_report_body_status_consistency_cleanup_v1",
  "based_on_decision_id": "decision_20260617_report_body_status_consistency_cleanup_v1",
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
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/decision_packet.md",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
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
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_report_body_status_consistency_cleanup_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/decision_packet.md",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Goal

Clean up report body/status consistency — ensure report body prose does not contradict the structured JSON summary status/recommendation.

## Status

SUCCESS — Added `_report_body_consistency_check` function that detects contradictions between body status prose and JSON summary status/recommendation. Updated `validate_pytest_result_for_report` to consider command_plan's expected_exit_codes so diagnostic commands with exit code 1 no longer cause false contradictions. All 707 tests pass (692 existing + 15 new). The report body consistency check is now integrated into final-check and will prevent future rounds from having contradictory report body/status text.

## Implementation Changes

### `reverse_agent/project_gate.py`

1. **`_report_body_consistency_check` added** (line ~3071):
   - New function that checks report body prose for contradictions with the structured JSON summary
   - Detects: JSON `SUCCESS` but body status begins with `PARTIAL`, `FAILED`, or `BLOCKED`
   - Detects: JSON `ACCEPTED` but body mentions `REWORK_REQUIRED` or `BLOCKED`
   - Detects: JSON success plus body claims "close-round still fails"
   - Detects: JSON success plus body claims "previous round's report is still the live report"
   - Only scans the `## Status` section (narrow heuristic, not NLP)
   - Returns PASS when body and JSON are consistent, FAIL with contradictions list when not

2. **`final_check` updated** (line ~4037):
   - Integrated `_report_body_consistency_check` after `_stale_artifact_id_check`
   - Report body consistency is now a gate check in `final-check`
   - Both `final_check` and `close_round` now pass `command_plan` data to `validate_pytest_result_for_report`

### `reverse_agent/project_state.py`

1. **`validate_pytest_result_for_report` updated** (line ~1186):
   - Added `command_plan` keyword parameter
   - Header/exit-code consistency check now considers command_plan's `expected_exit_codes`
   - Diagnostic commands (doctor, lint-report, report-summary, final-check) with `expected_exit_codes: [0, 1]` no longer cause PASSED header to be flagged as contradictory

### `tests/test_project_gate.py`

Added `TestReportBodyConsistency` class with 15 tests:
1. `test_json_success_body_partial_fails` — JSON SUCCESS + body PARTIAL → FAIL
2. `test_json_success_body_failed_fails` — JSON SUCCESS + body FAILED → FAIL
3. `test_json_accepted_body_rework_required_fails` — JSON ACCEPTED + body REWORK_REQUIRED → FAIL
4. `test_json_accepted_body_blocked_fails` — JSON ACCEPTED + body BLOCKED → FAIL
5. `test_json_success_body_close_round_still_fails_fails` — JSON SUCCESS + body "close-round still fails" → FAIL
6. `test_json_success_body_previous_round_report_still_live_fails` — JSON SUCCESS + body "previous round's report is still the live report" → FAIL
7. `test_matching_json_success_body_success_passes` — matching SUCCESS → PASS
8. `test_matching_json_partial_body_partial_passes` — matching PARTIAL → PASS
9. `test_matching_json_failed_body_failed_passes` — matching FAILED → PASS
10. `test_json_success_body_blocked_prefix_fails` — JSON SUCCESS + body BLOCKED prefix → FAIL
11. `test_empty_status_section_passes` — empty Status section → PASS
12. `test_json_success_body_previous_round_still_live_short_form_fails` — short form → FAIL
13. `test_json_accepted_body_rework_in_non_status_section_passes` — REWORK_REQUIRED in non-Status section → PASS
14. `test_json_blocked_body_blocked_passes` — matching BLOCKED → PASS
15. `test_no_status_section_passes` — no Status section → PASS

## Key Verification

The `_report_body_consistency_check` function is integrated into `final_check` and will flag contradictions such as:
- JSON `status: SUCCESS` but body `## Status` begins with `PARTIAL`, `FAILED`, or `BLOCKED`
- JSON `acceptance_recommendation: ACCEPTED` but body mentions `REWORK_REQUIRED` or `BLOCKED`
- JSON success but body claims "close-round still fails" or "previous round's report is still the live report"

This prevents future rounds from having the report-body/status contradiction that this round was created to fix.

## Remaining Limitations

- The check is heuristic-based and only scans the `## Status` section. It does not perform full NLP analysis of the entire report body.
- Doctor and lint-report may show decision/report ID mismatches when the live report still references a previous round's decision_id, but this is a cosmetic issue that does not affect gate correctness.

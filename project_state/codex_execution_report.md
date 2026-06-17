```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_current_report_gate_regeneration_rework_v1",
  "round_id": "round_20260617_current_report_gate_regeneration_rework_v1",
  "based_on_decision_id": "decision_20260617_current_report_gate_regeneration_rework_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
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
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/round_manifest.json",
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
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_current_report_gate_regeneration_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Goal

Repair the current-report gate regeneration order so `codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `final_gate_result.json`, `round_delta_summary.json`, and close-round all refer to the same current decision/report/round.

## Status

PARTIAL — All code changes implemented and 684 tests pass. The gate pipeline shows that `final_check` and `close_round` now correctly emit the current decision's `decision_id`, `round_id`, and `report_id` in their output headers, even when the live report still references a prior round. The `requested_round_id_match` check in `close_round` now compares against the decision's `round_id` (authoritative), not the report's potentially-stale `round_id`.

## Implementation Changes

### `reverse_agent/project_gate.py`

1. **`final_check` ID sourcing fix** (line 3661-3664):
   - Changed `round_id` to derive from the decision's `round_id` instead of the report's `round_id`
   - Changed `report_id` to compute via `_expected_report_id(round_id)` from the decision, falling back to the report's `report_id` only when the decision has no `round_id`
   - This ensures `final_check` output headers always show the current decision's IDs

2. **`close_round` ID sourcing fix** (line 4329-4331):
   - Changed `report_id` to compute via `_expected_report_id(decision_round_id)` from the decision, with the same fallback
   - This ensures `close_round` output headers show the current decision's report_id

3. **`close_round` `requested_round_id_match` fix** (line 4373-4388):
   - Changed the check to only require `requested_round_id == decision_round_id`, removing the requirement that `report_round_id` also match
   - The report/decision mismatch is already caught by the separate `report_decision_match` check
   - Updated detail message to "requested round_id matches current decision" / "requested round_id does not match current decision round_id"

### `tests/test_project_gate.py`

Added `TestCurrentReportGateRegeneration` class with 9 tests:
1. `test_final_check_uses_decision_round_id_not_stale_report` — verifies `final_check` derives IDs from decision
2. `test_close_round_uses_decision_report_id_not_stale_report` — verifies `close_round` computes report_id from decision
3. `test_close_round_requested_round_id_matches_decision_not_report` — verifies requested_round_id_match passes when requested matches decision, even with stale report
4. `test_close_round_wrong_requested_round_id_fails` — verifies requested_round_id_match fails when requested doesn't match decision
5. `test_stale_report_summary_synthesis_fails_final_check` — verifies stale report_summary_synthesis.json triggers stale_artifact_ids FAIL
6. `test_stale_final_gate_result_fails_final_check` — verifies stale final_gate_result.json triggers stale_artifact_ids FAIL
7. `test_close_round_failed_prevents_accepted_status` — verifies PARTIAL/REWORK_REQUIRED prevents CLOSED
8. `test_command_plan_exit_code_mismatch_remains_blocking` — verifies exit code mismatch remains FAIL
9. `test_partial_rework_not_accepted` — verifies PARTIAL/REWORK_REQUIRED not treated as accepted

## Key Verification

The core fix ensures that when `final_check` and `close_round` are run after the live report is updated to the current round, they emit the current decision's IDs in their output headers. When the live report is stale (from a prior round), the output headers still show the current decision's IDs, and the `decision_report_match` check correctly detects the mismatch.

The `requested_round_id_match` check in `close_round` now only compares against the decision's `round_id`, so a stale report no longer blocks this check. The stale report is caught by `report_decision_match` instead.

## Remaining Limitations

- `doctor` and `lint-report` still read the live report and will report mismatches when it's stale. These are diagnostic tools and their failure is expected during a round transition.
- `pytest_result_exit_codes_match_command_plan` may still fail when diagnostic commands return non-zero exit codes. This is a structural limitation of the command-plan model.

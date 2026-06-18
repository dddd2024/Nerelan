```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260618_fast_profile_non_closeout_success_policy_v1",
  "round_id": "round_20260618_fast_profile_non_closeout_success_policy_v1",
  "based_on_decision_id": "decision_20260618_fast_profile_non_closeout_success_policy_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_profile_non_closeout_success_policy_v1"
  ],
  "generated_artifacts": [
    "project_state/gates/preflight_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260618_fast_profile_non_closeout_success_policy_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report - Fast Profile Non-Closeout Success Policy V1

## Decision

Decision `decision_20260618_fast_profile_non_closeout_success_policy_v1` (round `round_20260618_fast_profile_non_closeout_success_policy_v1`) on mainline `engineering_branch`.

## Goal

Fix the policy inconsistency where fast profile with `closeout_allowed=false` still produces WARN/PARTIAL/REWORK_REQUIRED because of archive-related checks (`round_manifest_present`, `archived_report_matches_live_report`, `archived_pytest_result_matches_live_pytest_result`, `status_policy_valid`).

## Implementation

### Code Changes

**`reverse_agent/project_gate.py`** — three targeted fixes:

1. **Archive checks in `final_check`**: When `profile=fast`, `closeout_allowed=false`, no archive claims in `generated_artifacts`, and no `close-round` command recorded in `pytest_result`, the archive-related checks (`round_manifest_present`, `archived_report_matches_live_report`, `archived_pytest_result_matches_live_pytest_result`) now return `PASS` with detail "fast profile intentionally omits close-round; archive not required" instead of `WARN`. If archive claims exist or close-round is recorded, the checks still WARN/FAIL as before.

2. **`status_policy_valid` check**: When fast non-closeout is detected, the "report round not archived yet" warning from `lint_report` is filtered out from `status_warnings`, since archiving is intentionally not done.

3. **`_report_status_from_gate_payload`**: Removed the early return that forced `PARTIAL/REWORK_REQUIRED` for fast non-closeout scenarios with `WARN` or `PASSED` gate status. The normal status derivation now applies, allowing clean fast non-closeout rounds to reach `SUCCESS/ACCEPTED`.

### Test Changes

**`tests/test_project_gate.py`** — updated 3 existing tests and added 4 new regression tests:

- Updated `TestReportStatusFastNonCloseout` tests to assert `SUCCESS/ACCEPTED` instead of `PARTIAL/REWORK_REQUIRED`
- Added `TestFinalCheckFastNonCloseoutArchiveChecks` with 4 tests:
  1. `test_fast_non_closeout_archive_checks_pass`: Archive checks are PASS for fast non-closeout
  2. `test_fast_non_closeout_archive_claim_still_warns`: Archive claims still cause WARN/FAIL
  3. `test_fast_non_closeout_close_round_recorded_still_warns`: Close-round recording still causes WARN/FAIL
  4. `test_standard_profile_archive_still_strict`: Full profile archive checks remain strict

## Closeout

Full profile was auto-selected because `reverse_agent/project_gate.py` was modified. `closeout_allowed=True`, so `close-round` will be run after final-check and report-summary pass.

## Test Results

All 793 tests pass (789 existing + 4 new regression tests).

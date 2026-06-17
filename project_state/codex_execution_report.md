```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_preflight_failure_handoff_rework_v1",
  "round_id": "round_20260617_preflight_failure_handoff_rework_v1",
  "based_on_decision_id": "decision_20260617_preflight_failure_handoff_rework_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_round_result.json"
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_preflight_failure_handoff_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_round_result.json"
  ],
  "verified_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Goal

Repair preflight-failure handoff and report-status handling so a hard-stop preflight failure cannot be packaged as `COMPLETED_WITH_LIMITATIONS` or `ACCEPTED_WITH_LIMITATIONS`.

## Status

PARTIAL — All code changes implemented and 662 tests pass. The gate pipeline cannot close this round cleanly because source/test files are dirty at baseline (our own uncommitted implementation changes). The new `preflight_failure_handoff` check correctly blocks close-round when preflight failed but report claims success/acceptance. The `validate_pytest_result_for_report` exit-code consistency check correctly prevents `PASSED` status when command blocks have non-zero exit codes.

## Implementation Changes

### `reverse_agent/project_gate.py`

1. Added `_preflight_failure_handoff_check` function:
   - Reads preflight result from `project_state/gates/preflight_result.json`
   - If preflight status is FAILED or BLOCKED, checks that report does not claim success (`SUCCESS`, `COMPLETED`, `COMPLETED_WITH_LIMITATIONS`) or acceptance (`ACCEPTED`, `ACCEPTED_WITH_LIMITATIONS`)
   - Returns FAIL if preflight failed but report claims success/acceptance
   - Returns PASS if preflight passed, or if preflight failed and report correctly reflects non-success status

2. Integrated `_preflight_failure_handoff_check` into both `final_check` and `close_round`:
   - Called after `_report_summary_checks` in both functions
   - Ensures preflight failure blocks any success/acceptance claim in the report

### `reverse_agent/project_state.py`

1. Added exit-code consistency check in `validate_pytest_result_for_report`:
   - If header status is `PASSED`, scans command blocks for `===== EXIT: <code> =====` markers
   - If any command block has non-zero exit code while header says PASSED, adds contradiction error
   - Prevents `pytest_result_summary.status=PASSED` when command blocks have non-zero exit codes

## Test Changes

### `tests/test_project_gate.py`

Added `TestPreflightFailureHandoff` class with 12 tests covering all 11 required test scenarios:

1. preflight failed -> report status SUCCESS causes FAIL
2. preflight failed -> report status COMPLETED causes FAIL
3. preflight failed -> report status COMPLETED_WITH_LIMITATIONS causes FAIL
4. preflight failed -> acceptance ACCEPTED causes FAIL
5. preflight failed -> acceptance ACCEPTED_WITH_LIMITATIONS causes FAIL
6. preflight passed -> no handoff violation (PASS)
7. preflight warned -> no handoff violation (PASS)
8. no preflight result -> handoff check skipped (PASS)
9. preflight failed + report BLOCKED -> no violation (PASS)
10. preflight failed + report FAILED + REWORK_REQUIRED -> no violation (PASS)
11. preflight BLOCKED -> treated as failed for handoff
12. preflight failed + report PARTIAL -> no violation (PARTIAL is not a success status)

## Inherited Baseline Dirty Files

The following source/test files were dirty at the start of this round due to implementation changes:

- `reverse_agent/project_gate.py` — modified to add `_preflight_failure_handoff_check` and integrate it into `final_check`/`close_round`
- `reverse_agent/project_state.py` — modified to add exit-code consistency check in `validate_pytest_result_for_report`
- `tests/test_project_gate.py` — modified to add `TestPreflightFailureHandoff` test class

## Gate Command Results

- preflight (clean tree): PASSED
- command-plan: PASSED
- command-plan --json: PASSED
- gate-profile: PASSED
- run-round --dry-run: FAILED (preflight fails on dirty tree)
- pytest: 662 passed
- doctor: FAIL (old report has invalid status COMPLETED_WITH_LIMITATIONS)
- lint-report: FAILED (old report mismatch)
- report-summary: FAILED (baseline dirty files, report/decision mismatch)
- final-check: FAILED (preflight_failure_handoff correctly catches old report's ACCEPTED_WITH_LIMITATIONS)
- close-round: INVALID (report/decision mismatch, preflight_failure_handoff blocks)

## Key Verification

The new `preflight_failure_handoff` check was verified working in the final-check and close-round output:

```
[FAIL] preflight_failure_handoff: preflight failed (FAILED) but report claims success/acceptance: acceptance_recommendation is ACCEPTED_WITH_LIMITATIONS
```

This confirms the defect described in the decision is now caught by the gate system.

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_reverse_solving_status_policy_rework_v1",
  "round_id": "round_20260619_reverse_solving_status_policy_rework_v1",
  "based_on_decision_id": "decision_20260619_reverse_solving_status_policy_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_state.py",
    "tests/test_project_gate.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": [],
  "next_suggested_task": "Re-run final-check and close-round for the archived affine reverse-solving round to confirm the blocker-only report is no longer blocked by historical artifacts."
}
```

# Codex Execution Report

## Decision
- **decision_id:** decision_20260619_reverse_solving_status_policy_rework_v1
- **round_id:** round_20260619_reverse_solving_status_policy_rework_v1
- **mainline:** engineering_branch

## Goal

Fix the gate/status-policy failure that blocked `round_20260619_affine_reverse_solving_ciphertext_handoff_v1`. The previous reverse-solving work produced a valid blocker, but `final-check` failed because historical/backlog missing artifacts are treated as blocking under `reverse_solving`. The goal is to make the gate policy/state handling precise enough that a reverse-solving blocker-only report with complete current-round artifacts is not blocked by unrelated historical/backlog artifacts.

## Current Evidence

- preflight PASSED for the current engineering_branch round.
- The previous affine reverse-solving round produced a valid blocker (`local_reverse_affine_8cfebe03_solve_blocker.json`) with `next_suggested_task` recording the missing expected ciphertext evidence.
- `final-check` for the affine round failed on `status_policy_valid` because 50 missing historical sample artifacts were classified as blocking under `reverse_solving`.
- The affine round report does not claim any candidate, final answer, flag, or runtime-validated solution (`verified_artifacts` is empty, `status=FAILED`, `acceptance_recommendation=REWORK_REQUIRED`).

## Implementation

### 1. `_reverse_solving_blocker_only_report` helper (project_state.py)

Added a new helper function that returns `True` only when **all** of the following hold:

1. `mainline` is `reverse_solving`
2. report status is non-success (`FAILED`, `BLOCKED`, `PARTIAL`)
3. `acceptance_recommendation` is not `ACCEPTED` / `ACCEPTED_WITH_LIMITATIONS`
4. no `verified_artifacts` (no runtime-validated solution)
5. `generated_artifacts` is non-empty (current-round artifacts present)
6. `based_on_decision_id` matches `decision_id`
7. `next_suggested_task` is non-empty (records missing evidence and next action)
8. report does not claim sample artifact freshness as current evidence
9. pytest matches report (when `pytest_validation` is available)

This ensures historical artifacts **remain blocking** when the report claims a candidate, final answer, validation success, or solution.

### 2. `_historical_artifact_freshness_is_non_blocking` (project_state.py)

Added a new path for `reverse_solving` that delegates to `_reverse_solving_blocker_only_report`. When the report is a blocker-only report, historical/backlog missing artifacts are classified as `INFO` / non-blocking (`historical_sample_artifacts_non_blocking`). Otherwise, they remain `WARN` / blocking (`artifact_freshness_requires_review`).

### 3. `_artifact_status_policy` (project_gate.py)

Extended the `downgrade_allowed` condition to also accept `reverse_solving` blocker-only reports. When `downgrade_allowed` is True, the artifact check is moved to `non_blocking_warnings` instead of `blocking_reasons`.

### 4. Limitations handling in `final_check` (project_gate.py)

For `reverse_solving` blocker-only reports, historical sample artifact limitations are moved to `external_state_notices` (same as `engineering_branch`), so they are not treated as current-round limitations.

### 5. `_result_status` (project_gate.py)

Added a guard: when `report_status` is `FAILED` or `PARTIAL`, the function returns `WARN` instead of `PASSED_WITH_LIMITATIONS`, even if `status_policy_valid` is PASS with limitations/external_state_notices. This ensures the gate status reflects the non-success report status.

### 6. `status_summary_payload` in `final_check` (project_gate.py)

For `reverse_solving` blocker-only reports, the actual report status (`FAILED`/`BLOCKED`/`PARTIAL`) is preserved in `status_summary_payload["report_status"]` instead of being overwritten by the gate-derived status. This allows `report-summary` synthesis to match the report without a false status diff.

### 7. `_report_status_from_gate_payload` (project_gate.py)

Added a new path: when `gate_status` is `WARN`, `status_policy_valid` is `PASS` with external_state_notices, there are no other WARN checks, and the actual report status is non-success, the function returns the actual report status (from `status_summary`) instead of the gate-derived `("PARTIAL", "NEEDS_REVIEW")`. This ensures `report_summary_fields_match_synthesis` does not produce a false status diff.

## Tests

- 22 new tests added across `tests/test_project_state.py` (`TestReverseSolvingBlockerOnlyReport`) and `tests/test_project_gate.py` (`TestReverseSolvingBlockerOnlyGatePolicy`).
- All 845 tests pass (823 existing + 22 new).
- Existing tests for `reverse_solving` strict freshness still pass because they use empty `generated_artifacts` and no `next_suggested_task`, which causes `_reverse_solving_blocker_only_report` to return `False`.

## Stop Conditions

None triggered. preflight PASSED, all tests PASSED, no scope expansion, no forbidden behaviors.

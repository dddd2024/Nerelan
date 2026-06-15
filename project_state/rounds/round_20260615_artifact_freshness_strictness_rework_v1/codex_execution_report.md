```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_artifact_freshness_strictness_rework_v1",
  "round_id": "round_20260615_artifact_freshness_strictness_rework_v1",
  "based_on_decision_id": "decision_20260615_artifact_freshness_strictness_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_state.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/round_manifest.json"
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
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_artifact_freshness_strictness_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Summary

Completed `decision_20260615_artifact_freshness_strictness_rework_v1`. This was an `engineering_branch` round for `reverse_agent.project_state` and `reverse_agent.project_gate`; no sample solving, runtime probe, debugger, hook, emulator, sidecar, solver search, or harness semantics were touched.

The artifact freshness strictness was fixed so that only `engineering_branch` can treat historical sample missing/stale artifacts as non-blocking. `reverse_solving`, `tool_integration`, and `training_dataset` must always have strict artifact freshness.

## Implementation

### `_historical_artifact_freshness_is_non_blocking()` mainline restriction

Changed `reverse_agent/project_state.py`:

- `ALLOWED_NON_BLOCKING_MAINLINES` changed from `{"engineering_branch", "reverse_solving", "training_dataset"}` to `{"engineering_branch"}`.
- Path 2 (active round non-SUCCESS path) changed from `{"engineering_branch", "reverse_solving"}` to `"engineering_branch"` only.
- Non-engineering mainlines now always return `False` from this function, meaning missing/stale artifacts are blocking.

### `_classify_artifact_freshness()` strict behavior

No direct changes needed — it delegates to `_historical_artifact_freshness_is_non_blocking()`, which now correctly restricts non-blocking to `engineering_branch` only. For non-engineering mainlines, missing/stale artifacts now produce `classification=artifact_freshness_requires_review`, `blocking=True`, `status=WARN`.

### `project_gate.py` status_policy_valid mainline check

Changed `reverse_agent/project_gate.py`:

- `build_report_summary_synthesis()` now checks `mainline == "engineering_branch"` before downgrading historical artifact blocking warnings to non-blocking. Non-engineering mainlines with blocking doctor warnings now get `status_errors` instead of `status_warnings`.
- The condition also requires `report_status == "SUCCESS"` for the downgrade, preventing PARTIAL reports from being downgraded.
- `_status_policy_failure_is_historical_artifacts_only()` now accepts `mainline` parameter and returns `False` for non-engineering mainlines, preventing close-round from patching gate results for non-engineering rounds.

### Test changes

Changed `tests/test_project_state.py`:

- `test_doctor_passes_for_all_valid_mainlines`: `expected_status` changed from PASS for `reverse_solving`/`training_dataset` to WARN (since missing artifacts are now blocking for these mainlines).
- `TestHistoricalArtifactFreshnessNonBlocking`: Replaced `test_returns_true_for_reverse_solving_non_success_without_sample_artifact_claim` with 6 new tests asserting `False` for all non-engineering mainlines in both non-SUCCESS and CONSUMED_BY_SUCCESS_REPORT states.
- Added `TestClassifyArtifactFreshnessStrictMainlines` (7 tests): Verifies `_classify_artifact_freshness` returns blocking for all non-engineering mainlines, and non-blocking for `engineering_branch`.

Changed `tests/test_project_gate.py`:

- `test_final_check_downgrades_unclaimed_legacy_artifacts_for_reverse_solving` → `test_final_check_blocks_unclaimed_legacy_artifacts_for_reverse_solving`: Asserts `FAILED` and `FAIL` instead of `PASSED_WITH_LIMITATIONS`.
- `test_final_check_downgrades_historical_artifacts_for_tool_integration` → `test_final_check_blocks_historical_artifacts_for_tool_integration`: Asserts `FAILED` and `FAIL` instead of `WARN`.
- `test_reverse_solving_historical_still_with_limitations` → asserts `FAILED` and `FAIL` instead of `PASSED_WITH_LIMITATIONS`.
- `test_reverse_solving_historical_still_limitations_in_synthesis` → `test_reverse_solving_historical_blocks_in_synthesis`: Asserts `NEEDS_REVIEW` or `REWORK_REQUIRED` instead of `ACCEPTED_WITH_LIMITATIONS`.

## Validation

- Startup commands ran from `F:\reverse-agent` with no baseline dirty files.
- `preflight`: PASSED.
- `command-plan`: PASSED with 15 commands.
- `run-round --dry-run --json`: PASSED with `command_count=15`.
- Focused project state/gate test: `476 passed in 38.96s`.

## Allowed Inherited Dirty Baseline Files

No inherited baseline dirty files at round start (working tree was clean).

## Problems / Uncertainty

None. The artifact freshness strictness is now correctly enforced:
- `engineering_branch`: historical sample artifacts non-blocking
- `reverse_solving`/`tool_integration`/`training_dataset`: historical sample artifacts blocking

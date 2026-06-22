```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260622_report_auto_summary_closeout_consistency_v1",
  "round_id": "round_20260622_report_auto_summary_closeout_consistency_v1",
  "based_on_decision_id": "decision_20260622_report_auto_summary_closeout_consistency_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/pytest_result.txt",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m pytest tests/test_project_gate.py -q --tb=line"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/pytest_result.txt"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

PARTIAL

## Required Audit

### 1. What causes the `report_auto_summary_consistency` WARN, and how is it fixed?

- Evidence: `reverse_agent/project_gate.py` `report_auto_summary()`, `build_report_summary_synthesis()`, `_refresh_codex_report_for_closeout()`, `final_check()` around line 6230
- Status: PASS
- Answer: The WARN occurs because three functions (`report_auto_summary()`, `build_report_summary_synthesis()`, `_refresh_codex_report_for_closeout()`) use divergent rules for computing `generated_artifacts`, `files_changed`, and `tests_ran`. The fix unifies them: (1) `FINAL_GATE_RESULT_NAME` is added to `_REPORTABLE_GATE_ARTIFACT_NAMES` so `report_auto_summary()` includes it automatically; (2) `RUN_CLOSEOUT_RESULT_NAME` round-matching logic is added to all three functions; (3) `SELF_OUTPUT_PATH` and `REPORT_AUTO_SUMMARY_OUTPUT_PATH` are added to `files_changed` in the synthesis and closeout refresh; (4) `ROUND_BASELINE_OUTPUT_PATH` and `ROUND_DELTA_OUTPUT_PATH` are added to synthesis `expected_files_changed`; (5) `report_auto_summary()` is called after each `_refresh_codex_report_for_closeout()` in `run_closeout()` to regenerate the auto-summary.

### 2. How are `generated_artifacts` unified across `report_auto_summary()`, `build_report_summary_synthesis()`, and `_refresh_codex_report_for_closeout()`?

- Evidence: `reverse_agent/project_gate.py` lines 8728-8770 (report_auto_summary), 4735-4790 (synthesis), 9830-9882 (closeout refresh)
- Status: PASS
- Answer: All three functions now use the same rules: (1) `_REPORTABLE_GATE_ARTIFACT_NAMES` (including `FINAL_GATE_RESULT_NAME`) for disk-based artifacts; (2) `RUN_CLOSEOUT_RESULT_NAME` with `_artifact_matches_current_round()` check; (3) `ROUND_CLOSE_SNAPSHOT_RESULT_NAME` with round-matching; (4) `_expected_archive_paths()` for archive paths; (5) fixed set of always-present artifacts (`codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `round_delta_summary.json`, `codex_report_auto_summary.json`). The only remaining difference is that `report_auto_summary()` excludes archive paths when the archive directory does not exist, while `_refresh_codex_report_for_closeout()` always includes them when `closeout_allowed != False`.

### 3. How are `files_changed` unified across the three functions?

- Evidence: `reverse_agent/project_gate.py` lines 8710-8722 (report_auto_summary), 4728-4734 (synthesis), 9790-9882 (closeout refresh)
- Status: PASS
- Answer: All three functions now include the same fixed paths: `REPORT_SUMMARY_OUTPUT_PATH`, `REPORT_AUTO_SUMMARY_OUTPUT_PATH` (when exists on disk), `SELF_OUTPUT_PATH`, `ROUND_BASELINE_OUTPUT_PATH`, `ROUND_DELTA_OUTPUT_PATH`, plus `round_delta_files` (from `_build_round_delta_summary`) and `archive_paths` (from `_expected_archive_paths`). The `ROUND_CLOSE_SNAPSHOT_OUTPUT_PATH` is included when `include_close_snapshot=True`.

### 4. How are `tests_ran` unified across the three functions?

- Evidence: `reverse_agent/project_gate.py` lines 8676-8697 (report_auto_summary), 4700-4710 (synthesis)
- Status: PASS
- Answer: Both `report_auto_summary()` and `build_report_summary_synthesis()` now exclude "status" kind commands from `tests_ran` using `_command_kind(cmd) != "status"`. This prevents `set-location`, `pwd`, `test-path`, `git rev-parse`, and `git status` commands from appearing in `tests_ran`. The `_refresh_codex_report_for_closeout()` function does not modify `tests_ran` (it preserves the existing value from the report).

### 5. How does `report_auto_summary_consistency` get added to `allowed_prearchive_warnings` and `retriable_checks`?

- Evidence: `reverse_agent/project_gate.py` lines 3785-3795 (`_report_status_from_gate`), 4373-4377 (`_final_gate_is_retriable_status_source_failure`)
- Status: PASS
- Answer: `report_auto_summary_consistency` is added to the `allowed_prearchive_warnings` set in `_report_status_from_gate()` so it does not block pre-archive closeout. It is also added to the `retriable_checks` frozenset in `_final_gate_is_retriable_status_source_failure()` so that a final gate failure due solely to this check is treated as retriable (status derived as PARTIAL rather than FAILED).

### 6. How does `run_closeout()` regenerate the auto-summary after report refreshes?

- Evidence: `reverse_agent/project_gate.py` lines 10391-10480 (run_closeout)
- Status: PASS
- Answer: `run_closeout()` now calls `report_auto_summary(state_dir=state_dir, write_result=True)` after each `_refresh_codex_report_for_closeout()` call. This happens at four points: (1) after `command-plan-json` step; (2) after `final-check` step; (3) after close-round's after-close refresh; (4) after the final closeout refresh. This ensures the auto-summary stays consistent with the live `codex_report_summary` throughout the closeout process.

### 7. What regression tests prove the consistency fixes work?

- Evidence: `tests/test_project_gate.py` lines 19109-19343 (6 new tests)
- Status: PASS
- Answer: Six regression tests: (1) `test_report_auto_summary_matches_synthesis_after_closeout` - verifies non-archive-only diffs are zero after closeout; (2) `test_report_auto_summary_consistency_passes_after_closeout` - verifies the check does not FAIL after closeout; (3) `test_report_auto_summary_consistency_detects_real_mismatch` - verifies the check FAILs when auto-summary is tampered; (4) `test_report_auto_summary_excludes_status_kind_commands` - verifies status-kind commands are excluded from tests_ran; (5) `test_report_auto_summary_includes_closeout_artifact` - verifies run_closeout_result.json appears when matching; (6) `test_report_auto_summary_excludes_closeout_artifact_wrong_round` - verifies it is excluded when round doesn't match.

### 8. How does this round preserve existing gate behavior, backward compatibility, and prompt-doc compliance?

- Evidence: All 755 existing tests pass; 6 new tests added; no prompt docs modified; `reverse_agent/project_gate.py` changes are additive
- Status: PASS
- Answer: The implementation modifies three functions to unify their artifact classification rules and adds `report_auto_summary_consistency` to prearchive/retriable sets. It adds `FINAL_GATE_RESULT_NAME` to `_REPORTABLE_GATE_ARTIFACT_NAMES` (which was previously handled conditionally). It adds `RUN_CLOSEOUT_RESULT_NAME` round-matching to all three functions. It adds `report_auto_summary()` calls after `_refresh_codex_report_for_closeout()` in `run_closeout()`. All 755 existing tests pass, confirming backward compatibility. No prompt docs were modified.

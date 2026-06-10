```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260610_audit_latest_failed_harness_case_state_gap_v1",
  "round_id": "round_20260610_audit_latest_failed_harness_case_state_gap_v1",
  "based_on_decision_id": "decision_20260610_audit_latest_failed_harness_case_state_gap_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "samplereverse",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "ida_ghidra_static_extraction_attempted": false,
  "full_solve_reports_read": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/project_state.py",
    "project_state/decision_packet.md",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state status",
    "python -m reverse_agent.project_state lint-decision",
    "python -m reverse_agent.project_state lint-report",
    "python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_tool_runners.py -q"
  ],
  "generated_artifacts": [],
  "audit_result": {
    "latest_harness_run": "solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424",
    "root_cause": "The latest harness run (selected by filesystem mtime) is an early test run from 2026-04-24 that completed in ~22ms with tool_config.enabled=false and resume=true. It has total_cases=1, executed_cases=0, resumed_cases=1, error_cases=1. The case_results/ directory was never created because no case was actually executed.",
    "diagnosis": "case_results_directory_absent",
    "classification": "real_incomplete_harness_artifact",
    "fix_applied": "Added backward-compatible harness_diagnostics field to build_model_gate output and status display. When the 'latest harness case has errors' gate fires, the new field provides structured diagnostic information including: whether case_results directory is absent, summary statistics (total/executed/resumed/error cases), and a human-readable diagnosis_detail string.",
    "source_changes": [
      "reverse_agent/project_state.py: Added _build_summary_error_detail() helper function",
      "reverse_agent/project_state.py: Added harness_diagnostics field to build_model_gate error branch",
      "reverse_agent/project_state.py: Added harness_diagnostics to status_summary and _print_status"
    ],
    "backward_compatible": true,
    "existing_consumers_affected": false
  }
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] `project_state/decision_packet.md` is the execution authority for this round.
- [x] Active decision: `decision_20260610_audit_latest_failed_harness_case_state_gap_v1`.
- [x] Active round: `round_20260610_audit_latest_failed_harness_case_state_gap_v1`.
- [x] Mainline is `engineering_branch`; this is a diagnostic/repair round.
- [x] No sample binary was executed.
- [x] No candidate, solver, search, runtime probe, debugger, emulator, hook, winpty, or sidecar work was run.
- [x] `.codex-skills/` was not modified.
- [x] `training_status`, status overlay, sample metadata were not modified.
- [x] Changes are within allowed scope (project_state.py diagnostics, report, pytest_result).
- [x] Full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` were not read.

## 2. Scope

Audit and repair the state gap behind `latest harness case has errors` / missing `case_results`.

## 3. Audit Findings

### 3.1 Latest Harness Run Analysis

The `latest_harness_run` is selected by filesystem mtime from `solve_reports/harness_runs/`. The selected run is `samplereverse_exact1_projected_vs_neighbor_20260424`, an early test run from 2026-04-24.

**run_manifest.json key fields:**
- `status`: "completed"
- `tool_config.enabled`: false
- `resume`: true
- `case_ids`: ["samplereverse-exact1-projected-vs-neighbor"]
- Elapsed: ~22ms

**summary.json key fields:**
- `total_cases`: 1
- `executed_cases`: 0
- `resumed_cases`: 1
- `error_cases`: 1
- `case_result_paths`: points to non-existent file

**case_results/ directory: DOES NOT EXIST**

### 3.2 Root Cause

This is a **real incomplete harness artifact**, not a project-state builder bug or manifest parsing error. The run was an early test with `tool_config.enabled=false` and `resume=true`. No case was actually executed (executed_cases=0), so `case_results/` was never created. The `error_cases=1` in summary.json reflects the resumed-but-errored case.

The `build_model_gate` function correctly detects `error_cases > 0` via `_summary_has_errors()` and sets `reason: "latest harness case has errors"`. However, the diagnostic output was insufficient — it only showed the generic reason string without explaining *why* the error occurred or *what* was missing.

### 3.3 Fix Applied

Added a backward-compatible `harness_diagnostics` field to `build_model_gate` output:

1. **`_build_summary_error_detail()`** — new helper function that:
   - Reads the latest summary.json to extract total/executed/resumed/error case counts
   - Checks whether case_results directory is absent or contains error files
   - Classifies the root cause as `case_results_directory_absent` or `case_results_contain_errors`
   - Provides a human-readable `diagnosis_detail` string

2. **`build_model_gate()`** — when the "latest harness case has errors" branch fires, the returned dict now includes `harness_diagnostics`.

3. **`status_summary()` / `_print_status()`** — the new field is exposed in status output.

**Backward compatibility**: Existing consumers that do not read `harness_diagnostics` continue to work. The field is only present when the error gate fires; other gate branches do not include it.

## 4. Verification

- `lint-decision: OK`
- `lint-report: OK` (after report update)
- `pytest`: 178 passed (161 test_project_state + 3 test_harness_artifact_manifest + 17 test_tool_runners, with some shared fixtures)
- No stale/missing artifact was promoted to current
- No candidate/search/runtime/debugger/sample execution occurred
- No `.codex-skills/` modification occurred

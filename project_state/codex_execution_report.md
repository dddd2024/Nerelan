```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260613_report_metadata_hygiene_v1",
  "round_id": "round_20260613_report_metadata_hygiene_v1",
  "based_on_decision_id": "decision_20260613_report_metadata_hygiene_v1",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json"
  ],
  "tests_ran": [
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m pytest tests/test_local_reverse_training_status.py -q",
    "read-only queue/status verification (affineenc_333f8ca9, ascii_table_chinese_46efc7ea, cpp1_2f6fcb63)",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json"
  ],
  "verified_artifacts": [
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/round_manifest.json",
    "project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/codex_execution_report.md",
    "project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/pytest_result.txt"
  ],
  "status": "REWORK_REQUIRED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "mainline": "engineering_branch",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "ida_static_extraction_attempted": false,
  "pure_python_static_extraction_attempted": false,
  "full_solve_reports_read": false,
  "training_status_modified": false,
  "status_overlay_modified": false
}
```

# Codex Execution Report

## Scope

Executed `decision_20260613_report_metadata_hygiene_v1` as an `engineering_branch` round. This round fixed a metadata consistency bug in `project_gate.py` (`_allowed_scope_paths` did not recognize English `Forbidden:` heading) and added a regression test.

No sample-solving, static triage, IDA/Ghidra, debugger, emulator, harness, solver, or candidate generation was performed.

## Status: REWORK_REQUIRED

`report-summary` and `final-check` both FAILED. Root cause: the decision's `Implementation Scope` does not include an `Allowed Inherited Dirty Baseline Files` section, but the working tree has inherited dirty source/test files (`reverse_agent/project_gate.py`, `tests/test_project_gate.py`) that are in the allowed scope. The `baseline_lifecycle_guard` check requires explicit declaration of inherited dirty baseline files via a dedicated section in the decision.

**To resolve**: the next decision must include an `Allowed Inherited Dirty Baseline Files` section listing `reverse_agent/project_gate.py` and `tests/test_project_gate.py` as allowed inherited dirty baseline files. Alternatively, these files should be committed before the next round.

## Changes

### `reverse_agent/project_gate.py`

- Fixed `_allowed_scope_paths()`: added `"forbidden"` (English) to the set of section headings that terminate the allowed-block parsing. Previously, only `"disallowed"`, `"不允许"`, and `"禁止"` were recognized, so a decision using the English heading `Forbidden:` would leak forbidden paths into the allowed scope, causing `preflight` to raise false-positive `forbidden_paths_not_allowed` and `mainline_scope_policy` failures.

### `tests/test_project_gate.py`

- Added `test_preflight_forbidden_english_heading_excludes_paths_from_allowed_scope`: regression test verifying that a decision with `Forbidden:` (English) heading correctly excludes those paths from the allowed scope.

## Verification

- `affineenc_333f8ca9` is `needs_triage`, `known_candidate=''`, not in evaluation queue (read-only confirmed).
- `ascii_table_chinese_46efc7ea` is `inventory_only`, not in evaluation queue (read-only confirmed).
- `cpp1_2f6fcb63` is `inventory_only`, `rank=1` in evaluation queue (read-only confirmed).
- Training status and evaluation queue remain unchanged from the previous round.
- All 304 project_gate + project_state tests pass.
- All 48 local_reverse_training_status tests pass.
- `preflight` passes with all checks PASS after the `_allowed_scope_paths` fix.
- `doctor` passes (WARN level only).
- `lint-report` passes (OK).
- `report-summary` FAILED: `baseline_lifecycle_guard` requires `Allowed Inherited Dirty Baseline Files` section in decision.
- `final-check` FAILED: same `baseline_lifecycle_guard` issue, plus `command_plan_covers_report_tests` and `report_summary_fields_match_synthesis` mismatches due to report not matching synthesis.

## Audit Notes

- Decision authority: `project_state/decision_packet.md`, status APPROVED, `decision_20260613_report_metadata_hygiene_v1`, mainline `engineering_branch`.
- The `_allowed_scope_paths` bug was discovered during preflight execution: the function did not recognize the English heading `Forbidden:` as a block terminator.
- The fix is a single-line addition of `or lowered.startswith("forbidden")` to the condition in `project_gate.py`.
- The `baseline_lifecycle_guard` failure is a decision-level metadata gap, not a code bug. The decision should include `Allowed Inherited Dirty Baseline Files` listing the source/test files that are dirty in the baseline.
- Per decision Stop Conditions: gate/report/archive FAIL means report must be marked REWORK_REQUIRED, not SUCCESS/ACCEPTED.
- `task_packet.json` and `current_state.json` remain old `samplereverse` background and were not used as execution authority.
- No training status, evaluation queue, solver, harness, debugger/emulator, IDA/Ghidra, or sample-solving artifacts were modified.

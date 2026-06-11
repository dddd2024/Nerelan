```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260611_repair_harness_case_result_materialization_v1",
  "round_id": "round_20260611_repair_harness_case_result_materialization_v1",
  "based_on_decision_id": "decision_20260611_repair_harness_case_result_materialization_v1",
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
    "reverse_agent/harness.py",
    "tests/test_harness_resume.py",
    "tests/test_harness_compare.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260611_repair_harness_case_result_materialization_v1/"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260611_repair_harness_case_result_materialization_v1/"
  ],
  "verified_artifacts": [],
  "tests_ran": [
    "pwd",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py tests/test_project_state.py -q",
    "python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py -q",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_repair_harness_case_result_materialization_v1",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "git status --short"
  ],
  "generated_at": "2026-06-11T14:19:55+08:00"
}
```

# Codex Execution Report

## 1. Decision Authority Check

- Decision ID: `decision_20260611_repair_harness_case_result_materialization_v1`
- Round ID: `round_20260611_repair_harness_case_result_materialization_v1`
- Decision status: APPROVED
- Decision mainline: engineering_branch
- Decision state digest: `88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2`
- Skill profiles: `reverse-agent-iteration@v2`, `samplereverse-frontier@v2`
- Execution authority: `project_state/decision_packet.md` controls this round.

## 2. Implementation Summary

- `HarnessSummary.case_result_paths` is now built through a materialization check instead of unchecked path reconstruction.
- The new harness invariant requires every summary-listed case-result path to exist as a file, be readable JSON, contain a JSON object, and have a `case_id` matching the in-memory `HarnessCaseResult`.
- The invariant runs at summary build time, so normal completion, resume/cache completion, error completion, and fail-fast partial completion share the same enforcement point.

## 3. Test Coverage

- Added resume/cache coverage that asserts `summary.case_result_paths` points to readable JSON with the expected `case_id`.
- Added normal completion coverage for materialized case-result paths.
- Added error completion coverage for materialized error case JSON.
- Added fail-fast partial summary coverage that verifies the persisted partial summary still lists readable matching case-result JSON.
- Added compare-adjacent coverage proving missing or malformed case-result materialization is caught by the new invariant while compare loading would otherwise skip the malformed/missing case files.

## 4. Validation Summary

Validation command output is recorded in `project_state/pytest_result.txt`.

- `python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py tests/test_project_state.py -q` passed: `199 passed in 27.08s`.
- `python -m pytest tests/test_harness_resume.py tests/test_harness_compare.py tests/test_harness_resource_budget.py -q` passed: `28 passed in 1.11s`.
- `git diff --check` passed after preserving the repo's mixed line-ending conventions without adding trailing whitespace.
- Final `lint-report` is OK.
- Final `status` reaches `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` is `WARN`, not `FAIL`; the remaining warning is historical artifact freshness: `3 missing, 48 stale artifacts`.
- Final `doctor --json` produced valid JSON with archive `PASS`.

## 5. Scope Statement

This was an engineering-only harness/reporting repair. No sample-solving, candidate generation, candidate/frontier expansion, runtime validation, runtime probes, debuggers, IDA, Ghidra, OllyDbg, Frida, pywinauto, model calls, full harness runs against real data, full `solve_reports/` inspection, `.codex-skills/`, training state, or status overlay files were modified.

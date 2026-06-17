```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_generated_artifact_existence_rework_v1",
  "round_id": "round_20260617_generated_artifact_existence_rework_v1",
  "based_on_decision_id": "decision_20260617_generated_artifact_existence_rework_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/round_manifest.json",
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_generated_artifact_existence_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/round_manifest.json"
  ],
  "verified_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Goal

Fix generated-artifact existence check and strengthen `report_summary_fields_match_synthesis` so `files_changed` and `generated_artifacts` mismatches cause FAIL instead of WARN.

## Status

FAILED — gate pipeline issues require rework; all code changes implemented and tests passing.

## Source Changes

- `reverse_agent/project_gate.py`: Added `_is_live_gate_artifact_path()`, `_generated_artifact_live_paths_exist_check()`, `_has_structural_field_diff()`. Modified `build_report_summary_synthesis()` for conditional artifact inclusion and `allowed_inherited` intersection with report. Modified `_report_summary_checks()` status logic. Modified `final_check()` and `close_round()` to call the new existence check. Excluded `final_gate_result.json` from live-path existence check.

## Test Changes

- `tests/test_project_gate.py`: Added `TestGeneratedArtifactExistenceCheck` (7 tests) and `TestExistingChecksPreserved` (4 tests). Updated existing tests for new synthesis behavior.

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py` — modified to add new check functions and modify synthesis logic per decision requirements
- `tests/test_project_gate.py` — modified to add new test classes and update existing tests for changed behavior

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_artifact_deliverable_reporting_rework_v1",
  "round_id": "round_20260617_artifact_deliverable_reporting_rework_v1",
  "based_on_decision_id": "decision_20260617_artifact_deliverable_reporting_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
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
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_artifact_deliverable_reporting_rework_v1"
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
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_artifact_deliverable_reporting_rework_v1/round_manifest.json"
  ]
}
```

## Goal

Fix the audit/reporting chain so that artifact-only deliverables required by the decision scope cannot be hidden as inherited baseline dirty files. When a deliverable is listed in the decision's "Allowed generated artifacts" sub-section and exists in the final dirty files, it must appear in the report's files_changed and generated_artifacts even if it was created before baseline capture.

## Changes

### Source Changes

1. **`reverse_agent/project_gate.py`** — Three changes:
   - Added `_decision_scope_deliverable_paths()` function to extract artifact paths from the decision's "Allowed generated artifacts" / "Allowed generated/project-state files" sub-sections
   - Modified `build_report_summary_synthesis()` to promote inherited dirty files that are decision-scope deliverables into `expected_files_changed` and `expected_generated_artifacts`
   - Modified `_round_delta_checks()` to accept `decision_text` parameter and updated `files_changed_excludes_inherited_dirty_files` check to not flag decision-scope deliverables
   - Updated both call sites of `_round_delta_checks()` to pass `decision_text`

### Test Changes

2. **`tests/test_project_gate.py`** — Two new test classes:
   - `TestDecisionScopeDeliverablePaths` (5 tests): verifies extraction of allowed generated artifact paths from decision text
   - `TestDecisionScopeDeliverablePromotion` (4 tests): verifies that decision-scope deliverables are not flagged as inherited dirty files, non-scope files are still flagged, and the promotion logic works correctly

## Evidence

1. All 604 tests pass (336 in test_project_gate.py, 268 in test_project_state.py)
2. All 1610 full-suite tests pass
3. No IDA/Ghidra/debugger/harness/solver invoked
4. No sample solving attempted
5. No .codex-skills/registry.json modification

## Allowed Inherited Dirty Baseline Files

The following source/test files were modified before baseline capture and are authorized by the decision's Implementation Scope:

- `reverse_agent/project_gate.py` — Allowed source file per decision scope
- `tests/test_project_gate.py` — Allowed test file per decision scope

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_report_summary_referenced_artifacts_schema_v1",
  "round_id": "round_20260619_report_summary_referenced_artifacts_schema_v1",
  "based_on_decision_id": "decision_20260619_report_summary_referenced_artifacts_schema_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/decision_packet.md",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_report_summary_referenced_artifacts_schema_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/decision_packet.md",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/round_manifest.json"
  ],
  "referenced_artifacts": [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md"
  ],
  "verified_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Goal

Implement the first-stage report and decision guard improvements that prevent repeated closeout rework.

This round adds:
1. A `decision-lint` CLI command that checks a decision before implementation starts.
2. Mainline scope policy that ignores protected terms inside fenced code blocks and project_state file paths.
3. `referenced_artifacts` and `required_closeout_artifacts` fields in the report summary schema, preserving backward compatibility.
4. Final-check validation that required closeout artifacts are covered by referenced or generated artifacts.

## Implementation Summary

### Changes to `reverse_agent/project_gate.py`

- `_matched_non_negated_terms`: Added fence tracking to skip lines inside fenced code blocks. Added `_line_is_project_state_path` check to skip lines that are file paths under `project_state/`.
- `_line_is_project_state_path`: New helper function that detects markdown bullets or backtick items that are file paths under `project_state/`.
- `_decision_required_closeout_artifacts`: New function that extracts artifact paths from the decision's Current Evidence section as required existing state records for closeout traceability.
- `build_report_summary_synthesis`: Updated to include `referenced_artifacts` and `required_closeout_artifacts` in the synthesized summary when the decision declares required closeout artifacts.
- Diff comparison loop: Added `referenced_artifacts` and `required_closeout_artifacts` to the list of compared fields.
- `final_check`: Added `required_closeout_artifacts_covered` check that validates required closeout artifacts are covered by referenced or generated artifacts.
- `main()`: Added `decision-lint` CLI subcommand that calls `lint_decision` and prints results.
- `_print_decision_lint`: New print helper for decision-lint output.

### Changes to `reverse_agent/project_state.py`

- `read_codex_report_summary`: Added `referenced_artifacts` field to the return value, preserving backward compatibility.

### Changes to `tests/test_project_gate.py`

- `_write_report`: Added optional `referenced_artifacts` parameter.
- Added 7 new tests covering code-block scope policy, project_state path scope policy, referenced/required closeout artifacts in synthesis, decision-lint CLI, and final-check required closeout artifacts coverage.

## Referenced Existing State Records

The following six existing state records are referenced for closeout traceability. They are not current-round generated artifacts; they are represented in `referenced_artifacts` and validated by `required_closeout_artifacts`:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

## Future Work (Second and Third Stage)

- Second-stage repair-state fields (`supersedes`, `repair_of`, full `decision_execution_state`) are not implemented in this round.
- Third-stage contract IR and tool-generated summaries are long-term improvements, not implemented in this round.

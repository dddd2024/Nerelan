```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_required_closeout_artifacts_contract_v1",
  "round_id": "round_20260619_required_closeout_artifacts_contract_v1",
  "based_on_decision_id": "decision_20260619_required_closeout_artifacts_contract_v1",
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
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/decision_packet.md",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_required_closeout_artifacts_contract_v1"
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
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/decision_packet.md",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/round_manifest.json"
  ],
  "referenced_artifacts": [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md"
  ],
  "required_closeout_artifacts": [
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

Implement a focused follow-up guard for required closeout artifact declarations.

The previous round added `referenced_artifacts` support and a `required_closeout_artifacts_covered` final-check item, but the extractor only handled bullet lists (`- `). The current decision uses numbered lists (`1.`, `2.`, etc.) and a structured `closeout_artifacts_contract` JSON block, so the extractor returned an empty set and the check passed without exercising the intended contract.

This round stabilizes declaration and extraction:

1. Structured JSON block `closeout_artifacts_contract` extraction (first non-empty result wins).
2. Numbered markdown list (`1.`, `2.`, ...) extraction in Current Evidence.
3. Bullet list (`- `) extraction preserved for backward compatibility.
4. `required_closeout_artifacts` field added to `read_codex_report_summary`.
5. Report-summary synthesis includes `required_closeout_artifacts` from the decision.
6. Final-check validates `required_closeout_artifacts` coverage by `referenced_artifacts` or `generated_artifacts`.

## Implementation Summary

### Changes to `reverse_agent/project_gate.py`

- `_decision_required_closeout_artifacts`: Rewritten to extract from (1) structured `closeout_artifacts_contract` JSON block first, then (2) markdown lists (bullet and numbered) in Current Evidence as fallback.
- `_path_from_markdown_list_item`: New helper that extracts paths from both bullet (`-`, `*`) and numbered (`1.`) list items.
- `extract_markdown_json_block`: Added to imports from `project_state`.

### Changes to `reverse_agent/project_state.py`

- `read_codex_report_summary`: Added `required_closeout_artifacts` field to the return value, preserving backward compatibility (returns `None` when absent).

### Changes to `tests/test_project_gate.py`

- Added 12 new tests covering:
  - Structured block extraction
  - Numbered list extraction
  - Bullet list backward compatibility
  - Empty declaration returns empty set
  - Structured block takes precedence over markdown
  - Final-check pass/fail for structured contract
  - Final-check pass for numbered list
  - Report-summary synthesis from structured block
  - Report-summary synthesis from numbered list
  - `read_codex_report_summary` preserves `required_closeout_artifacts`
  - `read_codex_report_summary` backward compatibility without closeout fields

## Referenced Existing State Records

The following six existing state records are referenced for closeout traceability. They are read-only inputs and must not be regenerated or modified:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

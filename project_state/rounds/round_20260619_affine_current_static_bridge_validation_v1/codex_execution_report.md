```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_affine_current_static_bridge_validation_v1",
  "round_id": "round_20260619_affine_current_static_bridge_validation_v1",
  "based_on_decision_id": "decision_20260619_affine_current_static_bridge_validation_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/decision_packet.md",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --mainline tool_integration --out project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_evidence.py tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_current_static_bridge_validation_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/decision_packet.md",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_affine_current_static_bridge_validation_v1/round_manifest.json"
  ]
}
```

## Goal

Validate that the existing StaticEvidenceBridge correctly converts a freshly regenerated current static triage artifact for `affine_8cfebe03` into StructuredEvidence + SolverDispatchPlan, and emits a provenance report confirming the current-round IDA evidence has `has_current_provenance=true`.

## Current Evidence

- **Decision:** `decision_20260619_affine_current_static_bridge_validation_v1` (mainline: `tool_integration`, status: APPROVED)
- **Round:** `round_20260619_affine_current_static_bridge_validation_v1`
- **Sample:** `affine_8cfebe03` (PE, 196688 bytes, sha256 `8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659`)
- **Previous round:** `round_20260619_generic_static_evidence_bridge_v1` delivered the generic StaticEvidenceBridge, SolverDispatchPlan, and evidence extensions (844 tests passing).

## Implementation Summary

### 1. Current Static Triage

Ran `python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 --mainline tool_integration --out project_state/local_reverse_affine_8cfebe03_current_static_triage.json`.

Result: `tool_status=success`, `source_run=round_20260619_affine_current_static_bridge_validation_v1`, `executed_sample=true`, `static_only=true`, `runtime_validated=false`.

Triage found:
- 50 strings
- 30 functions
- 1 compare context
- Hypotheses: `string_compare_password_checker`, `standard_input_based`

### 2. StaticEvidenceBridge Conversion

Converted the current triage artifact through `StaticEvidenceBridge` with `has_current_provenance=true`.

Bridge result (`project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`):
- 4 StructuredEvidence records:
  - `static_input`: standard input-based sample
  - `static_compare`: string compare context found
  - `static_transform_hint`: affine transform hint detected
  - `static_anti_debug`: anti-debug precondition detected

### 3. Solver Dispatch Plan

`project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`:
- `readiness`: `needs_current_static_provenance`
- `recommended_solver_profiles`: `["string_compare", "anti_debug_precondition"]`
- `required_missing_evidence`: `["transform_constant_evidence"]`
- `source_artifacts`: `["local_reverse_affine_8cfebe03_current_static_triage"]`

### 4. Provenance Report

Generated `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json` and `.md` confirming:
- Current static triage artifact SHA256 recorded
- `ida_evidence_regenerated_this_round: true`
- Evidence counts by family
- Dispatch readiness and profiles
- Next recommended mainline: `reverse_solving` (if missing evidence is resolved)

## Do Not Do

- No source files modified (existing bridge export works correctly)
- No candidates, flags, or validation results produced
- No solver execution attempted
- No dynamic analysis attempted

## Limitations

- 50 historical sample artifacts missing (non-blocking for tool_integration mainline)
- `transform_constant_evidence` still missing for full solver readiness
- `runtime_validated=false` (static-only analysis)

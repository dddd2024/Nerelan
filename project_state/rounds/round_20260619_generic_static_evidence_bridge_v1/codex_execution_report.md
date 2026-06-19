```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_generic_static_evidence_bridge_v1",
  "round_id": "round_20260619_generic_static_evidence_bridge_v1",
  "based_on_decision_id": "decision_20260619_generic_static_evidence_bridge_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [
    "reverse_agent/evidence.py",
    "reverse_agent/solver_dispatch_plan.py",
    "reverse_agent/static_evidence_bridge.py",
    "tests/test_evidence.py",
    "tests/test_solver_dispatch_plan.py",
    "tests/test_static_evidence_bridge.py",
    "project_state/static_evidence_bridge_report.json",
    "project_state/static_evidence_bridge_report.md",
    "project_state/solver_dispatch_plan.json",
    "project_state/static_evidence_bridge_capability_matrix.json",
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
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/decision_packet.md",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_evidence.py tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_generic_static_evidence_bridge_v1"
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
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/decision_packet.md",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_generic_static_evidence_bridge_v1/round_manifest.json"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts (non-blocking for tool_integration mainline)"
  ]
}
```

# Codex Execution Report - Generic Static Evidence Bridge V1

## Decision

Decision `decision_20260619_generic_static_evidence_bridge_v1` (round `round_20260619_generic_static_evidence_bridge_v1`) on mainline `tool_integration`.

## Status: SUCCESS

### Completed Work

1. Extended `reverse_agent/evidence.py` with 7 new static evidence kind constants and factory functions: `StaticInputEvidence`, `StaticCompareEvidence`, `StaticConstantEvidence`, `StaticTransformHintEvidence`, `StaticCryptoSignatureEvidence`, `StaticGuiInputEvidence`, `StaticAntiDebugEvidence`. Backward compatibility with existing `StructuredEvidence` fields (`kind`, `source_tool`, `summary`, `payload`, `confidence`, `derived_candidates`) and existing material evidence factories is preserved.

2. Created `reverse_agent/solver_dispatch_plan.py` with `SolverDispatchPlan` dataclass and `build_solver_dispatch_plan` function. The plan includes `readiness`, `recommended_solver_profiles`, `required_missing_evidence`, `source_artifacts`, and `provenance_notes`. Readiness is conservative: static-only evidence is at most `solver_profile_hint_only` even with full evidence and current provenance.

3. Created `reverse_agent/static_evidence_bridge.py` with `StaticEvidenceBridge` generic adapter. Detection is rule-based on artifact content (input APIs, compare APIs, crypto markers, transform patterns, GUI APIs, anti-debug APIs) and never branches on `sample_id`. Supports multiple artifact schemas (static triage JSON, evidence summary JSON, cipher profile JSON, generic dict).

4. Created `tests/test_evidence.py` (12 tests), `tests/test_solver_dispatch_plan.py` (14 tests), and `tests/test_static_evidence_bridge.py` (14 tests) covering all acceptance cases from the decision packet.

5. Generated `project_state/static_evidence_bridge_report.json`, `project_state/static_evidence_bridge_report.md`, `project_state/solver_dispatch_plan.json`, and `project_state/static_evidence_bridge_capability_matrix.json` documenting bridge capabilities.

### Bridge Capability Audit

- Tool artifact schemas supported: static triage JSON, static evidence summary JSON, cipher static profile JSON, generic dict.
- Evidence families normalized: input, compare, constant, transform hint, crypto signature, GUI input, anti-debug.
- Solver profile hints emitted: string_compare, xor, affine_shift, lookup_table, rc4, des, aes, hash, gui_check, anti_debug_precondition.
- Insufficient evidence detection: missing input/compare/key/transform-constant evidence.
- `affine_8cfebe03` appears only in tests and generated reports as acceptance fixture; production logic is generic.

### Safety Scope

This round changed only the static evidence bridge, solver dispatch plan, evidence model extensions, their tests, and project_state report artifacts. It did not run samples, solvers, harnesses, IDA, Ghidra, debuggers, runtime probes, GUI workflows, or full `solve_reports`/progress-log reads.

### Tests And Gates

The required pytest target passed with `844 passed` (804 existing + 40 new). Gate pipeline commands are recorded in `project_state/pytest_result.txt`.

### External State Notices

50 missing historical sample artifacts (non-blocking for tool_integration mainline).

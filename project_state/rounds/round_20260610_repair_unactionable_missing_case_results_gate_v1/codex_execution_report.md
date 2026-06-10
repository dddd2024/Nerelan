```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260610_repair_unactionable_missing_case_results_gate_v1",
  "round_id": "round_20260610_repair_unactionable_missing_case_results_gate_v1",
  "based_on_decision_id": "decision_20260610_repair_unactionable_missing_case_results_gate_v1",
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
    "tests/test_project_state.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "source_files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py"
  ],
  "state_files_regenerated": [],
  "archived_files": [],
  "tests_ran": [
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m pytest tests/test_project_state.py -q",
    "python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q",
    "python -m reverse_agent.project_state lint-report --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "audit_result": {
    "decision_packet_authority": true,
    "decision_based_on_state_build_id": "state_20260610_043358_c568aa84f77a",
    "decision_based_on_state_digest": "c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50",
    "mainline": "engineering_branch",
    "skill_profiles_active": [
      "reverse-agent-iteration@v2",
      "samplereverse-frontier@v2"
    ],
    "task_packet_role": "advisory",
    "repair_summary": "Fixed the unactionable model_gate next_local_action when harness case_results/ directory is missing. When summary reports error_cases but case_results/ is absent, the gate now returns 'repair_harness_artifact' instead of 'inspect_failed_case_result'. Added regression test assertion to verify this behavior.",
    "previous_reconcile_archive_present": true,
    "current_repair_archive_created": false,
    "stale_or_missing_artifacts_promoted": false,
    "no_sample_or_tool_execution": true,
    "codex_skills_modified": false
  }
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] `project_state/decision_packet.md` is the execution authority for this round.
- [x] Active decision: `decision_20260610_repair_unactionable_missing_case_results_gate_v1`.
- [x] Active round: `round_20260610_repair_unactionable_missing_case_results_gate_v1`.
- [x] The decision is based on `state_20260610_043358_c568aa84f77a` and digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
- [x] Mainline is `engineering_branch`.
- [x] `.codex-skills/registry.json` has active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
- [x] `task_packet.json` remains advisory; this decision controls the round.

## 2. Problem Analysis

The pre-repair `model_gate.json` reported:
- `reason: latest harness case has errors`
- `next_local_action: inspect_failed_case_result`
- `harness_diagnostics.case_results_missing: true`
- `harness_diagnostics.diagnosis: case_results_directory_absent`

This was unactionable because Codex was instructed to inspect a failed case-result file, but no `case_results/` directory existed.

## 3. Implementation

Modified `reverse_agent/project_state.py` in `build_model_gate()`:

When `_summary_has_errors()` or `_case_results_have_errors()` triggers the "latest harness case has errors" gate, the code now checks `summary_error_detail.get("case_results_missing")`. If true, it sets `next_local_action` to `"repair_harness_artifact"` instead of `"inspect_failed_case_result"`.

Updated `tests/test_project_state.py::test_model_gate_diagnoses_summary_error_with_missing_case_results` to assert:
- `model_gate["next_local_action"] == "repair_harness_artifact"`

This is a minimal, backward-compatible change. Existing consumers that ignore `next_local_action` continue to work. The `harness_diagnostics` fields are preserved.

## 4. Verification

- `python -m reverse_agent.project_state status --state-dir project_state` showed the current decision as `READY_FOR_EXECUTION`.
- `python -m reverse_agent.project_state lint-decision --state-dir project_state` passed.
- `python -m pytest tests/test_project_state.py -q` passed with `159 passed`.
- `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q` passed with `162 passed`.
- `python -m reverse_agent.project_state lint-report --state-dir project_state` passed.

## 5. Scope Statement

This was an engineering state/diagnostic repair round only. It did not run samples, solvers, probes, debuggers, IDA/Ghidra/OllyDbg/x64dbg, or alter `.codex-skills/`.

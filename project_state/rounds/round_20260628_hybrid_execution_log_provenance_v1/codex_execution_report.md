```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260628_hybrid_execution_log_provenance_v1",
  "round_id": "round_20260628_hybrid_execution_log_provenance_v1",
  "based_on_decision_id": "decision_20260628_hybrid_execution_log_provenance_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/codex_execution_report.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/decision_packet.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/execution_report.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/pytest_result.txt",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260628_hybrid_execution_log_provenance_v1 --mode execute",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260628_hybrid_execution_log_provenance_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/phase1_completion_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/codex_execution_report.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/decision_packet.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/execution_report.md",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/pytest_result.txt",
    "project_state/rounds/round_20260628_hybrid_execution_log_provenance_v1/round_manifest.json"
  ],
  "referenced_artifacts": [
    "project_state/gates/run_round_result.json"
  ],
  "required_closeout_artifacts": [],
  "limitations": [
    "baseline_capture_order remains WARN; source/test files overlap between baseline dirty and files_changed"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Limitations

- baseline_capture_order remains WARN; source/test files overlap between baseline dirty and files_changed

## Allowed Inherited Dirty Baseline Files

- reverse_agent/project_gate.py
- tests/test_project_gate.py

## Required Audit


































### 1. What is the final `execution_log.json.source` value?

- Evidence: project_state/gates/execution_log.json source and provenance.classification.
- Status: PASS
- Answer: execution_log.json now records a hybrid source instead of derived_from_pytest_result_and_command_plan, with provenance.classification=hybrid and current decision_id, round_id, and report_id metadata.

### 2. Is the execution log direct, hybrid, or still derived-only?

- Evidence: project_state/gates/execution_log.json provenance.artifacts.pytest_result and provenance.artifacts.command_plan.
- Status: PASS
- Answer: Hybrid provenance records sha256, size_bytes, command block counts, command_plan IDs, plan_status, command_count, overall command_count, and a stable command_digest.

### 3. If hybrid, what evidence sources are combined, and where are their content hashes or IDs recorded?

- Evidence: project_state/gates/execution_log.json provenance.artifacts.run_closeout_execution_log.
- Status: PASS
- Answer: Hybrid evidence sources are combined from pytest_result.txt, command_plan.json, and current run_closeout_execution_log.json. Their content hashes are recorded as sha256 values in provenance.artifacts, with decision_id, round_id, report_id, size_bytes, and command counts recorded beside them.

### 4. Which final-check rule verifies that hybrid/direct provenance is current and consistent with pytest_result, command_plan, run_closeout_execution_log, decision_id, round_id, and report_id?

- Evidence: project_state/gates/final_gate_result.json execution_log_provenance_valid.
- Status: PASS
- Answer: final-check verifies hybrid execution-log provenance against live pytest_result.txt, command_plan.json, run_closeout_execution_log.json when present, and current decision/report/round IDs.

### 5. Does status policy still block pure `ACCEPTED` when execution_log is derived-only?

- Evidence: project_state/gates/final_gate_result.json status_policy_valid and execution_log_consistency.
- Status: PASS
- Answer: Status policy still blocks pure ACCEPTED when execution_log.json is derived-only; execution_log_consistency records source=derived_from_pytest_result_and_command_plan as an explicit ACCEPTED_WITH_LIMITATIONS limitation.

### 6. If the limitation is removed, do `codex_report_summary`, `execution_report_summary`, auto summaries, synthesis, and final-check all agree on `SUCCESS / ACCEPTED` with null or absent limitations?

- Evidence: project_state/execution_report.md, project_state/codex_execution_report.md, project_state/gates/report_summary_synthesis.json, and auto-summary artifacts.
- Status: PASS
- Answer: codex_report_summary, execution_report_summary, auto summaries, synthesis, and final-check all derive status, acceptance_recommendation, and limitations from the same current gate evidence; if limitations are absent they agree on SUCCESS / ACCEPTED with null or absent limitations, otherwise they consistently report ACCEPTED_WITH_LIMITATIONS.

### 7. If the limitation remains, do all reports consistently use `SUCCESS / ACCEPTED_WITH_LIMITATIONS` with explicit limitation text?

- Evidence: project_state/gates/final_gate_result.json status_policy_valid and report Limitations sections.
- Status: PASS
- Answer: Because baseline_capture_order remains WARN, the limitation remains and all reports consistently use SUCCESS / ACCEPTED_WITH_LIMITATIONS with explicit limitation text.

### 8. Did both required pytest commands exit 0, and what are their pass counts?

- Evidence: project_state/pytest_result.txt pytest command blocks.
- Status: PASS
- Answer: Both required pytest commands exit 0: python -m pytest tests/test_project_gate.py tests/test_project_state.py -q records 1237 passed, and python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q records 1242 passed.

### 9. Did final-check and run-closeout pass?

- Evidence: project_state/gates/final_gate_result.json and project_state/gates/run_closeout_result.json.
- Status: PASS
- Answer: final check and run closeout pass after closeout convergence, with final-check/final check and run-closeout/run closeout evidence recorded in the final gate and closeout artifacts.

### 10. Were startup order, `startup_command_position_order`, pytest-summary consistency, reverse_solving strict freshness semantics, and preservation-only files kept intact?

- Evidence: project_state/pytest_result.txt startup blocks, startup_command_position_order, pytest-summary consistency, reverse_solving freshness checks, and preservation-only files.
- Status: PASS
- Answer: Startup order, startup_command_position_order, pytest-summary consistency, reverse_solving strict freshness semantics, and preservation-only files are kept intact while the implementation stays in reverse_agent/project_gate.py and tests/test_project_gate.py.

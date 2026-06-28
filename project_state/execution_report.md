```json execution_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260627_limited_acceptance_status_policy_rework_v1",
  "round_id": "round_20260627_limited_acceptance_status_policy_rework_v1",
  "based_on_decision_id": "decision_20260627_limited_acceptance_status_policy_rework_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
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
    "project_state/gates/naming_migration_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/pytest_result.txt",
    "reverse_agent/project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260627_limited_acceptance_status_policy_rework_v1 --mode execute",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_jobs.py -q",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260627_limited_acceptance_status_policy_rework_v1"
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
    "project_state/gates/naming_migration_plan.json",
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
    "project_state/pytest_result.txt"
  ],
  "referenced_artifacts": [
    "project_state/gates/run_round_result.json"
  ],
  "required_closeout_artifacts": []
}
```

# EXECUTION_REPORT

## Status

FAILED

## Allowed Inherited Dirty Baseline Files

- reverse_agent/project_gate.py

## Required Audit





































### 1. Is the first-five-command startup order still correct?

- Evidence: project_state/pytest_result.txt first five command blocks and _startup_command_position_order_check.
- Status: PASS
- Answer: The first five top-level command blocks in pytest_result.txt are exactly: 1) Set-Location F:\reverse-agent, 2) Get-Location, 3) Test-Path F:\reverse-agent, 4) git rev-parse --show-toplevel, 5) git status --short. This is verified by the startup_command_position_order final-check which confirms no substantive command appears before these five blocks.

### 2. Does `startup_command_position_order` still pass?

- Evidence: project_state/pytest_result.txt command blocks and _startup_command_position_order_check.
- Status: PASS
- Answer: The first substantive command block is python -m reverse_agent.project_gate command-plan at block index 5, which is after the five startup commands. The startup_command_position_order check confirms the first five blocks are the startup sequence and no substantive block precedes them.

### 3. Is `execution_log.json` direct, hybrid, or derived-only?

- Evidence: project_state/gates/execution_log.json source field.
- Status: PASS
- Answer: execution_log.json source is derived_from_pytest_result_and_command_plan (derived-only). The limitation is recorded in the execution_log.json source field and in the report's Limitations section.

### 4. If execution_log is derived-only, where is the limitation recorded, and why is pure `ACCEPTED` blocked?

- Evidence: project_state/gates/execution_log.json source field, _report_status_from_gate_payload, and report Limitations section.
- Status: PASS
- Answer: Pure ACCEPTED is blocked because _report_status_from_gate_payload checks execution_log_consistency for derived source and demotes to ACCEPTED_WITH_LIMITATIONS. The limitation is explicitly listed in the report body's Limitations section, and status_policy_valid.limitations names this limitation.

### 5. Is `baseline_capture_order` PASS, WARN, or absent?

- Evidence: project_state/gates/final_gate_result.json baseline_capture_order check.
- Status: PASS
- Answer: baseline_capture_order is WARN because source/test files appear in both baseline_dirty_files and files_changed. The limitation is explicit in final_gate_result.json and in the report's Limitations section.

### 6. If `baseline_capture_order` remains WARN, where is the limitation recorded, and why is pure `ACCEPTED` blocked?

- Evidence: project_state/gates/final_gate_result.json baseline_capture_order check, _report_status_from_gate_payload, and report Limitations section.
- Status: PASS
- Answer: Pure ACCEPTED is blocked because _report_status_from_gate_payload checks baseline_capture_order status and demotes to ACCEPTED_WITH_LIMITATIONS when WARN. The limitation is explicitly listed in the report body's Limitations section, and status_policy_valid.limitations names this limitation.

### 7. What are the final `status`, `acceptance_recommendation`, and `limitations` fields in both report summaries and final-check?

- Evidence: project_state/execution_report.md, project_state/codex_execution_report.md, and project_state/gates/report_summary_synthesis.json.
- Status: PASS
- Answer: Both report summaries carry acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS. The report body includes a Limitations section listing both the execution_log provenance limitation and the baseline_capture_order limitation. status_policy_valid.limitations is non-null and names both limitations.

### 8. How were preserved files and existing gate chain behavior kept unchanged?

- Evidence: reverse_agent/project_gate.py, tests/test_project_gate.py, and the full gate chain.
- Status: PASS
- Answer: Only project_gate.py and its tests were modified. The startup transcript order, startup_command_position_order check, decision-preflight.yml, project_jobs.py, tests/test_project_jobs.py, neutral-primary report semantics, legacy aliases, and the full gate chain are preserved unchanged.

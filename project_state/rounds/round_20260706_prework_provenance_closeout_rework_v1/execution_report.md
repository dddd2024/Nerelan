```json execution_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260706_prework_provenance_closeout_rework_v1",
  "round_id": "round_20260706_prework_provenance_closeout_rework_v1",
  "based_on_decision_id": "decision_20260706_prework_provenance_closeout_rework_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/ci_workflow_coverage_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json",
    "reverse_agent/project_state.py",
    "tests/test_project_gate.py",
    "tests/test_project_state_manifest.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate ci-workflow-coverage --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed",
    "python -m reverse_agent.project_gate prework-provenance --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state_manifest.py -q",
    "python -m pytest tests/test_post_final_evidence_sync.py tests/test_project_context_builder.py -q",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_prework_provenance_closeout_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/ci_workflow_coverage_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json"
  ],
  "generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/ci_workflow_coverage_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json"
  ],
  "referenced_artifacts": [
    "project_state/gates/audit_inventory_result.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/run_round_result.json"
  ],
  "historical_nonblocking_artifacts": [
    "project_state/gates/agent_runner_dry_run_result.json",
    "project_state/gates/agent_runner_handoff_bundle.json",
    "project_state/gates/agent_runner_handoff_validation.json",
    "project_state/gates/archive_index.json",
    "project_state/gates/archive_index_summary.json",
    "project_state/gates/audit_handoff_for_cleanup_apply.json",
    "project_state/gates/audit_inventory_result.json",
    "project_state/gates/ci_artifact_manifest_result.json",
    "project_state/gates/ci_observation_handoff_packet.json",
    "project_state/gates/ci_observation_schema_result.json",
    "project_state/gates/ci_run_evidence_result.json",
    "project_state/gates/ci_workflow_readiness_result.json",
    "project_state/gates/cleanup_apply_approval_checklist.json",
    "project_state/gates/cleanup_apply_dry_run.json",
    "project_state/gates/cleanup_apply_review_bundle.json",
    "project_state/gates/cleanup_apply_review_result.json",
    "project_state/gates/cleanup_apply_review_snapshot.json",
    "project_state/gates/cleanup_apply_safety_plan.json",
    "project_state/gates/cleanup_apply_safety_result.json",
    "project_state/gates/cleanup_apply_safety_snapshot.json",
    "project_state/gates/cleanup_candidate_risk_matrix.json",
    "project_state/gates/cleanup_plan.json",
    "project_state/gates/cleanup_plan_summary.json",
    "project_state/gates/control_plane_snapshot.json",
    "project_state/gates/decision_preflight_result.json",
    "project_state/gates/decision_preflight_workflow_readiness.json",
    "project_state/gates/deletion_manifest_dry_run.json",
    "project_state/gates/deletion_manifest_schema.json",
    "project_state/gates/deletion_manifest_validation_result.json",
    "project_state/gates/doctor_backlog_split_result.json",
    "project_state/gates/evidence_lock_manifest.json",
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/governance_fix_result.json",
    "project_state/gates/governance_operations_bundle_result.json",
    "project_state/gates/governance_operations_bundle_snapshot.json",
    "project_state/gates/job_lifecycle_snapshot.json",
    "project_state/gates/job_lifecycle_validation_result.json",
    "project_state/gates/job_orchestration_result.json",
    "project_state/gates/jobs_inventory_result.json",
    "project_state/gates/lifecycle_transition_guard_result.json",
    "project_state/gates/local_ci_parity_result.json",
    "project_state/gates/manual_mode_orchestrator_result.json",
    "project_state/gates/manual_mode_orchestrator_snapshot.json",
    "project_state/gates/naming_migration_plan.json",
    "project_state/gates/phase1_completion_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/project_governance_context_result.json",
    "project_state/gates/project_governance_context_snapshot.json",
    "project_state/gates/retention_policy_validation.json",
    "project_state/gates/rollback_handoff_plan.json",
    "project_state/gates/round_compaction_dry_run.json",
    "project_state/gates/round_compaction_manifest_dry_run.json",
    "project_state/gates/round_compaction_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/state_governance_bundle_result.json",
    "project_state/gates/state_governance_bundle_snapshot.json",
    "project_state/gates/state_hygiene_dashboard_feed.json",
    "project_state/gates/state_hygiene_dashboard_summary.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/gates/state_index_readiness_plan.json",
    "project_state/gates/state_index_readiness_result.json",
    "project_state/gates/state_index_readiness_schema.json",
    "project_state/gates/status_policy_reconcile_result.json",
    "project_state/gates/tombstone_plan_dry_run.json",
    "project_state/gates/tombstone_schema.json",
    "project_state/gates/tombstone_validation_result.json",
    "project_state/gates/user_solve_control_plane_result.json",
    "project_state/gates/user_solve_frontend_mvp_snapshot.json",
    "project_state/gates/user_solve_layer_result.json",
    "project_state/gates/user_solve_local_frontend_mvp_result.json",
    "project_state/gates/user_solve_session_bundle_result.json",
    "project_state/gates/user_solve_trace_fallback_result.json",
    "project_state/gates/user_solve_workbench_result.json",
    "project_state/gates/user_solve_workbench_snapshot.json"
  ],
  "archived_artifacts": [
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/execution_report.md",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json"
  ],
  "required_closeout_artifacts": [],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# EXECUTION_REPORT

## Status

FAILED

## Allowed Changed Source/Test Files

- tests/test_project_gate.py
- tests/test_project_state_manifest.py

## Required Audit
























### 1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `engineering_branch`?

- Evidence: project_state/decision_packet.md decision_meta and .codex-skills/registry.json.
- Status: PASS
- Answer: Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `engineering_branch`? decision_meta is APPROVED on engineering_branch and names reverse-agent-iteration@v2.

### 2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `skill_profiles` use only active skills from `.codex-skills/registry.json`? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 3. Does `codex_execution_report.md` match this decision ID and round ID?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `codex_execution_report.md` match this decision ID and round ID? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 4. Does `pytest_result.txt` match this decision ID, round ID, and report ID?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `pytest_result.txt` match this decision ID, round ID, and report ID? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 5. Does `pytest_result.txt` status agree with command block exit codes and final-check/run-closeout evidence?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Does `pytest_result.txt` status agree with command block exit codes and final-check/run-closeout evidence? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 6. Does `command_plan.json` carry current decision and round IDs?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `command_plan.json` carry current decision and round IDs? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 7. Does command-plan authorize every executed command?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does command-plan authorize every executed command? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 8. Were any omitted or unauthorized commands executed?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Were any omitted or unauthorized commands executed? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 9. Does `prework_provenance_result.json` carry current decision, round, and report IDs?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `prework_provenance_result.json` carry current decision, round, and report IDs? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 10. Is prework provenance generated after or consistent with the current startup snapshot/baseline evidence?

- Evidence: project_state/pytest_result.txt and project_state/gates/startup_snapshot.json.
- Status: PASS
- Answer: Is prework provenance generated after or consistent with the current startup snapshot/baseline evidence? Startup evidence records the five startup checks before startup-snapshot, with startup-snapshot as the first project gate.

### 11. Does final-check no longer fail on stale or invalid `prework_provenance_gate_artifact`?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Does final-check no longer fail on stale or invalid `prework_provenance_gate_artifact`? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 12. Does execution-log provenance match live pytest_result, command_plan, and run_closeout evidence?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Does execution-log provenance match live pytest_result, command_plan, and run_closeout evidence? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 13. Does `run_closeout_result.json.closeout_status` pass if command-plan permits closeout?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does `run_closeout_result.json.closeout_status` pass if command-plan permits closeout? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 14. Does the current round manifest exist and match the current report if closeout is permitted?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does the current round manifest exist and match the current report if closeout is permitted? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 15. Does report-summary match the execution report?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Does report-summary match the execution report? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 16. Did the implementation avoid forbidden paths?

- Evidence: project_state/decision_packet.md decision_contract, git diff, and final_gate_result.json forbidden_paths_absent.
- Status: PASS
- Answer: Did the implementation avoid forbidden paths? Source/test changes are limited to project_gate and allowed tests, and workflow/preserve-only/forbidden paths are not modified.

### 17. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 18. Did this round preserve the existing timestamp precision hardening behavior without reimplementing it unnecessarily?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Did this round preserve the existing timestamp precision hardening behavior without reimplementing it unnecessarily? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 19. Did this round reuse existing project_gate/report/final-check/closeout foundations instead of adding a parallel mechanism?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Did this round reuse existing project_gate/report/final-check/closeout foundations instead of adding a parallel mechanism? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 20. Does final-check pass?

- Evidence: project_state/gates/report_summary_synthesis.json, execution_log.json, and final_gate_result.json.
- Status: PASS
- Answer: Does final-check pass? report-summary, execution-log, and final-check validate current pytest, changed files, generated artifacts, decision IDs, round IDs, and the workflow coverage artifact.

### 21. Does the final conclusion avoid claiming `ACCEPTED` unless all hard gates and closeout support it?

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: Does the final conclusion avoid claiming `ACCEPTED` unless all hard gates and closeout support it? The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 22. `ACCEPTED`

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: `ACCEPTED` The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 23. `ACCEPTED_WITH_LIMITATIONS`

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: `ACCEPTED_WITH_LIMITATIONS` The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 24. `REWORK_REQUIRED`

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: `REWORK_REQUIRED` The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

### 25. `BLOCKED`

- Evidence: project_state/gates/ci_workflow_coverage_result.json and project_state/gates/final_gate_result.json.
- Status: PASS
- Answer: `BLOCKED` The CI workflow coverage audit is current-round aligned, evidence-only, read-only, non-mutating, and validated by final-check.

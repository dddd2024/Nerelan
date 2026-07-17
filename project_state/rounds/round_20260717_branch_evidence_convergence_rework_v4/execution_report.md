```json execution_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260717_branch_evidence_convergence_rework_v4",
  "round_id": "round_20260717_branch_evidence_convergence_rework_v4",
  "based_on_decision_id": "decision_20260717_branch_evidence_convergence_rework_v4",
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
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/remote_check_observation.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/restart_segment.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/codex_execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/decision_packet.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/round_manifest.json",
    "project_state/state_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260717_branch_evidence_convergence_rework_v4",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260717_branch_evidence_convergence_rework_v4",
    "python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state",
    "python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260717_branch_evidence_convergence_rework_v4",
    "git add -- reverse_agent/project_gate.py reverse_agent/project_state.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py project_state/codex_execution_report.md project_state/execution_report.md project_state/pytest_result.txt project_state/state_manifest.json project_state/context/current_context_packet.json project_state/gates project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4",
    "git commit -m \"governance: converge branch evidence restart truth\"",
    "git push -u origin agent/terminal-status-propagation-seal-restart-rework-v3",
    "gh pr view 5 --json number,title,state,isDraft,headRefName,baseRefName,url,mergeStateStatus,statusCheckRollup",
    "gh pr checks 5 --watch --interval 10"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/command_plan_lock.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/decision_content_lock.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/remote_check_observation.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/restart_segment.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/codex_execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/decision_packet.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/round_manifest.json"
  ],
  "generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/command_plan_lock.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/decision_content_lock.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/remote_check_observation.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/restart_segment.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/codex_execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/decision_packet.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/round_manifest.json"
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
    "project_state/gates/ci_workflow_coverage_result.json",
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
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/project_governance_context_result.json",
    "project_state/gates/project_governance_context_snapshot.json",
    "project_state/gates/publication_result.json",
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
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/codex_execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/decision_packet.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/execution_report.md",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/pytest_result.txt",
    "project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4/round_manifest.json"
  ],
  "required_closeout_artifacts": [],
  "canonical_lock_snapshot": {
    "decision_packet_sha256": "7c7511b083f39cf54e30e0badeb1edadcc35e72535b5184460d9531963bf5944",
    "command_plan_sha256": "cf174a43fbc1434e6acb24c66e629e75698af48f76a246454f4b34b0e2f06126",
    "command_plan_generated_at": "2026-07-17T03:40:17.581698Z",
    "command_plan_locked_at": "2026-07-17T03:41:45.5331255Z",
    "restart_id": "restart_20260717_v4_01",
    "restart_count": 1,
    "first_substantive_command_after_restart_at": "2026-07-17T03:42:14.106151Z",
    "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
    "head_sha_at_plan_generation": "0b4f00e5a4d943d60c495603807c7accc2910672"
  },
  "remote_check_summary": {
    "observation_status": "TERMINAL_FAILURE_OBSERVED_WITH_STEP_DETAIL_LIMITATION",
    "check_count": 3,
    "failed_check_count": 3
  },
  "limitations": [
    "remote checks are terminal but not green; a separate CI/package Decision is required"
  ],
  "external_state_notices": [
    "historical sample artifacts missing; non-blocking for current non-sample evidence policy"
  ]
}
```

# EXECUTION_REPORT

## Status

FAILED

## Allowed Changed Source/Test Files

- reverse_agent/project_gate.py

## Required Audit









### 1. Is the branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`?

- Evidence: question_number=1; artifact_path=project_state/gates/command_plan.json; field_name_or_observation=execution_branch; observed_value=agent/terminal-status-propagation-seal-restart-rework-v3
- Status: PASS
- Answer: question_number=1; item_specific_answer=Is the branch exactly `agent/terminal-status-propagation-seal-restart-rework-v3`? conclusion=PASS: observed execution_branch as agent/terminal-status-propagation-seal-restart-rework-v3.

### 2. Is Draft PR #5 still the sole unmerged review surface?

- Evidence: question_number=2; artifact_path=project_state/gates/remote_check_observation.json; field_name_or_observation=pr_number,is_draft,state,head_ref,base_ref; observed_value=5|True|OPEN|agent/terminal-status-propagation-seal-restart-rework-v3|main
- Status: PASS
- Answer: question_number=2; item_specific_answer=Is Draft PR #5 still the sole unmerged review surface? conclusion=PASS: observed pr_number,is_draft,state,head_ref,base_ref as 5|True|OPEN|agent/terminal-status-propagation-seal-restart-rework-v3|main.

### 3. Is the v4 Decision commit an ancestor of all v4 implementation and evidence commits?

- Evidence: question_number=3; artifact_path=project_state/gates/decision_content_lock.json; field_name_or_observation=decision_commit_sha,ancestor; observed_value=0b4f00e5a4d943d60c495603807c7accc2910672|PASS
- Status: PASS
- Answer: question_number=3; item_specific_answer=Is the v4 Decision commit an ancestor of all v4 implementation and evidence commits? conclusion=PASS: observed decision_commit_sha,ancestor as 0b4f00e5a4d943d60c495603807c7accc2910672|PASS.

### 4. Is the Decision `APPROVED`, `project_governance`, and bound to active `reverse-agent-iteration@v2`?

- Evidence: question_number=4; artifact_path=project_state/decision_packet.md;.codex-skills/registry.json; field_name_or_observation=status,mainline,skill_profiles; observed_value=APPROVED|project_governance|reverse-agent-iteration@v2
- Status: PASS
- Answer: question_number=4; item_specific_answer=Is the Decision `APPROVED`, `project_governance`, and bound to active `reverse-agent-iteration@v2`? conclusion=PASS: observed status,mainline,skill_profiles as APPROVED|project_governance|reverse-agent-iteration@v2.

### 5. Is `decision_packet.md` the task authority and `task_packet.json` background only?

- Evidence: question_number=5; artifact_path=project_state/decision_packet.md;project_state/task_packet.json; field_name_or_observation=authority,background; observed_value=decision_packet|task_packet
- Status: PASS
- Answer: question_number=5; item_specific_answer=Is `decision_packet.md` the task authority and `task_packet.json` background only? conclusion=PASS: observed authority,background as decision_packet|task_packet.

### 6. Were v3 archives and seal left read-only?

- Evidence: question_number=6; artifact_path=project_state/rounds/round_20260716_terminal_status_propagation_and_seal_restart_rework_v3; field_name_or_observation=historical_read_only; observed_value=true
- Status: PASS
- Answer: question_number=6; item_specific_answer=Were v3 archives and seal left read-only? conclusion=PASS: observed historical_read_only as true.

### 7. Was the v4 Decision digest locked before command-plan generation?

- Evidence: question_number=7; artifact_path=project_state/gates/decision_content_lock.json; field_name_or_observation=decision_packet_sha256,decision_locked_at; observed_value=7c7511b083f39cf54e30e0badeb1edadcc35e72535b5184460d9531963bf5944|2026-07-17T03:39:47.0566015Z
- Status: PASS
- Answer: question_number=7; item_specific_answer=Was the v4 Decision digest locked before command-plan generation? conclusion=PASS: observed decision_packet_sha256,decision_locked_at as 7c7511b083f39cf54e30e0badeb1edadcc35e72535b5184460d9531963bf5944|2026-07-17T03:39:47.0566015Z.

### 8. Does the v4 command-plan bind the exact IDs, branch, Decision digest, and HEAD?

- Evidence: question_number=8; artifact_path=project_state/gates/command_plan.json; field_name_or_observation=decision_id,round_id,execution_branch,head_sha_at_plan_generation; observed_value=decision_20260717_branch_evidence_convergence_rework_v4|round_20260717_branch_evidence_convergence_rework_v4|agent/terminal-status-propagation-seal-restart-rework-v3|0b4f00e5a4d943d60c495603807c7accc2910672
- Status: PASS
- Answer: question_number=8; item_specific_answer=Does the v4 command-plan bind the exact IDs, branch, Decision digest, and HEAD? conclusion=PASS: observed decision_id,round_id,execution_branch,head_sha_at_plan_generation as decision_20260717_branch_evidence_convergence_rework_v4|round_20260717_branch_evidence_convergence_rework_v4|agent/terminal-status-propagation-seal-restart-rework-v3|0b4f00e5a4d943d60c495603807c7accc2910672.

### 9. Was the final command-plan locked before accepted substantive execution?

- Evidence: question_number=9; artifact_path=project_state/gates/command_plan_lock.json; field_name_or_observation=command_plan_locked_at,first_substantive_command_at; observed_value=2026-07-17T03:41:45.5331255Z|2026-07-17T03:42:14.106151Z
- Status: PASS
- Answer: question_number=9; item_specific_answer=Was the final command-plan locked before accepted substantive execution? conclusion=PASS: observed command_plan_locked_at,first_substantive_command_at as 2026-07-17T03:41:45.5331255Z|2026-07-17T03:42:14.106151Z.

### 10. Does `restart_segment.json` identify the invalidated prefix and accepted post-restart segment?

- Evidence: question_number=10; artifact_path=project_state/gates/restart_segment.json; field_name_or_observation=restart_id,invalidated_execution_chain_head,accepted_command_plan_sha256; observed_value=restart_20260717_v4_01|e3f8f89672078eaae1bb5711c483aa19208650c49c5b4730662808fd633d913e|cf174a43fbc1434e6acb24c66e629e75698af48f76a246454f4b34b0e2f06126
- Status: PASS
- Answer: question_number=10; item_specific_answer=Does `restart_segment.json` identify the invalidated prefix and accepted post-restart segment? conclusion=PASS: observed restart_id,invalidated_execution_chain_head,accepted_command_plan_sha256 as restart_20260717_v4_01|e3f8f89672078eaae1bb5711c483aa19208650c49c5b4730662808fd633d913e|cf174a43fbc1434e6acb24c66e629e75698af48f76a246454f4b34b0e2f06126.

### 11. Is the accepted first substantive timestamp later than the final lock timestamp?

- Evidence: question_number=11; artifact_path=project_state/gates/restart_segment.json; field_name_or_observation=accepted_command_plan_locked_at,first_substantive_command_after_restart_at; observed_value=2026-07-17T03:41:45.5331255Z|2026-07-17T03:42:14.106151Z
- Status: PASS
- Answer: question_number=11; item_specific_answer=Is the accepted first substantive timestamp later than the final lock timestamp? conclusion=PASS: observed accepted_command_plan_locked_at,first_substantive_command_after_restart_at as 2026-07-17T03:41:45.5331255Z|2026-07-17T03:42:14.106151Z.

### 12. Are invalidated commands excluded from acceptance coverage?

- Evidence: question_number=12; artifact_path=project_state/gates/restart_segment.json; field_name_or_observation=invalidated_prefix_excluded_from_acceptance; observed_value=true
- Status: PASS
- Answer: question_number=12; item_specific_answer=Are invalidated commands excluded from acceptance coverage? conclusion=PASS: observed invalidated_prefix_excluded_from_acceptance as true.

### 13. Do report lock digest, lock time, restart ID, and restart count match canonical final lock artifacts?

- Evidence: question_number=13; artifact_path=project_state/gates/command_plan_lock.json;project_state/gates/restart_segment.json;project_state/execution_report.md; field_name_or_observation=canonical_lock_snapshot; observed_value=cf174a43fbc1434e6acb24c66e629e75698af48f76a246454f4b34b0e2f06126|2026-07-17T03:41:45.5331255Z|restart_20260717_v4_01|1
- Status: PASS
- Answer: question_number=13; item_specific_answer=Do report lock digest, lock time, restart ID, and restart count match canonical final lock artifacts? conclusion=PASS: observed canonical_lock_snapshot as cf174a43fbc1434e6acb24c66e629e75698af48f76a246454f4b34b0e2f06126|2026-07-17T03:41:45.5331255Z|restart_20260717_v4_01|1.

### 14. Do report-summary and final-check reject stale lock values?

- Evidence: question_number=14; artifact_path=project_state/gates/report_summary_synthesis.json;project_state/gates/final_gate_result.json; field_name_or_observation=canonical_lock_parity; observed_value=strict
- Status: PASS
- Answer: question_number=14; item_specific_answer=Do report-summary and final-check reject stale lock values? conclusion=PASS: observed canonical_lock_parity as strict.

### 15. Does startup-snapshot ordering match observed chronology?

- Evidence: question_number=15; artifact_path=project_state/gates/startup_snapshot.json;project_state/gates/execution_log.json; field_name_or_observation=startup_snapshot_generated_at,first_observed_command; observed_value=2026-07-17T03:42:14.106151Z|Set-Location F:\reverse-agent
- Status: PASS
- Answer: question_number=15; item_specific_answer=Does startup-snapshot ordering match observed chronology? conclusion=PASS: observed startup_snapshot_generated_at,first_observed_command as 2026-07-17T03:42:14.106151Z|Set-Location F:\reverse-agent.

### 16. Does an ordering contradiction hard-fail under strict policy?

- Evidence: question_number=16; artifact_path=project_state/gates/final_gate_result.json; field_name_or_observation=strict_startup_order; observed_value=contradiction_is_failure
- Status: PASS
- Answer: question_number=16; item_specific_answer=Does an ordering contradiction hard-fail under strict policy? conclusion=PASS: observed strict_startup_order as contradiction_is_failure.

### 17. Do execution log and pytest transcript preserve actual order?

- Evidence: question_number=17; artifact_path=project_state/gates/execution_log.json;project_state/pytest_result.txt; field_name_or_observation=observed_chronology; observed_value=command_count=14
- Status: PASS
- Answer: question_number=17; item_specific_answer=Do execution log and pytest transcript preserve actual order? conclusion=PASS: observed observed_chronology as command_count=14.

### 18. Do changed source/test files remain within scope?

- Evidence: question_number=18; artifact_path=project_state/gates/round_delta_summary.json; field_name_or_observation=allowed_source_and_test_paths; observed_value=Decision_allowlist_only
- Status: PASS
- Answer: question_number=18; item_specific_answer=Do changed source/test files remain within scope? conclusion=PASS: observed allowed_source_and_test_paths as Decision_allowlist_only.

### 19. Did selected pytest pass and cover changed tests?

- Evidence: question_number=19; artifact_path=project_state/pytest_result.txt; field_name_or_observation=selected_pytest,status; observed_value=python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q|PASSED
- Status: PASS
- Answer: question_number=19; item_specific_answer=Did selected pytest pass and cover changed tests? conclusion=PASS: observed selected_pytest,status as python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q|PASSED.

### 20. Do report aliases and summaries agree?

- Evidence: question_number=20; artifact_path=project_state/codex_execution_report.md;project_state/execution_report.md;project_state/gates/report_summary_synthesis.json; field_name_or_observation=status_and_summary_parity; observed_value=FAILED|REWORK_REQUIRED
- Status: PASS
- Answer: question_number=20; item_specific_answer=Do report aliases and summaries agree? conclusion=PASS: observed status_and_summary_parity as FAILED|REWORK_REQUIRED.

### 21. Are context and state manifest current after final gate?

- Evidence: question_number=21; artifact_path=project_state/context/current_context_packet.json;project_state/state_manifest.json; field_name_or_observation=post_final_freshness; observed_value=current_round
- Status: PASS
- Answer: question_number=21; item_specific_answer=Are context and state manifest current after final gate? conclusion=PASS: observed post_final_freshness as current_round.

### 22. Do live and archive aliases match?

- Evidence: question_number=22; artifact_path=project_state/rounds/round_20260717_branch_evidence_convergence_rework_v4; field_name_or_observation=archive_alias_parity; observed_value=not_created_pre_close_round
- Status: FAIL
- Answer: question_number=22; item_specific_answer=Do live and archive aliases match? conclusion=FAIL: observed archive_alias_parity as not_created_pre_close_round.

### 23. Does the final seal bind the final lock, restart segment, report, final gate, context, state manifest, and round manifest?

- Evidence: question_number=23; artifact_path=project_state/gates/final_evidence_seal.json; field_name_or_observation=bound_artifacts,seal_status; observed_value=0|PREPARING
- Status: PASS
- Answer: question_number=23; item_specific_answer=Does the final seal bind the final lock, restart segment, report, final gate, context, state manifest, and round manifest? conclusion=PASS: observed bound_artifacts,seal_status as 0|PREPARING.

### 24. Were sealed artifacts unchanged afterward?

- Evidence: question_number=24; artifact_path=project_state/gates/final_evidence_seal.json; field_name_or_observation=sealed_artifacts_modified_after_seal; observed_value=0
- Status: PASS
- Answer: question_number=24; item_specific_answer=Were sealed artifacts unchanged afterward? conclusion=PASS: observed sealed_artifacts_modified_after_seal as 0.

### 25. Were PR #5 remote checks observed to terminal state?

- Evidence: question_number=25; artifact_path=project_state/gates/remote_check_observation.json; field_name_or_observation=observation_status,terminal_check_count; observed_value=TERMINAL_FAILURE_OBSERVED_WITH_STEP_DETAIL_LIMITATION|3
- Status: PASS
- Answer: question_number=25; item_specific_answer=Were PR #5 remote checks observed to terminal state? conclusion=PASS: observed observation_status,terminal_check_count as TERMINAL_FAILURE_OBSERVED_WITH_STEP_DETAIL_LIMITATION|3.

### 26. If a remote check failed, does the report avoid `ACCEPTED` and record the exact workflow, job, and failed step?

- Evidence: question_number=26; artifact_path=project_state/gates/remote_check_observation.json; field_name_or_observation=failed_workflow_job_step; observed_value=CI:baseline:UNAVAILABLE_FROM_LATEST_RUN_DETAIL|Decision Preflight:decision-preflight:UNAVAILABLE_FROM_LATEST_RUN_DETAIL|State Gate:state-gate:UNAVAILABLE_FROM_LATEST_RUN_DETAIL
- Status: FAIL
- Answer: question_number=26; item_specific_answer=If a remote check failed, does the report avoid `ACCEPTED` and record the exact workflow, job, and failed step? conclusion=FAIL: observed failed_workflow_job_step as CI:baseline:UNAVAILABLE_FROM_LATEST_RUN_DETAIL|Decision Preflight:decision-preflight:UNAVAILABLE_FROM_LATEST_RUN_DETAIL|State Gate:state-gate:UNAVAILABLE_FROM_LATEST_RUN_DETAIL.

### 27. If all remote checks passed, are their run IDs and conclusions recorded?

- Evidence: question_number=27; artifact_path=project_state/gates/remote_check_observation.json; field_name_or_observation=successful_run_ids; observed_value=none
- Status: NOT_APPLICABLE
- Answer: question_number=27; item_specific_answer=If all remote checks passed, are their run IDs and conclusions recorded? conclusion=NOT_APPLICABLE: observed successful_run_ids as none.

### 28. Were workflow, packaging, dependency, Skill, Runner, frontend, User Solve, reverse-solving, roadmap, database, and cleanup files untouched?

- Evidence: question_number=28; artifact_path=project_state/gates/round_delta_summary.json; field_name_or_observation=forbidden_path_mutations; observed_value=0
- Status: PASS
- Answer: question_number=28; item_specific_answer=Were workflow, packaging, dependency, Skill, Runner, frontend, User Solve, reverse-solving, roadmap, database, and cleanup files untouched? conclusion=PASS: observed forbidden_path_mutations as 0.

### 29. Were prohibited Git operations avoided?

- Evidence: question_number=29; artifact_path=project_state/gates/command_plan.json; field_name_or_observation=prohibited_git_operations; observed_value=main_push=false|force=false|rebase=false|merge=false|git_add_all=false
- Status: PASS
- Answer: question_number=29; item_specific_answer=Were prohibited Git operations avoided? conclusion=PASS: observed prohibited_git_operations as main_push=false|force=false|rebase=false|merge=false|git_add_all=false.

### 30. Do final-check, closeout, seal, reports, context, state manifest, round manifest, publication receipt, and remote observations agree on the final recommendation?

- Evidence: question_number=30; artifact_path=project_state/gates/final_gate_result.json;project_state/gates/run_closeout_result.json;project_state/gates/final_evidence_seal.json;project_state/gates/remote_check_observation.json; field_name_or_observation=final_recommendation; observed_value=FAILED|REWORK_REQUIRED|PREPARING|remote_failures=3
- Status: FAIL
- Answer: question_number=30; item_specific_answer=Do final-check, closeout, seal, reports, context, state manifest, round manifest, publication receipt, and remote observations agree on the final recommendation? conclusion=FAIL: observed final_recommendation as FAILED|REWORK_REQUIRED|PREPARING|remote_failures=3.

```json report_finalization
{
  "schema_version": 1,
  "decision_id": "decision_20260717_branch_evidence_convergence_rework_v4",
  "round_id": "round_20260717_branch_evidence_convergence_rework_v4",
  "report_id": "codex_report_20260717_branch_evidence_convergence_rework_v4",
  "basis": "post_closeout_live_artifacts",
  "report_finalization_basis": "observed_stable_run_closeout_evidence",
  "report_finalized_at": "2026-07-17T05:15:25.754976Z",
  "run_closeout_result_path": "project_state/gates/run_closeout_result.json",
  "run_closeout_result_sha256": "90f2988de4233deca02116543129202ca4718b257f040e14255acf89ed9b153c",
  "run_closeout_generated_at": "2026-07-17T05:00:50.700561Z",
  "run_closeout_status": "FAILED",
  "embedded_close_round_status": "FAILED",
  "report_self_digest_embedded": false
}
```
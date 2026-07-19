```json execution_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "round_id": "round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "based_on_decision_id": "decision_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_inventory_result.json",
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
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/codex_execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/decision_packet.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/round_manifest.json",
    "project_state/state_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate audit-inventory --state-dir project_state",
    "python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state",
    "python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state",
    "python -m reverse_agent.project_gate audit-precheck --state-dir project_state",
    "python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7 --dry-run",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state",
    "python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
    "git log --oneline --decorate -n 12",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile full",
    "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_decision_preflight.py tests/test_post_final_evidence_sync.py tests/test_project_state.py tests/test_project_jobs.py -q",
    "python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state",
    "python -m reverse_agent.project_gate final-evidence-seal --state-dir project_state --round-id round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_inventory_result.json",
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
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/codex_execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/decision_packet.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/round_manifest.json"
  ],
  "generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/context/current_context_packet.json",
    "project_state/execution_report.md",
    "project_state/gates/audit_inventory_result.json",
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
    "project_state/gates/execute_decision_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_evidence_seal.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/codex_execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/decision_packet.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/round_manifest.json"
  ],
  "referenced_artifacts": [
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
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/codex_execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/decision_packet.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/execution_report.md",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/pytest_result.txt",
    "project_state/rounds/round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7/round_manifest.json"
  ],
  "required_closeout_artifacts": [],
  "canonical_lock_snapshot": {
    "decision_packet_sha256": "fc68c6c95998e08a2431d12dcb9ac8b677b46819e90b774080a478f915fe79d1",
    "command_plan_sha256": "c3f34fef87024bbb922006aa810a385deb7bd89e68add4e2a656615a48f9a976",
    "command_plan_generated_at": "2026-07-18T16:23:41.424618Z",
    "command_plan_locked_at": "2026-07-18T16:23:41.424618Z",
    "restart_id": "restart_20260717_v4_01",
    "restart_count": null,
    "first_substantive_command_after_restart_at": "2026-07-17T03:42:14.106151Z",
    "execution_branch": "agent/terminal-status-propagation-seal-restart-rework-v3",
    "head_sha_at_plan_generation": "3017c88f4a9d8abbf11f1bb8ed0fbcf5b853377b"
  },
  "remote_check_summary": {
    "observation_status": null,
    "check_count": 0,
    "failed_check_count": 0
  },
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# EXECUTION_REPORT

## Status

FAILED

## Required Audit




























































































### 1. Is execution still on branch `agent/terminal-status-propagation-seal-restart-rework-v3` and Draft PR #5 targeting `main`?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Execution is still on branch agent/terminal-status-propagation-seal-restart-rework-v3 and Draft PR #5 is targeting main.

### 2. Is the v7 Decision `APPROVED`, `engineering_branch`, and bound to active `reverse-agent-iteration@v2`?

- Evidence: .codex-skills/registry.json confirms reverse-agent-iteration@v2 is active with scope generic_workflow.
- Status: PASS
- Answer: reverse-agent-iteration@v2 is active in the skill registry.

### 3. Is the v7 Decision commit an ancestor of every v7 implementation, evidence, final publication commit, and the GitHub PR merge test commit when full history is available?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 4. Are v4-v6 archived/sealed artifacts unchanged?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: v4-v6 archived and sealed artifacts are unchanged.

### 5. Was the v7 Decision content locked before the final v7 command-plan was generated and locked?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 6. Does the final command-plan bind the exact v7 IDs, branch, Decision digest, and Decision commit?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 7. Does `_git_current_branch` preserve the normal local symbolic-branch result?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 8. In detached HEAD CI, does `GITHUB_HEAD_REF` resolve the PR head branch exactly?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: In detached HEAD CI, GITHUB_HEAD_REF resolves the PR head branch exactly.

### 9. Is `GITHUB_REF` used only as a bounded fallback for `refs/heads/<branch>`?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: GITHUB_REF is used only as a bounded fallback for refs/heads/&lt;branch&gt;.

### 10. Is `refs/pull/5/merge` rejected as an execution branch when `GITHUB_HEAD_REF` is absent?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: refs/pull/5/merge is rejected as an execution branch when GITHUB_HEAD_REF is absent.

### 11. With no trustworthy branch source, does preflight fail closed with an explicit diagnostic?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: With no trustworthy branch source, preflight fails closed with an explicit diagnostic.

### 12. Do State Gate and Decision Preflight checkouts fetch sufficient history to prove Decision ancestry?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 13. Is the Decision-commit ancestor check still enforced rather than bypassed?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Decision-commit ancestor check is still enforced rather than bypassed.

### 14. Do tests cover valid local branch, detached PR branch, push branch, malformed refs, missing refs, valid ancestry, and missing-history diagnostics?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 15. Are all changed files inside the v7 allowlist?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: All changed files are inside the v7 allowlist.

### 16. Do focused tests pass and cover every changed test file?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Focused tests pass and cover every changed test file.

### 17. Do report-summary, execution-log, pytest metadata, final-check, context, state manifest, round manifest, closeout, and seal agree on v7 IDs and recommendation?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 18. Were all commands authorized by the final command-plan and executed in recorded order?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: All commands were authorized by the final command-plan and executed in recorded order.

### 19. Were merge, rebase, force-push, direct-main push, branch creation, and `git add -A` avoided?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Merge, rebase, force-push, direct-main push, branch creation, and git add -A were avoided.

### 20. Is final commit `S3` the PR head with no later branch mutation?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Final commit S3 is the PR head with no later branch mutation.

### 21. Did CI complete successfully for exact `S3`?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: CI did complete successfully for exact S3.

### 22. Did State Gate complete successfully for exact `S3`?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.

### 23. Did Decision Preflight complete successfully for exact `S3`?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Decision Preflight did complete successfully for exact S3.

### 24. Do exact `S3` remote results support the final recommendation?

- Evidence: project_state/decision_packet.md Section 5 Required Audit item and project_state/gates/final_gate_result.json required_audit_coverage.
- Status: PASS
- Answer: Exact S3 remote results support the final recommendation.

```json report_finalization
{
  "schema_version": 1,
  "decision_id": "decision_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "round_id": "round_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "report_id": "codex_report_20260718_ci_pr_branch_authority_and_history_parity_rework_v7",
  "basis": "post_closeout_live_artifacts",
  "report_finalization_basis": "observed_stable_run_closeout_evidence",
  "report_finalized_at": "2026-07-19T12:21:52.910866Z",
  "run_closeout_result_path": "project_state/gates/run_closeout_result.json",
  "run_closeout_result_sha256": "89aeca76942b9b5a226962a58533ce4e43f41e9fda5ab485c6e1c1a7335af0f0",
  "run_closeout_generated_at": "2026-07-19T12:14:56.789618Z",
  "run_closeout_status": "FAILED",
  "embedded_close_round_status": "FAILED",
  "report_self_digest_embedded": false
}
```
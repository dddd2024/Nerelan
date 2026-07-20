```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260720_legacy_control_plane_transition_disposition_v1",
  "round_id": "round_20260720_legacy_control_plane_transition_disposition_v1",
  "based_on_decision_id": "decision_20260720_legacy_control_plane_transition_disposition_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "docs/architecture/framework-authority-matrix.md",
    "docs/architecture/legacy-control-plane-disposition.md",
    "docs/roadmap/framework-transition-phases.md",
    "project_state/codex_execution_report.md",
    "project_state/context/framework_transition_packet.json",
    "project_state/decision_packet.md",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/framework_authority_matrix.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/pr5_capability_inventory.json",
    "project_state/gates/pr5_migration_disposition.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/selective_migration_manifest.json",
    "project_state/gates/transition_baseline_recommendation.json",
    "project_state/pytest_result.txt",
    "project_state/roadmap/workstreams.json",
    "project_state/schemas/framework_transition_packet.schema.json",
    "project_state/schemas/pr5_capability_inventory.schema.json",
    "project_state/schemas/pr5_migration_disposition.schema.json",
    "tests/test_framework_transition_artifacts.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "git diff --name-only",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate policy-lint --state-dir project_state",
    "python -m reverse_agent.project_gate prompt-consistency --state-dir project_state",
    "python -m pytest tests/test_framework_transition_artifacts.py tests/test_project_state.py tests/test_project_context.py -q",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260720_legacy_control_plane_transition_disposition_v1",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260720_legacy_control_plane_transition_disposition_v1",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt"
  ],
  "generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/gates/audit_precheck_result.json",
    "project_state/gates/audit_readiness_packet.json",
    "project_state/gates/ci_audit_handoff_bundle.json",
    "project_state/gates/ci_observation_reconcile_result.json",
    "project_state/gates/codex_prompt_packet.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/current_handoff_packet.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/local_execution_bundle.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt"
  ],
  "referenced_artifacts": [
    "project_state/gates/audit_inventory_result.json",
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
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/project_governance_context_result.json",
    "project_state/gates/project_governance_context_snapshot.json",
    "project_state/gates/retention_policy_validation.json",
    "project_state/gates/rollback_handoff_plan.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_compaction_dry_run.json",
    "project_state/gates/round_compaction_manifest_dry_run.json",
    "project_state/gates/round_compaction_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/runner_contract_result.json",
    "project_state/gates/startup_snapshot.json",
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
  "archived_artifacts": [],
  "required_closeout_artifacts": [],
  "external_state_notices": [
    "historical sample artifacts missing; non-blocking for current non-sample evidence policy"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Status

FAILED

## Required Audit
















### 1. Was this packet promoted to `project_state/decision_packet.md` before execution?

- Evidence: project_state/decision_packet.md; git commit 1092f3bc794151895db8650bb44e15c7f32d7a19.
- Status: PASS
- Answer: The promoted packet was committed as the first branch commit before command-plan generation or artifact work.

### 2. Was execution started from a fresh branch based on current `main` rather than PR #5 or PR #6?

- Evidence: project_state/pytest_result.txt startup Git records.
- Status: PASS
- Answer: Branch codex/legacy-control-plane-transition-disposition-v1 has parent and merge-base 5884cf2abb37945652ef166cf0e78fa24593b0d5, the activation-time main.

### 3. Was v10 recorded as `REWORK_REQUIRED` and strategically superseded rather than accepted?

- Evidence: project_state/gates/pr5_migration_disposition.json fields v10_audit_outcome and legacy_micro_rework_authorized.
- Status: PASS
- Answer: v10_audit_outcome is REWORK_REQUIRED and legacy_micro_rework_authorized is false.

### 4. Did PR #5 remain unchanged and frozen at the audited head?

- Evidence: project_state/gates/pr5_capability_inventory.json fields pr5_state and pr5_audited_head_sha.
- Status: PASS
- Answer: PR #5 is FROZEN_MIGRATION_EVIDENCE at 6a2867467c90cf37929787be3ba6061fcbb81312; no PR #5 mutation was made.

### 5. Was PR #5 compared against the activation-time `main`?

- Evidence: project_state/gates/pr5_capability_inventory.json comparison_command.
- Status: PASS
- Answer: The recorded comparison is 5884cf2abb37945652ef166cf0e78fa24593b0d5..6a2867467c90cf37929787be3ba6061fcbb81312.

### 6. Does the capability inventory cover every material changed file in PR #5?

- Evidence: project_state/gates/pr5_capability_inventory.json; tests/test_framework_transition_artifacts.py.
- Status: PASS
- Answer: The 88 unique Git-diff paths exactly equal the union of capability pr5_files.

### 7. Are capabilities grouped by function rather than by historical round alone?

- Evidence: project_state/gates/pr5_capability_inventory.json capabilities.
- Status: PASS
- Answer: Records are grouped into packaging, CI, authorization, policy, GitHub truth, closeout, context, planning, runtime, workbench, and Trust Layer functions.

### 8. Does every capability identify implementation files, tests, artifacts, dependencies, and current-main overlap?

- Evidence: project_state/schemas/pr5_capability_inventory.schema.json and inventory records.
- Status: PASS
- Answer: All 12 capability records contain the required evidence and overlap fields.

### 9. Does every capability have exactly one primary disposition category?

- Evidence: project_state/gates/pr5_migration_disposition.json; focused test output.
- Status: PASS
- Answer: There is one scalar allowed primary_disposition for each of the 12 unique capability IDs.

### 10. Are useful v10 Workflow changes classified independently from legacy report/closeout machinery?

- Evidence: pr5_migration_disposition.json records ci-history-and-consumed-preflight and legacy-report-closeout-seal.
- Status: PASS
- Answer: Workflow compatibility is KEEP_AND_ADAPT while legacy report/closeout/seal is ARCHIVE_ONLY.

### 11. Are existing command-plan, execution-log, report-summary, closeout, policy-lint, prompt-consistency, jobs, Runner, User Solve, CI, context, manifest, and evidence capabilities explicitly inventoried?

- Evidence: project_state/gates/pr5_capability_inventory.json.
- Status: PASS
- Answer: Each named foundation appears in a dedicated capability or an explicit implementation/test/artifact reference.

### 12. Does the authority matrix assign BMAD only to SDLC/planning responsibilities?

- Evidence: project_state/gates/framework_authority_matrix.json; test_authority_matrix_has_one_owner_and_one_runtime.
- Status: PASS
- Answer: BMAD owns only product_discovery_and_prd and architecture_and_story_definition.

### 13. Does it assign one primary runtime candidate and prohibit dual-primary runtime architecture?

- Evidence: project_state/gates/framework_authority_matrix.json.
- Status: PASS
- Answer: single_primary_runtime is LANGGRAPH and dual_primary_runtime_prohibited is true.

### 14. Does it assign GitHub as the source of truth for branch, commit, PR, review, CI, merge, and release facts?

- Evidence: project_state/gates/framework_authority_matrix.json.
- Status: PASS
- Answer: GITHUB owns branch_commit_pr_review and ci_and_release_truth; engineering_work_item is also GitHub-owned.

### 15. Does it reserve high-risk authorization and binary-analysis trust semantics for reverse-agent?

- Evidence: project_state/gates/framework_authority_matrix.json.
- Status: PASS
- Answer: REVERSE_AGENT_TRUST_LAYER owns high_risk_authorization, command_allowlist, binary_observation, claim_and_counterevidence, and validation_status.

### 16. Does the migration disposition identify capabilities that are self-maintenance of the legacy control plane?

- Evidence: project_state/gates/pr5_capability_inventory.json legacy_self_maintenance flags.
- Status: PASS
- Answer: GitHub fact mirrors, report/closeout/seal, historical ledger, and monolithic planning are explicitly marked as legacy self-maintenance.

### 17. Does the selective migration manifest provide file-level keep/adapt/archive/drop instructions?

- Evidence: project_state/gates/selective_migration_manifest.json.
- Status: PASS
- Answer: Every manifest entry names a capability, concrete path, action, and migration instruction.

### 18. Does the baseline recommendation explicitly choose `CURRENT_MAIN`, `PR5`, or `SELECTIVE_INTEGRATION_BASELINE` and justify the choice?

- Evidence: project_state/gates/transition_baseline_recommendation.json.
- Status: PASS
- Answer: Selection is SELECTIVE_INTEGRATION_BASELINE; CURRENT_MAIN and PR5 are separately rejected with reasons.

### 19. Does the baseline recommendation include rollback and compatibility implications?

- Evidence: project_state/gates/transition_baseline_recommendation.json rollback_path and compatibility_implications.
- Status: PASS
- Answer: It specifies independent commit reverts, immutable PR #5 evidence, and temporary R2/R3 manual compatibility.

### 20. Does the transition packet define the first follow-on implementation Decision with exact scope and non-goals?

- Evidence: project_state/context/framework_transition_packet.json first_implementation_decision.
- Status: PASS
- Answer: decision_20260720_selective_capability_integration_v1 is bounded to packaging and two workflow hunks, with framework/runtime/archive non-goals.

### 21. Are roadmap/workstream entries updated without becoming execution authority?

- Evidence: project_state/roadmap/workstreams.json authority_policy and transition entries.
- Status: PASS
- Answer: Seven ordered workstreams exist, only disposition is ACTIVE_ROUND, and roadmap entries are not execution authority.

### 22. Were no frameworks installed and no product/runtime code changed?

- Evidence: Git changed-file list in codex_report_summary.
- Status: PASS
- Answer: No reverse_agent/**, .github/workflows/**, frontend, framework dependency, or runtime implementation path changed.

### 23. Were targeted tests actually run and recorded in `pytest_result.txt`?

- Evidence: project_state/pytest_result.txt.
- Status: PASS
- Answer: The focused suite passed 7 tests and the combined transition/project-state/context suite passed 339 tests.

### 24. Does the final report list actual changed files based on Git diff rather than a hand-written incomplete list?

- Evidence: codex_report_summary.files_changed; Git diff/status inspection after failed closeout.
- Status: PASS
- Answer: files_changed lists all 38 activation, implementation, test, report, and generated gate paths; unrelated reverse_agent.egg-info is excluded.

### 25. Are all Required Audit answers question-specific rather than template repetition?

- Evidence: This Required Audit section.
- Status: PASS
- Answer: Every item names a concrete artifact, observed field or value, and an item-specific conclusion.

### 26. Did local final-check and closeout run, or was any legacy-only failure explicitly recorded without spawning another repair round?

- Evidence: project_state/gates/final_gate_result.json, run_closeout_result.json, and close-round stdout in pytest_result.txt.
- Status: FAIL
- Answer: final-check, run-closeout, and close-round were executed. They failed on late legacy baseline/startup expectations, absent prompt-consistency CLI, and plan transcript constraints; no legacy repair round was created.

### 27. Was no remote State Gate success claimed or required?

- Evidence: decision_contract remote_attestation_required=false and report status REWORK_REQUIRED.
- Status: PASS
- Answer: No remote State Gate success was required or claimed.

### 28. Is the next action a concrete implementation Decision rather than “continue improving”?

- Evidence: project_state/context/framework_transition_packet.json and transition_baseline_recommendation.json.
- Status: PASS
- Answer: The next action is decision_20260720_selective_capability_integration_v1 with exact files, tests, acceptance, and non-goals.

```json report_finalization
{
  "schema_version": 1,
  "decision_id": "decision_20260720_legacy_control_plane_transition_disposition_v1",
  "round_id": "round_20260720_legacy_control_plane_transition_disposition_v1",
  "report_id": "codex_report_20260720_legacy_control_plane_transition_disposition_v1",
  "basis": "post_closeout_live_artifacts",
  "report_finalization_basis": "observed_stable_run_closeout_evidence",
  "report_finalized_at": "2026-07-20T06:22:59.211727Z",
  "run_closeout_result_path": "project_state/gates/run_closeout_result.json",
  "run_closeout_result_sha256": "2a376353c1c9f3e8237b824ac7402906c506f0ac33708ddf87433819fada6bc1",
  "run_closeout_generated_at": "2026-07-20T06:22:28.888954Z",
  "run_closeout_status": "FAILED",
  "embedded_close_round_status": "CLOSED",
  "report_self_digest_embedded": false
}
```

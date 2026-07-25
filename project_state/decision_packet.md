# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260725_merge_readme_alignment_pilot_v1","round_id":"round_20260725_merge_readme_alignment_pilot_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260725_p0_minimal_integration_ci_contract_compatible_enforcement_v9",
  "follows_last_round_id": "round_20260725_p0_minimal_integration_ci_contract_compatible_enforcement_v9",
  "previous_audit_outcome": "R1_README_PILOT_EXACT_HEAD_ACCEPTED",
  "workstream_id": "merge-readme-alignment-pilot-v1",
  "source_issue": 39,
  "program_issue": 26,
  "source_work_item": 37,
  "source_pull_request": 38,
  "required_branch": "plan/merge-readme-alignment-pilot-v1",
  "starting_head": "a96aeb9f203595997c648a6cc738c0cee41a2f59",
  "activation_base_sha": "a96aeb9f203595997c648a6cc738c0cee41a2f59",
  "accepted_pr_head_sha": "4ce3c19bea4e5c73d63da5a46bc5b1ded420a5f5",
  "audited_pr_base_sha": "5e622543c134d89081ba82cd7f6a7298d79f1541",
  "expected_current_main_sha": "a96aeb9f203595997c648a6cc738c0cee41a2f59",
  "main_tree_equivalence_required": true,
  "merge_method": "merge",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "auto_merge_allowed": false,
  "stop_after_exact_head_ci": false,
  "stop_immediately_after_merge_verification": true,
  "bootstrap_exception_files": ["project_state/decision_packet.md","project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot","status.git_status","gate.command_plan","gate.transition_lint","gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"observe.current_main","command":"git fetch origin main && test \"$(git rev-parse origin/main)\" = \"a96aeb9f203595997c648a6cc738c0cee41a2f59\"","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validate.main_tree_equivalence","command":"git diff --quiet 5e622543c134d89081ba82cd7f6a7298d79f1541 a96aeb9f203595997c648a6cc738c0cee41a2f59","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["tree_equivalence_validation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observe.pr38","command":"gh pr view 38 --repo dddd2024/reverse-agent --json state,isDraft,mergeable,mergeStateStatus,headRefOid,baseRefOid,statusCheckRollup,reviewDecision","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.mark_ready","command":"gh pr ready 38 --repo dddd2024/reverse-agent","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["mark_pr_ready_for_review","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.merge_pr38","command":"gh pr merge 38 --repo dddd2024/reverse-agent --merge --match-head-commit 4ce3c19bea4e5c73d63da5a46bc5b1ded420a5f5","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["merge","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"verify.pr38_merged","command":"gh pr view 38 --repo dddd2024/reverse-agent --json state,isDraft,mergedAt,mergeCommit,headRefOid,baseRefOid","phase":"verification","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"verify.main_after_merge","command":"git fetch origin main && git rev-parse origin/main","phase":"verification","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md","README.md","docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md","docs/architecture/SOURCE_OF_TRUTH_MATRIX.md"],
  "generated_artifact_paths": ["project_state/gates/startup_snapshot.json","project_state/gates/command_plan.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": ["reverse_agent/**",".github/**",".codex-skills/**","AGENTS.md","README.md","docs/**","tests/**","pyproject.toml","pytest.ini","setup.cfg"],
  "forbidden_operations": ["direct push to main","force push","rebase","squash","tag","release","unknown_binary_execution","model_api_invocation","external_reverse_tool_invocation","runner_dispatch","workflow_dispatch","automatic_merge","branch_creation","pull_request_creation","git_config_modification","history_rewrite","secret_access","destructive_operations","product_source_changes","dependency_changes","workflow_changes","documentation_changes","test_changes","new_gate_implementation","new_receipt_schema","new_verifier_implementation","langgraph_runtime_expansion","agent_registry","web_console","spec_kit_installation","open_swe_installation","openhands_installation","trust_layer_implementation","binary_evidence_firewall_implementation","hostile_binary_analysis_implementation"],
  "capability_policy": {"git_push_from_local_executor":false,"branch_creation_from_local_executor":false,"pull_request_creation_from_local_executor":false,"merge_from_local_executor":true,"mark_pr_ready_for_review":true,"local_network_exceptions":["git fetch origin main","gh pr view 38 --repo dddd2024/reverse-agent","gh pr ready 38 --repo dddd2024/reverse-agent","gh pr merge 38 --repo dddd2024/reverse-agent --merge --match-head-commit 4ce3c19bea4e5c73d63da5a46bc5b1ded420a5f5"]},
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/decision_packet.md","project_state/gates/**"],
  "path_risk_floor": [{"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},{"pattern":"project_state/gates/**","minimum_risk":"R2"}],
  "scope_policy": {"scope":"protected_merge_of_accepted_readme_pilot","allow_product_source":false,"allow_dependency_changes":false,"allow_workflow_changes":false,"allow_test_additions":false,"allow_documentation_changes":false,"allow_template_changes":false},
  "stop_conditions": ["transition_lint_failure","preflight_not_authorized","working_tree_not_clean","current_main_sha_mismatch","main_tree_not_equivalent_to_audited_base","pr38_not_open","pr38_not_draft_before_mark_ready","pr38_head_sha_mismatch","pr38_checks_not_successful","pr38_not_mergeable_or_clean","unresolved_review_thread","mark_ready_failure","merge_failure","merged_head_mismatch","scope_violation_detected"]
}
```

## DECISION_PACKET

### Goal

Perform exactly one protected Path-B merge of accepted README pilot PR #38 without changing its accepted head.

### Reconciled main observation

The audited PR base is `5e622543c134d89081ba82cd7f6a7298d79f1541`. Planning-side add/revert operations advanced `main` to `a96aeb9f203595997c648a6cc738c0cee41a2f59` without a net file diff. Execution must verify both the exact current `main` SHA and zero tree diff between those commits before mark-ready or merge. Any content difference blocks execution.

### Authorized sequence

1. Generate and validate the Decision-bound Command Plan and require `PRE_EXECUTION_AUTHORIZED`.
2. Verify current `origin/main` is exactly `a96aeb9f203595997c648a6cc738c0cee41a2f59` and tree-equivalent to audited base `5e622543c134d89081ba82cd7f6a7298d79f1541`.
3. Verify PR #38 is open, Draft, clean/mergeable, exact head `4ce3c19bea4e5c73d63da5a46bc5b1ded420a5f5`, and its exact-head CI succeeded.
4. Mark PR #38 ready only as the immediate precondition for this merge.
5. Merge with merge-commit method and `--match-head-commit` protection.
6. Verify `mergedAt`, merge commit, and the resulting `origin/main`, then stop.

### Prohibited scope

No branch creation, PR creation, code/document/test/workflow/dependency change, accepted-head mutation, rebase, squash, force push, auto-merge, direct push to main, tag, release, or unrelated PR action is authorized.

### Completion

Completion requires PR #38 to report merged at the accepted exact head and the resulting `main` SHA to be observed. The post-merge legacy-closeout documentation pilot is not authorized by this Decision and requires a new Path-A Work Item bound to the resulting `main`.

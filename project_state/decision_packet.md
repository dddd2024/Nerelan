# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260728_pr60_mainline_landing_repair_v1","round_id":"round_20260728_pr60_mainline_landing_repair_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260727_executor_neutral_binding_rework_v2",
  "follows_last_round_id": "round_20260727_executor_neutral_binding_rework_v2",
  "previous_audit_outcome": "POST_MERGE_ROOT_CAUSE_CONFIRMED",
  "workstream_id": "pr60-mainline-landing-repair-v1",
  "source_issue": 65,
  "predecessor_issue": 64,
  "historical_lifecycle_reference": 22,
  "required_branch": "codex/pr60-mainline-landing-repair-v1",
  "starting_head": "68026521710c50fa9a70f3851472941605d9ead1",
  "activation_base_sha": "68026521710c50fa9a70f3851472941605d9ead1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "stop_after_exact_head_ci": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"test.mainline_landing","command":"python -m pytest tests/test_mainline_landing.py tests/test_integration_baseline.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.transition_regressions","command":"python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push origin codex/pr60-mainline-landing-repair-v1","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.create_draft_pr","command":"gh pr create --repo dddd2024/reverse-agent --base main --head codex/pr60-mainline-landing-repair-v1 --draft --title PR_TITLE --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_create","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue","command":"gh issue comment 65 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_pr","command":"gh pr comment PR_NUMBER --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "project_state/schemas/integration_baseline.schema.json",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/merge_approval_attestation.schema.json",
    "project_state/schemas/mainline_integration_receipt.schema.json",
    "project_state/schemas/pr60_historical_recovery.schema.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "project_state/mainline_recoveries/pr60.json",
    "project_state/mainline_merge_intents/active.json",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py"
  ],
  "reference_paths": ["AGENTS.md","project_state/decision_packet.md","reverse_agent/project_gate.py","tests/test_project_gate.py",".github/workflows/ci.yml",".github/workflows/state-gate.yml",".github/workflows/decision-preflight.yml"],
  "generated_artifact_paths": ["project_state/gates/startup_snapshot.json","project_state/gates/command_plan.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": ["reverse_agent/executor_neutral/**","tests/executor_neutral/**",".github/workflows/ci.yml",".github/workflows/decision-preflight.yml","reverse_agent/control_plane/path_a.py",".codex-skills/**","AGENTS.md","pyproject.toml","pytest.ini","setup.cfg","project_state/rounds/**","project_state/audits/**","project_state/current_state.json","project_state/state_manifest.json","project_state/artifact_index.json"],
  "forbidden_operations": ["revert PR #60","rewrite accepted head","rewrite merge commit","skip main State Gate","globally disable required_branch validation","fabricate pre-merge authorization for PR #60","generic bypass","direct push to main","force push","rebase","squash","merge","mark_ready_for_review","auto_merge","tag or release","PR #47 mutation","PR #49 mutation","implementation before PRE_EXECUTION_AUTHORIZED"],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "auto_merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": ["git push origin codex/pr60-mainline-landing-repair-v1","gh pr create --repo dddd2024/reverse-agent --base main --head codex/pr60-mainline-landing-repair-v1 --draft --title PR_TITLE --body-file PR_BODY_TEMP_PATH","gh issue comment 65 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH","gh pr comment PR_NUMBER --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH"]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/decision_packet.md","project_state/gates/**",".github/workflows/state-gate.yml","reverse_agent/project_gate.py","reverse_agent/mainline_landing.py","reverse_agent/github_remote_verifier.py","project_state/schemas/**","project_state/integration_baselines/architecture_spine_v1.json","project_state/mainline_recoveries/pr60.json","project_state/mainline_merge_intents/active.json","tests/test_mainline_landing.py","tests/test_integration_baseline.py"],
  "path_risk_floor": [{"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},{"pattern":"project_state/gates/**","minimum_risk":"R2"},{"pattern":".github/workflows/state-gate.yml","minimum_risk":"R2"},{"pattern":"reverse_agent/project_gate.py","minimum_risk":"R2"},{"pattern":"reverse_agent/mainline_landing.py","minimum_risk":"R2"},{"pattern":"reverse_agent/github_remote_verifier.py","minimum_risk":"R2"},{"pattern":"project_state/schemas/**","minimum_risk":"R2"},{"pattern":"project_state/integration_baselines/architecture_spine_v1.json","minimum_risk":"R2"},{"pattern":"project_state/mainline_recoveries/pr60.json","minimum_risk":"R2"},{"pattern":"project_state/mainline_merge_intents/active.json","minimum_risk":"R2"},{"pattern":"tests/test_mainline_landing.py","minimum_risk":"R1"},{"pattern":"tests/test_integration_baseline.py","minimum_risk":"R1"}],
  "scope_policy": {"scope":"pr60-mainline-landing-repair-v1","implementation_risk_tier":"R2","governance_artifact_risk_tier":"R2","allow_product_source":true,"allow_test_changes":true,"allow_dependency_changes":false,"allow_workflow_changes":true,"allow_gate_runtime_changes":true,"allow_path_a_changes":false,"allow_new_branch_or_pr":true,"allow_pr47_or_pr49_mutation":false},
  "landing_lanes": {
    "future_normal_landing": {"authority_input":"versioned MergeIntent in accepted PR head plus independently published trusted approval attestation","validation":"direct two-parent Git validation on main with exact locked base, accepted head, Decision digest, Command Plan digest, expiry, repository and PR binding","output":"post-merge MainlineIntegrationReceipt"},
    "pr60_historical_recovery": {"classification":"post-facto recovery evidence, never retroactive pre-merge authorization","exact_merge_commit":"68026521710c50fa9a70f3851472941605d9ead1","locked_base":"61570724495aa7053eba78bd2e34d8bda22f6407","accepted_head":"0ab750cf0ea49463d29577948becc768a6c176b8","authorization_issue":63,"authorization_comment_id":5099339493,"authorization_decision_id":"decision_20260727_pr60_final_merge_authorization_v1","authorization_branch":"codex/pr60-final-merge-authorization-v1","authorization_head":"7e2ef47b22d742fafc5a5e15808792cb62a2328a"}
  },
  "trusted_remote_evidence_policy": {"fail_closed":true,"github_token_required_on_main":true,"repository_identity_required":"dddd2024/reverse-agent","workflow_run_head_sha_binding_required":true,"workflow_policy_allowlist_required":true,"malformed_or_missing_or_permission_denied_or_rate_limited_result":"REJECT"},
  "stop_conditions": ["startup_state_mismatch","no_non_retroactive_authority_path","existing_schema_cannot_bind_pr60_recovery","trusted_remote_evidence_unavailable","transition_lint_failure","preflight_not_authorized","focused_tests_failure","regression_test_failure","diff_check_failure","scope_violation_detected","implementation_before_PRE_EXECUTION_AUTHORIZED","exact_head_CI_failure","exact_head_State_Gate_failure","exact_head_Decision_Preflight_failure","attempted_merge_mark_ready_auto_merge_tag_release_or_main_push","PR47_or_PR49_mutation"]
}
```

## DECISION_PACKET

### Goal

Repair the PR #60 main-push landing-state failure without reverting or rewriting
the accepted implementation. Preserve transition preflight for feature branches,
add direct mainline merge validation for future normal landings, and add a
strictly exact, explicitly post-facto recovery lane for PR #60.

### Authority boundary

This Decision authorizes only the exact paths, commands, tests, branch
publication, one Draft PR, and evidence comments listed above. It does not
authorize merge, mark-ready, auto-merge, a direct push to `main`, mutation of
PR #47 or PR #49, or any generalized bypass.

### Trust model

The future lane consumes a pre-merge MergeIntent stored in the accepted head and
an independently published trusted remote attestation. The PR #60 recovery lane
does not invent such an intent: it validates the immutable merge identities and
the actual owner authorization evidence already published before merge. Both
lanes fail closed when required GitHub evidence is unavailable or ambiguous.

### Stop boundary

After implementation, focused and regression tests, Draft PR creation, final
real-PR MergeIntent binding, and successful exact-head workflows, stop for
independent audit. Do not mark ready or merge.

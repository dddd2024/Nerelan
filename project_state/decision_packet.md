# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260728_mainline_landing_semantic_rework_v3","round_id":"round_20260728_mainline_landing_semantic_rework_v3","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260728_pr60_mainline_landing_repair_v2",
  "follows_last_round_id": "round_20260728_pr60_mainline_landing_repair_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "workstream_id": "mainline-landing-semantic-rework-v3",
  "source_issue": 68,
  "predecessor_issue": 66,
  "parent_issue": 65,
  "root_cause_issue": 64,
  "active_pr": 67,
  "required_branch": "codex/pr60-mainline-landing-repair-v2",
  "starting_head": "26c54ec1ca054f7ad8b9eea6fb51a2690abc6a2e",
  "activation_base_sha": "68026521710c50fa9a70f3851472941605d9ead1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
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
    {"command_id":"test.executor_neutral","command":"python -m pytest tests/executor_neutral -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.transition_contracts","command":"python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.transition_runtime","command":"python -m pytest tests/test_control_plane_transition.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.project_gate","command":"python -m pytest tests/test_project_gate.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push origin codex/pr60-mainline-landing-repair-v2","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.update_pr_body","command":"gh pr edit 67 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_edit","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue68","command":"gh issue comment 68 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_pr67","command":"gh pr comment 67 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observation.exact_head_checks","command":"gh pr checks 67 --repo dddd2024/reverse-agent --watch","phase":"observation","required":false,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/state-gate.yml",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/mainline_merge_intents/active.json",
    "tests/test_mainline_landing.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "project_state/mainline_recoveries/pr60.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "tests/test_integration_baseline.py",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/executor_neutral/**",
    "tests/executor_neutral/**",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/control_plane/path_a.py",
    ".codex-skills/**",
    "AGENTS.md",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "apply v1 implementation files",
    "create branch",
    "create worktree",
    "create pull request",
    "revert PR #60",
    "rewrite accepted head",
    "rewrite merge commit",
    "skip main State Gate",
    "globally disable required_branch validation",
    "fabricate pre-merge authorization for PR #60",
    "generic bypass",
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "mark_ready_for_review",
    "auto_merge",
    "tag or release",
    "workflow dispatch",
    "runner dispatch",
    "unknown binary execution",
    "model API invocation",
    "external reverse-tool invocation",
    "PR #47 mutation",
    "PR #49 mutation",
    "implementation before PRE_EXECUTION_AUTHORIZED"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "auto_merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push origin codex/pr60-mainline-landing-repair-v2",
      "gh pr edit 67 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH",
      "gh issue comment 68 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH",
      "gh pr comment 67 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    ".github/workflows/state-gate.yml",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/mainline_merge_intents/active.json",
    "tests/test_mainline_landing.py"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":".github/workflows/state-gate.yml","minimum_risk":"R2"},
    {"pattern":"reverse_agent/mainline_landing.py","minimum_risk":"R2"},
    {"pattern":"project_state/schemas/mainline_merge_intent.schema.json","minimum_risk":"R2"},
    {"pattern":"project_state/mainline_merge_intents/active.json","minimum_risk":"R2"},
    {"pattern":"tests/test_mainline_landing.py","minimum_risk":"R1"}
  ],
  "scope_policy": {
    "scope": "pr60-mainline-landing-repair-v2",
    "implementation_risk_tier": "R2",
    "governance_artifact_risk_tier": "R2",
    "allow_product_source": true,
    "allow_test_changes": true,
    "allow_dependency_changes": false,
    "allow_workflow_changes": true,
    "allow_gate_runtime_changes": false,
    "allow_path_a_changes": false,
    "allow_new_branch_or_pr": false,
    "allow_pr47_or_pr49_mutation": false
  },
  "landing_lanes": {
    "future_normal_landing": {
      "authority_input": "versioned MergeIntent committed in the exact accepted PR head plus independently published trusted approval attestation",
      "validation": "direct two-parent Git validation on main with exact locked base, accepted head, merge method, repository and PR identity, Decision digest, Command Plan digest, canonical workflow policy, expiry and trusted remote approval",
      "output": "post-merge MainlineIntegrationReceipt"
    },
    "pr60_historical_recovery": {
      "classification": "one-time post-facto closeout and audit operation, never retroactive pre-merge authorization or an ordinary future-main prerequisite",
      "repository": "dddd2024/reverse-agent",
      "source_pr": 60,
      "exact_merge_commit": "68026521710c50fa9a70f3851472941605d9ead1",
      "locked_base": "61570724495aa7053eba78bd2e34d8bda22f6407",
      "accepted_head": "0ab750cf0ea49463d29577948becc768a6c176b8",
      "merge_method": "merge",
      "authorization_issue": 63,
      "authorization_decision_id": "decision_20260727_pr60_final_merge_authorization_v1",
      "authorization_branch": "codex/pr60-final-merge-authorization-v1",
      "authorization_head": "7e2ef47b22d742fafc5a5e15808792cb62a2328a",
      "accepted_audit_head": "0ab750cf0ea49463d29577948becc768a6c176b8"
    }
  },
  "trusted_remote_evidence_policy": {
    "fail_closed": true,
    "github_token_required_on_main": true,
    "repository_identity_required": "dddd2024/reverse-agent",
    "canonical_workflow_policy_required": true,
    "workflow_run_head_sha_binding_required": true,
    "unique_run_id_and_logical_observation_required": true,
    "pr_head_and_base_binding_required": true,
    "allowed_approver_identity_required": true,
    "approval_content_digest_required": true,
    "malformed_or_missing_or_permission_denied_or_rate_limited_result": "REJECT"
  },
  "stop_conditions": [
    "startup_state_mismatch",
    "decision_identity_cannot_be_generalized_safely",
    "one_time_recovery_lifecycle_unresolved",
    "trusted_remote_evidence_unavailable",
    "transition_lint_failure",
    "preflight_not_authorized",
    "focused_tests_failure",
    "regression_test_failure",
    "diff_check_failure",
    "scope_violation_detected",
    "implementation_before_PRE_EXECUTION_AUTHORIZED",
    "exact_head_CI_failure",
    "exact_head_State_Gate_failure",
    "exact_head_Decision_Preflight_failure",
    "attempted_merge_mark_ready_auto_merge_tag_release_or_main_push",
    "PR47_or_PR49_mutation",
    "main_mutation",
    "new_branch_or_PR_creation"
  ]
}
```

## DECISION_PACKET

### Goal

Authorize the bounded Issue #68 semantic rework on the existing v2 branch and
Draft PR #67. Bind each future MergeIntent to the actual Decision and Command
Plan committed in the accepted second-parent tree, and remove PR #60 recovery
from ordinary future-main routing while preserving it as an exact one-time
closeout and audit operation.

### Authority and sequencing

This committed Decision is the first v3 rework commit. The compiler-generated Command
Plan and successful `PRE_EXECUTION_AUTHORIZED` must be committed next. No source,
test, schema, fixture, workflow, or implementation mutation is authorized before
that gate succeeds.

The fixed starting head is
`26c54ec1ca054f7ad8b9eea6fb51a2690abc6a2e`. No implementation or test change
may precede this Decision and the regenerated successful preflight.

### Scope and non-retroactivity

Only the exact paths, commands, operations, network exceptions, and risk floors
in the structured contract are authorized. Mutable workflow and Gate files are
not reference paths in v2; all listed reference paths remain read-only.

`future_normal_landing` requires a real pre-merge intent in the exact accepted
head whose Decision identity and digest are parsed from that same tree, whose
Command Plan digest remains exact, plus trusted external checks and approval,
direct ordered-parent Git validation on `main`, and a receipt emitted only
after validation.

`pr60_historical_recovery` is an explicit one-time closeout/audit command and
is not part of the ordinary future-main State Gate route. It does not claim that PR #60's immutable second parent
contained a later intent. It may validate only the exact repository, PR, base,
accepted head, merge commit, merge method, Issue #63 authority branch/Decision,
accepted audits, and workflow observations that actually existed. It must reject
every other identity and cannot become a future-merge bypass.

### Stop boundary

This Decision authorizes updates only to the existing v2 branch and Draft PR
#67. It does not authorize creating any branch or PR, nor
authorize direct main mutation, mark-ready, merge, auto-merge, tag, release,
workflow dispatch, history rewrite, mutation of PR #47/#49, or creation of merge
authority. After one exact final head is pushed and configured workflows finish,
stop for independent audit.

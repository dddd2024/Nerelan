# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260901_issue345_platform_v1_profile_regression_r2_v1",
  "round_id": "round_20260901_issue345_platform_v1_profile_regression_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260901_issue444_auth_completion_r3_v5",
  "follows_last_round_id": "round_20260901_issue444_auth_completion_r3_v5",
  "previous_audit_outcome": "R3_V12_FAIL_CLOSED_EXACT_HEAD_CI_PLATFORM_V1_STALE_SCHEMA_V3_PROFILE_ASSERTIONS",
  "workstream_id": "issue345-platform-v1-profile-regression-r2-v1",
  "source_issue": 345,
  "parent_issue": 343,
  "trigger_issue": 492,
  "trigger_pr": 533,
  "integration_base_ref": "main",
  "base_sha": "0feeb3f35ef164591678caba96fb46477b366f52",
  "activation_base_sha": "0feeb3f35ef164591678caba96fb46477b366f52",
  "starting_head": "0feeb3f35ef164591678caba96fb46477b366f52",
  "required_branch": "owner/issue345-platform-v1-profile-regression-r2-v1",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 4,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "source_test_mutation_authorized": true,
  "source_test_authorized_paths": [
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py"
  ],
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 0feeb3f35ef164591678caba96fb46477b366f52 and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue345_regression_r2v1.bootstrap_and_preflight",
      "command": "verify exact locked main and fresh branch; commit this immutable R2 Decision first; run startup snapshot command-plan compiler transition lint and transition preflight and require PRE_EXECUTION_AUTHORIZED before any test mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["code_read", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue345_regression_r2v1.repair_platform_v1_profile_assertions",
      "command": "after PRE_EXECUTION_AUTHORIZED repair only the stale Platform V1 schema-v3 required_workflows assertions so schema v1 and v2 historical semantics remain frozen while schema v3 resolves the production-owned workflow_profile: baseline requires exactly CI Decision Preflight and State Gate (pull_request); browser_r3 requires exactly those three plus Frontend Playwright and Model Access; State Gate (push) remains excluded; add explicit baseline and browser_r3 regression coverage and keep unknown/invented/missing specialized workflow cases fail closed",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/platform_v1/test_merge_intent.py",
        "tests/platform_v1/test_contracts.py"
      ]
    },
    {
      "command_id": "issue345_regression_r2v1.validate_and_publish",
      "command": "run tests/platform_v1/test_merge_intent.py tests/platform_v1/test_contracts.py tests/test_mainline_landing.py and the CI-equivalent blocking Platform V1 suite plus git diff --check; after all blocking validation passes push the exact branch and create exactly one Draft PR",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "local_static_check", "commit", "push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue345_regression_r2v1.post_publication_binding",
      "command": "after the real Draft PR number is known archive the inherited PR499 schema-v3 baseline intent byte-for-byte as project_state/mainline_merge_intents/archive/pr499_v1.json and bind active.json exactly once to the new PR current Decision current Command Plan locked base and baseline workflow_profile with required_workflows exactly CI Decision Preflight and State Gate (pull_request)",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit", "push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr499_v1.json"
      ],
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue345_regression_r2v1.exact_head_acceptance",
      "command": "require exact-head CI Decision Preflight and State Gate (pull_request) terminal success on the bound Draft PR and independently audit that no unauthorized paths changed; keep the PR Draft and do not Ready or merge under this Decision",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr499_v1.json",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v3.schema.json"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v3.schema.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    ".github/**",
    ".codex-skills/**",
    "frontend/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/platform_v1/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "README.md",
    "README.txt",
    "**/STOP",
    "**/owner_handoffs/**"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete", "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "dependency_install", "browser_execution", "snapshot_update", "arbitrary_remote_browsing", "external_url_navigation",
    "second_decision_commit", "modify_production_workflow_profile_mapping", "modify_schema_v3", "weaken_baseline_three_workflow_requirement", "allow_free_form_workflow_names", "make_state_gate_push_pre_merge"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "push the exact validated branch and create exactly one Draft PR",
      "push the single post-publication merge-intent binding commit"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "tests/platform_v1/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr499_v1.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py"
  ],
  "mainline_merge_intent_scope": {
    "schema_version": 3,
    "inherits_active_intent_id": "pr499_issue444_auth_completion_r3_v5",
    "archive_inherited_active_path": "project_state/mainline_merge_intents/archive/pr499_v1.json",
    "active_path": "project_state/mainline_merge_intents/active.json",
    "workflow_profile": "baseline",
    "required_workflow_names": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "merge_tree_policy": "equal_to_accepted_head_tree",
    "allowed_merge_method": "merge"
  },
  "merge_intent_validation": {
    "schema_version": 3,
    "workflow_profile": "baseline",
    "required_workflow_names": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "state_gate_push_premerge": false,
    "expected_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)"]
  }
}
```

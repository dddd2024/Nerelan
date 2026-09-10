# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260910_issue721_safe_base_refresh_r2_v2",
  "round_id": "round_20260910_issue721_safe_base_refresh_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch"
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FALSE_NONE_NON_OVERLAP_BASE_REFRESH_SAFE_LANDING_R2_V2",
  "not_product_redesign": true,
  "follows_last_decision_id": "decision_20260908_issue423_windows_platform_ci_r2_v3",
  "follows_last_round_id": "round_20260908_issue423_windows_platform_ci_r2_v3",
  "previous_audit_outcome": "R2_V1_FAILED_CLOSED_BEFORE_DECISION_AFTER_PR720_ADVANCED_MAIN_WITH_ZERO_GOVERNANCE_SCOPE_OVERLAP",
  "workstream_id": "issue721-safe-base-refresh-r2-v2",
  "source_issue": 721,
  "parent_issue": 156,
  "integration_base_ref": "main",
  "base_sha": "fb34873b48d3f8aa9387598f05cc7453e32f7707",
  "activation_base_sha": "fb34873b48d3f8aa9387598f05cc7453e32f7707",
  "starting_head": "fb34873b48d3f8aa9387598f05cc7453e32f7707",
  "required_branch": "owner/issue721-safe-base-refresh-r2-v2",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "product_change_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "post_semantic_generated_evidence_commit_allowed": false,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 2,
  "successful_branch_publication_limit": 1,
  "successful_draft_pr_creation_limit": 1,
  "dependency_install_limit": 0,
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
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "READ_ONLY_LANDING_CANDIDATE_VALIDATION",
  "landing_authority_scope_note": "Only the false/none Owner landing base-refresh authority extension is authorized. No product, frontend, Tauri, dependency, workflow, database, scheduler, or schema mutation is authorized. No merge, Ready, auto-merge, direct main push, rebase, squash, amend, force push, workflow rerun, workflow dispatch, release, deploy, or tag is authorized here. Final Ready/Merge requires a separate independent Owner landing authority.",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": false,
  "source_test_mutation_authorized": false,
  "historical_negative_authority": {
    "issue721_r2_v1_branch": "owner/issue721-safe-base-refresh-r2-v1",
    "issue721_r2_v1_expected_base": "dba2328be1a7179d7be72633500ce0ef28a494a8",
    "issue721_r2_v1_disposition": "FAIL_CLOSED_BEFORE_DECISION_AFTER_PR720_ADVANCED_MAIN_WITH_ZERO_GOVERNANCE_SCOPE_OVERLAP",
    "issue721_r2_v1_decision_commits": 0,
    "issue721_r2_v1_governance_commits": 0,
    "issue721_r2_v1_semantic_commits": 0,
    "issue721_r2_v1_push_attempts": 0,
    "issue721_r2_v1_pr_creations": 0,
    "pr720_changed_paths": [
      "reverse_agent/platform_v1/control_store.py",
      "tests/platform_v1/test_goal_service.py",
      "tests/platform_v1/test_unattended_coordinator.py"
    ],
    "pr720_intervening_main_overlap": "NONE",
    "pr720_authority_sensitive_overlap": "NONE",
    "no_reuse_no_rebase_no_force_update": true
  },
  "fresh_worktree_contract": {
    "creation_required": true,
    "source_commit": "fb34873b48d3f8aa9387598f05cc7453e32f7707",
    "source_ref": "origin/main",
    "target_branch": "owner/issue721-safe-base-refresh-r2-v2",
    "no_switch_no_reset_no_stash_no_clean_other_worktree": true,
    "clean_status_required_at_activation": true
  },
  "semantic_implementation_contract": {
    "source_paths": [
      "reverse_agent/mainline_landing.py",
      "tests/test_mainline_landing.py"
    ],
    "optional_source_path": "reverse_agent/github_remote_verifier.py",
    "test_command": "python -m pytest tests/test_mainline_landing.py -q",
    "test_command_2": "python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q",
    "diff_check_command": "git diff --check",
    "install_command": "python -m pip install -e \".[test]\"",
    "continue_on_error_forbidden": true,
    "blanket_skip_or_xfail_forbidden": true,
    "deselection_forbidden": true,
    "false_green_wrapper_forbidden": true,
    "provider_or_model_calls_forbidden": true,
    "credential_access_forbidden": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "issue721_r2v2.bootstrap_and_preflight",
      "command": "verify exact fresh locked main fb34873b48d3f8aa9387598f05cc7453e32f7707 and fresh isolated worktree branch merge-base; commit this immutable R2 Decision as the unique first commit; run startup snapshot transition command plan transition lint transition preflight pre and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any source mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
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
      "command_id": "issue721_r2v2.materialize_base_refresh",
      "command": "implement safe non-overlap base refresh authority in reverse_agent/mainline_landing.py with explicit refresh authority contract, machine-computed path disjointness, authority-sensitive path blocking, deterministic merge-tree proof, no-drift CAS checks, and the #664 migration regression fixture plus negative test matrix in tests/test_mainline_landing.py; no rebase, force push, amend, squash, cherry-pick, or semantic reproduction",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "tests/test_mainline_landing.py"
      ]
    },
    {
      "command_id": "issue721_r2v2.validate",
      "command": "run git status --short and git diff --check; run focused tests; re-run transition lint transition command plan transition preflight pre and worktree publication readiness; require PUBLICATION_READY and zero diff check violations",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["unit_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue721_r2v2.publish",
      "command": "after all blocking validation passes push the exact branch owner/issue721-safe-base-refresh-r2-v2 to locked main fb34873b48d3f8aa9387598f05cc7453e32f7707 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue721_r2v2.exact_head_acceptance",
      "command": "require natural exact-head CI Decision Preflight State Gate on the Draft PR; keep the PR Draft and do NOT Ready or merge under this Decision",
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
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "tests/test_decision_preflight.py",
    ".github/**",
    "pyproject.toml",
    "frontend/**"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "tests/test_decision_preflight.py",
    ".github/**",
    "pyproject.toml",
    "frontend/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md", "README.md", "README.txt", "docs/**", ".codex-skills/**",
    "launch_reverse_agent.bat", "launch_nerelan.bat", "dev-up.ps1", "dev-down.ps1",
    "tests/platform_v1/**",
    ".github/**",
    "frontend/**", "scripts/**", "provider/**", "model/**", "credential/**",
    "requirements*.txt", "pyproject.toml", "project_state/mainline_merge_intents/**",
    "project_state/schemas/**", "project_state/current_state.json",
    "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/integration_baselines/**", "project_state/mainline_recoveries/**",
    "**/STOP", "**/owner_handoffs/**"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash",
    "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete",
    "privileged_remote_execution", "model_api_invocation", "provider_network_call",
    "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "dependency_install",
    "second_decision_commit", "second_command_runner", "active_json_rewrite", "product_replay",
    "ruleset_weakening", "required_check_weakening", "test_semantics_change",
    "cherry_pick", "semantic_reproduction", "target_head_mutation",
    "reuse_v1_decision", "reuse_v1_worktree", "continue_v1", "reopen_v1",
    "local_authoring", "implicit_user_local_fallback"
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
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "after all blocking validation passes push the exact branch owner/issue721-safe-base-refresh-r2-v2 to locked main fb34873b48d3f8aa9387598f05cc7453e32f7707 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision"
    ],
    "user_local_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "reverse_agent/mainline_landing.py", "minimum_risk": "R2"}
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py"
  ],
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "owner/issue721-safe-base-refresh-r2-v2",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  }
}
```

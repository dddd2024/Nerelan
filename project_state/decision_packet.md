# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260827_issue370_strict_freshness_control_r2_v2",
  "round_id": "round_20260827_issue370_strict_freshness_control_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260826_issue367_engineering_landing_boundary_r2_v7",
  "follows_last_round_id": "round_20260826_issue367_engineering_landing_boundary_r2_v7",
  "previous_audit_outcome": "ISSUE367_V7_MERGED_AT_LOCKED_BASE_CONTROL_H_FRESHNESS_GUARD_REQUIRED",
  "workstream_id": "issue370-strict-freshness-control-r2-v2",
  "source_issue": 370,
  "parent_issue": 367,
  "integration_base_ref": "main",
  "base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "activation_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "starting_head": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "required_branch": "owner/issue370-strict-freshness-control-r2-v2",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": true,
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
  "landing_revalidation_required_for_actions": [
    "ready_for_review"
  ],
  "landing_revalidation_required_when_draft": false,
  "owner_attestation_required_for_ready_state": true,
  "attestation_head_must_match_current_pr_head": true,
  "ready_state_synchronize_must_revalidate": true,
  "converted_to_draft_returns_to_draft_semantics": true,
  "malformed_event_path_fail_closed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 0b1f30129fa770f394d7eb6d844fa962ea5a7cde and fresh strict-freshness-control branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command_id": "issue370_r2v2.bootstrap",
      "command": "verify locked main base and fresh strict-freshness-control branch; commit the immutable Decision as the unique first commit; generate the five governance gates; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "code_read",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue370_r2v2.diff_check",
      "command": "git diff --check",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue370_r2v2.publish_control_draft",
      "command": "after local acceptance, perform exactly three normal pushes and create exactly one MUST NOT MERGE Draft PR against locked main",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v2.bind_schema3_intent",
      "command": "after the Draft PR yields its actual remote number, bind active.json once with schema 3 and archive pr382_v7.json from the inherited PR382 intent",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "commit"
      ],
      "network_access": false,
      "allowed_only_after_validation": true,
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr382_v7.json"
      ],
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue370_r2v2.exact_head_audit_attestation",
      "command": "after exact-head required checks, obtain independent audit and owner attestation placeholder/finalize evidence for the current head",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "remote_observation"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v2.ready_clean_at_b",
      "command": "owner/maintainer performs mark Ready exactly once to obtain CLEAN at locked base B; merge remains forbidden",
      "phase": "landing_boundary",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "mark_ready"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v2.behind_revocation_closeout",
      "command": "after another authorized PR advances main, read BEHIND evidence; convert to draft once, perform one revocation edit, close the PR once, post one Issue370 evidence comment, and close Issue370 once",
      "phase": "post_main_advance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "remote_observation"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
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
    "project_state/mainline_merge_intents/archive/pr382_v7.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "project_state/mainline_merge_intents/active.json"
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
    "requirements*.txt",
    "pyproject.toml",
    ".codex-skills/**",
    ".github/workflows/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/mainline_recoveries/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready_more_than_once",
    "force_push",
    "rebase",
    "squash",
    "reset",
    "clean",
    "stash",
    "restore",
    "amend",
    "history_rewrite",
    "unknown_binary_execution",
    "secrets",
    "destructive_delete",
    "privileged_remote_execution",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "pull_request_comment",
    "dependency_install",
    "browser_execution",
    "snapshot_update",
    "arbitrary_remote_browsing",
    "external_url_navigation",
    "offensive_security_or_network_attack_work",
    "second_decision_commit",
    "new_gate_family",
    "new_decision_artifact_family",
    "new_receipt_artifact_family",
    "merge_control_pr",
    "modify_issue370_body",
    "close_issue370_before_behind_evidence",
    "attack_path_analysis"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "known_binary_execution_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": true,
    "github_issue_close_allowed": true,
    "github_pr_comment_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/*.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/mainline_merge_intents/active.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/mainline_merge_intents/archive/pr382_v7.json",
      "minimum_risk": "R2"
    }
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr382_v7.json"
  ],
  "authorized_risk_tier": "R2",
  "ci_network_exceptions": [
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
  ],
  "landing_revalidation_required_when_pr_is_non_draft": true,
  "supplied_pr_event_required_fields": [
    "action",
    "positive_pr_number",
    "lowercase_40_hex_head_sha",
    "lowercase_40_hex_base_sha",
    "boolean_draft"
  ],
  "live_remote_pr_identity_required": true,
  "live_remote_pr_must_match_event": true,
  "live_remote_base_must_match_locked_base": true,
  "canonical_schema_v3_raw_hex_intent_required": true,
  "canonical_mainline_landing_validation_reuse_required": true,
  "second_gate_schema_or_verifier_forbidden": true,
  "owner_attestation_creation_by_agent_allowed": false,
  "github_ruleset_mutation_allowed": false,
  "final_tracked_preflight_required": true,
  "final_tracked_preflight_status_required": "PRE_EXECUTION_AUTHORIZED",
  "final_tracked_preflight_branch_identity_required": true,
  "final_tracked_preflight_self_referential_head_claim_forbidden": true,
  "superseded_pr_close_attempt_limit": 0,
  "superseded_pr_number": 382,
  "superseded_pr_expected_head_sha": "8f9a7c75ac428253669393b420c4b8c36ec29997",
  "superseded_pr_expected_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "superseded_pr_branch_deletion_allowed": false,
  "replay_source_commit": "472bc745d7d53c21d6e3f0dc838ba82122815092",
  "replay_test_commit": "e4dbbcd183d5d7425b4607d9b5046be339bbd944",
  "cherry_pick_no_commit_limit": 2,
  "authorized_cherry_pick_no_commit_commits": [
    "472bc745d7d53c21d6e3f0dc838ba82122815092",
    "e4dbbcd183d5d7425b4607d9b5046be339bbd944"
  ],
  "write_result_false_must_be_fully_side_effect_free": true,
  "bootstrap_expiry_must_be_idempotent_for_same_decision_round": true,
  "bootstrap_expiry_must_rebind_for_different_decision_or_round": true,
  "github_pr_close_allowed": false,
  "superseded_pr_observation_only": true,
  "superseded_pr_reopen_allowed": false,
  "superseded_pr_comment_allowed": false,
  "superseded_pr_review_thread_resolution_allowed": false,
  "premerge_intent_schema_version_required": 3,
  "premerge_attestation_schema_version_required": 3,
  "premerge_schema_version_must_be_non_boolean_integer": true,
  "postmerge_legacy_schema_compatibility_required": true,
  "prebinding_active_must_equal_locked_base_blob": true,
  "prebinding_active_supported_schema_versions": [
    1,
    2,
    3
  ],
  "prebinding_active_must_not_bind_current_decision": true,
  "postbinding_active_schema_version_required": 3,
  "postbinding_active_must_bind_actual_pr_and_current_decision": true,
  "relay_negative_test_external_network_forbidden": true,
  "relay_negative_test_real_loopback_http_required": true,
  "relay_negative_test_sanitized_502_required": true,
  "local_acceptance_test_retry_limit": 0,
  "terminal_v6_local_head": "e4dbbcd183d5d7425b4607d9b5046be339bbd944",
  "terminal_v6_remote_head": "ABSENT",
  "terminal_v6_must_remain_unpublished": true,
  "relay_test_free_port_probe_forbidden": true,
  "relay_test_os_assigned_port_required": true,
  "relay_test_server_shutdown_close_join_required": true,
  "missing_lease_nonempty_body_readable_400_required": true,
  "missing_lease_connection_reset_not_accepted": true,
  "convert_to_draft_attempt_limit": 1,
  "revocation_edit_attempt_limit": 1,
  "pr_close_attempt_limit": 1,
  "issue_comment_attempt_limit": 1,
  "issue_close_attempt_limit": 1,
  "freshness_control_profile": "strict_freshness_control_h",
  "freshness_protected_domains": [
    "reverse_solving",
    "claimed_evidence"
  ],
  "historical_or_missing_freshness_must_block": true,
  "non_claimed_engineering_freshness_nonblocking": true,
  "stale_pr_requires_fresh_base": true,
  "behind_evidence_required": true,
  "must_not_merge_control_pr": true,
  "merge_budget": 0,
  "owner_ready_budget": 1,
  "normal_push_budget": 3,
  "draft_pr_budget": 1,
  "issue370_must_not_merge": true,
  "issue370_behind_closeout_required": true,
  "issue370_behind_closeout_limits": {
    "convert_to_draft": 1,
    "revocation_edit": 1,
    "pr_close": 1,
    "issue_comment": 1,
    "issue_close": 1
  },
  "authority_expiry": "2026-08-28T06:00:00Z"
}
```


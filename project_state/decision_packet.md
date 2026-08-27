# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260827_issue370_strict_freshness_advance_r2_v5",
  "round_id": "round_20260827_issue370_strict_freshness_advance_r2_v5",
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
  "previous_audit_outcome": "ISSUE370_P_INDEPENDENT_PREPARATION_PENDING_CONTROL_H_READY_CLEAN_AT_B",
  "workstream_id": "issue370-strict-freshness-advance-r2-v5",
  "source_issue": 370,
  "parent_issue": 367,
  "integration_base_ref": "main",
  "base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "activation_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "starting_head": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "required_branch": "owner/issue370-strict-freshness-advance-r2-v5",
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
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
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
  "test_semantics_changes_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 0b1f30129fa770f394d7eb6d844fa962ea5a7cde and fresh branch merge-base",
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
      "command_id": "issue370_r2v5.bootstrap_governance",
      "command": "verify locked main B and fresh branch; commit this immutable Decision first; generate five governed gate artifacts; run transition-lint, preflight --mode pre, worktree-publication-readiness, and git diff --check; commit exactly one generated-governance commit; do not push, create a PR, comment, mark ready, merge, or close Issue #370",
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
      "diagnostic_only": false,
      "allowed_only_after_validation": false,
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
      "command_id": "issue370_r2v5.publish_governed_draft",
      "command": "only after an independent server observation proves control H is Ready and CLEAN at locked base B, push the exact named branch at most three times, create exactly one governed Draft PR P against main at B, and update its body at most twice; keep P Draft and do not comment, mark ready, merge, or close Issue #370",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "push",
        "draft_pr",
        "pr_body_update",
        "network_access"
      ],
      "network_access": true,
      "diagnostic_only": false,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": []
    },
    {
      "command_id": "issue370_r2v5.bind_schema3_intent",
      "command": "after actual Draft PR P exists, archive inherited PR382 v7 intent byte-for-byte at project_state/mainline_merge_intents/archive/pr382_v7.json and bind active.json exactly once to P with schema 3, current Decision and command-plan digests, locked base B, baseline workflows, merge method merge, equal_to_accepted_head_tree, and expiry 2026-09-04T23:59:59Z",
      "phase": "post_publication_binding",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "code_read",
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "diagnostic_only": false,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr382_v7.json"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue370_r2v5.final_tracked_preflight",
      "command": "after schema3 binding and its push, read current Draft event facts and run transition-preflight with write_result=true on the exact named branch and supplied Draft event; require PRE_EXECUTION_AUTHORIZED, exact branch identity, zero blockers, and a self-exclusion-safe tracked result; commit only project_state/gates/transition_preflight_result.json as the second generated-governance commit and push once",
      "phase": "final_evidence",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check",
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "diagnostic_only": false,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ]
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
  "reference_paths": [],
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
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_recoveries/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready",
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
    "issue_comment",
    "issue_close",
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
    "create_owner_merge_attestation",
    "modify_issue367_decision",
    "modify_pr382",
    "direct_active_intent_rotation_without_binding",
    "issue370_feature_decision_landing",
    "external_landing_decision_required"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_pr_creation_allowed": true,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_comment_allowed": false,
    "github_pr_close_allowed": false,
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
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
  "ci_network_exceptions": [],
  "issue_close_allowed": false,
  "pr_body_update_attempt_limit": 2,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "landing_revalidation_required_for_actions": [
    "ready_for_review"
  ],
  "landing_revalidation_required_when_draft": false,
  "owner_attestation_required_for_ready_state": true,
  "attestation_head_must_match_current_pr_head": true,
  "ready_state_synchronize_must_revalidate": true,
  "converted_to_draft_returns_to_draft_semantics": true,
  "malformed_event_path_fail_closed": true,
  "bootstrap_expiry_must_be_idempotent_for_same_decision_round": true,
  "bootstrap_expiry_must_rebind_for_different_decision_or_round": true,
  "write_result_false_must_be_fully_side_effect_free": true,
  "final_tracked_preflight_required": true,
  "superseded_pr_observation_only": true,
  "premerge_intent_schema_version_required": 3,
  "prebinding_active_supported_schema_versions": [
    1,
    2,
    3
  ],
  "prebinding_active_must_equal_locked_base_blob": true,
  "postbinding_active_schema_version_required": 3,
  "postbinding_active_must_bind_actual_pr_and_current_decision": true,
  "canonical_schema_v3_raw_hex_intent_required": true,
  "canonical_mainline_landing_validation_reuse_required": true,
  "second_gate_schema_or_verifier_forbidden": true,
  "owner_attestation_creation_by_agent_allowed": false,
  "landing_revalidation_required_when_pr_is_non_draft": true,
  "live_remote_pr_identity_required": true,
  "live_remote_pr_must_match_event": true,
  "live_remote_base_must_match_locked_base": true,
  "github_pr_close_allowed": false,
  "superseded_pr_close_attempt_limit": 0,
  "final_tracked_preflight_status_required": "PRE_EXECUTION_AUTHORIZED",
  "final_tracked_preflight_branch_identity_required": true,
  "final_tracked_preflight_self_referential_head_claim_forbidden": true,
  "external_landing_decision_required": true,
  "feature_decision_landing_allowed": false,
  "control_h_publication_precondition": {
    "required_state": "READY_CLEAN",
    "required_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
    "independent_server_observation_required": true,
    "must_precede_first_push": true,
    "local_preflight_does_not_substitute": true
  },
  "authority_expiry": "2026-08-28T06:00:00Z",
  "intent_expiry": "2026-09-04T23:59:59Z"
}
```


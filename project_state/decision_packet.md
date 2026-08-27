# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260827_issue370_pr389_ready_failure_containment_r2_v1",
  "round_id": "round_20260827_issue370_pr389_ready_failure_containment_r2_v1",
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
  "previous_audit_outcome": "PR389_READY_ATTEMPT_FAILED_STATE_GATE_RUN33045221487_CONTAINMENT_REQUIRED",
  "workstream_id": "issue370-pr389-ready-failure-containment-r2-v1",
  "source_issue": 370,
  "integration_base_ref": "main",
  "base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "activation_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "starting_head": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "required_branch": "owner/issue370-pr389-ready-failure-containment-r2-v1",
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
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
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
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "landing_revalidation_required_for_actions": [
    "ready_for_review"
  ],
  "landing_revalidation_required_when_draft": false,
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
    "verify exact main base 0b1f30129fa770f394d7eb6d844fa962ea5a7cde and fresh containment branch merge-base",
    "commit this immutable R2 containment Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command_id": "issue370_pr389_containment.bootstrap",
      "command": "verify locked main base and fresh PR389 containment branch; commit the immutable Decision as the unique first commit; generate the five governance gates; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
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
      "command_id": "issue370_pr389_containment.readbacks",
      "command": "read back PR389 base head draft merge and failed State Gate run33045221487 attempt1 without mutation",
      "phase": "observation",
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
      "command_id": "issue370_pr389_containment.attestation_revoke",
      "command": "edit existing attestation comment 5435113147 exactly once to revoked with superseded_by containment Decision",
      "phase": "containment",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "pull_request_comment"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_pr389_containment.draft_close",
      "command": "convert PR389 to Draft exactly once and close PR389 unmerged exactly once",
      "phase": "containment",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "convert_to_draft",
        "pull_request_close"
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
    "project_state/gates/transition_preflight_result.json"
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
    ".github/workflows/model-access.yml"
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
    "project_state/mainline_recoveries/**",
    "project_state/mainline_merge_intents/**"
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
    "new_pr",
    "pr_creation",
    "pull_request_comment_create",
    "issue_comment",
    "issue_close",
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
    "branch_delete",
    "ready_pr389",
    "merge_pr389",
    "rerun_state_gate",
    "dispatch_workflow",
    "create_issue370_comment",
    "close_issue370",
    "modify_pr389_source",
    "modify_pr389_tests"
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
    "known_browser_execution_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_comment_allowed": true,
    "github_pr_creation_allowed": false,
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
    }
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "ci_network_exceptions": [
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
  ],
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
  "final_tracked_preflight_required": false,
  "final_tracked_preflight_status_required": "PRE_EXECUTION_AUTHORIZED",
  "final_tracked_preflight_branch_identity_required": true,
  "final_tracked_preflight_self_referential_head_claim_forbidden": true,
  "write_result_false_must_be_fully_side_effect_free": true,
  "bootstrap_expiry_must_be_idempotent_for_same_decision_round": true,
  "bootstrap_expiry_must_rebind_for_different_decision_or_round": true,
  "premerge_intent_schema_version_required": 3,
  "premerge_attestation_schema_version_required": 3,
  "premerge_schema_version_must_be_non_boolean_integer": true,
  "prebinding_active_must_equal_locked_base_blob": true,
  "revocation_edit_attempt_limit": 1,
  "audit_comment_create_attempt_limit": 1,
  "authority_expiry": "2026-08-28T06:00:00Z",
  "draft_pr_body_update_attempt_limit": 0,
  "pull_request_comment_allowed": true,
  "pr_comment_create_limit": 0,
  "pr_comment_edit_limit": 1,
  "issue_comment_allowed": false,
  "issue_close_allowed": false,
  "github_pr_comment_allowed": true,
  "github_pr_close_allowed": true,
  "github_issue_comment_allowed": false,
  "github_issue_close_allowed": false,
  "pr_creation_allowed": false,
  "test_semantics_changes_allowed": false,
  "mainline_merge_intent_required": false,
  "external_authority_only": true,
  "target_pr": 389,
  "target_pr_head_sha": "1cbf79f792578df2e52697cf91d5c432745d2b5c",
  "target_pr_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "failed_state_gate_run_id": "33045221487",
  "failed_state_gate_attempt": 1,
  "failed_state_gate_workflow": "State Gate",
  "failure_root_cause": "attestation intent_digest used file SHA instead of canonical JSON digest",
  "containment_actions": [
    "readbacks",
    "edit existing attestation comment 5435113147 once to revoked/superseded_by containment decision",
    "convert PR389 to Draft once",
    "close PR389 unmerged once"
  ],
  "attestation_comment_id": 5435113147,
  "attestation_edit_limit": 1,
  "convert_to_draft_attempt_limit": 1,
  "pr_close_attempt_limit": 1,
  "issue_comment_attempt_limit": 0,
  "issue_close_attempt_limit": 0
}
```

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260827_issue370_strict_freshness_control_r2_v8",
  "round_id": "round_20260827_issue370_strict_freshness_control_r2_v8",
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
  "previous_audit_outcome": "PR389_V6_FAILED_READY_UNMERGED_INTENT_DIGEST_ENCODING",
  "workstream_id": "issue370-strict-freshness-control-r2-v8",
  "source_issue": 370,
  "integration_base_ref": "main",
  "base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "activation_base_sha": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "starting_head": "0b1f30129fa770f394d7eb6d844fa962ea5a7cde",
  "required_branch": "owner/issue370-strict-freshness-control-r2-v8",
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
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
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
    "verify exact main base 0b1f30129fa770f394d7eb6d844fa962ea5a7cde and fresh strict-freshness-control v8 branch merge-base",
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
      "command_id": "issue370_r2v8.bootstrap",
      "command": "verify locked main base and fresh strict-freshness-control v8 branch; commit the immutable Decision as the unique first commit; generate the five governance gates; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
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
      "command_id": "issue370_r2v8.diff_check",
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
      "command_id": "issue370_r2v8.publish_control_draft",
      "command": "after local acceptance and local canonical intent_digest proof, perform exactly three normal pushes and create exactly one MUST NOT MERGE Draft PR against locked main; do not mark Ready or merge",
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
      "command_id": "issue370_r2v8.bind_schema3_intent",
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
      "command_id": "issue370_r2v8.pre_ready_dry_validation",
      "command": "before any Ready action, run a non-mutating trusted verifier stub against the parsed active intent and attestation, prove canonical_digest with sorted compact JSON rather than file-byte SHA, and perform exactly two exact remote PR readbacks; production Ready State Gate remains decisive",
      "phase": "pre_ready_validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "local_static_check",
        "remote_observation",
        "network_access"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v8.exact_head_checks",
      "command": "after the Draft PR is created, run provider-free exact-head required checks and record their repository-truth result without changing product, source, or test files",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "unit_test",
        "local_static_check"
      ],
      "network_access": false,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v8.audit_attestation_comments",
      "command": "after exact-head checks, create exactly one independent audit comment and one attestation placeholder comment, finalize the attestation once, and revoke once if BEHIND",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "remote_observation",
        "pull_request_comment"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v8.ready_clean_at_b",
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
      "command_id": "issue370_r2v8.behind_revocation_closeout",
      "command": "after another authorized PR advances main, read BEHIND evidence; convert to Draft once, perform one revocation edit, close the unmerged PR once, post one Issue370 evidence comment, and close Issue370 once",
      "phase": "post_main_advance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "network_access",
        "remote_observation",
        "pull_request_comment",
        "issue_comment"
      ],
      "network_access": true,
      "allowed_only_after_validation": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue370_r2v8.final_tracked_preflight",
      "command": "after post-binding exact-head evidence, run transition-preflight with write_result=True on the exact named branch and commit only the final tracked transition_preflight_result.json",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "allowed_only_after_validation": true,
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ],
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json"
      ],
      "required_evidence_source": "local_command_evidence"
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
    "project_state/mainline_recoveries/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
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
    "github_pr_comment_allowed": true,
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
  "intent_digest_encoding_containment_required_before_first_push": true,
  "attestation_intent_digest_required": true,
  "attestation_intent_digest_algorithm": "canonical_digest",
  "attestation_intent_digest_source": "parsed_active_intent",
  "attestation_intent_digest_json_encoding": {
    "sort_keys": true,
    "separators": [
      ",",
      ":"
    ],
    "ensure_ascii": true
  },
  "attestation_intent_digest_must_not_use_file_byte_sha256": true,
  "attestation_intent_digest_local_proof_required_before_finalize": true,
  "attestation_intent_digest_local_proof_required_before_first_push": true,
  "attestation_intent_digest_local_proof": {
    "required": true,
    "phase": "pre_finalize",
    "compares_canonical_digest_of_parsed_active_intent_to_attestation_intent_digest": true,
    "rejects_file_byte_sha256": true
  },
  "pre_ready_dry_validation_required": true,
  "pre_ready_dry_validation_mode": "trusted_verifier_stub",
  "pre_ready_dry_validation_must_be_non_mutating": true,
  "pre_ready_dry_validation_must_precede_ready": true,
  "trusted_verifier_stub_required": true,
  "exact_remote_readbacks_required_before_ready": true,
  "exact_remote_readback_count": 2,
  "exact_remote_readback_fields": [
    "pr_number",
    "head_sha",
    "base_sha",
    "base_ref",
    "draft",
    "mergeable",
    "merge_state_status",
    "required_checks"
  ],
  "production_ready_state_gate_decisive": true,
  "second_gate_schema_or_verifier_forbidden": true,
  "owner_attestation_creation_by_agent_allowed": false,
  "final_tracked_preflight_required": true,
  "prior_failed_ready_unmerged_observation": {
    "decision_id": "decision_20260827_issue370_strict_freshness_control_r2_v6",
    "round_id": "round_20260827_issue370_strict_freshness_control_r2_v6",
    "remote_pr": 389,
    "status": "FAILED_READY_UNMERGED",
    "reason": "attestation intent_digest used file-byte SHA instead of canonical_digest(parsed active intent)",
    "containment_required_before_first_push": true
  },
  "final_tracked_preflight_status_required": "PRE_EXECUTION_AUTHORIZED",
  "final_tracked_preflight_branch_identity_required": true,
  "final_tracked_preflight_self_referential_head_claim_forbidden": true,
  "write_result_false_must_be_fully_side_effect_free": true,
  "bootstrap_expiry_must_be_idempotent_for_same_decision_round": true,
  "bootstrap_expiry_must_rebind_for_different_decision_or_round": true,
  "github_pr_close_allowed": true,
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
  "draft_pr_body_update_attempt_limit": 2,
  "convert_to_draft_attempt_limit": 1,
  "revocation_edit_attempt_limit": 1,
  "pr_close_attempt_limit": 1,
  "issue_comment_attempt_limit": 1,
  "issue_close_attempt_limit": 1,
  "audit_comment_create_attempt_limit": 1,
  "issue_close_allowed": true,
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
  "issue370_must_not_merge": true,
  "issue370_behind_closeout_required": true,
  "issue370_behind_closeout_limits": {
    "convert_to_draft": 1,
    "revocation_edit": 1,
    "pr_close": 1,
    "issue_comment": 1,
    "issue_close": 1
  },
  "unpublished_rejected_observations": [
    {
      "decision_id": "decision_20260827_issue370_strict_freshness_control_r2_v2",
      "round_id": "round_20260827_issue370_strict_freshness_control_r2_v2",
      "status": "REJECTED_UNPUBLISHED",
      "remote_pr": null,
      "reason": "prior local contract conflict; no remote publication"
    },
    {
      "decision_id": "decision_20260827_issue370_strict_freshness_control_r2_v4",
      "round_id": "round_20260827_issue370_strict_freshness_control_r2_v4",
      "status": "REJECTED_UNPUBLISHED",
      "remote_pr": null,
      "reason": "unrelated legacy fields and noncanonical budget names; no remote publication"
    },
    {
      "decision_id": "decision_20260827_issue370_strict_freshness_advance_r2_v3",
      "round_id": "round_20260827_issue370_strict_freshness_advance_r2_v3",
      "status": "REJECTED_UNPUBLISHED",
      "remote_pr": null,
      "reason": "advance preparation rejected before remote publication"
    },
    {
      "decision_id": "decision_20260827_issue370_strict_freshness_advance_r2_v5",
      "round_id": "round_20260827_issue370_strict_freshness_advance_r2_v5",
      "status": "REJECTED_UNPUBLISHED",
      "remote_pr": null,
      "reason": "advance preparation rejected before remote publication"
    }
  ],
  "authority_expiry": "2026-08-28T06:00:00Z",
  "pr_comment_create_limit": 2,
  "pr_comment_edit_limit": 2,
  "audit_comment_create_limit": 1,
  "attestation_placeholder_create_limit": 1,
  "attestation_finalize_edit_limit": 1,
  "attestation_revoke_edit_limit": 1,
  "github_pr_comment_allowed": true,
  "github_issue_comment_allowed": true,
  "github_issue_close_allowed": true,
  "test_semantics_changes_allowed": false
}
```

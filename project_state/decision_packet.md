# Decision Packet — #721 safe non-overlap base refresh current-main v9

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260918_issue721_safe_base_refresh_r2_v9_current",
  "round_id": "round_20260918_issue721_safe_base_refresh_r2_v9_current",
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
  "decision_scope": "SAFE_BASE_REFRESH_REAL_READY_ROUTE_AND_LIVE_MAIN_R2_V9",
  "follows_last_decision_id": "decision_20260918_issue721_safe_base_refresh_r2_v8_current",
  "follows_last_round_id": "round_20260918_issue721_safe_base_refresh_r2_v8_current",
  "previous_audit_outcome": "V6_PR946_CLOSED_REVIEW_NEGATIVE_SAFE_REFRESH_CORE_UNREACHABLE_BEFORE_PROJECT_GATE_BASE_MISMATCH;V7_LOCAL_SCOPE_INSUFFICIENT_NO_SEMANTIC_COMMIT_OR_PUBLICATION;V8_IMMUTABLE_DECISION_PREFLIGHT_BLOCKED_ALLOWED_REFERENCE_PATH_CONFLICT_NO_SEMANTIC_COMMIT_OR_PUBLICATION;V9_PREACTIVATION_AUDIT_CAUGHT_STALE_COPIED_AUTHORITY_FIELDS_BEFORE_DECISION_COMMIT",
  "workstream_id": "issue721-safe-base-refresh-r2-v9-current",
  "source_issue": 721,
  "parent_issue": 156,
  "migration_fixture_issue": 664,
  "mother_roadmap": 137,
  "parent_issue_must_not_be_migration_fixture_issue": true,
  "integration_base_ref": "main",
  "base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "activation_base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "starting_head": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "required_branch": "owner/issue721-safe-base-refresh-r2-v9-current",
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
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "post_publication_binding_commit_limit": 0,
  "commit_order_contract": [
    "D_decision_only_on_clean_tree",
    "startup_snapshot",
    "transition_command_plan",
    "transition_lint",
    "transition_preflight_pre",
    "worktree_publication_readiness",
    "S_semantic_implementation_only"
  ],
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
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
  "landing_authority_scope_note": "Only the exact mainline_landing.py base refresh validation and its test suite are authorized. No dependency, framework, workflow, frontend, database/schema, scheduler, or AGENTS.md mutation is authorized. No merge, Ready, auto-merge, direct main push, rebase, squash, amend, force push, workflow rerun, workflow dispatch, release, deploy or tag is authorized here. Final Ready/Merge requires a separate independent Owner landing authority.",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "source_test_mutation_authorized": true,
  "source_test_mutation_scope": "SAFE_REFRESH_CORE_PLUS_REAL_READY_ROUTE_AND_LIVE_MAIN_REF_VERIFICATION",
  "startup_source_test_clean_start_required": true,
  "startup_snapshot_must_show_empty_raw_git_status_short": true,
  "startup_snapshot_must_not_show_primary_worktree_path": true,
  "migration_fixture_664_required": true,
  "migration_fixture_664_target_head": "f72c5f1c5307cf8655715269687541ead8ead180",
  "migration_fixture_664_workflow_blob": "0360c23a3821c38b18f6e0d6abf85ac0531ff08c",
  "migration_fixture_664_workflow_path": ".github/workflows/tauri-desktop-check.yml",
  "migration_fixture_664_byte_binding_required": true,
  "migration_fixture_664_positive_gate_status_required": "PASSED",
  "migration_fixture_664_must_distinguish_historical_evidence_identity_from_synthetic_execution_identity": true,
  "historical_negative_authority": {
    "pr730": "1d55f60de99ab9b0e8f715babbb1487fe8f9e9b8",
    "pr730_disposition": "CLOSED_UNMERGED_R2_V3_TERMINAL_NEGATIVE_AUTHORITY_ONLY",
    "pr726": "160a0e49069e77ae09b97403db8f94fadc9cb54d",
    "pr726_disposition": "CLOSED_UNMERGED_R2_V2_TERMINAL_NEGATIVE_AUTHORITY_ONLY",
    "issue721_r2_v1_branch": "owner/issue721-safe-base-refresh-r2-v1",
    "issue721_r2_v1_disposition": "CLOSED_UNMERGED_TERMINAL_NEGATIVE_AUTHORITY_ONLY",
    "issue721_r2_v2_branch": "owner/issue721-safe-base-refresh-r2-v2",
    "issue721_r2_v2_branch_sha": "160a0e49069e77ae09b97403db8f94fadc9cb54d",
    "issue721_r2_v2_disposition": "CLOSED_UNMERGED_R2_V2_TERMINAL_NEGATIVE_AUTHORITY_ONLY",
    "issue721_r2_v3_branch": "owner/issue721-safe-base-refresh-r2-v3",
    "issue721_r2_v3_branch_sha": "1d55f60de99ab9b0e8f715babbb1487fe8f9e9b8",
    "issue721_r2_v3_disposition": "CLOSED_UNMERGED_R2_V3_TERMINAL_NEGATIVE_AUTHORITY_ONLY",
    "issue721_r2_v4_local_decision": "c102ede49f363593037aa3eaf2f7e8587f629507",
    "issue721_r2_v4_local_governance": "9a93525784732ce3d9892c255d827f7b180e1bfa",
    "issue721_r2_v4_local_semantic_head": "adad1fbb98e9767e13fa53c93c118c6f0cf9d501",
    "issue721_r2_v4_base_sha": "fb34873b48d3f8aa9387598f05cc7453e32f7707",
    "issue721_r2_v4_publication": "NONE",
    "issue721_r2_v4_disposition": "LOCAL_VALIDATED_UNPUBLISHED_R2_V4_SEMANTIC_EVIDENCE",
    "pr730_rejection_reasons": [
      "SOURCE_TEST_DIRTY_BEFORE_BOOTSTRAP",
      "FRESH_WORKTREE_CONTRACT_VIOLATED",
      "DECISION_AUTHORITY_METADATA_DRIFT",
      "REQUIREMENTS_GLOB_UNDERMATCH",
      "MIGRATION_FIXTURE_FALSE_PROOF"
    ],
    "pr726_rejection_reasons": [
      "MISSING_SKILL_PROFILES",
      "INCOMPLETE_DEPENDENCY_MANIFEST_LOCKFILE_POLICY",
      "INCOMPLETE_REFRESH_NEGATIVE_MATRIX",
      "GOVERNANCE_EVIDENCE_PROVENANCE_MISMATCH"
    ],
    "no_reuse_no_rebase_no_force_update": true,
    "no_cherry_pick_no_amend_no_squash": true,
    "no_commit_transplant_no_patch_series_history_reuse": true,
    "v3_read_only_negative_evidence_only": true,
    "v4_local_validated_unpublished_semantic_evidence_only": true,
    "no_v6_auto_creation": true,
    "main_drift_before_v5_push": "PR729_FRONTEND_SCOPE_ONLY_NO_OVERLAP_WITH_ISSUE721",
    "pr946_v6": "4a6d9b6b2b3c4184b866b53f5f6654f88d4acc6e",
    "pr946_v6_disposition": "CLOSED_UNMERGED_REVIEW_NEGATIVE_CORE_UNREACHABLE_AT_PROJECT_GATE_BASE_CHECK",
    "v7_decision": "8e66beadd0a628ec0732af1da3e2a636cd3f7943",
    "v7_disposition": "LOCAL_SCOPE_INSUFFICIENT_NO_SEMANTIC_COMMIT_OR_PUBLICATION",
    "v8_decision": "dc0b0844aec04921479c82abcb93bf7b8369a4f7",
    "v8_disposition": "TERMINAL_PREFLIGHT_ALLOWED_REFERENCE_PATH_CONFLICT_NO_SEMANTIC_COMMIT_OR_PUBLICATION"
  },
  "dependency_manifest_policy": {
    "principle": "dependency_resolution_drift_during_base_refresh_fails_closed",
    "matching_semantics": "basename_exact_plus_deterministic_case_sensitive_basename_glob_via_fnmatchcase_after_lowercasing_basename",
    "no_endswith_suffix_heuristic": true,
    "no_endswith_requirements_token": true,
    "basename_only_so_nested_and_root_variants_are_equivalent": true,
    "conservative_over_blocking_accepted": true,
    "exact_basenames": [
      "pyproject.toml",
      "requirements.txt",
      "uv.lock",
      "poetry.lock",
      "Pipfile",
      "Pipfile.lock",
      "package.json",
      "package-lock.json",
      "pnpm-lock.yaml",
      "yarn.lock",
      "Cargo.toml",
      "Cargo.lock"
    ],
    "basename_globs": [
      "requirements*.txt",
      "requirements-*.txt"
    ],
    "must_block_examples": [
      "pyproject.toml",
      "requirements.txt",
      "requirements-dev.txt",
      "requirements-test.txt",
      "requirements-ci.txt",
      "frontend/requirements-dev.txt",
      "uv.lock",
      "poetry.lock",
      "Pipfile",
      "Pipfile.lock",
      "package.json",
      "package-lock.json",
      "pnpm-lock.yaml",
      "yarn.lock",
      "Cargo.toml",
      "Cargo.lock"
    ],
    "must_not_match_examples": [
      "notes/requirements",
      "notes/requirements-",
      "requirements-notes.md",
      "docs/requirements-review.md",
      ".github/workflows/tauri-desktop-check.yml"
    ],
    "workflow_yaml_parsing_for_dependency_inference_forbidden": true
  },
  "git_object_validation": {
    "principle": "explicit_cat_file_before_ancestry_diff_merge_tree",
    "command": "git cat-file -e <sha>^{commit}",
    "required_objects": [
      "original_locked_base",
      "refreshed_base",
      "accepted_exact_target_head"
    ],
    "abbreviated_ambiguous_shas_forbidden": true,
    "sha1_40_hex_required": true,
    "non_commit_object_must_fail": true,
    "missing_object_must_fail": true
  },
  "refresh_security_properties": [
    "exact_40_hex_commit_validation",
    "git_cat_file_e_commit_object_check",
    "original_base_ancestry_of_refreshed_base",
    "machine_computed_original_target_paths",
    "machine_computed_original_refreshed_main_paths",
    "authority_sensitive_path_blocking",
    "dependency_control_path_blocking",
    "exact_accepted_target_head_binding",
    "target_decision_digest_binding",
    "owner_exact_head_review_binding",
    "fresh_authority_sidecar_binding",
    "current_main_redrift_blocking",
    "git_merge_tree_write_tree",
    "merge_conflict_blocking",
    "merge_tree_identity_comparison",
    "ordinary_merge_only",
    "expected_head_protection",
    "strict_legacy_locked_base_when_refresh_authority_absent"
  ],
  "refresh_negative_matrix": {
    "N1_target_overlap": "intervening_main_touches_target_semantic_path_must_block",
    "N2_authority_sensitive_drift": "github_project_state_landing_governance_drift_must_block",
    "N2_dependency_manifest_drift": "dependency_manifest_or_lockfile_drift_including_requirements-dev-txt_must_block",
    "N3_target_head_drift": "accepted_target_head_must_not_drift",
    "N4_decision_drift": "target_decision_bytes_or_digest_must_not_drift",
    "N5_ancestry_failure": "original_locked_base_must_be_ancestor_of_refreshed_base",
    "N6_main_redrift": "refresh_authority_base_must_match_final_landing_base",
    "N7_merge_conflict": "real_git_merge_conflict_must_block",
    "N8_merge_tree_mismatch": "clean_merge_but_different_expected_tree_must_block",
    "N9_invalid_object": "missing_non_commit_or_abbreviated_git_object_must_block",
    "N10_history_rewrite": "reauthored_target_cannot_bypass_exact_head_binding"
  },
  "fresh_worktree_contract": {
    "creation_required": true,
    "source_commit": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
    "source_ref": "origin/main",
    "target_branch": "owner/issue721-safe-base-refresh-r2-v9-current",
    "worktree_path": "F:/reverse-agent-issue721-r2-v9-current",
    "primary_worktree_path_forbidden": "F:/reverse-agent",
    "v4_worktree_path_forbidden": "F:/reverse-agent-issue721-r2-v4",
    "worktree_must_be_distinct_from_primary": true,
    "worktree_must_be_distinct_from_v4": true,
    "no_switch_no_reset_no_stash_no_clean_no_restore_primary_worktree": true,
    "clean_status_required_at_activation": true,
    "no_source_test_dirty_before_decision_bootstrap_preflight": true,
    "no_switch_no_reset_no_stash_no_clean_other_worktree": true
  },
  "semantic_implementation_contract": {
    "specification": "Preserve the v6 safe-refresh core and landed #891 ordinary/formal Ready role split, then make refresh reachable on the real cutover route without weakening strict behavior. Legacy intent mode and cutover without a complete refresh authority remain strict locked-base. In cutover, remote PR head/base/draft must bind the Ready event. A thin GitHubRemoteAcceptanceVerifier ref-SHA method must prove the event base is still live heads/main. Ordinary state-gate may perform only generic/live-main candidate validation and must not consume or authorize Owner attestation. Formal landing-state-gate is the sole premerge Owner-attestation validator and, when landing base differs from original locked base, must require one complete refresh block and run the full #721 base-refresh validator. Partial/malformed/wrong refresh evidence, live-main redrift, wrong original/refreshed base, target drift, authority-sensitive/dependency drift, merge conflict/tree mismatch, or missing object fail closed. Same-base no-refresh behavior remains unchanged.",
    "execution_surface_note": "Decision/source/test/commit run only in this clean isolated v9 trusted_worker checkout. Generated gate files are ephemeral with zero commit budget. Remote Decision/semantic commit graph, branch ref and Draft PR are created only through github_control_plane; local git push is forbidden. The verifier addition reuses the existing urllib REST transport and Python stdlib only.",
    "completion_boundary": "One immutable v9 Decision commit plus one semantic commit and one Draft PR. No generated-governance commit, local git push, Ready, Merge, rerun, dispatch, rebase or history rewrite."
  },
  "main_drift_checkpoints": [
    "immediately_before_decision_commit",
    "immediately_before_github_control_plane_branch_ref_creation",
    "immediately_before_draft_pr_creation"
  ],
  "main_drift_locked_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "main_drift_must_fail_closed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "issue721v9.bootstrap",
      "command": "Verify exact clean isolated v9 current-main checkout and immutable Decision. Run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Generated gates are ephemeral and uncommitted. Require PRE_EXECUTION_AUTHORIZED before semantic mutation.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue721v9.implement",
      "command": "After PRE_EXECUTION_AUTHORIZED rematerialize the validated v6 safe-refresh core in mainline_landing/test_mainline_landing, then add only the minimum project_gate live-main refresh routing, GitHubRemoteAcceptanceVerifier ref-SHA check over the existing REST transport, and focused production-route regressions in test_project_gate. Preserve the landed #891 ordinary/formal job split. No cherry-pick/rebase/history reuse. Commit exactly once.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "reverse_agent/project_gate.py",
        "reverse_agent/github_remote_verifier.py",
        "tests/test_mainline_landing.py",
        "tests/test_project_gate.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v9.validate",
      "command": "Run full tests/test_mainline_landing.py, focused project_gate false-none/landing-authority/base-refresh route regressions, verifier ref-SHA regressions, git diff --check, and post-semantic transition preflight/readiness. Natural exact-head CI/Decision Preflight/State Gate are mandatory final validation.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "local_static_check",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v9.publish",
      "command": "Through github_control_plane only create the exact v9 Decision then semantic commit graph, branch owner/issue721-safe-base-refresh-r2-v9-current, and one Draft PR against main@ef8bb6959ac37301c880e0971a97a9d56e9c99a9. No local git push, Ready or Merge.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v9.observe",
      "command": "Fresh-read exact base/head/trees, natural Actions, and Owner-audit real Ready routing, live-main redrift handling, #891 role separation, N1-N10 and #664 positive fixture. No Ready/Merge.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "code_read",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "reference_paths": [
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/command_authority.py",
    ".github/workflows/state-gate.yml",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "tests/platform_v1/test_merge_intent.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/command_authority.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "tests/platform_v1/test_merge_intent.py",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/tauri-desktop-check.yml"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "**/.env",
    "**/secrets/**",
    ".codex-skills/**",
    ".github/**",
    "AGENTS.md",
    "Cargo.lock",
    "Cargo.toml",
    "Pipfile",
    "Pipfile.lock",
    "README.md",
    "README.txt",
    "docs/**",
    "frontend/**",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "requirements-*.txt",
    "reverse_agent/control_plane/**",
    "tests/platform_v1/**",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "uv.lock",
    "yarn.lock"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
    "amend",
    "amend_after_validation",
    "auth_store_read",
    "auto_merge",
    "cherry_pick",
    "clean",
    "commit_transplant",
    "compute_and_ignore_blob_identity",
    "continue_push_v1",
    "continue_push_v2",
    "continue_push_v3",
    "continue_push_v4",
    "create_v6_automatically",
    "credential_access",
    "database_schema_change",
    "dependency_install",
    "deployment",
    "destructive_delete",
    "direct_push_main",
    "endswith_requirements_suffix_heuristic",
    "false_positive_migration_fixture_proof",
    "force_push",
    "force_update_v1",
    "force_update_v2",
    "force_update_v3",
    "force_update_v4",
    "generated_governance_commit",
    "gitpython",
    "history_rewrite",
    "implicit_user_local_fallback",
    "literal_expected_blob_assertion_only",
    "local_authoring",
    "mark_ready",
    "merge",
    "merge_queue_integration",
    "merge_v3",
    "model_api_invocation",
    "new_dependency",
    "new_framework",
    "new_github_client",
    "new_landing_scheduler",
    "new_workflow",
    "pass_or_blocked_status_acceptance",
    "patch_series_history_reuse",
    "primary_worktree_authoring",
    "privileged_remote_execution",
    "product_replay",
    "provider_network_call",
    "pygit2",
    "rebase",
    "rebase_v1",
    "rebase_v2",
    "rebase_v3",
    "rebase_v4",
    "reopen_v1",
    "reopen_v2",
    "reopen_v3",
    "reopen_v4",
    "required_check_weakening",
    "reset",
    "reset_to_v3",
    "reset_to_v4",
    "restore",
    "reuse_v1_decision",
    "reuse_v2_decision",
    "reuse_v3_decision",
    "reuse_v4_decision",
    "ruleset_weakening",
    "runner_dispatch",
    "second_command_runner",
    "second_decision_commit",
    "secrets",
    "source_test_dirty_before_bootstrap",
    "squash",
    "squash_after_validation",
    "startupsnapshot_general_bug_fix",
    "stash",
    "tag_or_release",
    "target_branch_push",
    "unknown_binary_execution",
    "v4_worktree_authoring",
    "workflow_dispatch",
    "workflow_rerun",
    "workflow_yaml_parsing_for_dependency_inference"
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
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Create only the v9 Decision/semantic commit graph and branch owner/issue721-safe-base-refresh-r2-v9-current in dddd2024/Nerelan, then one Draft PR against main@ef8bb6959ac37301c880e0971a97a9d56e9c99a9; comment only on Issue721/156 and that Draft; never Ready/Merge."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/project_gate.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/github_remote_verifier.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/test_mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/test_project_gate.py",
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
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "owner/issue721-safe-base-refresh-r2-v9-current",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  },
  "fresh_base": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "current_main_expected": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "workflow_dispatch_limit": 0,
  "workflow_dispatch_allowed": false,
  "provider_free_acceptance_required": true,
  "current_main_coupling": {
    "landed_prerequisite_issue": 891,
    "landed_prerequisite_pr": 943,
    "landed_prerequisite_merge": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
    "landed_prerequisite_state_gate_run": 35321470706,
    "false_none_attestation_premerge_semantics_must_remain_unchanged": true,
    "project_gate_refresh_routing_mutation_authorized": true,
    "project_gate_role_split_semantics_must_be_preserved": true,
    "ordinary_state_gate_must_not_consume_owner_attestation": true,
    "formal_landing_state_gate_remains_attestation_validator": true
  },
  "issue_completion_close_allowed": [],
  "mother_roadmap_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User delegated repository Owner execution, self-audit, and trusted-worker access via Remote Desktop Commander. Fresh current-main audit confirms #891 is landed and machine-green, PR946 v6 safe-refresh core is reusable but unreachable, v7 proved the five-file route scope is required, and v8 correctly failed before semantic mutation because copied reference-only roles conflicted with newly writable paths. V9 performs a pre-activation recursive authority consistency pass, then authorizes only the minimum five-file route/verifier/test correction on current main.",
  "supersedes_decision_id": "decision_20260918_issue721_safe_base_refresh_r2_v8_current",
  "superseded_evidence": "V8 Decision dc0b0844aec04921479c82abcb93bf7b8369a4f7 is immutable terminal local authority evidence. Startup/plan/lint passed but transition-preflight BLOCKED on allowed_reference_path_conflict for the newly writable project_gate/github_remote_verifier/test_project_gate paths. V8 had no semantic commit and no remote publication. V9 is fresh current-main authority only; no V8 history reuse.",
  "startup_snapshot_must_show_isolated_current_worktree_path": true
}
```

## Goal

Make #721 safe non-overlap base refresh reachable and fail-closed on the real landed #891 Ready route, including fresh live-main verification, without weakening strict legacy/no-refresh behavior.

## Build vs reuse

Reuse the v6 safe-refresh core, landed #891 role split, current GitHubRemoteAcceptanceVerifier REST transport, system Git and git merge-tree. Add only a thin live-ref verifier and minimal routing glue. No scheduler, queue, new GitHub client, Git library, workflow, dependency, database or schema.

## Stop conditions

Stop on main/base drift, Decision mutation, source/test dirty before bootstrap, failed preflight, scope expansion, #891 role regression, incomplete refresh authority acceptance, live-main redrift false-pass, test/check failure, publication-surface mismatch or exhausted budget. Generated gate evidence may be regenerated but never committed. No Ready/Merge under this Decision.

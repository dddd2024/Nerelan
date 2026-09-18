# Decision Packet — PR939 Owner landing authority v1

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260918_issue940_pr939_owner_landing_r2_v1",
  "round_id": "round_20260918_issue940_pr939_owner_landing_r2_v1",
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
  "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR",
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "repository": "dddd2024/Nerelan",
  "source_issue": 940,
  "parent_issue": 891,
  "target_pr": 939,
  "source_pr": 939,
  "target_branch": "owner/issue891-false-none-attestation-r2-v4-api",
  "accepted_exact_head_sha": "36bb532126c3ca830bb59155625d2ea012050fcb",
  "owner_exact_head_review_id": 5244478744,
  "owner_exact_head_review_commit": "36bb532126c3ca830bb59155625d2ea012050fcb",
  "target_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v4",
  "target_round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v4",
  "target_ci_run_id": 35309810630,
  "target_decision_preflight_run_id": 35309810812,
  "target_state_gate_run_ids": [
    35309810720
  ],
  "target_pre_ready_state_gate_run_id": 35309810720,
  "base_sha": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "activation_base_sha": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "starting_head": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "fresh_base": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "current_main_expected": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "integration_base_ref": "main",
  "required_branch": "owner/issue940-pr939-owner-landing-r2-v1-clean",
  "follows_last_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v4",
  "follows_last_round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v4",
  "workstream_id": "issue940-pr939-owner-landing-r2-v1",
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
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "approval_basis": "The user explicitly delegated repository Owner execution. Target PR939 exact head has natural CI #1333, Decision Preflight #542 and State Gate #3236 SUCCESS plus Owner exact-head audit review 5244478744. This Decision authorizes only bounded landing through the existing false/none Owner-attestation path.",
  "landing_authority_scope_note": "Governance-only Decision-only sidecar for PR939 exact head 36bb532126c3ca830bb59155625d2ea012050fcb at locked main 3ec2235d583c92c71077aae3751e3216d5bcd94c. Sidecar remains Draft/unmerged forever. Require natural sidecar CI/Decision Preflight/State Gate SUCCESS, then one existing-format pre-Ready OWNER_LANDING_MERGE_ATTESTATION, one Ready transition, natural formal landing-state-gate SUCCESS, fresh no-drift revalidation, one expected-head ordinary merge, and a new natural main-push State Gate SUCCESS.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "36bb532126c3ca830bb59155625d2ea012050fcb"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35309810720,
    "required_status_contexts": [
      "baseline",
      "state-gate",
      "landing-state-gate"
    ],
    "pre_ready_completed_contexts": [
      "baseline",
      "state-gate"
    ],
    "formal_landing_context_completed_only_after_ready": "landing-state-gate",
    "exactly_one_active_matching_attestation_required": true,
    "post_hoc_after_merge_allowed": false
  },
  "activation_acceptance_contract": {
    "pre_execution_authorization_required": true,
    "generated_governance_commit_required": false,
    "sidecar_natural_ci_decision_preflight_state_gate_success_required": true,
    "no_rerun_or_noop_commit": true
  },
  "required_landing_sequence": [
    "require natural sidecar CI Decision Preflight and State Gate terminal SUCCESS with no rerun or dispatch",
    "fresh-read main target PR target head review threads Ruleset and target checks and require no drift",
    "while PR939 remains Draft publish exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target, exact unmerged sidecar authority, Owner audit review 5244478744, target State Gate run 35309810720, Ruleset and canonical contexts",
    "re-read target comments and require exactly one active matching canonical attestation before Ready",
    "mark PR939 Ready exactly once",
    "require the naturally triggered formal landing-state-gate SUCCESS on exact target head 36bb532126c3ca830bb59155625d2ea012050fcb",
    "fresh-read main target head sidecar attestation review threads Ruleset and required checks and require no drift",
    "merge PR939 exactly once with method merge and expected head 36bb532126c3ca830bb59155625d2ea012050fcb",
    "verify merged state and new main head",
    "require the new natural main-push State Gate SUCCESS without rerun",
    "only then close Issue891/Issue940 and reactivate/reconcile Issue721"
  ],
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/command_authority.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "docs/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
    "amend",
    "auto_merge",
    "credential_access",
    "dependency_install",
    "destructive",
    "direct_push_main",
    "external_reverse_tool_invocation",
    "force_push",
    "generated_governance_commit",
    "history_rewrite",
    "model_api_invocation",
    "post_hoc_attestation_after_target_merge",
    "provider_network_call",
    "rebase",
    "runner_dispatch",
    "second_attestation_family",
    "sidecar_pr_ready_or_merge",
    "squash",
    "tag_or_release",
    "target_branch_push",
    "unknown_binary_execution",
    "workflow_dispatch",
    "workflow_rerun"
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Create only owner/issue940-pr939-owner-landing-r2-v1-clean in dddd2024/Nerelan with one Decision commit and one Draft sidecar PR against exact main@3ec2235d583c92c71077aae3751e3216d5bcd94c; keep sidecar Draft/unmerged.",
      "After sidecar natural checks and fresh no-drift validation, post exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION on PR939 while Draft, binding exact target 36bb532126c3ca830bb59155625d2ea012050fcb, base 3ec2235d583c92c71077aae3751e3216d5bcd94c, target Decision, exact sidecar authority/runs, Owner review 5244478744, target State Gate 35309810720, Ruleset 21023698 and canonical contexts.",
      "Then mark PR939 Ready at most once; require natural formal landing-state-gate SUCCESS; fresh-read again; merge PR939 at most once with method merge and expected head 36bb532126c3ca830bb59155625d2ea012050fcb; verify new main and observe new natural main-push State Gate. Never rerun/dispatch."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue940v1.bootstrap",
      "command": "On a fresh exact-main trusted checkout validate this immutable Decision with startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Generated gate files are ephemeral evidence only and must not be committed.",
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
      "command_id": "issue940v1.publish",
      "command": "Through github_control_plane only create the Decision commit/ref owner/issue940-pr939-owner-landing-r2-v1-clean and exactly one Draft sidecar PR against 3ec2235d583c92c71077aae3751e3216d5bcd94c; no local git push and never Ready/Merge the sidecar.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue940v1.validate",
      "command": "Require natural sidecar CI Decision Preflight State Gate SUCCESS and fresh target PR939 exact base/head/Draft/checks/Owner review/Ruleset/thread state with no drift.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue940v1.attest",
      "command": "While PR939 remains Draft publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION with canonical digest binding target and sidecar evidence; re-read and require exactly one active matching candidate.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "pull_request_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue940v1.land_target",
      "command": "After valid pre-Ready attestation, mark PR939 Ready once; after separate remote observation proves natural formal landing-state-gate SUCCESS and no drift, merge once by method merge with expected head 36bb532126c3ca830bb59155625d2ea012050fcb.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready",
        "merge",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue940v1.observe",
      "command": "Fresh-read target, sidecar, main, attestation, Ruleset, review threads and natural checks before merge; after merge verify merged state, new main and a new natural main-push State Gate SUCCESS. Never rerun or dispatch.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "target_decision_content_sha256": "6777555810f9493ce4b7bc508a11d001687e49c7c8bb8e6584bdcfd91bc31187"
}
```

## Goal

Land PR #939 exactly once under existing false/none Owner landing authority, with pre-Ready attestation, natural formal landing-state-gate, expected-head merge, and new main-push State Gate success.

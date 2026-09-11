# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260911_issue815_pr810_owner_landing_r2_v1",
  "round_id": "round_20260911_issue815_pr810_owner_landing_r2_v1",
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
  "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR_FALSE_NONE",
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 810,
  "source_pr": 810,
  "target_branch": "codex/f02-accepted-artifact-handoff-r2-v5",
  "accepted_exact_head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416",
  "base_sha": "2a1239b1230461f3f43fd86bb8edd0915552e1a2",
  "activation_base_sha": "2a1239b1230461f3f43fd86bb8edd0915552e1a2",
  "starting_head": "2a1239b1230461f3f43fd86bb8edd0915552e1a2",
  "fresh_base": "2a1239b1230461f3f43fd86bb8edd0915552e1a2",
  "current_main_expected": "2a1239b1230461f3f43fd86bb8edd0915552e1a2",
  "integration_base_ref": "main",
  "required_branch": "codex/pr810-owner-landing-r2-v1",
  "source_issue": 815,
  "parent_issue": 799,
  "trigger_issue": 799,
  "trigger_pr": 810,
  "owner_exact_head_review_id": 5180621815,
  "owner_exact_head_review_commit": "028a5962b1319c6b66160665d79ebb4fd214f416",
  "target_decision_content_sha256": "64bd7ce4c39d1d840b5fa660de89da113d9515b481a7d54dc18ae6e28e61ec71",
  "follows_last_decision_id": "decision_20260911_issue799_artifact_handoff_r2_v5",
  "follows_last_round_id": "round_20260911_issue799_artifact_handoff_r2_v5",
  "previous_audit_outcome": "PR810_EXACT_HEAD_028a5962b1319c6b66160665d79ebb4fd214f416_DISCLOSED_CODEX_SELF_AUDIT_ACCEPTED_OWNER_REVIEW_5180621815",
  "workstream_id": "issue815-pr810-owner-landing-r2-v1",
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
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "expected_total_new_commits_from_locked_main": 2,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 2,
  "successful_branch_publication_limit": 1,
  "successful_draft_pr_creation_limit": 1,
  "transport_retry_allowed": true,
  "transport_retry_requires_confirmed_no_remote_mutation": true,
  "transport_retryable_failure_classes": [
    "TLS_FAILURE",
    "EOF",
    "CONNECTION_RESET",
    "TIMEOUT"
  ],
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "expected_head_protection_required": true,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "OWNER_LANDING_AUTHORITY_SIDECAR",
  "landing_authority_scope_note": "Validation-only / landing-authority-only sidecar v1 for PR #810. This immutable R2 Decision binds target_pr=810, source_pr=810, target_branch=codex/f02-accepted-artifact-handoff-r2-v5, accepted_exact_head_sha=028a5962b1319c6b66160665d79ebb4fd214f416, base_sha=2a1239b1230461f3f43fd86bb8edd0915552e1a2, integration_base_ref=main. It grants the Owner exactly-once Mark Ready and exactly-one expected-head protected regular merge of PR #810 using merge method merge, only after the natural target Ready-triggered landing-state-gate reports terminal SUCCESS on the unchanged exact target head 028a5962b1319c6b66160665d79ebb4fd214f416 with contexts baseline=success, state-gate=success, landing-state-gate=success. The sidecar authority PR itself must remain Draft forever and must never be marked Ready or merged. mainline_merge_intent_required=false + active_pr_binding_mode=none is the false/none cutover contract; project_state/mainline_merge_intents/active.json is never read or rewritten and active_json_rewrite is forbidden. No target-branch push, no target semantic mutation, no workflow rerun or dispatch, no runner dispatch, no direct main push, no auto-merge, no force push and no rebase. Publication retry accounting: maximum 3 total push invocations and 2 total PR-create invocations; transport failures consume an attempt; retry only if read-only remote observation proves no remote mutation occurred. Owner actions in this round are explicitly delegated to Codex by the user and must be disclosed as agent actions. No independent human review is claimed.",
  "false_none_invariants_preserved": {
    "mainline_merge_intent_required": false,
    "active_pr_binding_mode": "none",
    "active_json_rewrite_forbidden": true,
    "mainline_merge_intents_mutation_forbidden": true
  },
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "mark_ready_attempt_limit": 1,
    "merge_attempt_limit": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "028a5962b1319c6b66160665d79ebb4fd214f416"
  },
  "required_landing_sequence": [
    "sidecar requires only natural CI, Decision Preflight and State Gate on the exact sidecar head",
    "re-check main == 2a1239b1230461f3f43fd86bb8edd0915552e1a2, target PR #810 head == 028a5962b1319c6b66160665d79ebb4fd214f416, target PR #810 still OPEN, DRAFT and unmerged",
    "mark target PR #810 Ready exactly once",
    "observe a NEW natural target State Gate triggered by Ready",
    "require unchanged exact target head 028a5962b1319c6b66160665d79ebb4fd214f416 and contexts baseline=success, state-gate=success, landing-state-gate=success",
    "explicitly reject landing-state-gate-draft-inert as formal landing evidence",
    "publish exactly one pre-merge structured comment OWNER_LANDING_MERGE_ATTESTATION with JSON block owner_landing_merge_attestation on target PR #810",
    "fresh no-drift check",
    "merge target PR #810 exactly once with method=merge and expected head 028a5962b1319c6b66160665d79ebb4fd214f416"
  ],
  "landing_revalidation_required_for_actions": [
    "ready_for_review",
    "owner_landing_merge_attestation",
    "merge"
  ],
  "formal_landing_context_must_be_success_before_attestation": true,
  "formal_landing_context_must_be_success_before_merge": true,
  "formal_landing_context_must_not_be_draft_inert": true,
  "premerge_owner_landing_attestation_required": true,
  "owner_landing_attestation_marker": "OWNER_LANDING_MERGE_ATTESTATION",
  "owner_landing_attestation_json_block": "owner_landing_merge_attestation",
  "owner_landing_attestation_comment_limit": 1,
  "sidecar_ready_and_merge_forbidden": true,
  "bootstrap_compatibility_notes": [
    "POST_CUTOVER_EXECUTION_SURFACE_COMPATIBILITY",
    "NO_LEGACY_LOCAL_AUTHORING",
    "NO_STARTUP_SNAPSHOT_REQUIRED"
  ],
  "bootstrap_compatibility_detail": "This fresh authority Decision v1 is created from the currently locked main schema at 2a1239b1230461f3f43fd86bb8edd0915552e1a2. All Decision authoring, command-plan/gate generation, focused deterministic tests and local validation are declared on trusted_worker; GitHub-native sidecar push and Draft PR creation on github_control_plane; natural workflow observation and no-drift audits on remote_observation. No allowed_command selects the legacy local surface and no bootstrap_exception_command is used. user_local is not declared because no machine-specific capability is required for this round. The startup-snapshot gate is NOT required for this sidecar round; project_state/gates/startup_snapshot.json and project_state/gates/bootstrap_state.json are NOT part of the accepted 4-file sidecar committed shape and MUST NOT be committed, staged, amended, restored into another commit or used as target evidence. In this machine scope, bootstrap_state.json is explicitly allowed at R2 for generator updates only, while remaining outside the exact four-file committed shape and forbidden to stage/commit/amend.",
  "bootstrap_state_side_effect_rule": {
    "allowed_incidental_local_effect": "project_state/gates/bootstrap_state.json",
    "classification_when_regenerated": "AUTHORIZED_GENERATED_LOCAL_OBSERVATION_ONLY",
    "must_not_be_staged_or_committed": true,
    "must_not_be_target_evidence": true,
    "fail_closed_if_gate_treats_side_effect_as_blocker": true,
    "explicit_path_and_risk_grant": true
  },
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": false,
  "source_test_mutation_authorized": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "pr810_owner_landing_r2_v1.bootstrap_and_preflight",
      "command": "verify exact fresh locked main 2a1239b1230461f3f43fd86bb8edd0915552e1a2, exact target head 028a5962b1319c6b66160665d79ebb4fd214f416 and fresh sidecar branch merge-base; commit this immutable R2 Owner landing authority Decision first as the unique first commit touching project_state/decision_packet.md; run transition command plan transition lint transition preflight pre and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any generated artifact mutation; do NOT run startup-snapshot The existing gate generator may update project_state/gates/bootstrap_state.json as an explicitly allowed local observation only; never stage or commit it. Re-observe preflight on the final committed head with this permitted local delta present.",
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
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "pr810_owner_landing_r2_v1.validate",
      "command": "run focused deterministic tests tests/test_mainline_landing.py tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py tests/test_planning_and_github_adapters.py tests/test_ci_responsibility.py tests/platform_v1/test_merge_intent.py -q; require git diff --check clean and transition-lint/transition-command-plan/transition-preflight revalidation and worktree-publication-readiness PUBLICATION_READY; make zero provider model browser or credential calls; do NOT require tests/test_github_remote_verifier.py",
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
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "pr810_owner_landing_r2_v1.materialize_generated_authority",
      "command": "commit exactly one generated governance commit chore: materialize PR810 landing authority R2 v1 containing only project_state/gates/command_plan.json project_state/gates/transition_command_plan_preview.json and project_state/gates/transition_preflight_result.json; no product semantic commit exists in this sidecar and project_state/gates/bootstrap_state.json is never committed; if another tracked commit is necessary FAIL CLOSED",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "pr810_owner_landing_r2_v1.publish_authority",
      "command": "after all blocking validation passes, push only the exact authority branch codex/pr810-owner-landing-r2-v1 to locked main 2a1239b1230461f3f43fd86bb8edd0915552e1a2 and create exactly one Draft authority sidecar PR recording the immutable authority snapshot; keep the sidecar Draft forever and never mark Ready or merge the sidecar; never push the target branch codex/f02-accepted-artifact-handoff-r2-v5 and never push main; never rerun or dispatch workflows; publication retry accounting: maximum 3 total push invocations with transport retries only when read-only remote observation confirms no remote mutation; maximum 2 total PR-create invocations with retry only when read-only GitHub search confirms no existing PR for this exact head/base and successful_draft_pr_creation_count==0; after first successful remote push NO further push invocation; after first successfully created Draft PR NO second creation call",
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
      "allowed_only_after_validation": true
    },
    {
      "command_id": "pr810_owner_landing_r2_v1.natural_authority_validation",
      "command": "require natural exact-head CI, Decision Preflight and State Gate observations on the authority Draft PR head and confirm no main drift from 2a1239b1230461f3f43fd86bb8edd0915552e1a2 and no target head drift from 028a5962b1319c6b66160665d79ebb4fd214f416 and no concurrent landing authority; keep the authority PR Draft and do NOT mark Ready or merge; the authority grants the Owner exactly-once Mark Ready and exactly-one expected-head protected merge of target PR 810 only after a formal Ready-triggered landing-state-gate success and required exact-head contexts baseline state-gate landing-state-gate",
      "phase": "final_evidence",
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
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml",
    ".github/workflows/tauri-desktop-check.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "project_state/mainline_merge_intents/active.json"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml",
    ".github/workflows/tauri-desktop-check.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "project_state/mainline_merge_intents/active.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "runner_managed_artifact_paths": [],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml",
    ".github/workflows/tauri-desktop-check.yml",
    ".codex-skills/**",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/**",
    "frontend/**",
    "src-tauri/**",
    "desktop/**",
    "provider/**",
    "model/**",
    "credential/**",
    "tests/**",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "project_state/gates/startup_snapshot.json",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "README.md",
    "README.txt",
    "**/STOP",
    "**/owner_handoffs/**"
  ],
  "forbidden_operations": [
    "local_authoring",
    "implicit_user_local_fallback",
    "direct_push_main",
    "auto_merge",
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
    "workflow_dispatch",
    "tag_or_release",
    "deployment",
    "dependency_install",
    "browser_execution",
    "snapshot_update",
    "arbitrary_remote_browsing",
    "external_url_navigation",
    "second_decision_commit",
    "second_command_runner",
    "active_json_rewrite",
    "product_replay",
    "ruleset_weakening",
    "required_check_weakening",
    "target_semantic_mutation",
    "target_branch_push",
    "head_substitution",
    "base_substitution",
    "reopen_target_pr",
    "amend_target_pr",
    "rebase_target_pr",
    "continue_push_target_pr",
    "mark_target_ready_twice",
    "merge_target_twice",
    "weaken_decision_immutability",
    "weaken_expected_head_protection",
    "weaken_required_checks",
    "ignore_operation_surface_admissibility",
    "retroactive_false_none_attestation",
    "landing_state_gate_draft_inert_accepted",
    "sidecar_pr_ready_or_merge",
    "sidecar_pr_merge",
    "sidecar_pr_mark_ready",
    "sidecar_pr_workflow_rerun",
    "sidecar_pr_workflow_dispatch",
    "startup_snapshot_required",
    "startup_snapshot_write",
    "bootstrap_state_stage",
    "bootstrap_state_commit",
    "bootstrap_state_amend",
    "duplicate_remote_mutation",
    "pr_body_update_after_creation"
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
      "after all blocking validation passes, push only the exact authority branch codex/pr810-owner-landing-r2-v1 to locked main 2a1239b1230461f3f43fd86bb8edd0915552e1a2 and create exactly one Draft authority sidecar PR recording the immutable authority snapshot; keep the sidecar Draft forever and never mark Ready or merge the sidecar; never rerun or dispatch workflows; publication retry accounting: maximum 3 total push invocations and 2 total PR-create invocations with transport-retry rules as defined"
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": ".github/workflows/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "**/secrets/**",
      "minimum_risk": "R3"
    }
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "ruleset_id": 21023698,
  "required_status_contexts": [
    "baseline",
    "state-gate",
    "landing-state-gate"
  ],
  "required_status_contexts_all_success": true,
  "forbidden_status_contexts": [
    "landing-state-gate-draft-inert"
  ],
  "target_decision_contract": {
    "decision_id": "decision_20260911_issue799_artifact_handoff_r2_v5",
    "round_id": "round_20260911_issue799_artifact_handoff_r2_v5",
    "content_sha256": "64bd7ce4c39d1d840b5fa660de89da113d9515b481a7d54dc18ae6e28e61ec71",
    "mainline_merge_intent_required": false,
    "active_pr_binding_mode": "none",
    "target_decision_mark_ready_allowed": true,
    "target_decision_merge_allowed": true,
    "target_workflow_profile": "baseline"
  },
  "target_acceptance_evidence": {
    "owner_exact_head_review_id": 5180621815,
    "owner_exact_head_review_commit": "028a5962b1319c6b66160665d79ebb4fd214f416",
    "owner_exact_head_review_state": "COMMENTED",
    "review_kind": "DISCLOSED_CODEX_SELF_AUDIT",
    "target_pr_state": "OPEN",
    "target_pr_is_draft": true,
    "target_pr_merged": false,
    "natural_runs": [
      {
        "name": "baseline",
        "workflow": "CI",
        "run_id": 34616330347,
        "run_number": 1201,
        "conclusion": "success",
        "head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416"
      },
      {
        "name": "decision-preflight",
        "workflow": "Decision Preflight",
        "run_id": 34616330428,
        "run_number": 509,
        "conclusion": "success",
        "head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416"
      },
      {
        "name": "state-gate",
        "workflow": "State Gate",
        "run_id": 34616330526,
        "run_number": 2871,
        "conclusion": "success",
        "head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416"
      },
      {
        "name": "verify",
        "workflow": "Model Access",
        "run_id": 34616330435,
        "run_number": 256,
        "conclusion": "success",
        "head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416"
      },
      {
        "name": "e2e",
        "workflow": "Frontend Playwright",
        "run_id": 34616330317,
        "run_number": 148,
        "conclusion": "success",
        "head_sha": "028a5962b1319c6b66160665d79ebb4fd214f416"
      }
    ],
    "diagnostic_result": "UNCHANGED_BASELINE_FAILURE_SET",
    "model_access_expected": "ACTUAL_SUCCESS_RUN_34616330435_92_PYTHON_410_FRONTEND_AND_LINT",
    "playwright_expected": "ACTUAL_SUCCESS_RUN_34616330317_30_PASSED_2_SKIPPED",
    "local_required_tests": "358 backend tests and410 frontend tests passed; lint/build/diff hygiene and real TS HTTP Git SQLite single/team reopen passed; one existing crash-thread warning retained",
    "diagnostic_summary": "22 failed, 6299 passed, 23 skipped, 1 warning in 492.52s (0:08:12)"
  },
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "codex/pr810-owner-landing-r2-v1",
    "target_product_branch": "codex/f02-accepted-artifact-handoff-r2-v5",
    "authority_path": "Path B R2 transition",
    "execution_surfaces": [
      "trusted_worker",
      "github_control_plane",
      "remote_observation"
    ],
    "legacy_local_surface_forbidden": true,
    "local_agent_ready_or_merge_authority": true,
    "authority_actor_note": "Only the exact target under explicit session owner delegation and this bounded R2 Decision."
  },
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "8a493d5857f0f0bedb8b44845f99f17cd8289aae237519870d8cd4baa3f9f654",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "The user explicitly delegated owner authority, self-audit and merge. This is disclosed agent activity, not independent human review.",
  "landing_actor": "Codex under explicit session owner delegation"
}
```

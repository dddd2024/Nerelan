# Decision Packet — PR900 Owner landing authority v1

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260915_issue901_pr900_owner_landing_r2_v1",
  "round_id": "round_20260915_issue901_pr900_owner_landing_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
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
  "source_issue": 901,
  "parent_issue": 898,
  "target_pr": 900,
  "source_pr": 900,
  "target_branch": "owner/issue898-tracked-plan-prereq-r2-v2",
  "accepted_exact_head_sha": "f64a5a54d959ea6098234b3bac12d7de5696db3b",
  "owner_exact_head_review_id": 5209309250,
  "owner_exact_head_review_commit": "f64a5a54d959ea6098234b3bac12d7de5696db3b",
  "target_decision_id": "decision_20260915_issue898_tracked_plan_prerequisite_r2_v2",
  "target_round_id": "round_20260915_issue898_tracked_plan_prerequisite_r2_v2",
  "target_ci_run_id": 34958919999,
  "target_decision_preflight_run_id": 34958919931,
  "target_state_gate_run_ids": [34958920077],
  "target_pre_ready_state_gate_run_id": 34958920077,
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "fresh_base": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "current_main_expected": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "integration_base_ref": "main",
  "required_branch": "owner/issue901-pr900-owner-landing-r2-v1",
  "follows_last_decision_id": "decision_20260915_issue898_tracked_plan_prerequisite_r2_v2",
  "follows_last_round_id": "round_20260915_issue898_tracked_plan_prerequisite_r2_v2",
  "workstream_id": "issue901-pr900-owner-landing-r2-v1",
  "fresh_worktree_creation_required": false,
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
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
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
  "approval_basis": "The user explicitly delegated repository Owner execution and requested the highest-priority non-overlapping work. PR900 exact head f64a5a54d959ea6098234b3bac12d7de5696db3b has natural CI, Decision Preflight and State Gate SUCCESS plus disclosed Owner exact-head COMMENT review 5209309250. This sidecar only authorizes bounded landing; it is delegated Agent/Owner activity, not independent human approval.",
  "landing_authority_scope_note": "Governance-only sidecar for target PR900 exact head f64a5a54d959ea6098234b3bac12d7de5696db3b at locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Sidecar remains Draft/unmerged. Activation preflight and ordinary State Gate may authorize one deterministic generated-governance binding even if activation CI is red solely on the historical stale tracked-plan equality. After post-G exact-head natural CI/Decision Preflight/State Gate success, publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION while target remains Draft, then Ready once, require formal landing-state-gate SUCCESS, fresh no-drift revalidation, merge target once with expected-head ordinary merge, and require new main natural push State Gate SUCCESS before acceptance.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "f64a5a54d959ea6098234b3bac12d7de5696db3b"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 34958920077,
    "required_status_contexts": ["baseline", "state-gate", "landing-state-gate"],
    "pre_ready_completed_contexts": ["baseline", "state-gate"],
    "formal_landing_context_completed_only_after_ready": "landing-state-gate",
    "exactly_one_active_matching_attestation_required": true,
    "post_hoc_after_merge_allowed": false
  },
  "activation_acceptance_contract": {
    "pre_execution_authorization_required_before_g": true,
    "ordinary_state_gate_success_required_before_g": true,
    "activation_ci_success_required_before_g": false,
    "activation_ci_failure_allowed_only_if": "historical_tracked_command_plan_identity_prerequisite",
    "no_rerun_or_noop_commit": true,
    "post_g_ci_decision_preflight_state_gate_success_required": true
  },
  "required_landing_sequence": [
    "require natural activation Decision Preflight PRE_EXECUTION_AUTHORIZED and ordinary State Gate SUCCESS; activation CI is not a pre-G requirement when its sole failure is the historical tracked command-plan identity prerequisite",
    "materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from this immutable Decision projection without user-local execution",
    "require terminal successful natural post-G sidecar CI Decision Preflight and State Gate without rerun or dispatch",
    "fresh-read main target PR target head review threads Ruleset and checks and require no drift from the bound snapshot",
    "while target PR900 remains Draft publish exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target, sidecar authority, review 5209309250, successful exact-head target State Gate run 34958920077, Ruleset and canonical contexts",
    "re-read target comments and require exactly one active matching attestation with canonical digest before Ready",
    "mark target PR900 Ready exactly once",
    "observe the naturally triggered formal landing-state-gate and require terminal SUCCESS on exact target head f64a5a54d959ea6098234b3bac12d7de5696db3b without rerun or dispatch",
    "fresh-read main target PR target head sidecar attestation review threads Ruleset and required checks and require no drift",
    "merge target PR900 exactly once with method merge and expected head f64a5a54d959ea6098234b3bac12d7de5696db3b",
    "verify target merged true recorded merge commit and new main head",
    "observe the new main natural push State Gate and require SUCCESS without rerun",
    "only then record Issue898/Issue901 landing acceptance and fresh-reconcile PR893/Issue894 against the new main"
  ],
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
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
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "target_branch_push",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "sidecar_pr_ready_or_merge",
    "post_hoc_attestation_after_target_merge",
    "second_attestation_family"
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
      "Publish only owner/issue901-pr900-owner-landing-r2-v1 and exactly one Draft sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1; keep sidecar Draft and unmerged.",
      "After post-G sidecar validation and fresh no-drift checks, publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION on target PR900 while it remains Draft, binding exact target f64a5a54d959ea6098234b3bac12d7de5696db3b, locked base d3ffafc8924614f309a8f85b6224137f94b2d8c1, target Decision, exact unmerged sidecar authority, Owner audit review 5209309250, target exact-head State Gate run 34958920077, live Ruleset and canonical contexts; re-read and require exactly one active matching attestation.",
      "Then mark target PR900 Ready at most once, require natural formal landing-state-gate SUCCESS, fresh-read again, merge target PR900 at most once using ordinary merge with expected head f64a5a54d959ea6098234b3bac12d7de5696db3b, verify merged state/new main, and observe the new natural main-push State Gate; never rerun or dispatch a workflow."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "issue901v1.bootstrap",
      "command": "On the exact sidecar activation run the existing transition command-plan, transition lint and transition preflight against locked main. Require PRE_EXECUTION_AUTHORIZED and immutable Decision evidence before materializing generated plan files. Activation CI may be observed but is not a prerequisite for G when its sole failure is the historical stale tracked-plan equality.",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
    },
    {
      "command_id": "issue901v1.materialize",
      "command": "Materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from the immutable Issue901 Decision projection. No product, test, workflow or source edit and no user-local handoff.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"],
      "produced_artifacts": []
    },
    {
      "command_id": "issue901v1.validate",
      "command": "Require natural post-G sidecar CI Decision Preflight and State Gate SUCCESS plus exact target CI Decision Preflight State Gate SUCCESS; fresh-read current main, target exact head/base/Draft state, Owner review, Ruleset and review threads. Require no drift and no workflow rerun.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue901v1.publish",
      "command": "Publish only owner/issue901-pr900-owner-landing-r2-v1 and one Draft sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Keep sidecar Draft forever and never merge or mark it Ready.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue901v1.attest",
      "command": "Only after post-G validation and while target PR900 is still Draft, publish exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target head f64a5a54d959ea6098234b3bac12d7de5696db3b/base d3ffafc8924614f309a8f85b6224137f94b2d8c1/Decision, exact unmerged sidecar authority and natural runs, Owner review 5209309250, successful exact-head target State Gate run 34958920077, live Ruleset and canonical contexts. Re-read and require exactly one active matching canonical digest before Ready. No post-hoc or duplicate attestation.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["pull_request_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue901v1.land_target",
      "command": "Only after the valid pre-Ready attestation exists: mark target PR900 Ready once; require natural formal landing-state-gate terminal SUCCESS on f64a5a54d959ea6098234b3bac12d7de5696db3b without rerun or dispatch; fresh-read every bound target/base/check/thread/Ruleset/attestation/sidecar predicate; merge PR900 once using method merge with expected head protection; verify merged state/new main; observe a new natural main-push State Gate SUCCESS before recording acceptance.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["mark_ready", "merge", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue901v1.observe",
      "command": "Fresh-read sidecar, target and main natural checks, exact merge outcome and new main-push State Gate. Preserve negative evidence and fresh-reconcile PR893/Issue894 against the new main; never silently reuse their old locked-base authority.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [898, 901]
}
```

## Goal

Land accepted PR #900 exactly once under a bounded governance-only sidecar, then require a new natural main-push State Gate before recording acceptance. The sidecar never enters target history.

## Build vs Reuse

Reuse existing Path-B Decision/transition machinery, existing deterministic command-plan projection, existing Owner landing attestation parser/schema, Ruleset, GitHub Ready/Merge and natural State Gate. No new component, workflow, receipt family, runner or dependency.

## Bootstrap Compatibility

This is the final pre-#898 landing round. Activation preflight and ordinary State Gate authorize one deterministic generated-governance binding. Activation CI may be red solely because current main still contains the historical Platform V1 tracked-plan equality prerequisite; do not rerun or add a no-op commit. Post-G exact-head CI/Decision Preflight/State Gate must all succeed.

## Stop Conditions

Any main/target/sidecar drift, immutable Decision mutation, unexpected changed path, non-historical activation failure, post-G required-check failure, duplicate/stale attestation, blocking review thread, Ruleset drift, exhausted attempt budget or unavailable required GitHub capability stops the round. No force/rebase/rerun/dispatch or target branch push.

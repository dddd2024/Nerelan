# Decision Packet — PR893 Owner landing recovery authority v4

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260915_issue894_pr893_owner_landing_recovery_r2_v4",
  "round_id": "round_20260915_issue894_pr893_owner_landing_recovery_r2_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR_RECOVERY",
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "repository": "dddd2024/Nerelan",
  "source_issue": 894,
  "parent_issue": 891,
  "target_pr": 893,
  "source_pr": 893,
  "target_branch": "owner/issue891-false-none-attestation-r2-v2",
  "accepted_exact_head_sha": "de5400fe67c33e8f26517fac49f9e28d41132139",
  "owner_exact_head_review_id": 5205536976,
  "owner_exact_head_review_commit": "de5400fe67c33e8f26517fac49f9e28d41132139",
  "target_decision_id": "decision_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "target_round_id": "round_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "target_ci_run_id": 34865425320,
  "target_decision_preflight_run_id": 34865425267,
  "target_state_gate_run_ids": [34865425131, 34865523623],
  "target_pre_ready_state_gate_run_id": 34865523623,
  "target_existing_attestation_comment_id": 5677002202,
  "target_failed_ready_state_gate_run_id": 34946231419,
  "target_converted_to_draft_revocation_run_id": 34961481739,
  "target_revocation_state_gate_job_id": 104355839284,
  "target_revocation_landing_job_id": 104355839670,
  "target_revocation_expected_landing_failure_step": "Invalidate converted-to-Draft landing context",
  "target_revocation_expected_state_gate_job_conclusion": "success",
  "target_revocation_expected_landing_job_conclusion": "failure",
  "target_is_draft_after_revocation": true,
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "fresh_base": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "current_main_expected": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "integration_base_ref": "main",
  "required_branch": "owner/issue894-pr893-owner-landing-r2-v4",
  "follows_last_decision_id": "decision_20260915_issue894_pr893_owner_landing_recovery_r2_v3",
  "follows_last_round_id": "round_20260915_issue894_pr893_owner_landing_recovery_r2_v3",
  "workstream_id": "issue894-pr893-owner-landing-r2-v4",
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
  "approval_basis": "The user explicitly delegated repository Owner execution and requested the highest-priority non-overlapping work. PR893 exact head de5400fe67c33e8f26517fac49f9e28d41132139 has accepted exact-head CI, Decision Preflight, State Gate and disclosed Owner audit review 5205536976. Recovery v3 correctly converted the target back to Draft, and natural run 34961481739 proved the workflow's actual revocation semantics: the ordinary state-gate job succeeded while landing-state-gate intentionally failed at 'Invalidate converted-to-Draft landing context'. V3 is closed unmerged because it incorrectly required the whole converted_to_draft workflow to succeed. V4 changes only the landing choreography and keeps the target implementation immutable.",
  "landing_authority_scope_note": "Governance-only recovery sidecar for target PR893 exact head de5400fe67c33e8f26517fac49f9e28d41132139 at locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Sidecar remains Draft/unmerged. Target remains Draft after the intentional converted_to_draft revocation run. Activation preflight and ordinary State Gate may authorize one deterministic generated-governance binding even if activation CI is red solely on the historical stale tracked-plan equality. After post-G exact-head natural CI/Decision Preflight/State Gate success, update the one existing parser-visible OWNER_LANDING_MERGE_ATTESTATION comment in place to bind this v4 authority; never create a second parser-visible attestation. Then Ready once, require formal landing-state-gate SUCCESS, fresh no-drift revalidation, merge target once with expected-head ordinary merge, and require new main natural push State Gate SUCCESS before acceptance.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "de5400fe67c33e8f26517fac49f9e28d41132139"
  },
  "converted_to_draft_revocation_contract": {
    "run_id": 34961481739,
    "ordinary_state_gate_job_id": 104355839284,
    "ordinary_state_gate_job_required_conclusion": "success",
    "landing_state_gate_job_id": 104355839670,
    "landing_state_gate_job_required_conclusion": "failure",
    "landing_failure_step": "Invalidate converted-to-Draft landing context",
    "landing_failure_is_expected_revocation_evidence": true,
    "whole_workflow_success_required": false,
    "second_convert_to_draft_allowed": false
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "update_existing_comment_id": 5677002202,
    "create_second_parser_visible_attestation_allowed": false,
    "target_pre_ready_state_gate_run_id": 34865523623,
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
    "fresh-read main target PR target head review threads Ruleset checks and converted_to_draft revocation evidence and require no drift from the bound snapshot",
    "require target PR893 is Draft and exact converted_to_draft run 34961481739 proves ordinary state-gate job SUCCESS plus landing-state-gate FAILURE only at the intentional revocation step; do not require whole workflow SUCCESS and do not convert to Draft again",
    "while target PR893 remains Draft update existing parser-visible attestation comment 5677002202 in place to the current existing-format OWNER_LANDING_MERGE_ATTESTATION binding exact target, this v4 sidecar authority, Owner review 5205536976, successful exact-head target State Gate workflow run 34865523623, live Ruleset and canonical contexts; never create a second parser-visible marker",
    "re-read target comments and require exactly one active matching attestation with canonical digest before Ready",
    "mark target PR893 Ready exactly once",
    "observe the naturally triggered formal landing-state-gate and require terminal SUCCESS on exact target head de5400fe67c33e8f26517fac49f9e28d41132139 without rerun or dispatch",
    "fresh-read main target PR target head sidecar attestation review threads Ruleset and required checks and require no drift",
    "merge target PR893 exactly once with method merge and expected head de5400fe67c33e8f26517fac49f9e28d41132139",
    "verify target merged true recorded merge commit and new main head",
    "observe the new main natural push State Gate and require SUCCESS without rerun",
    "require unchanged post-merge false-none validation to accept the same pre-merge attestation and completed target contexts",
    "only then record Issue891/Issue894 landing acceptance and current-main governance-green state"
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
    "second_attestation_family",
    "second_convert_to_draft"
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
      "Publish only owner/issue894-pr893-owner-landing-r2-v4 and exactly one Draft sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1; keep sidecar Draft and unmerged.",
      "After post-G validation and fresh no-drift checks, update existing target PR893 parser-visible attestation comment 5677002202 in place to bind exact target de5400fe67c33e8f26517fac49f9e28d41132139, locked base d3ffafc8924614f309a8f85b6224137f94b2d8c1, target Decision, exact unmerged v4 sidecar authority, Owner audit review 5205536976, target exact-head successful State Gate workflow run 34865523623, live Ruleset and canonical contexts; do not create a second parser-visible attestation.",
      "Then mark target PR893 Ready at most once, require natural formal landing-state-gate SUCCESS, fresh-read again, merge target PR893 at most once using ordinary merge with expected head de5400fe67c33e8f26517fac49f9e28d41132139, verify merged state/new main, and observe the new natural main-push State Gate; never rerun or dispatch a workflow."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "issue894v4.bootstrap",
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
      "command_id": "issue894v4.materialize",
      "command": "Materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from the immutable Issue894 v4 Decision projection. No product, test, workflow or source edit and no user-local handoff.",
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
      "command_id": "issue894v4.validate",
      "command": "Require natural post-G sidecar CI Decision Preflight and State Gate SUCCESS plus exact target CI Decision Preflight State Gate SUCCESS; fresh-read current main, target exact head/base/Draft state, Owner review, Ruleset, review threads and converted_to_draft revocation evidence. Require no drift and no workflow rerun.",
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
      "command_id": "issue894v4.publish",
      "command": "Publish only owner/issue894-pr893-owner-landing-r2-v4 and one Draft sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Keep sidecar Draft forever and never merge or mark it Ready.",
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
      "command_id": "issue894v4.attest",
      "command": "Only after post-G validation and while target PR893 remains Draft, update existing comment 5677002202 in place to one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target head de5400fe67c33e8f26517fac49f9e28d41132139/base d3ffafc8924614f309a8f85b6224137f94b2d8c1/Decision, exact unmerged v4 sidecar authority and natural runs, Owner review 5205536976, successful exact-head target State Gate workflow run 34865523623, live Ruleset and canonical contexts. Re-read and require exactly one active matching canonical digest before Ready. No post-hoc or duplicate attestation.",
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
      "command_id": "issue894v4.land_target",
      "command": "Only after the valid updated pre-Ready attestation exists: mark target PR893 Ready once; require natural formal landing-state-gate terminal SUCCESS on de5400fe67c33e8f26517fac49f9e28d41132139 without rerun or dispatch; fresh-read every bound target/base/check/thread/Ruleset/attestation/sidecar predicate; merge PR893 once using method merge with expected head protection; verify merged state/new main; observe a new natural main-push State Gate SUCCESS and unchanged post-merge false-none validation before recording acceptance.",
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
      "command_id": "issue894v4.observe",
      "command": "Fresh-read sidecar, target and main natural checks, exact merge outcome, new main-push State Gate and post-merge false-none validation. Preserve all v1-v3 negative evidence; never silently reinterpret the intentional converted_to_draft landing failure as a successful landing context.",
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
  "issue_completion_close_allowed": [891, 894]
}
```

## Goal

Recover and land accepted PR #893 exactly once under a bounded governance-only sidecar, preserving the workflow's intentional converted-to-Draft revocation semantics, then require a new natural main-push State Gate and unchanged post-merge false/none validation before recording acceptance.

## Build vs Reuse

Reuse existing Path-B Decision/transition machinery, deterministic command-plan projection, existing Owner landing attestation parser/schema, Ruleset, GitHub Ready/Merge and natural State Gate. No new component, workflow, receipt family, runner or dependency.

## V3 Negative Evidence

PR #897 / Decision `decision_20260915_issue894_pr893_owner_landing_recovery_r2_v3` is closed unmerged. It correctly produced a generated-governance binding and converted target #893 back to Draft, but its immutable chronology incorrectly required the entire `converted_to_draft` State Gate workflow to succeed. Natural run `34961481739` proved the actual repository contract: ordinary `state-gate` job `104355839284` succeeded, while `landing-state-gate` job `104355839670` intentionally failed at `Invalidate converted-to-Draft landing context` to revoke prior landing authority. No attestation update, second Ready, merge, rerun or dispatch followed.

## Bootstrap Compatibility

Current main still contains the historical tracked-plan CI prerequisite. Activation preflight and ordinary State Gate authorize one deterministic generated-governance binding. Activation CI may be red solely because of that stale tracked-plan equality; do not rerun or add a no-op commit. Post-G exact-head CI/Decision Preflight/State Gate must all succeed.

## Stop Conditions

Any main/target/sidecar drift, immutable Decision mutation, unexpected changed path, non-historical activation failure, post-G required-check failure, incorrect revocation evidence, duplicate/stale attestation, blocking review thread, Ruleset drift, exhausted attempt budget or unavailable required GitHub capability stops the round. No force/rebase/rerun/dispatch, no second convert-to-Draft, no target branch push, and no second parser-visible attestation.

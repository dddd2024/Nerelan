# Decision Packet — PR893 Owner landing authority v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260915_issue894_pr893_owner_landing_r2_v2",
  "round_id": "round_20260915_issue894_pr893_owner_landing_r2_v2",
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
  "historical_failed_main_state_gate_run_id": 34820409545,
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "fresh_base": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "current_main_expected": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "integration_base_ref": "main",
  "required_branch": "owner/issue894-pr893-owner-landing-r2-v2",
  "follows_last_decision_id": "decision_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "follows_last_round_id": "round_20260914_issue891_false_none_premerge_attestation_r2_v2",
  "supersedes_decision_id": "decision_20260915_issue894_pr893_owner_landing_r2_v1",
  "superseded_evidence": "Closed-unmerged PR895 at f9c527d629f64de049d2bdda5af625b472f07f39 is terminal negative Decision evidence. Natural Decision Preflight #526/run34929640428 and State Gate #3107 failed deterministically because issue894.attest and issue894.land_target paired read_only_audit with github_control_plane. No target attestation, Ready, merge, rerun or dispatch occurred. V2 only corrects the command operation/surface contract; target snapshot and landing chronology are unchanged.",
  "workstream_id": "issue894-pr893-owner-landing-r2-v2",
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
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "approval_basis": "The user repeatedly delegated repository Owner execution and requested completion of the highest-priority non-overlapping work. Exact-head S2 audit review 5205536976 found no remaining semantic defect at de5400fe67c33e8f26517fac49f9e28d41132139. V1 sidecar failure was a command surface declaration error and is preserved as negative evidence. This is disclosed delegated Agent/Owner activity, not independent human review.",
  "landing_authority_scope_note": "Governance-only sidecar for target PR893 exact head de5400fe67c33e8f26517fac49f9e28d41132139 at locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Sidecar remains Draft/unmerged. After natural sidecar checks and generated-governance binding, publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION while target is Draft, then Ready once, require formal landing-state-gate SUCCESS, fresh no-drift revalidation, merge target once with expected-head ordinary merge, and require new main natural push State Gate SUCCESS before closure.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "de5400fe67c33e8f26517fac49f9e28d41132139"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 34865523623,
    "required_status_contexts": ["baseline", "state-gate", "landing-state-gate"],
    "pre_ready_completed_contexts": ["baseline", "state-gate"],
    "formal_landing_context_completed_only_after_ready": "landing-state-gate",
    "exactly_one_active_matching_attestation_required": true,
    "post_hoc_after_merge_allowed": false
  },
  "required_landing_sequence": [
    "require terminal successful natural target exact-head CI Decision Preflight and State Gate",
    "require terminal successful natural sidecar CI Decision Preflight and State Gate",
    "fresh-read main target PR target head review threads Ruleset and checks and require no drift from the bound snapshot",
    "while target PR893 remains Draft publish exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target, sidecar authority, review 5205536976, successful exact-head target State Gate run 34865523623, Ruleset and canonical contexts",
    "re-read target comments and require exactly one active matching attestation with canonical digest before Ready",
    "mark target PR893 Ready exactly once",
    "observe the naturally triggered formal landing-state-gate and require terminal SUCCESS on exact target head without rerun or dispatch",
    "fresh-read main target PR target head sidecar attestation review threads Ruleset and required checks and require no drift",
    "merge target PR893 exactly once with method merge and expected head de5400fe67c33e8f26517fac49f9e28d41132139",
    "verify target merged true recorded merge commit and new main head",
    "observe the new main natural push State Gate and require SUCCESS without rerun",
    "require unchanged post-merge false/none validator to accept the same pre-merge attestation and completed baseline state-gate landing-state-gate contexts",
    "only then close Issues891 and894 and call current main governance-green"
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
    "AGENTS.md", ".github/**", ".codex-skills/**", "docs/**", "reverse_agent/**", "frontend/**", "tests/**", "project_state/mainline_merge_intents/**", "pyproject.toml", "requirements*.txt"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "squash", "amend", "history_rewrite", "target_branch_push", "workflow_rerun", "workflow_dispatch", "runner_dispatch", "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution", "external_reverse_tool_invocation", "destructive", "tag_or_release", "dependency_install", "sidecar_pr_ready_or_merge", "post_hoc_attestation_after_target_merge", "second_attestation_family", "historical_run_34820409545_rerun"
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
      "Publish only owner/issue894-pr893-owner-landing-r2-v2 and exactly one Draft sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1; keep sidecar Draft and unmerged.",
      "After sidecar and target required checks are terminal SUCCESS and fresh no-drift validation passes, publish exactly one existing-format OWNER_LANDING_MERGE_ATTESTATION on target PR893 while it remains Draft. Bind exact target de5400fe67c33e8f26517fac49f9e28d41132139, locked base d3ffafc8924614f309a8f85b6224137f94b2d8c1, target Decision, exact unmerged sidecar authority, Owner audit review 5205536976, target exact-head State Gate run 34865523623, live Ruleset and canonical contexts. Re-read and require exactly one active matching attestation.",
      "Then mark target PR893 Ready at most once, require the natural formal landing-state-gate SUCCESS, fresh-read again, merge target PR893 at most once using ordinary merge with expected head de5400fe67c33e8f26517fac49f9e28d41132139, verify merged state/new main, observe the new natural main-push State Gate and post bounded evidence to Issues894 and891. Never rerun or dispatch a workflow."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "issue894v2.bootstrap",
      "command": "On the exact sidecar activation run the existing transition command plan, transition lint and transition preflight against locked main. Require PRE_EXECUTION_AUTHORIZED and immutable Decision evidence before materializing generated plan files.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
    },
    {
      "command_id": "issue894v2.materialize",
      "command": "Materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from the immutable Decision projection. No product/test/source edit.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["source_edit", "local_static_check"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"], "produced_artifacts": []
    },
    {
      "command_id": "issue894v2.validate",
      "command": "Require natural sidecar CI Decision Preflight and State Gate success plus exact target CI Decision Preflight State Gate success; fresh-read current main/target head/base/Draft state, Owner review, Ruleset and review-thread state. Require no drift and no workflow rerun.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation", "operations": ["code_read", "read_only_audit", "repository_observation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue894v2.publish",
      "command": "Publish only owner/issue894-pr893-owner-landing-r2-v2 and one Draft PR against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1. Keep sidecar Draft forever and never merge or mark it Ready.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["push", "draft_pr", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue894v2.attest",
      "command": "Only after validation and while target PR893 is still Draft, publish exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION binding target head de5400fe67c33e8f26517fac49f9e28d41132139/base d3ffafc8924614f309a8f85b6224137f94b2d8c1/Decision, exact unmerged sidecar authority and its natural runs, Owner review 5205536976, already-successful exact-head target State Gate run 34865523623, live Ruleset and canonical contexts. Re-read and require exactly one active matching canonical digest before Ready. No post-hoc or duplicate attestation.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["pull_request_comment", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue894v2.land_target",
      "command": "Only after the valid pre-Ready attestation exists: mark target PR893 Ready once; require natural formal landing-state-gate terminal SUCCESS on de5400fe67c33e8f26517fac49f9e28d41132139 without rerun/dispatch; fresh-read every bound target/base/check/thread/Ruleset/attestation/sidecar predicate; merge PR893 once using method merge with expected head protection; verify merged state/new main; observe a new natural main-push State Gate SUCCESS and unchanged post-merge validation using the same attestation before closing Issues891/894.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["mark_ready", "merge", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [891, 894]
}
```

## Goal

Authorize only the exact no-drift landing of accepted PR #893 using the repaired acyclic false/none attestation lifecycle, then require a new natural main-push State Gate success before #891/#894 closure. This v2 supersedes only the invalid sidecar Decision in closed PR #895; it does not supersede or mutate the target implementation Decision.

## Stop Conditions

Any target/base/head/Decision/sidecar/Ruleset/review/check/attestation drift, duplicate or stale attestation, failed or pending mandatory check, blocking review condition, Decision mutation, sidecar check failure, unexpected Ready landing-gate failure, ambiguous merge result or unavailable required GitHub capability stops landing. No bypass, rerun, force, rebase, target mutation, post-hoc attestation or alternate merge method.

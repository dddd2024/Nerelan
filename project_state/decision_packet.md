# Decision Packet — PR893 Owner landing recovery authority v3

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260915_issue894_pr893_owner_landing_recovery_r2_v3",
  "round_id": "round_20260915_issue894_pr893_owner_landing_recovery_r2_v3",
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
  "decision_scope": "OWNER_LANDING_RECOVERY_SIDECAR",
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
  "target_original_pre_ready_state_gate_run_id": 34865523623,
  "failed_ready_state_gate_run_id": 34946231419,
  "failed_ready_landing_job_id": 104306170587,
  "failed_ready_landing_check": "false_none_authority_decision_owner_scope",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "fresh_base": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "current_main_expected": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "integration_base_ref": "main",
  "required_branch": "owner/issue894-pr893-owner-landing-r2-v3",
  "follows_last_decision_id": "decision_20260915_issue894_pr893_owner_landing_r2_v2",
  "follows_last_round_id": "round_20260915_issue894_pr893_owner_landing_r2_v2",
  "supersedes_decision_id": "decision_20260915_issue894_pr893_owner_landing_r2_v2",
  "superseded_evidence": "PR896 remains Draft/unmerged at G head 3374a58a34e380e58805d84bea0eedf9a92b3dbe with natural CI/Decision Preflight/State Gate SUCCESS. Target PR893 was marked Ready once only after a unique valid pre-Ready attestation, then natural State Gate #3112/run34946231419 failed solely because the immutable v2 authority Decision omitted active_json_rewrite from forbidden_operations. No merge, rerun, dispatch, target-branch push, main mutation or product mutation followed. V3 is a recovery authority only.",
  "workstream_id": "issue894-pr893-owner-landing-recovery-r2-v3",
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
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "target_convert_to_draft_attempt_limit": 1,
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
  "target_convert_to_draft_allowed": true,
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
  "approval_basis": "The user delegated repository Owner execution. V3 is the smallest recovery after the natural Ready State Gate #3112 failed on one immutable authority-expression omission. Target implementation S2 and the canonical attestation fields/digests/runs were accepted by the failed formal validator; this is delegated Agent/Owner activity, not independent human review.",
  "landing_authority_scope_note": "Governance-only recovery sidecar. It may not mutate target code/history. After its own exact-head acceptance, convert target PR893 back to Draft exactly once, require the natural converted_to_draft State Gate SUCCESS, update the existing parser-visible attestation comment 5677002202 in place so parser-visible count remains exactly one and bind it to this v3 authority and the new successful Draft State Gate, then mark Ready exactly once and require a new natural formal landing-state-gate SUCCESS before expected-head ordinary merge.",
  "owner_landing_bounds": {
    "draft_reset_attempts": 1,
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "de5400fe67c33e8f26517fac49f9e28d41132139"
  },
  "recovery_contract": {
    "failed_ready_run_id": 34946231419,
    "failed_ready_landing_job_id": 104306170587,
    "failed_check": "false_none_authority_decision_owner_scope",
    "exact_missing_v2_forbidden_operation": "active_json_rewrite",
    "reuse_existing_attestation_comment_id": 5677002202,
    "second_parser_visible_attestation_forbidden": true,
    "convert_target_to_draft_once": true,
    "require_natural_converted_to_draft_state_gate_success": true,
    "rebind_existing_attestation_after_draft_gate": true,
    "mark_ready_once_after_rebind": true,
    "require_new_natural_formal_landing_state_gate_success": true,
    "workflow_rerun_or_dispatch_forbidden": true
  },
  "required_landing_sequence": [
    "require terminal successful natural v3 sidecar exact-head CI Decision Preflight and State Gate",
    "fresh-read main target head/base Ready/unmerged state failed run34946231419 review threads Ruleset existing attestation comment5677002202 and require no drift",
    "convert target PR893 from Ready to Draft exactly once without target branch mutation",
    "observe the naturally triggered converted_to_draft State Gate and require terminal SUCCESS on exact target head without rerun or dispatch",
    "update existing canonical top-level attestation comment5677002202 in place; never create a second parser-visible attestation; bind exact target, v3 sidecar authority and natural runs, Owner review, new successful exact-head Draft State Gate run, live Ruleset and canonical contexts; recompute canonical digest",
    "re-read target issue comments and require exactly one active matching attestation and canonical digest",
    "mark target PR893 Ready exactly once under v3",
    "observe a new naturally triggered formal landing-state-gate and require terminal SUCCESS on exact target head without rerun or dispatch",
    "fresh-read main target sidecar attestation review threads Ruleset and required checks and require no drift",
    "merge target PR893 exactly once using method merge with expected head de5400fe67c33e8f26517fac49f9e28d41132139",
    "verify merged state and new main head",
    "observe the new main natural push State Gate and require SUCCESS without rerun",
    "require unchanged post-merge false/none validator to accept the same updated pre-merge attestation and completed contexts",
    "only then close Issues891 and894 and call current main governance-green"
  ],
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
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
    "pyproject.toml",
    "requirements*.txt"
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
    "second_parser_visible_attestation",
    "failed_run_34946231419_rerun"
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
      "Publish only owner/issue894-pr893-owner-landing-r2-v3 and exactly one Draft recovery sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1; keep sidecar Draft and unmerged.",
      "After exact v3 sidecar acceptance and fresh no-drift validation, convert target PR893 at de5400fe67c33e8f26517fac49f9e28d41132139 back to Draft exactly once. This is a PR readiness-state recovery mutation only; never push the target branch and never rerun or dispatch a workflow.",
      "After the natural converted_to_draft State Gate succeeds, update existing top-level attestation comment 5677002202 in place exactly once for v3 binding and preserve parser-visible attestation count=1.",
      "After the updated attestation is reread and valid, mark target PR893 Ready exactly once under v3; require a new natural formal landing-state-gate SUCCESS; then merge once by ordinary merge with expected head de5400fe67c33e8f26517fac49f9e28d41132139; never rerun or dispatch a workflow."
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
      "command_id": "issue894v3.bootstrap",
      "command": "On the exact v3 sidecar activation run existing transition command-plan, lint and preflight against locked main. Require PRE_EXECUTION_AUTHORIZED and immutable Decision evidence before generated-plan materialization.",
      "phase": "bootstrap",
      "required": false,
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
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "issue894v3.materialize",
      "command": "Materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from the immutable v3 Decision projection. No product test workflow or source edit.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue894v3.validate",
      "command": "Require natural v3 sidecar CI Decision Preflight and State Gate success; fresh-read current main target exact head/base Ready unmerged state, failed run34946231419, existing canonical attestation comment5677002202, Owner review, Ruleset and review threads; require no drift and no workflow rerun.",
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
      "command_id": "issue894v3.publish",
      "command": "Publish only owner/issue894-pr893-owner-landing-r2-v3 and exactly one Draft recovery sidecar against locked main d3ffafc8924614f309a8f85b6224137f94b2d8c1; keep sidecar Draft and unmerged.",
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
      "command_id": "issue894v3.reset_target_draft",
      "command": "After exact v3 sidecar acceptance and fresh no-drift validation, convert target PR893 at de5400fe67c33e8f26517fac49f9e28d41132139 back to Draft exactly once. This is a PR readiness-state recovery mutation only; never push the target branch and never rerun or dispatch a workflow.",
      "phase": "recovery",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "ready",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue894v3.rebind_attestation",
      "command": "After the natural converted_to_draft State Gate succeeds, update existing top-level attestation comment 5677002202 in place exactly once for v3 binding and preserve parser-visible attestation count=1.",
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
      "command_id": "issue894v3.land_target",
      "command": "After the updated attestation is reread and valid, mark target PR893 Ready exactly once under v3; require a new natural formal landing-state-gate SUCCESS; then merge once by ordinary merge with expected head de5400fe67c33e8f26517fac49f9e28d41132139; never rerun or dispatch a workflow.",
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
    }
  ],
  "issue_completion_close_allowed": [
    891,
    894
  ]
}
```

## Goal

Recover only the exact no-drift landing of accepted PR #893 after natural State Gate #3112 exposed the v2 sidecar authority-expression omission. Preserve target implementation and failed evidence; do not rerun workflows or mutate target history.

## Stop Conditions

Any main/head/base/Decision/sidecar/Ruleset/review/thread/attestation drift, v3 sidecar check failure, converted-to-Draft State Gate failure, duplicate parser-visible attestation, new formal landing failure, ambiguous merge result, unavailable required GitHub capability, or unexpected mutation stops landing. No bypass, workflow rerun/dispatch, target-branch push, force/rebase/squash/history rewrite, direct main push, post-hoc attestation, second parser-visible attestation, alternate merge method, product/source/test/workflow mutation, provider/model/credential/binary work.

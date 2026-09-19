# Approved bounded PR964 delegated Owner landing v1

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260919_issue829_pr964_owner_landing_r2_v1",
  "round_id": "round_20260919_issue829_pr964_owner_landing_r2_v1",
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
  "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR_CURRENT_MAIN",
  "source_issue": 829,
  "parent_issue": 800,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly delegated full Owner completion, independent subagent audit and merge. Exact target c920afa68cee774028cccf5c53407e21e733bbca accepted by independent auditor at PR964 comment5743146841. Transparently delegated Owner COMMENT review5256231312 binds that head. Target naturalCI35451512928 and latestStateGate35451513616 SUCCESS; actual full diagnostic exit0/6542passed23skipped4excluded, nativeartifact10587132287 contains6565cases0failures0errors23skips andall43workspacecasespassed. This is fresh bounded Agent landing authority, not personal human acceptance or reuse of prior961 authority.",
  "superseded_evidence": "V8 Draft963 stopped before implementation publication due nonexistent required test path; closed unmerged externally. V9 new approval/activation/Draft964 corrected that command and passed all exact-head local checks. The first v9 implementation90a1909 failed naturalCI35449857360 because its replacement-ref positive control used Git2.55 builtinemptytree. Repairc920afa changes only that fixture to an ordinary nonempty tree, retaining all assertions; fresh local checks passed. Earlier checks are not repair-head acceptance. Prior961 landing authority and closed962 sidecar are historical schema references only, never grants for964.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "61664039f6f1c2684fcb67d7cb24073e7b6b8a63",
  "activation_base_sha": "61664039f6f1c2684fcb67d7cb24073e7b6b8a63",
  "starting_head": "61664039f6f1c2684fcb67d7cb24073e7b6b8a63",
  "fresh_base": "61664039f6f1c2684fcb67d7cb24073e7b6b8a63",
  "current_main_expected": "61664039f6f1c2684fcb67d7cb24073e7b6b8a63",
  "required_branch": "codex/pr964-owner-landing-r2-v1-20260919",
  "workstream_id": "issue829-pr964-owner-landing-r2-v1",
  "follows_last_decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "follows_last_round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
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
  "normal_push_attempt_limit": 0,
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
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
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
  "semantic_implementation_contract": {
    "specification": "No product implementation. Authorize only one delegated Owner landing of exact Draft964 after targetCI35451512928 actual diagnostic exit0/nativeJUnit0 and StateGate35451513616 SUCCESS, new independent exact-head ACCEPT and new transparently delegated Owner COMMENT review; sidecar canonical CI/Decision Preflight/State Gate SUCCESS and independent review. Preserve R1 Issue829 approval/bodydigest903b987b32ba166e0ca028d22c4e86543603f3b40a832c71a6bdf8510554d580 and exact snapshot/base. Publish one existing-format pre-Ready attestation, verify via existing false/none evaluator even though Ready dispatches Path-A; Ready once, require ordinary+formal StateGate SUCCESS, reobserve no drift/concurrency, ordinary expected-head merge once and verify exactmerge/main/parents and natural mainpush StateGate and CI.",
    "completion_boundary": "Sidecar stays Draft/unmerged and never enters target history. Close only829 after its actual criteria and postmerge proof. Keep652/800/659/137 open; pure scratch observation is not persistent artifact integration. Preserve721/913 ownership and all source/evidence/refs. No other PR closure authority is required or granted;962/963 already externallyclosed. No target/source/Decision mutation."
  },
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
  "authorized_risk_paths": [
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
    "generated_governance_commit"
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
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only the Decision commit graph/ref codex/pr964-owner-landing-r2-v1-20260919 and one Draft sidecar against locked main, via GitHub Git API. No local git push.",
      "After all exact-head target/sidecar checks and independent acceptance, publish one existing-format preReady attestation for964 using actual new review and canonical run identities. Ready964 once and merge once using method merge with expected headc920afa68cee774028cccf5c53407e21e733bbca after fresh no-drift/no-concurrency. No admin bypass or rerun/dispatch.",
      "After verified merge/main/parents and natural mainpush CI/StateGate success, record factual evidence and close only completed829. Coordination comments on829/721 permitted; comments never grant authority."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue829landingv1.bootstrap",
      "command": "Use fresh F:/Nerelan-pr964-owner-landing-v1 at locked main; commit only Decision, then startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre and worktree-publication-readiness. Run provider-free tests/test_control_plane_transition.py and tests/test_decision_preflight.py, git diff --check. Generated gate files never committed.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "unit_test",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue829landingv1.publish",
      "command": "Publish only exact local Decision tree/commit to named ref via GitHub Git API and create one Draft sidecar. Verify identical SHA. No local git push; never Ready/Merge the sidecar.",
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
      "command_id": "issue829landingv1.validate",
      "command": "Require exact target CI35451512928 actual diagnostic exit0/nativeJUnit0 and StateGate35451513616 SUCCESS, independent acceptance and new Owner COMMENT review; require sidecar canonical three natural workflows SUCCESS and independent sidecar audit. Target R1 has no applicable DecisionPreflight/freshness run. Fresh-read Issue approval/digest, main, heads/base, reviews/threads/ruleset and ownership. No concurrent Ready/landing or new721 successor.",
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
      "command_id": "issue829landingv1.attest",
      "command": "While964 remains Draft, publish exactly one existing-format attestation binding inherited target integration961 Decision ID/digest, fresh sidecar Decision/digest/runs, new actual964 Owner review, preReadySG35451513616 and fresh live Ruleset. Verify unique unmodified payload/digest and existing false/none evaluator; no authored _remote fields.",
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
      "command_id": "issue829landingv1.land_target",
      "command": "Ready964 once after all predicates; wait natural ordinary and formal Path-A StateGate SUCCESS. Independently verify sidecar and false/none attestation since Ready dispatch alone does not do so. Fresh no-drift/no-concurrency, ordinary merge964 once with method merge and expected headc920afa68cee774028cccf5c53407e21e733bbca. Verify newmain/mergeparents and natural mainpush CI/StateGate SUCCESS.",
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
      "command_id": "issue829landingv1.observe",
      "command": "Read exactpostmerge main/merge/parents and natural CI/StateGate; inspect829 acceptance. Record factual proof externally. No writes through remote_observation surface.",
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
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue829landingv1.close_completed",
      "command": "Only after verified postmerge success and829 acceptance, comment and close829. Preserve broad roadmaps,721/913 worktrees, allsource/evidence and refs. No other Issue/PRclosure.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "issue_comment",
        "pull_request_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [
    829
  ],
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 964,
  "source_pr": 964,
  "target_branch": "codex/workspace-drift-env-object-integrity-r1-v9-20260919",
  "accepted_exact_head_sha": "c920afa68cee774028cccf5c53407e21e733bbca",
  "owner_exact_head_review_id": 5256231312,
  "owner_exact_head_review_commit": "c920afa68cee774028cccf5c53407e21e733bbca",
  "target_decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_ci_run_id": 35451512928,
  "target_state_gate_run_ids": [
    35451513616
  ],
  "target_pre_ready_state_gate_run_id": 35451513616,
  "workflow_profile": "baseline",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "landing_authority_scope_note": "Single964 delegatedAgentlanding only, never personalhuman carve-out. Preserve721/913 owners and serialize main publication. Inherited targetDecision identifies existingfalse/none policy only; newsidecar is landingauthority.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "c920afa68cee774028cccf5c53407e21e733bbca"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35451513616,
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
  "required_landing_sequence": [
    "require target and sidecar exact-head checks/independent acceptance and fresh964review; no concurrent landing/721 successor",
    "fresh-read approved829digest and exact main/Draft heads/base/threads/ruleset",
    "publish one existing-format preReady attestation and verify unique digest plus existing false/none evaluator",
    "Ready964 once; require natural ordinary and formal StateGate SUCCESS",
    "fresh no-drift/no-concurrency and expected-head ordinary merge964 once",
    "verify mergeparents/newmain; require natural mainpush CI and StateGate SUCCESS",
    "verify829 fullcriteria thencloseonly829; no broadergoalclosure"
  ]
}
```

## Stop conditions
Stop affected action on any base/head/Decision/scope drift, failed mandatory check, missing independent acceptance, invalid/repeated attestation or concurrent publication. No target source edit, history rewrite, bypass, generated-gate commit or721/913 takeover.

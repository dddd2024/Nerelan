# Approved bounded PR961 delegated Owner landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260919_issue659_pr961_owner_landing_r2_v1",
  "round_id": "round_20260919_issue659_pr961_owner_landing_r2_v1",
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
  "source_issue": 659,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly delegated full Owner completion, independent subagent audit and merge. Exact target head b3e557373ed11539611561a41e380414576a7499 accepted by independent auditor, recorded at PR961 comment5742230555. Real transparently delegated Owner COMMENT review5255859250 binds that head. Four target natural workflows SUCCESS; actual diagnostic exit0 with6499passed/23skipped/4deselected and nativeJUnit0failures/errors. This is separate bounded Agent landing authority, not a personal human carve-out.",
  "superseded_evidence": "Prior source PRs949/952/954/957/959/960 supplied reviewed content to target961; those authorities do not authorize this landing. Failed predecessor958 is preserved. No old authority branch/Decision is reused.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "activation_base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "starting_head": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "fresh_base": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "current_main_expected": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "required_branch": "codex/pr961-owner-landing-r2-20260919",
  "workstream_id": "issue659-pr961-owner-landing-r2-v1",
  "follows_last_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v5",
  "follows_last_round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v5",
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
    "specification": "No semantic implementation. This Decision-only sidecar authorizes one bounded delegated Owner landing of exact PR961 only, after target full selected diagnostic actual exit0/nativeJUnit0failure/error, independently attributed exact-head ACCEPT, real transparently attributed Owner COMMENT review, target four natural checks SUCCESS and this sidecar three natural checks SUCCESS and independent exact-head sidecar review. No target/head/Decision mutation. Publish one existing-format pre-Ready attestation, Ready once, ordinary and formal landing StateGate SUCCESS, immediately fresh-validate main/head/ruleset/threads/no concurrent publication, merge once with method merge and expected head, verify merge parent identities/main and new natural main-push StateGate SUCCESS. Never bypass checks or use admin merge.",
    "completion_boundary": "Authority sidecar stays Draft/unmerged and never enters target history. Only exact source issues948/951/953/955/687 may close after per-Issue acceptance check against merged result and postmerge StateGate SUCCESS; broader659/152/137 stay open. Superseded exact Draft PRs949/952/954/957/958/959/960 may close unmerged with preserved refs and factual integration link only after that same proof, only if heads remain unchanged. Preserve721 worktree and existing source evidence. Serialized main landing is permitted only if no other active Ready/landing publication or newly published721 successor is observed; otherwise pause and coordinate. This is not task takeover or independent human acceptance."
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
      "Publish only the Decision commit graph/ref codex/pr961-owner-landing-r2-20260919 and one Draft sidecar against locked main. Keep sidecar Draft/unmerged; no local git push.",
      "After target and sidecar exact-head success and independent acceptance, publish one existing-format OWNER_LANDING_MERGE_ATTESTATION on Draft target961 using actual verified review/run/ruleset identities; Ready target961 once, require both natural StateGate jobs, then one method=merge action with expected headb3e557373ed11539611561a41e380414576a7499 after fresh no-drift and no-concurrency validation. No admin bypass, rerun, dispatch, force, rebase, squash, tag or release.",
      "After merged state/main identity and natural main-push StateGate SUCCESS, add factual comments and close only completion-proven issues948/951/953/955/687 and unchanged superseded Draft PRs949/952/954/957/958/959/960. Preserve branches and all721 work. Coordination comments on659/721 are permitted; never use comments as authority."
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
      "command_id": "issue659landingv1.bootstrap",
      "command": "Use fresh F:/Nerelan-pr961-owner-landing at locked main; commit only Decision, then startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre and worktree-publication-readiness. Run provider-free tests/test_control_plane_transition.py and tests/test_decision_preflight.py, git diff --check. Generated gate files never committed.",
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
      "command_id": "issue659landingv1.publish",
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
      "command_id": "issue659landingv1.validate",
      "command": "Require target CI35444720835/Preflight35444720836/StateGate35444720834/freshness35444720910 SUCCESS, target actual selected diagnostic exit0/JUnit0, independent exact-head ACCEPT and real Owner review; require sidecar three canonical natural checks SUCCESS and independent exact-head sidecar review. Fresh-read main, Draft target/sidecar heads/base, reviews/threads and Ruleset; no active parallel Ready/landing publication, no new721 PR, no drift.",
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
      "command_id": "issue659landingv1.attest",
      "command": "While target961 remains Draft publish exactly one existing-format attestation with actual verified target/sidecar Decision digests, sidecar natural runs, recorded Owner review ID, pre-Ready StateGate35444720834, current Ruleset21023698 and canonical baseline/state-gate/landing-state-gate contexts. Re-read unique active payload and digest; no _remote runtime fields authored.",
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
      "command_id": "issue659landingv1.land_target",
      "command": "Only after all conditions and one valid pre-Ready attestation: Ready961 once; wait natural ordinary and formal landing StateGate SUCCESS; immediate fresh no-drift/no-concurrency observation; merge961 once via method merge with expected headb3e557373ed11539611561a41e380414576a7499, no admin bypass. Verify new main and natural main-push StateGate SUCCESS.",
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
      "command_id": "issue659landingv1.observe",
      "command": "Read postmerge exact main/merge/parents and natural StateGate. Under the preceding explicit control-plane grant, only after success verify narrow source Issue criteria before closure, comment/close unchanged superseded Drafts; preserve broad roadmaps/721 and branch refs.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation",
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
    948,
    951,
    953,
    955,
    687
  ],
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 961,
  "source_pr": 961,
  "target_branch": "codex/audit-fixes-integration-r2-20260919",
  "accepted_exact_head_sha": "b3e557373ed11539611561a41e380414576a7499",
  "owner_exact_head_review_id": 5255859250,
  "owner_exact_head_review_commit": "b3e557373ed11539611561a41e380414576a7499",
  "target_decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_ci_run_id": 35444720835,
  "target_decision_preflight_run_id": 35444720836,
  "target_state_gate_run_ids": [
    35444720834
  ],
  "target_pre_ready_state_gate_run_id": 35444720834,
  "workflow_profile": "baseline",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "landing_authority_scope_note": "Single target961 under explicit full Owner delegation; no personal human carve-out. Serialize main mutation with occupied721 and any other Ready/landing lane using fresh live PR/check/ref observations; never infer that unpublished721 is abandoned or edit its checkout. A main advance does not grant rewriting its Decision.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "b3e557373ed11539611561a41e380414576a7499"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35444720834,
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
    "require target and sidecar exact-head natural checks and independent target acceptance; no active concurrent Ready/landing or published721 successor",
    "fresh-read locked main, exact Draft target/sidecar head/base, real Owner review, all threads and live Ruleset",
    "publish one existing-format attestation while target961 remains Draft; re-read and verify uniqueness/digest",
    "mark target961 Ready once and require natural ordinary state-gate and formal landing-state-gate SUCCESS",
    "fresh no-drift/no-concurrency revalidation; merge961 once with method merge and expected head",
    "verify merged state, first/second parents and new main equals merge commit",
    "require new natural main-push StateGate SUCCESS",
    "only then check each narrow source Issue acceptance, record exact integration and close allowed completed Issues/superseded unchanged Drafts; keep broad roadmaps open and721 untouched"
  ]
}
```

## Stop conditions
Stop affected action on any base/head/Decision/scope drift, failed mandatory check, missing independent acceptance, invalid/repeated attestation or active concurrent publication. No target source edit, history rewrite, bypass, generated-gate commit or721 takeover.

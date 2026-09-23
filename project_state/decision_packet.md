# Approved bounded PR983 delegated Owner R3 landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue982_pr983_owner_landing_r3_v1",
  "round_id": "round_20260923_issue982_pr983_owner_landing_r3_v1",
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
  "source_issue": 982,
  "parent_issue": 260,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly delegated full Owner completion, independent subagent audit and merge. Independent exact-head acceptance comment5789567546 and disclosed delegated Owner COMMENT review5287231472 bind 7665a4456fb9b13afb660c9da110f9672b82d4be. All five natural target checks SUCCESS; actual CI6563passed23skipped4deselected exit0/native6586cases0failures0errors; Playwright32passed2skipped. Independently reviewed fresh bounded R3 sidecar candidate, including required natural main State Gate and existing receipt. No historical contract is amended.",
  "superseded_evidence": "Prior landing Decisions are schema references only, never grants. Target983 remains frozen; preserve Draft981 exacthead849af4ae2039bb7d30ebb442404a567e5c7152f2, ownerPR978/979 and live first-use runtime. Codex985 and discovery986 remain separate planning work.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "activation_base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "starting_head": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "fresh_base": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "current_main_expected": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "required_branch": "codex/pr983-owner-landing-r3-v1-20260923",
  "workstream_id": "issue982-pr983-owner-landing-r3-v1",
  "follows_last_decision_id": "decision_20260920_issue913_reviewed_goldens_r3_v3",
  "follows_last_round_id": "round_20260920_issue913_reviewed_goldens_r3_v3",
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
    "specification": "No product implementation. Single PR983 delegated Owner landing under fresh R3 Path B authority after all five exact-head natural target workflows succeed, actual CI exit0/native JUnit zero failures/errors, independent acceptance and actual delegated Owner COMMENT review. Require Decision-only sidecar three canonical natural checks and independent acceptance. Use existing pre-Ready attestation and existing false_none evaluator, natural Ready ordinary and formal landing State Gate success, then one expected-head method merge. No source/workflow/dependency/provider/browser changes.",
    "completion_boundary": "Require natural main CI actual exit0/native zero failures/errors, main State Gate SUCCESS and actual existing integration receipt with exact identities/no blockers, main Model Access and Playwright success, supplemental existing false_none postmerge validation and independent audit. Close only982 source-repair work after its criteria; runtime login/model acceptance and user-facing activation remain separate unfinished stages."
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
    "user_local_network_exceptions": [
      "Use F:/Nerelan-issue982-gpt-oauth-network and F:/Nerelan-pr983-owner-landing-v1 to verify exact objects and immutable Decisions. Run existing false_none evaluator separately before Ready, before merge and after merge using real read-only GitHub observations. After merge fetch exact observed merge SHA once from canonical origin without tags/ref destination or FETCH_HEAD mutation; verify identity/parents/tree/workflow bytes/complete delta. This is supplemental user_local evidence, not Actions. No source/index/branch mutation, provider/browser/model/credential access. Failed predicates stop dependent actions."
    ],
    "github_control_plane_network_exceptions": [
      "Publish the identical local Decision blob/tree/commit through the GitHub Git API to the exact named fresh branch. Verify every SHA and create one Draft sidecar. No local git push. Never mark the sidecar Ready or merge it.",
      "While PR983 remains Draft publish one existing-format attestation binding actual Owner review, accepted head, target982v1 Decision/digest, new sidecar Decision/digest/runs, pre-Ready SG35821008268 and current Ruleset. Read back and prove uniqueness/unchanged bytes. Run existing evaluator only under separate local_validation before Ready.",
      "After fresh remote predicates and separate successful local_validation, Ready983 once. Require natural ordinary and formal landing State Gate SUCCESS. Reobserve all identities/concurrency and successful Ready-stage local_validation before one expected-head method merge. Verify parents/tree/new main. Require natural main CI, State Gate including existing integration receipt, Model Access and Playwright acceptance before closure.",
      "Only after verified postmerge obligations and all Issue982 repair criteria, publish acceptance and close only982. Do not claim real GPT login or inference, Codex integration, model discovery, automated binding, UI localization or overall product completion. Preserve all other tasks, branches, worktrees and evidence."
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
      "command_id": "issue982landingv1.bootstrap",
      "command": "Create F:/Nerelan-pr983-owner-landing-v1 from the locked base. Commit only the approved Decision once, then run startup-snapshot, transition-command-plan, transition-lint and transition-preflight sequentially to terminal success. Run tests/test_control_plane_transition.py and tests/test_decision_preflight.py, git diff --check, and worktree-publication-readiness. Never commit generated gates.",
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
      "command_id": "issue982landingv1.publish",
      "command": "Publish the identical local Decision blob/tree/commit through the GitHub Git API to the exact named fresh branch. Verify every SHA and create one Draft sidecar. No local git push. Never mark the sidecar Ready or merge it.",
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
      "command_id": "issue982landingv1.validate",
      "command": "Require target CI35821008278 actual exit0/native JUnit zero failures/errors; Decision Preflight35821008253, State Gate35821008268, Model Access35821008255 and Playwright35821008192 SUCCESS. Require independent exact-head acceptance and real delegated Owner COMMENT review. Require sidecar three canonical natural checks and independent acceptance. Fresh-read target and sidecar immutable Decisions/digests, complete scopes, main/base/head/merge-base, review threads, Ruleset and concurrent ownership. No R1 Issue snapshot substitute for Path B authority.",
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
      "command_id": "issue982landingv1.attest",
      "command": "While PR983 remains Draft publish one existing-format attestation binding actual Owner review, accepted head, target982v1 Decision/digest, new sidecar Decision/digest/runs, pre-Ready SG35821008268 and current Ruleset. Read back and prove uniqueness/unchanged bytes. Run existing evaluator only under separate local_validation before Ready.",
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
      "command_id": "issue982landingv1.land_target",
      "command": "After fresh remote predicates and separate successful local_validation, Ready983 once. Require natural ordinary and formal landing State Gate SUCCESS. Reobserve all identities/concurrency and successful Ready-stage local_validation before one expected-head method merge. Verify parents/tree/new main. Require natural main CI, State Gate including existing integration receipt, Model Access and Playwright acceptance before closure.",
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
      "command_id": "issue982landingv1.observe",
      "command": "Read exact merge/main/parents/tree and complete actual push delta. Require natural main CI actual exit0/native JUnit zero failures/errors, natural main State Gate SUCCESS and existing mainline integration receipt EMITTED/PASSED with exact identities/no blockers, natural main Model Access and Playwright SUCCESS. Download actual run-bound artifacts with digest/XML provenance. Main Decision Preflight has no push trigger. No checkout validation on this surface; feed separate local_validation.",
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
      "command_id": "issue982landingv1.local_validation",
      "command": "Use F:/Nerelan-issue982-gpt-oauth-network and F:/Nerelan-pr983-owner-landing-v1 to verify exact objects and immutable Decisions. Run existing false_none evaluator separately before Ready, before merge and after merge using real read-only GitHub observations. After merge fetch exact observed merge SHA once from canonical origin without tags/ref destination or FETCH_HEAD mutation; verify identity/parents/tree/workflow bytes/complete delta. This is supplemental user_local evidence, not Actions. No source/index/branch mutation, provider/browser/model/credential access. Failed predicates stop dependent actions.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue982landingv1.close_completed",
      "command": "Only after verified postmerge obligations and all Issue982 repair criteria, publish acceptance and close only982. Do not claim real GPT login or inference, Codex integration, model discovery, automated binding, UI localization or overall product completion. Preserve all other tasks, branches, worktrees and evidence.",
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
    982
  ],
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 983,
  "source_pr": 983,
  "target_branch": "codex/gpt-oauth-network-r3-v1-20260923",
  "accepted_exact_head_sha": "7665a4456fb9b13afb660c9da110f9672b82d4be",
  "owner_exact_head_review_id": 5287231472,
  "owner_exact_head_review_commit": "7665a4456fb9b13afb660c9da110f9672b82d4be",
  "target_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "target_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "target_ci_run_id": 35821008278,
  "target_state_gate_run_ids": [
    35821008268
  ],
  "target_pre_ready_state_gate_run_id": 35821008268,
  "workflow_profile": "baseline",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "landing_authority_scope_note": "Single target983 delegated landing under fresh Path B only after actual acceptance is bound. No personal-human carve-out, no source edits, no live OAuth/model calls, and no authority for other PRs.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "7665a4456fb9b13afb660c9da110f9672b82d4be"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35821008268,
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
    "Require five target natural checks, actual CI/native, independent acceptance and Owner review; require sidecar three canonical checks and independent acceptance",
    "Fresh immutable Decisions, complete scopes, main/base/head/merge-base, Ruleset, reviews and concurrency",
    "Publish unique existing-format pre-Ready attestation; existing local false_none validation",
    "Ready983 once; natural ordinary and formal landing SG SUCCESS; fresh predicates and Ready-stage local validation",
    "One expected-head method merge; verify exact parents/tree/main",
    "Natural main CI actual exit0/native0, SG SUCCESS and existing receipt, Model Access/Playwright SUCCESS; supplemental postmerge evaluator and independent audit",
    "Close only982 after all bounded criteria; preserve other work"
  ],
  "postmerge_applicability_scope_note": "Main State Gate is APPLICABLE due to project_state/decision_packet.md and unchanged trusted workflow. Absence/failure is blocking, never N/A. Require actual natural main integration receipt. Main Decision Preflight has no push trigger. No change to historical obligations.",
  "reference_postmerge_evidence": {
    "base": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
    "head": "7665a4456fb9b13afb660c9da110f9672b82d4be",
    "two_point_paths": [
      "frontend/src/components/connection-binding-editor.tsx",
      "frontend/src/routes/settings.tsx",
      "frontend/src/schemas/model-access.ts",
      "frontend/tests/model-settings.test.tsx",
      "project_state/decision_packet.md",
      "reverse_agent/model_access/account_auth.py",
      "reverse_agent/platform_v1/opencode_executor.py",
      "tests/platform_v1/test_opencode_executor.py",
      "tests/test_model_access.py"
    ],
    "workflow": {
      ".github/workflows/state-gate.yml": {
        "base_blob": "a368f4fdb875c9cca5ba2634462b5e884df7b226",
        "sha256": "0eac06095bd03241bf223147b6ebd83f41afca042f62b1d688ef649d1356b5c6",
        "unchanged_in_target": true
      },
      ".github/workflows/ci.yml": {
        "base_blob": "700f614646f9b39b6d50a42c06920983e6f30738",
        "sha256": "25646a6e895df77ef62885fdd8102bbd55248bf1f11bc1eb03d0ba00bb95e744",
        "unchanged_in_target": true
      }
    },
    "state_gate_push_patterns": [
      "project_state/**",
      ".github/workflows/**",
      ".codex-skills/**",
      "docs/prompts/**",
      "reverse_agent/control_plane/**",
      "reverse_agent/project_gate.py",
      "reverse_agent/project_state.py",
      "reverse_agent/decision_preflight.py",
      "reverse_agent/post_final_evidence_sync.py",
      "reverse_agent/mainline_landing.py",
      "reverse_agent/project_ci.py",
      "reverse_agent/project_jobs.py",
      "reverse_agent/github_remote_verifier.py",
      "reverse_agent/architecture/report_truth.py"
    ],
    "state_gate_applicability": "APPLICABLE",
    "ci_applicability": "APPLICABLE",
    "limit": "Exact-case observation only. Revalidate workflow bytes, complete delta, actual merge parents/tree and natural push runs. No historical obligation changed."
  },
  "target_decision_sha256": "dc5337fcb5b895ecffb97475e1cb941dac8c60e903ef34a0e7b396941099e94c",
  "independent_exact_head_comment_id": 5789567546
}
```

Approved under current explicit Owner delegation; immutable after activation.

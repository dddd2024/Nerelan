# Approved bounded PR968 delegated Owner R3 landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260920_issue913_pr968_owner_landing_r3_v1",
  "round_id": "round_20260920_issue913_pr968_owner_landing_r3_v1",
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
  "source_issue": 913,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly delegated full Owner completion, independent subagent audit and merge. Independent exact-head acceptance comment5747724320 and disclosed delegated Owner COMMENT review5259569327 bind 387cb209efc1903977af88068280cc30f8d2b980. All five natural target checks SUCCESS; actual CI6542passed23skipped4deselected exit0/native6565cases0failures0errors; Playwright32passed2skipped. Independently reviewed fresh bounded R3 sidecar candidate, including required natural main State Gate and existing receipt. No historical contract is amended.",
  "superseded_evidence": "913 v2 stopped before product commit/publication because immutable delta cardinality was wrong; preserve its worktree and negative evidence. V3 independently reviewed, frozen and published as Draft968. Prior966/967 landing is complete, not authority for968. Preserve829/891 historical HOLD,965/967 Draft and721 ownership.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "activation_base_sha": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "starting_head": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "fresh_base": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "current_main_expected": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "required_branch": "codex/pr968-owner-landing-r3-v1-20260920",
  "workstream_id": "issue913-pr968-owner-landing-r3-v1",
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
    "specification": "No product implementation. Single PR968 delegated Owner landing under fresh R3 Path B authority after all five exact-head natural target workflows succeed, actual CI exit0/native JUnit zero failures/errors, independent acceptance and actual delegated Owner COMMENT review. Require Decision-only sidecar three canonical natural checks and independent acceptance. Use existing pre-Ready attestation and existing false_none evaluator, natural Ready ordinary and formal landing State Gate success, then one expected-head method merge. No source/workflow/dependency/provider/browser changes.",
    "completion_boundary": "Require natural main CI actual exit0/native zero failures/errors, natural main State Gate SUCCESS and its existing mainline_integration_receipt.json with EMITTED/PASSED, exact merge/parents/target/authority/attestation and no blockers; natural main Model Access and Playwright success; supplemental existing false_none local postmerge validation and independent audit. Main SG is APPLICABLE because the exact delta includes project_state/decision_packet.md. Main Decision Preflight has no push trigger and is not required. Close only913 after all original criteria and these obligations. Preserve all other tasks and evidence."
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
      "Only local_validation: read-only canonical dddd2024/Nerelan GitHub REST through existing gh without credential-value access; one bounded git fetch --no-tags --no-write-fetch-head origin <exact observed merge SHA> into F:/Nerelan-issue913-reviewed-goldens-v3 objectstore, no branch/tag/source/index mutation. No provider or other network."
    ],
    "github_control_plane_network_exceptions": [
      "Publish identical Decision graph/ref to codex/pr968-owner-landing-r3-v1-20260920 and one Draft through GitHub Git API; no git push.",
      "After all predicates publish one existing-format pre-Ready attestation, Ready968 once, merge968 once method merge expected head 387cb209efc1903977af88068280cc30f8d2b980; no bypass/rerun/dispatch.",
      "After verified postmerge acceptance comment and close only913; no other closure."
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
      "command_id": "issue913landingv1.bootstrap",
      "command": "Create F:/Nerelan-pr968-owner-landing-v1 from the locked base. Commit only the approved Decision once, then run startup-snapshot, transition-command-plan, transition-lint and transition-preflight sequentially to terminal success. Run tests/test_control_plane_transition.py and tests/test_decision_preflight.py, git diff --check, and worktree-publication-readiness. Never commit generated gates.",
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
      "command_id": "issue913landingv1.publish",
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
      "command_id": "issue913landingv1.validate",
      "command": "Require target CI35489547807 actual exit0/native JUnit zero failures/errors; Decision Preflight35489547855, State Gate35489547793, Model Access35489547823 and Playwright35489547792 SUCCESS. Require independent exact-head acceptance and real delegated Owner COMMENT review. Require sidecar three canonical natural checks and independent acceptance. Fresh-read target and sidecar immutable Decisions/digests, complete scopes, main/base/head/merge-base, review threads, Ruleset and concurrent ownership. No R1 Issue snapshot substitute for Path B authority.",
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
      "command_id": "issue913landingv1.attest",
      "command": "While PR968 remains Draft publish one existing-format attestation binding actual Owner review, accepted head, target913v3 Decision/digest, new sidecar Decision/digest/runs, pre-Ready SG35489547793 and current Ruleset. Read back and prove uniqueness/unchanged bytes. Run existing evaluator only under separate local_validation before Ready.",
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
      "command_id": "issue913landingv1.land_target",
      "command": "After fresh remote predicates and separate successful local_validation, Ready968 once. Require natural ordinary and formal landing State Gate SUCCESS. Reobserve all identities/concurrency and successful Ready-stage local_validation before one expected-head method merge. Verify parents/tree/new main. Require natural main CI, State Gate including existing integration receipt, Model Access and Playwright acceptance before closure.",
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
      "command_id": "issue913landingv1.observe",
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
      "command_id": "issue913landingv1.local_validation",
      "command": "Use F:/Nerelan-issue913-reviewed-goldens-v3 and F:/Nerelan-pr968-owner-landing-v1 to verify exact objects and immutable Decisions. Run existing false_none evaluator separately before Ready, before merge and after merge using real read-only GitHub observations. After merge fetch exact observed merge SHA once from canonical origin without tags/ref destination or FETCH_HEAD mutation; verify identity/parents/tree/workflow bytes/complete delta. This is supplemental user_local evidence, not Actions. No source/index/branch mutation, provider/browser/model/credential access. Failed predicates stop dependent actions.",
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
      "command_id": "issue913landingv1.close_completed",
      "command": "Only after verified postmerge obligations and all Issue913 criteria, publish acceptance and close only913. Preserve829/891 HOLD,965/967 Draft,721 ownership, all refs/worktrees/evidence. No other closure.",
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
    913
  ],
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 968,
  "source_pr": 968,
  "target_branch": "codex/f03-reviewed-goldens-r3-v3-20260920",
  "accepted_exact_head_sha": "387cb209efc1903977af88068280cc30f8d2b980",
  "owner_exact_head_review_id": 5259569327,
  "owner_exact_head_review_commit": "387cb209efc1903977af88068280cc30f8d2b980",
  "target_decision_id": "decision_20260920_issue913_reviewed_goldens_r3_v3",
  "target_round_id": "round_20260920_issue913_reviewed_goldens_r3_v3",
  "target_ci_run_id": 35489547807,
  "target_state_gate_run_ids": [
    35489547793
  ],
  "target_pre_ready_state_gate_run_id": 35489547793,
  "workflow_profile": "baseline",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "landing_authority_scope_note": "Single PR968 delegated Agent landing, not personal human carve-out. Target913v3 Decision binds implementation; this fresh sidecar grants landing. Preserve721 ownership and historical829/891 HOLD.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "387cb209efc1903977af88068280cc30f8d2b980"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35489547793,
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
    "Ready968 once; natural ordinary and formal landing SG SUCCESS; fresh predicates and Ready-stage local validation",
    "One expected-head method merge; verify exact parents/tree/main",
    "Natural main CI actual exit0/native0, SG SUCCESS and existing receipt, Model Access/Playwright SUCCESS; supplemental postmerge evaluator and independent audit",
    "Close only913 after all bounded criteria; preserve other work"
  ],
  "postmerge_applicability_scope_note": "Main State Gate is APPLICABLE due to project_state/decision_packet.md and unchanged trusted workflow. Absence/failure is blocking, never N/A. Require actual natural main integration receipt. Main Decision Preflight has no push trigger. No change to historical obligations.",
  "reference_postmerge_evidence": {
    "base": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
    "head": "387cb209efc1903977af88068280cc30f8d2b980",
    "two_point_paths": [
      "docs/functional-validation.md",
      "frontend/e2e/functional-validation.spec.ts",
      "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
      "frontend/e2e/snapshots/desktop-chromium/home-light.png",
      "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
      "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
      "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
      "frontend/e2e/snapshots/mobile-chromium/home-light.png",
      "frontend/e2e/snapshots/mobile-chromium/settings-dark.png",
      "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
      "frontend/src/components/connection-binding-editor.tsx",
      "frontend/src/components/functional-validation.tsx",
      "frontend/src/components/goal-composer.tsx",
      "frontend/src/components/goal-current-activity.tsx",
      "frontend/src/components/goal-progress.tsx",
      "frontend/src/components/theme-selector.tsx",
      "frontend/src/index.css",
      "frontend/src/lib/functional-validation.ts",
      "frontend/src/lib/platform-client.ts",
      "frontend/src/routes/approvals.tsx",
      "frontend/src/routes/home.tsx",
      "frontend/src/routes/roadmap.tsx",
      "frontend/src/routes/runs.tsx",
      "frontend/src/routes/settings.tsx",
      "frontend/tests/approvals.test.tsx",
      "frontend/tests/goal-completion-evidence.test.tsx",
      "frontend/tests/goal-progress.test.tsx",
      "frontend/tests/platform-home.test.tsx",
      "frontend/tests/roadmap.test.tsx",
      "frontend/tests/task-first-lifecycle-states.test.tsx",
      "project_state/decision_packet.md"
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
  "target_decision_sha256": "b434a8123e057aea330e25ea305ea7c59c8212955b80ab8da23f6ccdb40ee676",
  "independent_exact_head_comment_id": 5747724320
}
```

Approved under current explicit Owner delegation; immutable after activation.

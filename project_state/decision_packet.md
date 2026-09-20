# Approved bounded PR966 delegated Owner landing v1

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260920_issue931_pr966_owner_landing_r2_v1",
  "round_id": "round_20260920_issue931_pr966_owner_landing_r2_v1",
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
  "source_issue": 931,
  "parent_issue": 786,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly delegated Owner completion, independent subagent audit and merge. Independent exact-head ACCEPT comment5747349173 and disclosed delegated Owner COMMENT review5259302639 bind target2ba693b51f1fc125e36fab32629796541d24b37c. Natural CI35486196945 actual diagnostic exit0/6542passed23skipped4excluded/native6565cases0failures0errors, StateGate35486201174, ModelAccess35486196923 and Playwright35486196818(30passed2skipped) succeeded. This new bounded Decision adopts independently reviewed exact-case postmerge applicability before execution; it does not retroactively alter965/829 or fix891 production routing.",
  "superseded_evidence": "931v4 empty activation metadata usedCRLF, naturalSG35485811062failed;LF-only correction plus freshOwnerapproval31469473782 preservednormalizeddigest and naturalSG35485923879succeeded before source. Old932 stalehistory/checks not currentauthority. Prior964/965landingcontract cannot authorize966 and its historicalpostmergeSGobligation remainsHOLD.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
  "activation_base_sha": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
  "starting_head": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
  "fresh_base": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
  "current_main_expected": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
  "required_branch": "codex/pr966-owner-landing-r2-v1-20260920",
  "workstream_id": "issue931-pr966-owner-landing-r2-v1",
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
    "specification": "No product implementation. Single966 delegatedOwnerlanding on lockedbase after all applicable targetCI/StateGate/ModelAccess/Playwright exact-head SUCCESS, actualfullCIexit0/nativeJUnit0, newindependentaudit and OwnerCOMMENTreview; separateDecision-onlysidecar threecanonicalnaturalchecks andindependentacceptance. ExistingformatpreReadyattestation andexistingfalse_noneevaluator beforeReady; actualordinary+formallandingStateGateSUCCESS andfreshnopublicationconflict beforeoneexpectedheadmethodmerge. No provider/browser/credential/source/workflow mutation.",
    "completion_boundary": "Aftermerge require naturalmainCIactualexit0/nativeJUnit0 andexistingfalse_nonepostmerge evaluator withrealGitHubdata plus exactparents/tree/main. MainStateGate is EXPECTED_NOT_APPLICABLE only for frozenexacttwofrontendpaths andunchangedtrustedbaseworkflow. This is not naturalSGsuccess. Closeonly931afteractualcriteria. Keep829/891HOLD/open and965Draft; do notretroactivelyamendtheircontracts. Preserve721/913andallhistory."
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
      "Only local_validation: read-only canonical dddd2024/Nerelan GitHub REST through existing gh, without reading credentialvalues; one bounded git fetch --no-tags origin <exact observed merge SHA> into F:/Nerelan-issue931-activation-error-v4 objectstore, no branch/tag publication, no source/index/worktree mutation. Verify fetchedobjectSHA/topology before existinglocalvalidator. No provider/other network."
    ],
    "github_control_plane_network_exceptions": [
      "PublishexactDecisiongraph/ref to codex/pr966-owner-landing-r2-v1-20260920 andoneDraftsidecar throughGitHubGitAPI only; no normalgitpush.",
      "AfterallpredicatespublishoneexistingformatpreReadyattestation, Ready966once, merge966oncemethodmergeexpectedhead2ba693b51f1fc125e36fab32629796541d24b37c; noadminbypass/rerun/dispatch.",
      "Afterverifiedpostmergeboundedacceptancecommentandcloseonly931; nootherIssue/PRclosure."
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
      "command_id": "issue931landingv1.bootstrap",
      "command": "Create F:/Nerelan-pr966-owner-landing-v1 from the locked base. Commit only the approved Decision once, then run startup-snapshot, transition-command-plan, transition-lint and transition-preflight sequentially to terminal success. Run tests/test_control_plane_transition.py and tests/test_decision_preflight.py, git diff --check, and worktree-publication-readiness. Never commit generated gates.",
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
      "command_id": "issue931landingv1.publish",
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
      "command_id": "issue931landingv1.validate",
      "command": "Require target CI35486196945 with actual diagnostic exit0 and native JUnit zero failures/errors; State Gate35486201174, Model Access35486196923 and Playwright35486196818 must succeed. Require a new independent exact-head acceptance and a real delegated Owner COMMENT review. Require the sidecar three canonical natural checks and independent acceptance. Fresh-read Issue931 approval/digest, main, both PR identities/snapshots, review threads, Ruleset and concurrent ownership. Recompute the complete two-point target path set and trusted-base workflow hashes.",
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
      "command_id": "issue931landingv1.attest",
      "command": "While PR966 remains Draft, publish one existing-format attestation binding the actual new Owner review, accepted target, inherited integration961 Decision/digest, new sidecar Decision/digest/runs, pre-Ready State Gate35486201174 and current Ruleset. Read back through the API and prove uniqueness and unchanged bytes. The checkout evaluator runs only under the separate local_validation command and must pass before Ready.",
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
      "command_id": "issue931landingv1.land_target",
      "command": "After fresh remote checks and successful separate local_validation, mark PR966 Ready once. Require natural ordinary and formal landing State Gate success. Reobserve identity, concurrency and fixed-case applicability; require successful Ready-stage local_validation before one merge-method merge with expected-head protection. Verify parents/tree/new main through the API. Run the postmerge evaluator only under the separate user_local command. Natural main CI is required; main State Gate is not expected for the frozen excluded path set.",
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
      "command_id": "issue931landingv1.observe",
      "command": "Read exact merge/main/parents/tree and natural main CI actual exit0/native JUnit zero failures/errors through canonical APIs. Read the complete actual push path set and trusted workflow bytes. No subprocess or checkout validation on this surface; observations feed local_validation. Inspect any unexpected exact-main State Gate run and stop closure on failure or unknown identity; do not ignore failure as N/A.",
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
      "command_id": "issue931landingv1.local_validation",
      "command": "Use the explicit Windows checkouts F:/Nerelan-issue931-activation-error-v4 and F:/Nerelan-pr966-owner-landing-v1 to verify locally materialized exact Git objects and immutable Decision evidence. Run the existing false/none evaluator separately before Ready, before merge and after merge, with actual read-only GitHub observations. After merge only, fetch the exact observed merge SHA once from canonical origin with no tags or branch destination; verify object identity, parents/tree and trusted workflow bytes against the complete actual push delta. Local object availability/provenance is machine-specific. This is supplemental user_local verification, never a trusted Actions run. No source, tests, workflow, index or branch mutation; no provider/model calls or credential-value access. A failed predicate stops dependent Ready/merge/closure.",
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
      "command_id": "issue931landingv1.close_completed",
      "command": "Only after verified postmerge acceptance under this new bounded contract and all Issue931 criteria, comment and close Issue931. Preserve the historical Issue829/891 HOLD, Draft965, Issue721/913 ownership, and all refs/evidence. No other Issue or PR closure.",
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
    931
  ],
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "target_pr": 966,
  "source_pr": 966,
  "target_branch": "codex/f05-activation-error-r1-v4-20260920",
  "accepted_exact_head_sha": "2ba693b51f1fc125e36fab32629796541d24b37c",
  "owner_exact_head_review_id": 5259302639,
  "owner_exact_head_review_commit": "2ba693b51f1fc125e36fab32629796541d24b37c",
  "target_decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "target_ci_run_id": 35486196945,
  "target_state_gate_run_ids": [
    35486201174
  ],
  "target_pre_ready_state_gate_run_id": 35486201174,
  "workflow_profile": "baseline",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "landing_actor": "ChatGPT under the user's explicit current repository Owner delegation",
  "landing_authority_scope_note": "Single966 delegatedAgentlanding, no personalhuman carveout. Preserve721/913ownership. Existing inheritedintegration961Decision identifiesfalse_nonepolicy only; this freshsidecar islandingauthority.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "2ba693b51f1fc125e36fab32629796541d24b37c"
  },
  "attestation_contract": {
    "marker": "OWNER_LANDING_MERGE_ATTESTATION",
    "schema_reuse_required": true,
    "new_receipt_family_allowed": false,
    "publish_before_target_ready": true,
    "target_pre_ready_state_gate_run_id": 35486201174,
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
    "RequiretargetapplicableCI/SG/ModelAccess/Playwrightsuccess plus newindependentaudit/Ownerreview; require sidecarcanonicalthreechecksandindependentacceptance",
    "Freshapproved931digest/label/Owner, main/base/head/PRsnapshot/ruleset/reviewthreads/concurrency; recomputecomplete2pointpathsandtrustedworkflowhashes",
    "PublishoneexistingformatpreReadyattestation andevaluateexistingfalse_nonepredicates againstlive data",
    "Ready966once; require actualordinary+formallandingSGSUCCESS, thenfreshidentity/applicabilitycheck",
    "One methodmergeexpectedhead, verifyparents/tree/newmain",
    "RequireactualnaturalmainCIexit0/nativeJUnit0; existingpostmergefalse_noneevaluatorandindependentactualtopology/applicabilityreview",
    "Closeonly931 whenalloriginalcriteriaandnewboundedpostmergeobligationsmet; retain891/829historicHOLD"
  ],
  "postmerge_applicability_scope_note": "This freshboundedDecision selects satisfiable obligations for966 only; no generalapplicabilityframework ornewreceiptfamily. BeforeReady/merge andaftermerge independently recompute exactbase/head/pathset andtheseunchangedtrustedworkflowbytes. Anyunknown/truncation/workflowdrift/extraentry blocks. ActualmainpushCIrequired; absentmainStateGate is EXPECTED_NOT_APPLICABLE, never SUCCESS. If any unexpected exact-main StateGate run exists, inspect actualevent/head/attempt/result; failure orunknownidentity stopsclosure andcannotbeignoredusingexpectedN/A.",
  "reference_postmerge_evidence": {
    "base": "78f0b2d975d2937848afd1240fdd7b944ea5bd24",
    "head": "2ba693b51f1fc125e36fab32629796541d24b37c",
    "two_point_paths": [
      "frontend/src/lib/goal-continuation-operation.ts",
      "frontend/tests/goal-continuation-activation-errors.test.ts"
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
    "state_gate_applicability": "EXPECTED_NOT_APPLICABLE_FOR_THIS_EXACT_DIFF",
    "ci_applicability": "APPLICABLE",
    "limit": "Read-only exact-case planning observation, not new authority or general GitHub glob verifier. Must revalidate workflow bytes, actual merge parents/tree and complete push delta before postmerge acceptance. No old965 obligation is changed."
  }
}
```

Stop on any failed mandatory check, identity/scope drift, unknown applicability, duplicate attestation or concurrent publication. Sidecar stays Draft/unmerged. No product/source implementation.

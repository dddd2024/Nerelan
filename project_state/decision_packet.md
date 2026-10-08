# Corrected first Ready exact landing authority

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue891_bootstrap_exact_landing_r2_v1",
  "round_id": "round_20261008_issue891_bootstrap_exact_landing_r2_v1",
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
  "decision_scope": "ISSUE891_CORRECTED_FIRST_READY_EXACT_LANDING",
  "source_issue": 891,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; Distinct exact landing authority for the independently reviewed cyclic Ready-run correction at6221fe3. Old1099 grant remains parked; no use of oldDraft asReady evidence. Owner delegated controller approver, personally_human=false.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue891-bootstrap-exact-landing-r2-20261008",
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
  "normal_push_attempt_limit": 1,
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
  "issue_comment_allowed": false,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Decision-only authorization for exact corrective PR1100 at6221fe3/main97d. This Authority must remain Draft/unmerged. Before Ready require source and Authority deterministic checks, original natural exact-head CI allSUCCESS, independent source and Authority exact-head acceptance, no unresolved blocking review, live unchanged repository/base/head and ruleset. Record truthful delegated COMMENTED exact-head review, not independent/human approval. Mark only PR1100 Ready once; observe its actual new StateGate pull_request run ID, then write exactly one existing-format canonical landing attestation binding that current ReadyID before formal validation reads it. Formaljob must verify real completed ordinary job in its own currentrun, never oldDraft. Require actual wholeReadyworkflowSUCCESS, formalbaseline/state-gate/landing-state-gateSUCCESS and immediate lockedmain/base/head/mergeableclean before one merge method expected-head protected merge. Verify merged PR, actual mergecommit equalsremote main and new natural postmerge validation/receipt; preserve any actualfailure and never rerun/reset/bypass.",
    "reuse": "Existing immutable PathB Decision/compiler/preflight, owner_landing_merge_attestation schema, exact corrected source workflow/verifier and actual GitHub REST. No newGate/schema/receiptfamily.",
    "completion_boundary": "One real firstReady corrective landing only; whole unattended/backlog remainsincomplete. SourceScopeReady/mergefalse staysimmutable, new separateAuthority only. Failure parksaffectedlanding; no old1094/1099 mutation/Ready/merge, no fullplatformclaim.",
    "execution_surface_note": "Real platform currently fixedchecker-only and lacks this GitHub executor, as independently accepted host evidence shows; supervisedCodex alternate on boundedGitHub controlplane."
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
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/command_authority.py",
    "tests/test_mainline_landing.py",
    ".github/workflows/state-gate.yml",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    ".codex-skills/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit",
    "active_json_rewrite",
    "ruleset_change",
    "bypass_required_checks",
    "merge_authority_pr",
    "issue_close"
  ],
  "capability_policy": {
    "github_control_plane_network_exceptions": [
      "Publish only codex/issue891-bootstrap-exact-landing-r2-20261008 and one AuthorityDraft; one truthful delegatedreview and one canonicalattestation on exactPR1100, Readyonce and expectedhead mergeonce onlyunderallboundchecks. No old1094/1099 sideeffects, bypass, rerun, directmainpush, release/deploy/model/provider."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "AGENTS.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "docs/agents/governance-reference.md",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "landing.validation",
      "command": "python -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider; git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "unit_test",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.authority_publication",
      "command": "Publish only exact codex/issue891-bootstrap-exact-landing-r2-20261008 and one Authority Draft against main after PUBLICATION_READY; keep Authority Draft/unmerged.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.evidence",
      "command": "Record one truthful delegated exact-head COMMENTED review on PR1100; after actualReadyID creation, publish one canonical attestation bindingthatcurrentID. No oldDraft substitution or independent self-acceptance.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "pull_request_comment"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.ready",
      "command": "Only after independently accepted exactsource+Authority/naturalCI and unchanged remote main/base/head, mark only PR1100 Ready once; observe actualReadyrunID and publish pre-authorized attestation beforeformaljob. AuthorityremainsDraft.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "landing.merge",
      "command": "After actualReady wholeworkflow and required formalcontextsSUCCESS plus immediate lockedstate/ruleset/threads reobservation, merge onlyPR1100 once withmethodmerge and expectedhead 6221fe3dabd24098b41aa0e9d3472fd7e1b3ed91; verifyactualmain mergecommit and postmerge naturalvalidation.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "merge"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "approval_event_or_time": "2026-10-08T09:26:19.086261+00:00",
  "owner_delegation_sha256": "99b4d9e72c7ce8bf79966c10d54714c5228d0a6032a7f435877276c1b14848ba",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 0,
  "development_correction_round_limit": 0,
  "mandatory_check_run_limit": 2,
  "execution_expires_at": "2026-10-08T10:29:33.368369+00:00",
  "target_pr": 1100,
  "accepted_exact_head_sha": "6221fe3dabd24098b41aa0e9d3472fd7e1b3ed91",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge"
}
```

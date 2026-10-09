# Explicit additional exact Task API landing allocation

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261009_issue118_task_api_exact_landing_r3_v1",
  "round_id": "round_20261009_issue118_task_api_exact_landing_r3_v1",
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
  "decision_scope": "ISSUE118_1109_EXPLICIT_ADDITIONAL_EXACT_LANDING_ALLOCATION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; Root explicitly appends90min allowance for SAME #118 landing lineage/new1109@bf9d/mainDec after original source CI independent acceptance. Old aggregate3WT/3Decision/6checks/3push/3Draft/2review/2attestation/2Ready/0merge and all expired grants/failures remain. No old allowance reuse, source/runtime renewal, human impersonation or self-independent acceptance.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "dec321721ab9c33a0107a0b2283839654d569a88",
  "activation_base_sha": "dec321721ab9c33a0107a0b2283839654d569a88",
  "starting_head": "dec321721ab9c33a0107a0b2283839654d569a88",
  "required_branch": "codex/issue118-task-api-exact-landing-r3-20261009",
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
    "specification": "Explicit append-only bounded allocation for the SAME #118 foundation landing lineage, targeting only new source1109@bf9d5d5f814d5eb3d43f5d90c08eaad44f69ed7b/baseDec. Source/local and original natural CI independently accepted. Decision-only new Authority stays Draft/unmerged. Its exact local/original natural CI and independent acceptance precede one truthful delegated COMMENTED review and one Ready. Actual new1109 Ready runID, ordinary completion, canonical attestation, whole/formal success and independent acceptance precede one expected-head merge. Verify actual new main, both merge parents, original postmerge CI and existing receipt. All three old landing allocations, old Source1106 validP2 and every expiry/spend/failure are preserved. No old PR writes/resolution, source/body/runtime edits, workflow dispatch/rerun, bypass, main push/history rewrite, model/provider, release or deployment.",
    "reuse": "Existing Decision/compiler/preflight, actual-currentReadyID verifier and canonical attestation/postmerge receipt; no new Gate/schema/receipt/runtime.",
    "execution_surface_note": "Accepted project host supports fixed checking but lacks this governed GitHub landing executor; authorized Codex fallback.",
    "completion_boundary": "Only source1109@bf9d5d5f814d5eb3d43f5d90c08eaad44f69ed7b landing. Source66 paths, frozen64candidate7b and main8 verified. Authority stays Draft/unmerged. All old PRs preserved. Coding profile, next evidence integration and full unattended/backlog remain incomplete."
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
      "Publish only codex/issue118-task-api-exact-landing-r3-20261009 and one new AuthorityDraft; new delegatedreview/actualReadyID attestation/Ready/protectedmerge of source1109 only after all prerequisites. No oldPR writes, source/body/runtime edits, mainpush/historyrewrite, bypass/rerun/dispatch, model/provider/release/deploy."
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
      "command": "Publish only exact codex/issue118-task-api-exact-landing-r3-20261009 and one new AuthorityDraft after PUBLICATION_READY; keep Draft/unmerged.",
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
      "command": "One truthful delegated COMMENTED exact-head review and canonical actual-currentReadyID attestation on source1109 only; not human or independent selfapproval.",
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
      "command": "After independent source+Authority exact local/original CI acceptance and fresh principal/state/ruleset/no blockers, Ready source1109 once and bind actual new Ready ID.",
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
      "command": "After actual whole Ready/formal success and independent acceptance plus immediate exact state/ruleset/threads, merge source1109 once using merge method and match-head bf9d5d5f814d5eb3d43f5d90c08eaad44f69ed7b; verify actual main/two parents/original postmerge CI/receipt.",
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
  "approval_event_or_time": "2026-10-09T05:06:20.154780+00:00",
  "owner_delegation_sha256": "fce2e05c0be1c0b337b3f7b48c0083582b38f93d3569c05b3baf24210622664f",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 0,
  "development_correction_round_limit": 0,
  "mandatory_check_run_limit": 2,
  "execution_expires_at": "2026-10-09T06:36:20.154780+00:00",
  "target_pr": 1109,
  "accepted_exact_head_sha": "bf9d5d5f814d5eb3d43f5d90c08eaad44f69ed7b",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge"
}
```

# Delegated controller footprint repair v3

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue118_delegated_controller_r2_v3_footprint",
  "round_id": "round_20261008_issue118_delegated_controller_r2_v3_footprint",
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
  "decision_scope": "ISSUE118_DELEGATED_CONTROLLER_AUTHORITY_ORCHESTRATION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; Controller-authorized compile repair under the same explicit Owner delegation. Prior immutable a105fc3 decision and blocked plan preserved; original absolute expiry and product restrictions unchanged. Controller-authorized v3 successor repairs observed unchanged footprint test failure at 6072309 (13282 bytes > 12000). Preserve immutable v2, CI diagnostic and all prior spending; append separate check allowance, retain original absolute expiry.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "607230915e892c64b8bced7772c90ba34282e7f3",
  "required_branch": "codex/issue118-delegated-controller-authority-r2-v2-20261008",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": true,
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
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
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
    "specification": "Compress only the AGENTS.md Long-duration unattended section to a bounded linked entry. All delegated workflow semantics remain in existing docs/agents/governance-reference.md. Do not alter reference, tests, byte ceiling, compiler or runtime. Repair observed footprint failure and verify unchanged tests.",
    "reuse": "Existing AGENTS entry, conditional governance reference, transition parser/compiler/preflight and exact-head CI. No new Gate or authority schema.",
    "execution_surface_note": "Reuse the same existing branch and full worktree at exact starting_head 6072309. One new Decision-only activation, canonical preflight before AGENTS edit. Prior history immutable; no history rewrite.",
    "completion_boundary": "Draft only, exact source diff, deterministic checks, natural exact-head CI, independent acceptance required before separately authorized landing. No runtime/model/provider/credential/merge/Ready/release/deploy."
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
    "project_state/gates/transition_preflight_result.json",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "tests/test_decision_preflight.py",
    "tests/test_control_plane_transition.py",
    "tests/test_codex_skills.py",
    ".github/workflows/ci.yml",
    "tests/test_agent_instruction_context.py"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
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
    "generated_governance_commit"
  ],
  "capability_policy": {
    "github_control_plane_network_exceptions": [
      "Publish only the exact codex/issue118-delegated-controller-authority-r2-v2-20261008 branch to dddd2024/Nerelan and create/update its single Draft PR against main after canonical publication readiness."
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
      "command_id": "delegation.implementation",
      "command": "Compress only the AGENTS.md Long-duration unattended section to a bounded linked entry. All delegated workflow semantics remain in existing docs/agents/governance-reference.md. Do not alter reference, tests, byte ceiling, compiler or runtime. Repair observed footprint failure and verify unchanged tests.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "AGENTS.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "delegation.validation",
      "command": "python -m pytest tests/test_agent_instruction_context.py tests/test_decision_preflight.py tests/test_control_plane_transition.py tests/test_codex_skills.py -q -p no:cacheprovider",
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
      "command_id": "delegation.publication",
      "command": "Publish only the exact codex/issue118-delegated-controller-authority-r2-v2-20261008 branch to dddd2024/Nerelan and create/update its single Draft PR against main after canonical publication readiness.",
      "phase": "publication",
      "required": false,
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
    }
  ],
  "issue_completion_close_allowed": [],
  "approval_event_or_time": "2026-10-08T06:09:32.343629+00:00",
  "owner_delegation_sha256": "f93f274e6c64d5da0ce72f3dab2ebb4227ec638e04183f57a3342dee6a5364ee",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 1,
  "development_correction_round_limit": 1,
  "mandatory_check_run_limit": 4,
  "execution_expires_at": "2026-10-08T09:22:21.386602+00:00"
}
```

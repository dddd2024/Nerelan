# Existing A2aa current-main recovery

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue1039_current_base_recovery_r2_v1",
  "round_id": "round_20261008_issue1039_current_base_recovery_r2_v1",
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
  "decision_scope": "ISSUE1039_CURRENT_MAIN_COLLECTOR_BINDING_RECOVERY",
  "source_issue": 1039,
  "parent_issue": 118,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; delegated selection and bounded approval of existing #1039 current-base source recovery.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue1039-current-base-recovery-r2-20261008",
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
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
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
    "specification": "Restore the three original A2a collector execution binding files from Draft #1040@3fb22f620fa3c91009b4b8ae7f46e463f91561cb at current main. Reuse existing evidence adapter and command parser. Required test selection must be nonempty, entire batch validated before execution, runner exit a true integer, target worktree cwd explicit, and HEAD/root reobserved around commands and workflows. Preserve existing original tests, authority, TaskStore and lifecycle. This establishes scoped execution binding, not protected verifier identity, atomic snapshot/ABA protection or full autonomous acceptance.",
    "reuse": "Exact original three source blobs, existing functional_validation and disk SQLite/Task/Run integration regressions; canonical transition kernel and publication guard. No additional store, judge, workflow or authority schema.",
    "execution_surface_note": "Full fresh main checkout, immutable Decision-only activation and PRE_EXECUTION_AUTHORIZED before source import. Precharge all spending. Model/provider/browser calls zero. Old candidate and failed/spent phase evidence remain unchanged.",
    "completion_boundary": "Exact three source blobs plus Decision, actual focused/full-checkout checks, natural exact-head CI and independent scoped review. Draft only; full unattended, provenance, landing or deployment not claimed."
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
    "reverse_agent/platform_v1/evidence_adapter.py",
    "tests/platform_v1/test_collector_execution_binding.py",
    "docs/evidence-collector-binding.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/evidence_adapter.py",
    "tests/platform_v1/test_collector_execution_binding.py",
    "docs/evidence-collector-binding.md"
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
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "tests/platform_v1/test_evidence_adapter.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".codex-skills/**",
    "AGENTS.md",
    "docs/agents/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
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
      "Publish only exact codex/issue1039-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "reverse_agent/platform_v1/evidence_adapter.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "a2a.implementation",
      "command": "Restore the three original A2a collector execution binding files from Draft #1040@3fb22f620fa3c91009b4b8ae7f46e463f91561cb at current main. Reuse existing evidence adapter and command parser. Required test selection must be nonempty, entire batch validated before execution, runner exit a true integer, target worktree cwd explicit, and HEAD/root reobserved around commands and workflows. Preserve existing original tests, authority, TaskStore and lifecycle. This establishes scoped execution binding, not protected verifier identity, atomic snapshot/ABA protection or full autonomous acceptance.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "source_edit",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/evidence_adapter.py",
        "tests/platform_v1/test_collector_execution_binding.py",
        "docs/evidence-collector-binding.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "a2a.validation",
      "command": "python -m pytest tests/platform_v1/test_collector_execution_binding.py tests/platform_v1/test_evidence_adapter.py tests/test_control_plane_transition.py tests/test_decision_preflight.py -q -p no:cacheprovider",
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
      "command_id": "a2a.publication",
      "command": "Publish only exact codex/issue1039-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness.",
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
  "approval_event_or_time": "2026-10-08T06:21:31.220369+00:00",
  "owner_delegation_sha256": "47b8f83df14cc81308eaf6e331f7b5b5e396c6b96bf640df2511890c99f6c301",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 1,
  "development_correction_round_limit": 2,
  "mandatory_check_run_limit": 4,
  "execution_expires_at": "2026-10-08T09:22:21.386602+00:00",
  "reference_implementation": {
    "repository": "dddd2024/Nerelan",
    "pr": 1040,
    "head": "3fb22f620fa3c91009b4b8ae7f46e463f91561cb",
    "files": [
      {
        "path": "reverse_agent/platform_v1/evidence_adapter.py",
        "blob_sha": "1c02af9302fffc79f122f6cd820a55c7e97540e0",
        "sha256": "3dd3e926168e632587f4709cabb410d5054f1c7f1fbd5b4fcbabdc32407a8b8d",
        "bytes": 22550,
        "original_base_blob": "83f7d58b460b6ad78997ffe0573d8b167471883e",
        "main_blob": "83f7d58b460b6ad78997ffe0573d8b167471883e",
        "main_unchanged_from_original_base": true
      },
      {
        "path": "tests/platform_v1/test_collector_execution_binding.py",
        "blob_sha": "d7230f54870743047f4d6261e91a5f9396a4eeef",
        "sha256": "e9a28eb2792af33b3a3a7c040c64d0bf436e5ec7259149a4b36a9984c9483ee5",
        "bytes": 13575,
        "original_base_blob": null,
        "main_blob": null,
        "main_unchanged_from_original_base": true
      },
      {
        "path": "docs/evidence-collector-binding.md",
        "blob_sha": "2a6ee5beab10dac429e4b41440a7811eb98cdf2c",
        "sha256": "d8821f1e2100cb4b48a788c66e3cf95bea758bfaec30056d232edacb733706c5",
        "bytes": 4900,
        "original_base_blob": null,
        "main_blob": null,
        "main_unchanged_from_original_base": true
      }
    ]
  }
}
```

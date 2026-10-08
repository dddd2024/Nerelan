# Existing EBA-1a current-main recovery

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue1037_current_base_recovery_r2_v1",
  "round_id": "round_20261008_issue1037_current_base_recovery_r2_v1",
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
  "decision_scope": "ISSUE1037_CURRENT_MAIN_EBA1_REPORT_RECOVERY",
  "source_issue": 1037,
  "parent_issue": 118,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; delegated selection and bounded approval of existing #1037 current-base source recovery.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue1037-current-base-recovery-r2-20261008",
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
    "specification": "Restore the three original EBA-1a files from Draft #1038@3bb5548270e0560b0ef13fc9fe9f2500e850c621 at current main. Reuse existing functional validation, TaskStore and tests. Strict count/format report consistency must reject zero-test, all-skipped, failing, malformed, duplicate TAP and contradictory stored evidence. Existing execution/environment, contract/artifact bindings, lifecycle and original tests unchanged. This establishes report consistency, not trusted producer/collector provenance or full autonomous acceptance.",
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
    "reverse_agent/platform_v1/functional_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
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
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_artifact_handoff.py",
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
      "Publish only exact codex/issue1037-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "eba1.implementation",
      "command": "Restore the three original EBA-1a files from Draft #1038@3bb5548270e0560b0ef13fc9fe9f2500e850c621 at current main. Reuse existing functional validation, TaskStore and tests. Strict count/format report consistency must reject zero-test, all-skipped, failing, malformed, duplicate TAP and contradictory stored evidence. Existing execution/environment, contract/artifact bindings, lifecycle and original tests unchanged. This establishes report consistency, not trusted producer/collector provenance or full autonomous acceptance.",
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
        "reverse_agent/platform_v1/functional_validation.py",
        "tests/platform_v1/test_functional_report_consistency.py",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "eba1.validation",
      "command": "python -m pytest tests/platform_v1/test_functional_report_consistency.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_artifact_handoff.py tests/test_control_plane_transition.py tests/test_decision_preflight.py -q -p no:cacheprovider",
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
      "command_id": "eba1.publication",
      "command": "Publish only exact codex/issue1037-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness.",
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
  "approval_event_or_time": "2026-10-08T06:14:34.519416+00:00",
  "owner_delegation_sha256": "477db715d0ad35f9330670d55da90b2c4905187f30edab34e4c1e198cfcdfa7d",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 1,
  "development_correction_round_limit": 2,
  "mandatory_check_run_limit": 4,
  "execution_expires_at": "2026-10-08T09:22:21.386602+00:00",
  "reference_implementation": {
    "repository": "dddd2024/Nerelan",
    "pr": 1038,
    "head": "3bb5548270e0560b0ef13fc9fe9f2500e850c621",
    "files": [
      {
        "path": "reverse_agent/platform_v1/functional_validation.py",
        "blob_sha": "6771006e5347337af468305eea0576a14c0be62a",
        "sha256": "7b28cf8361ce763df8e4c3a40b65a2522eb4508f9372b18af0e20b7ffc09ad27",
        "bytes": 34026,
        "original_base_blob": "84a9c3c04e0425b6ec4ed55f7848d102158ee49d",
        "main_blob": "84a9c3c04e0425b6ec4ed55f7848d102158ee49d",
        "main_unchanged_from_original_base": true
      },
      {
        "path": "tests/platform_v1/test_functional_report_consistency.py",
        "blob_sha": "790187d16dec682029bdb3eab4ef3dd67f8346f2",
        "sha256": "7923d10155120a50db65edefafc461c234ce9dac51dd00098d5b9ca2039706f0",
        "bytes": 12305,
        "original_base_blob": null,
        "main_blob": null,
        "main_unchanged_from_original_base": true
      },
      {
        "path": "docs/functional-validation.md",
        "blob_sha": "ee2afe402b78c4f66dc1e7bee32a900a35d78659",
        "sha256": "e80e417f3d4e257997e008fdc86115eae296b396f015be4107be3a3be0b5a6d0",
        "bytes": 11270,
        "original_base_blob": "63cd425d669f895f3f0c767e0ded255ffe8fbe6b",
        "main_blob": "63cd425d669f895f3f0c767e0ded255ffe8fbe6b",
        "main_unchanged_from_original_base": true
      }
    ]
  }
}
```

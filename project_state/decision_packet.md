# Owner-delegated pure canonical policy preview

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue118_policy_preview_r3_v1",
  "round_id": "round_20261003_issue118_policy_preview_r3_v1",
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
  "decision_scope": "PURE_CANONICAL_AUTONOMY_POLICY_PREVIEW",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Owner full-project delegation authorizes this necessary bounded pure first stage; project R0/R1 Work Item adapter cannot execute R3, so Codex fallback implements under Path B. This is not a quota reset for previous work or authority for privileged actions.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "codex/issue118-policy-preview-r3-v1-20261003",
  "fresh_worktree_creation_required": false,
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
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
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
    "specification": "Owner explicit full-project delegation prospectively authorizes the roadmap1010 A3 first pure policy-preview/evaluation stage of Issue118 Phase A. Source Issue118 remains planning, not authority; this bounded R3 Decision is the applicable authority. Reuse current AutonomyService, KNOWN_OPERATIONS, MAX_WINDOW_DURATION, CapabilityRegistry, canonical_json/sha256_json and sensitive-key rejection. Implement a pure canonical candidate policy normalizer and operation preview, with all Issue118 canonical categories: schema/id/revision/owner and declared confirmation metadata, creation/start/expiry, repository/base-branch/head-branch/path/goal/capability scope, worker delegation, check/review/merge constraints, publication/version/artifact/credential-reference targets, deployment/rollback data, operation and cost/token/time/retry budgets, stop/notification/summary rules and canonical digest. Normalize immutably without mutating input, preserve meaningful precision, strict finite types/bounds and stable sanitized denials; canonical digest binds all fields and is insertion/set-order invariant where order has no semantic meaning. Evaluate expiry/not-started/revoked or stale identity/digest/revision, exact request scope, upper-authority intersection/expansion, supported backend capability, worker roles, exact-head/check/review conditions, publication/artifact/version/environment/rollback constraints, operation/usage/runtime/retry budgets including unknown usage fail closed. A preview always reports execution_authorized=false and owner_confirmation_verified=false: declaration strings and supplied upstream observations are input data, not independently verified authority. No activated policy/window/token/receipt or side effect is produced. Future privileged operations remain unavailable in current registry, even if payload claims approval. Expose AutonomyService.preview without altering activate/authorize/summary, existing store/schema/claims/budgets/receipts or coordinator behavior. No second policy/authority/store, no Gate/receipt invented to enable landing, no dependency/provider/credential resolver, runtime/API/frontend/workflow/security-setting changes. control_store.py and test_autonomy.py remain original-owner occupied and read-only. Only three named source/test paths; preserve every existing test/assertion. Fresh exact-main branch in same owned checkout preserves five known generated gates; Decision-only activation and actual PRE_EXECUTION_AUTHORIZED plus activation Draft precede product changes. At most eight provider-free checks and two bounded scoped correction rounds: legacy autonomy baseline<=180s; new preview focus<=180s; combined legacy/preview<=180s; mandatory full Platform with unchanged four installed-OpenCode exclusions<=2400s and durable native failure capture/JUnit; Path-A<=120s; one exact committed-head combined autonomy suite<=180s; at most two additional scoped development checks if justified. Full mandatory failure/timeout stops publication and has no retry. One product commit after mandatory precommit success, two normal exact-branch pushes total, one Draft, exact-head description rebinding and natural source-head CI. No Ready/Merge/main push/comments/Issue closure/rerun/dispatch, models/providers/credential access/install/browser or existing runtime mutation. Completion boundary is this pure preview source candidate and actual checks/Draft/CI; live activation/persistence, revocation/recovery, trusted A2 identity and privileged adapters remain unimplemented subsequent stages. Do not claim Issue118 or whole backlog complete.",
    "completion_boundary": "Pure canonical policy preview stage only; exact source tests/Draft/natural CI required; independent acceptance/landing and all further Issue118 phases separate."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/autonomy_policy_preview.py",
    "tests/platform_v1/test_autonomy_policy_preview.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/autonomy_policy_preview.py",
    "tests/platform_v1/test_autonomy_policy_preview.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    ".codex-skills/registry.json",
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/test_path_a_gate.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/credential_relay.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "frontend/package*.json",
    "frontend/node_modules/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "**/auth.json",
    "frontend/**",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py"
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing provider-free pytest-owned temporary loopback fixtures only; no real models/providers/Internet/existing runtime."
    ],
    "github_control_plane_network_exceptions": [
      "Exactly two normal pushes to codex/issue118-policy-preview-r3-v1-20261003, one activation Draft against main@9092911f41a089e249f27c883526904299be1d17, exact-head description updates and bounded read-only GitHub CI observation. No other writes."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "policy.bootstrap",
      "command": "Fresh exact-main branch, preserve known generated gates; one Decision-only activation, actual startup/plan/lint/preflight/readiness, one activation push and Draft before source changes.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md",
        "reverse_agent/platform_v1/workspace_drift.py",
        "tests/platform_v1/test_workspace_drift.py"
      ],
      "produced_artifacts": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "policy.implement",
      "command": "Owner explicit full-project delegation prospectively authorizes the roadmap1010 A3 first pure policy-preview/evaluation stage of Issue118 Phase A. Source Issue118 remains planning, not authority; this bounded R3 Decision is the applicable authority. Reuse current AutonomyService, KNOWN_OPERATIONS, MAX_WINDOW_DURATION, CapabilityRegistry, canonical_json/sha256_json and sensitive-key rejection. Implement a pure canonical candidate policy normalizer and operation preview, with all Issue118 canonical categories: schema/id/revision/owner and declared confirmation metadata, creation/start/expiry, repository/base-branch/head-branch/path/goal/capability scope, worker delegation, check/review/merge constraints, publication/version/artifact/credential-reference targets, deployment/rollback data, operation and cost/token/time/retry budgets, stop/notification/summary rules and canonical digest. Normalize immutably without mutating input, preserve meaningful precision, strict finite types/bounds and stable sanitized denials; canonical digest binds all fields and is insertion/set-order invariant where order has no semantic meaning. Evaluate expiry/not-started/revoked or stale identity/digest/revision, exact request scope, upper-authority intersection/expansion, supported backend capability, worker roles, exact-head/check/review conditions, publication/artifact/version/environment/rollback constraints, operation/usage/runtime/retry budgets including unknown usage fail closed. A preview always reports execution_authorized=false and owner_confirmation_verified=false: declaration strings and supplied upstream observations are input data, not independently verified authority. No activated policy/window/token/receipt or side effect is produced. Future privileged operations remain unavailable in current registry, even if payload claims approval. Expose AutonomyService.preview without altering activate/authorize/summary, existing store/schema/claims/budgets/receipts or coordinator behavior. No second policy/authority/store, no Gate/receipt invented to enable landing, no dependency/provider/credential resolver, runtime/API/frontend/workflow/security-setting changes. control_store.py and test_autonomy.py remain original-owner occupied and read-only. Only three named source/test paths; preserve every existing test/assertion. Fresh exact-main branch in same owned checkout preserves five known generated gates; Decision-only activation and actual PRE_EXECUTION_AUTHORIZED plus activation Draft precede product changes. At most eight provider-free checks and two bounded scoped correction rounds: legacy autonomy baseline<=180s; new preview focus<=180s; combined legacy/preview<=180s; mandatory full Platform with unchanged four installed-OpenCode exclusions<=2400s and durable native failure capture/JUnit; Path-A<=120s; one exact committed-head combined autonomy suite<=180s; at most two additional scoped development checks if justified. Full mandatory failure/timeout stops publication and has no retry. One product commit after mandatory precommit success, two normal exact-branch pushes total, one Draft, exact-head description rebinding and natural source-head CI. No Ready/Merge/main push/comments/Issue closure/rerun/dispatch, models/providers/credential access/install/browser or existing runtime mutation. Completion boundary is this pure preview source candidate and actual checks/Draft/CI; live activation/persistence, revocation/recovery, trusted A2 identity and privileged adapters remain unimplemented subsequent stages. Do not claim Issue118 or whole backlog complete.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/autonomy.py",
        "reverse_agent/platform_v1/autonomy_policy_preview.py",
        "tests/platform_v1/test_autonomy_policy_preview.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "policy.validate",
      "command": "At most8 provider-free checks and2 scoped correction rounds, all mandatory native checks as specified; full-suite failure/timeout stops publication without retry; one product commit then exact-head focused/legacy check; scoped diff and actual readiness. Native JUnit and unchanged source required.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "commit",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/autonomy.py",
        "reverse_agent/platform_v1/autonomy_policy_preview.py",
        "tests/platform_v1/test_autonomy_policy_preview.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "policy.publish",
      "command": "Two normal pushes to exact codex/issue118-policy-preview-r3-v1-20261003, one activation Draft against main@9092911f41a089e249f27c883526904299be1d17, exact-head body binding, bounded natural CI; no Ready/Merge/Issue close/comments/dispatch/rerun.",
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
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Same owned checkout, only five known generated gates carried over. External authority/helper/native evidence under issue118-policy-preview-r3-v1, no cleanup or gate staging."
  },
  "follows_last_decision_id": "decision_20261003_issue829_validation_r2_v3",
  "follows_last_round_id": "round_20261003_issue829_validation_r2_v3",
  "workstream_id": "issue118-policy-preview-r3-v1",
  "source_issues": [
    118,
    1010
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 8,
  "development_correction_round_limit": 2,
  "execution_window_hours": 8,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T05:33:50.832144+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0
}
```

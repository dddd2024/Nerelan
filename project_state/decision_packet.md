# Exact-main bounded late text Draft publication

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue980_late_text_main_publication_r2_v1",
  "round_id": "round_20261003_issue980_late_text_main_publication_r2_v1",
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
  "decision_scope": "EXACT_MAIN_LATE_TEXT_DRAFT_PUBLICATION",
  "source_issue": 980,
  "parent_issue": 280,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Current explicit full-project Owner delegation permits necessary two-file Codex fallback and exact Draft publication. Live GitHub compare confirms main9092911f. Separate exact-main source slice, not publication of local695/native history.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "codex/issue980-late-text-main-r2-v1-20261003",
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
    "specification": "Current explicit Owner full project delegation. Transfer only the reviewed12-line late-evidence source hunk and60-line tests plus import from local66d95166 to a fresh branch based on exact observed main9092911f, preserving main OpenCode linked-worktree implementation and every other source/runtime/frontend file. A whole local OpenCode file transfer would import unrelated unmerged Native preparation and is forbidden. Separate owned full worktree F:\\Nerelan-issue980-late-text-publication protects existing frontend/services/gates. Exact patch issue980-narrow-transfer.patch from66 parent diff only two files. Zero providers/models/credentials/install/browser/host; one Decision activation, one product commit, two exact branch push attempts, one Draft against main, exact-head description rebinding and bounded read-only natural CI observation. Draft/actual PRE_EXECUTION_AUTHORIZED precede source patch transfer. Run original text/executor provider-free pytest, AST builder-only, scoped diff check, actual PUBLICATION_READY. No Ready/Merge/main push/comments/Issue closure/history rewrite/workflow rerun/dispatch or independent self-acceptance. Preserve v1 scope conflict and all prior artifacts. Previous failed system/native calls are not retried. Candidate source behavior remains exactly v2 specification: last usable late typed text within40 evidence items, original redaction/status/schema/task/protocol/executor behavior unchanged except selection; no arbitrary nested/reasoning text.",
    "completion_boundary": "Exact-main two-file Draft candidate, local actual checks and natural CI terminal evidence if available. Independent acceptance and landing remain separate. Whole GitHub goal incomplete."
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_text_evidence.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_text_evidence.py"
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
    "tests/platform_v1/test_artifact_handoff.py",
    "tests/platform_v1/test_functional_execution.py",
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "tests/platform_v1/test_codex_integration.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "frontend/vite.config.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx"
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
    "frontend/**"
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
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Exactly two pushes to codex/issue980-late-text-main-r2-v1-20261003 in dddd2024/Nerelan only, one Draft against main9092911f, exact-head description rebind, read-only natural Actions observation. No other GitHub writes."
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
      "command_id": "ui.bootstrap",
      "command": "External preview approved command plan, fresh exact-main owned linked worktree/branch and Decision-only activation; actual startup/plan/lint/preflight/readiness and activation push/Draft before source transfer. Preserve original frontend/runtime worktree.",
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
        "project_state/decision_packet.md"
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
      "command_id": "late_text.implement",
      "command": "Current explicit Owner full project delegation. Transfer only the reviewed12-line late-evidence source hunk and60-line tests plus import from local66d95166 to a fresh branch based on exact observed main9092911f, preserving main OpenCode linked-worktree implementation and every other source/runtime/frontend file. A whole local OpenCode file transfer would import unrelated unmerged Native preparation and is forbidden. Separate owned full worktree F:\\Nerelan-issue980-late-text-publication protects existing frontend/services/gates. Exact patch issue980-narrow-transfer.patch from66 parent diff only two files. Zero providers/models/credentials/install/browser/host; one Decision activation, one product commit, two exact branch push attempts, one Draft against main, exact-head description rebinding and bounded read-only natural CI observation. Draft/actual PRE_EXECUTION_AUTHORIZED precede source patch transfer. Run original text/executor provider-free pytest, AST builder-only, scoped diff check, actual PUBLICATION_READY. No Ready/Merge/main push/comments/Issue closure/history rewrite/workflow rerun/dispatch or independent self-acceptance. Preserve v1 scope conflict and all prior artifacts. Previous failed system/native calls are not retried. Candidate source behavior remains exactly v2 specification: last usable late typed text within40 evidence items, original redaction/status/schema/task/protocol/executor behavior unchanged except selection; no arbitrary nested/reasoning text.",
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
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_opencode_text_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "late_text.validate",
      "command": "Provider-free python -B -m pytest tests/platform_v1/test_opencode_text_evidence.py tests/platform_v1/test_opencode_executor.py -q -p no:cacheprovider; exact two-file diff check, source AST limits, unchanged Decision, actual worktree readiness and local one source commit only.",
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
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "late_text.publish",
      "command": "Exactly two branch pushes, one activation Draft against main9092911f and exact-head description rebind after product push. Natural CI read-only observations. No Ready/Merge/comments/Issue closure or other refs.",
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
    "note": "Fresh exact-main owned publication worktree and external issue980-main-publication-v1. Preserve existing issue1027/UI/private source/config/services/worktrees. No generated gates staged."
  },
  "follows_last_decision_id": "decision_20261003_issue980_late_text_r2_v1",
  "follows_last_round_id": "round_20261003_issue980_late_text_r2_v1",
  "workstream_id": "issue980-main-publication-v1",
  "source_issues": [
    986,
    985
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 4,
  "development_correction_round_limit": 2,
  "execution_window_hours": 2,
  "integration_observation_surface": "user_local_owned_planning_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-02T16:23:24.898536+00:00",
  "credential_status_probe_limit": 8,
  "provider_network_call_limit": 0
}
```

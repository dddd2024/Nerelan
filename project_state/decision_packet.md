# Bounded complete workspace-drift semantic successor

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue829_semantic_successor_r2_v1",
  "round_id": "round_20261003_issue829_semantic_successor_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "WORKSPACE_DRIFT_COMPLETE_SEMANTIC_SUCCESSOR",
  "source_issue": 829,
  "parent_issue": 800,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Current explicit full-project Owner delegation; fresh main and all39 open PR file lists verified; no overlap. Distinct829 successor, not renewed980 or model budget.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "codex/issue829-semantic-successor-r2-v1-20261003",
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
    "specification": "Current explicit Owner full-project delegation authorizes a fresh exact-main successor for Issue829, not amendment or revival of closed-unmerged semantic-negative PR978. Reuse only its two source/test blobs as reviewed content, never its branch history, authority or acceptance. Repair ALL four confirmed main residuals: bounded Git argv batching for 3000-10000 paths, semantic index identity ignoring stat/fsmonitor cache changes, storage-format-aware SHA1/SHA256 object validation, and hard streaming stdout/stderr/time bounds. Additionally preserve CE_INTENT_TO_ADD identity, skip-worktree and assume-unchanged semantics; empty-file git add -N to ordinary git add must classify LOCAL_GENERATION_CHANGED while cache-only refresh remains equal. Keep existing public capture/classify interfaces, actor-neutral states, secret-free bounded output, fixed Git argv and ambient GIT_* removal, no lazy fetch/replace objects/filter/hooks/fsmonitor/setup/remote helpers, scratch-only observation writes, staged blob availability/type verification, unusual valid path identity, no new store/dependency or execution-path integration. Only reverse_agent/platform_v1/workspace_drift.py and tests/platform_v1/test_workspace_drift.py may change. Retain all landed security tests and useful predecessor regressions, add actual intent-to-add/cache/batching/format/stream-limit regressions without skip/xfail weakening. Existing trusted Git/Python and provider-free test-owned temporary repositories, inert hook/filter/helper sentinels, bounded child processes and ordinary supported OS process cleanup are allowed only in these deterministic regressions; no existing user worktree/process/runtime/config mutation. Original project execution has already failed to produce a reviewed source result; use authorized Codex source fallback, with zero new model/provider/credential calls. No installs/browser/host launches. Run scoped drift, executor_neutral+functional_validation, full provider-free Platform V1, Path-A suite and diff check with native JUnit. Existing four opted-in OpenCode integrations stay excluded as in unchanged natural CI, not passed. All focused/mandatory failures stop publication until repaired within scope; unavailable OS cases are explicitly unverified. Separate owned fresh full checkout at exact observed main protects all prior work. Actual generated plan and PRE_EXECUTION_AUTHORIZED before source; Decision-only activation Draft before source adoption. One activation, one product commit, two normal exact-branch pushes and one Draft only. No rerun/dispatch/comments/Issue closure/Ready/Merge/main push/history rewrite or self-certified independent acceptance.",
    "completion_boundary": "Complete two-file residual repair with exact-head checks and Draft publication; independent exact-head acceptance and landing separate; full GitHub goal incomplete."
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
    "reverse_agent/platform_v1/workspace_drift.py",
    "tests/platform_v1/test_workspace_drift.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/workspace_drift.py",
    "tests/platform_v1/test_workspace_drift.py"
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
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "tests/executor_neutral",
    "tests/platform_v1/test_functional_validation.py",
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
      "Two normal pushes to codex/issue829-semantic-successor-r2-v1-20261003 in dddd2024/Nerelan, one Draft against main@9092911f41a089e249f27c883526904299be1d17, exact-head description binding and bounded read-only natural CI. No other GitHub writes."
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
      "command_id": "drift.bootstrap",
      "command": "Fresh owned exact-main checkout, one Decision-only activation, actual startup/plan/lint/preflight/readiness; activation push and Draft before source adoption.",
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
      "command_id": "drift.implement",
      "command": "Current explicit Owner full-project delegation authorizes a fresh exact-main successor for Issue829, not amendment or revival of closed-unmerged semantic-negative PR978. Reuse only its two source/test blobs as reviewed content, never its branch history, authority or acceptance. Repair ALL four confirmed main residuals: bounded Git argv batching for 3000-10000 paths, semantic index identity ignoring stat/fsmonitor cache changes, storage-format-aware SHA1/SHA256 object validation, and hard streaming stdout/stderr/time bounds. Additionally preserve CE_INTENT_TO_ADD identity, skip-worktree and assume-unchanged semantics; empty-file git add -N to ordinary git add must classify LOCAL_GENERATION_CHANGED while cache-only refresh remains equal. Keep existing public capture/classify interfaces, actor-neutral states, secret-free bounded output, fixed Git argv and ambient GIT_* removal, no lazy fetch/replace objects/filter/hooks/fsmonitor/setup/remote helpers, scratch-only observation writes, staged blob availability/type verification, unusual valid path identity, no new store/dependency or execution-path integration. Only reverse_agent/platform_v1/workspace_drift.py and tests/platform_v1/test_workspace_drift.py may change. Retain all landed security tests and useful predecessor regressions, add actual intent-to-add/cache/batching/format/stream-limit regressions without skip/xfail weakening. Existing trusted Git/Python and provider-free test-owned temporary repositories, inert hook/filter/helper sentinels, bounded child processes and ordinary supported OS process cleanup are allowed only in these deterministic regressions; no existing user worktree/process/runtime/config mutation. Original project execution has already failed to produce a reviewed source result; use authorized Codex source fallback, with zero new model/provider/credential calls. No installs/browser/host launches. Run scoped drift, executor_neutral+functional_validation, full provider-free Platform V1, Path-A suite and diff check with native JUnit. Existing four opted-in OpenCode integrations stay excluded as in unchanged natural CI, not passed. All focused/mandatory failures stop publication until repaired within scope; unavailable OS cases are explicitly unverified. Separate owned fresh full checkout at exact observed main protects all prior work. Actual generated plan and PRE_EXECUTION_AUTHORIZED before source; Decision-only activation Draft before source adoption. One activation, one product commit, two normal exact-branch pushes and one Draft only. No rerun/dispatch/comments/Issue closure/Ready/Merge/main push/history rewrite or self-certified independent acceptance.",
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
        "reverse_agent/platform_v1/workspace_drift.py",
        "tests/platform_v1/test_workspace_drift.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "drift.validate",
      "command": "Provider-free python -B -m pytest tests/platform_v1/test_workspace_drift.py -q -p no:cacheprovider; python -B -m pytest tests/executor_neutral tests/platform_v1/test_functional_validation.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1 -q -p no:cacheprovider excluding only unchanged CI opt-in OpenCode cases; python -B -m pytest tests/test_path_a_gate.py -q -p no:cacheprovider; native JUnit, git diff --check, actual PUBLICATION_READY; one product commit after all required local checks pass.",
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
      "command_id": "drift.publish",
      "command": "Two exact normal pushes to codex/issue829-semantic-successor-r2-v1-20261003, one activation Draft against main@9092911f41a089e249f27c883526904299be1d17, exact-head description binding; read-only natural CI. No other writes.",
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
    "note": "Fresh owned F:\\Nerelan-issue829-semantic-successor only; external issue829-semantic-successor-v1 evidence. No existing worktree cleanup or generated-gate staging."
  },
  "follows_last_decision_id": "decision_20261003_issue980_late_text_main_publication_r2_v1",
  "follows_last_round_id": "round_20261003_issue980_late_text_main_publication_r2_v1",
  "workstream_id": "issue829-semantic-successor-v1",
  "source_issues": [
    829,
    652,
    800
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 8,
  "development_correction_round_limit": 3,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T03:23:10.475029+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0
}
```

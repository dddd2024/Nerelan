# Approved single-file line-ending repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue118_single_file_line_ending_repair_r2_v1",
  "round_id": "round_20261008_issue118_single_file_line_ending_repair_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE118_SINGLE_FILE_LINE_ENDING_REPAIR",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 Owner via explicit chat approval 批准继续",
  "approval_basis": "User explicitly approved immediately preceding one-file line-ending proposal and finite additional checks.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-fixture-continuation-r2-20261008",
  "base_sha": "7bd146b0d32c71792c566626a9d3a7ccbaf697bf",
  "activation_base_sha": "7bd146b0d32c71792c566626a9d3a7ccbaf697bf",
  "starting_head": "7bd146b0d32c71792c566626a9d3a7ccbaf697bf",
  "required_branch": "codex/issue118-line-endings-r2-20261008",
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
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": false,
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
    "specification": "Owner replied 批准继续 on 2026-10-08 to the concrete one-file CRLF-to-LF proposal and one correction, one development check, four mandatory checks. Preserve all prior Decisions, failures and cumulative spending; do not reset any counter or extend any original deadline. Fresh exact local planning branch from7bd146b0d32c71792c566626a9d3a7ccbaf697bf, which contains the two HTTP fixture repairs and earlier product candidate. Only frontend/src/components/goal-composer.tsx may change, by replacing CRLF with LF while retaining every other byte. Original/proposed worktree SHA256 are frozen in the prior unapplied-line-ending-proposal.json. No behavior, test, assertion, config, whitespace-policy or exclusion weakening. Codex fallback because trusted project runtime remains unaccepted and expired; no real Task/Goal/window activation.\nAdditional finite local allowance: one immutable Decision activation, one source correction, one development typecheck <=120s, four mandatory invocations (canonical precommit and postcommit gate sequences, committed-range git diff --check from82c9b185a66561d17cf8a6857cd3add2d23215ca, and full provider-free platform/root-adapter pytest <=2400s with only the four original opt-in exclusions), one product commit. No repeated passed frontend suite or focused checks because only line endings change; prior unit evidence is historical and full exact-head pytest provides current backend acceptance. Append/fsync new spending, retaining prior ledgers and consumed attempts. Original absolute repair deadline remains2026-10-08T03:21:27.885456+00:00, no renewal. Stop on any mandatory failure, unavailable capability, source/hash/scope drift, expiry or exhaustion; no automatic successor. All gate deltas remain unstageable.\nNo remote writes/push/Draft/comments/mark-ready/merge/main/tag/release, no CI rerun/dispatch, models/providers/secrets, installs/workflows, real runtime/browser/native startup, destructive cleanup or historical database writes. Only owned disposable provider-free pytest localhost fixtures. Canonical PUBLICATION_READY is a local guard result, not independent acceptance or publication authority. Remote CI, independent acceptance, native resizing, actual Goal execution and cold-service restart remain incomplete and deferred, never claimed completed by this local-only repair.",
    "completion_boundary": "Local CRLF normalization and exact-head deterministic checks only; no remote/native/mainline/full-goal acceptance."
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
    "frontend/src/components/goal-composer.tsx"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/src/components/goal-composer.tsx"
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
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env",
    "**/auth.json"
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
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch",
    "self_independent_acceptance"
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
      "Provider-free ephemeral localhost test fixture HTTP only. No real runtime."
    ],
    "github_control_plane_network_exceptions": [
      "Bounded read-only observation only; all GitHub writes prohibited."
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
      "command_id": "native.bootstrap",
      "command": "Fresh bounded Decision-only activation and canonical gates",
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
      "command_id": "native.implementation",
      "command": "Owner replied 批准继续 on 2026-10-08 to the concrete one-file CRLF-to-LF proposal and one correction, one development check, four mandatory checks. Preserve all prior Decisions, failures and cumulative spending; do not reset any counter or extend any original deadline. Fresh exact local planning branch from7bd146b0d32c71792c566626a9d3a7ccbaf697bf, which contains the two HTTP fixture repairs and earlier product candidate. Only frontend/src/components/goal-composer.tsx may change, by replacing CRLF with LF while retaining every other byte. Original/proposed worktree SHA256 are frozen in the prior unapplied-line-ending-proposal.json. No behavior, test, assertion, config, whitespace-policy or exclusion weakening. Codex fallback because trusted project runtime remains unaccepted and expired; no real Task/Goal/window activation.\nAdditional finite local allowance: one immutable Decision activation, one source correction, one development typecheck <=120s, four mandatory invocations (canonical precommit and postcommit gate sequences, committed-range git diff --check from82c9b185a66561d17cf8a6857cd3add2d23215ca, and full provider-free platform/root-adapter pytest <=2400s with only the four original opt-in exclusions), one product commit. No repeated passed frontend suite or focused checks because only line endings change; prior unit evidence is historical and full exact-head pytest provides current backend acceptance. Append/fsync new spending, retaining prior ledgers and consumed attempts. Original absolute repair deadline remains2026-10-08T03:21:27.885456+00:00, no renewal. Stop on any mandatory failure, unavailable capability, source/hash/scope drift, expiry or exhaustion; no automatic successor. All gate deltas remain unstageable.\nNo remote writes/push/Draft/comments/mark-ready/merge/main/tag/release, no CI rerun/dispatch, models/providers/secrets, installs/workflows, real runtime/browser/native startup, destructive cleanup or historical database writes. Only owned disposable provider-free pytest localhost fixtures. Canonical PUBLICATION_READY is a local guard result, not independent acceptance or publication authority. Remote CI, independent acceptance, native resizing, actual Goal execution and cold-service restart remain incomplete and deferred, never claimed completed by this local-only repair.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/goal-composer.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "One development frontend typecheck; four mandatory gate/diff/full-pytest invocations per specification. No runtime or remote write.",
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
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Owned external test scratch only, no historical DB writes or actual runtime."
  },
  "workstream_id": "issue118-line-ending-continuation-20261008",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 0,
  "execution_window_hours": 2,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-08T01:33:32.140547+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 0,
  "runtime_acceptance_limits": {
    "clone": 0,
    "stack_start": 0,
    "browser_start": 0,
    "observations": 0,
    "normal_cleanup": 0,
    "real_provider_free_windows": 0,
    "source_corrections": 1,
    "expires_at": "2026-10-08T03:21:27.885456+00:00"
  },
  "development_check_run_limit": 1,
  "development_correction_round_limit": 1,
  "mandatory_pytest_process_limit": 1,
  "owned_test_scratch_root": "F:\\reverse-agent-artifacts\\worktree-audit-20261002-56c5\\issue118-line-ending-continuation-20261008\\test-scratch",
  "cumulative_prior_development_checks": 26,
  "cumulative_prior_correction_rounds": 22,
  "cumulative_development_check_limit": 27,
  "cumulative_correction_round_limit": 23,
  "mandatory_check_run_limit": 4
}
```

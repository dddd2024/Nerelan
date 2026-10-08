# Approved two-file local fixture continuation

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue118_two_http_fixture_continuation_r2_v1",
  "round_id": "round_20261008_issue118_two_http_fixture_continuation_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE118_TWO_HTTP_FIXTURE_LOCAL_CONTINUATION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 Owner via explicit chat approval 批准继续",
  "approval_basis": "User approval on 2026-10-08 of the immediately preceding two-file additional correction/check request.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-delegated-policy-recovery-r3-v1-20261007",
  "base_sha": "e0f12c1e1d9e5893e835f14ad6ade345f57f5f40",
  "activation_base_sha": "e0f12c1e1d9e5893e835f14ad6ade345f57f5f40",
  "starting_head": "e0f12c1e1d9e5893e835f14ad6ade345f57f5f40",
  "required_branch": "codex/issue118-fixture-continuation-r2-20261008",
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
  "product_change_commit_limit": 2,
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
    "specification": "Owner replied 批准继续 on 2026-10-08 after a concrete request for two extra fixture paths and additional bounded correction/check allowance. New local-only continuation, not a reset or extension of the expired 2026-10-07 authority. Preserve every prior Decision, failure, spending ledger, commit, Draft and absolute expiry. Exact local planning base e0f12c1e1d9e5893e835f14ad6ade345f57f5f40 already contains the reviewed product candidate; do not edit its product/backend/frontend files. Only the two named HTTP fixture modules may change, by explicit in-process legacy AutonomyService injection, retaining all assertions and strict production defaults. Frozen proposal is unapplied-fixture-alignment-proposal.patch in the prior external evidence store. No additional exclusions, skips or weakened assertions. Project fallback remains Codex because the trusted runtime was not accepted and its prior real execution authority expired; do not activate a caller-declared window.\nAdditional allowances: one Decision activation/fresh local branch, at most two two-file correction cycles, two development pytest invocations <=900s each, six mandatory check invocations including at most two full pytest processes <=2400s each, two source commits. Bootstrap canonical gates are one bounded sequence; final canonical gates one mandatory invocation. Required checks: focused two HTTP files together with task service production strict negatives, full platform plus the two original root adapter modules with only the same four original provider opt-ins deselected, git diff --check against both the new local base and original phase6 integration base82c9, canonical preflight and publication-readiness. Count every attempt at start in an append-only external ledger with inherited totals; original ledgers never change. Expiry is a fresh two-hour local repair window, not a renewal of original native/browser/model authority. Stop on mandatory failure, scope/hash drift, expiry or exhausted added allowance. No automatic successor. Commit only named source paths, never generated gates.\nNo GitHub writes/push/Draft/comments/mark-ready/merge/main/tag/release, CI rerun/dispatch, models/providers/credentials, installs/workflows, browser/native/runtime startup, real Task/Goal/window activation, destructive cleanup or historical DB mutation. Synthetic provider-free localhost fixtures only. Full Issue118/backlog/native/persistence acceptance remains unproven. Independent exact-head review and remote CI are deferred, not waived or claimed by these local checks.",
    "completion_boundary": "Local two-fixture repair and deterministic exact-head verification only; no native/remote/mainline/full-goal acceptance."
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
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_goal_completion_evidence.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_goal_completion_evidence.py"
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
      "command": "Owner replied 批准继续 on 2026-10-08 after a concrete request for two extra fixture paths and additional bounded correction/check allowance. New local-only continuation, not a reset or extension of the expired 2026-10-07 authority. Preserve every prior Decision, failure, spending ledger, commit, Draft and absolute expiry. Exact local planning base e0f12c1e1d9e5893e835f14ad6ade345f57f5f40 already contains the reviewed product candidate; do not edit its product/backend/frontend files. Only the two named HTTP fixture modules may change, by explicit in-process legacy AutonomyService injection, retaining all assertions and strict production defaults. Frozen proposal is unapplied-fixture-alignment-proposal.patch in the prior external evidence store. No additional exclusions, skips or weakened assertions. Project fallback remains Codex because the trusted runtime was not accepted and its prior real execution authority expired; do not activate a caller-declared window.\nAdditional allowances: one Decision activation/fresh local branch, at most two two-file correction cycles, two development pytest invocations <=900s each, six mandatory check invocations including at most two full pytest processes <=2400s each, two source commits. Bootstrap canonical gates are one bounded sequence; final canonical gates one mandatory invocation. Required checks: focused two HTTP files together with task service production strict negatives, full platform plus the two original root adapter modules with only the same four original provider opt-ins deselected, git diff --check against both the new local base and original phase6 integration base82c9, canonical preflight and publication-readiness. Count every attempt at start in an append-only external ledger with inherited totals; original ledgers never change. Expiry is a fresh two-hour local repair window, not a renewal of original native/browser/model authority. Stop on mandatory failure, scope/hash drift, expiry or exhausted added allowance. No automatic successor. Commit only named source paths, never generated gates.\nNo GitHub writes/push/Draft/comments/mark-ready/merge/main/tag/release, CI rerun/dispatch, models/providers/credentials, installs/workflows, browser/native/runtime startup, real Task/Goal/window activation, destructive cleanup or historical DB mutation. Synthetic provider-free localhost fixtures only. Full Issue118/backlog/native/persistence acceptance remains unproven. Independent exact-head review and remote CI are deferred, not waived or claimed by these local checks.",
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
        "tests/platform_v1/test_artifact_handoff_http.py",
        "tests/platform_v1/test_goal_completion_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "Bounded local focused/full provider-free pytest, scoped committed-range git diff --check and canonical gates, per exact specification; no runtime or GitHub writes.",
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
  "workstream_id": "issue118-fixture-continuation-20261008",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 0,
  "execution_window_hours": 2,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-08T01:21:27.885456+00:00",
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
    "source_corrections": 2,
    "expires_at": "2026-10-08T03:21:27.885456+00:00"
  },
  "development_check_run_limit": 2,
  "development_correction_round_limit": 2,
  "mandatory_pytest_process_limit": 2,
  "owned_test_scratch_root": "F:\\reverse-agent-artifacts\\worktree-audit-20261002-56c5\\issue118-fixture-continuation-20261008\\test-scratch",
  "cumulative_prior_development_checks": 24,
  "cumulative_prior_correction_rounds": 20,
  "cumulative_development_check_limit": 26,
  "cumulative_correction_round_limit": 22,
  "mandatory_check_run_limit": 6
}
```

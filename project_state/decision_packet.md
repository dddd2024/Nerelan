# Owner-delegated correction of confirmed policy preview findings

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_pr1066_correction_r3_v1",
  "round_id": "round_20261003_pr1066_correction_r3_v1",
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
  "decision_scope": "PREVIEW_HEAD_AND_NOTIFICATION_OBLIGATION_CORRECTION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Persistent Owner delegation authorizes corrective work for newly confirmed advisory defects, bounded prospectively without changing prior authority or budgets.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-policy-preview-r3-v1-20261003",
  "base_sha": "34875cc3deeab463c1b4cb16e5e72ad2cd33b5af",
  "activation_base_sha": "34875cc3deeab463c1b4cb16e5e72ad2cd33b5af",
  "starting_head": "34875cc3deeab463c1b4cb16e5e72ad2cd33b5af",
  "required_branch": "codex/issue118-preview-obligations-r3-v1-20261003",
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
    "specification": "Owner persistent full-project delegation prospectively authorizes a NEW bounded corrective candidate for two actual project-review findings in Draft1066 at exact34875cc3. Project reviewer succeeded with full tracked source2927 blobs/zero mismatches, source/config unchanged, but advisory is not independent acceptance. Supervisor provider-free diagnosis check7/8 reproduced missing commit identity for supported open_draft_pr and four dropped upper notification obligations. Original source CI remains success, not functional acceptance. Preserve original Decisions, budgets, commits and reports; this does not amend/retry an old failed trial or authorize any model retry. Fresh branch from explicit planning integration codex/issue118-policy-preview-r3-v1-20261003 at34875cc3, no implicit main base. Decision-only activation, actual PRE_EXECUTION_AUTHORIZED/readiness and exact activation Draft against that integration branch precede product changes. Exactly two product paths. Require commit head binding for open_draft_pr independent of optional check/review declarations; retain no mandatory reviewer for initial Draft because independent acceptance is required only before separately authorized promotion. Bind future declared push_task_branch/delete_merged_branch head-sensitive operations if present; unavailable adapters stay unavailable. Upper true notifications on_completion/on_blocked/on_failure/summary_at_expiry cannot be dropped by a lower policy; false upper may be strengthened to true. Preserve all current always-false authority flags, no-store/no-side-effect behavior, strict data/digest/identity/usage/revocation and component-sensitive glob semantics. Do not weaken paths to legacy adapter fnmatch, clear a valid candidate digest on upper denial, or perform cosmetic cleanup. Add meaningful regressions for missing/mismatched/valid publication head with no checks/reviews and each notification obligation/allowed strengthening. Preserve every original test/function/assertion except exact implementation conditions. Original AutonomyService and original-owner control_store.py/test_autonomy.py remain byte-identical to base. No runtime/API/frontend/store/schema/provider/credential/model/browser/install/dependency/workflow/security-setting changes. Current project R0/R1 Work Item adapter refuses R3 before backend; Codex fallback performs this bounded source correction rather than bypassing that policy. At most6 provider-free check processes: mandatory combined legacy/preview<=180s, mandatory full Platform V1 with same4 installed-OpenCode exclusions<=2400s, Path-A<=120s, exact committed-head combined<=180s; at most2 additional scoped development checks if justified and2 scoped correction rounds. Full mandatory failure/timeout stops publication without retry. One product commit, at most2 normal exact-branch pushes total and1 activation Draft; only its description may be updated to exact source head/natural CI evidence. No comments/Issue updates/closure/Ready/Merge/main push/rewrite/dispatch/rerun or other PR writes. Complete only this corrective source candidate, actual mandatory validation and natural exact-head CI; independent acceptance, actual activation and all later Issue118/backlog work remain separate. Four-hour window.",
    "completion_boundary": "Corrective preview source candidate, native mandatory checks and natural source CI; not independent acceptance/landing/Issue118 completion."
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
    "tests/test_path_a_gate.py",
    "reverse_agent/platform_v1/autonomy.py"
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
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "reverse_agent/platform_v1/capability_registry.py"
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
      "At most2 normal pushes to exact codex/issue118-preview-obligations-r3-v1-20261003,1 activation Draft against explicit codex/issue118-policy-preview-r3-v1-20261003@34875cc3deeab463c1b4cb16e5e72ad2cd33b5af, exact-head description updates and bounded read-only natural CI observation. No other writes."
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
      "command_id": "correction.bootstrap",
      "command": "Preserve gates and immutable parent34875cc3, fresh explicit integration-base branch, one Decision-only activation, actual startup/plan/lint/preflight/readiness, one activation push and Draft before product changes.",
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
      "command_id": "correction.implement",
      "command": "Owner persistent full-project delegation prospectively authorizes a NEW bounded corrective candidate for two actual project-review findings in Draft1066 at exact34875cc3. Project reviewer succeeded with full tracked source2927 blobs/zero mismatches, source/config unchanged, but advisory is not independent acceptance. Supervisor provider-free diagnosis check7/8 reproduced missing commit identity for supported open_draft_pr and four dropped upper notification obligations. Original source CI remains success, not functional acceptance. Preserve original Decisions, budgets, commits and reports; this does not amend/retry an old failed trial or authorize any model retry. Fresh branch from explicit planning integration codex/issue118-policy-preview-r3-v1-20261003 at34875cc3, no implicit main base. Decision-only activation, actual PRE_EXECUTION_AUTHORIZED/readiness and exact activation Draft against that integration branch precede product changes. Exactly two product paths. Require commit head binding for open_draft_pr independent of optional check/review declarations; retain no mandatory reviewer for initial Draft because independent acceptance is required only before separately authorized promotion. Bind future declared push_task_branch/delete_merged_branch head-sensitive operations if present; unavailable adapters stay unavailable. Upper true notifications on_completion/on_blocked/on_failure/summary_at_expiry cannot be dropped by a lower policy; false upper may be strengthened to true. Preserve all current always-false authority flags, no-store/no-side-effect behavior, strict data/digest/identity/usage/revocation and component-sensitive glob semantics. Do not weaken paths to legacy adapter fnmatch, clear a valid candidate digest on upper denial, or perform cosmetic cleanup. Add meaningful regressions for missing/mismatched/valid publication head with no checks/reviews and each notification obligation/allowed strengthening. Preserve every original test/function/assertion except exact implementation conditions. Original AutonomyService and original-owner control_store.py/test_autonomy.py remain byte-identical to base. No runtime/API/frontend/store/schema/provider/credential/model/browser/install/dependency/workflow/security-setting changes. Current project R0/R1 Work Item adapter refuses R3 before backend; Codex fallback performs this bounded source correction rather than bypassing that policy. At most6 provider-free check processes: mandatory combined legacy/preview<=180s, mandatory full Platform V1 with same4 installed-OpenCode exclusions<=2400s, Path-A<=120s, exact committed-head combined<=180s; at most2 additional scoped development checks if justified and2 scoped correction rounds. Full mandatory failure/timeout stops publication without retry. One product commit, at most2 normal exact-branch pushes total and1 activation Draft; only its description may be updated to exact source head/natural CI evidence. No comments/Issue updates/closure/Ready/Merge/main push/rewrite/dispatch/rerun or other PR writes. Complete only this corrective source candidate, actual mandatory validation and natural exact-head CI; independent acceptance, actual activation and all later Issue118/backlog work remain separate. Four-hour window.",
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
        "reverse_agent/platform_v1/autonomy_policy_preview.py",
        "tests/platform_v1/test_autonomy_policy_preview.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "correction.validate",
      "command": "At most6 provider-free check processes and2 scoped correction rounds; mandatory combined/full Platform/Path-A/exact committed combined as specified, native JUnit, original tests and read-only reference byte identity; mandatory full failure has no retry.",
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
        "reverse_agent/platform_v1/autonomy_policy_preview.py",
        "tests/platform_v1/test_autonomy_policy_preview.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "correction.publish",
      "command": "At most2 normal exact-branch pushes,1 activation Draft against explicit codex/issue118-policy-preview-r3-v1-20261003@34875cc3deeab463c1b4cb16e5e72ad2cd33b5af, exact-head description rebinding and bounded natural CI observation; no other GitHub writes.",
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
    "note": "Existing five generated gates preserved unstaged; external pr1066-correction-r3-v1 evidence only. No cleanup or original runtime/model changes."
  },
  "follows_last_decision_id": "decision_20261003_issue118_policy_preview_r3_v1",
  "follows_last_round_id": "round_20261003_issue118_policy_preview_r3_v1",
  "workstream_id": "pr1066-correction-r3-v1",
  "source_issues": [
    118,
    1010
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 2,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T06:58:58.202558+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0
}
```

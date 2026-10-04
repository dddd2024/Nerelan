# Durable autonomous-window lifecycle prerequisite for Issue118

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_window_lifecycle_r3_v1",
  "round_id": "round_20261004_issue118_window_lifecycle_r3_v1",
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
  "decision_scope": "ISSUE118_DURABLE_WINDOW_LIFECYCLE",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / explicit current Owner full architecture delegation",
  "approval_basis": "Current Owner delegates implementation and routine scoped decisions; this prospective bounded source phase preserves all privileged publication and independent acceptance boundaries.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue118-window-lifecycle-r3-v1-20261004",
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
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "The current Owner explicitly delegates full responsibility to implement the unattended-platform architecture and identifies its GitHub Issue. Live Issue118 is the canonical architecture target, with separately governed phases. This NEW Phase-E lifecycle foundation addresses concrete runtime races before canonical-policy integration: serialize expiry/replay/conflict checking and insertion in the existing TaskStore SQLite transaction so concurrent hosts cannot activate two windows; reserve a future-start active window against competing activation; retain immutable policy revision/digest and historical replay without reactivation or reset of task/retry/usage counters. AutonomyService delegates activation exclusivity to that store transaction, and authorization checks the exact requested currently active window rather than existence of any window. Require expiry/start and identity fences to remain fail closed. Reuse existing TaskStore, window rows, coordinator claims/reservations, receipts and API; no second database, authority schema, Gate, runtime, verifier or unrestricted Boolean. Browser identity/ACTIVATE is NOT authenticated Owner authority; no claim that this slice implements canonical Owner verification or privileged adapters. No model or existing runtime launch/mutation; the observed project executor's R0/R1 adapter rejects R3 source work before dispatch, so use authorized Codex source fallback rather than bypassing the adapter or retrying the failed native reviewer. Explicit fresh main97d766d base, not obsolete origin/main; reuse idle F controller preserving its old Decision/native failure and five unstaged generated gates. Decision-only activation, canonical startup/plan/lint/preflight/readiness and exact activation Draft precede product changes. Exactly four product paths: autonomy.py, control_store.py, a new lifecycle regression test, and explanatory lifecycle documentation. Preserve all original tests and schema/fields/capabilities/budget accounting. Add meaningful multi-connection concurrency, scheduled-window reservation, same-revision conflict, restart/replay/counter preservation, stopped/expired replay, stale-window authorization and denied-receipt tests; use owned file-backed SQLite fixtures and controlled clocks, never real TaskStore/runtime. Development max6 provider-free pytest processes <=300s each and max3 correction rounds; only repeat after a change/failure/unresolved need. Final mandatory full PlatformV1 once<=2400s with only four preexisting installed OpenCode opt-in deselections, PathA once<=120s, committed exact-head lifecycle+autonomy+coordinator/budget regressions once<=300s. Mandatory failure stops this candidate publication, no retry or implicit renewal. Freeze all four source files during checks, retain real logs/JUnit/native exit and source hashes; git diff --check and scoped publication readiness. One Decision activation commit, one product commit, two normal pushes to exact branch, one Draft against main@97d766d, at most6 description updates; natural exact-head Actions original logs/artifacts read only. No Ready/Merge/main push/auto-merge/rebase/rewrite/tag/release/deploy/Issue or PR comments/closure/runner/workflow dispatch or rerun/install/credential/model/browser/private-session access. Source candidate and CI are not independent acceptance, canonical-policy/privileged-operation completion or mainline landing. Whole118 and all122Issue backlog remain the full objective; this critical-path prerequisite does not replace them. Absolute six-hour expiry and actual cumulative counters within this separate source window, no transfer/reset of prior811 budgets. No automatic successor grant.",
    "completion_boundary": "Atomic durable-window lifecycle and exact-window authorization source implementation with actual provider-free checks and source CI; all remaining architecture stages and independent landing acceptance remain required."
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
    "reverse_agent/platform_v1/control_store.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "docs/unattended-window-lifecycle.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "docs/unattended-window-lifecycle.md"
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
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_unattended_coordinator_shutdown.py",
    ".github/workflows/ci.yml"
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
    "reverse_agent/model_access/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "**/auth.json",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/publication_controller.py",
    "tests/platform_v1/test_autonomy.py"
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
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
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
      "New owned provider-free test loopback fixtures only; no model/provider/existing services."
    ],
    "github_control_plane_network_exceptions": [
      "Two normal pushes to codex/issue118-window-lifecycle-r3-v1-20261004, one activation Draft against main@97d766d7253378c093c31ed29c990cb6921f2ae4, max6 exact-head body updates; bounded natural CI/log/artifact and live authority readback only. No other writes."
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
      "command_id": "window.bootstrap",
      "command": "Fresh exact-main branch preserving existing five gates, Decision-only commit, canonical preflight/readiness, exact activation Draft before any product mutation.",
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
      "command_id": "window.implementation",
      "command": "The current Owner explicitly delegates full responsibility to implement the unattended-platform architecture and identifies its GitHub Issue. Live Issue118 is the canonical architecture target, with separately governed phases. This NEW Phase-E lifecycle foundation addresses concrete runtime races before canonical-policy integration: serialize expiry/replay/conflict checking and insertion in the existing TaskStore SQLite transaction so concurrent hosts cannot activate two windows; reserve a future-start active window against competing activation; retain immutable policy revision/digest and historical replay without reactivation or reset of task/retry/usage counters. AutonomyService delegates activation exclusivity to that store transaction, and authorization checks the exact requested currently active window rather than existence of any window. Require expiry/start and identity fences to remain fail closed. Reuse existing TaskStore, window rows, coordinator claims/reservations, receipts and API; no second database, authority schema, Gate, runtime, verifier or unrestricted Boolean. Browser identity/ACTIVATE is NOT authenticated Owner authority; no claim that this slice implements canonical Owner verification or privileged adapters. No model or existing runtime launch/mutation; the observed project executor's R0/R1 adapter rejects R3 source work before dispatch, so use authorized Codex source fallback rather than bypassing the adapter or retrying the failed native reviewer. Explicit fresh main97d766d base, not obsolete origin/main; reuse idle F controller preserving its old Decision/native failure and five unstaged generated gates. Decision-only activation, canonical startup/plan/lint/preflight/readiness and exact activation Draft precede product changes. Exactly four product paths: autonomy.py, control_store.py, a new lifecycle regression test, and explanatory lifecycle documentation. Preserve all original tests and schema/fields/capabilities/budget accounting. Add meaningful multi-connection concurrency, scheduled-window reservation, same-revision conflict, restart/replay/counter preservation, stopped/expired replay, stale-window authorization and denied-receipt tests; use owned file-backed SQLite fixtures and controlled clocks, never real TaskStore/runtime. Development max6 provider-free pytest processes <=300s each and max3 correction rounds; only repeat after a change/failure/unresolved need. Final mandatory full PlatformV1 once<=2400s with only four preexisting installed OpenCode opt-in deselections, PathA once<=120s, committed exact-head lifecycle+autonomy+coordinator/budget regressions once<=300s. Mandatory failure stops this candidate publication, no retry or implicit renewal. Freeze all four source files during checks, retain real logs/JUnit/native exit and source hashes; git diff --check and scoped publication readiness. One Decision activation commit, one product commit, two normal pushes to exact branch, one Draft against main@97d766d, at most6 description updates; natural exact-head Actions original logs/artifacts read only. No Ready/Merge/main push/auto-merge/rebase/rewrite/tag/release/deploy/Issue or PR comments/closure/runner/workflow dispatch or rerun/install/credential/model/browser/private-session access. Source candidate and CI are not independent acceptance, canonical-policy/privileged-operation completion or mainline landing. Whole118 and all122Issue backlog remain the full objective; this critical-path prerequisite does not replace them. Absolute six-hour expiry and actual cumulative counters within this separate source window, no transfer/reset of prior811 budgets. No automatic successor grant.",
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
        "reverse_agent/platform_v1/control_store.py",
        "tests/platform_v1/test_autonomy_window_lifecycle.py",
        "docs/unattended-window-lifecycle.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "window.validation",
      "command": "Max6 development checks<=300s and3 correction rounds; final mandatory fullPlatform once2400s/PathA once120s/committed focused once300s; existing4 opt-in deselections only, original logs/XML, source freeze and git diff check.",
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
      "command_id": "window.publication",
      "command": "Max2 normal pushes/1 Draft against main@97d766d7253378c093c31ed29c990cb6921f2ae4/6 description updates, natural CI original evidence readback only, no landing or comments.",
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
    "note": "Preserve old five generated gates unstaged and old failed native window; only new owned disposable SQLite/pytest fixtures under F:/nrl-window118-v1 and external evidence directory. No existing host/model/runtime changes."
  },
  "workstream_id": "issue118-window-lifecycle-r3-v1",
  "source_issues": [
    118
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 3,
  "execution_window_hours": 6,
  "integration_observation_surface": "user_local_exact_main_fresh_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-04T06:00:04.757249+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6,
  "owned_test_scratch_root": "F:\\nrl-window118-v1",
  "mandatory_pytest_process_limit": 3,
  "cumulative_development_check_limit": 6,
  "cumulative_correction_round_limit": 3
}
```

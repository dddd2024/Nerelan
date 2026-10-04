# Actual Windows native-client acceptance for118/384

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_native_browser_acceptance_r3_v1",
  "round_id": "round_20261004_issue118_native_browser_acceptance_r3_v1",
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
  "decision_scope": "ISSUE118_ACTUAL_WINDOWS_PRIVATE_CLIENT_ACCEPTANCE",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / explicit current Owner full architecture delegation",
  "approval_basis": "Existing explicit Owner takeover/frontend-opening/full architecture delegation; prospective bounded real runtime acceptance, no source/model/privileged-publication renewal.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-client-guard-bootstrap-r3-v1-20261004",
  "base_sha": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "activation_base_sha": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "starting_head": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "required_branch": "codex/issue118-native-browser-acceptance-r3-v1-20261004",
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
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
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
  "local_browser_execution_allowed": true,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Current Owner's explicit project takeover, frontend-opening and full unattended-architecture delegation authorizes this separately bounded real Windows runtime acceptance, not a retry or budget reset of the closed source phase1081. Source1b99c23d is locally/natively verified but Draft, unaccepted and unmerged. Preserve original source3/8 dev,4/4 corrections,3 mandatory checks,2/2 pushes, all failures and original absolute expiry. This runtime phase has NO source correction or product commit, NO models/provider calls/credential reads/auth-list probes/unknown tools/install/real task execution/window activation/privileged publication. Before any runtime operation create this immutable Decision-only activation, canonical plan/preflight/readiness and its own exact Draft againstcodex/issue118-client-guard-bootstrap-r3-v1-20261004@1b99c23d1e6c51289b973b2bbfe893627353af6f. Project runtime is used directly, not simulated.\nOne new owned temporary local clone only atF:\\nrl-auth118-native1, exact source1b99c23d1e6c51289b973b2bbfe893627353af6f, canonical origin dddd2024/Nerelan, not a new registered worktree. Source controller and accepted healthy frontend/old runtime processes are READ ONLY. Clone all tracked code from the known source; bind actual commit/tree/hash and disclose runtime deltas. Runtime-only frontend vite.config.ts may add cacheDir beneath the new owned clone so the existing frontend node_modules junction stays read-only. No frontend application, backend, trusted broker or launcher algorithm may change. Use existing mature playwright-core1.62.1 via read-only junction to F:/reverse-agent/frontend/node_modules; no dependency/cache modification or install. Known Node SHA58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f and Microsoft-signed Edge SHA39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907 only. No existing browser, host, saved configuration or unrelated window is modified.\nAt most1 supported dev-up launch (180seconds),1 owned native browser launch,1 Vite/combined stack startup,2 bounded acceptance observation invocations (<=180seconds each), and1 normal owned dev-down cleanup (120seconds). Frontend18879, Task18877, Model18878 must be free before launch; relay is owned ephemeral loopback. Fresh runtime TaskStore and ModelProfileStore are empty with no bindings, connections, secrets or external sessions; verify no OpenCode/auth-list/model subprocess. All real project HTTP observations stay on exactly these owned loopback ports, no public token-fetch/command endpoint. No private capability in argv/env/URL/files/logs/evidence/renderer/network screenshots. Never read the host's private value; use boolean HTTP outcomes and sanitized process metadata.\nUse actual Windows UI Automation/Win32 observation on the exact owned Edge window identified by process tree, creation times and frontend18879 address. Read-only UI navigation is limited to home/tasks/settings; capture owned-window pixels, not simulated screenshots. Observe positive Task API reads through real frontend, then unrelated native missing-capability/no-Origin requests must be401 before any task/window/store mutation; GEThealth exposes readiness only. Do not perform synthetic fixtures as real product implementation or claim Owner activation/upper authority/compiler/Model Control authentication solved.\nClose only the exact owned browser window through native UI; observe broker PID, creation time, ready flag and group lifecycle rather than assuming exit from browser disconnect. Preserve original outcome on any browser-close/private-stdin/readiness defect. Failure stops this acceptance and forbids another launch or source change under this packet; no automatic successor, retry or reset. Normal cleanup uses only this clone's canonical dev-down with verified ownership; never name-wide kill, PID-only kill, reset, clean, stash, delete or remove existing work. Record real commands, exits, timestamps, pixel evidence, frontend/backend source hashes, safety deltas and all receipts. Unknown usage is not zero. This is provider-free actual client acceptance, not independent audit, full384/full118/all backlog completion or mainline landing. Expiry2026-10-04T12:26:34.697358+00:00 with no renewal.",
    "completion_boundary": "Actual owned Windows frontend/native private transport and browser-only closure evidence; source defects stop this phase. No complete architecture, independent acceptance or landing claim."
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
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "frontend/**",
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
      "Owned real frontend18879/Task18877/Model18878/ephemeral relay only; no models/provider/auth probes/other listeners."
    ],
    "github_control_plane_network_exceptions": [
      "One activation push exactcodex/issue118-native-browser-acceptance-r3-v1-20261004, one Draft againstcodex/issue118-client-guard-bootstrap-r3-v1-20261004@1b99c23d1e6c51289b973b2bbfe893627353af6f,2 descriptions, bounded read-only natural CI and authority; no other writes."
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
      "command": "Fresh exact-base branch, immutable Decision-only activation and canonical gates; Draft before any actual runtime.",
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
      "command": "Current Owner's explicit project takeover, frontend-opening and full unattended-architecture delegation authorizes this separately bounded real Windows runtime acceptance, not a retry or budget reset of the closed source phase1081. Source1b99c23d is locally/natively verified but Draft, unaccepted and unmerged. Preserve original source3/8 dev,4/4 corrections,3 mandatory checks,2/2 pushes, all failures and original absolute expiry. This runtime phase has NO source correction or product commit, NO models/provider calls/credential reads/auth-list probes/unknown tools/install/real task execution/window activation/privileged publication. Before any runtime operation create this immutable Decision-only activation, canonical plan/preflight/readiness and its own exact Draft againstcodex/issue118-client-guard-bootstrap-r3-v1-20261004@1b99c23d1e6c51289b973b2bbfe893627353af6f. Project runtime is used directly, not simulated.\nOne new owned temporary local clone only atF:\\nrl-auth118-native1, exact source1b99c23d1e6c51289b973b2bbfe893627353af6f, canonical origin dddd2024/Nerelan, not a new registered worktree. Source controller and accepted healthy frontend/old runtime processes are READ ONLY. Clone all tracked code from the known source; bind actual commit/tree/hash and disclose runtime deltas. Runtime-only frontend vite.config.ts may add cacheDir beneath the new owned clone so the existing frontend node_modules junction stays read-only. No frontend application, backend, trusted broker or launcher algorithm may change. Use existing mature playwright-core1.62.1 via read-only junction to F:/reverse-agent/frontend/node_modules; no dependency/cache modification or install. Known Node SHA58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f and Microsoft-signed Edge SHA39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907 only. No existing browser, host, saved configuration or unrelated window is modified.\nAt most1 supported dev-up launch (180seconds),1 owned native browser launch,1 Vite/combined stack startup,2 bounded acceptance observation invocations (<=180seconds each), and1 normal owned dev-down cleanup (120seconds). Frontend18879, Task18877, Model18878 must be free before launch; relay is owned ephemeral loopback. Fresh runtime TaskStore and ModelProfileStore are empty with no bindings, connections, secrets or external sessions; verify no OpenCode/auth-list/model subprocess. All real project HTTP observations stay on exactly these owned loopback ports, no public token-fetch/command endpoint. No private capability in argv/env/URL/files/logs/evidence/renderer/network screenshots. Never read the host's private value; use boolean HTTP outcomes and sanitized process metadata.\nUse actual Windows UI Automation/Win32 observation on the exact owned Edge window identified by process tree, creation times and frontend18879 address. Read-only UI navigation is limited to home/tasks/settings; capture owned-window pixels, not simulated screenshots. Observe positive Task API reads through real frontend, then unrelated native missing-capability/no-Origin requests must be401 before any task/window/store mutation; GEThealth exposes readiness only. Do not perform synthetic fixtures as real product implementation or claim Owner activation/upper authority/compiler/Model Control authentication solved.\nClose only the exact owned browser window through native UI; observe broker PID, creation time, ready flag and group lifecycle rather than assuming exit from browser disconnect. Preserve original outcome on any browser-close/private-stdin/readiness defect. Failure stops this acceptance and forbids another launch or source change under this packet; no automatic successor, retry or reset. Normal cleanup uses only this clone's canonical dev-down with verified ownership; never name-wide kill, PID-only kill, reset, clean, stash, delete or remove existing work. Record real commands, exits, timestamps, pixel evidence, frontend/backend source hashes, safety deltas and all receipts. Unknown usage is not zero. This is provider-free actual client acceptance, not independent audit, full384/full118/all backlog completion or mainline landing. Expiry2026-10-04T12:26:34.697358+00:00 with no renewal.",
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
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "Current Owner's explicit project takeover, frontend-opening and full unattended-architecture delegation authorizes this separately bounded real Windows runtime acceptance, not a retry or budget reset of the closed source phase1081. Source1b99c23d is locally/natively verified but Draft, unaccepted and unmerged. Preserve original source3/8 dev,4/4 corrections,3 mandatory checks,2/2 pushes, all failures and original absolute expiry. This runtime phase has NO source correction or product commit, NO models/provider calls/credential reads/auth-list probes/unknown tools/install/real task execution/window activation/privileged publication. Before any runtime operation create this immutable Decision-only activation, canonical plan/preflight/readiness and its own exact Draft againstcodex/issue118-client-guard-bootstrap-r3-v1-20261004@1b99c23d1e6c51289b973b2bbfe893627353af6f. Project runtime is used directly, not simulated.\nOne new owned temporary local clone only atF:\\nrl-auth118-native1, exact source1b99c23d1e6c51289b973b2bbfe893627353af6f, canonical origin dddd2024/Nerelan, not a new registered worktree. Source controller and accepted healthy frontend/old runtime processes are READ ONLY. Clone all tracked code from the known source; bind actual commit/tree/hash and disclose runtime deltas. Runtime-only frontend vite.config.ts may add cacheDir beneath the new owned clone so the existing frontend node_modules junction stays read-only. No frontend application, backend, trusted broker or launcher algorithm may change. Use existing mature playwright-core1.62.1 via read-only junction to F:/reverse-agent/frontend/node_modules; no dependency/cache modification or install. Known Node SHA58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f and Microsoft-signed Edge SHA39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907 only. No existing browser, host, saved configuration or unrelated window is modified.\nAt most1 supported dev-up launch (180seconds),1 owned native browser launch,1 Vite/combined stack startup,2 bounded acceptance observation invocations (<=180seconds each), and1 normal owned dev-down cleanup (120seconds). Frontend18879, Task18877, Model18878 must be free before launch; relay is owned ephemeral loopback. Fresh runtime TaskStore and ModelProfileStore are empty with no bindings, connections, secrets or external sessions; verify no OpenCode/auth-list/model subprocess. All real project HTTP observations stay on exactly these owned loopback ports, no public token-fetch/command endpoint. No private capability in argv/env/URL/files/logs/evidence/renderer/network screenshots. Never read the host's private value; use boolean HTTP outcomes and sanitized process metadata.\nUse actual Windows UI Automation/Win32 observation on the exact owned Edge window identified by process tree, creation times and frontend18879 address. Read-only UI navigation is limited to home/tasks/settings; capture owned-window pixels, not simulated screenshots. Observe positive Task API reads through real frontend, then unrelated native missing-capability/no-Origin requests must be401 before any task/window/store mutation; GEThealth exposes readiness only. Do not perform synthetic fixtures as real product implementation or claim Owner activation/upper authority/compiler/Model Control authentication solved.\nClose only the exact owned browser window through native UI; observe broker PID, creation time, ready flag and group lifecycle rather than assuming exit from browser disconnect. Preserve original outcome on any browser-close/private-stdin/readiness defect. Failure stops this acceptance and forbids another launch or source change under this packet; no automatic successor, retry or reset. Normal cleanup uses only this clone's canonical dev-down with verified ownership; never name-wide kill, PID-only kill, reset, clean, stash, delete or remove existing work. Record real commands, exits, timestamps, pixel evidence, frontend/backend source hashes, safety deltas and all receipts. Unknown usage is not zero. This is provider-free actual client acceptance, not independent audit, full384/full118/all backlog completion or mainline landing. Expiry2026-10-04T12:26:34.697358+00:00 with no renewal.",
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
      "command_id": "native.publication",
      "command": "One exact activation push and Draft, two truthful evidence descriptions; no landing. codex/issue118-native-browser-acceptance-r3-v1-20261004",
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
    "note": "Exactly new owned external runtimeF:\\nrl-auth118-native1; one clone/stack/browser, readonly shared deps, cacheDir safety config only. Never stage runtime/evidence. Existing runtimes preserved."
  },
  "workstream_id": "issue118-native-browser-acceptance-r3-v1",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 1,
  "execution_window_hours": 1.5,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 1,
  "frontend_launch_limit": 1,
  "approval_event_or_time": "2026-10-04T10:56:34.697358+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 2,
  "runtime_acceptance_limits": {
    "clone": 1,
    "stack_start": 1,
    "browser_start": 1,
    "observations": 2,
    "normal_cleanup": 1,
    "source_corrections": 0,
    "source_checks_replay": 0,
    "prior_source_dev_spent": 3,
    "prior_source_corrections_spent": 4,
    "prior_source_original_deadline": "2026-10-04T14:55:31.639949+00:00",
    "owned_runtime_root": "F:\\nrl-auth118-native1",
    "expires_at": "2026-10-04T12:26:34.697358+00:00"
  }
}
```

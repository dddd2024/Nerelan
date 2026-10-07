# Actual Windows native-client acceptance for118/384

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_native_browser_acceptance_r3_v3",
  "round_id": "round_20261004_issue118_native_browser_acceptance_r3_v3",
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
  "approval_basis": "Owner explicitly approved v3 scope, activation-bound 90-minute window, then exact updated signed Edge fingerprint on 2026-10-07; all failure/spending history preserved.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-launcher-compatibility-r3-v2-20261004",
  "base_sha": "86caba45888455994b0e43c820833878a8a5bac1",
  "activation_base_sha": "86caba45888455994b0e43c820833878a8a5bac1",
  "starting_head": "86caba45888455994b0e43c820833878a8a5bac1",
  "required_branch": "codex/issue118-native-browser-acceptance-r3-v3-20261004",
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
    "specification": "# Explicitly selected new acceptance after observer failure \u2014 pending\n\nThis proposal grants no authority. The approved v2 execution is terminal: startup succeeded on source 86caba45888455994b0e43c820833878a8a5bac1, native client ready, real UIA home and visible Settings observed. Observation1 failed because it searched UIA Name for the address; observation2 failed foreground-window assertion. Canonical cleanup returned0, both owned Windows Jobs empty. No screenshots, positive/negative HTTP status or native browser-only closure acceptance completed. Do not classify these observer failures as product failures. Draft #1085 records the exact result.\n\n## Concrete observer changes selected for review\n\n1. Check the address through the uniquely identified native address Edit control's ValuePattern, normalizing optional http scheme/trailing slash, rather than searching all control names. Require exact loopback hostname and port18879. Retain broker executable/creation-time and Edge parent/executable/creation-time/owned-window binding.\n2. Use actual native PrintWindow rendering of the owned window for pixels, without depending on foreground ownership. Verify returned image visually; a blank/black/unavailable rendering is unverified and stops acceptance, never a synthetic screenshot. Do not capture another foreground window.\n3. Use the UIA names observed in v2: task navigation is Button `\u6253\u5f00\u4efb\u52a1\u5217\u8868`; Settings is Hyperlink `\u8bbe\u7f6e`, accessible through `\u66f4\u591a\u5bfc\u822a` if needed. Navigate home/tasks/settings by native UIA only; do not create goals/tasks/windows or save model configuration.\n4. Record actual frontend-frame read-only HTTP 200 using native browser DevTools UI; no capability value access or logging. Probe only the owned Task API without capability/no-Origin and require401; health readiness-only. If direct HTTP status evidence cannot be captured, mark incomplete rather than infer it from coordinator-online text.\n5. Close only the identity-bound Edge window through native WindowPattern.Close regardless of foreground. Observe original broker identity disappearing and readiness clearing before canonical identity-bound cleanup. Cleanup is mandatory on failure.\n\n## Exact requested new bounds\n\nKeep product source86caba/tree0b7ec91968977c2abb3920a2996a95e8e6ae0d7a unchanged, same approved ports18877/18878/18879 and known Node/signed Edge fingerprints. Fresh runtime F:/nrl-auth118-native3, only isolated cacheDir safety delta and read-only existing dependencies. Fresh branch codex/issue118-native-browser-acceptance-r3-v3-20261004 from source86caba, one immutable Decision-only activation, canonical existing gates, one push/one Draft against codex/issue118-launcher-compatibility-r3-v2-20261004, two description updates. No product commit/correction, install, models, credentials, source-test replay, workflow dispatch/rerun, Ready/merge/main/tag/release/deploy.\n\nAdd exactly one startup<=180s, one browser launch, two observations<=180s each, one owned cleanup<=120s. Cutoff remains 2026-10-04T15:30:00Z / tonight23:30 China, no extension/renewal/automatic successor. Require an 11-minute runtime/cleanup reserve plus preparation time before starting. Existing healthy frontend/runtime, failed native1 and terminal native2 remain untouched. Preserve every original failure and spending: source dev6/corrections7; prior runtime startups2, initial startup failed, second startup passed but acceptance incomplete; prior browser launches1 and observation invocations2. If v3 starts, aggregate runtime startups3, browser launches2, observation ceiling4. No counter reset.\n\nCurrent v2 Decision disallows automatic successors/retries; this additional startup therefore requires explicit Owner selection/approval of this new bounded scope before activation. Success would establish this client acceptance only, not independent review, full#118/#384, privileged adapter completion, landing or all backlog completion.\n\nEXPLICIT OWNER APPROVAL: Owner approved this exact v3 scope, then on 2026-10-07 approved its cutoff amendment to one 90-minute window frozen as absolute timestamps at first activation, then explicitly approved ONLY the Edge SHA256 update to d366716ba3cd2cc67d92d9b712b129fea4c8df769961d1e04b037ce034780ad0 at the same existing path with VALID Microsoft signature. These amendments supersede ONLY the originally proposed v3 fixed cutoff and browser fingerprint. All old absolute cutoffs/failures/counters remain historical. No automatic successor, expiry renewal or counter reset. Product source stays86caba; source corrections and checks replay zero.\n\nFROZEN ACTIVATION_START=2026-10-07T08:19:02.635253+00:00; EXPIRES_AT=2026-10-07T09:49:02.635253+00:00",
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
      "One activation push exactcodex/issue118-native-browser-acceptance-r3-v3-20261004, one Draft againstcodex/issue118-launcher-compatibility-r3-v2-20261004@86caba45888455994b0e43c820833878a8a5bac1,2 descriptions, bounded read-only natural CI and authority; no other writes."
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
      "command": "# Explicitly selected new acceptance after observer failure \u2014 pending\n\nThis proposal grants no authority. The approved v2 execution is terminal: startup succeeded on source 86caba45888455994b0e43c820833878a8a5bac1, native client ready, real UIA home and visible Settings observed. Observation1 failed because it searched UIA Name for the address; observation2 failed foreground-window assertion. Canonical cleanup returned0, both owned Windows Jobs empty. No screenshots, positive/negative HTTP status or native browser-only closure acceptance completed. Do not classify these observer failures as product failures. Draft #1085 records the exact result.\n\n## Concrete observer changes selected for review\n\n1. Check the address through the uniquely identified native address Edit control's ValuePattern, normalizing optional http scheme/trailing slash, rather than searching all control names. Require exact loopback hostname and port18879. Retain broker executable/creation-time and Edge parent/executable/creation-time/owned-window binding.\n2. Use actual native PrintWindow rendering of the owned window for pixels, without depending on foreground ownership. Verify returned image visually; a blank/black/unavailable rendering is unverified and stops acceptance, never a synthetic screenshot. Do not capture another foreground window.\n3. Use the UIA names observed in v2: task navigation is Button `\u6253\u5f00\u4efb\u52a1\u5217\u8868`; Settings is Hyperlink `\u8bbe\u7f6e`, accessible through `\u66f4\u591a\u5bfc\u822a` if needed. Navigate home/tasks/settings by native UIA only; do not create goals/tasks/windows or save model configuration.\n4. Record actual frontend-frame read-only HTTP 200 using native browser DevTools UI; no capability value access or logging. Probe only the owned Task API without capability/no-Origin and require401; health readiness-only. If direct HTTP status evidence cannot be captured, mark incomplete rather than infer it from coordinator-online text.\n5. Close only the identity-bound Edge window through native WindowPattern.Close regardless of foreground. Observe original broker identity disappearing and readiness clearing before canonical identity-bound cleanup. Cleanup is mandatory on failure.\n\n## Exact requested new bounds\n\nKeep product source86caba/tree0b7ec91968977c2abb3920a2996a95e8e6ae0d7a unchanged, same approved ports18877/18878/18879 and known Node/signed Edge fingerprints. Fresh runtime F:/nrl-auth118-native3, only isolated cacheDir safety delta and read-only existing dependencies. Fresh branch codex/issue118-native-browser-acceptance-r3-v3-20261004 from source86caba, one immutable Decision-only activation, canonical existing gates, one push/one Draft against codex/issue118-launcher-compatibility-r3-v2-20261004, two description updates. No product commit/correction, install, models, credentials, source-test replay, workflow dispatch/rerun, Ready/merge/main/tag/release/deploy.\n\nAdd exactly one startup<=180s, one browser launch, two observations<=180s each, one owned cleanup<=120s. Cutoff remains 2026-10-04T15:30:00Z / tonight23:30 China, no extension/renewal/automatic successor. Require an 11-minute runtime/cleanup reserve plus preparation time before starting. Existing healthy frontend/runtime, failed native1 and terminal native2 remain untouched. Preserve every original failure and spending: source dev6/corrections7; prior runtime startups2, initial startup failed, second startup passed but acceptance incomplete; prior browser launches1 and observation invocations2. If v3 starts, aggregate runtime startups3, browser launches2, observation ceiling4. No counter reset.\n\nCurrent v2 Decision disallows automatic successors/retries; this additional startup therefore requires explicit Owner selection/approval of this new bounded scope before activation. Success would establish this client acceptance only, not independent review, full#118/#384, privileged adapter completion, landing or all backlog completion.\n\nEXPLICIT OWNER APPROVAL: Owner approved this exact v3 scope, then on 2026-10-07 approved its cutoff amendment to one 90-minute window frozen as absolute timestamps at first activation, then explicitly approved ONLY the Edge SHA256 update to d366716ba3cd2cc67d92d9b712b129fea4c8df769961d1e04b037ce034780ad0 at the same existing path with VALID Microsoft signature. These amendments supersede ONLY the originally proposed v3 fixed cutoff and browser fingerprint. All old absolute cutoffs/failures/counters remain historical. No automatic successor, expiry renewal or counter reset. Product source stays86caba; source corrections and checks replay zero.\n\nFROZEN ACTIVATION_START=2026-10-07T08:19:02.635253+00:00; EXPIRES_AT=2026-10-07T09:49:02.635253+00:00",
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
      "command": "# Explicitly selected new acceptance after observer failure \u2014 pending\n\nThis proposal grants no authority. The approved v2 execution is terminal: startup succeeded on source 86caba45888455994b0e43c820833878a8a5bac1, native client ready, real UIA home and visible Settings observed. Observation1 failed because it searched UIA Name for the address; observation2 failed foreground-window assertion. Canonical cleanup returned0, both owned Windows Jobs empty. No screenshots, positive/negative HTTP status or native browser-only closure acceptance completed. Do not classify these observer failures as product failures. Draft #1085 records the exact result.\n\n## Concrete observer changes selected for review\n\n1. Check the address through the uniquely identified native address Edit control's ValuePattern, normalizing optional http scheme/trailing slash, rather than searching all control names. Require exact loopback hostname and port18879. Retain broker executable/creation-time and Edge parent/executable/creation-time/owned-window binding.\n2. Use actual native PrintWindow rendering of the owned window for pixels, without depending on foreground ownership. Verify returned image visually; a blank/black/unavailable rendering is unverified and stops acceptance, never a synthetic screenshot. Do not capture another foreground window.\n3. Use the UIA names observed in v2: task navigation is Button `\u6253\u5f00\u4efb\u52a1\u5217\u8868`; Settings is Hyperlink `\u8bbe\u7f6e`, accessible through `\u66f4\u591a\u5bfc\u822a` if needed. Navigate home/tasks/settings by native UIA only; do not create goals/tasks/windows or save model configuration.\n4. Record actual frontend-frame read-only HTTP 200 using native browser DevTools UI; no capability value access or logging. Probe only the owned Task API without capability/no-Origin and require401; health readiness-only. If direct HTTP status evidence cannot be captured, mark incomplete rather than infer it from coordinator-online text.\n5. Close only the identity-bound Edge window through native WindowPattern.Close regardless of foreground. Observe original broker identity disappearing and readiness clearing before canonical identity-bound cleanup. Cleanup is mandatory on failure.\n\n## Exact requested new bounds\n\nKeep product source86caba/tree0b7ec91968977c2abb3920a2996a95e8e6ae0d7a unchanged, same approved ports18877/18878/18879 and known Node/signed Edge fingerprints. Fresh runtime F:/nrl-auth118-native3, only isolated cacheDir safety delta and read-only existing dependencies. Fresh branch codex/issue118-native-browser-acceptance-r3-v3-20261004 from source86caba, one immutable Decision-only activation, canonical existing gates, one push/one Draft against codex/issue118-launcher-compatibility-r3-v2-20261004, two description updates. No product commit/correction, install, models, credentials, source-test replay, workflow dispatch/rerun, Ready/merge/main/tag/release/deploy.\n\nAdd exactly one startup<=180s, one browser launch, two observations<=180s each, one owned cleanup<=120s. Cutoff remains 2026-10-04T15:30:00Z / tonight23:30 China, no extension/renewal/automatic successor. Require an 11-minute runtime/cleanup reserve plus preparation time before starting. Existing healthy frontend/runtime, failed native1 and terminal native2 remain untouched. Preserve every original failure and spending: source dev6/corrections7; prior runtime startups2, initial startup failed, second startup passed but acceptance incomplete; prior browser launches1 and observation invocations2. If v3 starts, aggregate runtime startups3, browser launches2, observation ceiling4. No counter reset.\n\nCurrent v2 Decision disallows automatic successors/retries; this additional startup therefore requires explicit Owner selection/approval of this new bounded scope before activation. Success would establish this client acceptance only, not independent review, full#118/#384, privileged adapter completion, landing or all backlog completion.\n\nEXPLICIT OWNER APPROVAL: Owner approved this exact v3 scope, then on 2026-10-07 approved its cutoff amendment to one 90-minute window frozen as absolute timestamps at first activation, then explicitly approved ONLY the Edge SHA256 update to d366716ba3cd2cc67d92d9b712b129fea4c8df769961d1e04b037ce034780ad0 at the same existing path with VALID Microsoft signature. These amendments supersede ONLY the originally proposed v3 fixed cutoff and browser fingerprint. All old absolute cutoffs/failures/counters remain historical. No automatic successor, expiry renewal or counter reset. Product source stays86caba; source corrections and checks replay zero.\n\nFROZEN ACTIVATION_START=2026-10-07T08:19:02.635253+00:00; EXPIRES_AT=2026-10-07T09:49:02.635253+00:00",
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
      "command": "One exact activation push and Draft, two truthful evidence descriptions; no landing. codex/issue118-native-browser-acceptance-r3-v3-20261004",
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
    "note": "Exactly new owned external runtimeF:\\nrl-auth118-native3; one clone/stack/browser, readonly shared deps, cacheDir safety config only. Never stage runtime/evidence. Existing runtimes preserved."
  },
  "workstream_id": "issue118-native-browser-acceptance-r3-v3",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 1,
  "execution_window_hours": 1.5,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 1,
  "frontend_launch_limit": 1,
  "approval_event_or_time": "2026-10-07T08:19:02.635253+00:00",
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
    "prior_source_dev_spent": 6,
    "prior_source_corrections_spent": 7,
    "prior_runtime_failed_startups": 1,
    "cumulative_runtime_startup_limit": 3,
    "prior_runtime_startups": 2,
    "prior_browser_startups": 1,
    "prior_observations_spent": 2,
    "prior_source_original_deadline": "2026-10-04T14:55:31.639949+00:00",
    "owned_runtime_root": "F:\\nrl-auth118-native3",
    "expires_at": "2026-10-07T09:49:02.635253+00:00"
  }
}
```

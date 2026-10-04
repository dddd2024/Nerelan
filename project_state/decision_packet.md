# Actual Windows native-client acceptance for118/384

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_native_browser_acceptance_r3_v2",
  "round_id": "round_20261004_issue118_native_browser_acceptance_r3_v2",
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
  "approval_basis": "Explicit Owner approval of exact v2 proposal followed by explicit approval of cutoff-only amendment to 2026-10-04T15:30:00Z; preserve all original spending/failures.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-launcher-compatibility-r3-v2-20261004",
  "base_sha": "86caba45888455994b0e43c820833878a8a5bac1",
  "activation_base_sha": "86caba45888455994b0e43c820833878a8a5bac1",
  "starting_head": "86caba45888455994b0e43c820833878a8a5bac1",
  "required_branch": "codex/issue118-native-browser-acceptance-r3-v2-20261004",
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
    "specification": "# #118 / #384 actual Windows client acceptance \u2014 proposed, NOT authorized\n\nPrepared 2026-10-04T14:20:44Z. No Decision is activated by this proposal.\n\nSource: dddd2024/Nerelan, codex/issue118-launcher-compatibility-r3-v2-20261004@86caba45888455994b0e43c820833878a8a5bac1, tree 0b7ec91968977c2abb3920a2996a95e8e6ae0d7a, Draft #1084. Local Platform 1992 passed / 22 skipped; Path A 191 passed; committed focused 171 passed. Native CI original JUnit 6863 passed / 31 skipped / zero failures or errors. Windows lifecycle 63 passed. Frontend CI 40 passed / 2 skipped is fixture acceptance, not actual private-client acceptance.\n\n## Proposed exact operations and bounds\n\n- Use the existing controller F:/Nerelan-issue1027-frontend-audit. Preserve its five generated gates before changing phases; no reset, restore, stash, deletion or broad staging. Fresh branch codex/issue118-native-browser-acceptance-r3-v2-20261004 from the exact source above; one immutable Decision-only activation, existing canonical plan/preflight and publication-readiness checks, one exact activation push, one Draft against that source branch, up to two Draft description updates. Product commits/source corrections/development test retries: zero.\n- Create exactly one new owned local clone F:/nrl-auth118-native2 (observed absent). Exact source commit/tree and canonical repository origin must be attested before runtime. This is not an additional registered worktree. Preserve failed clone native1 and all its evidence. Only a disclosed runtime safety delta to frontend/vite.config.ts may set cacheDir inside native2. Reuse existing dependency junction to F:/reverse-agent/frontend/node_modules; no installs or shared dependency/cache modifications. The committed launcher uses actual Vite CLI and configLoader runner. Verify owned optimizer output and absence of shared-cache writes; if this cannot be established, report it as unverified, not read-only proof.\n- One supported dev-up invocation, at most 180 seconds; one stack/frontend startup and one native Edge launch. Require loopback ports 18877 Task, 18878 Model and 18879 frontend free first. Private relay uses an owned ephemeral loopback port. Use fresh empty stores; do not copy/read existing credentials, saved sessions or model configuration. Zero provider/model calls, auth-list probes, OpenCode launches, task execution, window activation or privileged operations.\n- Known Node SHA256 58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f; Edge SHA256 39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907, Microsoft signature VALID at preparation. Recheck immediately before execution. Unknown executable or changed fingerprint stops execution.\n- At most two acceptance observation invocations, each <=180 seconds. Actual Windows UI Automation/Win32 observations and screenshots of the exact owned Edge window only; navigate home/tasks/settings. Observe successful authenticated frontend Task API reads. Missing-capability/no-Origin native requests to this owned Task API must receive 401; health exposes readiness only. No private capability value in renderer, URL, argv, env, logs or evidence; do not read/export the host capability.\n- Close only the identity-bound owned browser window using native UI. Observe broker/process birth identity and readiness; require terminal broker cleanup rather than assume browser closure proves it. One canonical owned dev-down invocation <=120 seconds, including failure cleanup using existing identity-bound job ownership. Never stop unrelated processes or the accepted frontend at 4173/8765/8766. Keep owned logs, databases and failed evidence; do not delete the clone.\n- Absolute cutoff 2026-10-04T14:55:31.639949Z (2026-10-04 22:55:31 China), matching the unchanged source cutoff. Do not start if insufficient time remains for observation and owned cleanup. No renewal, automatic successor, second startup, repair or counter reset. Natural CI observation is read-only; no dispatch/rerun. No Ready, merge, main push, tag, release, deployment, issue/comment writes or independent acceptance claim.\n\n## Aggregate accounting and acceptance\n\nPreserve prior source totals six development invocations and seven correction rounds, prior mandatory failure, source PR #1084 two pushes/two description updates, and the original runtime failure #1082 startup 1/1. This proposal adds one prospective runtime startup only; aggregate real runtime startups become 2 with the first recorded failed, not 1 after a reset. New phase activation/push/Draft budgets remain separate and cumulative records remain intact.\n\nSuccess requires actual pixels/navigation, private transport positive/negative HTTP evidence, browser-only closure/process evidence, and exact-owned cleanup. Any missing result is unverified; a failed acceptance stops this phase. This is neither independent review nor #118/#384/all backlog completion nor landing. Owner/compiler authority and privileged adapters remain subsequent separately scoped work.\n\nApproval is required because the currently activated compatibility Decision explicitly has local_browser_execution_allowed=false and runtime_host_launch_limit=0. The failed runtime Decision explicitly forbids automatic successor/retry/reset and is expired. The next runtime is an explicitly selected new exact-source phase, not continuation under either exhausted grant. After approval, record the approval verbatim and activate a fresh bounded Decision using existing repository mechanisms before any runtime.\n\nOwner explicitly approved the exact proposal, then explicitly approved ONLY its cutoff amendment to 2026-10-04T15:30:00Z in this chat on 2026-10-04. The original cutoff, all failed attempts and all cumulative source spending remain historical and unchanged. This exact new runtime Decision grants ONE prospective additional startup on source86caba, not a reset or automatic successor under the expired original runtime. Original runtime startup remains one failed; cumulative becomes two only if this launch actually begins. Original source total six development checks/seven corrections. No product corrections/commits, source test replays or models. No independent acceptance or landing.\nThe proposal text above records its originally prepared cutoff; this explicitly Owner-approved amendment supersedes ONLY the new runtime cutoff: expiry 2026-10-04T15:30:00Z, no renewal.\n",
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
      "One activation push exactcodex/issue118-native-browser-acceptance-r3-v2-20261004, one Draft againstcodex/issue118-launcher-compatibility-r3-v2-20261004@86caba45888455994b0e43c820833878a8a5bac1,2 descriptions, bounded read-only natural CI and authority; no other writes."
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
      "command": "# #118 / #384 actual Windows client acceptance \u2014 proposed, NOT authorized\n\nPrepared 2026-10-04T14:20:44Z. No Decision is activated by this proposal.\n\nSource: dddd2024/Nerelan, codex/issue118-launcher-compatibility-r3-v2-20261004@86caba45888455994b0e43c820833878a8a5bac1, tree 0b7ec91968977c2abb3920a2996a95e8e6ae0d7a, Draft #1084. Local Platform 1992 passed / 22 skipped; Path A 191 passed; committed focused 171 passed. Native CI original JUnit 6863 passed / 31 skipped / zero failures or errors. Windows lifecycle 63 passed. Frontend CI 40 passed / 2 skipped is fixture acceptance, not actual private-client acceptance.\n\n## Proposed exact operations and bounds\n\n- Use the existing controller F:/Nerelan-issue1027-frontend-audit. Preserve its five generated gates before changing phases; no reset, restore, stash, deletion or broad staging. Fresh branch codex/issue118-native-browser-acceptance-r3-v2-20261004 from the exact source above; one immutable Decision-only activation, existing canonical plan/preflight and publication-readiness checks, one exact activation push, one Draft against that source branch, up to two Draft description updates. Product commits/source corrections/development test retries: zero.\n- Create exactly one new owned local clone F:/nrl-auth118-native2 (observed absent). Exact source commit/tree and canonical repository origin must be attested before runtime. This is not an additional registered worktree. Preserve failed clone native1 and all its evidence. Only a disclosed runtime safety delta to frontend/vite.config.ts may set cacheDir inside native2. Reuse existing dependency junction to F:/reverse-agent/frontend/node_modules; no installs or shared dependency/cache modifications. The committed launcher uses actual Vite CLI and configLoader runner. Verify owned optimizer output and absence of shared-cache writes; if this cannot be established, report it as unverified, not read-only proof.\n- One supported dev-up invocation, at most 180 seconds; one stack/frontend startup and one native Edge launch. Require loopback ports 18877 Task, 18878 Model and 18879 frontend free first. Private relay uses an owned ephemeral loopback port. Use fresh empty stores; do not copy/read existing credentials, saved sessions or model configuration. Zero provider/model calls, auth-list probes, OpenCode launches, task execution, window activation or privileged operations.\n- Known Node SHA256 58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f; Edge SHA256 39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907, Microsoft signature VALID at preparation. Recheck immediately before execution. Unknown executable or changed fingerprint stops execution.\n- At most two acceptance observation invocations, each <=180 seconds. Actual Windows UI Automation/Win32 observations and screenshots of the exact owned Edge window only; navigate home/tasks/settings. Observe successful authenticated frontend Task API reads. Missing-capability/no-Origin native requests to this owned Task API must receive 401; health exposes readiness only. No private capability value in renderer, URL, argv, env, logs or evidence; do not read/export the host capability.\n- Close only the identity-bound owned browser window using native UI. Observe broker/process birth identity and readiness; require terminal broker cleanup rather than assume browser closure proves it. One canonical owned dev-down invocation <=120 seconds, including failure cleanup using existing identity-bound job ownership. Never stop unrelated processes or the accepted frontend at 4173/8765/8766. Keep owned logs, databases and failed evidence; do not delete the clone.\n- Absolute cutoff 2026-10-04T14:55:31.639949Z (2026-10-04 22:55:31 China), matching the unchanged source cutoff. Do not start if insufficient time remains for observation and owned cleanup. No renewal, automatic successor, second startup, repair or counter reset. Natural CI observation is read-only; no dispatch/rerun. No Ready, merge, main push, tag, release, deployment, issue/comment writes or independent acceptance claim.\n\n## Aggregate accounting and acceptance\n\nPreserve prior source totals six development invocations and seven correction rounds, prior mandatory failure, source PR #1084 two pushes/two description updates, and the original runtime failure #1082 startup 1/1. This proposal adds one prospective runtime startup only; aggregate real runtime startups become 2 with the first recorded failed, not 1 after a reset. New phase activation/push/Draft budgets remain separate and cumulative records remain intact.\n\nSuccess requires actual pixels/navigation, private transport positive/negative HTTP evidence, browser-only closure/process evidence, and exact-owned cleanup. Any missing result is unverified; a failed acceptance stops this phase. This is neither independent review nor #118/#384/all backlog completion nor landing. Owner/compiler authority and privileged adapters remain subsequent separately scoped work.\n\nApproval is required because the currently activated compatibility Decision explicitly has local_browser_execution_allowed=false and runtime_host_launch_limit=0. The failed runtime Decision explicitly forbids automatic successor/retry/reset and is expired. The next runtime is an explicitly selected new exact-source phase, not continuation under either exhausted grant. After approval, record the approval verbatim and activate a fresh bounded Decision using existing repository mechanisms before any runtime.\n\nOwner explicitly approved the exact proposal, then explicitly approved ONLY its cutoff amendment to 2026-10-04T15:30:00Z in this chat on 2026-10-04. The original cutoff, all failed attempts and all cumulative source spending remain historical and unchanged. This exact new runtime Decision grants ONE prospective additional startup on source86caba, not a reset or automatic successor under the expired original runtime. Original runtime startup remains one failed; cumulative becomes two only if this launch actually begins. Original source total six development checks/seven corrections. No product corrections/commits, source test replays or models. No independent acceptance or landing.\nThe proposal text above records its originally prepared cutoff; this explicitly Owner-approved amendment supersedes ONLY the new runtime cutoff: expiry 2026-10-04T15:30:00Z, no renewal.\n",
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
      "command": "# #118 / #384 actual Windows client acceptance \u2014 proposed, NOT authorized\n\nPrepared 2026-10-04T14:20:44Z. No Decision is activated by this proposal.\n\nSource: dddd2024/Nerelan, codex/issue118-launcher-compatibility-r3-v2-20261004@86caba45888455994b0e43c820833878a8a5bac1, tree 0b7ec91968977c2abb3920a2996a95e8e6ae0d7a, Draft #1084. Local Platform 1992 passed / 22 skipped; Path A 191 passed; committed focused 171 passed. Native CI original JUnit 6863 passed / 31 skipped / zero failures or errors. Windows lifecycle 63 passed. Frontend CI 40 passed / 2 skipped is fixture acceptance, not actual private-client acceptance.\n\n## Proposed exact operations and bounds\n\n- Use the existing controller F:/Nerelan-issue1027-frontend-audit. Preserve its five generated gates before changing phases; no reset, restore, stash, deletion or broad staging. Fresh branch codex/issue118-native-browser-acceptance-r3-v2-20261004 from the exact source above; one immutable Decision-only activation, existing canonical plan/preflight and publication-readiness checks, one exact activation push, one Draft against that source branch, up to two Draft description updates. Product commits/source corrections/development test retries: zero.\n- Create exactly one new owned local clone F:/nrl-auth118-native2 (observed absent). Exact source commit/tree and canonical repository origin must be attested before runtime. This is not an additional registered worktree. Preserve failed clone native1 and all its evidence. Only a disclosed runtime safety delta to frontend/vite.config.ts may set cacheDir inside native2. Reuse existing dependency junction to F:/reverse-agent/frontend/node_modules; no installs or shared dependency/cache modifications. The committed launcher uses actual Vite CLI and configLoader runner. Verify owned optimizer output and absence of shared-cache writes; if this cannot be established, report it as unverified, not read-only proof.\n- One supported dev-up invocation, at most 180 seconds; one stack/frontend startup and one native Edge launch. Require loopback ports 18877 Task, 18878 Model and 18879 frontend free first. Private relay uses an owned ephemeral loopback port. Use fresh empty stores; do not copy/read existing credentials, saved sessions or model configuration. Zero provider/model calls, auth-list probes, OpenCode launches, task execution, window activation or privileged operations.\n- Known Node SHA256 58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f; Edge SHA256 39966f2799d3503e74871c945ba1c4877f38426d1c28756ab1545ad7c3de8907, Microsoft signature VALID at preparation. Recheck immediately before execution. Unknown executable or changed fingerprint stops execution.\n- At most two acceptance observation invocations, each <=180 seconds. Actual Windows UI Automation/Win32 observations and screenshots of the exact owned Edge window only; navigate home/tasks/settings. Observe successful authenticated frontend Task API reads. Missing-capability/no-Origin native requests to this owned Task API must receive 401; health exposes readiness only. No private capability value in renderer, URL, argv, env, logs or evidence; do not read/export the host capability.\n- Close only the identity-bound owned browser window using native UI. Observe broker/process birth identity and readiness; require terminal broker cleanup rather than assume browser closure proves it. One canonical owned dev-down invocation <=120 seconds, including failure cleanup using existing identity-bound job ownership. Never stop unrelated processes or the accepted frontend at 4173/8765/8766. Keep owned logs, databases and failed evidence; do not delete the clone.\n- Absolute cutoff 2026-10-04T14:55:31.639949Z (2026-10-04 22:55:31 China), matching the unchanged source cutoff. Do not start if insufficient time remains for observation and owned cleanup. No renewal, automatic successor, second startup, repair or counter reset. Natural CI observation is read-only; no dispatch/rerun. No Ready, merge, main push, tag, release, deployment, issue/comment writes or independent acceptance claim.\n\n## Aggregate accounting and acceptance\n\nPreserve prior source totals six development invocations and seven correction rounds, prior mandatory failure, source PR #1084 two pushes/two description updates, and the original runtime failure #1082 startup 1/1. This proposal adds one prospective runtime startup only; aggregate real runtime startups become 2 with the first recorded failed, not 1 after a reset. New phase activation/push/Draft budgets remain separate and cumulative records remain intact.\n\nSuccess requires actual pixels/navigation, private transport positive/negative HTTP evidence, browser-only closure/process evidence, and exact-owned cleanup. Any missing result is unverified; a failed acceptance stops this phase. This is neither independent review nor #118/#384/all backlog completion nor landing. Owner/compiler authority and privileged adapters remain subsequent separately scoped work.\n\nApproval is required because the currently activated compatibility Decision explicitly has local_browser_execution_allowed=false and runtime_host_launch_limit=0. The failed runtime Decision explicitly forbids automatic successor/retry/reset and is expired. The next runtime is an explicitly selected new exact-source phase, not continuation under either exhausted grant. After approval, record the approval verbatim and activate a fresh bounded Decision using existing repository mechanisms before any runtime.\n\nOwner explicitly approved the exact proposal, then explicitly approved ONLY its cutoff amendment to 2026-10-04T15:30:00Z in this chat on 2026-10-04. The original cutoff, all failed attempts and all cumulative source spending remain historical and unchanged. This exact new runtime Decision grants ONE prospective additional startup on source86caba, not a reset or automatic successor under the expired original runtime. Original runtime startup remains one failed; cumulative becomes two only if this launch actually begins. Original source total six development checks/seven corrections. No product corrections/commits, source test replays or models. No independent acceptance or landing.\nThe proposal text above records its originally prepared cutoff; this explicitly Owner-approved amendment supersedes ONLY the new runtime cutoff: expiry 2026-10-04T15:30:00Z, no renewal.\n",
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
      "command": "One exact activation push and Draft, two truthful evidence descriptions; no landing. codex/issue118-native-browser-acceptance-r3-v2-20261004",
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
    "note": "Exactly new owned external runtimeF:\\nrl-auth118-native2; one clone/stack/browser, readonly shared deps, cacheDir safety config only. Never stage runtime/evidence. Existing runtimes preserved."
  },
  "workstream_id": "issue118-native-browser-acceptance-r3-v2",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 1,
  "execution_window_hours": 1.5,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 1,
  "frontend_launch_limit": 1,
  "approval_event_or_time": "2026-10-04T14:53:12.500836+00:00",
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
    "cumulative_runtime_startup_limit": 2,
    "prior_source_original_deadline": "2026-10-04T14:55:31.639949+00:00",
    "owned_runtime_root": "F:\\nrl-auth118-native2",
    "expires_at": "2026-10-04T15:30:00+00:00"
  }
}
```

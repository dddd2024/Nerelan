# Saved model catalog and native registry compatibility

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261002_issue986_catalog_selection_r3_v2",
  "round_id": "round_20261002_issue986_catalog_selection_r3_v2",
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
  "decision_scope": "SAVED_CONNECTION_CATALOG_AND_SELECTION_PREVIEW",
  "source_issue": 986,
  "parent_issue": 986,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner request in the current conversation",
  "approval_basis": "The Owner explicitly delegated full project takeover and decisions in this chat. Source-only v1 preserved candidate17a0d7be15b2962d94f98568c0a570690fe6dedd locally and STOPPED source publication because mandatory inherited native registry assertions are unsatisfied: test_connection_binding expects only OpenCode and no Codex, while approved684dec91 native integration intentionally includes non-operational/not_probed Codex. This separately bounded successor approves exact remote v1 activation branch at c75d4f42c07daafe5b400a403d544adeab7007e5 as planning integration (not main, not source acceptance), reuses preserved source only after fresh Decision activation/gates/Draft, and allows precisely the two outdated native-registry assertions to be updated to exact supported registry with Codex operational false/readiness not_probed and existing OpenCode descriptor unchanged. No skipped checks, weakening, hidden failure, runtime, credentials, model/provider catalog requests or native trial budget replenishment. Preserve old immutable Decision, candidate source commit, failed checks, old activation Draft and all five dirty gates. Internal Codex assistance remains author work, not Nerelan or independent model acceptance. The previous exact-head mandatory backend run had 435 tests:432 passed and3 failed. Two failures are the inherited registry assertions above. The third native integration fixture persisted a passed/verified real functional check, then failed artifact-retention Git observation. Preserve the failed XML and fixture; R0 observations establish the retention ref is absent and its lock path is260 characters, reaching the Windows legacy MAX_PATH limit before the terminating null; path length is the supported diagnosis, not a captured update-ref stderr. The successor checks must use a fresh short owned external basetemp under F:\\n986v2- to avoid test-artifact retention path overflow, with all original functional, retention and integration assertions unchanged. No global/local Git longpaths setting changes, no skipped tests or fake retention, no edits to native functional/artifact runtime code. If any mandatory check still fails, stop affected publication and preserve evidence.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue986-catalog-selection-r3-v1-20261002",
  "base_sha": "c75d4f42c07daafe5b400a403d544adeab7007e5",
  "activation_base_sha": "c75d4f42c07daafe5b400a403d544adeab7007e5",
  "starting_head": "c75d4f42c07daafe5b400a403d544adeab7007e5",
  "required_branch": "codex/issue986-catalog-selection-r3-v2-20261002",
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
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
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
    "specification": "Implement real saved-connection POST models and explicit catalog selection using existing trusted ModelProfileStore credential ownership, existing API surfaces and no second credential store. An opaque server process/generation configuration revision changes on authority/config/secret replacement/delete-recreate, not name-only; catalog results and writes CAS against that revision, invalidate stale/restarted discovery, never derive a revision from a secret/hash. Catalog is at most1000 deduplicated safe advertised IDs and bounded nonsecret optional metadata, projection digest revision, explicit empty/error/unsupported/stale/locked states. Advertised catalog is never entitlement or task success. Exactly one GET saved URL/models with explicit no redirects, reject URL userinfo/query/fragment and nonloopback plaintext HTTP, cap+1 1MiB response, total wallclock<=10s including DNS/headers/body using known installed Python bounded isolated worker/anonymous pipe; no credentials in argv/env/files/logs/public errors, no retries/pagination/inference. Default LIVE0 is zero network. Disposable provider-free tests may use only owned loopback servers, synthetic credentials, external temp dirs, known installed Python/Node and existing dependencies; no actual auth stores/provider endpoints. Private snapshots atomically resolve saved connection and secret under existing lock, perform I/O outside lock, CAS before admission. Generated binding selection has stable server-owned provenance/idempotent identity, protects existing manual/disabled binding tuples and user DeepSeek/Agnes setup; preserve v1/v2 loading and old Task refs, no migration/new database. Process-local generated provenance unknown after restart is treated conservatively as protected manual; no fake persistent proof. Add zero-network pure selection preview and POST model-selections/recommend using an atomic public snapshot. Filter protocol/auth/capability/observed readiness and routine GPT/unknown identity; requested aliases/static operational descriptors are not observed readiness or underlying identity. Rank explicit existing preference only, mark cost/quality/history evidence unknown without fabricated best/zero. Preview is not dispatch/admission/GPT authority; reject unexpected authority fields. Frontend real models route, safe revisions, Chinese loading/refresh/empty/error/unsupported/stale states, guard late results, preserve three identity axes and existing manual overrides, pick advertised model without mandatory ID typing through server CAS catalog-select, clear indication advertised-unverified and waiting for execution checks. Preserve all existing secrets/relay/native/OpenCode/runtime/Task/Goal behavior; no automatic binding repoint, task dispatch, GPT fallback, global default changes or weakening tests. Exact allowlist is immutable. This successor additionally permits tests/test_connection_binding.py only to replace the two inherited only-OpenCode/no-Codex assertions with exact two-descriptor registry assertions: unchanged OpenCode plus Codex operational false, readiness_status not_probed, model_selection/workspace_execution/single_mode. Preserve every other original assertion/test; adding native login metadata does not prove inference. Source v1 candidate copied by recorded SHA only AFTER this first new Draft; no history reuse/cherry-pick/rebase. Normalize changed files to UTF8 LF as needed for diff-check without semantic unrelated edits. The previous exact-head mandatory backend run had 435 tests:432 passed and3 failed. Two failures are the inherited registry assertions above. The third native integration fixture persisted a passed/verified real functional check, then failed artifact-retention Git observation. Preserve the failed XML and fixture; R0 observations establish the retention ref is absent and its lock path is260 characters, reaching the Windows legacy MAX_PATH limit before the terminating null; path length is the supported diagnosis, not a captured update-ref stderr. The successor checks must use a fresh short owned external basetemp under F:\\n986v2- to avoid test-artifact retention path overflow, with all original functional, retention and integration assertions unchanged. No global/local Git longpaths setting changes, no skipped tests or fake retention, no edits to native functional/artifact runtime code. If any mandatory check still fails, stop affected publication and preserve evidence.",
    "completion_boundary": "Same bounded source-only catalog/CAS/recommendation-preview phase with corrected inherited native registry contract. Full exact-head mandatory backend/frontend/type/lint/diff/readiness/natural CI required, no unavailable checks called passed. Full986 execution/budget/actual discovery/low-GPT task/distinct actual underlying review and landing remain OPEN and separate; all old failed native evidence/budget preserved. Local candidate is not published source acceptance. New Draft remains independently unaccepted."
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
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/catalog_transport.py",
    "reverse_agent/model_access/catalog_worker.py",
    "reverse_agent/model_access/selection.py",
    "tests/test_connection_models.py",
    "tests/test_model_catalog_store.py",
    "tests/test_catalog_transport.py",
    "tests/test_model_selection.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/hooks/use-model-access.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-control.test.ts",
    "frontend/tests/connection-binding-flow.test.tsx",
    "frontend/tests/connection-model-catalog.test.tsx",
    "tests/test_connection_binding.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/catalog_transport.py",
    "reverse_agent/model_access/catalog_worker.py",
    "reverse_agent/model_access/selection.py",
    "tests/test_connection_models.py",
    "tests/test_model_catalog_store.py",
    "tests/test_catalog_transport.py",
    "tests/test_model_selection.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/hooks/use-model-access.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-control.test.ts",
    "frontend/tests/connection-binding-flow.test.tsx",
    "frontend/tests/connection-model-catalog.test.tsx",
    "tests/test_connection_binding.py"
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
    "tests/platform_v1/test_codex_integration.py"
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
    "API_key_auth",
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass"
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
    "ci_network_exceptions": [
      "Unchanged natural repository CI dependency setup and provider-free validation only. No new workflow, rerun or dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Disposable provider-free owned loopback HTTP fixtures with synthetic credentials, no model inference/provider/existing runtime endpoint. Known installed Python isolated catalog worker only; parent owns its PID and deadlines."
    ],
    "github_control_plane_network_exceptions": [
      "Normal exact successor branch pushes<=3, one Draft against explicit v1 activationc75d4f42, exact-head description updates and read-only natural CI/backlog. No previous branch push/comments/Ready/Merge/close/rerun/dispatch."
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
      "command_id": "catalog.bootstrap",
      "command": "Preserve local source candidate17a0d7be, failures and five dirty gates externally; fresh branch from explicit remote v1 activationc75d4f42; Decision-only activation, actual startup/plan/lint/preflight/readiness and new first Draft BEFORE replaying candidate source.",
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
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "catalog.implement",
      "command": "Implement real saved-connection POST models and explicit catalog selection using existing trusted ModelProfileStore credential ownership, existing API surfaces and no second credential store. An opaque server process/generation configuration revision changes on authority/config/secret replacement/delete-recreate, not name-only; catalog results and writes CAS against that revision, invalidate stale/restarted discovery, never derive a revision from a secret/hash. Catalog is at most1000 deduplicated safe advertised IDs and bounded nonsecret optional metadata, projection digest revision, explicit empty/error/unsupported/stale/locked states. Advertised catalog is never entitlement or task success. Exactly one GET saved URL/models with explicit no redirects, reject URL userinfo/query/fragment and nonloopback plaintext HTTP, cap+1 1MiB response, total wallclock<=10s including DNS/headers/body using known installed Python bounded isolated worker/anonymous pipe; no credentials in argv/env/files/logs/public errors, no retries/pagination/inference. Default LIVE0 is zero network. Disposable provider-free tests may use only owned loopback servers, synthetic credentials, external temp dirs, known installed Python/Node and existing dependencies; no actual auth stores/provider endpoints. Private snapshots atomically resolve saved connection and secret under existing lock, perform I/O outside lock, CAS before admission. Generated binding selection has stable server-owned provenance/idempotent identity, protects existing manual/disabled binding tuples and user DeepSeek/Agnes setup; preserve v1/v2 loading and old Task refs, no migration/new database. Process-local generated provenance unknown after restart is treated conservatively as protected manual; no fake persistent proof. Add zero-network pure selection preview and POST model-selections/recommend using an atomic public snapshot. Filter protocol/auth/capability/observed readiness and routine GPT/unknown identity; requested aliases/static operational descriptors are not observed readiness or underlying identity. Rank explicit existing preference only, mark cost/quality/history evidence unknown without fabricated best/zero. Preview is not dispatch/admission/GPT authority; reject unexpected authority fields. Frontend real models route, safe revisions, Chinese loading/refresh/empty/error/unsupported/stale states, guard late results, preserve three identity axes and existing manual overrides, pick advertised model without mandatory ID typing through server CAS catalog-select, clear indication advertised-unverified and waiting for execution checks. Preserve all existing secrets/relay/native/OpenCode/runtime/Task/Goal behavior; no automatic binding repoint, task dispatch, GPT fallback, global default changes or weakening tests. Exact allowlist is immutable. This successor additionally permits tests/test_connection_binding.py only to replace the two inherited only-OpenCode/no-Codex assertions with exact two-descriptor registry assertions: unchanged OpenCode plus Codex operational false, readiness_status not_probed, model_selection/workspace_execution/single_mode. Preserve every other original assertion/test; adding native login metadata does not prove inference. Source v1 candidate copied by recorded SHA only AFTER this first new Draft; no history reuse/cherry-pick/rebase. Normalize changed files to UTF8 LF as needed for diff-check without semantic unrelated edits. The previous exact-head mandatory backend run had 435 tests:432 passed and3 failed. Two failures are the inherited registry assertions above. The third native integration fixture persisted a passed/verified real functional check, then failed artifact-retention Git observation. Preserve the failed XML and fixture; R0 observations establish the retention ref is absent and its lock path is260 characters, reaching the Windows legacy MAX_PATH limit before the terminating null; path length is the supported diagnosis, not a captured update-ref stderr. The successor checks must use a fresh short owned external basetemp under F:\\n986v2- to avoid test-artifact retention path overflow, with all original functional, retention and integration assertions unchanged. No global/local Git longpaths setting changes, no skipped tests or fake retention, no edits to native functional/artifact runtime code. If any mandatory check still fails, stop affected publication and preserve evidence.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "unit_test",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/contracts.py",
        "reverse_agent/model_access/store.py",
        "reverse_agent/model_access/service.py",
        "reverse_agent/model_access/catalog_transport.py",
        "reverse_agent/model_access/catalog_worker.py",
        "reverse_agent/model_access/selection.py",
        "tests/test_connection_models.py",
        "tests/test_model_catalog_store.py",
        "tests/test_catalog_transport.py",
        "tests/test_model_selection.py",
        "frontend/src/schemas/model-access.ts",
        "frontend/src/lib/model-control-client.ts",
        "frontend/src/hooks/use-model-access.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/model-control.test.ts",
        "frontend/tests/connection-binding-flow.test.tsx",
        "frontend/tests/connection-model-catalog.test.tsx",
        "tests/test_connection_binding.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "catalog.validate",
      "command": "Exact-head Python -B pytest tests/test_connection_models.py tests/test_model_catalog_store.py tests/test_catalog_transport.py tests/test_model_selection.py tests/test_model_access.py tests/test_connection_binding.py tests/test_provider_identity.py tests/platform_v1/test_codex_protocol.py tests/platform_v1/test_codex_executor.py tests/platform_v1/test_codex_integration.py -q -p no:cacheprovider with fresh short owned F:\\n986v2-<exact-head>-final basetemp and external XML; Node existing frontend vitest all tests, tsc --noEmit, eslint src; git diff --check and actual PUBLICATION_READY. Zero real providers/models/credentials/browser/installs, use disposable synthetic loopback only. Do not modify existing tests to accept regression.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "catalog.publish",
      "command": "Normal successor exact branch pushes<=3, one activation Draft against explicit v1 activationc75d4f42; rebind exact head. No source push to old1060/main/other branches, no Ready/Merge/close/comments/history mutation.",
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
    },
    {
      "command_id": "catalog.ci",
      "command": "Observe unchanged natural exact-head CI/Decision/State checks, provider-free and zero models. No rerun/dispatch/workflow/dependency change. Author evidence is not independent audit.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "code_read",
        "unit_test",
        "integration_test"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**",
      "frontend/node_modules/**",
      "frontend/vite.config.ts.timestamp-*.mjs",
      "frontend/*.tsbuildinfo"
    ],
    "stage_allowed": false,
    "note": "Preserve all existing runtimes, windows, failed fixture, local candidate17a0d7be and old immutable activation Draft. Owned source-only v2 evidence is external issue986-catalog-selection-v2; disposable short check roots are F:\\n986v2-*. All checks use synthetic credentials/loopback only; never stage runtime/generated gates."
  },
  "follows_last_decision_id": "decision_20261002_issue986_catalog_selection_r3_v1",
  "follows_last_round_id": "round_20261002_issue986_catalog_selection_r3_v1",
  "workstream_id": "issue986-catalog-selection-preview-v2",
  "source_issues": [
    986,
    985
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 3,
  "execution_window_hours": 8
}
```

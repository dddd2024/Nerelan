# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260831_issue444_auth_completion_r3_v1",
  "round_id": "round_20260831_issue444_auth_completion_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260830_issue367_landing_mode_fail_closed_r2_v12",
  "follows_last_round_id": "round_20260830_issue367_landing_mode_fail_closed_r2_v12",
  "previous_audit_outcome": "ISSUE441_PR442_EXACT_HEAD_REWORK_REQUIRED_CLOSED_UNMERGED",
  "workstream_id": "issue444-auth-completion-r3-v1",
  "source_issue": 444,
  "parent_issue": 438,
  "integration_base_ref": "main",
  "base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "activation_base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "starting_head": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "required_branch": "owner/issue438-auth-completion-r3-v1",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R3",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 5,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 1,
  "credential_access_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": true,
  "live_provider_access_allowed": true,
  "credential_access_allowed": true,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "landing_revalidation_required_for_actions": ["ready_for_review", "merge"],
  "landing_revalidation_required_when_draft": true,
  "owner_attestation_required_for_ready_state": true,
  "attestation_head_must_match_current_pr_head": true,
  "ready_state_synchronize_must_revalidate": true,
  "converted_to_draft_returns_to_draft_semantics": true,
  "malformed_event_path_fail_closed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base eb1cbfa520582988e90e83d798d53379ba537fa8 and fresh branch merge-base",
    "verify Issue #444 remains OPEN and PR #442 remains CLOSED unmerged at rejected head de0f3d697daeab011e98deec290adc8d6a015cb1",
    "commit this immutable R3 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue444.materialize_activation_packet",
      "command": "run the repository-owned startup snapshot command-plan compiler transition lint and preflight locally; materialize and commit only the declared generated gate artifacts after the immutable Decision activation commit",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue444.implement_durable_api_key",
      "command": "port the bounded Issue 441 durable Windows credential-store implementation onto the fresh base and repair vault plus sanitized-state failure atomicity for create replacement authority change clear and delete; declare correct ctypes signatures and fail-closed Windows error mapping; add deterministic fake-vault rollback tests",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "test_edit", "documentation_edit", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/os_vault.py",
        "reverse_agent/model_access/contracts.py",
        "reverse_agent/model_access/store.py",
        "reverse_agent/model_access/service.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "tests/test_model_access.py",
        "tests/test_connection_binding.py",
        "tests/platform_v1/test_trusted_host.py",
        "frontend/src/schemas/model-access.ts",
        "frontend/src/lib/model-control-client.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/model-access-client.test.ts",
        "frontend/tests/model-control.test.ts",
        "frontend/tests/connection-binding-flow.test.tsx",
        "docs/model-access.md"
      ]
    },
    {
      "command_id": "issue444.implement_native_oauth",
      "command": "add a thin trusted-host account-auth adapter over the official authenticated loopback OpenCode provider OAuth endpoints for OpenAI only; expose sanitized start callback status cancel and logout lifecycle plus frontend login UX; keep tokens provider-owned and preserve existing external-session reuse",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "test_edit", "documentation_edit", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/account_auth.py",
        "reverse_agent/model_access/contracts.py",
        "reverse_agent/model_access/store.py",
        "reverse_agent/model_access/service.py",
        "reverse_agent/platform_v1/opencode_server_transport.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "tests/test_model_access.py",
        "tests/test_connection_binding.py",
        "tests/platform_v1/test_opencode_server_transport.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_trusted_host.py",
        "frontend/src/schemas/model-access.ts",
        "frontend/src/lib/model-control-client.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/model-access-client.test.ts",
        "frontend/tests/model-control.test.ts",
        "frontend/tests/connection-binding-flow.test.tsx",
        "docs/model-access.md",
        "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md"
      ]
    },
    {
      "command_id": "issue444.validate_product",
      "command": "run focused Model Access Connection Binding trusted-host OpenCode executor and server-transport tests; run the full Platform V1 blocking command and frontend unit typecheck lint build functional and applicable visual suites; run transition lint preflight publication readiness and git diff check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "integration_test", "lint", "build", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue444.windows_vault_proof",
      "command": "on the trusted Windows host store resolve across a fresh adapter instance and delete exactly one generated non-user Nerelan namespaced sentinel in Windows Credential Manager; never print or persist the sentinel and verify cleanup",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["known_binary_execution", "credential_access", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue444.publish_draft",
      "command": "after all local validation push the exact branch normally and create one Draft PR against locked main; update only that PR body and require fresh exact-head CI Model Access Frontend Playwright State Gate and Decision Preflight before independent audit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "draft_pr", "pull_request_update", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue444.post_publication_binding",
      "command": "after Draft PR creation archive the previous schema-v3 active mainline intent byte-for-byte and bind active intent exactly once to the actual PR number locked base current immutable Decision current Command Plan baseline workflow profile and merge policy; commit and push that binding",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit", "push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true,
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr430_v3.json"
      ]
    },
    {
      "command_id": "issue444.independent_exact_head_audit",
      "command": "an independent auditor that did not implement the patch reviews and reproduces the exact remote head including the prior rollback blocker OAuth secret confinement external-session regressions Windows adapter contract and all required checks then records ACCEPTED or REWORK_REQUIRED as a PR comment",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "unit_test", "pull_request_comment"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue444.owner_landing",
      "command": "only after independent exact-head acceptance fresh exact-head required checks zero unresolved threads unchanged locked base valid mainline intent and repository-owned landing attestation mark the PR ready once merge once using merge commit with expected-head protection verify the new main SHA and close Issues 444 441 and 438 as completed",
      "phase": "landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["mark_ready", "merge", "issue_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_source_paths": [
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_model_access.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
    "frontend/tests/model-control.test.ts",
    "frontend/tests/connection-binding-flow.test.tsx",
    "docs/model-access.md",
    "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md"
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr430_v3.json",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_model_access.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
    "frontend/tests/model-control.test.ts",
    "frontend/tests/connection-binding-flow.test.tsx",
    "docs/model-access.md",
    "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr430_v3.json",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_model_access.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
    "frontend/tests/model-control.test.ts",
    "frontend/tests/connection-binding-flow.test.tsx",
    "docs/model-access.md",
    "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/actions/**",
    ".github/workflows/**",
    ".codex-skills/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/base_platform/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "project_state/context/**",
    "project_state/evidence/**",
    "project_state/proposed_state/**",
    "project_state/domains/**",
    "project_state/jobs/**",
    "project_state/roadmap/**",
    "project_state/solve_tasks/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "squash",
    "dependency_install",
    "workflow_change",
    "live_model_call",
    "model_api_invocation",
    "runner_dispatch",
    "tag_or_release",
    "deployment",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work",
    "plaintext_secret_storage",
    "custom_oauth_implementation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "authenticated loopback OpenCode provider OAuth API for one explicit user-initiated OpenAI account authorization",
      "normal push Draft PR update independent audit comment mark-ready expected-head merge and issue close for Issue 444"
    ],
    "ci_network_exceptions": [
      "provider-free fake HTTP fixtures bound only to 127.0.0.1"
    ],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/*credential*", "minimum_risk": "R3"},
    {"pattern": "**/*oauth*", "minimum_risk": "R3"}
  ],
  "success_terminal": "AUTH_COMPLETION_R3_MERGED_MAIN_GREEN_ISSUES_CLOSED",
  "blocked_terminal": "AUTH_COMPLETION_R3_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Complete the three user-facing authentication outcomes on one governed path:

1. an API key entered once is kept in Windows Credential Manager and remains usable after trusted-host restart without secret readback;
2. OpenAI/ChatGPT account login is initiated from Product Setup through OpenCode's official provider OAuth surface, with browser authorization and provider-owned token refresh/session persistence;
3. existing OpenCode account/CLI sessions remain reusable through fresh sanitized status and Binding readiness without copying credentials.

## Acceptance

1. The Decision is the unique first commit after `starting_head`, remains byte-identical thereafter, and all mutated paths stay within this contract.
2. The independent #442 blocker is closed with deterministic post-vault/pre-state failure tests proving same-ref replacement, authority-changing replacement, clear and delete preserve the previously committed state/vault relation and create no orphan.
3. The Windows adapter uses correct native signatures and error handling; a generated non-user sentinel survives adapter reconstruction and is deleted without being printed or persisted.
4. Public and persisted Nerelan state contains only sanitized credential/session status and non-secret references; no secret, OAuth code, verifier, token, cookie or password reaches browser persistence, TaskStore, evidence, logs, commands or unrelated children.
5. OpenAI account authorization delegates to authenticated loopback OpenCode provider-auth/OAuth endpoints; OpenCode owns PKCE, callback, access/refresh rotation and durable token storage. Nerelan does not implement provider OAuth or read token files.
6. OAuth start, browser continuation, optional code callback, status, timeout, cancel and logout are typed, bounded and tested with injected fakes; only server-advertised provider/method identifiers are accepted.
7. Restart re-proves account availability from a fresh sanitized OpenCode auth probe; `account_login` and `external_cli_session` dispatch successfully only when freshly available and keep existing behavior otherwise.
8. Required backend/frontend/local checks, independent exact-head audit, exact-head CI, State Gate, Decision Preflight and landing attestation all pass against one immutable head with unchanged base.
9. Exactly one authorized Ready and one expected-head merge commit land the accepted tree; post-merge main and issue closure are read back. No auto-merge, direct-main push, history rewrite, tag, release or deployment occurs.

## Execution policy

- The owner explicitly authorized this bounded R3 round and its publication lifecycle in the user request; that authorization is represented only by this immutable Decision and generated Command Plan, never by identity alone.
- No real provider/model inference is authorized. One explicit user-controlled OAuth browser authorization is allowed, but account credentials/consent remain in the provider browser and no token inspection is allowed.
- Keep #442 closed and unmerged. Use its source only as a reviewed reference; the new branch starts from the locked main base and receives fresh commits.
- Any Decision mutation, main drift, out-of-scope path, unexplained test failure, independent audit rejection, CI failure, credential leak, unresolved review thread or landing-attestation failure stops the round.

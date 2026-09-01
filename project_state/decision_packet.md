# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260901_issue444_auth_completion_r3_v5",
  "round_id": "round_20260901_issue444_auth_completion_r3_v5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260901_issue487_nerelan_runtime_brand_r2_v3",
  "follows_last_round_id": "round_20260901_issue487_nerelan_runtime_brand_r2_v3",
  "previous_audit_outcome": "PR497_ACCEPTED_V4_REPLAY_STALE_BASE_AFTER_PR490_MAIN_ADVANCE_REANCHOR_REQUIRED",
  "supersedes_decision_id": "decision_20260901_issue444_auth_completion_r3_v4",
  "workstream_id": "issue444-auth-completion-r3-v5",
  "source_issue": 444,
  "parent_issue": 438,
  "historical_source_pr": 497,
  "historical_source_head": "180ac417c488735c312bcf77089a1ac16c400074",
  "integration_base_ref": "main",
  "base_sha": "1935e9c61fcb9dcc9f8d4ac72033c299423c1d9c",
  "activation_base_sha": "1935e9c61fcb9dcc9f8d4ac72033c299423c1d9c",
  "starting_head": "1935e9c61fcb9dcc9f8d4ac72033c299423c1d9c",
  "required_branch": "owner/issue444-auth-completion-r3-v5",
  "fresh_worktree_creation_required": true,
  "semantic_replay_only": true,
  "history_reuse_allowed": false,
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R3",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 4,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
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
  "live_provider_access_allowed": false,
  "credential_access_allowed": true,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": false,
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
    "verify remote main remains 1935e9c61fcb9dcc9f8d4ac72033c299423c1d9c and the fresh target branch has zero commits beyond that base",
    "verify PR 497 is closed stale-base historical evidence at accepted head 180ac417c488735c312bcf77089a1ac16c400074 and is not reused as landing authority",
    "commit this complete immutable v5 R3 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue444v5.materialize_activation_packet",
      "command": "after the unique immutable Decision activation commit run the repository-owned startup snapshot command-plan compiler transition lint and transition preflight; require PRE_EXECUTION_AUTHORIZED with zero blockers and commit only the five declared compiler-owned gate artifacts",
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
      "command_id": "issue444v5.replay_accepted_authentication_semantics",
      "command": "replay all twenty authorized authentication product source test and documentation paths byte-for-byte from closed stale-base PR 497 exact head 180ac417c488735c312bcf77089a1ac16c400074 onto locked current main without cherry-pick merge rebase or history reuse; preserve the already-integrated compact Settings layout durable Windows vault failure atomicity absolute OAuth deadline provider-owned token boundary and fresh external-session readiness",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "test_edit", "documentation_edit", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/os_vault.py",
        "reverse_agent/model_access/account_auth.py",
        "reverse_agent/model_access/contracts.py",
        "reverse_agent/model_access/store.py",
        "reverse_agent/model_access/service.py",
        "reverse_agent/platform_v1/opencode_server_transport.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "tests/test_model_access.py",
        "tests/platform_v1/test_opencode_server_transport.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_trusted_host.py",
        "frontend/src/schemas/model-access.ts",
        "frontend/src/lib/model-control-client.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/model-access-client.test.ts",
        "frontend/tests/connection-binding-flow.test.tsx",
        "docs/model-access.md",
        "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md"
      ]
    },
    {
      "command_id": "issue444v5.validate_product",
      "command": "run the required focused Model Access OpenCode transport executor trusted-host and complete Platform V1 backend suites; run focused and full frontend unit typecheck lint build build-mock and repository Playwright with a known local browser; require every functional journey to pass and classify only the exact inherited eight Home and Settings light and dark desktop and mobile visual-golden mismatches as evidence-only; forbid snapshot mutation; run transition lint preflight publication readiness and git diff check without a real provider or model call",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "integration_test", "lint", "build", "known_binary_execution", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue444v5.windows_vault_sentinel_proof",
      "command": "on the trusted Windows host store resolve from a fresh adapter and delete exactly one generated non-user Nerelan sentinel in Windows Credential Manager; never inspect a real user credential never print or persist sentinel material and verify post-delete not-found",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["known_binary_execution", "credential_access", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue444v5.publish_new_draft",
      "command": "after all local validation normally push the exact fresh branch and create one new Draft PR against locked main; update only that PR body; require fresh exact-head CI State Gate Decision Preflight and Model Access success and run Frontend Playwright for explicit functional plus inherited-eight-case visual classification",
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
      "command_id": "issue444v5.post_publication_binding",
      "command": "after Draft PR creation archive the inherited schema-v3 PR 490 active mainline intent byte-for-byte and bind active intent exactly once to the actual new PR number locked base current immutable Decision current generated Command Plan baseline workflow profile and merge-only policy; commit and normally push that binding",
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
        "project_state/mainline_merge_intents/archive/pr490_v3.json"
      ]
    },
    {
      "command_id": "issue444v5.independent_exact_head_audit",
      "command": "an independent auditor that did not implement the replay reviews and reproduces the unchanged exact remote head including vault failure atomicity Windows adapter safety secret confinement absolute deadline account-auth lifecycle external-session reuse current Settings density and all required exact-head checks; the auditor must confirm zero functional Playwright failure and zero new visual failure beyond the exact inherited eight-case evidence set before recording ACCEPTED or REWORK_REQUIRED on the new PR",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "unit_test", "pull_request_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue444v5.owner_landing",
      "command": "only after independent exact-head acceptance fresh successful exact-head workflows zero unresolved blockers unchanged locked base and head valid mainline intent and current repository-owned owner attestation mark the new PR ready once and merge once using merge commit with expected-head protection; verify natural post-merge main checks then close Issue 444 and reconcile Issues 441 and 438 where acceptance is satisfied",
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
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
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
    "project_state/mainline_merge_intents/archive/pr490_v3.json",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_model_access.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
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
    "project_state/mainline_merge_intents/archive/pr490_v3.json",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_model_access.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/model-access-client.test.ts",
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
    "tests/platform_v1/test_merge_intent.py",
    "frontend/tests/settings-density.test.tsx",
    "frontend/e2e/functional.spec.ts",
    "frontend/e2e/visual.spec.ts"
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
    "frontend/tests/settings-density.test.tsx",
    "frontend/e2e/snapshots/**",
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
    "merge_history",
    "cherry_pick",
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
    "live_provider_access",
    "tag_or_release",
    "deployment",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work",
    "plaintext_secret_storage",
    "custom_oauth_implementation",
    "real_user_credential_access"
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
      "normal branch push and new Draft PR creation and body update after deterministic local validation",
      "independent exact-head audit observation and PR comment",
      "owner attestation mark-ready expected-head merge post-merge verification and issue reconciliation after every landing precondition passes"
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
  "success_terminal": "AUTH_COMPLETION_R3_MERGED_CURRENT_MAIN_GREEN_ISSUES_RECONCILED",
  "blocked_terminal": "AUTH_COMPLETION_R3_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Replay the independently accepted PR #497 authentication product tree byte-for-byte onto locked current main while preserving its reviewed security and current compact Settings semantics:

1. an API key entered once is stored in Windows Credential Manager and reconstructed after trusted-host restart through a sanitized reference only;
2. OpenAI/ChatGPT account login is delegated to OpenCode's official provider OAuth surface and OpenCode alone owns PKCE, callback, access/refresh/session tokens and durable session storage;
3. existing external OpenCode CLI/account sessions are reused through one fresh sanitized executor-owned readiness probe without credential copying.

## Acceptance

1. This Decision is the unique first commit after `starting_head`, remains byte-identical thereafter, and every mutation stays within the exact v5 allowlist.
2. All twenty authorized product/source/test/documentation paths are byte-for-byte equal to PR #497 exact head `180ac417c488735c312bcf77089a1ac16c400074`; no current-main validator requires a semantic deviation.
3. API-key vault mutation and sanitized state persistence remain failure-atomic for create, same-ref replacement, authority-changing replacement, clear and Connection deletion; no orphan or split truth is created.
4. The Windows adapter has correct ctypes signatures, distinguishes not-found from locked/unavailable errors, frees native memory, rejects invalid or oversized blobs, and never logs credential material.
5. Persisted and browser-visible state contains only non-secret credential references and sanitized status; restart re-resolves through the OS vault and never reads secret material back to the browser.
6. Account login is explicit-user-action only and delegates to an authenticated loopback OpenCode server using advertised provider methods. The absolute monotonic deadline governs discovery, authorization and completion at or after expiry.
7. OpenCode exclusively owns OAuth and provider session tokens. Completion, failure, timeout, cancellation and logout-required states are explicit and secret-free, and existing external sessions use a fresh sanitized auth-list probe.
8. Required backend, frontend, Windows sentinel, exact-head CI, State Gate, Decision Preflight and Model Access checks pass without a real provider/model call.
9. Repository Playwright runs with a known browser. Every functional journey must pass. Only the inherited `home-light`, `home-dark`, `settings-light`, and `settings-dark` visual cases across desktop and mobile may be evidence-only mismatches; any additional or functional failure blocks. No file under `frontend/e2e/snapshots/**` may change.
10. An independent auditor accepts the unchanged new-PR head and explicitly confirms zero new functional or visual failure beyond that inherited eight-case set.
11. Landing occurs only with unchanged base/head, zero unresolved blockers, valid schema-v3 intent and current owner attestation, using one Ready action and one expected-head merge commit.
12. Natural post-merge main checks are successful and Issues 444, 441 and 438 are reconciled only where their acceptance is satisfied. No auto-merge, direct-main push, rebase, cherry-pick, force push, snapshot refresh, tag, release or deployment occurs.

## Execution policy

- The owner explicitly authorized this bounded R3 v5 round and its publication lifecycle in the user request. That authority is represented only by this immutable Decision and its generated Command Plan; owner identity alone never bypasses a gate.
- PR #497 at `180ac417c488735c312bcf77089a1ac16c400074` is accepted stale-base content evidence only. Reuse file content and semantics, never its history or landing authority.
- Deterministic acceptance makes no real provider/model call and performs no live account consent. The only credential-store access is one generated non-user Nerelan sentinel that is stored, resolved from a fresh adapter, deleted, and confirmed absent without printing its material.
- The inherited eight visual mismatches are evidence-only because they already exist on current main; this round cannot mutate visual goldens or weaken thresholds.
- Any Decision mutation, base/head drift, out-of-scope path, failed functional check, new visual failure, credential leak, independent audit rejection, unresolved review thread or landing-attestation failure stops the round with exact evidence.

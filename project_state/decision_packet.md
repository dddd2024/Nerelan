# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v3",
  "round_id": "round_20260816_issue224_external_session_executor_managed_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v2",
  "follows_last_round_id": "round_20260816_issue224_external_session_executor_managed_r2_v2",
  "previous_audit_outcome": "ISSUE224_V2_SUPERSEDED_BEFORE_EXECUTION_FRONTEND_RESPONSE_CONTRACT_GAPS",
  "supersedes_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v2",
  "superseded_branches_must_not_execute": [
    "owner/issue224-external-session-executor-managed-r2-v1",
    "owner/issue224-external-session-executor-managed-r2-v2"
  ],
  "workstream_id": "issue224-external-session-executor-managed-r2-v3",
  "source_issue": 224,
  "parent_issue": 148,
  "required_branch": "owner/issue224-external-session-executor-managed-r2-v3",
  "starting_head": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "activation_base_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "canonical_planning_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "product_setup_mutation_allowed": false,
  "model_api_invocation_allowed": false,
  "provider_network_call_allowed": false,
  "opencode_invocation_allowed": false,
  "opencode_task_invocation_allowed": false,
  "opencode_auth_metadata_probe_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "live_connection_probe_allowed": false,
  "real_user_credential_access_allowed": false,
  "synthetic_test_credential_fixture_allowed": true,
  "synthetic_test_credential_fixture_scope": "authorized_test_files_and_temporary_test_state_only",
  "real_task_store_access_allowed": false,
  "product_change_commit_limit": 1,
  "required_runtime_status": "executor_managed",
  "derived_connection_status_write_policy": "reject_caller_supplied",
  "connection_provider_contract": "safe_identifier_parity_backend_frontend",
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-planning-smoke status --short",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue224-external-session-executor-managed-r2-v3",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue224-external-session-executor-managed-r2-v3",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue224-external-session-executor-managed-r2-v3);if($b){'ISSUE224_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue224-external-session-executor-managed-r2-v3'){'ISSUE224_V3_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE224_V3_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue224-external-session-executor-managed-r2-v3 F:/reverse-agent-issue224-external-session-executor-managed-r2-v3 origin/owner/issue224-external-session-executor-managed-r2-v3",
    "Set-Location F:/reverse-agent-issue224-external-session-executor-managed-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD 3b650e6239336c796593cecd3c137cf839cf1e95",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue224v3.status_before",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.python_focused_tests",
      "command": "python -m pytest tests/test_connection_binding.py tests/platform_v1/test_binding_resolver.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.frontend_focused_test",
      "command": "npm --prefix frontend test -- model-access-client.test.ts",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.frontend_typecheck",
      "command": "npm --prefix frontend run typecheck",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.changed_paths_before_commit",
      "command": "git diff --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.stage_exact_product",
      "command": "git add reverse_agent/model_access/contracts.py reverse_agent/model_access/store.py reverse_agent/platform_v1/trusted_host.py reverse_agent/platform_v1/binding_resolver.py tests/test_connection_binding.py tests/platform_v1/test_binding_resolver.py tests/platform_v1/test_trusted_host.py frontend/src/schemas/model-access.ts frontend/tests/model-access-client.test.ts",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_product_mutation", "repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.staged_diff_check",
      "command": "git diff --cached --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.commit_product",
      "command": "git commit -m \"Implement executor-managed external sessions\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue224v3.head_after_commit",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.compare_paths_after_commit",
      "command": "git diff --name-only 3b650e6239336c796593cecd3c137cf839cf1e95..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v3.push_branch",
      "command": "git push origin owner/issue224-external-session-executor-managed-r2-v3",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue224v3.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v3",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue224v3.status_final",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/tests/model-access-client.test.ts",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    "frontend/src/lib/model-control-client.ts",
    "frontend/package.json",
    "tests/platform_v1/test_opencode_executor.py",
    "AGENTS.md",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/**",
    "frontend/src/routes/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "tests/platform_v1/test_opencode_executor.py",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "governance_mutation_outside_generated_gates",
    "real_user_credential_file_discovery",
    "real_user_credential_file_read",
    "real_user_credential_value_read",
    "real_user_credential_value_print",
    "real_user_credential_value_hash",
    "real_user_credential_value_length_or_measurement",
    "import_real_credentials_into_tests",
    "auth_login",
    "auth_logout",
    "opencode_invocation",
    "opencode_auth_probe",
    "opencode_run",
    "opencode_models",
    "model_api_invocation",
    "provider_network_call",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
    "product_setup_mutation",
    "real_task_store_access",
    "dependency_install",
    "package_lock_mutation",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "tag_or_release",
    "direct_push_main"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue224-external-session-executor-managed-r2-v3",
      "git push origin owner/issue224-external-session-executor-managed-r2-v3"
    ],
    "external_provider_network_allowed": false,
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_trusted_host.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/tests/model-access-client.test.ts",
    "project_state/gates/**"
  ]
}
```

# Goal

Replace the default OpenCode human-terminal `auth list` readiness dependency with explicit `executor_managed` runtime state for `external_cli_session` and `account_login`, while preserving exact provider/base/model routing, secret isolation, fail-closed actual execution, optional trusted exact-provider refresh, and frontend/backend Connection contract parity.

# Required implementation semantics

1. `reverse_agent/model_access/contracts.py`
   - Add exact public external-session status `executor_managed`.
   - Add no secret, credential, path, or executor-specific credential field.

2. `reverse_agent/model_access/store.py`
   - New and freshly loaded `external_cli_session` / `account_login` Connections start as `executor_managed`.
   - `external_session_status` remains excluded from persisted state.
   - Reject caller-supplied `external_session_status` / `externalSessionStatus` on Connection writes as derived read-only metadata.
   - An authority-bearing change to an existing external-session Connection resets runtime status to `executor_managed`.
   - Preserve `refresh_external_session_status()` as a trusted internal exact-provider-ID hook: exact metadata may set `available`; absent exact provider metadata may set `missing`.
   - API-key and none semantics remain unchanged.

3. `reverse_agent/platform_v1/trusted_host.py`
   - Default `auth_list_probe` is `None`; do not import/use OpenCode auth-list probing as default startup authority.
   - `_refresh_external_session_auth()` runs only when an explicit trusted probe is injected.
   - Normal fresh startup performs zero OpenCode invocation and retains `executor_managed`.
   - Explicit injected trusted probes retain deterministic `available`/`missing` behavior.

4. `reverse_agent/platform_v1/binding_resolver.py`
   - `external_cli_session` / `account_login` accept exactly `executor_managed` or `available`.
   - `missing` and every unknown status fail closed with `external_session_unavailable`.
   - Exact Connection provider/base/model validation remains unchanged.

5. `frontend/src/schemas/model-access.ts`
   - Add exact `executor_managed` to `ExternalSessionStatusSchema`.
   - Align `ConnectionProviderSchema` with backend Connection provider identifier grammar `^[a-z0-9][a-z0-9._-]{0,79}$`; do not enumerate specific providers.
   - Preserve `ConnectionInputSchema` omission of `secretStatus` and `externalSessionStatus`.

6. `reverse_agent/platform_v1/opencode_executor.py` and `frontend/src/lib/model-control-client.ts` are reference-only and MUST NOT change.
   - Existing non-api-key config must still use exact Connection provider ID.
   - Existing Connection serializer must continue omitting derived statuses.
   - No display-name mapping or auth-list parser expansion is authorized.

# Synthetic test fixtures versus real credentials

Authorized tests may create/use deterministic, obviously non-real sentinel values solely as unit-test fixtures, including existing fixed fake API keys and temporary pytest/Vitest state. Such synthetic values may be asserted or read from temporary test fixtures when the test validates sanitization.

This does not authorize any real credential access. Do not search for, inspect, read, copy, print, hash, measure, compare, import, or persist any real API key, token, cookie, session, OpenCode auth-store value, credential environment value, shell-history secret, or provider credential. Do not read real credential/auth/config stores.

# Required test semantics

Python authorized tests must prove:
- caller-supplied derived external-session status is rejected;
- new/reloaded external Connection reports `executor_managed`;
- persisted state contains no runtime status/evidence;
- authority-bearing external changes reset to `executor_managed`;
- trusted exact refresh can set `available`/`missing`;
- default CombinedTrustedHost invokes no OpenCode auth metadata and retains `executor_managed`;
- injected trusted probe still derives `available`/`missing`;
- BindingResolver accepts `executor_managed` and `available`, rejects `missing` and unknown;
- API-key/none public status semantics stay unchanged.

Frontend authorized test must prove:
- HTTP/snake-case Connection response with provider `sensetime` and status `executor_managed` normalizes successfully;
- generic safe provider IDs accepted by backend also validate in frontend;
- invalid provider IDs remain rejected;
- upsert Connection request still excludes `secret_status`/`secretStatus` and `external_session_status`/`externalSessionStatus`.

The unchanged fake-only `test_opencode_executor.py` is validation-only and proves exact provider routing/config regression absence without real OpenCode invocation.

# Publication boundary

Only one implementation commit may be created after all required Python tests, focused frontend test, frontend typecheck, and diff checks pass. Stage exactly the nine authorized product/test files. Generated gate artifacts remain unstaged. Do not modify package manifests or lockfiles. Push only `owner/issue224-external-session-executor-managed-r2-v3`. Do not open a PR or merge.

# Terminal

Success:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_READY_FOR_OWNER_AUDIT`

Blocked:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_BLOCKED`

On BLOCKED, preserve the worktree and generated gate evidence and stop. Do not widen scope, inspect real credentials, invoke OpenCode, install dependencies, mutate Product Setup, or repair the Decision.

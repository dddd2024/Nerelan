# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v2",
  "round_id": "round_20260816_issue224_external_session_executor_managed_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v1",
  "follows_last_round_id": "round_20260816_issue224_external_session_executor_managed_r2_v1",
  "previous_audit_outcome": "ISSUE224_V1_SUPERSEDED_BEFORE_EXECUTION_SYNTHETIC_TEST_CREDENTIAL_PERMISSION_AMBIGUITY",
  "supersedes_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v1",
  "superseded_branch_must_not_execute": "owner/issue224-external-session-executor-managed-r2-v1",
  "workstream_id": "issue224-external-session-executor-managed-r2-v2",
  "source_issue": 224,
  "parent_issue": 148,
  "required_branch": "owner/issue224-external-session-executor-managed-r2-v2",
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
  "frontend_roundtrip_compatibility_verified": true,
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue224-external-session-executor-managed-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue224-external-session-executor-managed-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue224-external-session-executor-managed-r2-v2);if($b){'ISSUE224_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue224-external-session-executor-managed-r2-v2'){'ISSUE224_V2_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE224_V2_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue224-external-session-executor-managed-r2-v2 F:/reverse-agent-issue224-external-session-executor-managed-r2-v2 origin/owner/issue224-external-session-executor-managed-r2-v2",
    "Set-Location F:/reverse-agent-issue224-external-session-executor-managed-r2-v2",
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
      "command_id": "issue224v2.status_before",
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
      "command_id": "issue224v2.focused_tests",
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
      "command_id": "issue224v2.diff_check",
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
      "command_id": "issue224v2.changed_paths_before_commit",
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
      "command_id": "issue224v2.stage_exact_product",
      "command": "git add reverse_agent/model_access/contracts.py reverse_agent/model_access/store.py reverse_agent/platform_v1/trusted_host.py reverse_agent/platform_v1/binding_resolver.py tests/test_connection_binding.py tests/platform_v1/test_binding_resolver.py tests/platform_v1/test_trusted_host.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_product_mutation", "repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v2.staged_paths",
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
      "command_id": "issue224v2.staged_diff_check",
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
      "command_id": "issue224v2.commit_product",
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
      "command_id": "issue224v2.head_after_commit",
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
      "command_id": "issue224v2.compare_paths_after_commit",
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
      "command_id": "issue224v2.push_branch",
      "command": "git push origin owner/issue224-external-session-executor-managed-r2-v2",
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
      "command_id": "issue224v2.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v2",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue224v2.status_final",
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
    "frontend/**",
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue224-external-session-executor-managed-r2-v2",
      "git push origin owner/issue224-external-session-executor-managed-r2-v2"
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
    "project_state/gates/**"
  ]
}
```

# Goal

Replace the default OpenCode human-terminal `auth list` readiness dependency with an explicit `executor_managed` runtime state for `external_cli_session` and `account_login`, while preserving exact provider/base/model routing, secret isolation, fail-closed real execution, and the optional trusted exact-provider refresh hook.

# Required implementation semantics

1. `reverse_agent/model_access/contracts.py`
   - Add exact public external-session status `executor_managed`.
   - Add no secret, credential, path, or executor-specific credential field.

2. `reverse_agent/model_access/store.py`
   - New and freshly loaded `external_cli_session` / `account_login` Connections start as `executor_managed`.
   - `external_session_status` remains excluded from persisted state.
   - Reject caller-supplied `external_session_status` / `externalSessionStatus` on Connection writes as derived read-only metadata. Do not trust, normalize, echo through, or persist caller assertions.
   - An authority-bearing change to an existing external-session Connection resets runtime status to `executor_managed`.
   - Preserve `refresh_external_session_status()` as a trusted internal exact-provider-ID hook: exact metadata may set external-session Connections to `available`; absent exact provider metadata may set them to `missing`.
   - API-key and none semantics remain unchanged.

3. `reverse_agent/platform_v1/trusted_host.py`
   - Default `auth_list_probe` is `None`; do not import/use OpenCode auth-list probing as the default startup authority.
   - `_refresh_external_session_auth()` runs only when an explicit trusted probe is injected.
   - A normal fresh host with an external-session Connection performs zero OpenCode invocation and retains `executor_managed`.
   - Explicit injected trusted probes retain deterministic `available`/`missing` refresh behavior.

4. `reverse_agent/platform_v1/binding_resolver.py`
   - `external_cli_session` / `account_login` accept `external_session_status` in exactly `{executor_managed, available}`.
   - `missing` and every unknown status fail closed with `external_session_unavailable`.
   - Exact Connection provider/base/model validation remains unchanged.

5. `reverse_agent/platform_v1/opencode_executor.py` is reference-only and MUST NOT change.
   - Existing non-api-key config must still use the exact Connection provider ID.
   - No display-name mapping or auth-list parser expansion is authorized.

# Frontend/write-boundary compatibility

The canonical frontend serializer already omits `secretStatus` and `externalSessionStatus` from Connection PUT bodies, so rejecting caller-supplied derived status does not require frontend changes. Do not modify frontend or `model_access/service.py` in this round.

# Synthetic test fixtures versus real credentials

The authorized tests may create/use deterministic, obviously non-real sentinel values solely as unit-test fixtures, including existing fixed fake API keys and temporary test state. Examples include `sk-test-*`, `dummy-*`, and other constants that are clearly synthetic by construction. Such strings may be asserted, persisted into pytest temporary fixtures when the test specifically validates sanitization, and read back from those temporary fixtures.

This permission does NOT extend to any user/system/provider credential. The Agent must not search for, inspect, read, copy, print, hash, measure, compare, import, or persist any real API key, token, cookie, session, OpenCode auth-store value, credential environment value, shell-history secret, or other real authentication material. Do not read real credential/auth/config files. Do not convert a discovered real value into a test fixture.

# Required test semantics

Update only the three authorized test files. Prove at minimum:
- caller-supplied derived external-session status is rejected;
- new/reloaded external Connection reports `executor_managed`;
- state file contains no `external_session_status` or persisted `executor_managed` evidence field/value;
- authority-bearing external Connection changes reset status to `executor_managed`;
- trusted exact refresh can set `available` and `missing`;
- default CombinedTrustedHost does not call OpenCode auth metadata and retains `executor_managed`;
- explicitly injected probe still derives `available`/`missing`;
- BindingResolver accepts `executor_managed` and `available`, rejects `missing` and unknown;
- API-key/none public status semantics stay unchanged.

The required validation command also runs the unchanged fake-only `test_opencode_executor.py` to prove routing/config regressions are absent without real OpenCode invocation.

# Publication boundary

Only one implementation commit may be created after all required tests and diff checks pass. Stage exactly the seven authorized product/test files; generated gate artifacts remain unstaged. Push only `owner/issue224-external-session-executor-managed-r2-v2`. Do not open a PR or merge.

# Terminal

Success:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_READY_FOR_OWNER_AUDIT`

Blocked:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_BLOCKED`

On BLOCKED, preserve the worktree and generated gate evidence and stop. Do not widen scope, inspect real credentials, invoke OpenCode, mutate Product Setup, or repair the Decision.

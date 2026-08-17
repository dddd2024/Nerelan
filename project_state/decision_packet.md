# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260817_issue224_external_session_executor_managed_r2_v4",
  "round_id": "round_20260817_issue224_external_session_executor_managed_r2_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v3",
  "follows_last_round_id": "round_20260816_issue224_external_session_executor_managed_r2_v3",
  "previous_audit_outcome": "ISSUE224_V3_IMPLEMENTATION_BLOCKED_FRONTEND_NODE_MODULES_ABSENT",
  "supersedes_decision_id": "decision_20260816_issue224_external_session_executor_managed_r2_v3",
  "superseded_branches_must_not_execute": [
    "owner/issue224-external-session-executor-managed-r2-v1",
    "owner/issue224-external-session-executor-managed-r2-v2",
    "owner/issue224-external-session-executor-managed-r2-v3"
  ],
  "workstream_id": "issue224-external-session-executor-managed-r2-v4",
  "source_issue": 224,
  "parent_issue": 148,
  "required_branch": "owner/issue224-external-session-executor-managed-r2-v4",
  "starting_head": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "activation_base_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "canonical_planning_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "required_recovery_source_head": "0d9832975621abb04b188cd61d3d0dded98e2fb4",
  "required_recovery_worktree": "F:/reverse-agent-issue224-external-session-executor-managed-r2-v3",
  "preserved_dirty_worktree_reuse_allowed": true,
  "fresh_worktree_creation_required": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_recovery": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "worktree_creation_allowed": false,
  "local_branch_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "package_installation_allowed": true,
  "package_installation_exact_command_only": "npm ci --prefix frontend --no-audit --no-fund",
  "package_installation_scope": "frontend/node_modules only from canonical package-lock.json",
  "package_json_expected_blob": "f63104f56cf4d0ae3955bcc5628a43b74e4707e4",
  "package_lock_expected_blob": "ac4b0e89b94b95b97850c8367fcabd28fd3f4a66",
  "minimum_node_version": "22.22.0",
  "product_setup_mutation_allowed": false,
  "model_api_invocation_allowed": false,
  "provider_network_call_allowed": false,
  "package_registry_network_allowed": true,
  "opencode_invocation_allowed": false,
  "opencode_task_invocation_allowed": false,
  "opencode_auth_metadata_probe_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "live_connection_probe_allowed": false,
  "real_user_credential_access_allowed": false,
  "synthetic_test_credential_fixture_allowed": true,
  "real_task_store_access_allowed": false,
  "product_change_commit_limit": 1,
  "required_runtime_status": "executor_managed",
  "derived_connection_status_write_policy": "reject_caller_supplied",
  "connection_provider_contract": "safe_identifier_parity_backend_frontend",
  "bootstrap_exception_files": [
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
  "bootstrap_exception_commands": [
    "Set-Location F:/reverse-agent-issue224-external-session-executor-managed-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git diff --cached --name-only",
    "git diff --name-only",
    "git fetch origin owner/repository-modernization-v2-planning",
    "git fetch origin owner/issue224-external-session-executor-managed-r2-v4",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v4",
    "powershell -NoProfile -Command \"$b=(git branch --list owner/issue224-external-session-executor-managed-r2-v4);if($b){'ISSUE224_V4_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};'ISSUE224_V4_LOCAL_BRANCH_ABSENT'\"",
    "git switch -c owner/issue224-external-session-executor-managed-r2-v4 --track origin/owner/issue224-external-session-executor-managed-r2-v4",
    "git rev-parse HEAD",
    "git merge-base HEAD 3b650e6239336c796593cecd3c137cf839cf1e95",
    "git status --short",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue224v4.status_before",
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
      "command_id": "issue224v4.package_json_blob_before",
      "command": "git hash-object frontend/package.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.package_lock_blob_before",
      "command": "git hash-object frontend/package-lock.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.node_version",
      "command": "node --version",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["runtime_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.npm_version",
      "command": "npm --version",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["runtime_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.frontend_dependency_bootstrap",
      "command": "npm ci --prefix frontend --no-audit --no-fund",
      "phase": "environment_recovery",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_installation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.package_json_blob_after",
      "command": "git hash-object frontend/package.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.package_lock_blob_after",
      "command": "git hash-object frontend/package-lock.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.package_manifest_diff",
      "command": "git diff --exit-code -- frontend/package.json frontend/package-lock.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v4.python_focused_tests",
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
      "command_id": "issue224v4.frontend_focused_test",
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
      "command_id": "issue224v4.frontend_typecheck",
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
      "command_id": "issue224v4.diff_check",
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
      "command_id": "issue224v4.changed_paths_before_commit",
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
      "command_id": "issue224v4.stage_exact_product",
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
      "command_id": "issue224v4.staged_paths",
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
      "command_id": "issue224v4.staged_diff_check",
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
      "command_id": "issue224v4.commit_product",
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
      "command_id": "issue224v4.head_after_commit",
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
      "command_id": "issue224v4.compare_paths_after_commit",
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
      "command_id": "issue224v4.push_branch",
      "command": "git push origin owner/issue224-external-session-executor-managed-r2-v4",
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
      "command_id": "issue224v4.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v4",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue224v4.status_final",
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
  "generated_local_dependency_paths": [
    "frontend/node_modules/**"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    "frontend/src/lib/model-control-client.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/.gitignore",
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
    "discard_preserved_v3_edits",
    "npm_install",
    "npm_update",
    "npm_audit_fix",
    "alternate_package_manager_install",
    "package_manifest_mutation",
    "package_lock_mutation",
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
    "package_registry_access_allowed_only_during_exact_npm_ci": true
  },
  "terminal_success": "EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_READY_FOR_OWNER_AUDIT",
  "terminal_blocked": "EXTERNAL_SESSION_EXECUTOR_MANAGED_IMPLEMENTATION_BLOCKED"
}
```

## Owner recovery intent

R2 V3 reached `PRE_EXECUTION_AUTHORIZED`, produced the complete nine-file authorized implementation, and passed its bounded Python validation (`247 passed, 1 skipped`), but correctly stopped before stage/commit because `frontend/node_modules` was absent and V3 explicitly forbade dependency installation. V4 treats that as an environment-only blocker, not an implementation rejection.

V4 intentionally reuses the preserved V3 worktree at `F:/reverse-agent-issue224-external-session-executor-managed-r2-v3`. Before switching authority, local execution must prove all of the following:

1. current HEAD is exactly V3 authority `0d9832975621abb04b188cd61d3d0dded98e2fb4`;
2. nothing is staged;
3. the dirty tracked set is exactly the nine authorized product/test files plus the five generated gate files from V3;
4. no implementation commit or push exists;
5. canonical planning remains exactly `3b650e6239336c796593cecd3c137cf839cf1e95`.

Only then may the preserved dirty worktree switch to the V4 tracking branch. Switching authority must preserve the nine implementation edits; any conflict, lost edit, extra tracked change, or staged content is a hard stop.

## Frontend environment recovery

The only newly authorized capability is one lockfile-bound dependency bootstrap:

`npm ci --prefix frontend --no-audit --no-fund`

Before running it, `git hash-object frontend/package.json` must equal `f63104f56cf4d0ae3955bcc5628a43b74e4707e4` and `git hash-object frontend/package-lock.json` must equal `ac4b0e89b94b95b97850c8367fcabd28fd3f4a66`. Node must satisfy the repository engine floor `>=22.22.0`.

After `npm ci`, both blob hashes must remain exactly unchanged and `git diff --exit-code -- frontend/package.json frontend/package-lock.json` must exit 0. `frontend/node_modules/**` is local generated dependency state and is already ignored by `frontend/.gitignore`; it must never be staged or committed.

No other dependency command is authorized. Do not use `npm install`, `npm update`, `npm audit fix`, pnpm, yarn, bun, pip installation, lockfile repair, or package-version changes. If `npm ci` fails under the canonical lockfile or Node is below the required version, stop blocked rather than repair the environment ad hoc.

## Product implementation requirements retained from V3

The preserved nine-file implementation remains bounded to these semantics:

- `external_cli_session` / `account_login` gain runtime-derived `executor_managed` state;
- caller-supplied derived external-session status is rejected;
- new/reloaded external sessions default to `executor_managed` and the runtime status is not persisted;
- authority-bearing external Connection changes reset runtime evidence to `executor_managed`;
- explicit trusted exact-provider refresh may still set `available` / `missing`;
- default `CombinedTrustedHost` performs no OpenCode auth-list probe;
- BindingResolver accepts `executor_managed` / `available` and rejects `missing` / unknown;
- `opencode_executor.py` remains unchanged and exact provider/base/model routing remains authoritative;
- frontend accepts `executor_managed` and backend-safe provider identifiers such as `sensetime`, while invalid provider IDs remain rejected;
- frontend write payloads still cannot assert derived status.

## Validation and publication

After environment recovery, rerun all V4-authorized Python and frontend validations. Do not rely solely on V3's earlier Python result for publication. Only after every required validation exits 0 may the exact nine product/test files be staged, committed once with the authorized message, and pushed to the V4 branch.

The five generated transition-gate files remain unstaged. `project_state/decision_packet.md`, package manifests, package lock, reference-only files, and `frontend/node_modules` must not be included in the implementation commit.

No real/user credential access, OpenCode invocation, model/provider request, Connection live test, relay lease, Task execution, Product Setup mutation, real TaskStore access, PR creation, or merge is authorized.

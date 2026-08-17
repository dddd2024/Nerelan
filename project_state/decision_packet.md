# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260817_issue224_external_session_executor_managed_r2_v7",
  "round_id": "round_20260817_issue224_external_session_executor_managed_r2_v7",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260817_issue224_external_session_executor_managed_r2_v6",
  "follows_last_round_id": "round_20260817_issue224_external_session_executor_managed_r2_v6",
  "previous_audit_outcome": "ISSUE224_V6_OWNER_AUDIT_REJECTED_RUNTIME_EVIDENCE_RESET_AND_TEST_MASKING",
  "supersedes_decision_id": "decision_20260817_issue224_external_session_executor_managed_r2_v6",
  "superseded_branches_must_not_land": [
    "owner/issue224-external-session-executor-managed-r2-v6"
  ],
  "workstream_id": "issue224-external-session-executor-managed-r2-v7",
  "source_issue": 224,
  "parent_issue": 148,
  "required_branch": "owner/issue224-external-session-executor-managed-r2-v7",
  "starting_head": "f252dcffd84d033a8d38c9d4db083ad32b86234b",
  "activation_base_sha": "f252dcffd84d033a8d38c9d4db083ad32b86234b",
  "canonical_planning_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "required_recovery_source_head": "f252dcffd84d033a8d38c9d4db083ad32b86234b",
  "required_recovery_worktree": "F:/reverse-agent-issue224-external-session-executor-managed-r2-v3",
  "preserved_worktree_reuse_allowed": true,
  "fresh_worktree_creation_required": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "worktree_creation_allowed": false,
  "branch_creation_allowed": true,
  "branch_creation_scope": "local_tracking_branch_owner/issue224-external-session-executor-managed-r2-v7_only",
  "remote_branch_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "package_installation_allowed": false,
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
  "real_task_store_access_allowed": false,
  "product_change_commit_limit": 1,
  "required_runtime_status": "executor_managed",
  "non_authority_runtime_evidence_policy": "preserve_existing_available_or_missing",
  "authority_change_runtime_evidence_policy": "reset_executor_managed",
  "bootstrap_exception_files": [
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
    "git fetch origin owner/issue224-external-session-executor-managed-r2-v7",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v7",
    "powershell -NoProfile -Command \"$b=(git branch --list owner/issue224-external-session-executor-managed-r2-v7);if($b){'ISSUE224_V7_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};'ISSUE224_V7_LOCAL_BRANCH_ABSENT'\"",
    "git switch -c owner/issue224-external-session-executor-managed-r2-v7 --track origin/owner/issue224-external-session-executor-managed-r2-v7",
    "git rev-parse HEAD",
    "git merge-base HEAD f252dcffd84d033a8d38c9d4db083ad32b86234b",
    "git status --short",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue224v7.status_before",
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
      "command_id": "issue224v7.python_focused_tests",
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
      "command_id": "issue224v7.frontend_focused_test",
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
      "command_id": "issue224v7.frontend_typecheck",
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
      "command_id": "issue224v7.diff_check",
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
      "command_id": "issue224v7.changed_paths_before_commit",
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
      "command_id": "issue224v7.stage_exact_fix",
      "command": "git add reverse_agent/model_access/store.py tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_product_mutation", "repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v7.staged_paths",
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
      "command_id": "issue224v7.staged_diff_check",
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
      "command_id": "issue224v7.commit_fix",
      "command": "git commit -m \"Preserve trusted external session evidence\"",
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
      "command_id": "issue224v7.head_after_commit",
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
      "command_id": "issue224v7.compare_paths_after_commit",
      "command": "git diff --name-only f252dcffd84d033a8d38c9d4db083ad32b86234b..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue224v7.push_branch",
      "command": "git push origin owner/issue224-external-session-executor-managed-r2-v7",
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
      "command_id": "issue224v7.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue224-external-session-executor-managed-r2-v7",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue224v7.status_final",
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
    "reverse_agent/model_access/store.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_opencode_executor.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/tests/model-access-client.test.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "project_state/schemas/**"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "tests/platform_v1/test_binding_resolver.py",
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
    "auth_login",
    "auth_logout",
    "opencode_invocation",
    "opencode_auth_probe",
    "opencode_run",
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
  ]
}
```

## Implementation scope

This is a narrow post-V6 Owner-audit repair. Preserve the accepted V6 product implementation and change only the three authorized files.

### Store correction

In `ModelProfileStore.upsert_connection`, external-session runtime evidence MUST follow these rules:

1. New `account_login` / `external_cli_session` Connection -> `executor_managed`.
2. Reload from sanitized persistence -> `executor_managed` (already implemented in V6; do not alter).
3. Existing external Connection with authority-bearing change (`provider`, `base_url`, or `auth_method`) -> reset `executor_managed`.
4. Existing external Connection with NO authority-bearing change -> preserve the existing runtime status exactly. In particular, a trusted internal refresh that produced `available` or `missing` MUST survive a name-only or enabled-only upsert.
5. Caller-supplied derived status remains rejected. Do not reopen status injection.

The expected minimal product form is equivalent to leaving `external_status` untouched on the non-authority branch, not assigning `executor_managed` in both branches.

### Store regressions

Update `tests/test_connection_binding.py` so the prior misleading authority-unchanged test no longer asserts that `available` is discarded. Add/adjust tests to prove:

- trusted `available` survives an authority-unchanged upsert (prefer a name-only change so the test proves a genuine non-authority mutation);
- trusted `missing` survives an authority-unchanged upsert;
- provider/base/auth change still resets to `executor_managed`;
- new/reloaded behavior, non-persistence, caller rejection, and API-key semantics remain unchanged.

### Trusted-host regression integrity

In `tests/platform_v1/test_trusted_host.py`, change only the default-startup regression. It MUST NOT use `except Exception: pass` around `host.start()`. Start the host normally on ephemeral ports and use `try/finally` only to guarantee `host.stop()`. An unexpected startup exception must fail the test. Confirm after successful startup/stop that the external Connection remains `executor_managed` and no default auth probe was configured or invoked.

Do not modify `reverse_agent/platform_v1/trusted_host.py`; Owner static audit accepted its V6 product behavior.

## Validation

Run the exact bounded Python suite plus the unchanged frontend focused Vitest and TypeScript typecheck. Existing `frontend/node_modules` from V6 may be reused as ignored environment state; installing or updating dependencies is forbidden in V7. If it is unavailable, fail closed rather than installing.

Success terminal:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_V7_FIX_READY_FOR_OWNER_AUDIT`

Blocked terminal:
`EXTERNAL_SESSION_EXECUTOR_MANAGED_V7_FIX_BLOCKED`

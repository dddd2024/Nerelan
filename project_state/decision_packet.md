# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260817_issue226_product_setup_executor_managed_r2_v1",
  "round_id": "round_20260817_issue226_product_setup_executor_managed_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260817_issue224_external_session_executor_managed_r2_v8",
  "follows_last_round_id": "round_20260817_issue224_external_session_executor_managed_r2_v8",
  "previous_audit_outcome": "ISSUE224_EXECUTOR_MANAGED_EXTERNAL_SESSION_ACCEPTED_AND_LANDED",
  "workstream_id": "issue226-product-setup-executor-managed-r2-v1",
  "source_issue": 226,
  "parent_issue": 148,
  "required_branch": "owner/issue226-product-setup-executor-managed-r2-v1",
  "starting_head": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "activation_base_sha": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "canonical_planning_sha": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "product_setup_mutation_allowed": true,
  "provider_network_call_allowed": false,
  "opencode_invocation_allowed": false,
  "opencode_task_invocation_allowed": false,
  "opencode_auth_metadata_probe_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "live_connection_probe_allowed": false,
  "package_installation_allowed": false,
  "real_user_credential_access_allowed": false,
  "real_task_store_access_allowed": false,
  "synthetic_test_credential_fixture_allowed": false,
  "product_change_commit_limit": 0,
  "required_runtime_status": "executor_managed",
  "default_auth_list_probe_required": null,
  "fresh_os_process_cycles_required": 2,
  "first_model_auth_validity_proof_deferred_to_dogfood1": true,
  "authority_worktree": "F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1",
  "source_worktree": "F:/reverse-agent-issue226-product-setup-source-v1",
  "external_harness_write_path": "F:/reverse-agent-issue226-product-setup-bootstrap-v3/setup_bootstrap.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue226-product-setup-bootstrap-v3/**",
    "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json"
  ],
  "product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "product_setup_target_must_be_absent_before_install": true,
  "readiness_must_precede_product_setup_install": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "canonical_setup": {
    "connection_id": "sensenova-67-flash-lite",
    "connection_name": "SenseNova 6.7 Flash-Lite",
    "provider": "sensetime",
    "base_url": "https://token.sensenova.cn/v1",
    "auth_method": "external_cli_session",
    "binding_id": "opencode-sensenova-67-flash-lite",
    "binding_name": "OpenCode SenseNova 6.7 Flash-Lite",
    "executor_id": "opencode",
    "model_id": "sensenova-6.7-flash-lite",
    "enabled": true
  },
  "credential_boundary": {
    "agent_or_harness_direct_credential_file_read_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "opencode_internal_credential_resolution_allowed": false,
    "auth_metadata_probe_allowed": false,
    "raw_credential_persistence_allowed": false,
    "provider_credential_use_for_model_request_allowed": false
  },
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
    "bmad_installation_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue226-product-setup-executor-managed-r2-v1"
    ],
    "loopback_model_control_http_allowed": true,
    "loopback_task_api_start_allowed": true,
    "loopback_credential_relay_server_start_allowed": true,
    "credential_relay_lease_allowed": false,
    "external_provider_network_allowed": false,
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue226-product-setup-executor-managed-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue226-product-setup-executor-managed-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue226-product-setup-executor-managed-r2-v1);if($b){'ISSUE226_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1'){'ISSUE226_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue226-product-setup-source-v1'){'ISSUE226_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue226-product-setup-bootstrap-v3'){'ISSUE226_V1_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE226_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue226-product-setup-executor-managed-r2-v1 F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1 origin/owner/issue226-product-setup-executor-managed-r2-v1",
    "Set-Location F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD 5739b63875b7cfda0d0cdc14113524959fdf5ec0",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue226v1.target_absence_precheck",
      "command": "powershell -NoProfile -Command \"if(Test-Path -LiteralPath 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json'){'PRODUCT_SETUP_TARGET_BECAME_PRESENT';exit 20};'PRODUCT_SETUP_TARGET_ABSENT'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.source_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue226-product-setup-source-v1 5739b63875b7cfda0d0cdc14113524959fdf5ec0",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.source_head",
      "command": "git -C F:/reverse-agent-issue226-product-setup-source-v1 rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.source_status_before",
      "command": "git -C F:/reverse-agent-issue226-product-setup-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue226-product-setup-bootstrap-v3' -ErrorAction Stop | Out-Null; 'ISSUE226_V1_EVIDENCE_ROOT_CREATED'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.setup_bootstrap",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue226-product-setup-bootstrap-v3/setup_bootstrap.py' --source 'F:/reverse-agent-issue226-product-setup-source-v1' --root 'F:/reverse-agent-issue226-product-setup-bootstrap-v3/runtime' --target 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --authority $a --planning '5739b63875b7cfda0d0cdc14113524959fdf5ec0'\"",
      "phase": "configuration",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.source_status_after",
      "command": "git -C F:/reverse-agent-issue226-product-setup-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue226v1.authority_status_final",
      "command": "git -C F:/reverse-agent-issue226-product-setup-executor-managed-r2-v1 status --short",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "frontend/src/schemas/model-access.ts"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "repository_product_mutation",
    "repository_test_mutation",
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
    "opencode_models",
    "opencode_run",
    "model_api_invocation",
    "provider_network_call",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
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
    "direct_push_main",
    "overwrite_existing_product_setup_target",
    "delete_existing_product_setup_target"
  ]
}
```

## Execution objective

Bootstrap exactly one sanitized `sensetime` external-session Connection and one `opencode` Binding into the real Product Setup target only after deterministic zero-model readiness is proven twice in fresh OS processes.

This round MUST NOT prove or inspect credential availability. Default trusted-host startup must leave the Connection at `external_session_status=executor_managed`; that is the expected success state, not a blocker.

The external harness may be written only at `F:/reverse-agent-issue226-product-setup-bootstrap-v3/setup_bootstrap.py` after transition authorization. It is outside Git and must not contain or inspect credentials.

### Harness requirements

The harness must:

1. Fail closed with exit 20 before mutation if the real Product Setup target exists.
2. Import reverse-agent only from the exact detached source worktree.
3. Use disposable TaskStore/runtime directories only; never open the real `tasks.sqlite3`.
4. Start a bootstrap `CombinedTrustedHost` with ephemeral ports and default `auth_list_probe=None`.
5. Use ordinary loopback Model Control PUT routes to create exactly the canonical Connection and Binding; never call `/test`.
6. GET and validate public Connection/Binding fields, including `secret_status=not_applicable` and `external_session_status=executor_managed`.
7. Stop the bootstrap host and validate the generated candidate bytes/document strictly: schema_version=1; root keys exactly `schema_version`, `connections`, `bindings`; exactly one expected Connection and Binding; no `api_key_env`, credential fields, `secret_status`, or `external_session_status` persisted.
8. Copy candidate bytes to two fresh disposable cycle directories. For each cycle, launch a separate fresh Python OS process whose import path is pinned to the exact source worktree. The child must construct a canonical `CombinedTrustedHost` from a disposable TaskStore in that cycle directory, leave `auth_list_probe` at its default `None`, start on ephemeral ports, GET the reloaded Connection/Binding, require `executor_managed`, then stop. No PUT reconstruction is allowed in cycle 1 or 2.
9. Persist only sanitized evidence under the authorized evidence root; no raw credential/config/auth-store content.
10. If both cycles pass, re-check target absence and install the exact candidate bytes using atomic create-if-absent / no-overwrite semantics. A target race is exit 20 and must not overwrite.
11. Re-read only the installed sanitized state and require exact byte equality to the validated candidate.
12. Emit exactly one terminal: `DOGFOOD1_EXECUTOR_MANAGED_PRODUCT_SETUP_BOOTSTRAP_ACCEPTED` on success or `DOGFOOD1_EXECUTOR_MANAGED_PRODUCT_SETUP_BOOTSTRAP_BLOCKED` on bounded failure.

## Required report

Report only sanitized evidence:
- canonical planning SHA;
- authority SHA;
- transition terminal and blockers;
- real target absent before bootstrap yes/no;
- bootstrap public Connection and Binding identities/status;
- candidate schema/counts and forbidden-field scan result;
- cycle 1 fresh OS process result/status;
- cycle 2 fresh OS process result/status;
- target absent immediately before install yes/no;
- no-overwrite install succeeded yes/no;
- installed candidate byte-equivalent yes/no;
- real TaskStore access NO;
- OpenCode invocation NO;
- auth-list probe NO;
- model/provider call NO;
- credential access NO;
- Connection /test NO;
- credential relay lease NO;
- Task /execute NO;
- repository product/test mutation NO;
- dependency install NO;
- PR/commit/push/merge NO;
- source worktree final status;
- authority worktree final status;
- terminal.

Success terminal:
`DOGFOOD1_EXECUTOR_MANAGED_PRODUCT_SETUP_BOOTSTRAP_ACCEPTED`

Blocked terminal:
`DOGFOOD1_EXECUTOR_MANAGED_PRODUCT_SETUP_BOOTSTRAP_BLOCKED`

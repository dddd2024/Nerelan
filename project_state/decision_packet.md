# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260817_issue227_opencode_executor_managed_gate_r2_v1",
  "round_id": "round_20260817_issue227_opencode_executor_managed_gate_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260817_issue226_product_setup_executor_managed_r2_v1",
  "follows_last_round_id": "round_20260817_issue226_product_setup_executor_managed_r2_v1",
  "previous_audit_outcome": "ISSUE226_EXECUTOR_MANAGED_PRODUCT_SETUP_BOOTSTRAP_ACCEPTED_AND_STALE_EXECUTOR_GATE_FOUND",
  "workstream_id": "issue227-opencode-executor-managed-gate-r2-v1",
  "source_issue": 227,
  "parent_issue": 148,
  "required_branch": "owner/issue227-opencode-executor-managed-gate-r2-v1",
  "starting_head": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "activation_base_sha": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "canonical_planning_sha": "5739b63875b7cfda0d0cdc14113524959fdf5ec0",
  "authority_worktree": "F:/reverse-agent-issue227-opencode-executor-managed-gate-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "worktree_creation_allowed": true,
  "branch_creation_allowed": true,
  "branch_creation_scope": "local_tracking_branch_owner/issue227-opencode-executor-managed-gate-r2-v1_only",
  "remote_branch_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "package_installation_allowed": false,
  "product_setup_mutation_allowed": false,
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
  "required_external_session_acceptance": ["executor_managed", "available"],
  "required_external_session_rejection": ["missing", "not_applicable", "unknown", ""],
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue227-opencode-executor-managed-gate-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue227-opencode-executor-managed-gate-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue227-opencode-executor-managed-gate-r2-v1);if($b){'ISSUE227_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue227-opencode-executor-managed-gate-r2-v1'){'ISSUE227_V1_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE227_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue227-opencode-executor-managed-gate-r2-v1 F:/reverse-agent-issue227-opencode-executor-managed-gate-r2-v1 origin/owner/issue227-opencode-executor-managed-gate-r2-v1",
    "Set-Location F:/reverse-agent-issue227-opencode-executor-managed-gate-r2-v1",
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
      "command_id": "issue227v1.status_before",
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
      "command_id": "issue227v1.python_focused_tests",
      "command": "python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py tests/platform_v1/test_task_execution.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue227v1.diff_check",
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
      "command_id": "issue227v1.changed_paths_before_commit",
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
      "command_id": "issue227v1.stage_exact_fix",
      "command": "git add reverse_agent/platform_v1/opencode_executor.py tests/platform_v1/test_opencode_executor.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_product_mutation", "repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue227v1.staged_paths",
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
      "command_id": "issue227v1.staged_diff_check",
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
      "command_id": "issue227v1.commit_fix",
      "command": "git commit -m \"Accept executor-managed OpenCode sessions\"",
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
      "command_id": "issue227v1.head_after_commit",
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
      "command_id": "issue227v1.compare_paths_after_commit",
      "command": "git diff --name-only 5739b63875b7cfda0d0cdc14113524959fdf5ec0..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue227v1.push_branch",
      "command": "git push origin owner/issue227-opencode-executor-managed-gate-r2-v1",
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
      "command_id": "issue227v1.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue227-opencode-executor-managed-gate-r2-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue227v1.status_final",
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_opencode_executor.py",
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
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/contracts.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_execution.py",
    "project_state/schemas/**"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/**",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/test_connection_binding.py",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "opencode_invocation",
    "opencode_auth_probe",
    "opencode_models",
    "opencode_run",
    "auth_login",
    "auth_logout",
    "model_api_invocation",
    "provider_network_call",
    "real_user_credential_file_discovery",
    "real_user_credential_file_read",
    "real_user_credential_value_read",
    "real_user_credential_value_print",
    "real_user_credential_value_hash",
    "real_user_credential_value_length_or_measurement",
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
    "bmad_installation_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue227-opencode-executor-managed-gate-r2-v1",
      "git push origin owner/issue227-opencode-executor-managed-gate-r2-v1"
    ],
    "loopback_model_control_http_allowed": false,
    "loopback_task_api_start_allowed": false,
    "loopback_credential_relay_server_start_allowed": false,
    "credential_relay_lease_allowed": false,
    "external_provider_network_allowed": false,
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  }
}
```

## Execution objective

Remove the stale duplicate executor-side external-session availability gate so a valid `executor_managed` Binding can reach the actual OpenCode invocation in the later Dogfood1, while preserving fail-closed rejection of invalid/missing external statuses.

### Exact required semantics

For `binding_resolution.auth_method in {"external_cli_session", "account_login"}`:

- accept `external_session_status == "executor_managed"`;
- accept `external_session_status == "available"`;
- reject every other status with `ExecutorRuntimeError("external_session_unavailable")`.

Do not change API-key relay semantics, provider/model normalization, child environment policy, prompt construction, worktree behavior, auth-list code, or any actual subprocess invocation behavior.

## Test requirements

In `tests/platform_v1/test_opencode_executor.py`, use only fake/in-memory resolution objects and existing deterministic fixtures. Add focused regressions proving:

1. external_cli_session + executor_managed constructs successfully;
2. external_cli_session + available remains successful;
3. account_login + executor_managed constructs successfully;
4. missing/not_applicable/unknown/empty external status rejects;
5. `ExecutorRouter.create_executor(executor_kind="opencode", binding_resolution=<executor_managed>)` succeeds and returns an OpenCode executor without launching it;
6. executor-managed `build_binding_config_content()` stays secret-free and keeps exact provider ID/base URL/model routing.

No test may call real OpenCode or access Product Setup/real TaskStore/credentials/network.

## Required report

Report:
- canonical planning SHA;
- authority SHA;
- transition terminal and blockers;
- exact changed paths;
- focused pytest pass/skip counts;
- executor_managed external_cli_session accepted YES/NO;
- available accepted YES/NO;
- executor_managed account_login accepted YES/NO;
- invalid/missing statuses rejected YES/NO;
- ExecutorRouter executor_managed construction accepted YES/NO;
- binding config exact provider/base/model and secret-free YES/NO;
- API-key behavior unchanged YES/NO;
- real OpenCode invocation NO;
- model/provider call NO;
- credential access NO;
- Product Setup mutation NO;
- Task execute NO;
- dependency installation NO;
- fix commit SHA;
- remote tracking SHA;
- final git status;
- terminal.

Success terminal:
`OPENCODE_EXECUTOR_MANAGED_GATE_FIX_READY_FOR_OWNER_AUDIT`

Blocked terminal:
`OPENCODE_EXECUTOR_MANAGED_GATE_FIX_BLOCKED`

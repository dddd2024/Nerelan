# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue218_issue216_validation_recovery_r2_v2",
  "round_id": "round_20260816_issue218_issue216_validation_recovery_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue218_issue216_validation_recovery_r2_v1",
  "follows_last_round_id": "round_20260816_issue218_issue216_validation_recovery_r2_v1",
  "previous_audit_outcome": "ISSUE216_REPAIR_V2_V1_BOUNDED_FAILURE_AUTHORITY_WORKTREE_GOVERNANCE_TEST_COUPLING",
  "workstream_id": "issue218-issue216-validation-recovery-r2-v2",
  "source_issue": 218,
  "parent_issue": 216,
  "required_branch": "owner/issue218-issue216-validation-recovery-r2-v2",
  "starting_head": "0054574b276bc9330dd4a6e1dc603415f3e8d50d",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "immutable_recovery_base_sha": "0054574b276bc9330dd4a6e1dc603415f3e8d50d",
  "supersedes_decision_id": "decision_20260816_issue218_issue216_validation_recovery_r2_v1",
  "superseded_branch_must_not_execute": "owner/issue218-issue216-validation-recovery-r2-v1",
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
  "model_api_invocation_allowed": false,
  "provider_network_call_allowed": false,
  "opencode_live_invocation_allowed": false,
  "credential_file_read_allowed": false,
  "credential_value_access_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "product_setup_mutation_allowed": false,
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
      "git push origin owner/issue218-issue216-validation-recovery-r2-v2"
    ],
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue218-issue216-validation-recovery-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue218-issue216-validation-recovery-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue218-issue216-validation-recovery-r2-v2);if($b){'ISSUE218_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue218-issue216-validation-recovery-r2-v2'){'ISSUE218_V2_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE218_V2_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue218-issue216-validation-recovery-r2-v2 F:/reverse-agent-issue218-issue216-validation-recovery-r2-v2 origin/owner/issue218-issue216-validation-recovery-r2-v2",
    "Set-Location F:/reverse-agent-issue218-issue216-validation-recovery-r2-v2",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD 09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue218v2.task3c_config_unit",
      "command": "python -m pytest tests/platform_v1/test_task3c_v5_opencode_probe.py::TestTransientProviderConfig -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.focused",
      "command": "python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.integration",
      "command": "python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.diff_check",
      "command": "git diff --check 0054574b276bc9330dd4a6e1dc603415f3e8d50d",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.path_list",
      "command": "git diff --name-only 0054574b276bc9330dd4a6e1dc603415f3e8d50d",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.status_precommit",
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
      "command_id": "issue218v2.stage",
      "command": "git add reverse_agent/platform_v1/opencode_executor.py tests/platform_v1/test_task3c_v5_opencode_probe.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue218v2.staged_scope",
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
      "command_id": "issue218v2.commit",
      "command": "git commit -m \"fix: require relay lease for api-key config\"",
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
      "command_id": "issue218v2.head",
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
      "command_id": "issue218v2.push",
      "command": "git push origin owner/issue218-issue216-validation-recovery-r2-v2",
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
      "command_id": "issue218v2.status_final",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py"
  ],
  "reference_paths": [
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py"
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
    "project_state/mainline_merge_intents/**",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "credential_value_read",
    "credential_value_print",
    "credential_value_hash",
    "credential_value_length_check",
    "credential_file_read",
    "credential_file_discovery",
    "auth_login",
    "auth_logout",
    "model_api_invocation",
    "provider_network_call",
    "opencode_live_invocation",
    "credential_relay_lease",
    "task_execute",
    "product_setup_mutation",
    "package_install",
    "pr_create",
    "merge",
    "direct_push_main",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "tag_or_release"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/gates/**",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py"
  ]
}
```

# Goal

Re-land only the already-audited two-file #218 repair on top of immutable product base `0054574b276bc9330dd4a6e1dc603415f3e8d50d`, without running governance-coupled or live-OpenCode full-suite tests in the Decision-bearing authority worktree.

## Required repair

1. `build_binding_config_content()` must fail closed with a stable bounded error such as `api_key_lease_required` when `resolution.auth_method == "api_key"` and no execution relay lease is supplied.
2. With an api-key lease, preserve `reverse-agent-relay`, lease relay URL, lease ID as `apiKey`, and provider-facing model derived from `lease.model_id`.
3. Non-api-key `external_cli_session`, `account_login`, and `none` keep the #216 actual-provider-ID configuration and contain no secret fields.
4. `TestTransientProviderConfig` in `tests/platform_v1/test_task3c_v5_opencode_probe.py` must use an explicit synthetic lease for api-key relay assertions and add a pure unit regression for the no-lease fail-closed error. Do not modify the live OpenCode probe classes.

## Validation separation

This V2 authority deliberately does NOT run the full Platform V1 suite. Only the pure Task3C config class, #216 focused tests, and existing integration tests are authorized here. After the implementation commit is pushed and Owner audits the exact two-file diff, Owner will reconstruct a new product-only candidate directly on canonical planning, excluding this Decision and all gate artifacts. The provider-free full suite will be run only against that detached product-only candidate, with no transition gates executed in that product worktree.

Success terminal:
`ISSUE216_REPAIR_V2_READY_FOR_OWNER_PRODUCT_ONLY_RECONSTRUCTION`

Failure terminal:
`ISSUE216_REPAIR_V2_BOUNDED_FAILURE`

# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue218_issue216_validation_recovery_r2_v1","round_id":"round_20260816_issue218_issue216_validation_recovery_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue217_issue216_product_validation_r2_v1",
  "follows_last_round_id": "round_20260816_issue217_issue216_product_validation_r2_v1",
  "previous_audit_outcome": "ISSUE216_PRODUCT_ONLY_VALIDATION_BOUNDED_FAILURE_OWNER_CLASSIFIED_TWO_BASELINE_GOVERNANCE_FAILURES_TWO_STALE_API_KEY_TEST_CONTRACT_FAILURES_AND_LIVE_OPENCODE_SUITE_OVERLAP",
  "workstream_id": "issue218-issue216-validation-recovery-r2-v1",
  "source_issue": 218,
  "parent_issue": 216,
  "required_branch": "owner/issue218-issue216-validation-recovery-r2-v1",
  "starting_head": "0054574b276bc9330dd4a6e1dc603415f3e8d50d",
  "activation_base_sha": "0054574b276bc9330dd4a6e1dc603415f3e8d50d",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "recovery_base_sha": "0054574b276bc9330dd4a6e1dc603415f3e8d50d",
  "recovery_base_branch": "owner/issue216-opencode-credential-reuse-product-only-v1",
  "accepted_v5_recovery_sha": "372ff4fa4c3ad2e690c996ee1dea037eae308a64",
  "supersedes_validation_authority_sha": "a044025a6aca0daca91293d3ed8f80041e453833",
  "recovery_commit_count": 1,
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-product-only-v1",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue218-issue216-validation-recovery-r2-v1",
      "git push origin owner/issue218-issue216-validation-recovery-r2-v1"
    ],
    "external_provider_network_allowed": false,
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue218-issue216-validation-recovery-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue218-issue216-validation-recovery-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue218-issue216-validation-recovery-r2-v1);if($b){'ISSUE218_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue218-issue216-validation-recovery-r2-v1'){'ISSUE218_V1_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE218_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue218-issue216-validation-recovery-r2-v1 F:/reverse-agent-issue218-issue216-validation-recovery-r2-v1 origin/owner/issue218-issue216-validation-recovery-r2-v1",
    "Set-Location F:/reverse-agent-issue218-issue216-validation-recovery-r2-v1",
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
    {"command_id":"issue218v1.unit_transient_config","command":"python -m pytest tests/platform_v1/test_task3c_v5_opencode_probe.py::TestTransientProviderConfig -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.focused_issue216","command":"python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.integration","command":"python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.provider_free_full","command":"python -m pytest tests/platform_v1 -q --ignore=tests/platform_v1/test_credential_relay.py --ignore=tests/platform_v1/test_task3c_v5_opencode_probe.py --ignore=tests/platform_v1/test_merge_intent.py","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.diff_check","command":"git diff --check 0054574b276bc9330dd4a6e1dc603415f3e8d50d","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.path_list","command":"git diff --name-only 0054574b276bc9330dd4a6e1dc603415f3e8d50d","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.status_precommit","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.stage","command":"git add reverse_agent/platform_v1/opencode_executor.py tests/platform_v1/test_task3c_v5_opencode_probe.py","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.staged_scope","command":"git diff --cached --name-only","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.commit","command":"git commit -m \"fix: fail closed on api-key config without relay lease\"","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["local_commit"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_only_after_validation":true},
    {"command_id":"issue218v1.head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue218v1.push","command":"git push origin owner/issue218-issue216-validation-recovery-r2-v1","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true},
    {"command_id":"issue218v1.status_final","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
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
    "reverse_agent/platform_v1/binding_resolver.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_credential_relay.py"
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
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_credential_relay.py",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "credential_value_read","credential_value_print","credential_value_hash","credential_value_length_check","credential_file_read","credential_file_discovery","auth_login","auth_logout","model_api_invocation","provider_network_call","opencode_live_invocation","opencode_auth_list_live_invocation","credential_relay_lease","task_execute","product_setup_mutation","package_install","pr_create","merge","direct_push_main","force_push","rebase","reset","clean","stash","amend","tag_or_release"
  ],
  "authorized_risk_tier":"R2",
  "authorized_risk_paths":["project_state/gates/**","reverse_agent/platform_v1/opencode_executor.py","tests/platform_v1/test_task3c_v5_opencode_probe.py"]
}
```

# Goal

Recover #216 after #217 bounded validation failure without weakening credential isolation or re-running live OpenCode probes.

## Required product contract

`build_binding_config_content()` has two mutually exclusive modes:

1. `auth_method == "api_key"`: a non-null execution relay lease is mandatory. If `lease is None`, fail closed with `ExecutorRuntimeError("api_key_lease_required")` (or the exact bounded error named by the implementation if kept stable in tests). With a lease, the config MUST remain keyed by `reverse-agent-relay`, MUST use `lease.relay_url`, MUST place only `lease.lease_id` into `options.apiKey`, and MUST derive the provider-facing model from `lease.model_id`. The provider master key must never enter child config.
2. non-api-key (`external_cli_session`, `account_login`, `none`): `lease` must remain absent; config provider key is the actual sanitized `resolution.provider_id`, baseURL is `resolution.base_url`, and no apiKey/token/cookie/credential material is added.

Do not alter resolver semantics, trusted-host auth refresh, persisted metadata, child env allowlist, credential relay manager, or Task execution.

## Required test repair

Only `TestTransientProviderConfig` in `tests/platform_v1/test_task3c_v5_opencode_probe.py` may be changed. Rebind the first two legacy relay-config assertions to an explicit synthetic `ExecutionLeaseHandle` so they test the real api-key runtime contract. Add a pure unit regression proving api-key resolution without a lease fails closed. Existing lease/baseURL/apiKey/master-secret assertions remain intact.

Do not alter the live `TestDirectFakeProviderControl` or `TestRelayFakeProviderRun` classes and DO NOT execute them in this round.

## Validation boundary

The provider-free full suite intentionally excludes three files for explicit, different reasons:

- `test_credential_relay.py`: independent #207 Windows socket lifecycle workstream;
- `test_task3c_v5_opencode_probe.py`: contains real `opencode run` live probe classes; its safe pure `TestTransientProviderConfig` class is run separately;
- `test_merge_intent.py`: current canonical planning carries a stale governance Decision lifecycle and the two #217 immutability failures are mathematically identical on planning and the direct-child product candidate because neither the Decision file nor this test changed.

No additional ignore is allowed. A failure outside those explicit exclusions is a bounded failure and must not be repaired in this round.

# Exit

Success terminal:
`ISSUE216_REPAIR_V2_READY_FOR_OWNER_PRODUCT_ONLY_VALIDATION`

Unexpected failure terminal:
`ISSUE216_REPAIR_V2_BOUNDED_FAILURE`

No PR, merge, product-only reconstruction, live OpenCode, provider/model call, Product Setup mutation, credential read, or scope expansion is authorized in this round.

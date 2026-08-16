# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue216_opencode_credential_reuse_r2_v2","round_id":"round_20260816_issue216_opencode_credential_reuse_r2_v2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue216_opencode_credential_reuse_probe_r2_v1",
  "follows_last_round_id": "round_20260816_issue216_opencode_credential_reuse_probe_r2_v1",
  "previous_audit_outcome": "OPENCODE_EXISTING_CREDENTIAL_REUSE_PROBE_READY_FOR_OWNER_AUDIT__PERSISTED_AUTH_VISIBLE_IN_BINDING_ENV",
  "workstream_id": "issue216-opencode-credential-reuse-r2-v2",
  "source_issue": 216,
  "parent_issue": 148,
  "required_branch": "owner/issue216-opencode-credential-reuse-r2-v2",
  "starting_head": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "phase_a_authority_sha": "e9999fdf3e58a63a418b17ffaf9ce967730a8e02",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "implementation_commit_count": 1,
  "product_only_full_suite_validation_deferred_to_owner_recovery_round": true,
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
  "canonical_external_provider_for_acceptance": "sensetime",
  "canonical_external_auth_type_for_acceptance": "api",
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-r2-v2",
      "git -C F:/reverse-agent-issue216-opencode-credential-reuse-r2-v2 push origin owner/issue216-opencode-credential-reuse-r2-v2"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue216-opencode-credential-reuse-r2-v2);if($b){'ISSUE216_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-opencode-credential-reuse-r2-v2'){'ISSUE216_V2_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE216_V2_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue216-opencode-credential-reuse-r2-v2 F:/reverse-agent-issue216-opencode-credential-reuse-r2-v2 origin/owner/issue216-opencode-credential-reuse-r2-v2",
    "Set-Location F:/reverse-agent-issue216-opencode-credential-reuse-r2-v2",
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
    {"command_id":"issue216v2.focused","command":"python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.integration","command":"python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.diff_check_worktree","command":"git diff --check 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.path_list_worktree","command":"git diff --name-only 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.status_precommit","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.stage","command":"git add reverse_agent/model_access/store.py reverse_agent/platform_v1/trusted_host.py reverse_agent/platform_v1/opencode_executor.py tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_product_mutation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.staged_scope","command":"git diff --cached --name-only","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.commit","command":"git commit -m \"fix: reuse persisted OpenCode provider auth\"","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["local_commit"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_only_after_validation":true},
    {"command_id":"issue216v2.head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.diff_check_head","command":"git diff --check 09ac6ea2fd6fdb46364252407dd73ec136f82ec9..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.path_list_head","command":"git diff --name-only 09ac6ea2fd6fdb46364252407dd73ec136f82ec9..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v2.push","command":"git push origin owner/issue216-opencode-credential-reuse-r2-v2","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true},
    {"command_id":"issue216v2.status_final","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
  ],
  "allowed_mutated_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_opencode_executor.py"
  ],
  "reference_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/binding_resolver.py",
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
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "credential_value_read","credential_value_print","credential_value_hash","credential_value_length_check","credential_file_read","credential_file_discovery","auth_login","auth_logout","model_api_invocation","provider_network_call","opencode_live_invocation","credential_relay_lease","task_execute","product_setup_mutation","package_install","pr_create","merge","direct_push_main","force_push","rebase","reset","clean","stash","amend","tag_or_release"
  ],
  "authorized_risk_tier":"R2",
  "authorized_risk_paths":["project_state/gates/**","reverse_agent/model_access/store.py","reverse_agent/platform_v1/trusted_host.py","reverse_agent/platform_v1/opencode_executor.py","tests/test_connection_binding.py","tests/platform_v1/test_trusted_host.py","tests/platform_v1/test_opencode_executor.py"]
}
```

# Goal

Reuse OpenCode's already-persisted provider credential without copying or persisting the raw credential in reverse-agent. For the accepted local provider `sensetime`, fresh trusted-host processes must independently re-establish external-session availability from sanitized `opencode auth list` provider metadata, and non-api-key Binding execution must bind OpenCode's inline provider configuration to the actual `Connection.provider` ID rather than the unrelated `reverse-agent-relay` ID.

# Required implementation semantics

## A. External-session status is fresh, in-memory truth

Add the smallest store API needed to refresh `external_session_status` for `external_cli_session` / `account_login` Connections from a set/mapping of sanitized authenticated provider IDs. The refresh MUST:
- match exact provider ID only; no fuzzy/display-name matching;
- set `available` only for exact authenticated provider IDs;
- set `missing` otherwise;
- leave `api_key` / `none` status `not_applicable`;
- never persist `external_session_status`;
- never receive credential values.

Persisted Product Setup remains sanitized schema v1 unless a product requirement proves a schema change is necessary. Do not add credential material or stale availability to the state file.

## B. Fresh trusted-host auth revalidation

Add a bounded, injectable OpenCode auth probe used by the production CombinedTrustedHost startup path only when at least one external-session Connection exists. It may execute only the local metadata command equivalent to `opencode auth list` / `opencode auth ls`. It MUST NOT read `auth.json` directly.

Probe requirements:
- use the installed OpenCode CLI;
- use the same restricted non-secret runtime/location environment shape needed by Binding children (`PATH`, `SystemRoot`, OpenCode safety-disable flags); do not copy arbitrary parent environment values;
- parse only sanitized provider identifier/auth-type metadata;
- accept provider IDs only when they already satisfy reverse-agent's safe identifier grammar; for this round `sensetime` with auth type `api` must be recognized;
- ignore display-name-only entries that cannot be deterministically mapped to a provider ID;
- discard command path/header/credential-file path and raw stdout after parsing;
- on CLI missing/nonzero/unparseable output, fail closed to no available external providers rather than failing host startup or inventing availability;
- make the probe injectable/fakeable so unit/integration tests do not execute real OpenCode.

On every fresh CombinedTrustedHost process startup, re-run the probe before serving Model Control / Task API and refresh in-memory status. A status proven `available` in one process MUST NOT survive a later process whose fresh probe returns no matching provider.

## C. Bind actual provider identity for non-api-key execution

Preserve the existing api-key relay path exactly: execution leases continue to use provider ID `reverse-agent-relay` and relay-scoped lease credentials.

For non-api-key Binding config (`external_cli_session`, `account_login`, `none`), `build_binding_config_content()` must use `resolution.provider_id` as the OpenCode provider key, not `reverse-agent-relay`. Keep the existing OpenAI-compatible adapter metadata and set only non-secret authority metadata: `baseURL` from the Connection and the exact provider-facing model. Do not include `apiKey`, token, Authorization, cookie, or credential material.

The CLI model selector must remain the exact `provider_id/model_id` already resolved by BindingResolver. This makes Connection provider/base/model authority and OpenCode credential lookup refer to the same provider identity.

## D. Required regressions

At minimum prove:
1. `sensetime` external-session provider becomes `available` after a fake sanitized auth-list probe reports `sensetime api`;
2. a fresh restart with the same persisted setup and the same probe remains available without persisting status;
3. a later restart whose probe omits `sensetime` returns `missing` (no stale carry-forward);
4. probe failure/nonzero/malformed output fails closed to `missing` and does not crash trusted-host startup;
5. display names such as `GitHub Copilot` are not guessed into provider IDs;
6. auth-list parsing never returns credential values or credential-file paths;
7. external-session Binding config uses provider key `sensetime`, baseURL from resolution, and model `sensenova-6.7-flash-lite`, with no secret-bearing field;
8. api-key Binding/relay config remains byte/semantic compatible with existing behavior;
9. existing BindingResolver external-session and api-key tests continue to pass;
10. persisted state still contains no `external_session_status` or raw credential field.

# Validation boundary

Do NOT run the repository-wide `tests/platform_v1` suite in this Decision-bearing authority worktree. Governance-sensitive tests can inspect the current Decision and would contaminate product validation. This round requires only the named focused/integration suites. After Owner audit, the Owner will construct or validate a product-only candidate against canonical planning and run the full provider-free suite there.

# Terminal

Success only after exact scope, required tests, one implementation commit and one normal push:

`ISSUE216_OPENCODE_CREDENTIAL_REUSE_ADAPTER_READY_FOR_OWNER_AUDIT`

Any unexpected product/test failure or scope violation:

`ISSUE216_OPENCODE_CREDENTIAL_REUSE_ADAPTER_BOUNDED_FAILURE`

Do not self-authorize a repair outside the same allowed paths and semantics. No live model/provider/OpenCode auth mutation is permitted in this round.

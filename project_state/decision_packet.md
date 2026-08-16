# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue216_opencode_credential_reuse_r2_v3","round_id":"round_20260816_issue216_opencode_credential_reuse_r2_v3","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue216_opencode_credential_reuse_r2_v2",
  "follows_last_round_id": "round_20260816_issue216_opencode_credential_reuse_r2_v2",
  "previous_audit_outcome": "ISSUE216_V2_SUPERSEDED_BEFORE_EXECUTION_NETWORK_EXCEPTION_COMMAND_MISMATCH",
  "workstream_id": "issue216-opencode-credential-reuse-r2-v3",
  "source_issue": 216,
  "parent_issue": 148,
  "required_branch": "owner/issue216-opencode-credential-reuse-r2-v3",
  "starting_head": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "phase_a_authority_sha": "e9999fdf3e58a63a418b17ffaf9ce967730a8e02",
  "supersedes_decision_id": "decision_20260816_issue216_opencode_credential_reuse_r2_v2",
  "superseded_branch_must_not_execute": "owner/issue216-opencode-credential-reuse-r2-v2",
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
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "local_network_exceptions": [
      "git push origin owner/issue216-opencode-credential-reuse-r2-v3"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-r2-v3",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-r2-v3",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue216-opencode-credential-reuse-r2-v3);if($b){'ISSUE216_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-opencode-credential-reuse-r2-v3'){'ISSUE216_V3_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE216_V3_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue216-opencode-credential-reuse-r2-v3 F:/reverse-agent-issue216-opencode-credential-reuse-r2-v3 origin/owner/issue216-opencode-credential-reuse-r2-v3",
    "Set-Location F:/reverse-agent-issue216-opencode-credential-reuse-r2-v3",
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
    {"command_id":"issue216v3.focused","command":"python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.integration","command":"python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.diff_check_worktree","command":"git diff --check 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.path_list_worktree","command":"git diff --name-only 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.status_precommit","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.stage","command":"git add reverse_agent/model_access/store.py reverse_agent/platform_v1/trusted_host.py reverse_agent/platform_v1/opencode_executor.py tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.staged_scope","command":"git diff --cached --name-only","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.commit","command":"git commit -m \"fix: reuse persisted OpenCode provider auth\"","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["local_commit"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_only_after_validation":true},
    {"command_id":"issue216v3.head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.diff_check_head","command":"git diff --check 09ac6ea2fd6fdb46364252407dd73ec136f82ec9..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.path_list_head","command":"git diff --name-only 09ac6ea2fd6fdb46364252407dd73ec136f82ec9..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v3.push","command":"git push origin owner/issue216-opencode-credential-reuse-r2-v3","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true},
    {"command_id":"issue216v3.status_final","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
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

Add the smallest store API needed to refresh `external_session_status` for `external_cli_session` / `account_login` Connections from sanitized authenticated provider IDs. Exact ID match only; `available` iff exact ID is present, otherwise `missing`; `api_key` and `none` remain `not_applicable`. Never persist `external_session_status` and never receive credential values.

## B. Fresh trusted-host auth revalidation

Add a bounded, injectable OpenCode auth probe used by production `CombinedTrustedHost` startup only when at least one external-session Connection exists. It may execute only local metadata command `opencode auth list` / `opencode auth ls`; it MUST NOT read `auth.json` directly.

Requirements:
- use installed OpenCode CLI;
- use restricted non-secret environment: explicit runtime/location keys required for launch (`PATH`, `SystemRoot`) plus existing OpenCode safety-disable flags; never iterate/copy arbitrary parent env;
- parse only sanitized provider identifier/auth-type metadata;
- accept provider IDs only when they satisfy reverse-agent safe identifier grammar; this round must recognize exact `sensetime` + `api`;
- ignore display-name-only entries such as `GitHub Copilot` rather than guessing an ID;
- do not persist command header, credential-file path or raw stdout;
- CLI missing/nonzero/unparseable output => empty authenticated-provider set, host still starts, external sessions become `missing`;
- probe must be injectable/fakeable so tests never execute real OpenCode.

Every fresh trusted-host process re-runs the probe before serving APIs. Availability from one process must not carry into a later process whose probe no longer reports the exact provider.

## C. Actual provider identity in non-api-key config

Preserve api-key relay behavior exactly: lease-backed execution still uses `reverse-agent-relay` and relay-scoped lease material.

For non-api-key Binding config (`external_cli_session`, `account_login`, `none`), `build_binding_config_content()` must use `resolution.provider_id` as the OpenCode provider key, with the existing `@ai-sdk/openai-compatible` adapter, `baseURL` from the Connection, and only the exact provider-facing model. No `apiKey`, token, Authorization, cookie or credential material. CLI selection remains the already-resolved exact `provider_id/model_id`.

## D. Required regressions

At minimum prove:
1. `sensetime` external session becomes `available` from fake sanitized auth metadata;
2. fresh restart with same persisted setup re-derives `available` without persisted status;
3. later restart with probe omitting `sensetime` returns `missing`;
4. probe missing/nonzero/malformed fails closed without host-start crash;
5. display label `GitHub Copilot` is not guessed to an ID;
6. parser output contains provider IDs/auth types only, not auth-file path/raw output;
7. external-session Binding config key is `sensetime`, baseURL is resolution baseURL, model is `sensenova-6.7-flash-lite`, and contains no secret field;
8. api-key relay config remains semantically unchanged;
9. existing BindingResolver external-session/api-key regressions pass;
10. persisted setup still excludes `external_session_status` and all raw credential fields.

# Validation boundary

Do NOT run the repository-wide `tests/platform_v1` suite in this Decision-bearing authority worktree. Governance-sensitive tests can inspect the active Decision. Run only the named focused and integration suites. After Owner audit, product-only validation against canonical planning will run the full provider-free suite.

# Terminal

Success after exact scope, required tests, exactly one implementation commit after this authority commit, and one normal push:

`ISSUE216_OPENCODE_CREDENTIAL_REUSE_ADAPTER_READY_FOR_OWNER_AUDIT`

Unexpected failure or scope violation:

`ISSUE216_OPENCODE_CREDENTIAL_REUSE_ADAPTER_BOUNDED_FAILURE`

No live model/provider call, no live OpenCode auth mutation, no Product Setup mutation, no raw credential access.

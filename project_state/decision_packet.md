# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue216_opencode_credential_reuse_r2_v4","round_id":"round_20260816_issue216_opencode_credential_reuse_r2_v4","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue216_opencode_credential_reuse_r2_v3",
  "follows_last_round_id": "round_20260816_issue216_opencode_credential_reuse_r2_v3",
  "previous_audit_outcome": "ISSUE216_V3_OWNER_AUDIT_REJECTED_AUTH_PROBE_FAIL_CLOSED_AND_REAL_OUTPUT_PARSER_DEFECTS",
  "workstream_id": "issue216-opencode-credential-reuse-r2-v4",
  "source_issue": 216,
  "parent_issue": 148,
  "required_branch": "owner/issue216-opencode-credential-reuse-r2-v4",
  "starting_head": "239eb27211b71176119f0cad3b0952fc92e544eb",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "rejected_v3_implementation_sha": "239eb27211b71176119f0cad3b0952fc92e544eb",
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
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "local_network_exceptions": [
      "git push origin owner/issue216-opencode-credential-reuse-r2-v4"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-r2-v4",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-r2-v4",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue216-opencode-credential-reuse-r2-v4);if($b){'ISSUE216_V4_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-opencode-credential-reuse-r2-v4'){'ISSUE216_V4_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE216_V4_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue216-opencode-credential-reuse-r2-v4 F:/reverse-agent-issue216-opencode-credential-reuse-r2-v4 origin/owner/issue216-opencode-credential-reuse-r2-v4",
    "Set-Location F:/reverse-agent-issue216-opencode-credential-reuse-r2-v4",
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
    {"command_id":"issue216v4.focused","command":"python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_binding_resolver.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.integration","command":"python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.diff_check","command":"git diff --check 239eb27211b71176119f0cad3b0952fc92e544eb","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.path_list","command":"git diff --name-only 239eb27211b71176119f0cad3b0952fc92e544eb","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.status_precommit","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.stage","command":"git add reverse_agent/platform_v1/trusted_host.py reverse_agent/platform_v1/opencode_executor.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_opencode_executor.py","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.staged_scope","command":"git diff --cached --name-only","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.commit","command":"git commit -m \"fix: harden OpenCode auth probe\"","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["local_commit"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_only_after_validation":true},
    {"command_id":"issue216v4.head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v4.push","command":"git push origin owner/issue216-opencode-credential-reuse-r2-v4","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true},
    {"command_id":"issue216v4.status_final","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
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
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "tests/test_connection_binding.py",
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
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/test_connection_binding.py",
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

Repair only the two Owner-audited defects in implementation `239eb27211b71176119f0cad3b0952fc92e544eb` before any product-only landing.

## Blocking defect 1 — empty/failed probe must revoke availability

`CombinedTrustedHost._refresh_external_session_auth()` must refresh external-session status even when the sanitized probe returns an empty mapping or raises. If any external-session Connection exists, every startup refresh attempt ends with exactly one store refresh using the observed sanitized provider mapping; probe missing/exception/nonzero/unparseable becomes `{}` and therefore exact external-session Connections become `missing`. An earlier in-memory `available` value must never survive a later failed/empty probe.

Required regression: begin with a store whose `sensetime` external session is already `available`, inject an empty-returning probe and separately a raising probe, call the production refresh/start path, and prove public status becomes `missing` while host startup remains bounded.

## Blocking defect 2 — parse the real OpenCode CLI list shape

The installed OpenCode Phase A probe proved the default `opencode auth list` command exposes human-readable terminal rows including exact `sensetime` with auth type `api`, plus a display-name entry `GitHub Copilot` with `oauth`. OpenCode's CLI contract does not provide a JSON-output flag for `auth list`; therefore production parsing must not depend on `json.loads(stdout)` succeeding.

Update `parse_opencode_auth_list()` to support the actual text-list shape produced by `opencode auth list`/`auth ls`. It may retain backwards-compatible JSON parsing, but text parsing is required. The text parser must:
- ignore headers, credential-file paths, totals, tree/bullet glyphs and unrelated lines;
- strip terminal decoration/ANSI safely if needed;
- interpret an authenticated credential row only when its final token is an allowed auth type and the preceding provider label itself is one exact safe provider identifier;
- accept `sensetime api` -> `{\"sensetime\": \"api\"}`;
- reject display labels containing spaces such as `GitHub Copilot oauth` rather than guessing `github-copilot`;
- never return raw stdout, credential paths, key/token fragments or arbitrary labels;
- malformed/unrecognized output -> empty mapping.

Tests must use fake captured output shaped like the Phase A/real CLI output, not an invented JSON-only contract. No real OpenCode invocation is allowed in V4.

# Preserved accepted V3 behavior

Do not redesign the accepted portions of `239eb272...`: exact provider `sensetime` mapping, non-api-key provider config keyed by `resolution.provider_id`, api-key relay path using `reverse-agent-relay`, restricted child environment, sanitized state persistence, and zero raw credential exposure remain unchanged.

# Exit

Success terminal:
`ISSUE216_V4_AUTH_PROBE_RECOVERY_READY_FOR_OWNER_AUDIT`

Unexpected failure terminal:
`ISSUE216_V4_AUTH_PROBE_RECOVERY_BOUNDED_FAILURE`

No PR, merge, product-only candidate, live OpenCode, provider/model call, Product Setup mutation, credential read, or scope expansion is authorized in this round.

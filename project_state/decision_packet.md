# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue216_opencode_credential_reuse_probe_r2_v1","round_id":"round_20260816_issue216_opencode_credential_reuse_probe_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v3",
  "follows_last_round_id": "round_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v3",
  "previous_audit_outcome": "ISSUE215_ENV_ONLY_STRATEGY_SUPERSEDED_BY_EXISTING_OPENCODE_CREDENTIAL_REUSE",
  "workstream_id": "issue216-opencode-credential-reuse-probe-r2-v1",
  "source_issue": 216,
  "parent_issue": 148,
  "required_branch": "owner/issue216-opencode-credential-reuse-probe-r2-v1",
  "starting_head": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
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
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "external_harness_write_path": "F:/reverse-agent-issue216-opencode-credential-probe-v1/credential_probe.py",
  "credential_boundary": {
    "agent_or_harness_direct_credential_file_read_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "agent_or_harness_credential_value_print_allowed": false,
    "opencode_auth_list_internal_credential_store_read_allowed": true,
    "opencode_auth_mutation_allowed": false,
    "provider_or_model_request_allowed": false
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": true,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-probe-r2-v1"
    ],
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue216-opencode-credential-reuse-probe-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue216-opencode-credential-reuse-probe-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue216-opencode-credential-reuse-probe-r2-v1);if($b){'ISSUE216_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-opencode-credential-reuse-probe-r2-v1'){'ISSUE216_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-probe-source-v1'){'ISSUE216_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue216-opencode-credential-probe-v1'){'ISSUE216_V1_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE216_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue216-opencode-credential-reuse-probe-r2-v1 F:/reverse-agent-issue216-opencode-credential-reuse-probe-r2-v1 origin/owner/issue216-opencode-credential-reuse-probe-r2-v1",
    "Set-Location F:/reverse-agent-issue216-opencode-credential-reuse-probe-r2-v1",
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
    {"command_id":"issue216v1.source_worktree_create","command":"git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue216-probe-source-v1 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"setup","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["worktree_create"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.source_head","command":"git -C F:/reverse-agent-issue216-probe-source-v1 rev-parse HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.source_status_before","command":"git -C F:/reverse-agent-issue216-probe-source-v1 status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.opencode_version","command":"powershell -NoProfile -Command \"opencode --version\"","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.evidence_root_create","command":"powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue216-opencode-credential-probe-v1' -ErrorAction Stop | Out-Null; 'ISSUE216_V1_EVIDENCE_ROOT_CREATED'\"","phase":"setup","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.credential_probe","command":"python F:/reverse-agent-issue216-opencode-credential-probe-v1/credential_probe.py","phase":"probe","required":true,"expected_exit_codes":[0,20],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.source_status_after","command":"git -C F:/reverse-agent-issue216-probe-source-v1 status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue216v1.authority_status_final","command":"git -C F:/reverse-agent-issue216-opencode-credential-reuse-probe-r2-v1 status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
  ],
  "allowed_mutated_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/model_access/store.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_binding_resolver.py"
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
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml"
  ],
  "forbidden_operations": [
    "repository_product_mutation",
    "repository_test_mutation",
    "credential_file_direct_read",
    "credential_value_read",
    "credential_value_print",
    "credential_value_hash",
    "credential_value_length_check",
    "credential_value_copy_or_export",
    "opencode_auth_login",
    "opencode_auth_logout",
    "opencode_run",
    "opencode_models",
    "provider_network_call",
    "model_api_invocation",
    "connection_or_binding_mutation",
    "credential_relay_lease",
    "task_execute",
    "local_commit",
    "push",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "dependency_install"
  ],
  "authorized_risk_tier":"R2",
  "authorized_risk_paths":["project_state/gates/**"]
}
```

# Goal

Prove whether the already-working OpenCode persisted credential is visible under both normal OpenCode execution context and the exact restricted environment shape currently used by reverse-agent Binding children, without reading credential files directly and without any model/provider request.

# Probe contract

The only external script permitted is `F:/reverse-agent-issue216-opencode-credential-probe-v1/credential_probe.py`, created only after `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`, and evidence-root creation.

The script may invoke only `opencode auth list` (or `opencode auth ls` as fallback) and may record only sanitized provider identity/name, auth type, exit code, and whether the same provider row is visible in the restricted environment. It must not read `auth.json` or any credential file itself.

Normal probe: invoke OpenCode with inherited process environment and the fixed OpenCode disable flags set by the child process invocation without materializing/copying the parent's environment mapping.

Restricted probe: construct an explicit child environment using only `PATH`, `SystemRoot`, and these fixed flags: `OPENCODE_DISABLE_AUTOUPDATE=true`, `OPENCODE_DISABLE_MODELS_FETCH=true`, `OPENCODE_DISABLE_LSP_DOWNLOAD=true`, `OPENCODE_DISABLE_DEFAULT_PLUGINS=true`, `OPENCODE_DISABLE_CLAUDE_CODE=true`. Do not include arbitrary parent environment variables.

No `/models`, `opencode run`, provider connection test, task execution or external network is allowed.

# Classification

Success does not require the restricted environment to work. Phase A succeeds when it produces exact non-secret evidence and one of:

- `OPENCODE_PERSISTED_AUTH_VISIBLE_IN_BINDING_ENV`
- `OPENCODE_PERSISTED_AUTH_HIDDEN_BY_BINDING_ENV`
- `OPENCODE_SENSENOVA_PROVIDER_ID_NOT_IDENTIFIABLE`
- `OPENCODE_AUTH_LIST_UNAVAILABLE`

Terminal on successful bounded observation:

`OPENCODE_EXISTING_CREDENTIAL_REUSE_PROBE_READY_FOR_OWNER_AUDIT`

Exit 20 is reserved for a bounded inability to identify/observe the credential without violating the secret boundary; it is not permission to inspect credential files.

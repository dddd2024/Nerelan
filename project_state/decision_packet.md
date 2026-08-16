# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v2","round_id":"round_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v1",
  "follows_last_round_id": "round_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v1",
  "previous_audit_outcome": "ISSUE215_V1_SUPERSEDED_BEFORE_EXECUTION_CREDENTIAL_SCOPE_AMBIGUITY",
  "workstream_id": "issue215-dogfood1-product-setup-bootstrap-r2-v2",
  "source_issue": 215,
  "parent_issue": 148,
  "required_branch": "owner/issue215-dogfood1-product-setup-bootstrap-r2-v2",
  "starting_head": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "activation_base_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "canonical_planning_sha": "09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "supersedes_decision_id": "decision_20260816_issue215_dogfood1_product_setup_bootstrap_r2_v1",
  "superseded_branch_must_not_execute": "owner/issue215-dogfood1-product-setup-bootstrap-r2-v1",
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
  "external_harness_write_path": "F:/reverse-agent-issue215-product-setup-bootstrap-v2/setup_bootstrap.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue215-product-setup-bootstrap-v2/**",
    "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json"
  ],
  "product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "product_setup_target_must_be_absent_before_install": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "canonical_setup": {
    "connection_id": "sensenova-67-flash-lite",
    "connection_name": "SenseNova 6.7 Flash-Lite",
    "provider": "openai-compatible",
    "base_url": "https://token.sensenova.cn/v1",
    "auth_method": "api_key",
    "api_key_env": "SENSENOVA_API_KEY",
    "binding_id": "opencode-sensenova-67-flash-lite",
    "binding_name": "OpenCode SenseNova 6.7 Flash-Lite",
    "executor_id": "opencode",
    "model_id": "sensenova-6.7-flash-lite",
    "enabled": true
  },
  "credential_boundary": {
    "agent_or_harness_credential_value_access_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "agent_or_harness_environment_name_presence_check_allowed": ["SENSENOVA_API_KEY"],
    "agent_or_harness_environment_value_read_allowed": false,
    "agent_or_harness_environment_value_print_allowed": false,
    "agent_or_harness_environment_value_hash_allowed": false,
    "agent_or_harness_environment_value_length_check_allowed": false,
    "agent_or_harness_environment_value_copy_or_export_allowed": false,
    "trusted_host_internal_env_backed_secret_resolution_allowed": true,
    "trusted_host_secret_output_allowed": false,
    "trusted_host_provider_use_allowed": false,
    "trusted_host_credential_relay_lease_allowed": false,
    "raw_credential_persistence_allowed": false
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
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue215-dogfood1-product-setup-bootstrap-r2-v2"
    ],
    "loopback_model_control_http_allowed": true,
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue215-dogfood1-product-setup-bootstrap-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue215-dogfood1-product-setup-bootstrap-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue215-dogfood1-product-setup-bootstrap-r2-v2);if($b){'ISSUE215_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue215-dogfood1-product-setup-bootstrap-r2-v2'){'ISSUE215_V2_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue215-bootstrap-source-v2'){'ISSUE215_V2_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue215-product-setup-bootstrap-v2'){'ISSUE215_V2_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE215_V2_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue215-dogfood1-product-setup-bootstrap-r2-v2 F:/reverse-agent-issue215-dogfood1-product-setup-bootstrap-r2-v2 origin/owner/issue215-dogfood1-product-setup-bootstrap-r2-v2",
    "Set-Location F:/reverse-agent-issue215-dogfood1-product-setup-bootstrap-r2-v2",
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
    {"command_id":"issue215v2.source_worktree_create","command":"git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue215-bootstrap-source-v2 09ac6ea2fd6fdb46364252407dd73ec136f82ec9","phase":"setup","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["worktree_create"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.source_head","command":"git -C F:/reverse-agent-issue215-bootstrap-source-v2 rev-parse HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.source_status_before","command":"git -C F:/reverse-agent-issue215-bootstrap-source-v2 status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.evidence_root_create","command":"powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue215-product-setup-bootstrap-v2' -ErrorAction Stop | Out-Null; 'ISSUE215_V2_EVIDENCE_ROOT_CREATED'\"","phase":"setup","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.setup_bootstrap","command":"powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue215-dogfood1-product-setup-bootstrap-r2-v2' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue215-product-setup-bootstrap-v2/setup_bootstrap.py' --source 'F:/reverse-agent-issue215-bootstrap-source-v2' --root 'F:/reverse-agent-issue215-product-setup-bootstrap-v2/runtime' --target 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --authority $a --planning '09ac6ea2fd6fdb46364252407dd73ec136f82ec9'\"","phase":"configuration","required":true,"expected_exit_codes":[0,20],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.source_status_after","command":"git -C F:/reverse-agent-issue215-bootstrap-source-v2 status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"issue215v2.authority_status_final","command":"git -C F:/reverse-agent-issue215-dogfood1-product-setup-bootstrap-r2-v2 status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"}
  ],
  "allowed_mutated_paths": [
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
    "reverse_agent/platform_v1/opencode_executor.py"
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
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "repository_product_mutation",
    "repository_test_mutation",
    "governance_mutation_outside_generated_gates",
    "agent_or_harness_credential_value_read",
    "agent_or_harness_credential_value_print",
    "agent_or_harness_credential_value_hash",
    "agent_or_harness_credential_value_length_check",
    "agent_or_harness_credential_value_copy_or_export",
    "agent_or_harness_credential_file_discovery",
    "session_api_key_configuration",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
    "model_api_invocation",
    "provider_network_call",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
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
    "tag_or_release",
    "overwrite_existing_product_setup_state",
    "real_task_store_mutation",
    "dependency_install"
  ],
  "authorized_risk_tier":"R2",
  "authorized_risk_paths":["project_state/gates/**"]
}
```

# Goal

Create exactly one restart-safe, environment-backed sanitized Product Setup record for SenseNova 6.7 Flash-Lite and prove that the resulting Connection/Binding survives two fresh trusted-host OS process cycles without Agent/harness access to the raw API key, without touching the real TaskStore, and without any model/provider request.

# Why v2 supersedes v1

V1 used an over-broad `credential_value_access_allowed=false` phrase while also requiring the trusted host to report `secret_status=environment`. Current trusted-host store semantics internally resolve an env-backed secret to derive/use trusted status. V2 scopes the prohibition correctly: the Agent/harness never receives or reads the value; the trusted host may perform its existing internal env-backed resolution, but may not output the secret, mint a credential lease, or make any provider request in this round.

# External harness rule

`F:/reverse-agent-issue215-product-setup-bootstrap-v2/setup_bootstrap.py` is the only external script permitted. It may be created only after transition preflight is `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`, and `issue215v2.evidence_root_create` succeeds. It must not be added to Git.

The script may test only membership of the literal environment key `SENSENOVA_API_KEY` (for example, `"SENSENOVA_API_KEY" in os.environ`). It must never retrieve that mapping value. Child trusted-host processes must inherit the environment implicitly; do not construct an `env` mapping by copying environment values.

# Configuration protocol

If `SENSENOVA_API_KEY` is absent, write a sanitized summary and exit 20 with blocker `SENSENOVA_API_KEY_ENV_NOT_PRESENT`; do not start a host or mutate Product Setup.

If present, use a disposable runtime and normal loopback Model Control PUT endpoints to create exactly:

Connection `sensenova-67-flash-lite`:
- name `SenseNova 6.7 Flash-Lite`
- provider `openai-compatible`
- base_url `https://token.sensenova.cn/v1`
- auth_method `api_key`
- api_key_env `SENSENOVA_API_KEY`
- enabled true

Binding `opencode-sensenova-67-flash-lite`:
- name `OpenCode SenseNova 6.7 Flash-Lite`
- executor_id `opencode`
- connection_id `sensenova-67-flash-lite`
- model_id `sensenova-6.7-flash-lite`
- enabled true

Do not call the Connection `/test` endpoint. Public GET must report the Connection with `secret_status=environment` while not revealing `api_key_env` or any raw credential.

After the disposable host is stopped, strictly validate the generated schema-v1 state. It must contain only the exact sanitized Connection/Binding and no forbidden credential-bearing field. Install those validated bytes into `F:/reverse-agent/.platform_v1_runtime/model_setup_state.json` only if that target is still absent. On Windows use a same-directory flushed/fsynced temporary file followed by a non-overwriting rename; if the target appears before rename, preserve it and exit 20 with `PRODUCT_SETUP_TARGET_BECAME_PRESENT`.

Never open, copy or modify `F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3`.

# Restart proof

After successful install, copy only the sanitized state bytes into a fresh disposable restart runtime. Start fresh trusted-host OS process cycle 1 and cycle 2 against that disposable TaskStore runtime using exact planning SHA and current authority HEAD. Between cycles stop only the exact child PID and require loopback ports to be released. Do not recreate Connection/Binding between cycles.

For both cycles require:
- exact trusted_host_meta authority/planning identities;
- GET Connection identity exact;
- GET Binding identity exact;
- GET executor `opencode` operational true;
- public Connection `secret_status=environment`;
- no public `api_key_env` field;
- no raw secret field/value in persisted state or public responses;
- no Task execute, credential lease, live probe, model/provider call or external network request.

If ports 8765/8766 are occupied by an unrelated process, do not kill it; exit 20 with `LOCAL_PRODUCT_PORT_OCCUPIED`.

# Acceptance

Success terminal:

`DOGFOOD1_PRODUCT_SETUP_BOOTSTRAP_AND_READINESS_ACCEPTED`

Bounded blocked terminal:

`DOGFOOD1_PRODUCT_SETUP_BOOTSTRAP_BLOCKED`

Exit 20 is a bounded blocked outcome only, never success. Any unexpected invariant failure uses a distinct nonzero/non-20 exit and terminal `DOGFOOD1_PRODUCT_SETUP_BOOTSTRAP_FAILURE`.

No repository commit/push/PR/merge is permitted in this round.

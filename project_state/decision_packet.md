# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue213_dogfood1_zero_model_readiness_r2_v1",
  "round_id": "round_20260816_issue213_dogfood1_zero_model_readiness_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue211_issue210_product_validation_r2_v1",
  "follows_last_round_id": "round_20260816_issue211_issue210_product_validation_r2_v1",
  "previous_audit_outcome": "ISSUE210_PRODUCT_ONLY_VALIDATION_ACCEPTED_AND_PR212_LANDED",
  "workstream_id": "issue213-dogfood1-zero-model-readiness-r2-v1",
  "source_issue": 213,
  "parent_issue": 148,
  "required_branch": "owner/issue213-dogfood1-zero-model-readiness-r2-v1",
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue213-dogfood1-zero-model-readiness-r2-v1"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue213-dogfood1-zero-model-readiness-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue213-dogfood1-zero-model-readiness-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue213-dogfood1-zero-model-readiness-r2-v1);if($b){'ISSUE213_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue213-dogfood1-zero-model-readiness-r2-v1'){'ISSUE213_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue213-readiness-source-v1'){'ISSUE213_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue213-dogfood-readiness-v1'){'ISSUE213_V1_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE213_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue213-dogfood1-zero-model-readiness-r2-v1 F:/reverse-agent-issue213-dogfood1-zero-model-readiness-r2-v1 origin/owner/issue213-dogfood1-zero-model-readiness-r2-v1",
    "Set-Location F:/reverse-agent-issue213-dogfood1-zero-model-readiness-r2-v1",
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
      "command_id": "issue213v1.source_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue213-readiness-source-v1 09ac6ea2fd6fdb46364252407dd73ec136f82ec9",
      "phase": "readiness_setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.source_head",
      "command": "git -C F:/reverse-agent-issue213-readiness-source-v1 rev-parse HEAD",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.source_status_before",
      "command": "git -C F:/reverse-agent-issue213-readiness-source-v1 status --short",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.python_version",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue213-readiness-source-v1'; python --version\"",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.opencode_version",
      "command": "powershell -NoProfile -Command \"$c=Get-Command opencode -ErrorAction Stop; Write-Output ('OPENCODE_PATH=' + $c.Source); & $c.Source --version\"",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.readiness_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue213-dogfood-readiness-v1' -ErrorAction Stop | Out-Null; 'ISSUE213_V1_READINESS_ROOT_CREATED'\"",
      "phase": "readiness_setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.readiness_probe",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue213-dogfood1-zero-model-readiness-r2-v1' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue213-dogfood-readiness-v1/readiness_probe.py' --source 'F:/reverse-agent-issue213-readiness-source-v1' --state-file 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --root 'F:/reverse-agent-issue213-dogfood-readiness-v1/runtime' --authority $a --planning '09ac6ea2fd6fdb46364252407dd73ec136f82ec9'\"",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.source_status_after",
      "command": "git -C F:/reverse-agent-issue213-readiness-source-v1 status --short",
      "phase": "readiness",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue213v1.authority_status_final",
      "command": "git -C F:/reverse-agent-issue213-dogfood1-zero-model-readiness-r2-v1 status --short",
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
  "reference_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "dev-up.ps1",
    "dev-down.ps1"
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
    "product_mutation",
    "test_mutation",
    "governance_mutation_outside_generated_gates",
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
    "task_execute",
    "credential_lease_create",
    "credential_value_read",
    "credential_value_print",
    "credential_value_hash",
    "credential_value_length_check",
    "credential_value_export",
    "model_api_invocation",
    "opencode_task_invocation",
    "codex_invocation",
    "openhands_invocation",
    "real_provider_call",
    "provider_probe",
    "external_network_request",
    "dependency_install",
    "connection_create",
    "connection_update",
    "connection_delete",
    "binding_create",
    "binding_update",
    "binding_delete"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/gates/**"
  ],
  "runner_managed_artifact_paths": []
}
```

# Goal

Determine whether the local machine already has one concrete restart-safe Binding/authentication path suitable for the narrow Long-running Unattended Dogfood 1, without making any model/provider request and without mutating Product Setup.

# Separation and local-state rule

The authority worktree exists only for transition-gate authorization and generated gate evidence. The detached source worktree is exact canonical planning and must remain clean. Runtime evidence and the readiness harness live outside Git under `F:/reverse-agent-issue213-dogfood-readiness-v1`.

The only existing Product Setup state authorized for inspection in this round is:

`F:/reverse-agent/.platform_v1_runtime/model_setup_state.json`

The probe may read that file because #210 guarantees it is sanitized Product Setup metadata. It may copy the exact bytes into the disposable readiness runtime. It MUST NOT mutate the original state file or original task DB.

# External harness creation authorization

Only after bootstrap succeeds, transition-preflight returns `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, and `issue213v1.readiness_root_create` succeeds, editor/file-write is authorized to create exactly one executable/script file:

`F:/reverse-agent-issue213-dogfood-readiness-v1/readiness_probe.py`

The script is outside the repository, is never staged/committed/pushed, and no other script/executable may be created. Do not generate it through an unlisted shell command.

# readiness_probe.py mandatory semantics

1. Read only the authorized source state file. If it is absent, persist a summary with blocker `PRODUCT_SETUP_STATE_ABSENT`, print `LONG_RUNNING_DOGFOOD1_ZERO_MODEL_READINESS_BLOCKED`, and exit 20.
2. Validate JSON root object, `schema_version == 1`, `connections`/`bindings` arrays, and reject unknown/credential-bearing fields. Never print the raw document.
3. Recursively reject raw credential-bearing field names including at least `api_key`, `authorization`, `bearer`, `token`, `password`, `secret`, `cookie`, `account_token`, `session_credential`, `private_key`, `external_session_status`, and `secret_status` as persisted authority fields.
4. For each `api_key` Connection, inspect only the persisted `api_key_env` variable NAME. Determine availability using key-membership semantics only (for example `env_name in os.environ`). The harness MUST NOT retrieve, print, hash, compare, measure, export, or serialize the environment variable value.
5. A v1 qualifying candidate must be: Connection enabled; Binding enabled; executor `opencode`; auth method `api_key`; nonempty persisted `api_key_env`; referenced environment variable present in the current/fresh child environment. Session-only API keys do not qualify. `external_cli_session`, `account_login`, and `none` do not qualify in v1 because this zero-provider round cannot independently prove their restart-safe credential truth.
6. If no candidate qualifies, persist sanitized reasons per Binding/Connection, print `LONG_RUNNING_DOGFOOD1_ZERO_MODEL_READINESS_BLOCKED`, and exit 20. Do not create or update Product Setup.
7. If one or more candidates qualify, copy only the validated sanitized state JSON to a fresh disposable runtime under the readiness root. Do not copy the original tasks DB.
8. Before host start, require loopback ports 8765 and 8766 are free. If occupied, report `LOCAL_PRODUCT_PORT_OCCUPIED` as a bounded readiness blocker; do not kill or interfere with the owning process.
9. Start a fresh child OS process from exact source `09ac6ea2...` using `python -m reverse_agent.platform_v1.trusted_host` with environment variables: `REVERSE_AGENT_TASK_DB_DIR=<disposable runtime>`, `REVERSE_AGENT_EXECUTION_AUTHORITY_SHA=<authority argument>`, `REVERSE_AGENT_PLANNING_SHA=09ac6ea2...`. Do not add provider/model credentials; the child inherits the existing process environment naturally.
10. Wait boundedly for canonical `trusted_host_meta.json`, then require its `execution_authority_sha` equals the supplied authority SHA and `planning_sha` equals `09ac6ea2...`.
11. Perform loopback GET only against normal Model Control/Task endpoints: Connections, Bindings, Executors, Tasks. Never call a PUT/POST/DELETE route, Task execute route, connection test/probe route, or credential relay endpoint.
12. Require each selected candidate is visible through the public API, the executor is operational, and the selected Connection reports `secret_status=environment`. Do not expose any credential value.
13. Stop the first child process boundedly without killing unrelated processes. Wait until 8765/8766 are free.
14. Start a second fresh child OS process against the exact same disposable runtime and repeat identity + GET checks. This proves persisted metadata survives a real host process restart without harness reconstruction.
15. Stop the second child boundedly. Verify the copied sanitized state bytes are unchanged, the original source state bytes are unchanged, and no original TaskStore was opened or mutated.
16. Persist external `summary.json` containing only sanitized: source state path; schema version; candidate Binding/Connection/model/provider/base URL/auth method; `api_key_env` NAME; env-present boolean; source/authority/planning SHAs; OpenCode/Python version evidence supplied by commands; both child PIDs/exit codes; both trusted-host metadata identities; public GET status summaries; restart candidate identity equality; zero model/provider/task-execute/lease/network-external counters; blocker or accepted terminal. Never persist environment values or raw response fields outside the documented public sanitized fields.

# Acceptance

Success terminal:

`LONG_RUNNING_DOGFOOD1_ZERO_MODEL_READINESS_ACCEPTED`

Blocked terminal:

`LONG_RUNNING_DOGFOOD1_ZERO_MODEL_READINESS_BLOCKED`

Exit 20 is an expected bounded blocked outcome, not permission to repair. Any unanticipated harness/runtime invariant failure must use a non-0/non-20 exit and terminal `LONG_RUNNING_DOGFOOD1_ZERO_MODEL_READINESS_FAILURE`.

After any terminal, the exact source worktree must remain clean and the authority worktree may contain only the five generated gate artifacts. No repository commit/push/PR/merge is authorized.

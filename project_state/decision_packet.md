# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue210_durable_product_setup_r2_v1","round_id":"round_20260816_issue210_durable_product_setup_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue209_heartbeat_evidence_recovery_r2_v1",
  "follows_last_round_id": "round_20260816_issue209_heartbeat_evidence_recovery_r2_v1",
  "previous_audit_outcome": "LONG_RUNNING_DOGFOOD_BLOCKED_BY_PROCESS_LOCAL_BINDING_STATE",
  "workstream_id": "issue210-durable-product-setup-r2-v1",
  "source_issue": 210,
  "parent_issue": 148,
  "blocked_successor": "long-running-unattended-dogfood-1",
  "required_branch": "owner/issue210-durable-product-setup-r2-v1",
  "starting_head": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "activation_base_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "canonical_planning_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "accepted_product_head": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "push_allowed": true,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue210-durable-product-setup-r2-v1",
      "git push origin owner/issue210-durable-product-setup-r2-v1"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue210-durable-product-setup-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue210-durable-product-setup-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue210-durable-product-setup-r2-v1);if($b){'ISSUE210_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue210-durable-product-setup-r2-v1'){'ISSUE210_V1_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE210_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue210-durable-product-setup-r2-v1 F:/reverse-agent-issue210-durable-product-setup-r2-v1 origin/owner/issue210-durable-product-setup-r2-v1",
    "Set-Location F:/reverse-agent-issue210-durable-product-setup-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue210v1.focused",
      "command": "python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_binding_resolver.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.integration",
      "command": "python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.nonrelay_full",
      "command": "python -m pytest tests/platform_v1 -q --ignore=tests/platform_v1/test_credential_relay.py",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.diff_check",
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
      "command_id": "issue210v1.status_before_stage",
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
      "command_id": "issue210v1.stage",
      "command": "git add reverse_agent/model_access/store.py reverse_agent/platform_v1/trusted_host.py tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_binding_resolver.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["staging"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.staged_scope",
      "command": "python -c \"import subprocess; allowed={'reverse_agent/model_access/store.py','reverse_agent/platform_v1/trusted_host.py','tests/test_connection_binding.py','tests/platform_v1/test_trusted_host.py','tests/platform_v1/test_binding_resolver.py'}; paths=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines()); assert paths and paths<=allowed,(paths,allowed); print('ISSUE210_V1_STAGED_SCOPE_OK',sorted(paths))\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.staged_diff_check",
      "command": "git diff --cached --check",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.commit",
      "command": "git commit -m \"feat: persist sanitized product setup metadata\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue210v1.postcommit_head",
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
      "command_id": "issue210v1.postcommit_status",
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
      "command_id": "issue210v1.push",
      "command": "git push origin owner/issue210-durable-product-setup-r2-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_binding_resolver.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "dev-up.ps1",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
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
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/**",
    ".github/**",
    "docs/**",
    "frontend/**",
    "AGENTS.md",
    "README.md"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "tag_or_release",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "real_provider_call",
    "real_credential_read",
    "dependency_install"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_binding_resolver.py",
    "project_state/gates/**"
  ],
  "runner_managed_artifact_paths": []
}
```

# Goal

Make canonical Connection + Binding product-setup metadata restart-stable across a `CombinedTrustedHost` process restart without persisting raw credentials. This closes the static blocker discovered before Long-running Unattended Dogfood 1.

# Owner implementation authorization

Only after bootstrap succeeds and transition-preflight returns `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, the local Agent may edit exactly these repository paths:

- `reverse_agent/model_access/store.py`
- `reverse_agent/platform_v1/trusted_host.py`
- `tests/test_connection_binding.py`
- `tests/platform_v1/test_trusted_host.py`
- `tests/platform_v1/test_binding_resolver.py`

No other repository mutation is authorized. `dev-up.ps1` is read-only in this round. If exact implementation proves `dev-up.ps1`, TaskStore, DurableExecutionService, credential relay, OpenCode executor, Model Control HTTP contracts, frontend, dependency, workflow, or another path must change, STOP and report the blocker; do not self-expand scope.

# Required implementation semantics

1. Add an optional durable sanitized-state path to `ModelProfileStore`. Existing tests/callers that do not request persistence must remain process-local and backward compatible.
2. The canonical `CombinedTrustedHost` default path must derive deterministically from its existing trusted runtime directory / task DB location, expected as `.platform_v1_runtime/model_setup_state.json`; an explicitly injected `ModelProfileStore` remains authoritative for tests/special callers.
3. Persist a schema-versioned document containing only sanitized Connection and Binding metadata required to reconstruct their identities/configuration. Do not persist legacy raw credential material.
4. Raw session `api_key` values MUST NEVER be serialized. A Connection configured with a raw session key remains usable during that process, but after a fresh store/host restart its metadata reloads with no raw key and must report/fail as credential missing.
5. `api_key_env` may persist only the validated environment-variable name. Never serialize the environment value. On a fresh process/store, availability must be derived from the current environment; absent variable must not be represented as an available credential.
6. Do not persist `secret_status` as authority. Derive it from current in-memory raw-session state or current environment-backed availability.
7. For `account_login` / `external_cli_session`, do not persist an `available` credential claim. Reloaded runtime availability must be fail-closed unless current runtime evidence independently establishes it; this round does not add such a probe.
8. Persist Binding metadata only: identity/name/executor/connection/model/enabled. Load must reject duplicate IDs, unknown executor IDs, dangling Connection references and malformed records.
9. Loading an existing state file must fail closed on invalid JSON, non-object root, unsupported schema version, invalid field types, duplicate IDs, malformed Connection/Binding, impossible references, or forbidden credential-bearing fields. Do not silently replace corrupt state with an empty configuration.
10. Writes must use same-directory temporary-file + flush/fsync + atomic `os.replace` (or an equivalently strong standard-library Windows-safe replacement). An interrupted temp write must not replace the last valid state; orphan temp files are non-authoritative.
11. Store mutation durability is transactional at the in-memory boundary: if persistence fails, the attempted Connection/Binding update/delete must not remain committed in memory as if durable. Restore the prior in-memory truth and raise a bounded error.
12. Preserve the existing authority-bearing Connection update invariant: provider/base_url/auth_method changes cannot silently retain an old raw session secret.
13. No new database, service, runtime dependency, credential protocol, public raw-secret endpoint, or frontend surface.
14. The persisted state file is runtime scratch and MUST NOT be added to Git.

# Required tests

Add/update deterministic provider-free tests proving all #210 acceptance criteria, including:

- restart restores sanitized Connection/Binding metadata;
- raw session sentinel absent from persisted bytes and missing after restart;
- env-reference name persists but env secret value never does; current env presence/absence controls availability;
- update/delete persistence and rollback on persistence failure;
- corrupt/unknown-schema/duplicate/dangling state fails closed;
- interrupted temp write preserves last valid state;
- fresh `CombinedTrustedHost` using the same runtime state exposes restored public metadata with no raw credential;
- existing BindingResolver and Task 3C/provider-free behavior remains green.

Do not weaken or skip #207. This Decision's broad regression command deliberately excludes only `tests/platform_v1/test_credential_relay.py` because #207 independently tracks its Windows socket-lifecycle flakiness; targeted Task 3C relay coverage remains required.

# Publication boundary

After all required commands pass, stage only the five authorized product/test paths using the exact command, verify staged scope, commit exactly once with `feat: persist sanitized product setup metadata`, and normal-push only `owner/issue210-durable-product-setup-r2-v1`.

Do not create a PR, merge, push planning/main, amend, rebase, force-push, or run any model/provider/OpenCode/Codex/OpenHands command. Owner will independently audit the pushed exact head and construct a sanitized product-only landing if accepted.

# Success terminal

`DURABLE_PRODUCT_SETUP_METADATA_PERSISTENCE_READY_FOR_OWNER_AUDIT`

# Failure terminal

`DURABLE_PRODUCT_SETUP_METADATA_PERSISTENCE_BLOCKED_WITH_EXACT_EVIDENCE`

On failure preserve the worktree and evidence, report the first blocking invariant/command and exact git status, and do not weaken secret boundaries or broaden scope.

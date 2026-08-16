# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue220_dogfood1_external_session_bootstrap_r2_v1",
  "round_id": "round_20260816_issue220_dogfood1_external_session_bootstrap_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue218_issue216_validation_recovery_r2_v2",
  "follows_last_round_id": "round_20260816_issue218_issue216_validation_recovery_r2_v2",
  "previous_audit_outcome": "ISSUE216_COMPLETED_AND_LANDED_PRODUCT_SETUP_STATE_STILL_REQUIRES_LOCAL_BOOTSTRAP",
  "workstream_id": "issue220-dogfood1-external-session-bootstrap-r2-v1",
  "source_issue": 220,
  "parent_issue": 148,
  "required_branch": "owner/issue220-dogfood1-external-session-bootstrap-r2-v1",
  "starting_head": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "activation_base_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "canonical_planning_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
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
  "product_setup_mutation_allowed": true,
  "model_api_invocation_allowed": false,
  "provider_network_call_allowed": false,
  "opencode_task_invocation_allowed": false,
  "opencode_auth_metadata_probe_allowed": true,
  "credential_file_read_allowed": false,
  "credential_value_access_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "live_connection_probe_allowed": false,
  "external_harness_write_path": "F:/reverse-agent-issue220-external-session-bootstrap-v1/setup_bootstrap.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue220-external-session-bootstrap-v1/**",
    "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json"
  ],
  "product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "product_setup_target_must_be_absent_before_install": true,
  "readiness_must_precede_product_setup_install": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "canonical_setup": {
    "connection_id": "sensenova-67-flash-lite",
    "connection_name": "SenseNova 6.7 Flash-Lite",
    "provider": "sensetime",
    "base_url": "https://token.sensenova.cn/v1",
    "auth_method": "external_cli_session",
    "binding_id": "opencode-sensenova-67-flash-lite",
    "binding_name": "OpenCode SenseNova 6.7 Flash-Lite",
    "executor_id": "opencode",
    "model_id": "sensenova-6.7-flash-lite",
    "enabled": true
  },
  "credential_boundary": {
    "direct_auth_store_file_access_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "raw_auth_probe_stdout_persistence_allowed": false,
    "trusted_product_auth_metadata_probe_allowed": true,
    "trusted_product_sanitized_provider_metadata_allowed": true,
    "trusted_host_provider_inference_allowed": false,
    "trusted_host_credential_relay_lease_allowed": false,
    "raw_credential_persistence_allowed": false
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue220-dogfood1-external-session-bootstrap-r2-v1"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue220-dogfood1-external-session-bootstrap-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue220-dogfood1-external-session-bootstrap-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue220-dogfood1-external-session-bootstrap-r2-v1);if($b){'ISSUE220_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue220-dogfood1-external-session-bootstrap-r2-v1'){'ISSUE220_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue220-bootstrap-source-v1'){'ISSUE220_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue220-external-session-bootstrap-v1'){'ISSUE220_V1_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE220_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue220-dogfood1-external-session-bootstrap-r2-v1 F:/reverse-agent-issue220-dogfood1-external-session-bootstrap-r2-v1 origin/owner/issue220-dogfood1-external-session-bootstrap-r2-v1",
    "Set-Location F:/reverse-agent-issue220-dogfood1-external-session-bootstrap-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD 3b650e6239336c796593cecd3c137cf839cf1e95",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue220v1.source_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue220-bootstrap-source-v1 3b650e6239336c796593cecd3c137cf839cf1e95",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.source_head",
      "command": "git -C F:/reverse-agent-issue220-bootstrap-source-v1 rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.source_status_before",
      "command": "git -C F:/reverse-agent-issue220-bootstrap-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue220-external-session-bootstrap-v1' -ErrorAction Stop | Out-Null; 'ISSUE220_V1_EVIDENCE_ROOT_CREATED'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.setup_bootstrap",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue220-dogfood1-external-session-bootstrap-r2-v1' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue220-external-session-bootstrap-v1/setup_bootstrap.py' --source 'F:/reverse-agent-issue220-bootstrap-source-v1' --root 'F:/reverse-agent-issue220-external-session-bootstrap-v1/runtime' --target 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --authority $a --planning '3b650e6239336c796593cecd3c137cf839cf1e95'\"",
      "phase": "configuration",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.source_status_after",
      "command": "git -C F:/reverse-agent-issue220-bootstrap-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue220v1.authority_status_final",
      "command": "git -C F:/reverse-agent-issue220-dogfood1-external-session-bootstrap-r2-v1 status --short",
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
    "credential_value_read",
    "credential_value_print",
    "credential_value_hash",
    "credential_value_length_check",
    "credential_file_read",
    "credential_file_discovery",
    "raw_auth_probe_stdout_persistence",
    "auth_login",
    "auth_logout",
    "sensenova_api_key_env_bootstrap",
    "session_api_key_configuration",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
    "model_api_invocation",
    "provider_network_call",
    "opencode_task_invocation",
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
    "delete_existing_product_setup_state",
    "real_task_store_mutation",
    "dependency_install"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/gates/**"]
}
```

# Goal

Create exactly one restart-safe sanitized Product Setup record for SenseNova 6.7 Flash-Lite that reuses the already-persisted OpenCode `sensetime` authentication through the landed external-session path, prove the exact record in two fresh trusted-host OS processes before durable installation, and perform zero model/provider execution and zero raw-credential access.

# Why this authority exists

#213 correctly stopped because the durable Product Setup state was absent. #215's env-backed `SENSENOVA_API_KEY` strategy was then superseded because the user already has working SenseNova authentication inside OpenCode and duplicate credential entry violates the configure-once/reuse architecture. #216/#218/#219 landed the required product support: exact provider-ID persisted-auth discovery, secret-free external-session config, and restart-time fail-closed auth re-derivation.

The remaining work is local state bootstrap/readiness, not product implementation.

# Local-state separation

The authority worktree exists only for transition-gate authorization and generated gate evidence. The detached source worktree is exact canonical planning and must remain tracked-clean. Runtime evidence and the single external harness live outside Git under `F:/reverse-agent-issue220-external-session-bootstrap-v1`.

The only durable real Product Setup target authorized for creation is:

`F:/reverse-agent/.platform_v1_runtime/model_setup_state.json`

The real task database `F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3` is read/write forbidden.

# External harness rule

Only after transition preflight is `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`, and `issue220v1.evidence_root_create` succeeds may the local Agent create exactly one external script:

`F:/reverse-agent-issue220-external-session-bootstrap-v1/setup_bootstrap.py`

It must never be added to Git. No other script/executable may be created.

The script may invoke only landed product code and ordinary Python/loopback/subprocess primitives needed for the bounded readiness proof. It MUST NOT directly locate/read OpenCode auth/config files or obtain raw auth-list stdout. Authentication visibility must be derived only by canonical trusted-host startup calling the landed product auth-metadata probe.

# Mandatory harness semantics

1. Fail closed before any Product Setup creation if the real target already exists. Terminal blocker: `PRODUCT_SETUP_TARGET_BECAME_PRESENT`.
2. Use exact source planning `3b650e6239336c796593cecd3c137cf839cf1e95` and disposable TaskStore/runtime paths only.
3. Create a disposable canonical `CombinedTrustedHost` with Model Control writes enabled on ephemeral loopback ports. Through the normal Model Control API create exactly:

Connection `sensenova-67-flash-lite`:
- name `SenseNova 6.7 Flash-Lite`
- provider `sensetime`
- base_url `https://token.sensenova.cn/v1`
- auth_method `external_cli_session`
- enabled true

Binding `opencode-sensenova-67-flash-lite`:
- name `OpenCode SenseNova 6.7 Flash-Lite`
- executor_id `opencode`
- connection_id `sensenova-67-flash-lite`
- model_id `sensenova-6.7-flash-lite`
- enabled true

Do not supply `api_key`, `api_key_env`, `external_session_status`, or any credential-bearing field.

4. Stop the creation host and validate its generated state document before any real-target write: schema v1; exactly one Connection and one Binding; exact safe fields/values; recursively reject all raw credential-bearing fields; reject persisted `external_session_status` and `secret_status`; reject unknown records/fields. Persist only a sanitized evidence summary, never the raw auth-list output.
5. Copy the exact validated state bytes into two independent disposable runtime directories. Launch two separate fresh Python OS processes sequentially. Each child must use canonical trusted-host startup so `_refresh_external_session_auth()` performs the landed product auth-metadata probe. Each child must expose via public loopback Model Control GET exactly the expected Connection/Binding and must observe `secret_status=not_applicable` plus `external_session_status=available` for provider `sensetime`.
6. Each child must stop cleanly. No child may call Task `/execute`, Connection `/test`, create a credential relay lease, or invoke `opencode run`. If either fresh cycle cannot establish external-session availability, return exit 20 and leave the real target absent.
7. Only after both independent fresh-process cycles pass, re-check that the real target is absent. Install the exact already-validated candidate with no-overwrite semantics. Any race must fail closed; never replace an existing target.
8. Re-read only the installed sanitized document and verify it is byte/content equivalent to the validated candidate. Do not run a third model/provider operation. Write a final sanitized summary outside Git.
9. Preserve source and authority worktrees tracked-clean except authorized generated gate files in the authority worktree.

# Terminal outcomes

Success:

`DOGFOOD1_EXTERNAL_SESSION_PRODUCT_SETUP_BOOTSTRAP_ACCEPTED`

Exit 20 bounded blocker:

`DOGFOOD1_EXTERNAL_SESSION_PRODUCT_SETUP_BOOTSTRAP_BLOCKED`

Expected blocker classifications include `PRODUCT_SETUP_TARGET_BECAME_PRESENT`, `OPENCODE_SENSITIME_AUTH_NOT_VISIBLE`, and `EXTERNAL_SESSION_NOT_AVAILABLE_AFTER_FRESH_RESTART`.

A blocker does not authorize credential inspection, auth repair, provider/model execution, repository mutation, retry under another model, or reuse of consumed/superseded #213/#215 authorities.

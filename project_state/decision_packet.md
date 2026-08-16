# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue221_opencode_auth_probe_differential_r2_v1",
  "round_id": "round_20260816_issue221_opencode_auth_probe_differential_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue220_dogfood1_external_session_bootstrap_r2_v2",
  "follows_last_round_id": "round_20260816_issue220_dogfood1_external_session_bootstrap_r2_v2",
  "previous_audit_outcome": "ISSUE220_V2_BOUNDED_BLOCKED_EXTERNAL_SESSION_MISSING_ROOT_CAUSE_UNRESOLVED",
  "workstream_id": "issue221-opencode-auth-probe-differential-r2-v1",
  "source_issue": 221,
  "parent_issue": 148,
  "required_branch": "owner/issue221-opencode-auth-probe-differential-r2-v1",
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
  "product_setup_mutation_allowed": false,
  "model_api_invocation_allowed": false,
  "provider_network_call_allowed": false,
  "opencode_task_invocation_allowed": false,
  "opencode_auth_metadata_probe_allowed": true,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": false,
  "live_connection_probe_allowed": false,
  "external_harness_write_path": "F:/reverse-agent-issue221-opencode-auth-diff-v1/auth_probe_diff.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue221-opencode-auth-diff-v1/**"
  ],
  "product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "product_setup_target_must_remain_absent": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "credential_boundary": {
    "agent_or_harness_direct_credential_file_read_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "opencode_internal_auth_store_resolution_for_auth_list_allowed": true,
    "harness_transient_auth_stream_capture_for_safe_parser_allowed": true,
    "raw_auth_stream_display_allowed": false,
    "raw_auth_stream_persistence_allowed": false,
    "sanitized_provider_metadata_persistence_allowed": true,
    "location_env_value_transient_child_pass_allowed_names": [
      "USERPROFILE",
      "HOME",
      "LOCALAPPDATA",
      "APPDATA",
      "XDG_DATA_HOME"
    ],
    "location_env_value_display_or_persistence_allowed": false,
    "arbitrary_environment_enumeration_allowed": false,
    "provider_credential_use_for_model_request_allowed": false
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue221-opencode-auth-probe-differential-r2-v1"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue221-opencode-auth-probe-differential-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue221-opencode-auth-probe-differential-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue221-opencode-auth-probe-differential-r2-v1);if($b){'ISSUE221_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue221-opencode-auth-probe-differential-r2-v1'){'ISSUE221_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue221-probe-source-v1'){'ISSUE221_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue221-opencode-auth-diff-v1'){'ISSUE221_V1_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE221_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue221-opencode-auth-probe-differential-r2-v1 F:/reverse-agent-issue221-opencode-auth-probe-differential-r2-v1 origin/owner/issue221-opencode-auth-probe-differential-r2-v1",
    "Set-Location F:/reverse-agent-issue221-opencode-auth-probe-differential-r2-v1",
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
      "command_id": "issue221v1.source_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue221-probe-source-v1 3b650e6239336c796593cecd3c137cf839cf1e95",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.source_head",
      "command": "git -C F:/reverse-agent-issue221-probe-source-v1 rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.source_status_before",
      "command": "git -C F:/reverse-agent-issue221-probe-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue221-opencode-auth-diff-v1' -ErrorAction Stop | Out-Null; 'ISSUE221_V1_EVIDENCE_ROOT_CREATED'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.auth_differential",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue221-opencode-auth-probe-differential-r2-v1' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue221-opencode-auth-diff-v1/auth_probe_diff.py' --source 'F:/reverse-agent-issue221-probe-source-v1' --root 'F:/reverse-agent-issue221-opencode-auth-diff-v1' --authority $a --planning '3b650e6239336c796593cecd3c137cf839cf1e95' --product-setup-target 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json'\"",
      "phase": "probe",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.source_status_after",
      "command": "git -C F:/reverse-agent-issue221-probe-source-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue221v1.authority_status_final",
      "command": "git -C F:/reverse-agent-issue221-opencode-auth-probe-differential-r2-v1 status --short",
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/store.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_trusted_host.py"
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
    "agent_or_harness_direct_credential_file_read",
    "agent_or_harness_credential_file_discovery",
    "agent_or_harness_credential_value_read",
    "agent_or_harness_credential_value_print",
    "agent_or_harness_credential_value_hash",
    "agent_or_harness_credential_value_length_check",
    "raw_auth_stream_display",
    "raw_auth_stream_persistence",
    "arbitrary_environment_enumeration",
    "auth_login",
    "auth_logout",
    "opencode_run",
    "opencode_models",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
    "product_setup_mutation",
    "model_api_invocation",
    "provider_network_call",
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
    "real_task_store_mutation",
    "dependency_install"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/gates/**"]
}
```

# Goal

Produce a sanitized, zero-model differential explaining why the landed fresh-process OpenCode auth probe returns `{}`. Do not repair code or authentication in this round.

# Separation

The authority worktree is only for transition gates. The detached source worktree is exact canonical planning and must remain tracked-clean. The only external script is:

`F:/reverse-agent-issue221-opencode-auth-diff-v1/auth_probe_diff.py`

It may be created only after `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`, and evidence-root creation. It is never staged, committed, or pushed.

The real Product Setup target must remain absent throughout:

`F:/reverse-agent/.platform_v1_runtime/model_setup_state.json`

If it is present at probe start, return exit 20 with `PRODUCT_SETUP_TARGET_BECAME_PRESENT`; do not read, modify, delete, or overwrite it.

# Mandatory differential semantics

1. Insert exact source worktree at the front of `sys.path` and import the canonical `resolve_opencode_cli`, `execute_opencode_auth_list_probe`, `parse_opencode_auth_list`, and `redact_secrets` functions from planning `3b650e6239336c796593cecd3c137cf839cf1e95`.
2. Resolve OpenCode once. Record only executable basename, `is_cmd`, and sanitized `opencode --version`; do not persist a user-specific full executable path.
3. Call canonical `execute_opencode_auth_list_probe()` once and record only its returned sanitized provider mapping.
4. Construct the exact restricted environment using only `PATH`, `SystemRoot`, and the five canonical `OPENCODE_DISABLE_*` flags. Invoke the same resolved CLI with `auth list`. If its return code is nonzero, invoke `auth ls` as fallback. Capture streams only in memory. For every executed variant record only return code, stdout/stderr nonempty booleans, and current `parse_opencode_auth_list()` results for stdout and stderr separately. Never persist or print raw stream content.
5. Run an inherited-environment control with the same CLI. To avoid copying/enumerating the parent environment, temporarily set only the five fixed `OPENCODE_DISABLE_*` names in the harness process, invoke the child with `env=None` so it inherits normally, then restore only those five fixed variables to their prior states. The harness must not enumerate or serialize the inherited environment. Record the same sanitized stream booleans/mappings only.
6. Only when the inherited control exposes exact provider `sensetime` but the exact restricted environment does not, test the bounded location-variable matrix. For each of `USERPROFILE`, `HOME`, `LOCALAPPDATA`, `APPDATA`, `XDG_DATA_HOME`, check that exact name only. If present, read its value transiently solely to add it to a fresh exact-restricted child environment. Never display, persist, hash, measure, compare, or return the value. Record only the variable name, `parent_present`, return code, stream nonempty booleans, and sanitized parser mappings. Do not enumerate any other environment variable.
7. Raw `auth list`/`auth ls` stdout/stderr is sensitive diagnostic material even when it usually contains only provider metadata. It must never be written to disk, printed to console, placed in exceptions, included in summaries, or returned to the Agent. Only current parser outputs and booleans may survive.
8. Do not call `opencode run`, `opencode models`, auth login/logout, Connection `/test`, credential relay, Task `/execute`, any model/provider endpoint, or any network operation other than bootstrap Git fetches.
9. Write exactly one sanitized JSON summary under the evidence root, for example `auth_probe_diff_summary.json`. It must contain no raw streams, no credential path, no location-env values, and no full OpenCode executable path.
10. Emit one primary classification from #221 and terminal `OPENCODE_AUTH_PROBE_DIFFERENTIAL_READY_FOR_OWNER_AUDIT` on a complete bounded observation. Use exit 20 / `OPENCODE_AUTH_PROBE_DIFFERENTIAL_BLOCKED` only when the differential cannot be completed within this boundary.

# Classification precedence

Use evidence, not guessing. Prefer the narrowest supported classification:

1. If canonical production probe already includes exact `sensetime`: `AUTH_VISIBLE_IN_PRODUCTION_PROBE`.
2. Else if exact restricted stdout parser includes `sensetime`: `AUTH_VISIBLE_RESTRICTED_STDOUT`.
3. Else if exact restricted stderr parser includes `sensetime`: `AUTH_VISIBLE_RESTRICTED_STDERR_ONLY`.
4. Else if inherited stdout or stderr parser includes `sensetime`: run the location-variable matrix. If one single-variable trial exposes it, classify `AUTH_VISIBLE_WITH_LOCATION_ENV_<NAME>` using the first fixed-order successful name. If none does, `AUTH_VISIBLE_INHERITED_ONLY`.
5. Else if executed auth commands return nonzero with no parsed `sensetime`: `OPENCODE_AUTH_LIST_COMMAND_FAILURE`.
6. Else if either stream is nonempty but parsers remain empty: `AUTH_OUTPUT_PRESENT_BUT_PARSER_EMPTY`.
7. Else: `AUTH_NOT_VISIBLE_INHERITED_OR_RESTRICTED`.

A classification is observation only and grants no repair authority.

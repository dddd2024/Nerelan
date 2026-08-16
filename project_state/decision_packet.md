# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue223_opencode_auth_cardinality_r2_v2",
  "round_id": "round_20260816_issue223_opencode_auth_cardinality_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue223_opencode_auth_cardinality_r2_v1",
  "follows_last_round_id": "round_20260816_issue223_opencode_auth_cardinality_r2_v1",
  "previous_audit_outcome": "ISSUE223_V1_SUPERSEDED_BEFORE_EXECUTION_CLASSIFICATION_NAMING_AND_ENV_INCONSISTENCY_GAP",
  "workstream_id": "issue223-opencode-auth-cardinality-r2-v2",
  "source_issue": 223,
  "parent_issue": 148,
  "required_branch": "owner/issue223-opencode-auth-cardinality-r2-v2",
  "starting_head": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "activation_base_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "canonical_planning_sha": "3b650e6239336c796593cecd3c137cf839cf1e95",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "supersedes_decision_id": "decision_20260816_issue223_opencode_auth_cardinality_r2_v1",
  "superseded_branch_must_not_execute": "owner/issue223-opencode-auth-cardinality-r2-v1",
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
  "external_harness_write_path": "F:/reverse-agent-issue223-opencode-auth-cardinality-v2/auth_cardinality_probe.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue223-opencode-auth-cardinality-v2/**"
  ],
  "product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "product_setup_target_must_remain_absent": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "expected_provider_id": "sensetime",
  "expected_auth_type": "api",
  "credential_boundary": {
    "agent_or_harness_direct_credential_file_read_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "opencode_internal_auth_store_resolution_for_auth_list_allowed": true,
    "harness_transient_auth_stream_capture_for_bounded_summary_allowed": true,
    "raw_auth_stream_display_allowed": false,
    "raw_auth_stream_persistence_allowed": false,
    "provider_display_label_persistence_allowed": false,
    "credential_row_text_persistence_allowed": false,
    "sanitized_credential_count_persistence_allowed": true,
    "sanitized_candidate_row_count_persistence_allowed": true,
    "sanitized_expected_row_boolean_persistence_allowed": true,
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue223-opencode-auth-cardinality-r2-v2"
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue223-opencode-auth-cardinality-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue223-opencode-auth-cardinality-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue223-opencode-auth-cardinality-r2-v2);if($b){'ISSUE223_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue223-opencode-auth-cardinality-r2-v2'){'ISSUE223_V2_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue223-probe-source-v2'){'ISSUE223_V2_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue223-opencode-auth-cardinality-v2'){'ISSUE223_V2_EVIDENCE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE223_V2_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue223-opencode-auth-cardinality-r2-v2 F:/reverse-agent-issue223-opencode-auth-cardinality-r2-v2 origin/owner/issue223-opencode-auth-cardinality-r2-v2",
    "Set-Location F:/reverse-agent-issue223-opencode-auth-cardinality-r2-v2",
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
      "command_id": "issue223v2.source_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue223-probe-source-v2 3b650e6239336c796593cecd3c137cf839cf1e95",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.source_head",
      "command": "git -C F:/reverse-agent-issue223-probe-source-v2 rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.source_status_before",
      "command": "git -C F:/reverse-agent-issue223-probe-source-v2 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue223-opencode-auth-cardinality-v2' -ErrorAction Stop | Out-Null; 'ISSUE223_V2_EVIDENCE_ROOT_CREATED'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.auth_cardinality",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue223-opencode-auth-cardinality-r2-v2' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue223-opencode-auth-cardinality-v2/auth_cardinality_probe.py' --source 'F:/reverse-agent-issue223-probe-source-v2' --root 'F:/reverse-agent-issue223-opencode-auth-cardinality-v2' --authority $a --planning '3b650e6239336c796593cecd3c137cf839cf1e95' --product-setup-target 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json'\"",
      "phase": "probe",
      "required": true,
      "expected_exit_codes": [0,20],
      "execution_surface": "local",
      "operations": ["run_checks","repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.source_status_after",
      "command": "git -C F:/reverse-agent-issue223-probe-source-v2 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue223v2.authority_status_final",
      "command": "git -C F:/reverse-agent-issue223-opencode-auth-cardinality-r2-v2 status --short",
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
    "provider_display_label_persistence",
    "credential_row_text_persistence",
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

Resolve the remaining #221 ambiguity without reading credential files or exposing raw OpenCode terminal output: determine whether OpenCode 1.18.15 reports zero credentials, reports credentials including an exact `sensetime api` row, or reports credentials whose terminal display identity cannot be safely mapped to provider ID.

This round is observation-only. It MUST NOT repair reverse-agent, mutate Product Setup, log in/out of OpenCode, or execute any model/provider task.

# Separation

R2 V1 is superseded before local execution and MUST NOT execute or be reused.

The authority worktree is only for transition gates. The detached source worktree is exact canonical planning and must remain tracked-clean.

The only external script is:

`F:/reverse-agent-issue223-opencode-auth-cardinality-v2/auth_cardinality_probe.py`

It may be created only after `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`, and evidence-root creation. It is never staged, committed, or pushed.

The real Product Setup target must remain absent throughout:

`F:/reverse-agent/.platform_v1_runtime/model_setup_state.json`

If it is present at probe start or appears before final evidence write, return exit 20 with `PRODUCT_SETUP_TARGET_BECAME_PRESENT`; do not read, modify, delete, or overwrite it.

# Mandatory probe semantics

1. Insert exact source worktree at the front of `sys.path` and import canonical `resolve_opencode_cli` and `redact_secrets` from planning `3b650e6239336c796593cecd3c137cf839cf1e95`.
2. Resolve OpenCode once. Record only executable basename, `is_cmd`, and sanitized `opencode --version`.
3. Restricted observation: child env contains only `PATH`, `SystemRoot`, and the five canonical `OPENCODE_DISABLE_*` flags. Run `auth list`; run `auth ls` only if list exits nonzero.
4. Inherited control: do not enumerate/copy/serialize parent env. Temporarily overlay only the five fixed disable flags in `os.environ`, run child with `env=None`, then restore those five names exactly.
5. Raw stdout/stderr may exist only transiently inside the harness and MUST NOT be printed, persisted, placed in exceptions, summaries, logs, digests, or returned evidence.
6. Normalize streams only in memory by removing ANSI CSI escapes and fixed terminal decoration/border glyphs; normalization must not emit or persist normalized lines.
7. For each executed auth command derive only: variant; return code; stdout/stderr nonempty; `credential_count`; `candidate_auth_row_count`; `exact_sensetime_api_row_present`.
8. `credential_count`: after normalization, accept only whole lines matching `^\s*(\d+)\s+credentials?\s*$` case-insensitively. Across stdout/stderr all matches must agree on one integer; otherwise null. Never persist matched text.
9. `candidate_auth_row_count`: first exclude every line that matches the credential-summary rule and every header line whose first normalized token is exactly `Credentials` case-insensitively. Then count remaining normalized lines whose final token is one of `api`, `oauth`, `sso`, `account_login`, `external_cli_session`, `api_key`, `session`, `credential`. Never persist row text/provider labels.
10. `exact_sensetime_api_row_present`: true only when a candidate row has auth type exactly `api` and the complete provider-label portion equals `sensetime` case-insensitively after trimming. No fuzzy/substring/slug/display-name mapping.
11. Define restricted-stronger-than-inherited as either: restricted exact row true while inherited exact row false; or both counts are non-null and restricted credential_count > inherited credential_count. This is an inconsistency and MUST classify `AUTH_METADATA_ENV_INCONSISTENT` before any zero-count conclusion.
12. Run location matrix only if inherited evidence is stronger than restricted: inherited count > 0 while restricted is 0/null, or inherited exact row true while restricted false. Fixed order: `USERPROFILE`, `HOME`, `LOCALAPPDATA`, `APPDATA`, `XDG_DATA_HOME`. Query each name directly; never enumerate env. Add at most one existing value per restricted trial; never display/persist/hash/measure/compare the value.
13. Harness may write only `F:/reverse-agent-issue223-opencode-auth-cardinality-v2/auth_cardinality_summary.json`, containing sanitized SHAs/CLI identity/observations/classification/false attestations. No raw terminal text, provider labels, credential rows/paths, location values, or full executable paths.
14. No model/provider call, `opencode run`, `opencode models`, Connection test, relay lease, Task execute, auth login/logout, Product Setup mutation, real TaskStore access, repo product/test mutation, or dependency install.

# Classification priority

Use the first matching rule:

1. inherited command cannot succeed -> `OPENCODE_AUTH_LIST_COMMAND_FAILURE`.
2. inherited succeeds but unique credential_count is null -> `AUTH_LIST_CARDINALITY_UNRESOLVED`.
3. restricted is stronger than inherited under rule 11 -> `AUTH_METADATA_ENV_INCONSISTENT`.
4. inherited credential_count == 0 -> `OPENCODE_INHERITED_CREDENTIAL_COUNT_ZERO`.
5. inherited and restricted exact `sensetime api` booleans both true -> `SENSETIME_AUTH_ROW_VISIBLE_IN_RESTRICTED_METADATA`.
6. inherited exact row true and restricted false -> run permitted location matrix; first restoring variable => `SENSETIME_AUTH_VISIBLE_WITH_LOCATION_ENV_<NAME>`; none => `SENSETIME_AUTH_VISIBLE_INHERITED_ONLY`.
7. inherited credential_count > 0 but exact `sensetime api` row false -> `CREDENTIALS_PRESENT_SENSETIME_IDENTITY_UNRESOLVED`.
8. otherwise -> `AUTH_LIST_CARDINALITY_UNRESOLVED`.

No repair is allowed in this round.

# Terminal

Success: `OPENCODE_AUTH_CARDINALITY_READY_FOR_OWNER_AUDIT`

Blocked: `OPENCODE_AUTH_CARDINALITY_BLOCKED`

Exit 20 is a bounded stop, not repair authority.

# Required final report

Report only sanitized evidence: remote planning SHA; remote authority SHA; local authority HEAD; source HEAD; transition terminal/blockers; sanitized OpenCode version; executable basename/is_cmd; restricted and inherited variant/returncode/stream booleans/credential_count/candidate_auth_row_count/exact_sensetime_api_row_present; location matrix if executed (names and sanitized fields only); primary classification; Product Setup target remained absent; source/authority final status; model/provider call NO; direct credential access NO; raw auth stream display/persistence NO; provider display-label/row persistence NO; repo product mutation NO; terminal state.

Stop for Owner audit.
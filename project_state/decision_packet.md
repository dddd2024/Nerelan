# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260817_issue228_dogfood1_one_shot_live_r2_v2",
  "round_id": "round_20260817_issue228_dogfood1_one_shot_live_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260817_issue228_dogfood1_one_shot_live_r2_v1",
  "follows_last_round_id": "round_20260817_issue228_dogfood1_one_shot_live_r2_v1",
  "previous_audit_outcome": "ISSUE228_V1_SUPERSEDED_BEFORE_EXECUTION_MARKER_BYTE_ENCODING_AND_BRANCH_SCOPE_PRECISION",
  "supersedes_decision_id": "decision_20260817_issue228_dogfood1_one_shot_live_r2_v1",
  "superseded_branch_must_not_execute": "owner/issue228-dogfood1-one-shot-live-r2-v1",
  "workstream_id": "issue228-dogfood1-one-shot-live-r2-v2",
  "source_issue": 228,
  "parent_issue": 148,
  "required_branch": "owner/issue228-dogfood1-one-shot-live-r2-v2",
  "starting_head": "b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa",
  "activation_base_sha": "b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa",
  "canonical_planning_sha": "b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa",
  "authority_worktree": "F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "worktree_creation_allowed": true,
  "branch_creation_allowed": true,
  "branch_creation_scope": "local_tracking_branch_owner/issue228-dogfood1-one-shot-live-r2-v2_only",
  "remote_branch_creation_allowed": false,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "direct_push_to_main_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "package_installation_allowed": false,
  "product_setup_mutation_allowed": false,
  "provider_network_call_allowed": true,
  "opencode_invocation_allowed": true,
  "opencode_task_invocation_allowed": true,
  "opencode_auth_metadata_probe_allowed": false,
  "credential_relay_lease_allowed": false,
  "task_execute_allowed": true,
  "live_connection_probe_allowed": false,
  "real_user_credential_access_allowed": false,
  "synthetic_test_credential_fixture_allowed": false,
  "real_task_store_access_allowed": false,
  "product_change_commit_limit": 0,
  "single_task_create_required": true,
  "single_task_execute_required": true,
  "single_opencode_run_required": true,
  "retry_allowed": false,
  "resume_allowed": false,
  "fallback_provider_allowed": false,
  "fallback_model_allowed": false,
  "manual_opencode_invocation_allowed": false,
  "bounded_external_runtime_cleanup_allowed": true,
  "external_session_validity_proof": "single_product_path_opencode_run",
  "real_product_setup_target": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "real_product_setup_target_must_exist": true,
  "real_product_setup_target_read_only": true,
  "real_task_store_path_forbidden": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "external_harness_write_path": "F:/reverse-agent-issue228-dogfood1-live-v2/dogfood1_live.py",
  "external_runtime_write_allowlist": [
    "F:/reverse-agent-issue228-dogfood1-live-v2/**"
  ],
  "bounded_cleanup_paths": [
    "F:/reverse-agent-issue228-dogfood1-live-v2/temp/opencode_prompt_*.txt"
  ],
  "prompt_temp_root": "F:/reverse-agent-issue228-dogfood1-live-v2/temp",
  "disposable_task_store_path": "F:/reverse-agent-issue228-dogfood1-live-v2/runtime/tasks.sqlite3",
  "disposable_seed_repo": "F:/reverse-agent-issue228-dogfood1-live-v2/seed-repo",
  "disposable_workspace_root": "F:/reverse-agent-issue228-dogfood1-live-v2/workspaces",
  "canonical_setup": {
    "connection_id": "sensenova-67-flash-lite",
    "provider": "sensetime",
    "base_url": "https://token.sensenova.cn/v1",
    "auth_method": "external_cli_session",
    "required_runtime_status": "executor_managed",
    "binding_id": "opencode-sensenova-67-flash-lite",
    "executor_id": "opencode",
    "raw_model_id": "sensenova-6.7-flash-lite",
    "normalized_model_id": "sensetime/sensenova-6.7-flash-lite"
  },
  "dogfood_task": {
    "executor_kind": "opencode",
    "binding_ref": "opencode-sensenova-67-flash-lite",
    "orchestration_mode": "single",
    "validation_command_id": "git_diff_check",
    "tracked_marker_path": "dogfood1_result.txt",
    "initial_marker_bytes": "PENDING\n",
    "required_marker_bytes": "DOGFOOD1_OK\n",
    "instruction": "Replace the entire contents of the tracked file dogfood1_result.txt with exactly DOGFOOD1_OK followed by one newline. Do not modify any other file. Do not run shell commands. Do not use web/search/network tools. Do not access anything outside the supplied worktree. After the file edit, stop."
  },
  "credential_boundary": {
    "agent_or_harness_direct_credential_file_read_allowed": false,
    "agent_or_harness_credential_file_discovery_allowed": false,
    "agent_or_harness_credential_value_access_allowed": false,
    "agent_or_harness_raw_opencode_output_access_allowed": false,
    "opencode_internal_persisted_credential_resolution_allowed": true,
    "opencode_internal_credential_use_for_single_model_run_allowed": true,
    "raw_credential_persistence_allowed": false,
    "auth_metadata_probe_allowed": false,
    "connection_test_allowed": false,
    "credential_relay_lease_allowed": false
  },
  "capability_policy": {
    "runner_dispatch_allowed": true,
    "model_api_invocation_allowed": true,
    "opencode_invocation_allowed": true,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "bmad_installation_allowed": false,
    "loopback_model_control_http_allowed": true,
    "loopback_task_api_start_allowed": true,
    "loopback_credential_relay_server_start_allowed": true,
    "credential_relay_lease_allowed": false,
    "external_provider_network_allowed": true,
    "provider_network_allowlist": [
      "https://token.sensenova.cn/v1"
    ],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue228-dogfood1-one-shot-live-r2-v2",
      "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue228-dogfood1-live-v2/dogfood1_live.py' --source 'F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2' --root 'F:/reverse-agent-issue228-dogfood1-live-v2' --product-setup 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --forbidden-task-store 'F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3' --authority $a --planning 'b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa'\""
    ]
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue228-dogfood1-one-shot-live-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue228-dogfood1-one-shot-live-r2-v2",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue228-dogfood1-one-shot-live-r2-v2);if($b){'ISSUE228_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2'){'ISSUE228_V2_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue228-dogfood1-live-v2'){'ISSUE228_V2_EVIDENCE_ROOT_ALREADY_EXISTS';exit 23};if(-not (Test-Path -LiteralPath 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json')){'DOGFOOD1_PRODUCT_SETUP_MISSING';exit 22};'ISSUE228_V2_BOOTSTRAP_PRECONDITIONS_PASS'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue228-dogfood1-one-shot-live-r2-v2 F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2 origin/owner/issue228-dogfood1-one-shot-live-r2-v2",
    "Set-Location F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue228v2.status_before",
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
      "command_id": "issue228v2.evidence_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue228-dogfood1-live-v2' -ErrorAction Stop | Out-Null; 'ISSUE228_V2_EVIDENCE_ROOT_CREATED'\"",
      "phase": "setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue228v2.one_shot_live",
      "command": "powershell -NoProfile -Command \"$a=(git -C 'F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2' rev-parse HEAD).Trim(); python 'F:/reverse-agent-issue228-dogfood1-live-v2/dogfood1_live.py' --source 'F:/reverse-agent-issue228-dogfood1-one-shot-live-r2-v2' --root 'F:/reverse-agent-issue228-dogfood1-live-v2' --product-setup 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json' --forbidden-task-store 'F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3' --authority $a --planning 'b6f5d11f698ed1b9c367cb70e1d7338c6bf654fa'\"",
      "phase": "execution",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": [
        "task_execute",
        "runner_dispatch",
        "opencode_invocation",
        "model_api_invocation",
        "provider_network_call"
      ],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue228v2.status_final",
      "command": "git status --short",
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
  "generated_artifact_paths": [
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
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/run_store.py",
    "project_state/schemas/**"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "AGENTS.md",
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
    "agent_or_harness_credential_value_length_or_measurement",
    "opencode_auth_probe",
    "opencode_models",
    "opencode_version_probe",
    "auth_login",
    "auth_logout",
    "manual_opencode_run",
    "second_task_execute",
    "task_resume",
    "task_retry",
    "fallback_provider",
    "fallback_model",
    "live_connection_probe",
    "credential_relay_lease",
    "product_setup_mutation",
    "real_task_store_access",
    "dependency_install",
    "package_lock_mutation",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "tag_or_release",
    "direct_push_main"
  ]
}
```

## Execution objective

Run exactly one live Dogfood1 through the normal product Task API and Binding path, using the real installed sanitized Product Setup but a disposable TaskStore and disposable Git repository/worktree.

V1 is superseded before local execution. Do not create or use any V1 local branch, worktree, harness, evidence root, or runtime artifact.

This Work Item intentionally allows one OpenCode model run. It does NOT allow any direct credential inspection, auth metadata probe, connection test, retry, resume, fallback, manual OpenCode invocation, or second Task execution.

The external harness may be written only at `F:/reverse-agent-issue228-dogfood1-live-v2/dogfood1_live.py` after transition authorization. It is outside Git.

### Harness requirements

1. Before importing reverse-agent, create the bounded temp directory and set both `TEMP` and `TMP` to it; explicitly set Python `tempfile.tempdir` to that exact directory.
2. Pin reverse-agent imports to the exact authority worktree and fail closed if the imported package is elsewhere.
3. Read the installed sanitized Product Setup bytes into memory only; never print/persist its full contents. Require the file exists. Preserve the bytes for post-run equality verification.
4. Construct `ModelProfileStore(state_path=<real Product Setup>)` and a disposable `TaskStore` at `<root>/runtime/tasks.sqlite3`; assert its resolved path is not the forbidden real TaskStore.
5. Set `REVERSE_AGENT_REPO_DIR=<root>/seed-repo` and `REVERSE_AGENT_TASK_WORKSPACE_ROOT=<root>/workspaces` in the trusted parent process.
6. Create `<root>/seed-repo` as a fresh local Git repository using structured local `git` commands only. Configure repository-local fake identity, create tracked `dogfood1_result.txt` with exact bytes `PENDING\n`, add and commit it, verify no remote is configured, and record the seed commit SHA.
7. Start `CombinedTrustedHost(store=<setup-backed store>, task_store=<disposable store>, execution_authority_sha=<authority>, planning_sha=<planning>)` on ephemeral ports with default `auth_list_probe=None`.
8. Before Task creation/execution, GET the public Connection and Binding. Require exact canonical identities, `secret_status=not_applicable`, and `external_session_status=executor_managed`. Do not call `/test`.
9. POST exactly one Task with executor `opencode`, the canonical Binding, orchestration `single`, branch equal to exact seed commit SHA, and the exact bounded marker-edit instruction. Require initial Task status `QUEUED`.
10. POST exactly one `/api/tasks/{id}/execute` with `validation_command_id=git_diff_check`. Set an in-harness boolean before sending; any attempted second call must raise locally and terminate without network activity.
11. Do not invoke OpenCode directly. The only permitted OpenCode child is the one launched by the product executor inside the single Task execution.
12. After the execute response returns, perform no retry regardless of status. Fetch the Task only through GET if needed for sanitized evidence.
13. On success require: status `READY_FOR_REVIEW`; validation exit 0; changed files exactly `dogfood1_result.txt`; execution worktree marker bytes exactly `DOGFOOD1_OK\n`; `git status --porcelain` shows only the expected tracked modification; no extra untracked files; runtime event metadata proves provider `sensetime`, model `sensetime/sensenova-6.7-flash-lite`, auth method `external_cli_session`, and exactly one OpenCode-start event.
14. Stop the host in `finally` for both success and failure.
15. Re-read only the installed sanitized Product Setup and require byte equality to the pre-run snapshot.
16. Inspect only `<root>/temp` for `opencode_prompt_*.txt`. Require at most one prompt file from the one run. Delete only that bounded file after host stop. Do not enumerate or clean system TEMP outside the evidence root.
17. Persist/report only sanitized evidence. Never persist raw OpenCode stdout/stderr, raw HTTP headers, environment dumps, Product Setup full contents, or any credential material.
18. Exit 0 only for full success; exit 20 for any bounded failure. Never retry.

### Required success terminal

`DOGFOOD1_ONE_SHOT_LIVE_ACCEPTED`

### Required blocked terminal

`DOGFOOD1_ONE_SHOT_LIVE_BLOCKED`

## Required report

Report only sanitized facts:
- planning SHA;
- authority SHA;
- transition terminal/blockers;
- Product Setup existed and pre/post bytes equal yes/no;
- pre-run public Connection/Binding fields and executor_managed status;
- disposable seed commit SHA;
- Task id/status before execute;
- Task execute request count (must be 1);
- OpenCode product-path launch count (must be 1 on a launched run);
- provider/model/auth-method event metadata;
- final task status;
- validation command/exit;
- changed files;
- marker exact bytes match yes/no;
- disposable worktree status;
- sanitized failure classification/detail if blocked;
- prompt temp files created count and cleaned yes/no;
- real TaskStore access NO;
- auth-list/models/version/login/logout NO;
- Connection `/test` NO;
- credential relay lease NO;
- Agent/harness credential access NO;
- manual OpenCode run NO;
- second execute/retry/resume/fallback NO;
- reverse-agent product repository mutation NO;
- dependency install NO;
- commit/push/PR/merge NO;
- authority worktree final status;
- final terminal.

STOP after the report for Owner audit.

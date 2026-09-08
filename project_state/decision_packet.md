# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260908_issue585_desktop0_tauri_r2_v7",
  "round_id": "round_20260908_issue585_desktop0_tauri_r2_v7",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FRESH_MAIN_DESKTOP0_TAURI_NATIVE_STARTUP_BRIDGE_R2_V7",
  "not_product_redesign": true,
  "follows_last_decision_id": "decision_20260908_issue585_desktop0_tauri_r2_v6",
  "follows_last_round_id": "round_20260908_issue585_desktop0_tauri_r2_v6",
  "previous_audit_outcome": "R2_V6_FAILED_CLOSED_BEFORE_PRODUCT_MUTATION_BECAUSE_FORBIDDEN_FRONTEND_GLOB_OVERLAPPED_AUTHORIZED_FRONTEND_PRODUCT_PATHS",
  "workstream_id": "issue585-desktop0-tauri-native-startup-bridge-r2-v7",
  "source_issue": 585,
  "parent_issue": 357,
  "integration_base_ref": "main",
  "base_sha": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "activation_base_sha": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "starting_head": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "required_branch": "owner/desktop0-tauri-r2-v7",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": true,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "test_semantics_changes_allowed": false,
  "source_test_mutation_authorized": false,
  "dependency_target_versions": {
    "@tauri-apps/cli": "2.11.4",
    "@tauri-apps/api": "2.11.1",
    "tauri": "2.11.5",
    "tauri-build": "2.6.3"
  },
  "cargo_repository_field": "https://github.com/dddd2024/Nerelan",
  "canonical_repository": "dddd2024/Nerelan",
  "historical_negative_authority": {
    "pr609_head": "fb4d54d7a146997dfd5decf224dab56dcb111781",
    "pr609_decision_commit": "dd4a72b695a3c23911b3184989bbc14adf4a35fb",
    "r2_v2_branch": "owner/desktop0-tauri-r2-v2",
    "r2_v3_issue": 600,
    "r2_v3_pr": 609,
    "r2_v4_branch": "owner/desktop0-tauri-r2-v4",
    "r2_v4_decision_commit": "e11735f3",
    "r2_v4_disposition": "TERMINAL_LOCAL_NEGATIVE_AUTHORITY_EVIDENCE_ONLY",
    "r2_v5_branch": "owner/desktop0-tauri-r2-v5",
    "r2_v5_decision_commit": "aec0d197",
    "r2_v5_disposition": "FAILED_TERMINAL_LOCAL_AUTHORITY_EVIDENCE_ONLY",
    "r2_v5_blocker": "active_pr_binding_mode = draft_pr_body_only is not a supported current literal",
    "r2_v6_branch": "owner/desktop0-tauri-r2-v6",
    "r2_v6_decision_commit": "7f532f28",
    "r2_v6_disposition": "FAILED_TERMINAL_LOCAL_AUTHORITY_EVIDENCE_ONLY",
    "r2_v6_blocker": "forbidden_mutated_paths contained frontend/** which glob-covered authorized frontend product paths",
    "no_cherry_pick_no_rebase_no_merge_no_force_update_no_history_reuse": true
  },
  "v6_terminal_evidence": {
    "decision_commit": "7f532f280200cf0b64999ed5701b3f2cca0f6e76",
    "result": "FAILED_TERMINAL_LOCAL_AUTHORITY_EVIDENCE_ONLY",
    "blocker": "forbidden_mutated_paths frontend/** glob-overlapped authorized frontend product paths",
    "root_cause": "forbidden_mutated_paths contained frontend/** which glob-covered authorized frontend paths"
  },
  "fresh_worktree_contract": {
    "creation_required": true,
    "source_commit": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
    "source_ref": "origin/main",
    "target_branch": "owner/desktop0-tauri-r2-v7",
    "no_switch_no_reset_no_stash_no_clean_other_worktree": true,
    "clean_status_required_at_activation": true
  },
  "semantic_implementation_contract": {
    "allowed_only_after_authorized": true,
    "webview_ipc_surface": "runtime_status | start_runtime | stop_runtime",
    "generic_shell_bridge_forbidden": true,
    "arbitrary_process_spawn_forbidden": true,
    "arbitrary_filesystem_bridge_forbidden": true,
    "powershell_execution_discrete_arg_required": true,
    "dev_up_ps1_unchanged": true,
    "dev_down_ps1_unchanged": true,
    "frontend_src_unchanged": true,
    "frontend_e2e_unchanged": true,
    "frontend_tests_unchanged": true,
    "frontend_vite_config_unchanged": true,
    "no_cherry_pick_pr609": true,
    "tauri_ipc_handlers": [
      "runtime_status",
      "start_runtime",
      "stop_runtime"
    ],
    "no_arbitrary_shell_bridge": true,
    "no_arbitrary_filesystem_bridge": true,
    "no_arbitrary_process_bridge": true,
    "dependency_versions": {
      "@tauri-apps/cli": "2.11.4",
      "@tauri-apps/api": "2.11.1",
      "tauri": "2.11.5",
      "tauri-build": "2.6.3"
    },
    "cargo_repository": "https://github.com/dddd2024/Nerelan",
    "powershell_discrete_arg_required": true,
    "dev_up_ps1_delta_none": true,
    "dev_down_ps1_delta_none": true,
    "frontend_src_delta_none": true,
    "frontend_e2e_delta_none": true,
    "frontend_tests_delta_none": true,
    "frontend_playwright_config_delta_none": true,
    "frontend_vite_config_delta_none": true,
    "github_workflows_delta_none": true,
    "pre_trust_workspace_execution_none": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "issue585_desktop0_v7.bootstrap_and_preflight",
      "command": "verify exact fresh locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and fresh isolated worktree branch merge-base; commit this immutable R2 Decision as the unique first commit; run startup snapshot transition command plan transition lint transition preflight pre and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any product mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue585_desktop0_v7.update_package_json",
      "command": "after PRE_EXECUTION_AUTHORIZED add @tauri-apps/cli 2.11.4 and @tauri-apps/api 2.11.1 to frontend/package.json devDependencies and dependencies respectively, update package-lock.json, and do not modify any other frontend file",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "commit", "package_install"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/package.json",
        "frontend/package-lock.json"
      ],
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v7.materialize_tauri_shell",
      "command": "after PRE_EXECUTION_AUTHORIZED create frontend/src-tauri on fresh main with Cargo.toml declaring tauri 2.11.5 tauri-build 2.6.3 and repository https://github.com/dddd2024/Nerelan plus build.rs src/main.rs src/lib.rs registering only runtime_status start_runtime stop_runtime through invoke_handler with no generic shell exec run_command API, tauri.conf.json, capabilities/default.json, generated bundle icons and .gitignore; do not modify frontend/src frontend/e2e frontend/tests dev-up.ps1 dev-down.ps1 frontend/vite.config.ts or any workflow",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/src-tauri/**"
      ],
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v7.rust_toolchain_if_missing",
      "command": "if rustc or cargo are absent after PRE_EXECUTION_AUTHORIZED provision only a current stable official Rust toolchain needed for cargo check using bounded official Rust distribution access in a user-scoped or temporary location outside repository state; do not install unrelated system packages do not read credentials and do not mutate repository files as part of toolchain provisioning",
      "phase": "implementation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["dependency_install", "local_static_check"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v7.validate",
      "command": "run npm --prefix frontend run typecheck, npm --prefix frontend test, npm --prefix frontend run build, npm --prefix frontend run tauri -- info, cargo check --manifest-path frontend/src-tauri/Cargo.toml, git diff --check plus targeted static audit proving invoke_handler registers only runtime_status start_runtime stop_runtime with no generic shell bridge and no pre-trust workspace execution; rerun transition-lint transition-command-plan transition-preflight --mode pre and worktree-publication-readiness on the exact implementation head; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["unit_test", "local_static_check", "diff_validation", "code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue585_desktop0_v7.publish",
      "command": "after all blocking validation passes push the exact branch owner/desktop0-tauri-r2-v7 to locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v7.exact_head_acceptance",
      "command": "require natural exact-head CI Decision Preflight State Gate and Tauri build lane on the Draft PR; keep the PR Draft and do NOT Ready or merge under this Decision",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src-tauri/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/vite.config.ts",
    "frontend/e2e/critical-user-journey.spec.ts",
    "docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/vite.config.ts",
    "frontend/e2e/critical-user-journey.spec.ts",
    "docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "README.md",
    "README.txt",
    "docs/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "tests/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "launch_nerelan.bat",
    "launch_reverse_agent.bat",
    "frontend/src/**",
    "frontend/e2e/**",
    "frontend/tests/**",
    "frontend/playwright.config.ts",
    "frontend/vite.config.ts",
    "requirements*.txt",
    "pyproject.toml",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/schemas/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/mainline_merge_intents/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready",
    "force_push",
    "rebase",
    "squash",
    "reset",
    "clean",
    "stash",
    "restore",
    "amend",
    "history_rewrite",
    "unknown_binary_execution",
    "secrets",
    "destructive_delete",
    "privileged_remote_execution",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "second_decision_commit",
    "second_command_runner",
    "active_json_rewrite",
    "product_replay",
    "ruleset_weakening",
    "required_check_weakening",
    "test_semantics_change",
    "reuse_v1_decision",
    "reuse_v2_decision",
    "reuse_v3_decision",
    "reuse_v4_decision",
    "reuse_v5_decision",
    "reuse_v6_decision",
    "rebase_v1",
    "rebase_v2",
    "rebase_v3",
    "rebase_v4",
    "rebase_v5",
    "rebase_v6",
    "continue_push_v1",
    "continue_push_v2",
    "continue_push_v3",
    "continue_push_v4",
    "continue_push_v5",
    "continue_push_v6",
    "force_update_v1",
    "force_update_v2",
    "force_update_v3",
    "force_update_v4",
    "force_update_v5",
    "force_update_v6",
    "reopen_v1",
    "reopen_v2",
    "reopen_v3",
    "reopen_v4",
    "reopen_v5",
    "reopen_v6",
    "local_authoring",
    "implicit_user_local_fallback",
    "cherry_pick_pr609",
    "generic_shell_bridge",
    "arbitrary_process_spawn",
    "arbitrary_filesystem_bridge",
    "arbitrary_environment_dump",
    "credential_access_via_webview",
    "pre_trust_workspace_execution",
    "frontend_src_mutation",
    "frontend_e2e_mutation",
    "frontend_tests_mutation",
    "dev_up_ps1_mutation",
    "dev_down_ps1_mutation",
    "github_workflows_mutation",
    "launcher_mutation",
    "test_file_mutation",
    "dependency_mutation_outside_allowlist"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [
      "after PRE_EXECUTION_AUTHORIZED add @tauri-apps/cli 2.11.4 and @tauri-apps/api 2.11.1 to frontend/package.json devDependencies and dependencies respectively, update package-lock.json, and do not modify any other frontend file",
      "if rustc or cargo are absent after PRE_EXECUTION_AUTHORIZED provision only a current stable official Rust toolchain needed for cargo check using bounded official Rust distribution access in a user-scoped or temporary location outside repository state; do not install unrelated system packages do not read credentials and do not mutate repository files as part of toolchain provisioning"
    ],
    "github_control_plane_network_exceptions": [
      "after all blocking validation passes push the exact branch owner/desktop0-tauri-r2-v7 to locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision"
    ],
    "user_local_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "frontend/package.json", "minimum_risk": "R2"},
    {"pattern": "frontend/package-lock.json", "minimum_risk": "R2"},
    {"pattern": "frontend/src-tauri/**", "minimum_risk": "R2"}
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src-tauri/**"
  ],
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "owner/desktop0-tauri-r2-v7",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  }
}
```

## Goal

Create a native Tauri desktop startup bridge for the Nerelan frontend, adding Tauri CLI and API dependencies to the frontend package, creating the `frontend/src-tauri/` directory with a Cargo project that registers only `runtime_status`, `start_runtime`, and `stop_runtime` IPC handlers, and publishing as a Draft PR against `main`.

## Remaining limitation

This Decision does not authorize any product redesign, workflow mutation, launcher modification, test file mutation, or any operation outside the `frontend/package.json`, `frontend/package-lock.json`, and `frontend/src-tauri/**` scope. The PR remains Draft until independent exact-head acceptance. No Ready, merge, tag, release, or deployment is authorized under this Decision.

## Execution policy

- This Decision is byte-immutable after its activation commit; any later edit to `project_state/decision_packet.md` fails closed and requires a new issue/round/branch/Decision rather than an in-place amendment.
- The v6 Decision commit `7f532f280200cf0b64999ed5701b3f2cca0f6e76` is terminal local negative evidence only. Do not amend, push, cherry-pick, rebase, or reuse it.
- PR609 head `fb4d54d7a146997dfd5decf224dab56dcb111781` is historical semantic evidence only. Do not cherry-pick it.
- Do not create a second governance gate; strengthen the existing transition, preflight, authority-collection, and publication-readiness surfaces.
- Do not execute the v2 through v6 worktrees; this round uses a fresh isolated worktree.
- Fail closed on any main drift, Decision mutation, scope contradiction, or unexplained test failure; stop and request a revised Work Item rather than widening this Decision.
- The `forbidden_mutated_paths` list does NOT contain `frontend/**` or `frontend/*`; forbidden paths are specific and non-overlapping with the allowed product paths. The `allowed_mutated_paths` list is the mutation boundary; any path outside the allowlist is caught by the `allowed_path_scope` check.
- All `execution_surface` values are from `CURRENT_AUTHORING_SURFACES` (`trusted_worker`, `github_control_plane`, `remote_observation`); the legacy `local` surface is never used.
- `active_pr_binding_mode` is `"none"`, which is the only supported cutover literal.

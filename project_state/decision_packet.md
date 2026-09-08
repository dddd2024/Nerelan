# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260908_issue585_desktop0_tauri_r2_v6",
  "round_id": "round_20260908_issue585_desktop0_tauri_r2_v6",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FRESH_MAIN_DESKTOP0_TAURI_NATIVE_STARTUP_BRIDGE_R2_V6",
  "not_product_redesign": true,
  "follows_last_decision_id": "decision_20260908_issue423_windows_platform_ci_r2_v3",
  "follows_last_round_id": "round_20260908_issue423_windows_platform_ci_r2_v3",
  "previous_audit_outcome": "R2_V5_FAILED_CLOSED_BEFORE_PRODUCT_MUTATION_BECAUSE_ACTIVE_PR_BINDING_MODE_DRAFT_PR_BODY_ONLY_IS_NOT_A_SUPPORTED_CURRENT_LITERAL",
  "workstream_id": "issue585-desktop0-tauri-native-startup-bridge-r2-v6",
  "source_issue": 585,
  "parent_issue": 357,
  "integration_base_ref": "main",
  "base_sha": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "activation_base_sha": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "starting_head": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
  "required_branch": "owner/desktop0-tauri-r2-v6",
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
  "historical_evidence_only": {
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
    "no_cherry_pick_no_rebase_no_merge_no_force_update_no_history_reuse": true
  },
  "v5_terminal_evidence": {
    "decision_commit": "aec0d197",
    "result": "FAILED_TERMINAL_LOCAL_AUTHORITY_EVIDENCE_ONLY",
    "blocker": "active_pr_binding_mode = draft_pr_body_only",
    "not_reused_as_authority": true,
    "no_amend_no_push_no_cherry_pick_no_rebase": true
  },
  "fresh_worktree_contract": {
    "creation_required": true,
    "source_commit": "5df08a23dbaa0e816f081b460ee6e2642004a2b1",
    "source_ref": "origin/owner/desktop0-tauri-r2-v6",
    "target_branch": "owner/desktop0-tauri-r2-v6",
    "no_reuse_of_v4_worktree": true,
    "no_reuse_of_v5_worktree": true,
    "no_switch_no_reset_no_stash_no_clean_other_worktree": true,
    "clean_status_required_at_activation": true
  },
  "execution_surface_contract": {
    "authoring_surface_truth": "reverse_agent/control_plane/command_authority.py CURRENT_AUTHORING_SURFACES and OPERATION_SURFACE_ADMISSIBILITY",
    "legacy_local_surface_used": false,
    "local_reserved_for_historical_legacy_compatibility_only": true,
    "bootstrap_and_preflight": "trusted_worker",
    "materialize_tauri_dependencies": "trusted_worker",
    "materialize_tauri_shell": "trusted_worker",
    "rust_toolchain_if_missing": "trusted_worker",
    "validate": "trusted_worker",
    "publish": "github_control_plane",
    "exact_head_acceptance": "remote_observation",
    "notes": "trusted_worker is the logical checked-out-repository execution surface and does not require a cloud host; the local Windows machine acting as the controlled executor of ordinary repository work in this isolated checkout is trusted_worker, not user_local. user_local is reserved for genuine machine-specific capability and would require machine_specific_execution, which this round does not need. GitHub publication is never a trusted_worker operation. Final read-only observation is remote_observation."
  },
  "semantic_implementation_contract": {
    "allowed_paths": ["frontend/package.json", "frontend/package-lock.json", "frontend/src-tauri/**"],
    "webview_ipc_commands": ["runtime_status", "start_runtime", "stop_runtime"],
    "no_generic_shell_exec_api": true,
    "no_execute_shell_no_run_command_no_exec_no_shell_no_spawn_arbitrary_binary": true,
    "no_arbitrary_file_read_or_write": true,
    "no_environment_dump_no_credential_access": true,
    "powershell_argument_boundaries_required": true,
    "powershell_executable": "powershell.exe",
    "no_concatenated_shell_command_string": true,
    "repository_path_from_trusted_backend_context": true,
    "no_execution_authority_from_webview_or_caller_cwd": true,
    "no_workspace_local_active_config_hook_mcp_or_project_local_executable_before_trust": true,
    "dev_up_invocation_minimum": ["-NoProfile", "-NonInteractive", "-NoLogo", "-ExecutionPolicy", "Bypass", "-File", "<repo>\\dev-up.ps1", "-NoBrowser", "-RepoDir", "<repo>"],
    "dev_down_invocation_minimum": ["-NoProfile", "-NonInteractive", "-NoLogo", "-ExecutionPolicy", "Bypass", "-File", "<repo>\\dev-down.ps1", "-RepoDir", "<repo>"],
    "dev_up_down_not_modified": true,
    "frontend_src_not_modified": true,
    "frontend_e2e_not_modified": true,
    "frontend_tests_not_modified": true,
    "workflow_not_modified": true,
    "no_browser_installation": true,
    "no_playwright_execution": true,
    "provider_model_calls_forbidden": true,
    "credential_access_forbidden": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "bounded read-only fetch of dddd2024/Nerelan to execute repository-owned local gate commands in the isolated owner/desktop0-tauri-r2-v6 checkout",
    "verify exact main base 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first new commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue585_desktop0_v6.bootstrap_and_preflight",
      "command": "verify exact fresh locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and fresh isolated worktree branch owner/desktop0-tauri-r2-v6 merge-base; commit this immutable R2 Decision as the unique first commit; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any dependency or product mutation",
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
      "command_id": "issue585_desktop0_v6.materialize_tauri_dependencies",
      "command": "after PRE_EXECUTION_AUTHORIZED add the DESKTOP-0 Tauri dependencies to frontend/package.json with dependencies @tauri-apps/api 2.11.1 devDependencies @tauri-apps/cli 2.11.4 and scripts.tauri set to tauri and refresh frontend/package-lock.json with matching lock entries using bounded official npm registry access; mutate no other path",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["dependency_install", "package_install", "source_edit"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/package.json",
        "frontend/package-lock.json"
      ],
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v6.materialize_tauri_shell",
      "command": "after PRE_EXECUTION_AUTHORIZED create frontend/src-tauri on fresh main with Cargo.toml declaring tauri 2.11.5 tauri-build 2.6.3 and repository https://github.com/dddd2024/Nerelan plus build.rs src/main.rs src/lib.rs registering only runtime_status start_runtime stop_runtime through invoke_handler with no generic shell exec run_command API, tauri.conf.json, capabilities/default.json, generated bundle icons and .gitignore; do not modify frontend/src, frontend/e2e, frontend/tests, dev-up.ps1, dev-down.ps1, frontend/vite.config.ts or any workflow",
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
      "command_id": "issue585_desktop0_v6.rust_toolchain_if_missing",
      "command": "if rustc or cargo are absent after PRE_EXECUTION_AUTHORIZED provision only a current stable official Rust toolchain needed for cargo check using bounded official Rust distribution access in a user-scoped or temporary location outside repository state; do not install unrelated system packages, do not read credentials, and do not mutate repository files as part of toolchain provisioning",
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
      "command_id": "issue585_desktop0_v6.validate",
      "command": "run npm --prefix frontend run typecheck, npm --prefix frontend test, npm --prefix frontend run build, npm --prefix frontend run tauri -- info, cargo check --manifest-path frontend/src-tauri/Cargo.toml, git diff --check plus targeted static audit proving invoke_handler registers only runtime_status start_runtime stop_runtime with no generic shell bridge and no pre-trust active workspace execution; rerun transition-lint, transition-command-plan, transition-preflight --mode pre and worktree-publication-readiness on the exact implementation head; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["unit_test", "build", "local_static_check", "diff_validation", "code_read"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue585_desktop0_v6.publish",
      "command": "after all blocking validation passes push the exact branch owner/desktop0-tauri-r2-v6 to locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and create exactly one Draft PR titled R2 v6: DESKTOP-0 Tauri native startup bridge (#585) with body recording the immutable R2 authority snapshot including Decision ID Round ID base SHA Decision commit SHA generated-governance commit SHA semantic commit SHA exact head SHA v5 aec0d197 terminal local negative authority evidence only and PR609 fb4d54d7 historical semantic evidence only plus changed paths dependency versions deterministic check results provider calls 0 credential access 0 browser execution 0 workflow mutation 0 READY NO MERGE NO; never mark Ready and never merge under this Decision",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pr_create"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue585_desktop0_v6.exact_head_acceptance",
      "command": "require natural exact-head GitHub Actions terminal success on the Draft PR; independently audit changed paths successful Rust cargo check evidence Tauri capability boundary immutable Decision chronology and locked base; keep the PR Draft and do NOT mark Ready and do NOT merge under this Decision",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_source_paths": [
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src-tauri/**"
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
    "reverse_agent/control_plane/command_authority.py"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/vite.config.ts",
    "frontend/e2e/critical-user-journey.spec.ts",
    "docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md",
    "reverse_agent/control_plane/command_authority.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "project_state/context/**",
    "project_state/evidence/**",
    "project_state/proposed_state/**",
    "project_state/domains/**",
    "project_state/jobs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/roadmap/**",
    "project_state/solve_tasks/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/evidence_source.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/local_seal.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/report_binding.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/__init__.py",
    "reverse_agent/platform_v1/**",
    "tests/**",
    "frontend/**",
    "docs/**",
    ".github/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "reset",
    "clean",
    "stash",
    "restore",
    "history_rewrite",
    "unknown_binary_execution",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "browser_execution",
    "arbitrary_webview_shell_bridge",
    "modify_dev_up",
    "modify_dev_down",
    "cherry_pick_pr609",
    "reuse_pr609_history",
    "cherry_pick_v5_decision",
    "amend_v5_decision",
    "push_v5_decision",
    "rebase_v5",
    "reuse_v5_history",
    "edit_v5_decision",
    "cherry_pick_v4_decision",
    "amend_v4_decision",
    "push_v4_decision",
    "rebase_v4",
    "reuse_v4_history",
    "edit_v4_decision",
    "workspace_local_active_config_hook_mcp_command_before_user_trust",
    "second_decision_commit",
    "second_command_runner",
    "active_json_rewrite",
    "product_replay",
    "ruleset_weakening",
    "required_check_weakening",
    "test_semantics_change",
    "dependency_mutation_outside_tauri_rust",
    "execution_surface_local_in_current_authoring"
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [
      "after PRE_EXECUTION_AUTHORIZED add the DESKTOP-0 Tauri dependencies to frontend/package.json with dependencies @tauri-apps/api 2.11.1 devDependencies @tauri-apps/cli 2.11.4 and scripts.tauri set to tauri and refresh frontend/package-lock.json with matching lock entries using bounded official npm registry access; mutate no other path",
      "if rustc or cargo are absent after PRE_EXECUTION_AUTHORIZED provision only a current stable official Rust toolchain needed for cargo check using bounded official Rust distribution access in a user-scoped or temporary location outside repository state; do not install unrelated system packages, do not read credentials, and do not mutate repository files as part of toolchain provisioning",
      "run npm --prefix frontend run typecheck, npm --prefix frontend test, npm --prefix frontend run build, npm --prefix frontend run tauri -- info, cargo check --manifest-path frontend/src-tauri/Cargo.toml, git diff --check plus targeted static audit proving invoke_handler registers only runtime_status start_runtime stop_runtime with no generic shell bridge and no pre-trust active workspace execution; rerun transition-lint, transition-command-plan, transition-preflight --mode pre and worktree-publication-readiness on the exact implementation head; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY"
    ],
    "github_control_plane_network_exceptions": [
      "after all blocking validation passes push the exact branch owner/desktop0-tauri-r2-v6 to locked main 5df08a23dbaa0e816f081b460ee6e2642004a2b1 and create exactly one Draft PR titled R2 v6: DESKTOP-0 Tauri native startup bridge (#585) with body recording the immutable R2 authority snapshot including Decision ID Round ID base SHA Decision commit SHA generated-governance commit SHA semantic commit SHA exact head SHA v5 aec0d197 terminal local negative authority evidence only and PR609 fb4d54d7 historical semantic evidence only plus changed paths dependency versions deterministic check results provider calls 0 credential access 0 browser execution 0 workflow mutation 0 READY NO MERGE NO; never mark Ready and never merge under this Decision"
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/package.json", "minimum_risk": "R2"},
    {"pattern": "frontend/package-lock.json", "minimum_risk": "R2"},
    {"pattern": "frontend/src-tauri/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
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
    "target_owner_branch": "owner/desktop0-tauri-r2-v6",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  },
  "success_terminal": "ISSUE585_R2_V6_DESKTOP0_TAURI_NATIVE_STARTUP_BRIDGE_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE585_R2_V6_DESKTOP0_TAURI_NATIVE_STARTUP_BRIDGE_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Reimplement the DESKTOP-0 Tauri native startup bridge on fresh `main` with the correct `active_pr_binding_mode = "none"` literal that the current `command_authority.py` machine gate supports. The v5 attempt failed because it used `active_pr_binding_mode = "draft_pr_body_only"` which is not a supported authored literal.

This Decision binds a Path-B R2 transition round to produce a Tauri shell on the Nerelan frontend with the exact dependency versions specified, a strictly bounded IPC surface (only `runtime_status`, `start_runtime`, `stop_runtime`), and a `powershell.exe`-only invocation path for `dev-up.ps1` with discrete argument binding. The round requires `PRE_EXECUTION_AUTHORIZED` and `PUBLICATION_READY` before any product mutation, deterministic validation on the exact semantic head, and a single Draft PR against `main`.

## Acceptance

1. `origin/main == 5df08a23dbaa0e816f081b460ee6e2642004a2b1` at activation; the branch `owner/desktop0-tauri-r2-v6` is rooted exactly at that SHA with merge-base equal to `base_sha`.
2. This Decision commit is the unique first new commit after `starting_head`; it is the only commit in `starting_head..HEAD` that modifies `project_state/decision_packet.md`; `HEAD:project_state/decision_packet.md` equals the activation-commit blob byte-for-byte for the lifetime of the branch.
3. `active_pr_binding_mode` is `"none"`; `mainline_merge_intent_required` is `false`. No `execution_surface = "local"` appears in any structured command. All repository checkout work uses `trusted_worker`; GitHub publication uses `github_control_plane`; final observation uses `remote_observation`.
4. `transition-lint`, `transition-command-plan`, `transition-preflight --mode pre`, and `worktree-publication-readiness` all pass with `PRE_EXECUTION_AUTHORIZED` and `PUBLICATION_READY` before any product mutation.
5. The `frontend/package.json` file is NOT listed in `reference_paths`, `reference_only_paths`, or `forbidden_mutated_paths`; it is only in `allowed_mutated_paths` and `allowed_source_paths`.
6. After all product and governance commits, `npm --prefix frontend run typecheck`, `npm --prefix frontend test`, `npm --prefix frontend run build`, `npm --prefix frontend run tauri -- info`, `cargo check --manifest-path frontend/src-tauri/Cargo.toml`, and `git diff --check` all pass.
7. The `invoke_handler` registers only `runtime_status`, `start_runtime`, and `stop_runtime`. No `execute_shell`, `run_command`, `exec`, arbitrary process spawn, arbitrary file read/write, environment dump, or credential access exists.
8. `dev-up.ps1`, `dev-down.ps1`, `frontend/src/**`, `frontend/e2e/**`, `frontend/tests/**`, `frontend/vite.config.ts`, `docs/**`, `.github/**`, `reverse_agent/**`, `tests/**`, `AGENTS.md`, `README*`, `pyproject.toml`, and `requirements*.txt` are unchanged.
9. Exactly one normal push of the exact branch and exactly one Draft PR against `main`; no mark-ready, merge, tag, release, runner dispatch, live model/provider call, credential access, force push, rebase, or history rewrite.
10. Fresh exact-head CI, State Gate, and Decision Preflight `pull_request` runs are observed; the round stops at `DRAFT_PR_READY_FOR_EXACT_HEAD_OWNER_AUDIT`.

## Execution policy

- This Decision is byte-immutable after its activation commit; any later edit to `project_state/decision_packet.md` fails closed and requires a new issue/round/branch/Decision rather than an in-place amendment.
- The v5 Decision commit `aec0d197` is terminal local negative evidence only. Do not amend, push, cherry-pick, rebase, or reuse it.
- PR609 head `fb4d54d7` is historical semantic evidence only. Do not cherry-pick it.
- Do not create a second governance gate; strengthen the existing transition, preflight, authority-collection, and publication-readiness surfaces.
- Do not execute the v4 or v5 worktrees; this round uses a fresh isolated worktree.
- Fail closed on any main drift, Decision mutation, scope contradiction, or unexplained test failure; stop and request a revised Work Item rather than widening this Decision.

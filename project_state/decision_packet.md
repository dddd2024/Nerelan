# Sidebar settings visibility repair v3

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261002_sidebar_settings_visibility_r3_v3",
  "round_id": "round_20261002_sidebar_settings_visibility_r3_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "FIX_USER_REPORTED_CLIPPED_SIDEBAR_SETTINGS_AND_VERIFY_ACTUAL_LOOPBACK_UI",
  "source_issue": 1027,
  "parent_issue": 1027,
  "approved_by": "dddd2024 via explicit Owner takeover delegation in this Codex chat",
  "approval_basis": "Owner delegated project decisions and now explicitly reported screenshot at127.0.0.1:4173 with bottom settings clipped. Fix only frontend layout and bounded real-browser visibility checks. Existing provider-free host sessions44587/95792 are owned by this chat, browser63514 remains preserved. This distinct immutable Decision supersedes startup-only for this bounded fix; old runtime Decision/branch/evidence are preserved. No changes to model/configuration/vault/dependencies/runtime business logic or task execution. Original composite junction/background launcher rejection remains binding; reuse existing dependency junction and foreground sessions only. Preserve v1 activation94bafe02 unchanged: typed push/draft operations were incorrectly marked user_local, command-plan blocked before any service stop, source edit or publication. Separate v2 corrects surface metadata under same user bug-fix request. Preserve v2 c00c7ab2 unchanged: code_read operation is incompatible with github_control_plane; v3 removes that operation from remote publication only, before tests/services/product changes. Read observations remain permitted by local machine-specific commands.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "required_branch": "codex/sidebar-settings-visibility-r3-v3-20261002",
  "workstream_id": "sidebar-settings-visibility-v3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 1,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "fresh_base": "9092911f41a089e249f27c883526904299be1d17",
  "current_main_expected": "9092911f41a089e249f27c883526904299be1d17",
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".platform_v1_runtime/**",
    "frontend/vite.config.ts.timestamp-*.mjs",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/index.css",
    "frontend/e2e/sidebar-settings-visibility.spec.ts"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".platform_v1_runtime/**",
    "frontend/vite.config.ts.timestamp-*.mjs",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/index.css",
    "frontend/e2e/sidebar-settings-visibility.spec.ts"
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
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "frontend/tests/**",
    "frontend/package*.json",
    "frontend/node_modules/**",
    "tests/**",
    "docs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
  ],
  "forbidden_operations": [
    "source_edit",
    "direct_push_main",
    "force_push",
    "rebase",
    "history_rewrite",
    "auto_merge",
    "tag_or_release",
    "workflow_rerun",
    "runner_dispatch",
    "model_api_invocation",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "dependency_install",
    "generated_governance_commit",
    "active_json_rewrite",
    "authority_pr_ready_or_merge",
    "target_branch_mutation",
    "push",
    "draft_pr",
    "mark_ready",
    "merge",
    "remote_branch_delete",
    "local_branch_delete",
    "worktree_reset_clean_stash",
    "worktree_remove_force",
    "process_termination",
    "shared_dependency_mutation",
    "shared_dependency_mutation",
    "existing_runtime_mutation",
    "worktree_removal",
    "autonomy_activation",
    "task_execution",
    "model_probe",
    "account_auth_probe"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/project_gate.py"
  ],
  "semantic_implementation_contract": {
    "specification": "Reuse F:/Nerelan-issue1027-frontend-audit and unchanged existing dependency junction. Fresh exact-main branch with Decision-only activation, actual preflight and PUBLICATION_READY and Draft before product edits. After gate, gracefully stop only confirmed owned frontend95792/backend44587 handles before source edits; preserve browser63514, runtime state and evidence. Start replacement installed Python/Node foreground sessions on same4173/8765/8766 with new host-local runtime .platform_v1_runtime/sidebar-settings-v1, autonomy/live-model disabled. At most one installed Edge Playwright browser launch to loopback; inspect actual rendered bounds/computed styles before correction, keep that same browser open for post-fix reload and desktop1440x1000/1920x950/1280x720/1024x600, collapsed rail, zoom-like increased font scale and mobile390x844 checks. Fix viewport/parent height or overflow only as evidence warrants; settings remains directly discoverable/clickable, nav middle can scroll, footer stays inside viewport and no new global hidden overflow. Existing semantic look/navigation remains. Add focused real-browser regression in exact allowed e2e file. No mock screenshot, model/provider/credential/config changes, installs, new dependency links, arbitrary policy/process changes or backlog task execution. Tool rejection stops operation.",
    "completion_boundary": "Real browser observes Settings visible and clicks through to settings on current user4173; screenshot/bounds and typecheck/focused relevant check/diff-check retained. Exact-head natural CI and independent acceptance remain pending if not observed. Keep Draft; no Ready/Merge/Issue closure."
  },
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
    "local_network_exceptions": [
      "Only loopback 127.0.0.1 frontend4173/model-control8765/task-api8766 and product-created ephemeral relay; provider/live probes disabled and autonomy disabled."
    ],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Only loopback 127.0.0.1 frontend4173/model-control8765/task-api8766 and product-created ephemeral relay; provider/live probes disabled and autonomy disabled."
    ],
    "github_control_plane_network_exceptions": [
      "Normal exact non-main branch push, one exact Draft against main909 and exact-head description updates/read-only natural CI; no comments, Ready/Merge, closure, rerun or dispatch."
    ]
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**",
      "frontend/node_modules/**",
      "frontend/vite.config.ts.timestamp-*.mjs"
    ],
    "stage_allowed": false,
    "note": "Existing node_modules junction is preserved read-only; new runtime/log metadata and Vite config cache are known scratch and never staged."
  },
  "allowed_commands": [
    {
      "command_id": "sidebar.bootstrap",
      "command": "Fresh exact-main branch in existing host preserving all old branches/runtime/junction; Decision-only LF commit; actual startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre/readiness; exact normal non-main activation push/Draft before edits. No generated gate staging.",
      "phase": "bootstrap",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "sidebar.runtime",
      "command": "After actual preflight stop only exact confirmed owned backend44587/frontend95792 handles gracefully; ordinary foreground replacements with inert settings/new runtime, same loopback ports. At most one installed Edge launch for before/after DOM bounds, click and screenshots; browser stays available across scoped edit. No unknown process stops, new dependency link or background launcher.",
      "phase": "implementation",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "sidebar.fix",
      "command": "Fix only observed layout bug in allowed frontend paths; focused real-browser regression and existing installed typecheck. Preserve user screenshot and before/after evidence, all unrelated product/API/configuration paths.",
      "phase": "implementation",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "unit_test",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/app-shell.tsx",
        "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
        "frontend/src/index.css",
        "frontend/e2e/sidebar-settings-visibility.spec.ts"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "sidebar.stage",
      "command": "Local scoped diff-check, typecheck and real browser regression; readiness and exact scoped staging/at most two product commits. No generated gate staging.",
      "phase": "validation",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "diff_validation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "sidebar.publish",
      "command": "At most three normal exact approved non-main branch pushes total, one activation Draft and exact-head descriptions, read-only natural CI. Local readiness/staging is separate. No comments/Ready/Merge/closure/rerun.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "workflow_profile": "baseline",
  "source_issues": [
    1027
  ],
  "follows_last_decision_id": "decision_20261002_sidebar_settings_visibility_r3_v2",
  "follows_last_round_id": "round_20261002_sidebar_settings_visibility_r3_v2"
}
```

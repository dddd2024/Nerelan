# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260905_issue503_visual_golden_r3_v1",
  "round_id": "round_20260905_issue503_visual_golden_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FRESH_MAIN_EIGHT_GOLDEN_VISUAL_ACCEPTANCE",
  "not_product_redesign": true,
  "follows_last_decision_id": "decision_20260904_issue156_postmerge_validator_cutover_r1_v2",
  "follows_last_round_id": "round_20260904_issue156_postmerge_validator_cutover_r1_v2",
  "previous_audit_outcome": "PR635_MERGED_MAIN_97A9C18;ISSUE381_COMPLETED;FRESH_MAIN_PLAYWRIGHT_RUN_33937230275_16_PASS_2_SKIP_8_VISUAL_ONLY_FAIL;ACTUAL_PNG_BYTES_OWNER_VISUALLY_ACCEPTED",
  "workstream_id": "issue503-visual-golden-r3-v1",
  "source_issue": 503,
  "parent_issue": 448,
  "integration_base_ref": "main",
  "base_sha": "97a9c18a8751e0f7ffd496b71883f51c009835ef",
  "activation_base_sha": "97a9c18a8751e0f7ffd496b71883f51c009835ef",
  "starting_head": "97a9c18a8751e0f7ffd496b71883f51c009835ef",
  "required_branch": "owner/issue503-visual-golden-r3-v1",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "semantic_replay_only": false,
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "workflow_profile": "browser_r3",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 4,
  "draft_pr_creation_limit": 1,
  "dependency_install_limit": 0,
  "browser_install_limit": 0,
  "browser_execution_limit": 0,
  "snapshot_update_limit": 1,
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
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "READ_ONLY_LANDING_CANDIDATE_VALIDATION",
  "landing_authority_scope_note": "This R3 Decision authorizes only the eight already-observed and Owner-reviewed Home/Settings PNG golden replacements. It does not authorize mark-ready or merge; landing remains separately governed after exact-head acceptance.",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": false,
  "source_test_mutation_authorized": false,
  "accepted_visual_evidence": {
    "source_run_id": 33937230275,
    "source_job_id": 101227405679,
    "artifact_id": 9960604836,
    "artifact_zip_sha256": "7345a815bdb1dec95571a128797f61582b420588dca485e8253e84e7719a74c4",
    "suite_result": {
      "total": 26,
      "passed": 16,
      "skipped": 2,
      "failed": 8
    },
    "failure_class": "FIXED_GOLDEN_MISMATCH_ONLY",
    "owner_same_viewport_visual_review": "ACCEPTED_CURRENT_TASK_FIRST_NERELAN_RENDERING",
    "accepted_snapshot_sha256": {
      "frontend/e2e/snapshots/desktop-chromium/home-light.png": "500a0a3918c94d027bf4dbe83a491edc9dc245a58e352dc075bad7a9ea5fd869",
      "frontend/e2e/snapshots/desktop-chromium/home-dark.png": "140b0dff6f3cf5d139d852a63adb4cbfd52865d9162a0bcfada79b6888f9cd01",
      "frontend/e2e/snapshots/desktop-chromium/settings-light.png": "c7f236675d70c88c8978fc9240d4b48645c6b55a3e18be3ee63eb19aabf5edcb",
      "frontend/e2e/snapshots/desktop-chromium/settings-dark.png": "c49bb2ea49192021a7283eecf054174ab88714e615879887f638667403e4e85a",
      "frontend/e2e/snapshots/mobile-chromium/home-light.png": "8821da7ffaec59891997cc02498c7b3f8a1b70ecf830be1bfc674c892d6de099",
      "frontend/e2e/snapshots/mobile-chromium/home-dark.png": "ab0225302346ffaef3fbe992d4ea6c238247a7056b961409233ed6916a86e56e",
      "frontend/e2e/snapshots/mobile-chromium/settings-light.png": "3e58ee1126fb7e51849299bb58416b0b93c3c87c47b04c4e0dffd64195e87877",
      "frontend/e2e/snapshots/mobile-chromium/settings-dark.png": "56848abfc843b93261d104caecf5f7c3dbfe52a31e3d048e8e283806b230a122"
    },
    "browser_lock": {
      "package": "@playwright/test",
      "package_version": "1.62.1",
      "browser_family": "chromium",
      "browser_title": "Chrome for Testing",
      "browser_version": "151.0.7922.34",
      "browser_revision": "1234",
      "runner_os": "ubuntu-24.04",
      "node_version": "22.23.1",
      "desktop_viewport": {
        "width": 1440,
        "height": 900
      },
      "mobile_viewport": {
        "width": 390,
        "height": 844
      },
      "workers": 1,
      "runtime_network_policy": "loopback_mock_only",
      "snapshot_update_in_ci": false
    }
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
    "verify exact fresh main 97a9c18a8751e0f7ffd496b71883f51c009835ef and fresh branch merge-base",
    "commit this immutable R3 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue503_r3v1.bootstrap_and_preflight",
      "command": "verify exact locked main 97a9c18a8751e0f7ffd496b71883f51c009835ef and branch owner/issue503-visual-golden-r3-v1; preserve the immutable Decision as the unique first commit; run repository-owned startup-snapshot transition-command-plan transition-lint transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any PNG mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "code_read",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ],
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue503_r3v1.materialize_accepted_goldens",
      "command": "after PRE_EXECUTION_AUTHORIZED obtain only GitHub Actions artifact 9960604836 from run 33937230275; verify artifact ZIP SHA256 7345a815bdb1dec95571a128797f61582b420588dca485e8253e84e7719a74c4; extract only the eight accepted *-actual.png files from test-results; verify every accepted per-file SHA256 frozen in this Decision; replace exactly the eight authorized Home/Settings snapshot PNGs; perform no browser execution or recapture and make exactly one product commit",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "source_edit",
        "local_static_check",
        "commit"
      ],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/e2e/snapshots/desktop-chromium/home-light.png",
        "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
        "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
        "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
        "frontend/e2e/snapshots/mobile-chromium/home-light.png",
        "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
        "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
        "frontend/e2e/snapshots/mobile-chromium/settings-dark.png"
      ]
    },
    {
      "command_id": "issue503_r3v1.validate_and_publish",
      "command": "verify git diff from locked base changes only the eight authorized snapshot PNGs plus compiler-owned governance artifacts; verify all eight PNG SHA256 values equal the frozen accepted manifest; run git diff --check and repository-owned transition-lint transition-command-plan transition-preflight --mode pre plus worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY; then push only the exact fresh branch and create exactly one Draft PR against locked main; do not mark Ready merge rerun or dispatch workflows",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check",
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue503_r3v1.exact_head_acceptance",
      "command": "observe natural exact-head CI Decision Preflight State Gate Model Access and Frontend Playwright on the Draft PR; require all trusted workflows terminal success and Frontend Playwright 24 passed 2 skipped 0 failed on 26 total; independently audit that only the eight frozen PNGs and compiler-owned governance artifacts changed; keep the PR Draft and do not mark Ready or merge",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit"
      ],
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
    "frontend/e2e/snapshots/desktop-chromium/home-light.png",
    "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/home-light.png",
    "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-dark.png"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "frontend/e2e/visual.spec.ts",
    "frontend/playwright.config.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/**"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "frontend/e2e/visual.spec.ts",
    "frontend/playwright.config.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/**"
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
    "docs/**",
    ".codex-skills/**",
    ".github/workflows/**",
    "frontend/src/**",
    "frontend/e2e/visual.spec.ts",
    "frontend/e2e/fixtures.ts",
    "frontend/e2e/lifecycle-visual.spec.ts",
    "frontend/playwright.config.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/design-qa.md",
    "reverse_agent/**",
    "tests/**",
    "scripts/**",
    "provider/**",
    "model/**",
    "credential/**",
    "requirements*.txt",
    "pyproject.toml",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "README.md",
    "README.txt",
    "**/STOP",
    "**/owner_handoffs/**"
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
    "dependency_install",
    "browser_execution",
    "browser_install",
    "arbitrary_remote_browsing",
    "external_url_navigation",
    "second_decision_commit",
    "second_command_runner",
    "active_json_rewrite",
    "product_replay",
    "desktop_reanchor",
    "ruleset_weakening",
    "required_check_weakening",
    "production_frontend_mutation",
    "test_semantics_change",
    "visual_spec_mutation",
    "playwright_config_mutation",
    "snapshot_recapture"
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
    "local_network_exceptions": [
      "after PRE_EXECUTION_AUTHORIZED obtain only GitHub Actions artifact 9960604836 from run 33937230275; verify artifact ZIP SHA256 7345a815bdb1dec95571a128797f61582b420588dca485e8253e84e7719a74c4; extract only the eight accepted *-actual.png files from test-results; verify every accepted per-file SHA256 frozen in this Decision; replace exactly the eight authorized Home/Settings snapshot PNGs; perform no browser execution or recapture and make exactly one product commit",
      "verify git diff from locked base changes only the eight authorized snapshot PNGs plus compiler-owned governance artifacts; verify all eight PNG SHA256 values equal the frozen accepted manifest; run git diff --check and repository-owned transition-lint transition-command-plan transition-preflight --mode pre plus worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY; then push only the exact fresh branch and create exactly one Draft PR against locked main; do not mark Ready merge rerun or dispatch workflows"
    ],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [],
    "user_local_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {
      "pattern": "frontend/e2e/snapshots/desktop-chromium/home-light.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/mobile-chromium/home-light.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
      "minimum_risk": "R3"
    },
    {
      "pattern": "frontend/e2e/snapshots/mobile-chromium/settings-dark.png",
      "minimum_risk": "R3"
    }
  ]
}
```

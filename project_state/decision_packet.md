# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue343_playwright_recovery_r3_v2",
  "round_id": "round_20260824_issue343_playwright_recovery_r3_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue334_visual_playwright_r3_v1",
  "follows_last_round_id": "round_20260824_issue334_visual_playwright_r3_v1",
  "previous_audit_outcome": "PR341_BLOCKED_CI_PLATFORM_V1_AND_MODEL_ACCESS_HEAD_22e4ffb0873f11d8caf82d503e41b1cd9213a396",
  "workstream_id": "issue343-playwright-recovery-r3-v2",
  "source_issue": 343,
  "parent_issue": 334,
  "superseded_source_pr": 341,
  "superseded_source_head_sha": "22e4ffb0873f11d8caf82d503e41b1cd9213a396",
  "superseded_source_audit_comment_id": 5393527771,
  "accepted_source_pr": 340,
  "accepted_source_head_sha": "96e7305b801a3f63847f6e9733d1855dd9923c38",
  "accepted_source_base_sha": "dbf714c228ca470a19bdf971d1f38ad237cba0c5",
  "accepted_source_audit_comment_id": 5392278514,
  "integration_base_ref": "main",
  "base_sha": "af0bfdb62d96e00b5f89660390950f3b7f096026",
  "activation_base_sha": "af0bfdb62d96e00b5f89660390950f3b7f096026",
  "starting_head": "af0bfdb62d96e00b5f89660390950f3b7f096026",
  "required_branch": "owner/issue343-playwright-recovery-r3-v2",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "product_replay_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "dependency_install_limit": 1,
  "browser_install_limit": 1,
  "browser_execution_limit": 12,
  "docker_image_pull_limit": 1,
  "docker_execution_limit": 3,
  "snapshot_update_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": true,
  "known_browser_execution_allowed": true,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "browser_lock": {
    "package": "@playwright/test",
    "package_version": "1.62.1",
    "browser_family": "chromium",
    "browser_channel": "chromium",
    "browser_title": "Chrome for Testing",
    "browser_version": "151.0.7922.34",
    "browser_revision": "1234",
    "runner_os": "ubuntu-24.04",
    "node_version": "22.23.1",
    "install_command_local": "npx playwright install --no-shell chromium",
    "install_command_ci": "npx playwright install --with-deps --no-shell chromium",
    "official_container_candidate": "mcr.microsoft.com/playwright:v1.62.1-noble",
    "desktop_viewport": {"width": 1440, "height": 900},
    "mobile_viewport": {"width": 390, "height": 844},
    "workers": 1,
    "fully_parallel": false,
    "retries": 0,
    "trace": "retain-on-failure",
    "screenshot": "only-on-failure",
    "video": "off",
    "base_url": "http://127.0.0.1:4173",
    "web_server_command": "npm run dev:mock -- --host 127.0.0.1 --port 4173 --strictPort",
    "runtime_network_policy": "loopback_data_blob_only",
    "snapshot_update_in_ci": false
  },
  "superseded_source_replay": {
    "source_ref": "22e4ffb0873f11d8caf82d503e41b1cd9213a396",
    "source_frontend_tree": "afd47805fae97c5835e91703eceb78a0c8fb3ac9",
    "blob_equal_paths": [
      ".github/workflows/frontend-playwright.yml",
      "frontend/.gitignore",
      "frontend/design-qa.md",
      "frontend/playwright.config.ts",
      "frontend/e2e/fixtures.ts",
      "frontend/e2e/home.spec.ts",
      "frontend/e2e/theme.spec.ts",
      "frontend/e2e/navigation.spec.ts",
      "frontend/e2e/goal.spec.ts",
      "frontend/e2e/runs.spec.ts",
      "frontend/e2e/states.spec.ts",
      "frontend/e2e/errors.spec.ts",
      "frontend/e2e/visual.spec.ts",
      "frontend/e2e/snapshots/desktop-chromium/home-light.png",
      "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
      "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
      "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
      "frontend/e2e/snapshots/mobile-chromium/home-light.png",
      "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
      "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
      "frontend/e2e/snapshots/mobile-chromium/settings-dark.png",
      "tests/test_ci_responsibility.py"
    ],
    "dirty_worktree_import_allowed": false,
    "cherry_pick_allowed": false,
    "bounded_visual_qa_repairs_after_replay_allowed": false
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
    "verify exact main base branch merge-base superseded PR341 source and no remote branch collision",
    "commit this immutable R3 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue343_r3v2.bootstrap",
      "command": "verify locked base and fresh branch; commit Decision first; generate five gates and require PRE_EXECUTION_AUTHORIZED",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["code_read", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue343_r3v2.merge_intent_boundary_fix",
      "command": "repair tests/platform_v1/test_merge_intent.py active Decision risk-tier assertion to accept exactly the production Path-B tiers R2 and R3 derived from repository production constants, rejecting R1 unknown and malformed tiers, without weakening exact base head Decision merge-method or immutability checks",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/platform_v1/test_merge_intent.py"
      ]
    },
    {
      "command_id": "issue343_r3v2.vitest_boundary_fix",
      "command": "add an explicit Vitest unit and component test boundary in frontend/vite.config.ts that excludes frontend/e2e from ordinary npm test collection while dedicated Playwright commands remain the only e2e runner",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/vite.config.ts"
      ]
    },
    {
      "command_id": "issue343_r3v2.playwright_replay",
      "command": "replay the governed frontend Playwright acceptance layer from superseded PR341 head 22e4ffb0 with blob equality: workflow, config, eight official Chromium specs, fixtures, eight fixed snapshots, dependency manifests and design-qa record; install exact Playwright dependency and official Chromium; run bounded local functional QA only against loopback",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "workflow_change", "dependency_change", "network_access", "execute_binary", "local_static_check", "commit"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        ".github/workflows/frontend-playwright.yml",
        "tests/test_ci_responsibility.py",
        "frontend/.gitignore",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/playwright.config.ts",
        "frontend/design-qa.md",
        "frontend/e2e/fixtures.ts",
        "frontend/e2e/home.spec.ts",
        "frontend/e2e/theme.spec.ts",
        "frontend/e2e/navigation.spec.ts",
        "frontend/e2e/goal.spec.ts",
        "frontend/e2e/runs.spec.ts",
        "frontend/e2e/states.spec.ts",
        "frontend/e2e/errors.spec.ts",
        "frontend/e2e/visual.spec.ts",
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
      "command_id": "issue343_r3v2.validate_and_publish",
      "command": "run deterministic frontend unit suite proving the e2e collection boundary, platform_v1 merge-intent suite proving the Path-B tier fix, typecheck lint build and build:mock; commit implementation; push exact branch and create one Draft PR",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "lint", "local_static_check", "commit", "push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue343_r3v2.bind_intent",
      "command": "after the real Draft PR number is known archive current active intent byte-identically as archive/pr338_v1.json and bind active.json schema v2 to the exact new PR base Decision and Command Plan",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr338_v1.json"
      ]
    },
    {
      "command_id": "issue343_r3v2.final_push_and_audit",
      "command": "push the final intent binding and require exact-head CI Decision Preflight State Gate Model Access and Frontend Playwright terminal success plus independent audit while the PR remains Draft",
      "phase": "audit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "push", "network_access", "read_only_audit"],
      "network_access": true,
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr338_v1.json",
    ".github/workflows/frontend-playwright.yml",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_merge_intent.py",
    "frontend/.gitignore",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/playwright.config.ts",
    "frontend/design-qa.md",
    "frontend/vite.config.ts",
    "frontend/e2e/fixtures.ts",
    "frontend/e2e/home.spec.ts",
    "frontend/e2e/theme.spec.ts",
    "frontend/e2e/navigation.spec.ts",
    "frontend/e2e/goal.spec.ts",
    "frontend/e2e/runs.spec.ts",
    "frontend/e2e/states.spec.ts",
    "frontend/e2e/errors.spec.ts",
    "frontend/e2e/visual.spec.ts",
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
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/platform_v1/contracts.py",
    "project_state/schemas/**",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/model-access.yml",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/run-client.ts",
    "frontend/src/fixtures/**"
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
    "reverse_agent/**",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/model-access.yml",
    "frontend/src/**",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/run-client.ts",
    "frontend/src/fixtures/**",
    "project_state/schemas/**",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete", "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_comment", "pull_request_close",
    "snapshot_update_in_ci", "arbitrary_remote_browsing", "external_url_navigation", "offensive_security_or_network_attack_work",
    "cherry_pick_pr341", "import_pr341_history", "import_dirty_worktree", "modify_pr341", "second_decision_commit",
    "unrestricted_risk_tier_assertion", "weaken_exact_base_head_decision_merge_method_or_immutability_checks",
    "skip_model_access_frontend_tests", "silent_ignore_playwright_failures", "second_e2e_runner", "broad_dependency_change"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": true,
    "known_binary_execution_allowed": true,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_comment_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "publication_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "install exact Playwright dependency and official Chromium; replay the governed e2e layer from superseded PR341 head with blob equality; run bounded local functional QA only against loopback",
      "run deterministic frontend unit suite proving the e2e collection boundary, platform_v1 merge-intent suite proving the Path-B tier fix, typecheck lint build and build:mock; commit implementation; push exact branch and create one Draft PR",
      "push the final intent binding and require exact-head CI Decision Preflight State Gate Model Access and Frontend Playwright terminal success plus independent audit while the PR remains Draft"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "frontend/package*.json", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/e2e/snapshots/**", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    ".github/workflows/frontend-playwright.yml",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr338_v1.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R3",
  "success_terminal": "ISSUE343_R3_RECOVERY_AND_OFFICIAL_CHROMIUM_ACCEPTANCE_DRAFT_ACCEPTED_FOR_OWNER_LANDING",
  "blocked_terminal": "ISSUE343_R3_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Recover the blocked #334 Slice-B round exactly as scoped by Issue #343: repair the two confirmed integration defects — the active merge-intent regression that hard-codes Path-B as R2, and the ordinary Vitest collection boundary that consumes Playwright E2E specs — without weakening any exact base/head/Decision/merge-method/immutability check, then replay the governed frontend Playwright acceptance layer from the superseded PR #341 head `22e4ffb0873f11d8caf82d503e41b1cd9213a396` onto locked current main `af0bfdb62d96e00b5f89660390950f3b7f096026` (which already carries the accepted PR #340 visual foundation), bind the resulting Draft PR to a schema-v2 merge intent, and stop for owner landing after exact-head checks and independent audit accept. The superseded PR #341 head remains preserved byte-for-byte as negative evidence.

## Acceptance

1. This Decision is the unique immutable first commit from `main@af0bfdb62d96e00b5f89660390950f3b7f096026`; all later implementation descends from it.
2. `tests/platform_v1/test_merge_intent.py` accepts legitimate R2 and R3 active mainline Decisions through repository production risk-tier semantics, while R1, missing, unknown or malformed tiers remain fail-closed; no exact base/head/Decision/merge-method/immutability assertion is weakened and no unrestricted string check is introduced.
3. `npm --prefix frontend test` runs only Vitest-owned unit/component suites and does not collect `frontend/e2e/**`; dedicated Playwright commands and the Frontend Playwright workflow remain the only E2E runner; Model Access frontend tests, typecheck, lint, production build and mock build all pass again.
4. The e2e infrastructure replays blob-equal from superseded PR #341 head `22e4ffb0873f11d8caf82d503e41b1cd9213a396`; only `@playwright/test@1.62.1` and bundled full Chromium Chrome for Testing `151.0.7922.34` may run, confined to `127.0.0.1:4173`, `data:` and `blob:`.
5. Blocking CI, State Gate, Decision Preflight, Model Access and Frontend Playwright reach terminal success on the successor exact head.
6. No new test framework, second governance gate, second runtime truth or broad dependency change is introduced; no production `reverse_agent/**` source changes.
7. The superseded PR #341 head `22e4ffb0873f11d8caf82d503e41b1cd9213a396` is never rewritten, rerun or marked clean; it remains negative evidence and is closed only as superseded after this successor lands.
8. One Draft PR is created and intent-bound; exact-head checks and independent audit accept; it remains Draft until the owner performs the audited landing.

## Execution policy

- Use file-level replay from the superseded source ref; never cherry-pick, never import PR #341 history, never consume the dirty root worktree.
- Stage only exact allowed paths. Never reset, clean, stash, restore, amend, rebase, squash or force push.
- Downloads are exact and bounded to npm and the Microsoft Playwright CDN. Browser runtime remains loopback-only.
- Snapshot update occurs at most once and only in the fixed Ubuntu-matched environment; never in CI. The eight replayed snapshots are used exactly as committed.
- Keep the PR Draft. Agent comment, attestation, ready and merge remain prohibited; owner landing follows independent audit under this Decision's bounded scope.

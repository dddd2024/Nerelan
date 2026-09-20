# Approved explicit user_local F03 reviewed source and Ubuntu goldens v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260920_issue913_reviewed_goldens_r3_v2",
  "round_id": "round_20260920_issue913_reviewed_goldens_r3_v2",
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
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "F03_EXACT_REVIEWED_SOURCE_AND_UBUNTU_GOLDEN_REUSE",
  "source_issue": 913,
  "parent_issue": 653,
  "approved_by": "dddd2024 via explicit delegated Owner execution",
  "approval_basis": "User explicitly delegated full Owner completion and independent subagent audits. Current main8fb171e6a395caf5c757bb44d43acf34bf06c03a passed actual postmerge acceptance5747578095;931 is closed. Independent913 feasibility, interface, final7commandcandidate audits accepted the supported explicituser_local route before activation. Revised913 planning was owner-published and read back; it is context only, while this immutableAPPROVEDDecision is the bounded execution authority. Historical914 and847 failures and prior Decisions remain unchanged.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "activation_base_sha": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "starting_head": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "fresh_base": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "current_main_expected": "8fb171e6a395caf5c757bb44d43acf34bf06c03a",
  "required_branch": "codex/f03-reviewed-goldens-r3-v2-20260920",
  "workstream_id": "issue913-f03-reviewed-goldens-r3-v2",
  "follows_last_decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "follows_last_round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
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
    "docs/functional-validation.md",
    "frontend/e2e/functional-validation.spec.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/goal-current-activity.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/components/theme-selector.tsx",
    "frontend/src/index.css",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/tests/goal-completion-evidence.test.tsx",
    "frontend/tests/goal-progress.test.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/roadmap.test.tsx",
    "frontend/tests/task-first-lifecycle-states.test.tsx",
    "frontend/e2e/snapshots/desktop-chromium/home-light.png",
    "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/home-light.png",
    "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-dark.png",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "docs/functional-validation.md",
    "frontend/e2e/functional-validation.spec.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/goal-current-activity.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/components/theme-selector.tsx",
    "frontend/src/index.css",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/tests/goal-completion-evidence.test.tsx",
    "frontend/tests/goal-progress.test.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/roadmap.test.tsx",
    "frontend/tests/task-first-lifecycle-states.test.tsx",
    "frontend/e2e/snapshots/desktop-chromium/home-light.png",
    "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
    "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/home-light.png",
    "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
    "frontend/e2e/snapshots/mobile-chromium/settings-dark.png",
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
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/tests/goal-continuation-activation-errors.test.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/tests/goal-continuation-activation-errors.test.ts",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "local_browser_execution",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Materialize exactly23reviewed847source blobs and8frozenUbuntuactualPNG bytes on freshbase. No semantic adaptation, dependency/workflow/assertion/threshold changes. Preserve current931activationerrors behavior and all unrelated edits. New source provenance is actual Windows user_local, not trusted_worker.",
    "completion_boundary": "Draft-only exacthead acceptance after all localdeterministic and5naturalbrowser_r3 workflows, actual diagnostic exit0/nativeJUnit0, independent review. No landing/Issueclosure in this round. Old847/914 remainnegativechronology; no new Windowsbrowser evidence is claimed."
  },
  "reference_product_head": "7d517b2d84b47c724f3df2218f9b94c02013726e",
  "reference_product_base": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "reference_product_blobs": {
    "docs/functional-validation.md": "63cd425d669f895f3f0c767e0ded255ffe8fbe6b",
    "frontend/e2e/functional-validation.spec.ts": "d010279ca5d4d8a1fbf82730f4110ed979ae271c",
    "frontend/src/components/connection-binding-editor.tsx": "280f50dcf3976c84ca6892d7ba2930c98b15cc0c",
    "frontend/src/components/functional-validation.tsx": "ad8518bec8dfbdaf4d3c7df9b2f8dfa427c8b014",
    "frontend/src/components/goal-composer.tsx": "817916489cccd463686860103b88c7fc9d68389f",
    "frontend/src/components/goal-current-activity.tsx": "91c5390649b33bbd054dea81936ec1734104acdc",
    "frontend/src/components/goal-progress.tsx": "77230adce3289e28409ad6e74ed99b3ffc33961c",
    "frontend/src/components/theme-selector.tsx": "17dc3a0d9363b399bdcf3e68e1721c54ea878c0f",
    "frontend/src/index.css": "81c72a660782bd14377ea8f329ddfb1bb6192013",
    "frontend/src/lib/functional-validation.ts": "a11d55e6f75f79aaf35afac9a9981980c1613749",
    "frontend/src/lib/platform-client.ts": "8b08d357b382be763b23d59914407a0ea44a3e75",
    "frontend/src/routes/approvals.tsx": "0d0d537e76aeb940c3f7ab71d938eb58f3bf1d03",
    "frontend/src/routes/home.tsx": "3afaa77629ac7c0add01fb895f0feef77fd6b8bc",
    "frontend/src/routes/roadmap.tsx": "0872355f4dc5b54a2f94bc6019a265a9058086a5",
    "frontend/src/routes/runs.tsx": "441531971ceb8c408a2da0fd90f9d63ebbcd7eae",
    "frontend/src/routes/settings.tsx": "944ded2aa28987a83d91aad06c459bc02e817f00",
    "frontend/tests/approvals.test.tsx": "a13de082577be79f9f61ff29d7c602a9e67b484e",
    "frontend/tests/functional-validation.test.tsx": "dc72f43ba45f5179423a744c89ef76d3465aef98",
    "frontend/tests/goal-completion-evidence.test.tsx": "c1308dccadb30db4a9f07dc3b891aef4ef6386df",
    "frontend/tests/goal-progress.test.tsx": "f0f90e7c44fae0f2728f987e4a30ad314ec70278",
    "frontend/tests/platform-home.test.tsx": "05abbcfda1135e9cf0dd83cc4b141fa788a7d745",
    "frontend/tests/roadmap.test.tsx": "14d6d72f5d5f21d8b921d3df112322b099fe1a37",
    "frontend/tests/task-first-lifecycle-states.test.tsx": "ca162428692cfdece43ab1e00836ea0590d7bf1d"
  },
  "reference_golden_hashes": {
    "frontend/e2e/snapshots/desktop-chromium/home-light.png": "689e60b0471b901dd1b99e50ff12d50a0afb7f9bda232888702b0a6e84f42c50",
    "frontend/e2e/snapshots/desktop-chromium/home-dark.png": "8b008e1663581d696553caa25ec8610b8e2e5a5a6df4352ca69459a9dadaefd9",
    "frontend/e2e/snapshots/desktop-chromium/settings-light.png": "ba6a593f268f051ef6546e1ecff21cfd16376143d4b1f24176e57a7152dadc2d",
    "frontend/e2e/snapshots/desktop-chromium/settings-dark.png": "cc9cf3b5f9977db3bcc00a0b8569c7e03514a67dc432d881557864f03a9c2c12",
    "frontend/e2e/snapshots/mobile-chromium/home-light.png": "8ba705e6700335ef354cace5214fdad2b5672eb73528f77e00cc17efce355bd5",
    "frontend/e2e/snapshots/mobile-chromium/home-dark.png": "79c169bfdbffa339ef32688774b912a8880cc63042123fc419ca90576b1ef7f7",
    "frontend/e2e/snapshots/mobile-chromium/settings-light.png": "05e0ca5d55bbb8540d0a7e762737b51c80026cf94db1e66e3f7eaf18fdcf237d",
    "frontend/e2e/snapshots/mobile-chromium/settings-dark.png": "eb69f172446e1db6a02e3d5bdb2b323380b86b01d42c8614c619b499e4116b78"
  },
  "reference_artifact": {
    "id": 10294643559,
    "run_id": 34684057222,
    "sha256": "0ae1bfbc2d9e27ea686a45d5836e820a06feceba7ff08060d09c2e903f61db39"
  },
  "runtime_scratch_policy": {
    "paths": [
      "frontend/node_modules/**",
      "frontend/dist/**",
      "frontend/.pytest_cache/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Only existingtool normal ignored outputs; compatible ignorednode_modules copied from F:/Nerelan-issue931-activation-error-v4/frontend/node_modules after exact package+lock equality. No install,trackeddependencyedit or cleanup."
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
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Only unchanged existing natural workflows provider-free dependencies/tests; no added workflow, manual dispatch or rerun."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Only existing scoped backendtest fixtures may bind isolated ephemeral127.0.0.1 and use fake Git/SQLite/model/binding doubles. No externalprovider/browser/credential/network."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical dddd2024/Nerelan Git API publish identical locally created2commitgraph/ref to exactnamedbranch andoneDraft; bounded evidence comments only913/newDraft/653/659. No Ready/merge/other refs."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue913v2.bootstrap",
      "command": "Create fresh full Windows checkout F:/Nerelan-issue913-reviewed-goldens-v2 from exact lockedbase after main966 postmergeacceptance. Verify clean tree/localGitidentity,31pathcollision/ownership and allfrozenblob/archive/PNG identities. Commit only thisAPPROVEDDecision once. Sequential startup-snapshot,transition-command-plan,transition-lint,transition-preflight --mode pre must reach PRE_EXECUTION_AUTHORIZED; worktree-publication-readiness must pass before source mutation. KnownGit/Python only; no copiedgates/history.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
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
      "command_id": "issue913v2.materialize",
      "command": "Afterpreflight materializeexact23sourceGitblobs from frozen847head and8frozenPNGbytes from verifiedartifact. Recheck SHA/blob identities anddiffexact31paths. No semanticediting/fixup. One productcommit only, separate fromDecisionactivation. Windows user_local sourceprovenance; never GitHubside sourceediting.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "docs/functional-validation.md",
        "frontend/e2e/functional-validation.spec.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/components/functional-validation.tsx",
        "frontend/src/components/goal-composer.tsx",
        "frontend/src/components/goal-current-activity.tsx",
        "frontend/src/components/goal-progress.tsx",
        "frontend/src/components/theme-selector.tsx",
        "frontend/src/index.css",
        "frontend/src/lib/functional-validation.ts",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/routes/approvals.tsx",
        "frontend/src/routes/home.tsx",
        "frontend/src/routes/roadmap.tsx",
        "frontend/src/routes/runs.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/approvals.test.tsx",
        "frontend/tests/functional-validation.test.tsx",
        "frontend/tests/goal-completion-evidence.test.tsx",
        "frontend/tests/goal-progress.test.tsx",
        "frontend/tests/platform-home.test.tsx",
        "frontend/tests/roadmap.test.tsx",
        "frontend/tests/task-first-lifecycle-states.test.tsx",
        "frontend/e2e/snapshots/desktop-chromium/home-light.png",
        "frontend/e2e/snapshots/desktop-chromium/home-dark.png",
        "frontend/e2e/snapshots/desktop-chromium/settings-light.png",
        "frontend/e2e/snapshots/desktop-chromium/settings-dark.png",
        "frontend/e2e/snapshots/mobile-chromium/home-light.png",
        "frontend/e2e/snapshots/mobile-chromium/home-dark.png",
        "frontend/e2e/snapshots/mobile-chromium/settings-light.png",
        "frontend/e2e/snapshots/mobile-chromium/settings-dark.png"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue913v2.dependencies",
      "command": "Use existing Node/npm/Python/Git. Verify currentfrontendpackage.json andpackage-lock exactbytes against F:/Nerelan-issue931-activation-error-v4. Copyonly matchingexistingignoredfrontendnode_modules into thisfreshworktree; no dependencyinstallation/download/lockfilechange. Do notstage ignoredcache or buildoutputs.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue913v2.validate",
      "command": "On exactcommittedimplementation head run frontend npm test, npm run lint, npm run typecheck, npm run build. Run python -B -m pytest tests/platform_v1/test_goal_completion_evidence.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_run_read_model.py -q -p no:cacheprovider; theseexisting fixtures only may use isolatedloopbackGit/SQLite/pytest andfakebinding/model doubles. No actualmodel/provider calls. Preserve new931activationerrors tests within full frontendtests. Run git diff --check on wholebase-to-head andworktree; sequentialexistingpreflight/immutability/publicationreadiness must pass. Any mandatoryfailure stops round, nofix-forward.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "build",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue913v2.publish",
      "command": "Afterallmandatorylocalchecks andPUBLICATION_READY, freshremote main/base/ownership; publish identical locally authoredDecision+productblob/tree/commit graph throughcanonicalGitAPI to exactfreshbranch,verifyeverySHA,createoneDraft againstmain. Normalgitpushbudget0. Comment disclosedproof only913/newDraft/653/659. NoGitHubsemanticedit.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue913v2.natural_checks",
      "command": "Only existing natural pull_request workflows verify exactpublishedhead; no manually invokedCI,runnerdispatch/rerun or productmutation. CI,DecisionPreflight,StateGate,ModelAccess,FrontendPlaywright must allSUCCESS andactualfullpytestdiagnosticexit0/nativeJUnit0. Browser_r3 profile selects existingCI validation; no user_localbrowsergrant. ExistingCI-owned network use is confined to unchangedworkflow dependency/test setup under the boundedci_network_exceptions; this command is not authority for local installation or manualCI execution.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue913v2.audit",
      "command": "Read actualcanonicalrun identities/results/nativeartifacts and independentexactheadaudit. Verify23sourceblobs equal847,8PNGhashes frozen,only32trackedpaths(Decision+31),preserved931behavior,currentbase/ownership. Separate currentnaturalvisualregression acceptance from historicalWindowsbrowserproof andoldPNGdesignreferences. Failedmandatory/naturalchecks stop,no rerun,no snapshotgeneration,no fixforward. KeepDraftunmerged for separatelyauthorizedlanding.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ]
}
```

Require fresh activation and sequential PRE_EXECUTION_AUTHORIZED before product mutation. Any mandatory failure stops this round; no fix-forward.

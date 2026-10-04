# Runtime-compatible protected review context projection

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue811_review_projection_r3_v1",
  "round_id": "round_20261004_issue811_review_projection_r3_v1",
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
  "decision_scope": "ISSUE811_READ_ONLY_PROJECTION_RUNTIME_CONTEXT_REPAIR",
  "source_issue": 811,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Owner persistent full project delegation prospectively authorizes runtime compatibility/context repair after actual native Task failure; old native/check/failed-helper budgets retained.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue811-review-only-runtime-r3-v3-20261004",
  "base_sha": "87f717b0a04083366ea0f9a1ac0d55be35cc09fd",
  "activation_base_sha": "87f717b0a04083366ea0f9a1ac0d55be35cc09fd",
  "starting_head": "87f717b0a04083366ea0f9a1ac0d55be35cc09fd",
  "required_branch": "codex/issue811-review-projection-r3-v1-20261004",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
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
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Persistent explicit Owner full project delegation prospectively authorizes bounded runtime/context repair of Issue811 NEW native failure on Draft1074@87f717b0a04083366ea0f9a1ac0d55be35cc09fd, explicitly approved planning base/source1074, not main. Original rootsource native CI37175055295 SUCCESS native6934pass31skip/all154reviewcases; first actual native Task API run task-1791087503153-9157c508b9c5 FAILED review_projection_mutated after11observedSenseNova requests. All2935targettrackedfiles, targetGitindex/config and originalsavedmodelconfig unchanged; owned jobs active0/portsfree/projectionremoved. Mutation paths were not preserved, exact cause unresolved: never claim cache/index versus model mutation is proven. Native context249762bytes one JSON line, model readability weakness observed as size/layout only, not a proven particular upstream truncation. Preserve all original source/test/CI/model/helperfailed evidence and exhausted native1/1; no same-head native retry/modelcall in source repair. Fresh rootbranch fromexact87; Decision-only activation and exact Draft against approved1074planning ref before changing any product/test/docs. Allowed product ONLY review_execution.py, test_review_execution.py, docs/review-only-tasks.md; collector/normalizer/API/task lifecycle/opencode permissions/binding/vault/workflows/deps/verifiers/sourcepolicy unchanged. Repair uses mature standard Git separate-git-dir: modelcwd childcontext with immutable .git pointer; disposable internal Git metadata outside modelcwd, so trusted runtime cache/index activity is separate from protected model inputs. No blanket .git ignore or broad mutation allowlist, no targetsource/index/config/ref write. Protect model context/plan/source text/.git pointer plus privatehost Git config/HEAD/exact initial branchref; model editstillhandoffonly, externaldirectory/bash/task/network all denied. Existing owned TemporaryDirectory handles cleanup only fresh private container; no original source/runtime/userdata cleanup. Materialize every collected nonwithheld base/head code/instruction/config text as ordinal .txt data under hostfixed review-data paths, UTF8 exactbytes preserved (no platformnewline translation), bounded by existing collector/filecount. Small readable structured context index references these immutable files and retains exact authenticated target/digests/contentstates; no targetAGENTS/MCP/plugins/config activation, no custom analyzer/index framework or second verifier. Do not narrow reviewed paths/content merely to make smoke test pass. Retain original all-current content observations binding, evidence refs and existing output private/secret/source/target/size checks, all flagsfalse, no functionality/independence/landing claims. Add bounded integrity rejection metadata through existing Task events: known hostpath labels only, unknown filename count without raw names/content, no raw secrets/private reasoning or new receipt/Gate/schema. Provider-free actualGit tests exercise separate metadata nativeGitstatus/cache activity without source mutation, complete multiline code-byte materialization including hostile AGENTS/config quoted data, immutable pointer/config/HEAD/ref/data/plan/unexpectedfile mutation fails, safe diagnostics and same existingAPI/lifecycle/ordinary/concurrency/regressions. Retain all existing assertions/protections, no newskip/deselect/testweakening. This is third cumulative runtime correction round (old2spent,charge1,max3); original development pytest6limit4spent -> remaining2 only: affected review/Git/API group<=300s then existing execution/service/opencode/regression<=600s, no extra dev processes. New sourcephase finalmandatory once fullPlatformV1<=2400s retaining onlyexactoriginal4installedOpenCode exclusions; PathAonce<=120s; committedheadfocusedonce<=300s. Original previousmandatorychecks3/3completed onold87preserved; new changed candidate requires fresh exact-head mandatorychecks, never rebrandoldtests as new. Mandatory failure stops publication/corrections/retries. Scratch new absent F:/nrl-reviewrt2 only, known installed providerfreeGit/Python/PS/node; cleanup onlyfreshownedfixtures/jobs. Root oneDecisionactivation and oneproductcommit, max2normalexactbranch pushes, oneactivationDraft,max6bodyupdates and naturalexactheadCIoriginal reads, no Ready/Merge/Issueclosure/comments/rewrite/rerun/dispatch/install/nativeOpenCode/model/credential/browser/liveprovider in this sourcephase. Existing UI/nativecontroller/runtime/source1074 preserved. No full811/backlog claim. Sixhour window.",
    "completion_boundary": "Corrected full-context disposable projection protected against model mutation; providerfree nativeGit/HTTP regressions and fresh exacthead CI. Live model/independent acceptance/full811 remain separate."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_execution.py",
    "tests/platform_v1/test_review_execution.py",
    "docs/review-only-tasks.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_execution.py",
    "tests/platform_v1/test_review_execution.py",
    "docs/review-only-tasks.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/review_git_snapshot.py",
    "reverse_agent/platform_v1/review_findings.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/credential_relay.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "frontend/package*.json",
    "frontend/node_modules/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "**/auth.json",
    "frontend/**",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_artifact_handoff.py"
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Trusted provider-free tests newly owned ephemeral loopback fixtures only; never existing frontend/Task/model services or real provider/auth/model."
    ],
    "github_control_plane_network_exceptions": [
      "Max2 normal pushes to codex/issue811-short-fixtures-r3-v1-20261003; one activation Draft against main@97d766d7253378c093c31ed29c990cb6921f2ae4; max6 body updates; bounded natural CI/artifact reads only."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "review.bootstrap",
      "command": "Fresh exact87 approved planningbase1074 Decision-only activation, canonicalgates, pushactivation/Draftbefore productcode. No productchange beforeDraft.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "review.implement",
      "command": "Persistent explicit Owner full project delegation prospectively authorizes bounded runtime/context repair of Issue811 NEW native failure on Draft1074@87f717b0a04083366ea0f9a1ac0d55be35cc09fd, explicitly approved planning base/source1074, not main. Original rootsource native CI37175055295 SUCCESS native6934pass31skip/all154reviewcases; first actual native Task API run task-1791087503153-9157c508b9c5 FAILED review_projection_mutated after11observedSenseNova requests. All2935targettrackedfiles, targetGitindex/config and originalsavedmodelconfig unchanged; owned jobs active0/portsfree/projectionremoved. Mutation paths were not preserved, exact cause unresolved: never claim cache/index versus model mutation is proven. Native context249762bytes one JSON line, model readability weakness observed as size/layout only, not a proven particular upstream truncation. Preserve all original source/test/CI/model/helperfailed evidence and exhausted native1/1; no same-head native retry/modelcall in source repair. Fresh rootbranch fromexact87; Decision-only activation and exact Draft against approved1074planning ref before changing any product/test/docs. Allowed product ONLY review_execution.py, test_review_execution.py, docs/review-only-tasks.md; collector/normalizer/API/task lifecycle/opencode permissions/binding/vault/workflows/deps/verifiers/sourcepolicy unchanged. Repair uses mature standard Git separate-git-dir: modelcwd childcontext with immutable .git pointer; disposable internal Git metadata outside modelcwd, so trusted runtime cache/index activity is separate from protected model inputs. No blanket .git ignore or broad mutation allowlist, no targetsource/index/config/ref write. Protect model context/plan/source text/.git pointer plus privatehost Git config/HEAD/exact initial branchref; model editstillhandoffonly, externaldirectory/bash/task/network all denied. Existing owned TemporaryDirectory handles cleanup only fresh private container; no original source/runtime/userdata cleanup. Materialize every collected nonwithheld base/head code/instruction/config text as ordinal .txt data under hostfixed review-data paths, UTF8 exactbytes preserved (no platformnewline translation), bounded by existing collector/filecount. Small readable structured context index references these immutable files and retains exact authenticated target/digests/contentstates; no targetAGENTS/MCP/plugins/config activation, no custom analyzer/index framework or second verifier. Do not narrow reviewed paths/content merely to make smoke test pass. Retain original all-current content observations binding, evidence refs and existing output private/secret/source/target/size checks, all flagsfalse, no functionality/independence/landing claims. Add bounded integrity rejection metadata through existing Task events: known hostpath labels only, unknown filename count without raw names/content, no raw secrets/private reasoning or new receipt/Gate/schema. Provider-free actualGit tests exercise separate metadata nativeGitstatus/cache activity without source mutation, complete multiline code-byte materialization including hostile AGENTS/config quoted data, immutable pointer/config/HEAD/ref/data/plan/unexpectedfile mutation fails, safe diagnostics and same existingAPI/lifecycle/ordinary/concurrency/regressions. Retain all existing assertions/protections, no newskip/deselect/testweakening. This is third cumulative runtime correction round (old2spent,charge1,max3); original development pytest6limit4spent -> remaining2 only: affected review/Git/API group<=300s then existing execution/service/opencode/regression<=600s, no extra dev processes. New sourcephase finalmandatory once fullPlatformV1<=2400s retaining onlyexactoriginal4installedOpenCode exclusions; PathAonce<=120s; committedheadfocusedonce<=300s. Original previousmandatorychecks3/3completed onold87preserved; new changed candidate requires fresh exact-head mandatorychecks, never rebrandoldtests as new. Mandatory failure stops publication/corrections/retries. Scratch new absent F:/nrl-reviewrt2 only, known installed providerfreeGit/Python/PS/node; cleanup onlyfreshownedfixtures/jobs. Root oneDecisionactivation and oneproductcommit, max2normalexactbranch pushes, oneactivationDraft,max6bodyupdates and naturalexactheadCIoriginal reads, no Ready/Merge/Issueclosure/comments/rewrite/rerun/dispatch/install/nativeOpenCode/model/credential/browser/liveprovider in this sourcephase. Existing UI/nativecontroller/runtime/source1074 preserved. No full811/backlog claim. Sixhour window.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/review_execution.py",
        "tests/platform_v1/test_review_execution.py",
        "docs/review-only-tasks.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.validate",
      "command": "Only current bounded2 remaining development checks; fresh oncefullPlatformV1/PathA/committedheadfocusedmandatory, gitdiffcheck/exactbranch/readiness/Draftbinding/naturalnativeCI and originalinputs preservation; no old87 test transfer.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "commit",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/review_execution.py",
        "tests/platform_v1/test_review_execution.py",
        "docs/review-only-tasks.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.publish",
      "command": "Only current bounded2 remaining development checks; fresh oncefullPlatformV1/PathA/committedheadfocusedmandatory, gitdiffcheck/exactbranch/readiness/Draftbinding/naturalnativeCI and originalinputs preservation; no old87 test transfer.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Carry preserved known source/gates unstaged; reuse only new absent child fixtures under owned F:/nrl-reviewrt1, external issue811-review-only-runtime-r3-v3. Existing user/runtime/process/configuration preserved."
  },
  "follows_last_decision_id": "decision_20261004_issue811_review_only_runtime_r3_v2",
  "follows_last_round_id": "round_20261004_issue811_review_only_runtime_r3_v2",
  "workstream_id": "issue811-review-only-runtime-r3-v3",
  "source_issues": [
    811,
    179,
    653
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 3,
  "execution_window_hours": 6,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-04T04:32:54.995030+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6,
  "owned_test_scratch_root": "F:\\nrl-reviewrt1",
  "mandatory_pytest_process_limit": 3,
  "cumulative_prior_development_checks": 1,
  "cumulative_development_check_limit": 6,
  "cumulative_prior_correction_rounds": 1,
  "cumulative_correction_round_limit": 3,
  "preserved_source_handoff_manifest": [
    {
      "path": "reverse_agent/platform_v1/review_git_snapshot.py",
      "sha256": "c24cd5e1f1cd9efb268a8da0ec149e29a018a09f70026022c9f84a6b62155e8d",
      "size": 12727,
      "modified_utc": "2026-10-03T16:22:51.069348+00:00"
    },
    {
      "path": "tests/platform_v1/test_review_git_snapshot.py",
      "sha256": "5ab1dc76a91f00222d623caedb7c30ca743e29e689966cd23c7868ccff1fa768",
      "size": 10045,
      "modified_utc": "2026-10-03T16:22:51.096549+00:00"
    },
    {
      "path": "docs/review-git-snapshot.md",
      "sha256": "687d8b7cbaa7725230eaefc664e4c69506fdf8aafac0be58251c95266e863f6a",
      "size": 2541,
      "modified_utc": "2026-10-03T16:22:51.127746+00:00"
    },
    {
      "path": "reverse_agent/platform_v1/review_execution.py",
      "sha256": "e61fbf7134e6449baff6e08b6e44f8caef95850aa19b5fd0e6d5fd39b0644fcf",
      "size": 12499,
      "modified_utc": "2026-10-03T16:37:46.501197+00:00"
    },
    {
      "path": "reverse_agent/platform_v1/task_execution.py",
      "sha256": "798400a59cd29ce2a1e4e085dcdfa4c9d8c324183d14b6379638468467d78420",
      "size": 47296,
      "modified_utc": "2026-10-04T02:52:37.827257+00:00"
    },
    {
      "path": "reverse_agent/platform_v1/task_service.py",
      "sha256": "c3de142b34ffde2cdd4dd92c6fd26056296e90adbc4745227db6e18632824bc0",
      "size": 53064,
      "modified_utc": "2026-10-03T16:31:20.954092+00:00"
    },
    {
      "path": "reverse_agent/platform_v1/opencode_executor.py",
      "sha256": "f11f9c92970e4084c7d0477f9eed365a776857069a037aac6a497ec41b6351b4",
      "size": 111002,
      "modified_utc": "2026-10-03T16:24:41.317163+00:00"
    },
    {
      "path": "tests/platform_v1/test_review_execution.py",
      "sha256": "c3b41314a621a0b74cf03cf9906c96d22f7d97bcfb17fc07b3f28e8d84cbff58",
      "size": 10106,
      "modified_utc": "2026-10-04T02:52:24.351229+00:00"
    },
    {
      "path": "tests/platform_v1/test_review_only_api.py",
      "sha256": "afdaf8ed09e11d997106813a73464a373ff595ad68c449e5c98ab9911067b4b4",
      "size": 3033,
      "modified_utc": "2026-10-03T16:36:22.464038+00:00"
    },
    {
      "path": "tests/platform_v1/test_opencode_executor.py",
      "sha256": "5aa1dd309952d8646d08f76e1ca27023068f5a6937aced545eef44b4ac1c0c7e",
      "size": 112445,
      "modified_utc": "2026-10-02T06:09:28.773094+00:00"
    },
    {
      "path": "docs/review-only-tasks.md",
      "sha256": "6ca6be15c0bd1ce3b9ccd1252e56f1b1d3aec06ceb9a943f31456e342abe7915",
      "size": 3507,
      "modified_utc": "2026-10-03T16:36:22.466041+00:00"
    }
  ]
}
```

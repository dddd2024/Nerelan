# Reuse existing Resume identity candidate on accepted main

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_issue120_resume_identity_r3_v3",
  "round_id": "round_20260928_issue120_resume_identity_r3_v3",
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
  "decision_scope": "REUSE_PR992_ATOMIC_RESUME_IDENTITY_AND_RECEIPTS",
  "source_issue": 120,
  "parent_issue": 1010,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "Owner mandates system completion of all prioritized GitHub work with independent supervisor acceptance. After verified PR1022 mainline closeout, priority02 resumes existing PR992 candidate without rewriting it. Original head a0af0b1508fd10295c463ff9f6c8b16bedc70106 six-product-file patch applies cleanly to current code. Fresh exactbase/Draft preserves old PR992 and reuses existing implementation, no second claim/budget/receipt subsystem. Supervisor transfers exact existing candidate and any strictly validated system-authored correction only, never authors product logic. Final exacthead and naturalCI remain mandatory; landing separate.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "activation_base_sha": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "starting_head": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "fresh_base": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "current_main_expected": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "required_branch": "codex/issue120-resume-identity-system-v3-20260928",
  "workstream_id": "issue120-resume-identity-system-v3",
  "follows_last_decision_id": "decision_20260923_issue120_resume_identity_receipts_r2_v2",
  "follows_last_round_id": "round_20260923_issue120_resume_identity_receipts_r2_v2",
  "workflow_profile": "baseline",
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
  "live_model_call_limit": 48,
  "provider_network_call_limit": 48,
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
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
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
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py"
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
    "frontend/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/model_access/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
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
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/model_access/credential_relay.py",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Re-anchor the public Resume write-gate from closed stale PR #979 onto current main and strengthen it so resume admission is identity-bound and auditable. Reuse the existing durable run identity, owner window, AutonomyService, PlatformControlStore claim/budget reservation, and operation-receipt tables. Add execution_authority_sha/planning_sha binding to coordinator claims and budget reservations; compare current identities to the durable run inside the same BEGIN IMMEDIATE claim transaction before claim/retry/budget mutation; fail closed on disagreement. Existing legacy active reservations without identity may be bound only by an explicit atomic compatible migration when the durable run exactly matches the current identities, and that migration must be receipted. Extend the existing operation receipt with a bounded non-secret identity snapshot rather than creating a Vestige subsystem or second audit table. Successful resume admission must persist its allow receipt atomically with the claim/reservation before any durable executor/tool re-entry. Denied resume admission must record a deny receipt when the referenced window exists; failure to record an allow receipt must prevent execution. Reuse the same identity-bound claim path for unattended Resume and manual Task API Resume. Preserve DurableExecutionService repository/worktree/HEAD/checkpoint checks. Preserve original PR992 implementation provenance and six-file scope; no wholesale file replacement over currentmain changes. Use exact git patch context/check, system text edits only for verified regression gaps within these six paths. Do not alter test expectations merely to hide failures; retain actual manualHTTP/unattended Resume no-dispatch/no-budget-mutation and atomic receipt rollback controls. Before accepting reused candidate, reproduce and resolve within same six paths: production unattended opencode Resume with missing both/partial current identities must fail BEFORE claim/retry/reservation writes; low-level provider-free bookkeeping compatibility must not become a production bypass. Manual Resume early identity rejection with an existing referenced window must persist bounded denial identity evidence rather than silently returning before the existing receipt path. Check whether denial receipt identity snapshots can race after comparison; if reproduced, retain compared facts captured at the transactional comparison point instead of later unrelated state. No new receipt table/ledger/authority engine. Regression tests must assert no executor dispatch/no budget mutation, correct denial evidence, and existing admitted resume still works.",
    "execution_surface_note": "Exact old six-file candidate patch only after fresh activationDraft. Provider-free disposable tests, no real Task/model executor dispatch. If correction needed, at most48 serial tool-free Codestral calls600sec each with0tools/dispatch/autoretry/spendcap; only named owned binding temporarilyenabled thenrestored, trustedstore/vault/relay resolves credentials internally withno rawsecretread/output. All tests zero model/provider calls. No source-stageReady/merge or deployment.",
    "completion_boundary": "Draft implementation only. Deterministic tests must prove planning mismatch causes no claim/retry/budget mutation and no executor/tool dispatch; budget-reservation planning mismatch fails closed before dispatch; allow and deny receipts expose bounded checked identity facts; legacy unbound active reservation is only safely rebound when durable/current identities agree; admitted manual and unattended Resume use the identity-bound claim path. No Ready/Merge or Issue closure."
  },
  "runtime_scratch_policy": {
    "paths": [
      ".platform_v1_runtime/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing launcher runtime stores/metadata only, preserve persisted settings. For approved provider-free tests ONLY, a test subprocess may set PYTHONPATH to existing trusted installed C:/Users/wjc27/AppData/Roaming/Python/Python313/site-packages so pytest is visible. No install, global env change or product child-env relaxation; no arbitrary home/secret reads. Evidence remains outside tracked source."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
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
      "Unchanged natural CI package setup and provider-free checks only; no added workflow or manual dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Verify owned supervised-route-mistral-20260928b exact mistral/codestral-latest/opencode disabled; temporaryenable onlyduringboundedtoolfreecalls, restoreexactdisabledfinally. Max48serialtextcalls600sec0autoretry0tools/dispatch. Nativecredentialresolutiononly,no rawkeyread/export, no userBinding/Connection edits. Existing provider-free tests/local fakeHTTP allowed. No actual OpenCodeTask, runtime restart, deployment, realOAuth or arbitrarycommands."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue120v3.bootstrap",
      "command": "After1022maincloseout fresh exactbase393886c2e1b764e6f8a4ed638aceb24cccdc92a8 F:/Nerelan-issue120-system-v3-20260928 branchcodex/issue120-resume-identity-system-v3-20260928. One immutableUTF8LFDecisioncommit; all5nativegates+diffcheck. Pushactivation/createDraft/readback beforeproductbytes. Nohistoryreuse/rewrite.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
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
      "command_id": "issue120v3.runtime",
      "command": "Verify owned supervised-route-mistral-20260928b exact mistral/codestral-latest/opencode disabled; temporaryenable onlyduringboundedtoolfreecalls, restoreexactdisabledfinally. Max48serialtextcalls600sec0autoretry0tools/dispatch. Nativecredentialresolutiononly,no rawkeyread/export, no userBinding/Connection edits. Existing provider-free tests/local fakeHTTP allowed. No actual OpenCodeTask, runtime restart, deployment, realOAuth or arbitrarycommands.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120v3.system",
      "command": "AfterverifiedDraft copy exact sixproduct-file gitdiff fromPR992head a0af0b1508fd10295c463ff9f6c8b16bedc70106 againstapprovedoriginalbase58d4068f43ca4914b122445685cae410a8fa156e; gitapplycheckfirst, applyonlydeclaredpaths, noDecisioncopy. Reuseexistingimplementation; ifneeded max48toolfreeCodestralcorrections withstrictnonlink/path/uniqueold/scope validation. Supervisorreviews/transfers, no product/testauthorship. Onefinalproductcommitafterdevelopmentchecks.",
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
        "machine_specific_execution",
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/unattended_coordinator.py",
        "tests/platform_v1/test_autonomy.py",
        "tests/platform_v1/test_task_service.py",
        "tests/platform_v1/test_unattended_coordinator.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120v3.checks",
      "command": "Developmentchecks/fixesbeforefreeze. Mandatoryexacthead: python -B -m pytest tests/platform_v1/test_autonomy.py tests/platform_v1/test_task_service.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_run_resume_control.py -q -p no:cacheprovider; python -B -m pytest tests/platform_v1 -q -p no:cacheprovider; git diff --check 393886c2e1b764e6f8a4ed638aceb24cccdc92a8 HEAD. Beforestagecachedstartupreadiness;stageonlysixproductpaths, oneproductcommit,all5gates. Finalmandatoryfailurestopspublication,no fixforward or weakentest.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120v3.publish",
      "command": "Atmosttwoexactbranchpushesactivation/final codex/issue120-resume-identity-system-v3-20260928 andoneDraftagainstmain@393886c2e1b764e6f8a4ed638aceb24cccdc92a8. Rebindexactheadbody, requirefinalchecks/readiness/base/scope. NoReady/merge/closure/historyrewrite.",
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
    },
    {
      "command_id": "issue120v3.ci",
      "command": "Natural exacthead sourceCI/Decision/State native diagnostics; no manualdispatch/rerun/workflowchanges.",
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
      "command_id": "issue120v3.audit",
      "command": "Independent supervisor examines resume identity BEFORE claim/retry/reservation mutation, sameSQLite transaction andreceiptrollback, boundedidentitydata,manualHTTP andunattendedadmission. Preserve durableworktree/HEAD/checkpoint checks. No separateledger or modelselfacceptance. Frontendnotdeployed; no newvisualclaim.",
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
  ],
  "concurrent_work_preservation": {
    "prs": [
      992,
      1023
    ],
    "policy": "Preserve old992 head a0af0b1508fd10295c463ff9f6c8b16bedc70106 and all other PR/source/root user edits. Activate only after1022 native maincloseout. No concurrent productmutation of same6paths; onlyone controlledlandinglane. Existing source/authority artifacts anduserAPIsettings unchanged."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_run_resume_control.py"
  ],
  "source_issues": [
    120
  ],
  "required_provider_free_checks": [
    "python -B -m pytest tests/platform_v1/test_autonomy.py tests/platform_v1/test_task_service.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_run_resume_control.py -q -p no:cacheprovider",
    "python -B -m pytest tests/platform_v1 -q -p no:cacheprovider",
    "git diff --check 393886c2e1b764e6f8a4ed638aceb24cccdc92a8 HEAD"
  ]
}
```

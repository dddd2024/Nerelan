# Native fixed profiles and exact-candidate validation

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261001_issue1049_native_fixed_candidate_r3_v3",
  "round_id": "round_20261001_issue1049_native_fixed_candidate_r3_v3",
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
  "decision_scope": "NATIVE_FIXED_PROFILES_AND_EXACT_CANDIDATE_VALIDATION",
  "source_issue": 1049,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner request in the current conversation",
  "approval_basis": "Owner explicitly approved bounded development of fixed test combinations and read-only specified-commit validation, 2026-10-01T12:19:54Z message Sentinel_550d74cc86a881918dc6c6d15edec061, and normal use of already configured free models. Delegated execution authorizes this fresh-main successor; original user workspace and #1038 immutable Decision are preserved. Exact remote main freshly observed as 9092911f41a089e249f27c883526904299be1d17. Codex integrates necessary unsupported improvements; later acceptance must be by a different auditor. No Ready/Merge/deployment/install/configuration or credential mutation/payment. Unpublished v1 activation f9c4fa7e1ab3d52b7a5b97d53d6952d8ec5e4515 failed preflight due incompatible read_only_audit/ci_only command metadata; preserve it unchanged. Fresh v2 corrects only that metadata before implementation, under the same bounded owner delegation. Owner continuation explicitly requests recovery of serialisation/pending-publication prerequisites without renewed permission. Preserve v2 fb2f36191ff362ccc629c843dcbdf2f75d7d813d unchanged: gates passed but extra EOF blank line failed diff-check; accidentally started CLI push remains pending and cannot be terminated without identity. Remote exact branch absent and commit API422 at recovery observation. V3 is a distinct fresh successor, no retry/rewrite of v2. Use authorized GitHub connector blob/tree/commit/branch Draft publication, after canonical LF and diff checks, and fresh local exact activation checkout/preflight before product work.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20261001-native-fixed-candidate-r3-v3",
  "fresh_worktree_creation_required": true,
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
  "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 4,
  "provider_network_call_limit": 4,
  "credential_access_limit": 0,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Add exactly two host-owned immutable pytest/JUnit combinations: report-consistency suite and functional_execution plus artifact_handoff. Update Python argv resolution, JUnit injection and report-format admission together; no client argv/targets/env expansion. Add provider-free candidate_validation executor route from owner-approved Goal validation task with exact expected_candidate_sha (40 lowercase hex), bound in existing Goal revision/digest and frozen FunctionalContract. Reuse ACTIVE window capability admission, TaskStore/durable lease fencing, existing report parsing and shared lifecycle. Check repository origin identity, expected SHA, immutable Git tree and before/after head/tree; another stable descendant sharing approved base must fail. Reject stale catalog/contract, wrong repo, contradictory/missing/zero/allskip reports. Reuse #1038 consistency predicate explicitly in this successor with negative regressions, without altering its Decision. Candidate result truthfully identifies provider-free host checks, never impersonates opencode. No accepted producer artifact/receipt fabrication or producer/export publication authority. Only exact candidate temporary checkout and native evidence writes; tests can execute code therefore read-only is not OS sandboxing.",
    "reuse": "Existing Goal/ACTIVE window/frozen functional contract, TaskStore fenced evidence and claims, Git workspace identity, fixed pytest/JUnit and report consistency. No new database, arbitrary command platform, schema/artifact family, workflow, generic judge or sandbox claim.",
    "execution_surface_note": "Fresh isolated full checkout in C:/Users/wjc27/AppData/Local/Temp/nerelan-native1049-20261001-v3/checkout. Decision-only activation and Draft before source edits. Actual local transition preflight required. Existing configured enabled coding-default/coding-glm/coding-kimi models may participate through genuine Nerelan Task execution only; internal native vault/relay resolution permitted without printing/exporting secrets. At most4 model calls, no automatic retries, each600s; no binding/provider/configuration changes, disabled route activation, purchases or acceptance of charges. Stop model call on unavailable/limit/unclear-charge response, preserve evidence, Codex may implement. No secrets/config changes. Provider-free disposable development tests and native Goal/Window/Task/Run checks allowed; no stop of unidentified/user process.",
    "completion_boundary": "One exact-branch Draft; final scoped local pytest + git diff --check, actual gates/readiness, natural exact-head CI, evidence and separate independent audit required. Local author tests are not independent acceptance. Full local suite not required; unchanged CI supplies blocking Platform/full checks. No Ready/Merge/Issue closure/deployment."
  },
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
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/candidate_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/goal_models.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_native_candidate_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/candidate_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/goal_models.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_native_candidate_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
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
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_artifact_handoff.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "launch_nerelan.bat",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural repository CI dependency setup and provider-free validation only. No new workflow, rerun or dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "At most4 normal genuine native calls using already enabled coding-default/coding-glm/coding-kimi; no automatic retry/config changes/payment/raw secrets. Preserve failure and stop that call on rate/unavailability/unclear charge. Owned loopback only if required, no user process stop."
    ],
    "github_control_plane_network_exceptions": [
      "Exact v3 branch and one Draft only using existing authorized GitHub connector blob/tree/commit/ref APIs; activation and exact final head updates preserve history. Read-only exact SHA fetch for local verification. Pending v2 untouched; no blind retry, duplicate Draft, Ready/Merge/closure/settings/install/dispatch."
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
      "command_id": "native.bootstrap",
      "command": "Fresh exact-main isolated clone with local core.autocrlf=false; canonical UTF8 LF Decision with exactly one EOF newline; git diff --check before activation. Authorized GitHub connector creates exact Decision blob/tree and one activation commit object parent approved base. Fetch exact real object into isolated checkout, local exact required branch, verify full bytes and existing startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre/readiness; actual PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before exact connector branch creation/Draft and all source edits. Preserve prior pending v2, no CLI re-push/termination/rewrite; never stage generated gates.",
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
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "native.implement",
      "command": "Implement only two fixed profiles and approved exact-candidate provider-free route plus #1038 strict report consistency reuse. Genuine native model development with enabled unchanged config at most4calls600s no autoretry; preserve failures, Codex integration/fallback allowed. Disposable fixture/SQLite/Goal/Window/Task/Run execution, no server deployment or original workspace writes.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "machine_specific_execution",
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/functional_validation.py",
        "reverse_agent/platform_v1/candidate_validation.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/goal_models.py",
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "reverse_agent/platform_v1/run_store.py",
        "tests/platform_v1/test_native_candidate_validation.py",
        "tests/platform_v1/test_functional_report_consistency.py",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validate",
      "command": "Development focused checks/fixes within five commits. Final exact-head python -B -m pytest tests/platform_v1/test_native_candidate_validation.py tests/platform_v1/test_functional_report_consistency.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_artifact_handoff.py -q -p no:cacheprovider; git diff --check base HEAD; actual transition gates and PUBLICATION_READY. Fixed-argv/stale-contract/candidate-SHA-other-descendant/repo/head/tree/report negative tests mandatory. Existing natural CI blocking Platform/all suite distinct from local, no installs/reruns.",
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
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "native.publish",
      "command": "At most7 exact-branch pushes and one Draft against main@9092911f41a089e249f27c883526904299be1d17, activation first; rebind exact head, read natural CI and progress comments. No Ready/Merge/closure/deployment/history rewrite.",
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
      "command_id": "native.ci",
      "command": "Observe unchanged natural exact-head CI/Decision/State checks, provider-free and zero models. No rerun/dispatch/workflow/dependency change. Author evidence is not independent audit.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "code_read",
        "unit_test",
        "integration_test"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**"
    ],
    "stage_allowed": false,
    "note": "All new task/run/model evidence and temporary fixtures remain in approved external Temp root. No original runtime write. Existing sanitized model metadata read-only; native internal vault resolution only. No installs."
  },
  "follows_last_decision_id": "decision_20261001_issue1049_native_fixed_candidate_r3_v2",
  "follows_last_round_id": "round_20261001_issue1049_native_fixed_candidate_r3_v2"
}
```

## Claim ceiling
Author implementation verification is not independent acceptance. Read-only validation is not OS sandboxing. No producer/export publication grant or fabricated AcceptedArtifact.

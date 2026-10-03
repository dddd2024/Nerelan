# Fresh current-main binding of reviewed Issue811 contract

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue811_current_main_reanchor_r2_v1",
  "round_id": "round_20261003_issue811_current_main_reanchor_r2_v1",
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
  "decision_scope": "EXACT_REVIEW_CONTRACT_FRESH_MAIN_REANCHOR",
  "source_issue": 811,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Owner explicit full responsibility prospectively bounds exact source reanchor onto current main; all old branches/Decisions/evidence preserved.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue811-current-main-reanchor-r2-v1-20261003",
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
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Current explicit Owner full project delegation prospectively authorizes Issue811 complete reviewed contract rematerialization on actual current main97d766d7253378c093c31ed29c990cb6921f2ae4. Preserve original PR1068/source71bdddd1f4555f7188fafd1aeed8d911be22d3a8 and all original immutable authority/evidence. Actual PR1068 is CONFLICTING through shared project_state/decision_packet.md; old main909..new97 changes only dev-up.ps1/dev-down.ps1/Decision/test_dev_up_contract.py, none of the three source paths or project policy_adapter. Exactly rematerialize three Git-blob-authenticated source files from71: reverse_agent/platform_v1/review_findings.py, tests/platform_v1/test_review_findings.py, docs/review-findings.md. Retain complete immutable ReviewTarget/finding/feedback contract and all existing tests/docs, without narrowing or changing semantic content. No copied old Decision, cherry-pick/rebase/amend/history rewrite, source repair or old head acceptance relabeled to new head. Current unchanged policy_adapter blocks R2 system execution before model calls, so authorized Codex fallback handles this bounded R2 work without bypassing it. Canonical startup/plan/lint PASSED, PRE_EXECUTION_AUTHORIZED, PUBLICATION_READY and one exact activation Draft required before source copies. Four mandatory actual provider-free pytest processes: focused review_findings <=180s; full Platform V1 <=2400s with only same four already-excluded installed-OpenCode tests deselected; tests/test_path_a_gate.py <=120s; exact committed-head focused <=180s. Actual git diff --check and exact source blob equality required. No retries or corrections under this authority; mandatory failure stops publication. One Decision-only activation and one product commit; max2 normal pushes total to exact fresh branch, one Draft against main97; max6 exact-head body updates, bounded natural CI/artifact reads. No comments/Issue writes/closure/Ready/Merge/main push/force/history rewrite/dispatch/rerun/model/provider/credential/browser/runtime/dependency/workflow changes or installs. Existing frontend/services and dirty historical721 worktrees preserved. Source phase requires same complete candidate and actual new-head local/natural CI success, not independent acceptance/full811/landing. Four-hour window from 2026-10-03T14:10:53.221549+00:00. Prior successful source checks are content evidence only, not fresh head evidence; this is a necessary new base binding, not reset of failing CI or exhausted models.",
    "completion_boundary": "Same complete REVIEWAGENT-1 source on fresh current main with actual new-head local and natural CI; independent acceptance/full811/landing separate."
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
    "reverse_agent/platform_v1/review_findings.py",
    "tests/platform_v1/test_review_findings.py",
    "docs/review-findings.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_findings.py",
    "tests/platform_v1/test_review_findings.py",
    "docs/review-findings.md"
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    ".github/workflows/ci.yml"
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
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_opencode_executor.py",
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
    "destructive",
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
    "existing_task_or_runtime_mutation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing provider-free pytest-owned temporary loopback fixtures only; no real models/providers/Internet/existing runtime."
    ],
    "github_control_plane_network_exceptions": [
      "Max2 normal exact-branch pushes to codex/issue811-current-main-reanchor-r2-v1-20261003; one activation Draft against main@97d766d7253378c093c31ed29c990cb6921f2ae4; max6 body updates and bounded natural CI/artifact reads; no other writes."
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
      "command": "Fresh branch from main@97d766d7253378c093c31ed29c990cb6921f2ae4, preserve gates, one Decision-only activation, canonical startup/plan/lint/preflight/readiness and exact activation Draft before source copies.",
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
      "command": "Current explicit Owner full project delegation prospectively authorizes Issue811 complete reviewed contract rematerialization on actual current main97d766d7253378c093c31ed29c990cb6921f2ae4. Preserve original PR1068/source71bdddd1f4555f7188fafd1aeed8d911be22d3a8 and all original immutable authority/evidence. Actual PR1068 is CONFLICTING through shared project_state/decision_packet.md; old main909..new97 changes only dev-up.ps1/dev-down.ps1/Decision/test_dev_up_contract.py, none of the three source paths or project policy_adapter. Exactly rematerialize three Git-blob-authenticated source files from71: reverse_agent/platform_v1/review_findings.py, tests/platform_v1/test_review_findings.py, docs/review-findings.md. Retain complete immutable ReviewTarget/finding/feedback contract and all existing tests/docs, without narrowing or changing semantic content. No copied old Decision, cherry-pick/rebase/amend/history rewrite, source repair or old head acceptance relabeled to new head. Current unchanged policy_adapter blocks R2 system execution before model calls, so authorized Codex fallback handles this bounded R2 work without bypassing it. Canonical startup/plan/lint PASSED, PRE_EXECUTION_AUTHORIZED, PUBLICATION_READY and one exact activation Draft required before source copies. Four mandatory actual provider-free pytest processes: focused review_findings <=180s; full Platform V1 <=2400s with only same four already-excluded installed-OpenCode tests deselected; tests/test_path_a_gate.py <=120s; exact committed-head focused <=180s. Actual git diff --check and exact source blob equality required. No retries or corrections under this authority; mandatory failure stops publication. One Decision-only activation and one product commit; max2 normal pushes total to exact fresh branch, one Draft against main97; max6 exact-head body updates, bounded natural CI/artifact reads. No comments/Issue writes/closure/Ready/Merge/main push/force/history rewrite/dispatch/rerun/model/provider/credential/browser/runtime/dependency/workflow changes or installs. Existing frontend/services and dirty historical721 worktrees preserved. Source phase requires same complete candidate and actual new-head local/natural CI success, not independent acceptance/full811/landing. Four-hour window from 2026-10-03T14:10:53.221549+00:00. Prior successful source checks are content evidence only, not fresh head evidence; this is a necessary new base binding, not reset of failing CI or exhausted models.",
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
        "reverse_agent/platform_v1/review_findings.py",
        "tests/platform_v1/test_review_findings.py",
        "docs/review-findings.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.validate",
      "command": "Exactly4 mandatory real provider-free focused/full Platform V1/Path-A/exact-head pytest checks, git diff --check and source Git blob equality; no retries/corrections.",
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
        "reverse_agent/platform_v1/review_findings.py",
        "tests/platform_v1/test_review_findings.py",
        "docs/review-findings.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.publish",
      "command": "Max2 normal pushes to codex/issue811-current-main-reanchor-r2-v1-20261003; one activation Draft against main@97d766d7253378c093c31ed29c990cb6921f2ae4; max6 body rebindings; natural CI/artifact reads; no other writes.",
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
    "note": "Existing five generated gates preserved unstaged; external issue811-readiness-v1 and issue811-review-contract-r2-v1 only. No cleanup/runtime changes."
  },
  "follows_last_decision_id": "decision_20261001_issue1047_windows_owned_shutdown_r3_v1",
  "follows_last_round_id": "round_20261001_issue1047_windows_owned_shutdown_r3_v1",
  "workstream_id": "issue811-current-main-reanchor-r2-v1",
  "source_issues": [
    811,
    179,
    653
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 4,
  "development_correction_round_limit": 0,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T14:10:53.221549+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6
}
```


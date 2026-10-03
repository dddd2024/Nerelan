# Revised bounded first-class read-only review task integration

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue811_review_only_runtime_r3_v2",
  "round_id": "round_20261004_issue811_review_only_runtime_r3_v2",
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
  "decision_scope": "ISSUE811_FIRST_CLASS_READ_ONLY_RUNTIME",
  "source_issue": 811,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Current persistent explicit full project delegation; new runtime implementation scope, not reset of old source/review budgets.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue811-short-fixtures-r3-v1-20261003",
  "base_sha": "277625927e39ee568f56cbf403b5107ca92e28dd",
  "activation_base_sha": "277625927e39ee568f56cbf403b5107ca92e28dd",
  "starting_head": "277625927e39ee568f56cbf403b5107ca92e28dd",
  "required_branch": "codex/issue811-review-only-runtime-r3-v2-20261004",
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
    "specification": "Owner persistent full delegation prospectively authorizes Issue811 first-class read-only Task lifecycle integration on explicit approved planning base PR1072@277625927e39ee568f56cbf403b5107ca92e28dd; base remains unmerged with static advisory review, not independent acceptance. Reuse exact three reviewed collector blobs from1069@874c3fb11806b9ca4d19b913fce6125e89782be2 unchanged. Implement TaskExecutionService.execute_review and bounded existing Task API POST /api/tasks/{id}/review with existing TaskStore/status/events/evidence, no new DB/schema/executor kind/verifier/index/merge authority or unattended dispatch. Resolve target repository only from trusted registry/task identity; browser cannot supply filesystem paths/tools/config/policy/credentials. Collect exact explicit base/head and bounded paths with mature Git collector, original repo source/refs/index/config read-only. Native model/executor cwd is a freshly owned minimal projection Git repo containing host-authored policy/plan and serialized untrusted base/head context only; no target checkout, target AGENTS/skills/MCP/plugin/config activation. New bounded review_only role denies ALL bash/task/external-directory/network tools, only handoff/review.md write, no target write capability. Parse <=64KiB structured review-findings handoff, reject unknown fields/target mismatch/non-model source/excess findings/private reasoning/known secret patterns across persisted fields; use existing normalize_review_finding and bounded sanitized existing evidence path. Atomic existing lifecycle transitions prevent competing model launches; clean/static report is not functional validation or human/independent approval. Target generation and explicit all authority flags remain false in persisted records. Preserve original source/config, source-packet/CI review reports and existing frontend services; no Task status forgery for earlier direct-role QUEUED task. Provider-free meaningful actual Git/HTTP tests exercise lifecycle success/failure/concurrent claim, output/mutation/secret/target mismatch, head instruction/config data-only, API repository/path authority confinement and ordinary/sequential regression. Test executors are provider-free controlled substitutes, never reported as live model/detection acceptance. No new live model/provider/credentials/browser/native OpenCode trials (existing4 installed-OpenCode tests deselected only). Known installed Git/Python/PS5/PS7/Node and newly owned disposable fixture process/job cleanup permitted only under new short absent F:/nrl-reviewrt1; no existing file/user/runtime cleanup. At most6 provider-free development pytest processes/3 correction rounds, then mandatory single full Platform V1<=2400s, PathA<=120s and final committed-head focused<=300s; mandatory failure stops publication, no rerun/extra correction. One Decision-only activation and one product commit, max2 normal exact-branch pushes, one activation Draft against explicit planning branch1072/base277, max6 body updates/natural CI reads, no Ready/Merge/Issue closure/comments/rewrite/dispatch/install/workflow/dependency/config changes. No claim full811/allGitHub tasks complete; analyzer/context enrichment/forge/incremental/repair remain explicit next integration requirements. Six-hour execution window. Prospective v2 resolves old-template read-only reference conflict by treating opencode_executor.py exclusively as approved edit scope. Original v1 immutable Decision-only activation/preflight BLOCKED preserved, zero source/test/model/push/Draft calls spent; no execution budget is reset or hidden. This is the sole bootstrap scope correction.",
    "completion_boundary": "Actual first-class provider-free Git/HTTP/TaskStore lifecycle implemented and verified; live-model quality/independent acceptance/landing/full811 separate."
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
    "reverse_agent/platform_v1/review_git_snapshot.py",
    "tests/platform_v1/test_review_git_snapshot.py",
    "docs/review-git-snapshot.md",
    "reverse_agent/platform_v1/review_execution.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_review_execution.py",
    "tests/platform_v1/test_review_only_api.py",
    "tests/platform_v1/test_opencode_executor.py",
    "docs/review-only-tasks.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_git_snapshot.py",
    "tests/platform_v1/test_review_git_snapshot.py",
    "docs/review-git-snapshot.md",
    "reverse_agent/platform_v1/review_execution.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_review_execution.py",
    "tests/platform_v1/test_review_only_api.py",
    "tests/platform_v1/test_opencode_executor.py",
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
      "command": "Fresh exact explicit planning base277 branch, Decision-only activation then canonical startup/plan/lint/preflight/readiness and activation Draft before product changes.",
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
      "command": "Owner persistent full delegation prospectively authorizes Issue811 first-class read-only Task lifecycle integration on explicit approved planning base PR1072@277625927e39ee568f56cbf403b5107ca92e28dd; base remains unmerged with static advisory review, not independent acceptance. Reuse exact three reviewed collector blobs from1069@874c3fb11806b9ca4d19b913fce6125e89782be2 unchanged. Implement TaskExecutionService.execute_review and bounded existing Task API POST /api/tasks/{id}/review with existing TaskStore/status/events/evidence, no new DB/schema/executor kind/verifier/index/merge authority or unattended dispatch. Resolve target repository only from trusted registry/task identity; browser cannot supply filesystem paths/tools/config/policy/credentials. Collect exact explicit base/head and bounded paths with mature Git collector, original repo source/refs/index/config read-only. Native model/executor cwd is a freshly owned minimal projection Git repo containing host-authored policy/plan and serialized untrusted base/head context only; no target checkout, target AGENTS/skills/MCP/plugin/config activation. New bounded review_only role denies ALL bash/task/external-directory/network tools, only handoff/review.md write, no target write capability. Parse <=64KiB structured review-findings handoff, reject unknown fields/target mismatch/non-model source/excess findings/private reasoning/known secret patterns across persisted fields; use existing normalize_review_finding and bounded sanitized existing evidence path. Atomic existing lifecycle transitions prevent competing model launches; clean/static report is not functional validation or human/independent approval. Target generation and explicit all authority flags remain false in persisted records. Preserve original source/config, source-packet/CI review reports and existing frontend services; no Task status forgery for earlier direct-role QUEUED task. Provider-free meaningful actual Git/HTTP tests exercise lifecycle success/failure/concurrent claim, output/mutation/secret/target mismatch, head instruction/config data-only, API repository/path authority confinement and ordinary/sequential regression. Test executors are provider-free controlled substitutes, never reported as live model/detection acceptance. No new live model/provider/credentials/browser/native OpenCode trials (existing4 installed-OpenCode tests deselected only). Known installed Git/Python/PS5/PS7/Node and newly owned disposable fixture process/job cleanup permitted only under new short absent F:/nrl-reviewrt1; no existing file/user/runtime cleanup. At most6 provider-free development pytest processes/3 correction rounds, then mandatory single full Platform V1<=2400s, PathA<=120s and final committed-head focused<=300s; mandatory failure stops publication, no rerun/extra correction. One Decision-only activation and one product commit, max2 normal exact-branch pushes, one activation Draft against explicit planning branch1072/base277, max6 body updates/natural CI reads, no Ready/Merge/Issue closure/comments/rewrite/dispatch/install/workflow/dependency/config changes. No claim full811/allGitHub tasks complete; analyzer/context enrichment/forge/incremental/repair remain explicit next integration requirements. Six-hour execution window. Prospective v2 resolves old-template read-only reference conflict by treating opencode_executor.py exclusively as approved edit scope. Original v1 immutable Decision-only activation/preflight BLOCKED preserved, zero source/test/model/push/Draft calls spent; no execution budget is reset or hidden. This is the sole bootstrap scope correction.",
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
        "reverse_agent/platform_v1/review_git_snapshot.py",
        "tests/platform_v1/test_review_git_snapshot.py",
        "docs/review-git-snapshot.md",
        "reverse_agent/platform_v1/review_execution.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_review_execution.py",
        "tests/platform_v1/test_review_only_api.py",
        "tests/platform_v1/test_opencode_executor.py",
        "docs/review-only-tasks.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.validate",
      "command": "At most6 development checks/3 corrections; mandatory full Platform V1 once2400s/four existing native OpenCode deselections only, PathA once120s, committed-head focused once300s. New owned short fixture root, no live models; final failure stops publication.",
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
        "reverse_agent/platform_v1/review_git_snapshot.py",
        "tests/platform_v1/test_review_git_snapshot.py",
        "docs/review-git-snapshot.md",
        "reverse_agent/platform_v1/review_execution.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_review_execution.py",
        "tests/platform_v1/test_review_only_api.py",
        "tests/platform_v1/test_opencode_executor.py",
        "docs/review-only-tasks.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.publish",
      "command": "Max2 normal exact-branch pushes, one activation Draft against codex/issue811-short-fixtures-r3-v1-20261003@277625927e39ee568f56cbf403b5107ca92e28dd; max6 body updates/natural exact-head CI reads only.",
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
    "note": "New owned F:/nrl-reviewrt1 disposable test fixtures and external issue811-review-only-runtime-r3-v2 only; existing gates/source/runtime preserved unstaged."
  },
  "follows_last_decision_id": "decision_20261004_issue811_review_only_runtime_r3_v1",
  "follows_last_round_id": "round_20261004_issue811_review_only_runtime_r3_v1",
  "workstream_id": "issue811-review-only-runtime-r3-v2",
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
  "approval_event_or_time": "2026-10-03T16:20:15.836421+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6,
  "owned_test_scratch_root": "F:\\nrl-reviewrt1",
  "mandatory_pytest_process_limit": 3
}
```

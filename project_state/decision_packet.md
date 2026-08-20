# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "round_id": "round_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260821_issue272_product_ux2b_opencode_server_r2_v4_landing",
  "follows_last_round_id": "round_20260821_issue272_product_ux2b_opencode_server_r2_v4_landing",
  "previous_audit_outcome": "ISSUE276_V2_PRE_PR_SCHEMA_V2_INTENT_COUPLING_BLOCKED_COMMENT_5359968290_ZERO_PRODUCT_COMMIT_ZERO_PUSH",
  "workstream_id": "issue276-durable-parallel-task-batches-r2-v3",
  "source_issue": 276,
  "required_branch": "owner/issue276-durable-parallel-task-batches-r2-v3",
  "starting_head": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "activation_base_sha": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "integration_base_ref": "main",
  "base_sha": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "pre_pr_intent_assertions_deferred": [
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_id",
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_locked_base_sha",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_id",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_locked_base_sha"
  ],
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_close_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md", "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue276-durable-parallel-task-batches-r2-v3 from exact main 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46 in an isolated canonical-LF checkout",
    "commit this immutable V3 Decision as the first new commit after 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46 before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue276v3.verify_baseline_and_stops",
      "command": "verify main and local base remain 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46; verify Issue 276 V1 comment 5359824526 and V2 comment 5359968290; verify both predecessors have zero product commit push or PR; preserve their transaction and pre-PR coupling evidence",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue276v3.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before product mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276v3.implement_validated_v2_product",
      "command": "recover the bounded V2 product intent only: add TaskStore-owned reentrant lock coverage to shared-connection durable transaction entrypoints without locking external executors; adapt coordinator admission to existing LangGraph Send over distinct durable tasks; add repeated barrier budget WIP failure restart and checkpoint regressions and architecture documentation; retain one store and existing modes",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_source_edit", "bounded_test_edit", "bounded_documentation_edit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276v3.prepublication_validation",
      "command": "run focused and repeated concurrency durable tests; run the CI Platform blocking gate with its ordinary seven deselections plus only the four exact pre_pr_intent_assertions_deferred entries; require 1101 or more passing tests and no other failure; run CI responsibility unchanged frontend transition lint preflight readiness and diff checks; zero live calls",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276v3.publish_initial_draft",
      "command": "after prepublication validation passes push owner/issue276-durable-parallel-task-batches-r2-v3 once and create exactly one Draft PR to main; read its actual number without guessing",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276v3.bind_actual_pr",
      "command": "archive committed PR 275 schema-v2 active intent byte-for-byte as archive/pr275_v2.json and replace active.json with schema v2 bound to the observed PR locked base this Decision committed Plan merge method merge exact three workflows and expiry 2026-08-28T23:59:59Z; commit once without Decision edit",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276v3.final_bound_validation_and_push",
      "command": "after actual PR binding run the full CI Platform blocking gate with only the ordinary seven CI deselections and require all four formerly deferred assertions pass; rerun focused repeated CI responsibility frontend transition readiness and diff checks; push the single binding commit once and observe fresh exact-head CI Decision Preflight and State Gate",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "push", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276v3.audit_attest_land",
      "command": "after workflows succeed perform clean detached exact-head audit and ACCEPTED comment; reobserve base head checks MERGEABLE CLEAN zero threads; publish schema-v2 approval attestation bound to actual comment and run IDs; owner mark-ready and merge once with merge and expected-head protection",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276v3.post_merge_verify",
      "command": "verify merge commit and origin/main; wait for State Gate push and main checks; run mainline-merge-validation; close Issue 276 only after all evidence is green",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_close", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md", "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py", "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_unattended_coordinator.py", "docs/architecture/LANGGRAPH_TEAM_RUNTIME.md",
    "project_state/mainline_merge_intents/active.json", "project_state/mainline_merge_intents/archive/pr275_v2.json",
    "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "project_state/decision_packet.md", "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json", "reverse_agent/workflows/team_graph.py",
    "reverse_agent/platform_v1/durable_execution.py", "reverse_agent/platform_v1/control_store.py", "AGENTS.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/rounds/**", "project_state/audits/**", "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**", "project_state/schemas/**", "requirements*.txt", "pyproject.toml", ".github/**",
    "reverse_agent/project_gate.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/mainline_landing.py",
    "reverse_agent/decision_preflight.py", "reverse_agent/platform_v1/control_store.py", "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_execution.py", "reverse_agent/workflows/**", "reverse_agent/architecture/**", "frontend/**", "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "live_model_call", "opencode_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "tag_or_release", "deployment", "worktree_deletion", "history_rewrite", "intent_schema_downgrade",
    "lock_held_across_external_executor", "per_worker_taskstore", "custom_production_thread_pool", "new_scheduler", "new_queue",
    "second_taskstore_or_budget_database", "executor_kind_multi_agent", "orchestration_mode_parallel_team",
    "network_attack_or_offensive_security_work"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false, "model_api_invocation_allowed": false, "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false, "credential_access_allowed": false, "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false, "destructive_operations_allowed": false, "dependency_install_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "verify main and local base remain 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46; verify Issue 276 V1 comment 5359824526 and V2 comment 5359968290; verify both predecessors have zero product commit push or PR; preserve their transaction and pre-PR coupling evidence",
      "after prepublication validation passes push owner/issue276-durable-parallel-task-batches-r2-v3 once and create exactly one Draft PR to main; read its actual number without guessing",
      "after actual PR binding run the full CI Platform blocking gate with only the ordinary seven CI deselections and require all four formerly deferred assertions pass; rerun focused repeated CI responsibility frontend transition readiness and diff checks; push the single binding commit once and observe fresh exact-head CI Decision Preflight and State Gate",
      "after workflows succeed perform clean detached exact-head audit and ACCEPTED comment; reobserve base head checks MERGEABLE CLEAN zero threads; publish schema-v2 approval attestation bound to actual comment and run IDs; owner mark-ready and merge once with merge and expected-head protection",
      "verify merge commit and origin/main; wait for State Gate push and main checks; run mainline-merge-validation; close Issue 276 only after all evidence is green"
    ],
    "ci_network_exceptions": [], "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": true, "github_issue_close_allowed": true, "github_pr_creation_allowed": true,
    "github_mark_ready_allowed": true, "github_merge_allowed": true, "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [], "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE276_DURABLE_LANGGRAPH_PARALLEL_TASK_BATCH_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE276_DURABLE_PARALLEL_TASK_BATCH_R2_V3_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Under a non-circular pre-PR validation contract, repair the shared-connection durable transaction lock boundary and make bounded unattended concurrency real through the accepted LangGraph `Send` fan-out over atomically admitted independent TaskStore tasks.

## Acceptance

1. V3 starts fresh from exact main; V1/V2 remain immutable negative evidence with zero product commit or publication.
2. Shared durable SQLite transaction entrypoints use the one TaskStore RLock; external executor work remains concurrent and twenty provider-free durable runs reach POST_VALIDATION with 100 checkpoints.
3. Coordinator admission, native Send fan-out, deterministic join, WIP, dependency, budget, mixed failure, claim fencing and restart recovery regressions pass without a second store/mode/executor/scheduler.
4. Before the PR number exists, the ordinary CI Platform gate may additionally deselect only the four exact PR-binding assertions listed in `pre_pr_intent_assertions_deferred`; no other failure is accepted.
5. After actual schema-v2 PR binding, the full ordinary Platform gate passes with only CI's seven standard deselections, including all four formerly deferred assertions.
6. Focused, repeated, CI responsibility, unchanged frontend, transition, readiness and diff checks pass with zero live calls, dependency/workflow/credential change or attack work.
7. Fresh exact-head CI/Decision/State Gate, detached audit, schema-v2 attestation, expected-head merge, push State Gate and mainline validation pass before Issue #276 closes.

## Execution policy

- Recover only the bounded V2 product intent after V3 preflight. Never downgrade or guess active intent identity.
- TaskStore remains the sole durable truth; lock SQLite critical sections only and never external executor runtime.
- Do not edit this Decision after activation. Publish once before and once after exact PR binding.
- Preserve unrelated content and stop on any scope, test, gate, remote, digest, thread or mergeability mismatch.

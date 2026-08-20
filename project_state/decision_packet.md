# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue276_durable_parallel_task_batches_r2_v1",
  "round_id": "round_20260821_issue276_durable_parallel_task_batches_r2_v1",
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
  "previous_audit_outcome": "PR275_MERGED_MAIN_3D2FA35D_STATE_GATE_PUSH_32398852971_SUCCESS",
  "workstream_id": "issue276-durable-parallel-task-batches-r2-v1",
  "source_issue": 276,
  "required_branch": "owner/issue276-durable-parallel-task-batches-r2-v1",
  "starting_head": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "activation_base_sha": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "integration_base_ref": "main",
  "base_sha": "3d2fa35d1baeec3f2b52706746e54d7f0eb0af46",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
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
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue276-durable-parallel-task-batches-r2-v1 from exact main 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46 in an isolated canonical-LF checkout",
    "commit this immutable Decision as the first new commit after 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46 before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue276.verify_baseline",
      "command": "verify origin/main and local base remain 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46; verify Issue 276 exists; inspect accepted Issue 151 LangGraph Send assets and current durable single sequential claim budget coordinator contracts; verify the target branch and Draft PR do not yet exist",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue276.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before product mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276.implement_parallel_batches",
      "command": "adapt UnattendedCoordinator to claim an admissible batch then use the accepted build_team_graph native LangGraph Send fan-out over distinct task IDs; execute each branch only through the existing durable single sequential or fixture path; finalize each claim independently and refresh affected Goals; add focused deterministic concurrency budget failure and restart regressions plus architecture documentation",
      "phase": "implementation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["bounded_source_edit", "bounded_test_edit", "bounded_documentation_edit"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276.validate_product",
      "command": "run focused coordinator team graph goal autonomy control store durable single and sequential tests including repeated barrier and restart cases; run the exact Platform V1 blocking gate CI responsibility frontend unchanged checks transition-lint transition-preflight publication readiness and git diff --check; require zero live model provider or OpenCode calls",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276.publish_initial_draft",
      "command": "after all local validation passes push owner/issue276-durable-parallel-task-batches-r2-v1 once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276.bind_actual_pr",
      "command": "using only the observed GitHub-assigned Draft PR number copy the committed schema-v2 PR 275 active intent byte-for-byte to project_state/mainline_merge_intents/archive/pr275_v2.json and replace active.json with schema version 2 bound to the actual PR locked base this Decision committed Command Plan merge method merge exact three pre-merge workflows and expiry 2026-08-28T23:59:59Z; commit exactly once without editing the Decision",
      "phase": "implementation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue276.publish_bound_head",
      "command": "rerun final bound validation; push the single PR-binding commit once; verify remote branch equals local head; observe fresh exact-head CI Decision Preflight and State Gate pull_request runs without rerun",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "push", "repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276.audit_attest_land",
      "command": "after fresh exact-head workflows succeed perform a clean detached exact-head audit and record ACCEPTED; immediately reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation bound to its actual comment ID and exact workflow run IDs; then owner-controlled mark-ready and merge once with merge method merge and expected-head protection",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue276.post_merge_verify",
      "command": "verify the PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 276 completed only after all post-merge evidence is green",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "issue_close", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "docs/architecture/LANGGRAPH_TEAM_RUNTIME.md",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr275_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "reverse_agent/workflows/team_graph.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/control_store.py",
    "AGENTS.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/rounds/**", "project_state/audits/**", "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**", "project_state/schemas/**", "requirements*.txt", "pyproject.toml", ".github/**",
    "reverse_agent/project_gate.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/mainline_landing.py",
    "reverse_agent/decision_preflight.py", "reverse_agent/platform_v1/run_store.py", "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/durable_execution.py", "reverse_agent/platform_v1/task_execution.py", "reverse_agent/workflows/**",
    "reverse_agent/architecture/**", "frontend/**", "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "live_model_call", "opencode_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "tag_or_release", "deployment", "worktree_deletion", "history_rewrite",
    "custom_production_thread_pool", "new_scheduler", "new_queue", "second_taskstore_or_budget_database",
    "executor_kind_multi_agent", "orchestration_mode_parallel_team", "network_attack_or_offensive_security_work"
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
    "dependency_install_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "verify origin/main and local base remain 3d2fa35d1baeec3f2b52706746e54d7f0eb0af46; verify Issue 276 exists; inspect accepted Issue 151 LangGraph Send assets and current durable single sequential claim budget coordinator contracts; verify the target branch and Draft PR do not yet exist",
      "after all local validation passes push owner/issue276-durable-parallel-task-batches-r2-v1 once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing",
      "rerun final bound validation; push the single PR-binding commit once; verify remote branch equals local head; observe fresh exact-head CI Decision Preflight and State Gate pull_request runs without rerun",
      "after fresh exact-head workflows succeed perform a clean detached exact-head audit and record ACCEPTED; immediately reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation bound to its actual comment ID and exact workflow run IDs; then owner-controlled mark-ready and merge once with merge method merge and expected-head protection",
      "verify the PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 276 completed only after all post-merge evidence is green"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": true,
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": true,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE276_DURABLE_LANGGRAPH_PARALLEL_TASK_BATCH_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE276_DURABLE_PARALLEL_TASK_BATCH_R2_V1_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Make bounded unattended concurrency real by adapting the coordinator to fan out an atomically admitted batch of distinct Goal tasks through the already accepted LangGraph `Send` team graph, while retaining existing per-task durable leases, checkpoints, claims, budgets, evidence and restart recovery as the only execution truth.

## Acceptance

1. This Decision is the first new commit after exact `main@3d2fa35d1baeec3f2b52706746e54d7f0eb0af46`; no product or merge-intent mutation precedes generated authority and `PRE_EXECUTION_AUTHORIZED`.
2. A coordinator tick claims and reserves up to the active window's real WIP/budget limit before dispatch, then invokes native LangGraph `Send` over distinct Task IDs. No custom production pool, scheduler, queue, new dependency or second database is introduced.
3. Every branch reuses the existing fixture or durable `single`/`sequential_team` execution path. There is no `multi_agent` executor kind and no `parallel_team` task orchestration mode.
4. Barrier evidence proves two admissible independent tasks overlap; WIP=1, dependency blocking and budget denial remain fail-closed with zero unauthorized dispatch.
5. Mixed success and worker exception reconcile the correct claim/reservation independently, preserve successful siblings, refresh all affected Goals and expose deterministic team results.
6. Expired-claim plus `INTERRUPTED` restart evidence proves a new epoch reuses the retained reservation and resumes once without duplicate dispatch. Existing per-task durable fixture and OpenCode-provider-free tests remain green.
7. Focused tests, repeated concurrency tests, exact Platform V1 gate, CI responsibility, unchanged frontend checks, transition lint/preflight, readiness and diff checks pass. No live model, provider or OpenCode call occurs.
8. The actual Draft PR number is bound through schema-v2 active intent after first publication. Fresh exact-head CI, Decision Preflight and State Gate succeed; clean detached audit accepts the head; schema-v2 owner attestation validates; owner-controlled merge uses expected-head protection.
9. Post-merge State Gate and mainline validation pass before Issue #276 closes. No direct-main push, auto-merge, force push, rebase, reset, clean, stash, history rewrite, tag, release, deployment, credential access or attack work occurs.

## Execution policy

- Treat Issue #151 as accepted reusable foundation; do not rewrite its fan-out/join graph or contracts.
- Parallelism is a coordinator batch over independent TaskStore tasks. Each task keeps its existing inner orchestration mode and durable run.
- Claim every task before it enters LangGraph. Finalize or abandon each claim exactly once and independently.
- Do not edit this Decision after activation and do not guess the Draft PR number.
- First publish one Draft PR, observe its actual number, then make one PR-binding governance commit and one final push.
- Preserve unrelated runtime/untracked content and stop on any base, path, gate, check, thread, digest or mergeability mismatch.

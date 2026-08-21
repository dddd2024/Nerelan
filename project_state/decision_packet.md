# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue282_home_goal_truth_r1_v1",
  "round_id": "round_20260821_issue282_home_goal_truth_r1_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "follows_last_round_id": "round_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "previous_audit_outcome": "ISSUE276_DURABLE_LANGGRAPH_PARALLEL_TASK_BATCH_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "workstream_id": "issue282-home-goal-truth-r1-v1",
  "source_issue": 282,
  "required_branch": "owner/issue282-home-goal-truth-r1-v1",
  "starting_head": "ecacfd94e5140151a97fb1d3d486cd992769271b",
  "activation_base_sha": "ecacfd94e5140151a97fb1d3d486cd992769271b",
  "integration_base_ref": "main",
  "base_sha": "ecacfd94e5140151a97fb1d3d486cd992769271b",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "risk_tier": "R1",
  "governance_artifact_risk_tier": "R1",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 3,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "issue_close_allowed": false,
  "mark_ready_allowed": false,
  "merge_allowed": false,
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
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/transition_lint_result.json"
  ],
  "bootstrap_exception_commands": [
    "git fetch origin main and verify origin/main == ecacfd94e5140151a97fb1d3d486cd992769271b; if not equal STOP with HARD_STOP_ISSUE282_REMOTE_MAIN_DRIFT",
    "git checkout -b owner/issue282-home-goal-truth-r1-v1 origin/main and commit this immutable Decision as the first new commit before product mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue282v1.verify_origin_main_and_worktree",
      "command": "verify origin/main == ecacfd94e5140151a97fb1d3d486cd992769271b, local branch == owner/issue282-home-goal-truth-r1-v1, and merge-base HEAD..origin/main == ecacfd94e5140151a97fb1d3d486cd992769271b; stop before any product mutation if any identity check fails",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue282v1.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before product mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue282v1.implement_authoritative_goal_state_and_home_v2",
      "command": "fix /api/goals to return authoritative task_links and reconciled goal status by reusing control_store.refresh_goal_status / list_goal_tasks in GoalService.list; redesign Home to a centered single-column layout with Goal Composer -> Current Execution (from authoritative selected goal) -> Recent Goals (<=3); reuse React Query and add focus/reconnect reconcile plus terminal polling backoff; no new polling state machine, no extra HTTP layer",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_source_edit", "bounded_test_edit"], "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ],
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/task_service.py",
        "frontend/src/routes/home.tsx",
        "frontend/src/components/goal-progress.tsx",
        "frontend/src/hooks/use-platform.ts",
        "frontend/src/lib/platform-client.ts"
      ]
    },
    {
      "command_id": "issue282v1.add_deterministic_tests",
      "command": "add backend tests proving /api/goals and /api/goals/{id} converge on goal status and task_links, all-READY_FOR_REVIEW -> COMPLETED, FAILED/BLOCKED/CANCELLED -> non-RUNNING; update frontend tests asserting no permanent right rail, Recent Goals <= 3, and Current Execution uses authoritative selected goal",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_test_edit"], "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/platform_v1/test_goal_service.py",
        "tests/platform_v1/test_task_service.py",
        "frontend/tests/platform-home.test.tsx"
      ]
    },
    {
      "command_id": "issue282v1.run_all_validation",
      "command": "run relevant frontend tests, frontend typecheck, frontend mock build, provider-free Platform V1 blocking tests, transition lint/preflight, publication readiness, git diff --check; zero live model/provider calls",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue282v1.publish_initial_draft",
      "command": "check changed-path allowlist, commit product changes once, push owner/issue282-home-goal-truth-r1-v1 once, and create exactly one Draft PR to main; do not mark ready, merge, close any issue, tag, release, or deploy",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/transition_lint_result.json",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/task_service.py",
    "frontend/src/routes/home.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/hooks/use-platform.ts",
    "frontend/src/lib/platform-client.ts",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_task_service.py",
    "frontend/tests/platform-home.test.tsx"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
    "AGENTS.md",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/transition_lint_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/workflows/**",
    "reverse_agent/architecture/**",
    "reverse_agent/control_plane/**",
    "AGENTS.md",
    "frontend/package.json",
    "frontend/package-lock.json"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "live_model_call", "opencode_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "tag_or_release", "deployment", "worktree_deletion", "history_rewrite", "mark_ready", "merge", "issue_close",
    "network_attack_or_offensive_security_work"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false, "model_api_invocation_allowed": false, "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false, "credential_access_allowed": false, "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false, "destructive_operations_allowed": false, "dependency_install_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "verify origin/main == ecacfd94e5140151a97fb1d3d486cd992769271b, local branch == owner/issue282-home-goal-truth-r1-v1, and merge-base HEAD..origin/main == ecacfd94e5140151a97fb1d3d486cd992769271b; stop before any product mutation if any identity check fails",
      "check changed-path allowlist, commit product changes once, push owner/issue282-home-goal-truth-r1-v1 once, and create exactly one Draft PR to main; do not mark ready, merge, close any issue, tag, release, or deploy"
    ],
    "ci_network_exceptions": [], "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": false, "github_issue_close_allowed": false, "github_pr_creation_allowed": true,
    "github_mark_ready_allowed": false, "github_merge_allowed": false, "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R1",
  "success_terminal": "ISSUE282_HOME_GOAL_TRUTH_R1_V1_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE282_HOME_GOAL_TRUTH_R1_V1_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Under Issue #282 make the platform's Goal list a single authoritative read path (status and task_links reconciled from linked TaskStore truth, no divergence between `/api/goals` and `/api/goals/{id}`) and replace Home's 1180+280 two-column layout with a centered single-column composition ordered Goal Composer → Current Execution → Recent Goals (≤3). Keep React Query ownership of polling, add focus/reconnect reconcile, and back off polling once the selected goal is terminal. No new polling state machine, no frontend reimplementation of the terminal state machine, no extra HTTP layer, no model calls, no dependency change, no workflow change.

## Acceptance

1. `/api/goals` returns every goal with reconciled `status` and `task_links` derived from linked TaskStore truth; `/api/goals` and `/api/goals/{id}` converge on the same goal status for the same goal.
2. All linked tasks READY_FOR_REVIEW or READY_FOR_REVIEW_FIXTURE drives the goal to COMPLETED; any linked task FAILED, BLOCKED, or CANCELLED drives the goal out of RUNNING.
3. Home is a centered single primary column (≈1080px max-width) with no permanent right rail; sections appear in order Goal Composer → Current Execution → Recent Goals (≤3); coordinator/autonomy/window state is a compact secondary status.
4. Current Execution uses the authoritative selected goal and its authoritative `task_links`; Recent Goals shows at most three entries with current status.
5. React Query remains the single polling source of truth: selected goal polled ~2-3 s, refetch on visibility change (focus) and on network reconnect; terminal selected goals stop or visibly back off polling; goal mutations invalidate both list and detail caches.
6. Deterministic tests cover backend convergence (list/detail parity, terminal-state transitions, task_link presence) and frontend structure (no permanent right rail, Recent Goals ≤ 3, Current Execution from authoritative truth); focused tests pass with zero live calls.
7. Transition lint/preflight reach `PRE_EXECUTION_AUTHORIZED`; provider-free Platform V1 blocking tests, frontend typecheck, frontend mock build, publication readiness, and `git diff --check` pass; branch pushed and Draft PR created (draft only, no mark-ready/merge/close/tag/release).

## Execution policy

- Keep TaskStore / control_store as the sole durable truth for goal status. Reuse `control_store.refresh_goal_status` and `list_goal_tasks` from `GoalService.list`; do not duplicate the terminal state machine in the browser.
- Do not introduce a second timer or state machine; React Query owns polling. Refetch on focus and reconnect; back off when the selected goal is terminal.
- Preserve sidebar, route structure, trusted-browser boundary, and mock/test infrastructure. Do not implement Issue #280 Activity Stream in this round; leave a natural slot under Current Execution for the next round.
- Do not edit this Decision after activation. Stop on scope, test, gate, remote, path, or policy drift.

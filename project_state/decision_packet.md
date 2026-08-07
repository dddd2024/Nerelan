# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_issue128_provider_free_task_plane_v1",
  "round_id": "round_20260807_issue128_provider_free_task_plane_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr121_final_owner_authority_v4",
  "follows_last_round_id": "round_20260807_pr121_final_owner_authority_v4",
  "previous_audit_outcome": "PR121_MERGED_CODEX_QUOTA_UNAVAILABLE_PROVIDER_FREE_TASK_PLANE_SELECTED",
  "workstream_id": "issue128-provider-free-task-plane-v1",
  "source_issue": 128,
  "parent_issue": 90,
  "blocked_codex_research_issue": 126,
  "future_codex_vertical_issue": 127,
  "historical_provider_free_reference_pr": 114,
  "required_branch": "owner/issue128-provider-free-task-plane-v1",
  "starting_head": "9f9b4336c58777b30eb45a85c9c2d4253ba993c1",
  "activation_base_sha": "9f9b4336c58777b30eb45a85c9c2d4253ba993c1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "normal_push_allowed": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "exact_head_workflow_observation_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "bounded_external_source_access_allowed": false,
  "frontend_dependency_installation_allowed": true,
  "loopback_frontend_runtime_allowed": true,
  "loopback_task_runtime_allowed": true,
  "repair_attempt_limit": 2,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "observation.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.merge_base",
      "command": "git merge-base origin/main owner/issue128-provider-free-task-plane-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.fetch_pr114_branch",
      "command": "git fetch origin agent/platform-v1-codex-e2e-v1",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "reference.pr114_run_store",
      "command": "git show a24d28728d3d1ad8383c24c0693aeaf5ec603767:reverse_agent/platform_v1/run_store.py",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.pr114_execution_adapters",
      "command": "git show a24d28728d3d1ad8383c24c0693aeaf5ec603767:reverse_agent/platform_v1/execution_adapters.py",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.pr114_coordinator",
      "command": "git show a24d28728d3d1ad8383c24c0693aeaf5ec603767:reverse_agent/platform_v1/coordinator.py",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "dependency.frontend_install",
      "command": "npm ci --prefix frontend",
      "phase": "dependency",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["dependency_installation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.provider_free_backend",
      "command": "python -m pytest tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_provider_free_task_plane.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.model_access_regression",
      "command": "python -m pytest tests/test_model_access.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.governance_regression",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.frontend",
      "command": "npm --prefix frontend test",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_typecheck",
      "command": "npm --prefix frontend run typecheck",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_lint",
      "command": "npm --prefix frontend run lint",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_build",
      "command": "npm --prefix frontend run build",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.frontend_mock_build",
      "command": "npm --prefix frontend run build:mock",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.provider_free_task_plane",
      "command": "python -m reverse_agent.platform_v1.provider_free_task_plane_acceptance --repo-dir F:/reverse-agent --workspace-root F:/reverse-agent-workspaces/issue128-provider-free-task-plane",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check 9f9b4336c58777b30eb45a85c9c2d4253ba993c1..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.path_list",
      "command": "git diff --name-only 9f9b4336c58777b30eb45a85c9c2d4253ba993c1..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/issue128-provider-free-task-plane-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/__init__.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/execution_adapters.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/provider_free_task_plane_acceptance.py",
    "tests/platform_v1/test_task_contracts.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_provider_free_task_plane.py",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/types/index.ts",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/src/components/task-card.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/components/activity-stream.tsx",
    "frontend/src/components/changes-panel.tsx",
    "frontend/src/components/evidence-panel.tsx",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "frontend/tests/workspace.test.tsx",
    "frontend/tests/states.test.tsx",
    "frontend/tests/model-task-composer.test.tsx",
    "docs/platform_v1/provider_free_task_plane.md"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/fixtures/tasks.ts",
    "frontend/src/routes/task-detail.tsx",
    "reverse_agent/model_access/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "project_state/schemas/**",
    "tests/test_model_access.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py"
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
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/workflows/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/fixtures/tasks.ts",
    "frontend/src/routes/**",
    "frontend/src/components/model-profile-editor.tsx",
    "frontend/src/hooks/use-model-profiles.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/schemas/model-profile.ts",
    "reverse_agent/model_access/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/unattended/**",
    "reverse_agent/executor_neutral/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/**",
    "docs/model-access.md"
  ],
  "forbidden_operations": [
    "model_api_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "native_multiagent",
    "third_party_provider_test",
    "credential_access",
    "credential_publication",
    "direct_push_main",
    "create_pr",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "reset_hard",
    "git_clean",
    "tag_or_release",
    "release",
    "deployment",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "wholesale_pr114_port",
    "unbounded_network_access"
  ],
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
    "local_network_exceptions": [
      "git fetch origin agent/platform-v1-codex-e2e-v1",
      "npm ci --prefix frontend",
      "git push origin owner/issue128-provider-free-task-plane-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "reverse_agent/platform_v1/**",
    "tests/platform_v1/**",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/types/index.ts",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/src/components/task-card.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/components/activity-stream.tsx",
    "frontend/src/components/changes-panel.tsx",
    "frontend/src/components/evidence-panel.tsx",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "frontend/tests/workspace.test.tsx",
    "frontend/tests/states.test.tsx",
    "frontend/tests/model-task-composer.test.tsx",
    "docs/platform_v1/provider_free_task_plane.md"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/platform_v1/**", "minimum_risk": "R2"},
    {"pattern": "frontend/src/hooks/use-tasks.ts", "minimum_risk": "R2"},
    {"pattern": "frontend/src/hooks/use-task.ts", "minimum_risk": "R2"},
    {"pattern": "frontend/src/lib/task-client.ts", "minimum_risk": "R2"}
  ]
}
```

## Goal

Implement Issue #128 as a provider-free task plane while Codex quota is unavailable. The round must connect the existing Frontend V1 task workspace to server-owned loopback task state and prove one deterministic non-model executor path in a disposable workspace.

Selected architecture:

```text
Frontend task hooks
  -> Task API client
  -> loopback-only trusted TaskService
  -> SQLite task/event store
  -> ExecutorRouter
  -> DeterministicFixtureExecutor
  -> disposable Git worktree/fixture
  -> LocalValidationRunner
  -> normalized task/activity/changed-file/evidence readback
```

The historical PR #114 is reference evidence, not a merge source. Port only the smallest compatible SQLite/worktree/validation concepts. Do not activate or execute CodexExecutorAdapter, do not port the PR #114 GitHub publication tail, and do not build a generic scheduler.

## Acceptance

1. Decision commit exists on `owner/issue128-provider-free-task-plane-v1` before generated gates or product mutation.
2. Generated transition artifacts bind this Decision and the exact base `9f9b4336c58777b30eb45a85c9c2d4253ba993c1`.
3. `transition-lint` passes and preflight reports `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]` before product mutation.
4. `POST /api/tasks`, `GET /api/tasks`, `GET /api/tasks/{id}`, and `GET /api/tasks/{id}/events` are loopback-only and enforce the same Origin fail-closed boundary pattern as model-control without sharing provider secrets/state.
5. Task state is server-owned and durable outside React Query cache; client idempotency keys do not create duplicate tasks.
6. The only executor implementation in this round is `DeterministicFixtureExecutor`; no Codex/OpenHands/model process or API is started.
7. A deterministic mutation occurs only in an approved disposable fixture/worktree, validation is captured, and normalized events/changed paths/evidence are persisted.
8. Frontend task list/detail/create flows read backend truth and visibly label the execution as fixture/provider-free; they never claim Codex completion.
9. Historical PR #114 components are selectively ported/adapted only where needed; no wholesale port or GitHub publication runtime is introduced.
10. Required backend/frontend/regression tests, typecheck, lint, production build, mock build, provider-free acceptance, and exact-base `git diff --check` pass.
11. Final diff contains only `allowed_mutated_paths`.
12. The tested branch is normally pushed to `origin/owner/issue128-provider-free-task-plane-v1` and execution stops. No PR creation, mark-ready, merge, main push, release, deployment, credential access, provider test, or live model call occurs.

Terminal:

```text
PROVIDER_FREE_TASK_PLANE_READY_FOR_OWNER_AUDIT
```

## Execution policy

- Treat Issue #128 and its comments as planning context only; this Decision plus generated Command Plan are the Path-B execution authority.
- Do not wait for Codex quota. This round is specifically designed to complete without Codex/model execution.
- Keep the task service separate from model-profile secret storage. Only sanitized model profile identifiers/references may cross the browser/task API boundary.
- Prefer bounded polling for events in V1 unless the existing stack makes SSE materially simpler without new dependencies.
- Do not modify frontend dependencies or Python dependencies in this round.
- Do not create a one-click launcher yet; defer `scripts/dev-up.ps1` until this task-plane acceptance is green so startup work cannot hide task-plane defects.
- Do not create or update a PR. Stop after exact tested branch push for independent Owner audit and the next landing authority decision.

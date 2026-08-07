# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_issue128_provider_free_task_plane_v4",
  "round_id": "round_20260807_issue128_provider_free_task_plane_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_issue128_provider_free_task_plane_v3",
  "follows_last_round_id": "round_20260807_issue128_provider_free_task_plane_v3",
  "previous_audit_outcome": "ISSUE128_V3_OWNER_AUDIT_REPAIR_REQUIRED_F5A_F6A",
  "workstream_id": "issue128-provider-free-task-plane-v4",
  "source_issue": 128,
  "parent_issue": 90,
  "blocked_codex_research_issue": 126,
  "future_codex_vertical_issue": 127,
  "historical_provider_free_reference_pr": 114,
  "required_branch": "owner/issue128-provider-free-task-plane-v1",
  "starting_head": "43a8a1351ca9ed5d6fc7fad824efb08126727212",
  "activation_base_sha": "9f9b4336c58777b30eb45a85c9c2d4253ba993c1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
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
  "fail_forward_repair_findings": [
    "I128-V3-F5A",
    "I128-V3-F6A"
  ],
  "final_diff_must_not_contain": [
    "reverse_agent/platform_v1/task_service_mapping.py"
  ],
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
      "command_id": "sync.fetch_issue128_branch",
      "command": "git fetch origin owner/issue128-provider-free-task-plane-v1",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
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
      "operations": ["dependency_install", "network_access"],
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
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/provider-free-task-plane.test.tsx"
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
      "git fetch origin owner/issue128-provider-free-task-plane-v1",
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
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/provider-free-task-plane.test.tsx"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/src/hooks/use-tasks.ts", "minimum_risk": "R2"},
    {"pattern": "frontend/src/lib/task-client.ts", "minimum_risk": "R2"}
  ]
}
```

## Goal

Fail-forward repair of Issue #128 v3 owner audit findings I128-V3-F5A and I128-V3-F6A.

The v3 implementation passed five of six original findings but failed Owner audit on two residual frontend issues:

- I128-V3-F5A: `useCreateTask().mutationFn` generates `crypto.randomUUID()` inside the mutation. The idempotency key must be produced once at the submit boundary (NewTaskComposer -> CreateTaskInput -> useCreateTask -> createTask -> HTTP), so that a retry of the same logical submit reuses the same key.
- I128-V3-F6A: The frontend create flow currently does POST create -> POST execute -> returns execute response directly. It must instead do POST /api/tasks -> POST /api/tasks/{id}/execute -> GET /api/tasks/{id} and return the GET readback truth, not the execute response.

Only frontend product files and the v4 governance/gate artifacts are in scope. Backend files are frozen. No new features, no new executor kinds, no new dependencies.

## Acceptance

1. v4 Decision is committed before any product mutation; v3 and v2 historical commits remain immutable.
2. Generated transition artifacts bind this v4 Decision and exact base `9f9b4336c58777b30eb45a85c9c2d4253ba993c1`.
3. `transition-lint` passes and preflight reports `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]` before product mutation.
4. I128-V3-F5A: NewTaskComposer generates `crypto.randomUUID()` once at the submit click boundary and places it into `CreateTaskInput.idempotencyKey`. `useCreateTask` and `createTask` do not generate a UUID; they only forward `input.idempotencyKey` as `idempotency_key`. A retry of the same mutation variables produces the same POST body `idempotency_key`.
5. I128-V3-F6A: `useCreateTask` sequence is exactly POST /api/tasks -> POST /api/tasks/{id}/execute -> GET /api/tasks/{id}. The returned Task comes from the GET readback. A frontend test proves the HTTP call order and proves the returned `updatedAt` matches the GET readback, not the execute response.
6. Frontend HTTP-flow test asserts exactly three fetch calls in order: POST /api/tasks, POST /api/tasks/{id}/execute, GET /api/tasks/{id}; and that execute response and GET readback carry distinct `updatedAt` values, with the mutation returning the GET readback value.
7. Idempotency regression test asserts that `CreateTaskInput.idempotencyKey` flows through to POST body `idempotency_key`, and that no UUID is generated inside `mutationFn`.
8. Final diff contains only the allowed v4 paths; no backend `reverse_agent/platform_v1/**` files touched; no `task_service_mapping.py`.
9. No Codex, OpenHands, or model/provider calls during runtime. `Codex runtime calls = 0`, `OpenHands runtime calls = 0`, `model/provider runtime calls = 0`.
10. Backend regression tests pass unmodified.
11. Branch pushed to origin; no PR, merge, release, deploy, or credential access.

## Execution policy

- v4 is a fail-forward repair of v3 findings F5A and F6A. Do not modify v3 or v2 historical commits.
- Do not re-design #128; do not widen scope. If a test requires a file outside the v4 scope, STOP and report.
- Do not touch backend files (`reverse_agent/platform_v1/**`).
- No new dependencies, no executor kinds, no model API, no scheduler.
- Do not create or update a PR. Stop after exact tested branch push for independent Owner audit.

Terminal:

```text
ISSUE128_V4_REPAIR_READY_FOR_OWNER_AUDIT
```

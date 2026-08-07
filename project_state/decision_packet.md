# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_pr121_model_access_land_v1",
  "round_id": "round_20260807_pr121_model_access_land_v1",
  "status": "APPROVED",
  "mainline": "model_access",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260806_issue117_frontend_v1_openhands_ui_v4",
  "follows_last_round_id": "round_20260806_issue117_frontend_v1_openhands_ui_v4",
  "previous_audit_outcome": "PR119_MERGED",
  "workstream_id": "pr121-model-access-landing-v1",
  "source_issue": 122,
  "parent_issue": 90,
  "selected_foundation_issue": 120,
  "backend_reference_pr": 120,
  "active_pr": 121,
  "required_branch": "owner/model-access-frontend-closeout-v1",
  "starting_head": "5c8681ebd5fa0dc9c6fccc79e4b2380255fbebdf",
  "activation_base_sha": "68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "model_execution_required": false,
  "bounded_external_source_access_allowed": false,
  "frontend_dependency_installation_allowed": true,
  "loopback_frontend_runtime_allowed": true,
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
      "command_id": "test.model_access_pytest",
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
      "command_id": "test.typecheck",
      "command": "npm --prefix frontend run typecheck",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.lint",
      "command": "npm --prefix frontend run lint",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "build.frontend",
      "command": "npm --prefix frontend run build",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "build.frontend_mock",
      "command": "npm --prefix frontend run build:mock",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.npm_audit",
      "command": "npm --prefix frontend audit --omit=dev --audit-level=high",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "runtime.frontend_mock",
      "command": "npm --prefix frontend run dev:mock -- --host 127.0.0.1 --port 4173",
      "phase": "visual_validation",
      "required": false,
      "expected_exit_codes": [0, 130],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "diagnostic_only": true
    },
    {
      "command_id": "runtime.model_control_service",
      "command": "python -m reverse_agent.model_access.service",
      "phase": "visual_validation",
      "required": false,
      "expected_exit_codes": [0, 130],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "diagnostic_only": true
    },
    {
      "command_id": "governance.stage_generated_gates",
      "command": "git add project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/bootstrap_state.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "commit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_changes"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "governance.commit_generated_gates",
      "command": "git commit -m \"governance: generate PR 121 model access command plan\"",
      "phase": "commit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "implementation.stage_model_access",
      "command": "git add reverse_agent/model_access tests/test_model_access.py project_state/mainline_merge_intents",
      "phase": "commit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_changes"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "implementation.commit_model_access",
      "command": "git commit -m \"fix(model-access): enforce server-side Origin gate MA-ORIGIN-001\"",
      "phase": "commit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
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
      "command": "git diff --name-only origin/main...HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.gate_test",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/model-access-frontend-closeout-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.pr121",
      "command": "gh pr view 121 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.pr121_checks",
      "command": "gh pr checks 121 --repo dddd2024/reverse-agent --watch",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/**",
    ".github/workflows/model-access.yml",
    "docs/model-access.md",
    "docs/superpowers/plans/2026-08-06-model-access-and-frontend-closeout.md",
    "docs/superpowers/specs/2026-08-06-model-access-and-frontend-closeout-design.md",
    "frontend/**",
    "reverse_agent/model_access/**",
    "tests/test_model_access.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "project_state/schemas/**"
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
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/platform_v1/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "tests/test_minimal_integration_baseline_docs.py"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "pr_114_changes",
    "platform_v1_fresh_port",
    "openhands_integration",
    "provider_expansion",
    "real_provider_probe",
    "live_provider_test",
    "reset_hard",
    "git_clean"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "npm --prefix frontend test",
      "npm --prefix frontend run typecheck",
      "npm --prefix frontend run lint",
      "npm --prefix frontend run build",
      "npm --prefix frontend run build:mock",
      "npm --prefix frontend audit --omit=dev --audit-level=high",
      "git push origin owner/model-access-frontend-closeout-v1",
      "gh pr view 121 --repo dddd2024/reverse-agent",
      "gh pr checks 121 --repo dddd2024/reverse-agent"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/**",
    "reverse_agent/model_access/**",
    "tests/test_model_access.py"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Implement MA-ORIGIN-001: a server-side Origin gate in the model-control HTTP service. Currently the service only conditionally emits `Access-Control-Allow-Origin` for matching Origins, but does not reject foreign Origins before handler side effects. The gate must ensure:

1. Requests with no Origin header are allowed (trusted loopback CLI / non-browser clients).
2. Requests with Origin equal to the configured `allowed_origin` are allowed with normal CORS response.
3. Requests with an Origin header present and not equal to `allowed_origin` are rejected with HTTP 403 before any store mutation or handler logic runs.
4. OPTIONS preflight for foreign Origins fails closed (no permissive-looking preflight response).
5. The 403 response body must not contain secrets, reflected API keys, request body content, or exception stack traces.

The existing loopback-only binding, live-probe default-disabled, and secret-not-in-log/response/browser-storage invariants must be preserved.

## Acceptance

1. Generated Command Plan and transition preflight bind PR #121 v1 Decision and report `PRE_EXECUTION_AUTHORIZED` with no blockers.
2. Only the authorized PR #121 delta paths and standard generated gate artifacts change.
3. `python -m pytest tests/test_model_access.py -q` passes with new HTTP boundary tests covering all six Origin-gate scenarios.
4. Frontend test, typecheck, lint, build, mock build, and npm audit pass.
5. Server-side Origin gate is exercised at the HTTP boundary, not only at the helper-function level.
6. Foreign Origin PUT/POST/DELETE requests do not mutate the model profile store.
7. 403 error body does not contain any submitted secret value.
8. Local UI/UAT passes: Settings page loads, profile CRUD works, default profile works, New Task blocks without valid profile, no API key in browser storage, no API key in service response, no secret leak in UI, desktop and mobile layout are intact.
9. All local work committed normally, exact branch pushed, PR #121 remains Draft against `main` for Owner audit.
10. No main push, merge, mark-ready, history rewrite, tag, release, real provider probe, deployment, credential access, or unrelated PR work occurs.

```text
PR121_MODEL_ACCESS_LANDING_V1_PENDING_AUTHORIZATION
```

## Execution policy

- This Decision is independent of the PR #119 (Issue #117) and PR #112 (Issue #111) Decisions.
- Run the standard Path-B gate sequence before modifying any product code.
- The Origin gate check must execute before any route handler logic for GET, PUT, POST, DELETE, and OPTIONS.
- 403 responses must be opaque: no secret reflection, no request body echo, no exception stack trace.
- Loopback binding and live-probe default-disabled invariants must be preserved.
- Two product-repair attempts and one infrastructure retry are allowed; do not stop for one ordinary test failure.
- Stop for authority mismatch, unexpected path, secret exposure risk, base/branch conflict, or exhausted bounded attempts.
- Publication is limited to the exact branch and exact-head workflow observation.
- No real provider credentials, live provider probes, or model execution.

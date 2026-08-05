# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260805_issue117_frontend_v1_openhands_ui_v1",
  "round_id": "round_20260805_issue117_frontend_v1_openhands_ui_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260804_issue111_pr112_bootstrap_path_tree_seal_v6",
  "follows_last_round_id": "round_20260804_issue111_pr112_bootstrap_path_tree_seal_v6",
  "previous_audit_outcome": "PR112_BOOTSTRAP_V6_MERGED_TO_MAIN_FRONTEND_V1_AUTHORITY_REQUIRED",
  "workstream_id": "issue117-frontend-v1-openhands-ui-v1",
  "source_issue": 117,
  "parent_issue": 90,
  "selected_foundation_issue": 116,
  "backend_reference_pr": 114,
  "active_pr": 119,
  "required_branch": "agent/frontend-v1-openhands-ui",
  "starting_head": "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507",
  "activation_base_sha": "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507",
  "selected_upstream_repository": "OpenHands/OpenHands",
  "selected_upstream_tag": "1.8.0",
  "selected_upstream_commit": "c7a765d900df294cbbf0f405ae26c9cbbd0fcc29",
  "selected_upstream_license": "MIT",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "draft_pr_creation_allowed": true,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "branch_creation_allowed": true,
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
  "bounded_external_source_access_allowed": true,
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
      "command_id": "observation.node_version",
      "command": "node --version",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.npm_version",
      "command": "npm --version",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.clone_openhands",
      "command": "git clone --filter=blob:none --depth 1 --branch 1.8.0 https://github.com/OpenHands/OpenHands.git F:/reverse-agent-upstreams/OpenHands-1.8.0",
      "phase": "preparation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "upstream.verify_openhands",
      "command": "git -C F:/reverse-agent-upstreams/OpenHands-1.8.0 rev-parse HEAD",
      "phase": "preparation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "dependency.npm_install",
      "command": "npm install --ignore-scripts",
      "phase": "preparation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "test.frontend",
      "command": "npm test",
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
      "command": "npm run typecheck",
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
      "command": "npm run lint",
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
      "command": "npm run build",
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
      "command": "npm run build:mock",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.frontend_mock",
      "command": "npm run dev:mock -- --host 127.0.0.1 --port 4173",
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
      "command_id": "validation.diff_check",
      "command": "git diff --check 1142dd324fdd4c4bf2a1353d9d5e93bc04b33507..HEAD",
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
      "command": "git diff --name-only 1142dd324fdd4c4bf2a1353d9d5e93bc04b33507..HEAD",
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
      "command": "git push origin agent/frontend-v1-openhands-ui",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.pr119",
      "command": "gh pr view 119 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.pr119_checks",
      "command": "gh pr checks 119 --repo dddd2024/reverse-agent --watch",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.pr119_edit",
      "command": "gh pr edit 119 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_body_update", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.pr119_comment",
      "command": "gh pr comment 119 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.issue117_comment",
      "command": "gh issue comment 117 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["issue_comment", "network_access"],
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
    "frontend/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".github/workflows/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/platform_v1/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
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
    "reverse_agent/**",
    "tests/**",
    "docs/**",
    "deploy/**",
    "examples/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/**"
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
    "package_publication",
    "container_publication",
    "deployment",
    "credential_access",
    "credential_publication",
    "production_api_mutation",
    "model_api_invocation",
    "runner_dispatch",
    "live_openhands_backend",
    "live_openhands_agent_runtime",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "modify_pr_106",
    "continue_issue118_backend_implementation",
    "publish_sites",
    "unbounded_network_access",
    "copy_enterprise_code"
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
      "git clone --filter=blob:none --depth 1 --branch 1.8.0 https://github.com/OpenHands/OpenHands.git F:/reverse-agent-upstreams/OpenHands-1.8.0",
      "npm install --ignore-scripts",
      "git push origin agent/frontend-v1-openhands-ui",
      "gh pr view 119 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "gh pr checks 119 --repo dddd2024/reverse-agent --watch",
      "gh pr edit 119 --repo dddd2024/reverse-agent --body-file -",
      "gh pr comment 119 --repo dddd2024/reverse-agent --body-file -",
      "gh issue comment 117 --repo dddd2024/reverse-agent --body-file -"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "frontend/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/package.json", "minimum_risk": "R2"},
    {"pattern": "frontend/package-lock.json", "minimum_risk": "R2"}
  ]
}
```

## Goal

Build a fixture-driven reverse-agent Frontend V1 by adapting the non-enterprise OpenHands 1.8.0 UI foundation at exact commit `c7a765d900df294cbbf0f405ae26c9cbbd0fcc29`. Provide a task inbox, task detail, activity/evidence stream, file/diff views, Platform V1 authority summaries, four controller permission profiles, and a bounded custom overnight-policy editor. The result remains frontend-only.

## Acceptance

1. Generated Command Plan and transition preflight bind this Decision and report `PRE_EXECUTION_AUTHORIZED` with no blockers.
2. Only `frontend/**` and the standard generated gate artifacts change.
3. OpenHands 1.8.0 exact commit is verified; only non-enterprise source is reused; MIT notices and a source-to-target reuse map are recorded.
4. Task inbox and task-detail screens work with deterministic fixtures and cover loading, empty, error, activity, changes, evidence, and responsive states.
5. `ASK_FOR_APPROVAL`, `CONTROLLER_REVIEW`, `OWNER_CONTROL`, and `CUSTOM` profiles work.
6. `CUSTOM` independently configures merge, push-main, tag/release, package/container publication, preview/staging/production deployment, rollback, scopes, checks, budgets, expiry, retries, and stop conditions.
7. The frontend validates and serializes policy objects and displays a plain-language authorization summary but performs no privileged side effect.
8. `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`, `npm run build:mock`, and the exact diff check pass.
9. Deterministic desktop and narrow screenshots are captured without credentials or absolute local paths.
10. The exact branch is normally pushed and PR #119 remains Draft against `main` for independent Owner audit.
11. No main push, merge, mark-ready, history rewrite, tag, release, publication, deployment, credential access, model invocation, OpenHands backend/runtime, workflow change, PR #106 mutation, or Issue #118 implementation occurs.

```text
FRONTEND_V1_OPENHANDS_PERMISSION_POLICY_PROTOTYPE_READY_FOR_OWNER_REVIEW
```

## Execution policy

- Run the standard Path-B gate sequence before modifying `frontend/**`.
- Use only the fixed OpenHands repository, tag, and commit; fail closed on mismatch.
- Clone upstream only into `F:/reverse-agent-upstreams/OpenHands-1.8.0` and never execute its backend, agent runtime, Docker, provider, or credential flows.
- Install dependencies with lifecycle scripts disabled and keep all frontend dependencies under `frontend/**`.
- Use deterministic fixture data only.
- Two product-repair attempts and one infrastructure retry are allowed; do not stop for one ordinary test failure.
- Stop for authority mismatch, unexpected path, secret exposure risk, base/branch conflict, upstream commit mismatch, or exhausted bounded attempts.
- Publication is limited to the exact branch, PR #119 Draft updates/comments, Issue #117 evidence comments, and exact-head workflow observation.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_pr121_model_access_land_v2",
  "round_id": "round_20260807_pr121_model_access_land_v2",
  "status": "APPROVED",
  "mainline": "model_access",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr121_model_access_land_v1",
  "follows_last_round_id": "round_20260807_pr121_model_access_land_v1",
  "previous_audit_outcome": "PR121_V1_PENDING_BASE_RECONCILIATION",
  "workstream_id": "pr121-model-access-landing-v2",
  "source_issue": 122,
  "parent_issue": 90,
  "selected_foundation_issue": 120,
  "backend_reference_pr": 120,
  "active_pr": 121,
  "required_branch": "owner/model-access-frontend-closeout-v1",
  "starting_head": "5de53389a3cf0a6557f2a0bb837eee4a5d5687fe",
  "activation_base_sha": "5de53389a3cf0a6557f2a0bb837eee4a5d5687fe",
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
  "merge_allowed": true,
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
  "bootstrap_state_initial": "BOOTSTRAP_COMPLETE",
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
      "command_id": "reconciliation.merge_origin_main",
      "command": "git merge --no-ff origin/main",
      "phase": "reconciliation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["merge", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md",
        "project_state/gates/**",
        "project_state/mainline_merge_intents/**"
      ]
    },
    {
      "command_id": "reconciliation.resolve_decision_conflicts",
      "command": "git diff --check",
      "phase": "reconciliation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
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
      "command": "git merge-base origin/main owner/model-access-frontend-closeout-v1",
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
      "command": "git commit -m \"governance: generate PR 121 model access v2 command plan\"",
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
      "command": "git commit -m \"fix(model-access): enforce server-side Origin gate MA-ORIGIN-001 v2\"",
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
    "docs/model-access.md",
    "docs/superpowers/plans/2026-08-06-model-access-and-frontend-closeout.md",
    "docs/superpowers/specs/2026-08-06-model-access-and-frontend-closeout-design.md",
    "frontend/**",
    "reverse_agent/model_access/**",
    "tests/test_model_access.py",
    "tests/platform_v1/**"
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
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
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

PR #121 v2 current-main reconciliation. The v1 Decision (`decision_20260807_pr121_model_access_land_v1`) was authorized against an activation_base_sha of `68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d`, but `origin/main` has advanced to `5de53389a3cf0a6557f2a0bb837eee4a5d5687fe`. The PR branch is 7 commits behind current main and 44 commits ahead.

This v2 Decision authorizes:

1. A normal non-rebase merge of `origin/main@5de53389` into `owner/model-access-frontend-closeout-v1`
2. Refresh of the active merge-intent to bind `locked_base_sha=5de53389`
3. Fix of MA-TEST-001 to add post-state HTTP boundary verification that the store is unchanged after a foreign-origin 403
4. Full local verification (pytest, frontend tests/typecheck/lint/build, npm audit, gate tests)
5. Normal push of the existing PR #121 branch

No new product functionality is introduced in this round.

## Acceptance

1. v2 Decision commit is authored before any reconciliation or implementation work.
2. Normal merge of origin/main into the PR branch succeeds without rebase, force-push, or history rewrite.
3. The v2 Decision and v1 historical archive are preserved; no historical governance artifacts are deleted.
4. Active merge intent (`project_state/mainline_merge_intents/active.json`) is updated with `locked_base_sha: 5de53389a3cf0a6557f2a0bb837eee4a5d5687fe` and `allowed_merge_method: merge`.
5. MA-TEST-001 adds a real HTTP-boundary post-state check: after a foreign-origin PUT receives 403, a follow-up allowed-Origin GET confirms the injected profile does not exist in the store.
6. `python -m pytest tests/test_model_access.py -q` passes with the enhanced test.
7. Frontend test, typecheck, lint, build, mock build, and npm audit pass.
8. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
9. `git diff --check` passes.
10. Local UAT: Settings page loads, profile CRUD works, default profile works, New Task blocks without valid profile, no API key in browser storage/response/UI, desktop and mobile layout intact.
11. All local work committed normally, exact branch pushed, PR #121 remains Draft against `main` for Owner audit.
12. No main push, merge PR, mark-ready, history rewrite, tag, release, real provider probe, deployment, credential access, or unrelated PR work occurs.

```text
PR121_AUTHORIZED_CURRENT_MAIN_HEAD_READY_FOR_OWNER_GITHUB_AUDIT
```

## Execution policy

- This v2 Decision follows and supersedes the v1 Decision for current-main landing authority only.
- The v1 Decision (`decision_20260807_pr121_model_access_land_v1`) is immutable and is preserved as the historical baseline for the initial authorization window.
- Run the standard Path-B gate sequence: transition-lint, transition-command-plan, transition-preflight (pre), before modifying any product code.
- Reconciliation must be a normal non-rebase merge (`git merge --no-ff origin/main`) — no rebase, no force push, no reset-hard, no history rewrite.
- After merge, transition-preflight must report `PRE_EXECUTION_AUTHORIZED` with the new `activation_base_sha` matching the post-merge `merge-base`.
- The Origin gate check must execute before any route handler logic for GET, PUT, POST, DELETE, and OPTIONS.
- 403 responses must be opaque: no secret reflection, no request body echo, no exception stack trace.
- Loopback binding and live-probe default-disabled invariants must be preserved.
- Two product-repair attempts and one infrastructure retry are allowed; do not stop for one ordinary test failure.
- Stop for authority mismatch, unexpected path, secret exposure risk, base/branch conflict, or exhausted bounded attempts.
- Publication is limited to the exact branch and exact-head workflow observation.
- No real provider credentials, live provider probes, or model execution.

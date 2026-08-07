# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_pr121_model_access_final_land_v3",
  "round_id": "round_20260807_pr121_model_access_final_land_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr121_model_access_land_v2",
  "follows_last_round_id": "round_20260807_pr121_model_access_land_v2",
  "previous_audit_outcome": "PR121_V2_INCOMPATIBLE_MAINLINE_CONTRACT",
  "workstream_id": "pr121-model-access-landing-v3",
  "source_issue": 122,
  "parent_issue": 90,
  "selected_foundation_issue": 120,
  "backend_reference_pr": 120,
  "active_pr": 121,
  "required_branch": "owner/model-access-frontend-closeout-v1",
  "starting_head": "9bcef389cd587d6b8a128fecc7a6dfd315d6c523",
  "activation_base_sha": "5de53389a3cf0a6557f2a0bb837eee4a5d5687fe",
  "allowed_merge_method": "merge",
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
  "mark_ready_allowed": true,
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
      "command_id": "validation.ci_failed_suites",
      "command": "python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.platform_v1",
      "command": "python -m pytest tests/platform_v1 -q",
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

PR #121 v3 governance closeout. The v2 Decision (`decision_20260807_pr121_model_access_land_v2`) was authorized with `mainline=model_access`, but the canonical mainline landing contract (`reverse_agent/mainline_landing.py`) requires `mainline=engineering_branch`. This v2 Decision was therefore incompatible with the CI-governance contract, producing `FAIL_GOVERNANCE_CONTRACT` on exact-head CI.

This v3 Decision fixes the mainline value to `engineering_branch` and authorizes governance closeout:

1. Immutable v3 Decision with `mainline=engineering_branch`
2. Restore historical `archive/pr112_v6.json` to exact `origin/main` bytes
3. Archive current v2 active intent as `archive/pr121_v2.json`
4. Update active merge intent to bind v3 Decision and command plan
5. Generate v3 gate sequence (startup-snapshot, command-plan, lint, preflight)
6. Run all CI-failing suites and Platform V1 tests to confirm green
7. Normal push of the existing PR #121 branch

No new product functionality is introduced in this round.

## Acceptance

1. v3 Decision commit is authored before any gate generation or intent modification.
2. Historical archive `project_state/mainline_merge_intents/archive/pr112_v6.json` matches `origin/main` blob exactly (SHA-1 `ed960c0e117051e8915b457028e4c0e5f0c3e07c`).
3. Current v2 active intent archived as `archive/pr121_v2.json` before modification.
4. Active intent updated to bind v3 Decision, v3 command plan, `source_pr=121`, `locked_base_sha=5de53389a3cf0a6557f2a0bb837eee4a5d5687fe`, `allowed_merge_method=merge`.
5. `python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q` passes.
6. `python -m pytest tests/platform_v1 -q` passes.
7. `python -m pytest tests/test_model_access.py -q` passes.
8. Frontend test, typecheck, lint, build, mock build, and npm audit pass.
9. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
10. v3 gate sequence reports `transition-lint: PASS`, `transition-preflight: PRE_EXECUTION_AUTHORIZED`.
11. `git diff --check` passes.
12. Local UAT: Settings page loads, profile CRUD works, default profile works, New Task blocks without valid profile, no API key in browser storage/response/UI, desktop and mobile layout intact.
13. All local work committed normally, exact branch pushed, PR #121 remains Draft against `main` for Owner audit.
14. `reverse_agent/mainline_landing.py` is NOT modified.
15. No main push, merge PR, mark-ready, history rewrite, tag, release, real provider probe, deployment, credential access, or unrelated PR work occurs.

```text
PR121_V3_AUTHORIZED_EXACT_HEAD_READY_FOR_OWNER_LANDING_AUDIT
```

## Execution policy

- This v3 Decision follows and supersedes the v2 Decision for PR #121 final landing authority only.
- The v2 Decision (`decision_20260807_pr121_model_access_land_v2`) is immutable and preserved as the historical baseline for the v2 reconciliation window.
- Run the standard Path-B gate sequence: transition-lint, transition-command-plan, transition-preflight (pre), before any intent modification.
- `mainline` must be `engineering_branch` to satisfy the canonical mainline landing contract.
- Do NOT modify `reverse_agent/mainline_landing.py` to accept `model_access`.
- Do NOT modify the v2 Decision.
- v3 is authorized for Owner attestation, mark Ready, and merge method=merge; local Agent must NOT execute `gh pr ready`, `gh pr merge`, or push to main.
- Publication is limited to the exact branch and normal push.
- No real provider credentials, live provider probes, or model execution.

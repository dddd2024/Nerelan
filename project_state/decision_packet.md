# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_pr129_provider_free_task_plane_landing_v5",
  "round_id": "round_20260807_pr129_provider_free_task_plane_landing_v5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_issue128_provider_free_task_plane_v4",
  "follows_last_round_id": "round_20260807_issue128_provider_free_task_plane_v4",
  "previous_audit_outcome": "PR129_CI_STALE_PR121_MAINLINE_INTENT",
  "workstream_id": "pr129-provider-free-task-plane-landing-v5",
  "source_issue": 128,
  "parent_issue": 90,
  "active_pr": 129,
  "required_branch": "owner/issue128-provider-free-task-plane-v1",
  "starting_head": "80761ed427e142f8cbd94a233c178618960a637c",
  "activation_base_sha": "9f9b4336c58777b30eb45a85c9c2d4253ba993c1",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": true,
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
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
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
      "command_id": "test.mainline_landing",
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
      "command_id": "test.platform_v1",
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
      "command_id": "test.gate_regression",
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
      "command": "git diff --name-only 80761ed427e142f8cbd94a233c178618960a637c..HEAD",
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr121_v4.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py",
    "tests/test_project_audits.py",
    "tests/platform_v1/**",
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
    ".github/**",
    "frontend/**",
    "docs/**",
    "reverse_agent/**",
    "tests/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
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
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "create_pr",
    "pr_creation",
    "draft_pr_creation",
    "pr_body_update",
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
    "mark_ready_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git fetch origin owner/issue128-provider-free-task-plane-v1",
      "git push origin owner/issue128-provider-free-task-plane-v1",
      "gh pr view 129 --repo dddd2024/reverse-agent",
      "gh pr checks 129 --repo dddd2024/reverse-agent"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

PR #129 v5 Owner landing governance-only round. The v4 product implementation head `80761ed427e142f8cbd94a233c178618960a637c` has passed local provider-free acceptance and all GitHub exact-head checks (Model Access, Decision Preflight, State Gate). The only remaining CI failure is in `tests/test_mainline_landing.py`:

- `test_committed_active_intent_binds_exact_current_authority`
- `test_production_pre_merge_simulation`

Root cause: `project_state/mainline_merge_intents/active.json` still binds PR121's `pr121_final_owner_authority_v4` intent (`source_pr=121`, decision `decision_20260807_pr121_final_owner_authority_v4`, base `5de53389a3cf0a6557f2a0bb837eee4a5d5687fe`). The current accepted product Decision is `decision_20260807_issue128_provider_free_task_plane_v4`. This is a stale-intent governance mismatch, not a product defect.

This v5 Decision authorizes ONLY governance landing artifacts:
1. New v5 Decision committed first.
2. Gate sequence generated against v5 Decision.
3. Current PR121 v4 active intent archived byte-for-byte.
4. New PR129 v5 active intent bound to the committed v5 Decision and v5 command plan, with `source_pr=129` and `locked_base_sha=9f9b4336c58777b30eb45a85c9c2d4253ba993c1`.

No product code, test, workflow, or documentation changes.

## Acceptance

1. v5 Decision committed before any gate generation or intent modification.
2. v4 Decision commit `bfd8edaa0afddb266b793366a1c5ec93efd82860` remains immutable.
3. Current PR121 v4 active intent archived byte-for-byte to `project_state/mainline_merge_intents/archive/pr121_v4.json` before modification.
4. Gate sequence reports `transition-lint: PASS`, `transition-preflight: PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
5. New active intent binds: `decision_id=decision_20260807_pr129_provider_free_task_plane_landing_v5`, `source_pr=129`, `locked_base_sha=9f9b4336c58777b30eb45a85c9c2d4253ba993c1`, `allowed_merge_method=merge`, `required_workflows=[CI, Decision Preflight, State Gate (pull_request), State Gate (push)]`.
6. `pr_comment_allowed=true`, `mark_ready_allowed=true`, `merge_allowed=true`, `auto_merge_allowed=false`. These authorize Owner-only post-acceptance actions; the local Agent must NOT execute PR comment, mark ready, or merge.
7. `python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q` passes with 0 failures.
8. `python -m pytest tests/platform_v1 -q` passes.
9. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
10. `git diff --check 9f9b4336c58777b30eb45a85c9c2d4253ba993c1..HEAD` passes.
11. `git diff --name-only 80761ed427e142f8cbd94a233c178618960a637c..HEAD` contains only the 8 allowed v5 paths.
12. No product code, runtime code, tests, workflows, docs, or package files modified.
13. No Codex, OpenHands, or model/provider calls during runtime. `Codex runtime calls = 0`, `OpenHands runtime calls = 0`, `model/provider runtime calls = 0`.
14. Branch pushed to origin via normal push only. No force push, rebase, merge, release, or deploy.

```text
PR129_V5_LANDING_GOVERNANCE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- This v5 Decision follows and supersedes the v4 Decision for PR #129 final Owner landing authority only.
- The v4 Decision (`decision_20260807_issue128_provider_free_task_plane_v4`) is immutable and preserved as the historical baseline for the v4 product acceptance window.
- Run the standard Path-B gate sequence: transition-lint, transition-command-plan, transition-preflight (pre), before any intent modification.
- `mainline` must be `engineering_branch` to satisfy the canonical mainline landing contract.
- Owner-only publication authority (`pr_comment_allowed`, `mark_ready_allowed`, `merge_allowed`) is internal to this Decision; the local Agent must NOT execute any Owner publication action.
- Publication is limited to the exact branch and normal push.
- No real provider credentials, live provider probes, or model execution.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260823_issue318_state_gate_reachability_r2_v1",
  "round_id": "round_20260823_issue318_state_gate_reachability_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260822_issue285_home_goal_truth_r2_v2_landing",
  "follows_last_round_id": "round_20260822_issue285_home_goal_truth_r2_v2_landing",
  "previous_audit_outcome": "V2_LANDING_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "workstream_id": "issue318-state-gate-reachability-r2-v1",
  "source_issue": 318,
  "required_branch": "owner/issue318-state-gate-reachability-r2-v1",
  "integration_base_ref": "main",
  "base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "activation_base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_close_allowed": false,
  "pr_close_allowed": false,
  "mark_ready_allowed": false,
  "merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "runner_dispatch_limit": 0,
  "tag_or_release_limit": 0,
  "deployment_limit": 0,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/test_ci_responsibility.py"
  ],
  "bootstrap_exception_commands": [
    "commit this immutable Decision as the unique first new commit after 772de2662949d2a454b611806a36b52f75cace9f on owner/issue318-state-gate-reachability-r2-v1 before any workflow implementation or generated governance artifact publication",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue318.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before workflow implementation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue318.fix_state_gate_paths_filter",
      "command": "remove the pull_request paths: filter from .github/workflows/state-gate.yml so the State Gate runs on all PRs; preserve all pull_request types, push paths, permissions, jobs, and pull_request_target bootstrap boundary",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [".github/workflows/state-gate.yml"]
    },
    {
      "command_id": "issue318.fix_ci_blocking_path_a_regression",
      "command": "add a blocking CI step in .github/workflows/ci.yml that unconditionally runs python -m pytest tests/test_path_a_gate.py -q to prevent state-gate reachability regressions from re-entering",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [".github/workflows/ci.yml"]
    },
    {
      "command_id": "issue318.fix_ci_responsibility_test",
      "command": "update tests/test_ci_responsibility.py to reflect restored pull_request reachability: rename test_state_gate_pull_request_event_has_paths_filter to test_state_gate_pull_request_event_has_no_paths_filter and assert no paths filter; update test_state_gate_governance_paths_do_match to only check push paths",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["tests/test_ci_responsibility.py"]
    },
    {
      "command_id": "issue318.fix_project_gate_test",
      "command": "update tests/test_project_gate.py test_transition_packaging_and_workflow_boundary to include the new Path-A gate reachability blocking step in the expected CI workflow step list",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["tests/test_project_gate.py"]
    },
    {
      "command_id": "issue318.validate_all_tests",
      "command": "run test_path_a_gate.py test_ci_responsibility.py test_control_plane_transition.py test_planning_and_github_adapters.py transition-lint transition-preflight publication-readiness git diff --check; all must pass",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue318.publish_draft_pr",
      "command": "push owner/issue318-state-gate-reachability-r2-v1 once and create exactly one Draft PR against main; stop for Owner audit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_product_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py"
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/**",
    "frontend/**",
    "tests/test_path_a_gate.py",
    "tests/**",
    "requirements*.txt",
    "pyproject.toml",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "product_mutation_outside_allowed_paths",
    "source_edit",
    "test_edit",
    "documentation_edit",
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "dependency_install",
    "live_model_call",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "runner_dispatch",
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "publication_allowed": true
  },
  "path_a_py_modification_forbidden": true,
  "yaml_fence_change_forbidden": true,
  "success_terminal": "ISSUE318_STATE_GATE_REACHABILITY_R2_REPAIR_COMPLETE",
  "blocked_terminal": "ISSUE318_STATE_GATE_REACHABILITY_R2_BLOCKED"
}
```

## Goal

Restore ordinary Path-A State Gate reachability by removing the `pull_request paths:` filter that prevents the State Gate from running on PRs that do not touch governance files, and add a blocking CI step for `test_path_a_gate.py` to prevent recurrence.

## Acceptance

1. The `pull_request` trigger in `.github/workflows/state-gate.yml` contains NO `paths:` key.
2. The `pull_request` trigger retains all current event types: opened, edited, synchronize, reopened, converted_to_draft, ready_for_review, labeled, unlabeled, auto_merge_enabled, auto_merge_disabled.
3. The `push` trigger, `pull_request_target` bootstrap boundary, permissions, and all job logic remain unchanged.
4. `.github/workflows/ci.yml` gains a blocking step that runs `python -m pytest tests/test_path_a_gate.py -q` unconditionally.
5. All 10 cases of `test_state_gate_pull_request_trigger_reaches_every_risk_only_change` pass.
6. `test_ci_responsibility.py`, `test_control_plane_transition.py`, `test_planning_and_github_adapters.py` all pass.
7. `transition-lint` and `transition-preflight` pass with `PRE_EXECUTION_AUTHORIZED`.
8. `worktree-publication-readiness` passes.
9. `git diff --check` passes.
10. `reverse_agent/control_plane/path_a.py` is NOT modified.
11. No dependency, package, frontend, model access, or test file changes are introduced.

## Execution policy

- This is a minimal R2 governance repair. Only `.github/workflows/state-gate.yml` and `.github/workflows/ci.yml` are modified as product files.
- All other changes are Decision-generated governance artifacts under `project_state/`.
- The Decision is committed before any workflow implementation.
- No mark-ready, merge, auto-merge, tag, release, deployment, dependency install, live model call, provider call, credential access, runner dispatch, force push, rebase, or history rewrite is permitted.
- Publication is bounded to one normal push of the exact branch and one Draft PR creation. Stop for Owner audit.

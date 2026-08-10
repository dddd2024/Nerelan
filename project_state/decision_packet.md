# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_issue178_bootstrap_command_id_audit_fix_v2",
  "round_id": "round_20260810_issue178_bootstrap_command_id_audit_fix_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_recovery_carveout": true,
  "recovery_reason": "Issue #178 production fix candidate 2ce7f1d669db2625671763fbe2beeffff8699b4d independently fixes the bootstrap command-ID collision, but Owner audit found one explicit acceptance-coverage gap: the collision Decision is validated only through lower-level build_transition_command_plan/validate_transition_command_plan rather than the public project_gate.transition_command_plan generation entrypoint required by #178. This successor authorizes only that missing regression test and preserves the accepted production candidate unchanged.",
  "workstream_id": "issue178-bootstrap-command-id-audit-fix-v2",
  "source_issue": 178,
  "parent_issue": 156,
  "blocked_product_issue": 176,
  "required_branch": "owner/issue178-bootstrap-command-id-r2-audit-fix-authority-v2",
  "starting_head": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "activation_base_sha": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "integration_target_before_sha": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "sanitized_target_branch": "owner/issue178-bootstrap-command-id-r2-v2",
  "sanitized_target_starting_head": "2ce7f1d669db2625671763fbe2beeffff8699b4d",
  "accepted_predecessor_product_head": "2ce7f1d669db2625671763fbe2beeffff8699b4d",
  "accepted_predecessor_product_message": "fix: make bootstrap command ids collision safe",
  "accepted_predecessor_product_paths": [
    "reverse_agent/control_plane/legacy_adapter.py",
    "tests/test_control_plane_transition.py"
  ],
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "This is a narrow Owner recovery successor for the transition-command-plan infrastructure defect. Do not recursively require the transition lifecycle being repaired; validation may invoke project_gate.transition_command_plan only inside pytest as the behavior under test.",
  "required_product_paths": [
    "tests/test_control_plane_transition.py"
  ],
  "required_product_path_count": 1,
  "project_state_paths_in_sanitized_commit": 0,
  "required_behavior": [
    "Preserve 2ce7f1d669db2625671763fbe2beeffff8699b4d production implementation byte-for-byte",
    "Add an explicit regression test that writes the collision Decision and calls project_gate.transition_command_plan(state_dir=state_dir)",
    "Assert the returned plan_status is PASSED",
    "Assert both distinct colliding bootstrap commands are present after projection with distinct non-empty bootstrap command IDs",
    "Do not weaken duplicate-command-ID validation",
    "Do not alter bootstrap network-policy or execution semantics"
  ],
  "required_tests": [
    "python -m pytest tests/test_control_plane_transition.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
    "python -m pytest -q",
    "git diff --check"
  ],
  "final_remote_cas_required": true,
  "planning_head_must_remain": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "branch_creation_allowed": true,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "normal_push_limit": 1,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "rebase_during_execution_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "destructive_operations_allowed": false,
  "unknown_binary_execution_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
  "allowed_mutated_paths": [
    "tests/test_control_plane_transition.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/**",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/**",
    "tests/platform_v1/**",
    ".github/**",
    "docs/**",
    "frontend/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "package.json",
    "package-lock.json"
  ],
  "forbidden_operations": [
    "transition_gate_regeneration",
    "task3c_execution",
    "planning_push",
    "main_push",
    "pr_create",
    "merge",
    "mark_ready",
    "reset",
    "clean",
    "restore",
    "stash",
    "rebase",
    "force_push",
    "amend",
    "squash",
    "cherry_pick",
    "tag_or_release",
    "deployment",
    "credential_access",
    "model_api_invocation"
  ]
}
```

## Owner audit-fix notes

- Owner accepts the production implementation in `2ce7f1d669db2625671763fbe2beeffff8699b4d` as the candidate fix; this successor exists only to close the explicit #178 end-to-end acceptance-test gap.
- The sanitized v2 branch starts exactly at that predecessor product head. Do not modify `reverse_agent/control_plane/legacy_adapter.py` or reproduce the production fix.
- The only authorized new product mutation is `tests/test_control_plane_transition.py`.
- The required new regression must exercise `project_gate.transition_command_plan(state_dir=state_dir)` on the collision Decision and prove `plan_status == "PASSED"` plus distinct bootstrap IDs.
- Test code may call the transition-command-plan Python entrypoint because it is the behavior under test. Do not run transition startup/lint/preflight against repository `project_state` and do not generate repository gate artifacts.
- Stop after one normal non-force push to `owner/issue178-bootstrap-command-id-r2-v2`. Owner will audit exact head and perform any planning landing separately.

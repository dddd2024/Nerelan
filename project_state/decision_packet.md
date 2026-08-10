# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_state_gate_pr_head_checkout_owner_exact_head_landing_v1",
  "round_id": "round_20260810_state_gate_pr_head_checkout_owner_exact_head_landing_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_exact_head_landing_carveout": true,
  "follows_last_decision_id": "decision_20260810_state_gate_pr_head_checkout_owner_recovery_v1",
  "follows_last_round_id": "round_20260810_state_gate_pr_head_checkout_owner_recovery_v1",
  "previous_audit_outcome": "OWNER_REMOTE_VALIDATION_CONFIRMED_STATE_GATE_CHECKOUTS_REAL_PR_HEAD",
  "workstream_id": "state-gate-pr-head-checkout-owner-exact-head-landing-v1",
  "source_issue": 161,
  "parent_issue": 156,
  "blocked_recovery_issue": 159,
  "blocked_product_issue": 151,
  "validation_pr": 162,
  "validation_state_gate_run": 31347543645,
  "validation_state_gate_job": 93332167954,
  "required_branch": "owner/state-gate-pr-head-checkout-fix-landing-authority-v1",
  "starting_head": "fcc34e4258c11eed1b93a4591f0cba1dc9244a8d",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "target_before_sha": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "target_after_sha": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
  "sanitized_branch": "owner/state-gate-pr-head-checkout-fix-v1",
  "sanitized_head": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
  "recovery_authority_branch": "owner/state-gate-pr-head-checkout-fix-authority-v1",
  "recovery_authority_head": "fcc34e4258c11eed1b93a4591f0cba1dc9244a8d",
  "risk_tier": "R2",
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "This successor authorizes only one exact non-force planning fast-forward after independent remote object/path/runtime validation; it must not recursively invoke the still-unfinished general Path-B lifecycle tracked by #156.",
  "required_product_paths": [
    ".github/workflows/state-gate.yml",
    "tests/test_state_gate_exact_head_checkout.py"
  ],
  "required_product_path_count": 2,
  "sanitized_project_state_path_count": 0,
  "sanitized_commit_parent": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "sanitized_commit_message": "governance: bind State Gate checkout to PR head",
  "remote_runtime_validation": {
    "checkout_ref_observed": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
    "checkout_head_observed": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
    "previous_error_absent": "workflow_exact_head_mismatch",
    "expected_later_blocker": "snapshot_missing"
  },
  "reported_local_validation": {
    "exact_head_checkout_test": "PASS",
    "path_a_control_plane": "259 passed",
    "project_gate": "1216 passed, 1 skipped",
    "diff_check": "PASS"
  },
  "final_remote_cas_required": true,
  "planning_head_must_equal_before": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "sanitized_head_must_equal": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
  "recovery_authority_head_must_equal": "fcc34e4258c11eed1b93a4591f0cba1dc9244a8d",
  "issue159_head_must_remain": "de7cdf822bc7ee8c531ed68cfdfe97de5c499bef",
  "planning_fast_forward_allowed": true,
  "planning_fast_forward_limit": 1,
  "planning_fast_forward_exact_from": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "planning_fast_forward_exact_to": "0a41df542fc90e8de4de7112c08d7f227e31c4a7",
  "validation_pr_merge_allowed": false,
  "validation_pr_mark_ready_allowed": false,
  "validation_pr_auto_merge_allowed": false,
  "branch_creation_allowed": true,
  "worktree_creation_allowed": false,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
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
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "allowed_mutated_paths": ["project_state/decision_packet.md"],
  "forbidden_operations": [
    "source_repair",
    "test_repair",
    "main_push",
    "pr_merge",
    "mark_ready",
    "auto_merge",
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
    "model_api_invocation",
    "issue159_product_recovery_before_rebinding"
  ]
}
```

## Owner landing notes

- Independent remote audit proved the sanitized product branch is exactly one commit ahead of planning and changes only the two #161 product paths.
- Validation PR #162 is evidence only and must never be merged. Its State Gate checkout explicitly used the real PR head `0a41df...`; Path-A then failed later with `snapshot_missing`, proving the former merge-ref exact-head contradiction is removed without weakening authority semantics.
- Before the planning ref update, re-observe planning, sanitized product, recovery authority, landing authority, and #159 target refs. Any drift blocks execution.
- The only authorized product-side mutation is one non-force fast-forward of `owner/repository-modernization-v2-planning` from exact `5a109df...` to exact `0a41df...`.
- After landing, #159/#160 must be re-audited because their approved base SHA is `5a109df...`; do not rebase, merge, or mutate that stale R1 history to absorb this governance commit.

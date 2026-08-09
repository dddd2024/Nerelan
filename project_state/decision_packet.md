# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_r1_unblocker_owner_exact_head_landing_v1",
  "round_id": "round_20260809_governance_v2_r1_unblocker_owner_exact_head_landing_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_exact_head_landing_carveout": true,
  "landing_reason": "Owner independently re-observed the sanitized remote exact head after the one-time recovery push and proved exact parent/path/blob/CAS identity. The predecessor recovery Decision explicitly forbids planning mutation and requires a new landing decision after this audit.",
  "follows_last_decision_id": "decision_20260809_governance_v2_r1_unblocker_owner_recovery_landing_v1",
  "follows_last_round_id": "round_20260809_governance_v2_r1_unblocker_owner_recovery_landing_v1",
  "previous_audit_outcome": "OWNER_EXACT_HEAD_AUDIT_PASSED_NO_BLOCKING_PRODUCT_IDENTITY_DEFECT",
  "workstream_id": "governance-v2-r1-unblocker-owner-exact-head-landing-v1",
  "source_issue": 158,
  "parent_issue": 148,
  "product_issue": 157,
  "related_issue": 156,
  "blocked_issue": 151,
  "required_branch": "owner/governance-v2-r1-unblocker-landing-authority-v1",
  "starting_head": "fc49d2ae02d0023e9fe2b647457c926b633e1215",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "target_before_sha": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "target_after_sha": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "sanitized_branch": "owner/governance-v2-r1-unblocker-sanitized-v1",
  "sanitized_head": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "accepted_source_branch": "owner/governance-v2-r1-unblocker-v1",
  "accepted_source_head": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "recovery_authority_branch": "owner/governance-v2-r1-unblocker-integration-authority-v1",
  "recovery_authority_head": "fc49d2ae02d0023e9fe2b647457c926b633e1215",
  "risk_tier": "R2",
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "This successor is an exact remote-object Owner landing decision after the predecessor recovery path. The unresolved first-class Path-B lifecycle defect remains tracked by Issue 156; do not recursively invoke the previously failing transition lifecycle for this one exact landing.",
  "required_product_paths": [
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/workflows/decision-preflight.yml",
    "AGENTS.md",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/project_gate.py",
    "tests/test_decision_preflight.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py"
  ],
  "required_product_path_count": 9,
  "sanitized_project_state_path_count": 0,
  "sanitized_commit_parent": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "sanitized_commit_message": "governance: integrate R1 execution unblocker",
  "source_product_identity_ref": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "owner_remote_blob_identity_verified": true,
  "owner_remote_blob_identity_count": 9,
  "remote_ci_replayed": false,
  "remote_ci_boundary": "No GitHub commit status or PR-triggered workflow run exists for sanitized exact head 5a109df; absence is not treated as success. Landing relies on independently re-observed remote Git object/path/blob/CAS identity plus previously reported local deterministic tests.",
  "final_remote_cas_required": true,
  "planning_head_must_equal_before": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "sanitized_head_must_equal": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "accepted_source_head_must_equal": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "recovery_authority_head_must_equal": "fc49d2ae02d0023e9fe2b647457c926b633e1215",
  "planning_fast_forward_allowed": true,
  "planning_fast_forward_limit": 1,
  "planning_fast_forward_exact_from": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "planning_fast_forward_exact_to": "5a109df046cf3d8fe74b88fbc049c454ef4d2a53",
  "branch_creation_allowed": true,
  "worktree_creation_allowed": false,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
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
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "allowed_mutated_paths": [
    "project_state/decision_packet.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "AGENTS.md",
    "reverse_agent/**",
    "tests/**",
    "docs/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock"
  ],
  "forbidden_operations": [
    "transition_gate_regeneration",
    "source_repair",
    "test_repair",
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

## Owner landing notes

- This is a successor to the completed recovery Decision, not a mutation or reuse of that immutable authority.
- The only product-side operation authorized is one non-force fast-forward of `owner/repository-modernization-v2-planning` from exact `f8010e1...` to exact `5a109df...`.
- Re-observe all four remote refs immediately before the update. Any drift blocks execution.
- No PR, merge commit, cherry-pick, rebase, force update, source edit, project-state transplant, main mutation, model/provider call, release or deployment is authorized.
- After the update, re-observe the four refs. Success requires planning to equal `5a109df...` and the sanitized, accepted-source and recovery-authority refs to remain unchanged.
- The absence of remote CI for `5a109df...` is explicitly recorded and is not represented as a passing workflow.
- After successful landing, create a fresh ordinary-R1 Work Item for Issue #151 recovery bound to the new planning base; do not mutate the frozen historical #151 workspace under an old authority.

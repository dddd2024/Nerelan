# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_issue178_bootstrap_command_id_owner_recovery_v1",
  "round_id": "round_20260810_issue178_bootstrap_command_id_owner_recovery_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_recovery_carveout": true,
  "recovery_reason": "Issue #176 Task 3C R2 v2 proved that transition-command-plan can fail before preflight because bootstrap command IDs are derived from command[:64]. Two distinct authorized fetch commands share that prefix and validate_command_plan correctly rejects the collision. This narrow recovery repairs only deterministic bootstrap command identity so governance does not recursively depend on the broken command-plan projection it is repairing.",
  "workstream_id": "issue178-bootstrap-command-id-owner-recovery-v1",
  "source_issue": 178,
  "parent_issue": 156,
  "blocked_product_issue": 176,
  "blocked_product_decision": "decision_20260810_issue176_task3c_narrow_relay_r2_v2",
  "observed_blocked_head": "ca14d36fc06fc519db5362202bd40a2c99b7721c",
  "observed_error_code": "duplicate_command_id",
  "required_branch": "owner/issue178-bootstrap-command-id-r2-authority-v1",
  "starting_head": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "activation_base_sha": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "sanitized_target_branch": "owner/issue178-bootstrap-command-id-r2-v1",
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "The defect being repaired is inside transition command-plan bootstrap identity generation. This one exact Owner recovery must not recursively require the broken transition-command-plan path before the repair exists.",
  "required_product_paths": [
    "reverse_agent/control_plane/legacy_adapter.py",
    "tests/test_control_plane_transition.py"
  ],
  "required_product_path_count": 2,
  "project_state_paths_in_sanitized_commit": 0,
  "required_behavior": [
    "bootstrap command IDs are deterministic and derived from the full canonical command rather than a truncated raw prefix",
    "two distinct bootstrap commands sharing the first 64 characters receive distinct command IDs",
    "exact duplicate canonical bootstrap commands remain de-duplicated",
    "structured allowed_commands command IDs remain unchanged",
    "validate_command_plan duplicate-ID enforcement is not weakened",
    "bootstrap execution and network-policy semantics are unchanged in this narrow recovery"
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
    "reverse_agent/control_plane/legacy_adapter.py",
    "tests/test_control_plane_transition.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/**",
    ".github/**",
    "AGENTS.md",
    "README.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/**",
    "tests/platform_v1/**",
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
    "task3c_product_recovery",
    "planning_push",
    "main_push",
    "pr_create",
    "merge",
    "mark_ready",
    "reset",
    "clean",
    "restore",
    "checkout_overwrite",
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

## Owner recovery notes

- This Decision authorizes only the two-path #178 bootstrap command-ID collision repair. It does not authorize the broader #156 redesign or any #176 Task 3C product implementation.
- The authority branch may contain this `project_state/decision_packet.md` commit; the sanitized product branch must start independently from exact planning `a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2` and must contain no `project_state/**` delta.
- Do not weaken `validate_command_plan()`. The fix belongs in bootstrap ID derivation and its regression tests.
- Use a bounded deterministic identifier derived from the full canonical command, preferably a SHA-256 digest; do not substitute the entire raw command as an unbounded ID.
- Do not change bootstrap network-policy semantics in this unblocker. The separate observation that bootstrap exceptions are network-policy-exempt remains residual #156 debt.
- Local implementation must run the required tests, create one bounded product commit on `owner/issue178-bootstrap-command-id-r2-v1`, perform at most one normal non-force push, and stop at `GOVERNANCE_BOOTSTRAP_COMMAND_ID_COLLISION_FIX_READY_FOR_OWNER_AUDIT`.
- Owner will independently audit the exact remote product head and issue any separate landing authority. The blocked #176 v2 branch/worktree remains immutable evidence and must not be reused or cleaned.

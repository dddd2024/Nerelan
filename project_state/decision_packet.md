# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_r1_unblocker_owner_recovery_landing_v1",
  "round_id": "round_20260809_governance_v2_r1_unblocker_owner_recovery_landing_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": false,
  "owner_recovery_carveout": true,
  "recovery_reason": "forensic_v4_proved_integration_v3_transition_preflight_failed_before_authority_binding because rebase_during_execution_allowed was missing_or_invalid; do not recursively require the failing transition lifecycle to land the already accepted governance product tree",
  "forensic_evidence": {
    "failed_preflight_sha256": "463F99E645197E9EEF83EDAB8DA3810942271FEF1A6694F96909CE7B6555107B",
    "blocking_reason": "invalid_transition_authority:missing_or_invalid_contract_field:rebase_during_execution_allowed",
    "forensic_authority_head": "4dca5ea7f8822db61f8b2149f4ff4be29bc790f2",
    "forensic_decision_blob": "7286f70809ecf105123cdf699115ac141be9b1b0"
  },
  "follows_last_decision_id": "decision_20260809_governance_v2_r1_unblocker_sanitized_integration_forensics_v4",
  "follows_last_round_id": "round_20260809_governance_v2_r1_unblocker_sanitized_integration_forensics_v4",
  "previous_audit_outcome": "PREFLIGHT_FORENSICS_V4_CAPTURED_ROOT_CAUSE_CONFIRMED",
  "workstream_id": "governance-v2-r1-unblocker-owner-recovery-landing-v1",
  "source_issue": 157,
  "parent_issue": 148,
  "related_issue": 156,
  "blocked_issue": 151,
  "required_branch": "owner/governance-v2-r1-unblocker-integration-authority-v1",
  "starting_head": "4dca5ea7f8822db61f8b2149f4ff4be29bc790f2",
  "activation_base_sha": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "accepted_product_head": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "sanitized_target_branch": "owner/governance-v2-r1-unblocker-sanitized-v1",
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "transition_commands_forbidden": true,
  "transition_commands_forbidden_reason": "this recovery authority exists specifically because the previous transition authority lifecycle failed before identity binding; recovery evidence is exact-head/object/test based instead",
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
  "project_state_paths_in_sanitized_commit": 0,
  "sanitized_commit_parent": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "sanitized_commit_message": "governance: integrate R1 execution unblocker",
  "source_product_identity_must_match": true,
  "source_product_identity_ref": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "canonical_lf_validation_required": true,
  "required_tests": [
    "python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_minimal_integration_baseline_docs.py tests/test_decision_preflight.py -q",
    "python -m pytest tests/platform_v1 -q",
    "git diff --check"
  ],
  "final_remote_cas_required": true,
  "planning_head_must_remain": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "accepted_source_head_must_remain": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "sanitized_remote_must_be_absent_before_push": true,
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
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 1,
  "allowed_mutated_paths": [
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
  "forbidden_mutated_paths": [
    "project_state/**",
    ".github/workflows/state-gate.yml",
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/**",
    "reverse_agent/architecture/contracts.py",
    "tests/platform_v1/**",
    "tests/test_team_graph.py",
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

## Owner recovery notes

- This is an explicit one-time Owner recovery landing authority, not another transition-kernel successor round.
- Forensic v4 established that integration v3 was blocked before Decision/Round binding because `rebase_during_execution_allowed` was missing or invalid. The accepted #157 product tree itself was not implicated.
- Do **not** run `startup-snapshot`, `transition-command-plan`, `transition-lint`, or `transition-preflight` under this authority. Those gates are deliberately outside this recovery path.
- Recovery acceptance is instead bound to exact remote refs, exactly nine product paths, raw/full-index Git object identity against accepted source `f369051...`, canonical-LF deterministic tests, one clean commit parented directly to planning `f8010e1...`, final CAS, and exactly one normal push of the sanitized branch.
- This authority does not permit a PR, merge, planning/main push, #151 mutation, #146 mutation, source repair, or any destructive Git operation.
- After the sanitized branch is pushed, Owner must independently audit its exact remote head before any landing decision.
- The missing/invalid transition contract field and the absence of a first-class audited recovery lifecycle remain tracked under #156; this recovery is not the permanent solution.

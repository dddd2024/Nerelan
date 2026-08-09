# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_foundation_planning_landing_v2",
  "round_id": "round_20260809_governance_v2_foundation_planning_landing_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_governance_v2_foundation_planning_landing_v1",
  "follows_last_round_id": "round_20260809_governance_v2_foundation_planning_landing_v1",
  "previous_audit_outcome": "LANDING_V1_LINT_BLOCKED_STALE_COMMAND_PLAN_BOOTSTRAP_ARTIFACT",
  "workstream_id": "governance-v2-foundation-planning-landing-v2",
  "source_issue": 153,
  "parent_issue": 148,
  "active_pr": 154,
  "authority_validation_pr": 155,
  "required_branch": "owner/governance-v2-foundation-landing-authority-v1",
  "starting_head": "296f34ba2faaa8ba9c3ebcc69de8b5d3d9018a54",
  "activation_base_sha": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "expected_planning_head_before": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "accepted_product_branch": "owner/governance-v2-foundation-sanitized-v1",
  "accepted_product_head": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "accepted_product_parent": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "accepted_product_ci_run_id": 31309425882,
  "accepted_product_ci_conclusion": "success",
  "accepted_product_changed_files": 11,
  "landing_mode": "OWNER_EXACT_HEAD_FAST_FORWARD",
  "planning_fast_forward_allowed": true,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "draft_pr_creation_allowed": true,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": false,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-foundation-sanitized-v1",
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
      "command_id": "observation.planning_head",
      "command": "git rev-parse origin/owner/repository-modernization-v2-planning",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.accepted_product_head",
      "command": "git rev-parse origin/owner/governance-v2-foundation-sanitized-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "validation.accepted_product_parent",
      "command": "git rev-parse f8010e1c05d64f556d64f81c35e6916bf825409e^",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.create_authority_pr",
      "command": "gh pr create --draft --base owner/repository-modernization-v2-planning --head owner/governance-v2-foundation-landing-authority-v1",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_creation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": false
    },
    {
      "command_id": "publication.fast_forward_planning",
      "command": "git push origin f8010e1c05d64f556d64f81c35e6916bf825409e:refs/heads/owner/repository-modernization-v2-planning",
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
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".gitignore",
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".gitignore",
    "AGENTS.md",
    "frontend/**",
    "docs/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "reverse_agent/**",
    "tests/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "source_edit",
    "test_edit",
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "cherry_pick",
    "reset_hard",
    "git_clean",
    "stash",
    "restore",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "dependency_change",
    "provider_configuration_mutation",
    "issue151_product_mutation",
    "pr146_mutation"
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
    "local_network_exceptions": [
      "gh pr create --draft --base owner/repository-modernization-v2-planning --head owner/governance-v2-foundation-landing-authority-v1",
      "git push origin f8010e1c05d64f556d64f81c35e6916bf825409e:refs/heads/owner/repository-modernization-v2-planning"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

v2 supersedes landing v1 after the validation-only PR exposed a historical bootstrap coupling: `transition-lint` runs before `transition-command-plan` and therefore requires a command plan already matching the active Decision. The authority-only branch now carries the deterministic v2 `project_state/gates/command_plan.json` projection before this Decision commit.

The accepted product remains immutable at `f8010e1c05d64f556d64f81c35e6916bf825409e`, whose only parent is planning `7e068aac0a4142e611a5d5b825353db31efd2cb7`. Product PR #154 has independently audited remote object identity and exact-head CI run `31309425882` completed successfully.

This one-time external R2 landing authority permits only validation on PR #155 and, after successful authority checks and final exact-head re-observation, Owner fast-forward of `owner/repository-modernization-v2-planning` from exact `7e068aac0a4142e611a5d5b825353db31efd2cb7` to exact `f8010e1c05d64f556d64f81c35e6916bf825409e`. It does not authorize product mutation, merging PR #155, PR #154 Ready/merge, main mutation, force/rebase, or any authority commit entering planning.

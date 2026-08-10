# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_issue165_product_setup_3a_planning_landing_v1",
  "round_id": "round_20260810_issue165_product_setup_3a_planning_landing_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260810_issue165_product_setup_3a_r2_v3",
  "follows_last_round_id": "round_20260810_issue165_product_setup_3a_r2_v3",
  "previous_audit_outcome": "PRODUCT_SETUP_3A_SANITIZED_PRODUCT_EXACT_HEAD_AUDITED_CI_ACCEPTED",
  "workstream_id": "issue165-product-setup-3a-planning-landing-v1",
  "source_issue": 165,
  "parent_issue": 148,
  "active_pr": 168,
  "required_branch": "owner/issue165-product-setup-3a-landing-authority-v1",
  "starting_head": "61af5932d35959567d541077cda67cdb5d7b5100",
  "activation_base_sha": "61af5932d35959567d541077cda67cdb5d7b5100",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "expected_planning_head_before": "61af5932d35959567d541077cda67cdb5d7b5100",
  "accepted_product_branch": "owner/issue165-product-setup-3a-sanitized-v1",
  "accepted_product_head": "d2b3d513a19c12304977e72b4e416a9b606aa9a0",
  "accepted_product_parent": "61af5932d35959567d541077cda67cdb5d7b5100",
  "accepted_product_ci_run_id": 31355673846,
  "accepted_product_ci_conclusion": "success",
  "accepted_model_access_run_id": 31355673845,
  "accepted_model_access_conclusion": "success",
  "accepted_product_changed_files": 8,
  "product_pr_state_gate_run_id": 31355673877,
  "product_pr_state_gate_expected_limitation": "snapshot_missing_on_sanitized_r2_product_pr",
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
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "rebase_during_execution_allowed": false,
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
    "git rev-parse origin/owner/issue165-product-setup-3a-sanitized-v1",
    "git rev-parse d2b3d513a19c12304977e72b4e416a9b606aa9a0^",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "git add project_state/gates/command_plan.json",
    "git commit -m \"chore: compile issue165 landing authority command plan\"",
    "git push origin owner/issue165-product-setup-3a-landing-authority-v1"
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
      "command": "git rev-parse origin/owner/issue165-product-setup-3a-sanitized-v1",
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
      "command": "git rev-parse d2b3d513a19c12304977e72b4e416a9b606aa9a0^",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "bootstrap.stage_compiled_command_plan",
      "command": "git add project_state/gates/command_plan.json",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation", "repository_staging"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/command_plan.json"]
    },
    {
      "command_id": "bootstrap.commit_compiled_command_plan",
      "command": "git commit -m \"chore: compile issue165 landing authority command plan\"",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation", "local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/command_plan.json"]
    },
    {
      "command_id": "bootstrap.push_compiled_command_plan",
      "command": "git push origin owner/issue165-product-setup-3a-landing-authority-v1",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.fast_forward_planning",
      "command": "git push origin d2b3d513a19c12304977e72b4e416a9b606aa9a0:refs/heads/owner/repository-modernization-v2-planning",
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
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_path_a_gate.py",
    "reverse_agent/model_access/**",
    "tests/test_connection_binding.py",
    "docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md",
    "docs/roadmap/PRODUCT_SETUP_CONNECTIONS_PLAN.md",
    "docs/roadmap/REPOSITORY_MODERNIZATION_V2_PLAN.md"
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
    "provider_configuration_mutation"
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
      "git push origin owner/issue165-product-setup-3a-landing-authority-v1",
      "git push origin d2b3d513a19c12304977e72b4e416a9b606aa9a0:refs/heads/owner/repository-modernization-v2-planning"
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

This external R2 landing authority binds Product Setup 3A to exact sanitized product head `d2b3d513a19c12304977e72b4e416a9b606aa9a0`, whose only parent is exact planning head `61af5932d35959567d541077cda67cdb5d7b5100` and whose cumulative product delta is exactly eight paths.

Owner remote audit accepted the product implementation, canonical-LF local evidence (`35` focused tests, `632` Platform V1 tests, diff checks PASS), GitHub CI run `31355673846` SUCCESS, and Model Access run `31355673845` SUCCESS. Product PR #168 is a sanitized product carrier; its State Gate run `31355673877` failed at ordinary-R1 `snapshot_missing` because the product PR is not the R2 authority carrier. Do not repair Path-A or add an R1 snapshot for this product PR.

Before the authority PR is opened, the repository-owned transition compiler must produce and commit a `project_state/gates/command_plan.json` matching this exact Decision. That bootstrap commit is the only local mutation/push permitted before sidecar workflow validation.

After sidecar State Gate / Decision Preflight validate this exact authority and Owner re-observes both refs, Owner may perform only the exact non-force fast-forward of `owner/repository-modernization-v2-planning` from `61af5932d35959567d541077cda67cdb5d7b5100` to `d2b3d513a19c12304977e72b4e416a9b606aa9a0`. The sidecar authority branch/PR must never be merged into planning. No product mutation, main mutation, force, rebase, squash, model/provider invocation, credential access, or release is authorized.

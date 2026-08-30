# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260830_issue423_windows_platform_ci_r2_v1",
  "round_id": "round_20260830_issue423_windows_platform_ci_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260829_issue367_landing_stage_check_identity_r2_v11",
  "follows_last_round_id": "round_20260829_issue367_landing_stage_check_identity_r2_v11",
  "previous_audit_outcome": "PR424_R1_REJECTED_WORKFLOW_PATH_REQUIRES_R2",
  "workstream_id": "issue423-windows-platform-ci-r2-v1",
  "source_issue": 423,
  "integration_base_ref": "main",
  "base_sha": "24fb827ab6c161267b7f4041f4b2b3f424c1ddfa",
  "activation_base_sha": "24fb827ab6c161267b7f4041f4b2b3f424c1ddfa",
  "starting_head": "24fb827ab6c161267b7f4041f4b2b3f424c1ddfa",
  "required_branch": "owner/issue423-windows-platform-ci-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/windows-platform-v1.yml"
  ],
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "test_semantics_changes_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 24fb827ab6c161267b7f4041f4b2b3f424c1ddfa and fresh branch merge-base",
    "verify PR #424 remains closed unmerged negative evidence",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue423_r2v1.materialize_activation_packet",
      "command": "run the repository-owned startup snapshot command-plan compiler transition lint and preflight; materialize the exact activation packet and commit only the five declared generated gate artifacts",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_provenance",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue423_r2v1.implement_windows_ci",
      "command": "add the single specialized .github/workflows/windows-platform-v1.yml workflow using windows-latest and run python -m pytest tests/platform_v1/test_dev_up_contract.py -q without false-green controls",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_provenance",
      "allowed_mutated_paths": [".github/workflows/windows-platform-v1.yml"]
    },
    {
      "command_id": "issue423_r2v1.validate_publish",
      "command": "validate workflow syntax and repository governance then push the exact branch create one Draft PR against locked main and require fresh CI State Gate Decision Preflight plus the Windows hosted job",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_truth",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue423_r2v1.final_exact_head_acceptance",
      "command": "require exact-head CI State Gate Decision Preflight and Windows hosted launcher lifecycle test success with zero unauthorized paths before independent Owner audit",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read"],
      "network_access": false,
      "required_evidence_source": "repository_truth"
    }
  ],
  "allowed_source_paths": [
    ".github/workflows/windows-platform-v1.yml"
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/windows-platform-v1.yml"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_dev_up_contract.py",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1"
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
    "docs/**",
    ".github/actions/**",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    ".github/workflows/freshness.yml",
    ".codex-skills/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/mainline_merge_intents/**"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "validate workflow syntax and repository governance then push the exact branch create one Draft PR against locked main and require fresh CI State Gate Decision Preflight plus the Windows hosted job"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ]
}
```

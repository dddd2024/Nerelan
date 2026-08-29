# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260829_issue367_ruleset_landing_context_r2_v1",
  "round_id": "round_20260829_issue367_ruleset_landing_context_r2_v1",
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
  "previous_audit_outcome": "PR416_FINAL_DRAFT_HEAD_6F5012DC_ACCEPTED_RULESET_PUBLICATION_PENDING",
  "workstream_id": "issue367-ruleset-landing-context-r2-v1",
  "source_issue": 367,
  "source_pr": 416,
  "integration_base_ref": "main",
  "base_sha": "fa2265478b7e1da61e121a3c7193a3cb8c797802",
  "activation_base_sha": "fa2265478b7e1da61e121a3c7193a3cb8c797802",
  "starting_head": "fa2265478b7e1da61e121a3c7193a3cb8c797802",
  "required_branch": "owner/issue367-ruleset-landing-context-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "workflow_profile": "baseline",
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "ruleset_update_attempt_limit": 1,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": false,
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
  "ruleset_mutation_allowed": true,
  "ruleset_id": 21023698,
  "ruleset_required_context_before": ["baseline", "state-gate"],
  "ruleset_required_context_after": ["baseline", "state-gate", "landing-state-gate"],
  "ruleset_preserve_enforcement": "active",
  "ruleset_preserve_strict_required_status_checks_policy": true,
  "ruleset_preserve_required_review_thread_resolution": true,
  "ruleset_preserve_allowed_merge_methods": ["merge"],
  "ruleset_preserve_bypass_mode": "pull_request",
  "ruleset_preserve_deletion_protection": true,
  "ruleset_preserve_non_fast_forward_protection": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base fa2265478b7e1da61e121a3c7193a3cb8c797802 exact PR416 head 6f5012dc664543fbd0c7bc9486c3c9bf9f4672a6 and Ruleset 21023698 before-state",
    "commit this immutable R2 Ruleset Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue367_ruleset_r2v1.materialize_authority",
      "command": "run the repository-owned startup snapshot command-plan compiler transition lint and preflight locally then commit only the five declared generated gate artifacts",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue367_ruleset_r2v1.publish_and_update",
      "command": "push the exact authority branch once then update repository Ruleset 21023698 required status checks from baseline and state-gate to baseline state-gate and landing-state-gate while preserving every other observed protection and verify exact readback",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access", "ruleset_update"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_ruleset_r2v1.final_observation",
      "command": "observe Ruleset 21023698 exact readback and PR416 unchanged Draft head base and mergeability before Owner attestation and Ready lifecycle",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_source_paths": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "tests/test_control_plane_transition.py"
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
    ".github/**",
    ".codex-skills/**",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
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
      "push the exact authority branch once then update repository Ruleset 21023698 required status checks from baseline and state-gate to baseline state-gate and landing-state-gate while preserving every other observed protection and verify exact readback"
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
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ]
}
```

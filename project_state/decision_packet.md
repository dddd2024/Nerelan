# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260909_issue678_pr675_ready_sidecar_r2_v1",
  "round_id": "round_20260909_issue678_pr675_ready_sidecar_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "EXACT_PR675_AGENT_MARK_READY_ONLY_R2_SIDECAR",
  "source_issue": 678,
  "parent_issue": 677,
  "governance_owner_issue": 156,
  "integration_base_ref": "main",
  "base_sha": "1dd4204f6a5fb4248a3c82258c2ea788a85e3e09",
  "activation_base_sha": "1dd4204f6a5fb4248a3c82258c2ea788a85e3e09",
  "starting_head": "1dd4204f6a5fb4248a3c82258c2ea788a85e3e09",
  "required_branch": "owner/issue677-pr675-ready-sidecar-r2-v1",
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
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "target_repository": "dddd2024/Nerelan",
  "target_pr": 675,
  "accepted_exact_head_sha": "6f8e7ebb7bbba822fe2de77823c405e087f54cbc",
  "target_base_ref": "main",
  "target_base_sha": "1dd4204f6a5fb4248a3c82258c2ea788a85e3e09",
  "target_operation": "mark_ready",
  "expected_head_protection_required": true,
  "mark_ready_allowed": true,
  "mark_ready_attempt_limit": 1,
  "merge_allowed": false,
  "merge_attempt_limit": 0,
  "auto_merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "issue678.observe_pr675_before_ready",
      "command": "observe exact PR 675 head 6f8e7ebb7bbba822fe2de77823c405e087f54cbc and base 1dd4204f6a5fb4248a3c82258c2ea788a85e3e09 immediately before Ready",
      "phase": "validation",
      "required": true,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": [
        "repository_observation",
        "read_only_audit"
      ],
      "network_access": false
    },
    {
      "command_id": "issue678.mark_ready_pr675",
      "command": "mark Ready on dddd2024/Nerelan PR 675 only at head 6f8e7ebb7bbba822fe2de77823c405e087f54cbc and base 1dd4204f6a5fb4248a3c82258c2ea788a85e3e09",
      "phase": "publication",
      "required": true,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready",
        "network_access"
      ],
      "network_access": true,
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue678.observe_pr675_after_ready",
      "command": "observe PR 675 after Ready and require same exact head and natural landing-state-gate without merge",
      "phase": "final_evidence",
      "required": true,
      "required_evidence_source": "repository_state_attestation",
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": [
        "repository_observation",
        "read_only_audit"
      ],
      "network_access": false
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "docs/**",
    "scripts/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/mainline_merge_intents/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "merge",
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "tag_or_release",
    "runner_dispatch",
    "workflow_rerun",
    "source_edit",
    "commit",
    "destructive",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "dependency_install",
    "package_install",
    "active_json_rewrite"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "mark Ready on dddd2024/Nerelan PR 675 only at head 6f8e7ebb7bbba822fe2de77823c405e087f54cbc and base 1dd4204f6a5fb4248a3c82258c2ea788a85e3e09"
    ],
    "user_local_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "AGENTS.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/control_plane/**",
      "minimum_risk": "R2"
    }
  ]
}
```

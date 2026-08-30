# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260830_issue367_pr430_owner_landing_r2_v1",
  "round_id": "round_20260830_issue367_pr430_owner_landing_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260830_issue367_landing_mode_fail_closed_r2_v12",
  "follows_last_round_id": "round_20260830_issue367_landing_mode_fail_closed_r2_v12",
  "previous_audit_outcome": "PR430_FINAL_DRAFT_HEAD_ACCEPTED_ATTESTED_AND_FORMAL_LANDING_REVALIDATION_REQUIRED",
  "workstream_id": "issue367-pr430-owner-landing-r2-v1",
  "source_issue": 367,
  "source_pr": 430,
  "integration_base_ref": "main",
  "base_sha": "1dcb985dddf61204aecd57ca1260ec14f79a4f75",
  "activation_base_sha": "1dcb985dddf61204aecd57ca1260ec14f79a4f75",
  "starting_head": "1dcb985dddf61204aecd57ca1260ec14f79a4f75",
  "accepted_exact_head_sha": "d5be835c0a849341428a4ed4fb0836ce6b791f95",
  "required_branch": "owner/issue367-pr430-owner-landing-r2-v1",
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
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": false,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
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
  "expected_head_protection_required": true,
  "independent_audit_comment_id": 5468233871,
  "owner_attestation_comment_id": 5468237294,
  "owner_attestation_expires_at": "2026-08-30T18:51:55Z",
  "ruleset_id": 21023698,
  "required_status_contexts": ["baseline", "state-gate", "landing-state-gate"],
  "required_draft_workflow_runs": {
    "CI": 33306787406,
    "Decision Preflight": 33306787380,
    "State Gate (pull_request)": 33306787387
  },
  "landing_revalidation_required_for_actions": ["ready_for_review"],
  "formal_landing_context_must_be_success_before_merge": true,
  "natural_new_main_ci_required": true,
  "natural_new_main_state_gate_required": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base PR430 head audit attestation Ruleset required contexts and zero unresolved review threads",
    "commit this immutable R2 Owner landing Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue367_pr430_owner_landing_r2v1.materialize_authority",
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
      "command_id": "issue367_pr430_owner_landing_r2v1.publish_authority",
      "command": "push the exact Owner landing authority branch once and verify remote commit identity",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr430_owner_landing_r2v1.mark_ready",
      "command": "after exact readback of unchanged PR430 head base active schema-v3 attestation Ruleset landing context and zero unresolved threads mark PR430 Ready exactly once",
      "phase": "landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "mark_ready"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr430_owner_landing_r2v1.verify_ready",
      "command": "observe the newly triggered formal landing-state-gate and Ready State Gate reach terminal success on unchanged PR430 head with all required contexts successful",
      "phase": "landing_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue367_pr430_owner_landing_r2v1.merge",
      "command": "after immediate reobservation merge PR430 exactly once with merge method merge and expected head d5be835c0a849341428a4ed4fb0836ce6b791f95",
      "phase": "landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "merge"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr430_owner_landing_r2v1.postmerge_verify",
      "command": "observe PR430 merged exact merge commit parent topology and natural exact-new-main CI push plus State Gate push terminal success before closure",
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
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "project_state/mainline_merge_intents/active.json"
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
      "push the exact Owner landing authority branch once and verify remote commit identity",
      "after exact readback of unchanged PR430 head base active schema-v3 attestation Ruleset landing context and zero unresolved threads mark PR430 Ready exactly once",
      "after immediate reobservation merge PR430 exactly once with merge method merge and expected head d5be835c0a849341428a4ed4fb0836ce6b791f95"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
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

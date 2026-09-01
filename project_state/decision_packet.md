# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260901_issue487_nerelan_runtime_brand_r2_v1",
  "round_id": "round_20260901_issue487_nerelan_runtime_brand_r2_v1",
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
  "previous_audit_outcome": "BRAND_R1_RUNTIME_PATHS_FAIL_CLOSED_TO_PATH_B",
  "workstream_id": "issue487-nerelan-runtime-brand-r2-v1",
  "source_issue": 487,
  "integration_base_ref": "main",
  "base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "activation_base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "starting_head": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "required_branch": "owner/issue487-nerelan-runtime-brand-r2-v1",
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
    "reverse_agent/gui.py",
    "reverse_agent/harness.py",
    "reverse_agent/olly_scripts/collect_evidence.py"
  ],
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 3,
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
    "verify exact main base eb1cbfa520582988e90e83d798d53379ba537fa8 and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue487_r2v1.activation_publication",
      "command": "publish the immutable Decision-only activation head to owner/issue487-nerelan-runtime-brand-r2-v1 and create exactly one Draft PR against locked main so repository-owned State Gate can generate the command plan and evaluate transition preflight",
      "phase": "activation_publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_truth"
    },
    {
      "command_id": "issue487_r2v1.implement_runtime_brand_copy",
      "command": "after PRE_EXECUTION_AUTHORIZED change only current user-facing product-brand strings in reverse_agent/gui.py reverse_agent/harness.py and reverse_agent/olly_scripts/collect_evidence.py from Reverse Agent parent-brand wording to Nerelan reverse-engineering wording without changing runtime logic schemas compatibility identifiers subprocess behavior or execution policy",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_provenance",
      "allowed_mutated_paths": [
        "reverse_agent/gui.py",
        "reverse_agent/harness.py",
        "reverse_agent/olly_scripts/collect_evidence.py"
      ]
    },
    {
      "command_id": "issue487_r2v1.validate_runtime_brand_copy",
      "command": "run python -m compileall -q reverse_agent and git diff --check and inspect the exact diff to prove only bounded product-brand text changed",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "lint", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_provenance"
    },
    {
      "command_id": "issue487_r2v1.publish_implementation",
      "command": "after validation push the exact implementation head to the already-bound branch and update only the existing Draft PR; require fresh State Gate Decision Preflight CI and exact-head audit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_truth",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue487_r2v1.final_exact_head_acceptance",
      "command": "require exact-head CI State Gate and Decision Preflight success plus diff audit proving compatibility identifiers and runtime behavior are unchanged before any Owner-controlled landing lifecycle",
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
    "reverse_agent/gui.py",
    "reverse_agent/harness.py",
    "reverse_agent/olly_scripts/collect_evidence.py"
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/gui.py",
    "reverse_agent/harness.py",
    "reverse_agent/olly_scripts/collect_evidence.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "README.txt",
    "README.md"
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
    ".github/**",
    ".codex-skills/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/**",
    "reverse_agent/model_access/**",
    "reverse_agent/base_platform/**",
    "frontend/**",
    "tests/**"
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
      "publish the immutable Decision-only activation head to owner/issue487-nerelan-runtime-brand-r2-v1 and create exactly one Draft PR against locked main so repository-owned State Gate can generate the command plan and evaluate transition preflight",
      "after validation push the exact implementation head to the already-bound branch and update only the existing Draft PR; require fresh State Gate Decision Preflight CI and exact-head audit"
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

## Goal

Close the remaining legacy reverse-engineering runtime brand copy under #487 without altering runtime behavior or technical compatibility identifiers.

## Stop conditions

Stop if transition preflight does not return PRE_EXECUTION_AUTHORIZED, if any path outside the three runtime files is required for product implementation, or if validation reveals a behavioral/schema/compatibility change.
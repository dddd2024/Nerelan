# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260908_issue423_windows_platform_ci_r2_v3",
  "round_id": "round_20260908_issue423_windows_platform_ci_r2_v3",
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
  "decision_scope": "FRESH_MAIN_WINDOWS_HOSTED_LAUNCHER_LIFECYCLE_CI_LANE_R2_V3_POST640_SURFACE",
  "not_product_redesign": true,
  "follows_last_decision_id": "decision_20260908_issue423_windows_platform_ci_r2_v2",
  "follows_last_round_id": "round_20260908_issue423_windows_platform_ci_r2_v2",
  "previous_audit_outcome": "R2_V1_ACTIVATION_BRANCH_A3FF0A6F_STALE_TERMINAL_NEGATIVE_AUTHORITY_ONLY;R2_V2_BASE_EB1CBFA5_STALE_TERMINAL_NEGATIVE_AUTHORITY_ONLY;PR424_WRONG_RISK_R1_FOR_WORKFLOW_PATH_CLOSED_UNMERGED_TERMINAL_NEGATIVE_AUTHORITY_ONLY;FRESH_CURRENT_MAIN_7452A592_LOCKED_FOR_V3_RE_ANCHOR",
  "workstream_id": "issue423-windows-platform-ci-r2-v3",
  "source_issue": 423,
  "parent_issue": 363,
  "integration_base_ref": "main",
  "base_sha": "7452a592edfce2a243c4524b1cb78c8172e748a9",
  "activation_base_sha": "7452a592edfce2a243c4524b1cb78c8172e748a9",
  "starting_head": "7452a592edfce2a243c4524b1cb78c8172e748a9",
  "required_branch": "owner/issue423-windows-platform-ci-r2-v3",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "workflow_profile": "windows_ci_r2",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "dependency_install_limit": 0,
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
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "READ_ONLY_LANDING_CANDIDATE_VALIDATION",
  "landing_authority_scope_note": "Only the exact new specialized Windows Hosted proof workflow .github/workflows/windows-platform-v1.yml is authorized. No launcher, test, existing workflow, dependency, product, or frontend mutation is authorized. No merge, Ready, auto-merge, direct main push, rebase, squash, amend, force push, workflow rerun, workflow dispatch, release, deploy or tag is authorized here. Final Ready/Merge requires a separate independent Owner landing authority.",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": false,
  "source_test_mutation_authorized": false,
  "workflow_mutation_scope": "ADD_NEW_WINDOWS_HOSTED_LANES_ONLY_NO_EXISTING_WORKFLOW_EDIT",
  "historical_negative_authority": {
    "pr424": "5758061b4fb4f2c85a25eca057084a3aa9167359",
    "pr424_disposition": "CLOSED_UNMERGED_TERMINAL_WRONG_RISK_NEGATIVE_AUTHORITY_ONLY",
    "issue423_r2_v1_branch": "owner/issue423-windows-platform-ci-r2-v1",
    "issue423_r2_v1_branch_sha": "a3ff0a6fbf84e216e0765581a408fdd2ee0c5592",
    "issue423_r2_v1_disposition": "STALE_ACTIVATION_BRANCH_TERMINAL_STALE_NEGATIVE_AUTHORITY_ONLY",
    "issue423_r2_v2_base": "eb1cbfa520582988e90e83d798d53379ba537fa8",
    "issue423_r2_v2_disposition": "STALE_V2_BASE_TERMINAL_STALE_NEGATIVE_AUTHORITY_ONLY",
    "no_reuse_no_rebase_no_force_update": true
  },
  "fresh_worktree_contract": {
    "creation_required": true,
    "source_commit": "7452a592edfce2a243c4524b1cb78c8172e748a9",
    "source_ref": "origin/main",
    "target_branch": "owner/issue423-windows-platform-ci-r2-v3",
    "no_switch_no_reset_no_stash_no_clean_other_worktree": true,
    "clean_status_required_at_activation": true
  },
  "semantic_implementation_contract": {
    "workflow_path": ".github/workflows/windows-platform-v1.yml",
    "runner": "windows-latest",
    "test_command": "python -m pytest tests/platform_v1/test_dev_up_contract.py -q",
    "install_command": "python -m pip install -e \".[test]\"",
    "checkout_ref": "github.event.pull_request.head.sha || github.sha",
    "continue_on_error_forbidden": true,
    "blanket_skip_or_xfail_forbidden": true,
    "deselection_forbidden": true,
    "false_green_wrapper_forbidden": true,
    "provider_or_model_calls_forbidden": true,
    "credential_access_forbidden": true,
    "no_ubuntu_baseline_duplication": true,
    "trigger_surfaces": [
      "launch_reverse_agent.bat",
      "dev-up.ps1",
      "dev-down.ps1",
      "tests/platform_v1/test_dev_up_contract.py",
      ".github/workflows/windows-platform-v1.yml"
    ]
  },
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
      "command_id": "issue423_r2v3.bootstrap_and_preflight",
      "command": "verify exact fresh locked main 7452a592edfce2a243c4524b1cb78c8172e748a9 and fresh isolated worktree branch merge-base; commit this immutable R2 Decision as the unique first commit; run startup snapshot transition command plan transition lint transition preflight pre and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before any workflow mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue423_r2v3.materialize_windows_workflow",
      "command": "add exactly one new specialized Windows Hosted proof workflow .github/workflows/windows-platform-v1.yml that runs on windows-latest, checks out the exact tested head, installs the repository existing test extras, and executes python -m pytest tests/platform_v1/test_dev_up_contract.py -q; no continue-on-error, no blanket skip or xfail, no deselection, no false-green wrapper, no provider or model call, no credential access, no Ubuntu baseline duplication",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        ".github/workflows/windows-platform-v1.yml"
      ]
    },
    {
      "command_id": "issue423_r2v3.validate",
      "command": "run git status --short and git diff --check; re-run transition lint transition command plan transition preflight pre and worktree publication readiness; run the applicable non-Windows deterministic governance tests; require PUBLICATION_READY and zero diff check violations",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["unit_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue423_r2v3.publish",
      "command": "after all blocking validation passes push the exact branch owner/issue423-windows-platform-ci-r2-v3 to locked main 7452a592edfce2a243c4524b1cb78c8172e748a9 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue423_r2v3.exact_head_acceptance",
      "command": "require natural exact-head CI Decision Preflight State Gate and Windows Hosted proof lane on the Draft PR; Windows Hosted proof lane must execute python -m pytest tests/platform_v1/test_dev_up_contract.py -q on windows-latest and report terminal SUCCESS; keep the PR Draft and do NOT Ready or merge under this Decision",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "read_only_audit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
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
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
    "tests/platform_v1/test_dev_up_contract.py",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    ".github/workflows/state-gate.yml",
    "pyproject.toml",
    "frontend/**",
    "reverse_agent/**",
    "tests/**"
  ],
  "reference_only_paths": [
    "AGENTS.md",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
    "tests/platform_v1/test_dev_up_contract.py",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    ".github/workflows/state-gate.yml",
    "pyproject.toml",
    "frontend/**",
    "reverse_agent/**",
    "tests/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md", "README.md", "README.txt", "docs/**", ".codex-skills/**",
    "launch_reverse_agent.bat", "launch_nerelan.bat", "dev-up.ps1", "dev-down.ps1",
    "tests/platform_v1/test_dev_up_contract.py", "tests/**",
    ".github/workflows/ci.yml", ".github/workflows/decision-preflight.yml",
    ".github/workflows/freshness.yml", ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml", ".github/workflows/state-gate.yml",
    "frontend/**", "reverse_agent/**", "scripts/**", "provider/**", "model/**", "credential/**",
    "requirements*.txt", "pyproject.toml", "project_state/mainline_merge_intents/**", "project_state/schemas/**",
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/integration_baselines/**", "project_state/mainline_recoveries/**",
    "**/STOP", "**/owner_handoffs/**"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean",
    "stash", "restore", "amend", "history_rewrite", "unknown_binary_execution", "secrets", "destructive_delete",
    "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "dependency_install",
    "second_decision_commit", "second_command_runner", "active_json_rewrite", "product_replay",
    "ruleset_weakening", "required_check_weakening", "test_semantics_change",
    "existing_workflow_mutation", "launcher_mutation", "test_file_mutation", "dependency_mutation",
    "reuse_v1_decision", "reuse_v2_decision", "rebase_v1", "rebase_v2", "continue_push_v1", "continue_push_v2",
    "force_update_v1", "force_update_v2", "reopen_v1", "reopen_v2",
    "local_authoring", "implicit_user_local_fallback",
    "continue_on_error_on_windows_proof", "blanket_skip_or_xfail", "deselection_on_windows_proof",
    "false_green_wrapper", "runner_dispatch_as_substitute", "manual_dispatch_as_substitute",
    "manual_runner_dispatch_as_substitute_for_pr_triggered_proof",
    "ubuntu_baseline_duplication"
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
      "after all blocking validation passes push the exact branch owner/issue423-windows-platform-ci-r2-v3 to locked main 7452a592edfce2a243c4524b1cb78c8172e748a9 and create exactly one Draft PR with body recording the immutable R2 authority snapshot; never mark Ready and never merge under this Decision"
    ],
    "user_local_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/windows-platform-v1.yml", "minimum_risk": "R2"}
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/windows-platform-v1.yml"
  ],
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "owner/issue423-windows-platform-ci-r2-v3",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  }
}
```

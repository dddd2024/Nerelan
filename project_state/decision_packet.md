# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260826_issue370_strict_required_checks_r2_v1",
  "round_id": "round_20260826_issue370_strict_required_checks_r2_v1",
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
  "follows_last_decision_id": "decision_20260826_issue367_engineering_landing_boundary_r2_v4",
  "follows_last_round_id": "round_20260826_issue367_engineering_landing_boundary_r2_v4",
  "previous_audit_outcome": "PR378_EXACT_HEAD_ACCEPTED_DRAFT_BLOCKED_ON_STRICT_RULESET_DEPENDENCY",
  "workstream_id": "issue370-strict-required-checks-r2-v1",
  "source_issue": 370,
  "parent_issue": 367,
  "integration_base_ref": "main",
  "base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "activation_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "starting_head": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "required_branch": "owner/issue370-strict-required-checks-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
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
  "test_semantics_changes_allowed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf and fresh settings branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue370_r2v1.bootstrap",
      "command": "verify the locked main base and fresh settings branch; commit this Decision as the unique first commit; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY; commit exactly the five generated governance artifacts; do not push or create a PR",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "code_read",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue370_r2v1.observe_ruleset",
      "command": "read GitHub server truth for repository dddd2024/reverse-agent Ruleset 21023698 and require enforcement active, target branch, conditions include refs/heads/main, pull_request rule present with merge-only method, deletion and non_fast_forward rules present, required_status_checks contexts exactly baseline and state-gate with strict false before mutation, bypass actor 206685950 User pull_request only, and no layered stricter equivalent; stop on any drift",
      "phase": "pre_mutation_observation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue370_r2v1.update_ruleset_strict",
      "command": "perform exactly one authenticated PUT to /repos/dddd2024/reverse-agent/rulesets/21023698 preserving name, target, active enforcement, exact include conditions, exact User 206685950 pull_request-only bypass, deletion, non_fast_forward, pull_request parameters and baseline/state-gate required contexts while changing only required_status_checks.strict_required_status_checks_policy from false to true; do not enable auto-merge, merge queue, new bypass, direct push, release, deployment, or another Ruleset",
      "phase": "settings_mutation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue370_r2v1.verify_ruleset",
      "command": "perform two independent GitHub server readbacks of Ruleset 21023698 and require active enforcement, main target, pull request required, deletion and non_fast_forward present, required contexts exactly baseline and state-gate, strict_required_status_checks_policy true, bypass unchanged and current_user_can_bypass pull_requests_only; verify PR378 remains Open Draft with unchanged exact head/base and required checks; do not close Issue370 until a deterministic natural main advance proves a previously green stale PR is not merge-eligible and a fresh current-base PR remains eligible",
      "phase": "post_mutation_verification",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
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
  "reference_paths": [],
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
    "requirements*.txt",
    "pyproject.toml",
    ".codex-skills/**",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "reverse_agent/project_state.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_ci.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/github_adapter.py",
    "reverse_agent/architecture/**",
    "reverse_agent/base_platform/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/worktree_state.py",
    "frontend/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "project_state/schemas/**",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_authority_adapter.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/platform_v1/test_task_service.py",
    "tests/base_platform/**",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_execution_evidence.py",
    "tests/test_decision_preflight.py",
    "tests/test_trusted_command_runner.py"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready",
    "force_push",
    "rebase",
    "squash",
    "reset",
    "clean",
    "stash",
    "restore",
    "amend",
    "history_rewrite",
    "unknown_binary_execution",
    "secrets",
    "destructive_delete",
    "privileged_remote_execution",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "issue_comment",
    "issue_close",
    "pull_request_comment",
    "dependency_install",
    "browser_execution",
    "snapshot_update",
    "arbitrary_remote_browsing",
    "external_url_navigation",
    "offensive_security_or_network_attack_work",
    "second_decision_commit",
    "make_state_gate_push_pre_merge",
    "broad_dependency_change",
    "new_gate_family",
    "new_decision_artifact_family",
    "new_receipt_artifact_family",
    "modify_issue345_decision",
    "modify_issue360_branch_or_pr",
    "modify_issue363_branch_or_pr",
    "modify_issue364_decision",
    "revisit_issue283_protection",
    "mark_ready_pr360",
    "merge_pr360",
    "close_pr360",
    "rebase_pr360",
    "start_issue358",
    "start_issue363",
    "delete_or_rotate_inherited_active_intent",
    "second_post_publication_binding_commit",
    "reuse_v1_or_v2_decision_or_binding",
    "create_owner_merge_attestation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "known_binary_execution_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_comment_allowed": false,
    "github_pr_creation_allowed": false,
    "github_pr_close_allowed": false,
    "remote_observation_read_only_allowed": true,
    "github_ruleset_mutation_allowed": true
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/command_plan.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/startup_snapshot.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/bootstrap_state.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/transition_command_plan_preview.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/transition_preflight_result.json",
      "minimum_risk": "R2"
    }
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "ci_network_exceptions": [
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
  ],
  "github_ruleset_mutation_allowed": true,
  "github_ruleset_mutation_attempt_limit": 1,
  "github_ruleset_id": 21023698,
  "github_ruleset_repository": "dddd2024/reverse-agent",
  "github_ruleset_expected_name": "reverse-agent protected integration v1",
  "github_ruleset_required_contexts": [
    "baseline",
    "state-gate"
  ],
  "github_ruleset_strict_before": false,
  "github_ruleset_strict_after": true,
  "github_ruleset_bypass_actor": {
    "actor_id": 206685950,
    "actor_type": "User",
    "bypass_mode": "pull_request"
  },
  "settings_mutation_requires_server_readback": true,
  "required_server_readback_count": 2,
  "deterministic_stale_pr_scenario_required_before_issue_close": true,
  "issue_close_allowed": false
}
```

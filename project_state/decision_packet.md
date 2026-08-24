# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue325_landing_candidate_r2_v8",
  "round_id": "round_20260824_issue325_landing_candidate_r2_v8",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue325_landing_candidate_r2_v7",
  "follows_last_round_id": "round_20260824_issue325_landing_candidate_r2_v7",
  "previous_audit_outcome": "ISSUE325_R2_V7_BLOCKED_DURABLE_TRUSTED_IDENTITY_TEST_FIXTURE",
  "workstream_id": "issue325-landing-candidate-r2-v8",
  "source_issue": 325,
  "accepted_source_pr": 337,
  "accepted_source_head_sha": "b430e0d026ff84e40b0d60c804bfe57b1ce34ca4",
  "accepted_source_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "integration_base_ref": "main",
  "base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "activation_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "starting_head": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "required_branch": "owner/issue325-decision-immutability-landing-r2-v8",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "product_replay_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "runner_dispatch_limit": 0,
  "tag_or_release_limit": 0,
  "deployment_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "accepted_source_replay": {
    "source_ref": "b430e0d026ff84e40b0d60c804bfe57b1ce34ca4",
    "blob_equal_paths": [
      ".github/workflows/ci.yml",
      "reverse_agent/project_gate.py",
      "tests/platform_v1/test_contracts.py",
      "tests/test_ci_responsibility.py",
      "tests/test_control_plane_transition.py",
      "tests/test_project_gate.py"
    ],
    "exclude_v4_decision_and_gates": true,
    "dirty_worktree_import_allowed": false,
    "cherry_pick_allowed": false
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact base branch merge-base and no remote collision",
    "commit this immutable Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue325_v8.bootstrap",
      "command": "verify locked base and fresh branch; commit Decision first; generate five gates and require PRE_EXECUTION_AUTHORIZED",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks", "generate_governance_artifact", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue325_v8.replay",
      "command": "with apply_patch replay the six accepted PR337 implementation paths with committed blob equality and fix only the trusted-host production-relay test fixture to pass resolved authority/planning SHAs; create one implementation commit",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "bounded_workflow_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        ".github/workflows/ci.yml",
        "reverse_agent/project_gate.py",
        "tests/platform_v1/test_contracts.py",
        "tests/test_ci_responsibility.py",
        "tests/test_control_plane_transition.py",
        "tests/test_project_gate.py",
        "tests/platform_v1/test_task3c_v6_production_relay.py"
      ]
    },
    {
      "command_id": "issue325_v8.validate_and_publish",
      "command": "run focused and blocking tests plus blob equality and transition gates; commit one generated-gate commit; push once and create one Draft PR",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "generate_governance_artifact", "commit", "push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue325_v8.bind_intent",
      "command": "after the real PR number is known archive current active intent byte-identically as archive/pr331_v2.json; bind active.json schema v2 to the exact new PR base Decision and Command Plan; create one binding commit",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr331_v2.json"
      ]
    },
    {
      "command_id": "issue325_v8.final_push_and_audit",
      "command": "rerun required validation; push the binding commit once; require exact-head CI State Gate and Decision Preflight SUCCESS; keep Draft and stop after independent exact-head ACCEPT",
      "phase": "audit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "push", "repository_observation", "network_access", "independent_audit"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
    "reverse_agent/project_gate.py",
    "tests/platform_v1/test_contracts.py",
    "tests/test_ci_responsibility.py",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr331_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/test_path_a_gate.py",
    "tests/test_planning_and_github_adapters.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**", "docs/**", "requirements*.txt", "pyproject.toml", "AGENTS.md",
    "reverse_agent/control_plane/**", "reverse_agent/mainline_landing.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/platform_v1/**",
    ".github/workflows/state-gate.yml", ".github/workflows/decision-preflight.yml", ".github/workflows/model-access.yml", ".github/workflows/freshness.yml",
    "project_state/schemas/**", "project_state/mainline_recoveries/**", "project_state/rounds/**", "project_state/audits/**",
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "dependency_install", "live_model_call", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read", "runner_dispatch", "workflow_rerun",
    "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_comment", "pull_request_close", "browser", "playwright", "offensive_security",
    "cherry_pick_pr337", "import_pr337_history", "import_pr337_dirty_worktree", "modify_pr337", "second_decision_commit"
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
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "publication_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "two normal fast-forward pushes to the exact named branch",
      "one Draft PR creation against locked main",
      "read-only exact-head workflow and audit observation"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    ".github/workflows/ci.yml",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr331_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE325_V8_BOUND_DRAFT_ACCEPTED_FOR_SEPARATE_LANDING_DECISION",
  "blocked_terminal": "ISSUE325_V8_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Replay the accepted PR #337 implementation onto locked current main, bind the resulting Draft PR to a schema-v2 active merge intent, pass exact-head checks and independent audit, then stop for a separate landing Decision.

## Acceptance

1. Decision is the unique immutable first commit from locked main.
2. One implementation commit keeps six replay blobs equal to accepted PR337 and fixes only the production-relay trusted-identity test fixture.
3. One generated-gate commit and one two-path intent-binding commit occur.
4. Two pushes and one Draft PR occur; final exact-head CI, State Gate, Decision Preflight and independent audit pass.
5. No merge, ready, comment, rerun, browser, dependency/model/provider/credential action or mutation of PR337 occurs.

## Execution policy

- Use `apply_patch`; do not cherry-pick or import dirty v4/v5/v6/v7 worktrees.
- Stage only exact allowed paths. Never reset, clean, stash, restore, amend, rebase or force push.
- Keep the new PR Draft. Attestation and merge require a separate immutable landing Decision.

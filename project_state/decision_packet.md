# Decision Packet — #721 safe non-overlap base refresh current-main v6

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260918_issue721_safe_base_refresh_r2_v6_current",
  "round_id": "round_20260918_issue721_safe_base_refresh_r2_v6_current",
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
  "decision_scope": "SAFE_NONOVERLAP_BASE_REFRESH_CURRENT_MAIN_V6",
  "source_issue": 721,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User delegated Owner execution and Remote Desktop Commander trusted-worker access. #891 correctness prerequisite is landed on current main. Historical #721 v4/v5 semantics are locally validated read-only content evidence; this fresh v6 re-materializes only the corrected safe-refresh delta against current main and preserves #891 role-split landing semantics.",
  "supersedes_decision_id": "decision_20260910_issue721_safe_base_refresh_r2_v5",
  "superseded_evidence": "Local-only v5 semantic head a8fa7ec1998b658311c7a7407dd73b521d19ced8 was never published because main drifted. v4/v5 are content/test evidence only; no history reuse.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "activation_base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "starting_head": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "required_branch": "owner/issue721-safe-base-refresh-r2-v6-current",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
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
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "workflow_profile": "baseline",
  "semantic_implementation_contract": {
    "specification": "Extend the landed #891 false/none Owner landing machinery with fail-closed safe non-overlap base-refresh authority. Preserve unchanged accepted target head, exact target Decision/review binding and the ordinary-vs-formal State Gate role split. A refresh is admissible only when original locked base is an ancestor of refreshed current main, target/intervening paths are machine-derived and conservatively non-overlapping, authority-sensitive and dependency-manifest drift are absent, exact Git objects exist, current main/head are revalidated, and git merge-tree yields the exact expected tree. Missing refresh fields fall back to strict locked-base behavior.",
    "execution_surface_note": "Decision/source/test/commit run only in the fresh isolated trusted_worker checkout. Generated gate files are ephemeral with zero commit budget. Remote commit graph/ref/Draft publication is GitHub control plane only; local git push is forbidden.",
    "completion_boundary": "One Decision commit plus one semantic commit and one Draft PR. No generated-governance commit, Ready, Merge, rerun, dispatch, rebase or history rewrite."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
    "amend",
    "auto_merge",
    "browser_execution",
    "destructive",
    "direct_push_main",
    "external_reverse_tool_invocation",
    "force_push",
    "generated_governance_commit",
    "history_rewrite",
    "mark_ready",
    "merge",
    "model_api_invocation",
    "rebase",
    "runner_dispatch",
    "squash",
    "tag_or_release",
    "target_branch_push",
    "unknown_binary_execution",
    "workflow_dispatch",
    "workflow_rerun"
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Create only the v6 Decision/semantic commit graph and branch owner/issue721-safe-base-refresh-r2-v6-current in dddd2024/Nerelan, then one Draft PR against main@ef8bb6959ac37301c880e0971a97a9d56e9c99a9; comment only on Issue721/156 and that Draft; never Ready/Merge."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue721v6.bootstrap",
      "command": "Verify exact clean isolated current-main checkout and immutable Decision. Run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, worktree-publication-readiness. Generated gates are ephemeral and uncommitted. Require PRE_EXECUTION_AUTHORIZED before source/test mutation.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue721v6.implement",
      "command": "After PRE_EXECUTION_AUTHORIZED re-materialize only the locally validated safe-refresh delta from v5 onto current main in reverse_agent/mainline_landing.py and tests/test_mainline_landing.py. Preserve landed #891 role-split semantics. No cherry-pick/rebase/history reuse. Fix any integration conflict from current main explicitly, run focused safe-refresh and false-none regressions, then commit exactly once.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "tests/test_mainline_landing.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v6.validate",
      "command": "Run tests/test_mainline_landing.py focused safe-refresh plus false-none regressions, tests/test_project_gate.py false-none/landing-authority regressions, git diff --check, and post-semantic transition preflight/readiness. Natural exact-head CI/Decision Preflight/State Gate are mandatory final validation.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "local_static_check",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v6.publish",
      "command": "Through github_control_plane only create the exact Decision then semantic commit graph, branch owner/issue721-safe-base-refresh-r2-v6-current, and one Draft PR against main@ef8bb6959ac37301c880e0971a97a9d56e9c99a9. No local git push, Ready or Merge.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue721v6.observe",
      "command": "Fresh-read exact base/head/trees, natural Actions, and Owner-audit safe-refresh semantics including #891 coupling and #664 positive fixture. No Ready/Merge.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "code_read",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "workstream_id": "issue721-safe-base-refresh-r2-v6-current",
  "follows_last_decision_id": "decision_20260910_issue721_safe_base_refresh_r2_v5",
  "follows_last_round_id": "round_20260910_issue721_safe_base_refresh_r2_v5",
  "fresh_base": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "current_main_expected": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "workflow_dispatch_limit": 0,
  "workflow_dispatch_allowed": false,
  "migration_fixture_issue": 664,
  "mother_roadmap_issue": 137
}
```

## Goal

Add fail-closed safe non-overlap base refresh to the landed false/none Owner landing path without changing the accepted target head or weakening #891.

## Build vs reuse

Reuse current landing machinery, GitHubRemoteAcceptanceVerifier, system Git and git merge-tree. Reuse only validated v4/v5 file-level safe-refresh semantics as content evidence. Do not add a scheduler, queue, Git library, GitHub client, workflow, dependency, database or schema.

## Stop conditions

Stop on main/base drift, Decision mutation, scope expansion, test/preflight failure, #891 semantic regression, publication-surface mismatch or exhausted budget. Generated gate evidence may be regenerated but never committed. Never Ready/Merge under this Decision.

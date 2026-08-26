# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260826_issue367_engineering_landing_boundary_r2_v4",
  "round_id": "round_20260826_issue367_engineering_landing_boundary_r2_v4",
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
  "follows_last_decision_id": "decision_20260826_issue367_engineering_landing_boundary_r2_v3",
  "follows_last_round_id": "round_20260826_issue367_engineering_landing_boundary_r2_v3",
  "previous_audit_outcome": "V3_PUBLISHED_PR377_POST_BINDING_BLOCKED_BY_WRITE_RESULT_FALSE_BOOTSTRAP_SIDE_EFFECT",
  "workstream_id": "issue367-engineering-landing-boundary-r2-v4",
  "source_issue": 367,
  "parent_issue": 365,
  "integration_base_ref": "main",
  "base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "activation_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "starting_head": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "required_branch": "owner/issue367-engineering-landing-boundary-r2-v4",
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
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 1,
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
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "landing_revalidation_required_for_actions": [
    "ready_for_review"
  ],
  "landing_revalidation_required_when_draft": false,
  "owner_attestation_required_for_ready_state": true,
  "attestation_head_must_match_current_pr_head": true,
  "ready_state_synchronize_must_revalidate": true,
  "converted_to_draft_returns_to_draft_semantics": true,
  "malformed_event_path_fail_closed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue367_r2v4.bootstrap",
      "command": "verify the locked main base and fresh v4 branch; commit this v4 Decision as the unique first commit; run startup-snapshot, transition-command-plan, transition-lint, a normal write-result transition-preflight --mode pre, and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY; commit exactly the five initial generated governance artifacts as the first of at most two generated-governance commits before implementation",
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
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue367_r2v4.landing_authority_gate",
      "command": "verify the exact v3 source patch befced4b916890467eec710adc52d0510db0bccc applies cleanly to the locked base, replay it without committing, and keep the v3 workflow/mainline-landing behavior; in the same single source commit make transition_preflight write_result=False fully side-effect free, make write_result=True bootstrap expiry idempotent byte-for-byte for the same Decision and Round, and still rebind inherited or different Decision/Round bootstrap authority; update the docstring so write_result controls every persistence side effect; preserve strict pull-request event typing, non-Draft landing revalidation, canonical schema-v3 intent and attestation reuse, post-merge fail-closed behavior, and Path-A lifecycle semantics; do not add a second Gate, schema, intent, verifier, or authority store",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/project_gate.py",
        "reverse_agent/mainline_landing.py",
        ".github/workflows/state-gate.yml"
      ]
    },
    {
      "command_id": "issue367_r2v4.landing_authority_tests",
      "command": "verify the exact v3 test patch f4bd0ed525467b8f0d75a462b9d2c205476d00a4 applies cleanly to the locked base and replay it without committing; retain the complete V3 cross-layer authority-drift regression matrix and add transition control-plane tests proving write_result=False leaves the complete project_state filename-and-byte mapping unchanged, repeated successful write_result=True calls for the same Decision/Round leave bootstrap_state.json byte-for-byte unchanged, and a different inherited Decision or Round is rebound with the current expiry; preserve historical PR347 schema-v3, post-merge fail-closed, #364 Path-A lifecycle, and direct #365 engineering-only blocking coverage",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_project_gate.py",
        "tests/test_mainline_landing.py",
        "tests/test_control_plane_transition.py",
        "tests/platform_v1/test_merge_intent.py",
        "tests/test_ci_responsibility.py",
        "tests/test_path_a_gate.py"
      ]
    },
    {
      "command_id": "issue367_r2v4.validate_and_publish_draft",
      "command": "run python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_mainline_landing.py tests/platform_v1/test_merge_intent.py tests/test_ci_responsibility.py tests/test_path_a_gate.py -q; run transition-lint, worktree-publication-readiness, and git diff --check; additionally call transition_preflight(write_result=False) while hashing all tracked gate blobs and recording git status before and after, and require the returned PRE_EXECUTION_AUTHORIZED plus byte-identical/status-identical state; push the exact branch for the first normal push and create exactly one replacement Draft PR against locked main; identify PR377 as superseded but do not comment on or close it yet; do not mark Ready, merge, rerun workflows, or dispatch runners",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "unit_test",
        "lint",
        "local_static_check",
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_r2v4.post_publication_binding",
      "command": "after the replacement Draft PR yields its actual GitHub PR number, derive archive/pr347_v3.json only from the locked-base inherited PR347 active intent and prove byte-for-byte Git-blob identity; bind active.json exactly once to the replacement PR using schema v3, raw 64-hex v4 Decision and Command Plan digests, locked base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf, workflow_profile baseline, exact baseline workflows, merge method merge, equal_to_accepted_head_tree, and bounded expiry; commit only the two binding paths and perform the second normal push; neither issue 367 nor superseded PR377 may substitute for the actual replacement PR number",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true,
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr347_v3.json"
      ]
    },
    {
      "command_id": "issue367_r2v4.final_evidence_sync",
      "command": "after the replacement-PR binding commit and second push, obtain current Draft PR event facts read-only and record bootstrap_state.json bytes; run the final local transition-preflight with write_result=True on the exact named branch and supplied Draft event; require PRE_EXECUTION_AUTHORIZED, current branch identity, zero blockers, and byte-identical bootstrap_state.json; require git diff --name-only to contain only project_state/gates/transition_preflight_result.json and forbid the artifact from claiming the commit that contains itself; commit that single final evidence file, rerun transition-lint, worktree-publication-readiness, focused tests, and git diff --check, then perform the third and final normal push; require fresh exact-head CI, State Gate, and Decision Preflight and stop for independent audit",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_static_check",
        "unit_test",
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true,
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ],
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue367_r2v4.close_superseded_pr377",
      "command": "only after the replacement Draft PR has completed all three pushes, all required exact-head workflows are SUCCESS, and an independent exact-head auditor has accepted that replacement head: re-observe PR377 and require it is still OPEN, Draft, based on 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf, and headed by f4bd0ed525467b8f0d75a462b9d2c205476d00a4; then consume the single exact superseded-PR close attempt to close PR377 without a comment and without deleting either remote branch; if any fact drifted, stop without closing",
      "phase": "post_acceptance_cleanup",
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
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_control_plane_transition.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/test_ci_responsibility.py",
    "tests/test_path_a_gate.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr347_v3.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/project_state.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_ci.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/architecture/report_truth.py",
    "reverse_agent/github_adapter.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
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
    "revisit_github_ruleset",
    "mark_ready_pr360",
    "merge_pr360",
    "close_pr360",
    "rebase_pr360",
    "start_issue358",
    "start_issue363",
    "delete_or_rotate_inherited_active_intent",
    "second_post_publication_binding_commit",
    "reuse_v1_or_v2_decision_or_binding",
    "github_ruleset_mutation",
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
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {
      "pattern": ".github/workflows/state-gate.yml",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/project_gate.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/mainline_merge_intents/active.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/test_project_gate.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/test_control_plane_transition.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/platform_v1/test_merge_intent.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/test_mainline_landing.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/test_path_a_gate.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/test_ci_responsibility.py",
      "minimum_risk": "R1"
    }
  ],
  "authorized_risk_paths": [
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "project_state/mainline_merge_intents/active.json"
  ],
  "authorized_risk_tier": "R2",
  "ci_network_exceptions": [
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
  ],
  "landing_revalidation_required_when_pr_is_non_draft": true,
  "supplied_pr_event_required_fields": [
    "action",
    "positive_pr_number",
    "lowercase_40_hex_head_sha",
    "lowercase_40_hex_base_sha",
    "boolean_draft"
  ],
  "live_remote_pr_identity_required": true,
  "live_remote_pr_must_match_event": true,
  "live_remote_base_must_match_locked_base": true,
  "canonical_schema_v3_raw_hex_intent_required": true,
  "canonical_mainline_landing_validation_reuse_required": true,
  "second_gate_schema_or_verifier_forbidden": true,
  "owner_attestation_creation_by_agent_allowed": false,
  "github_ruleset_mutation_allowed": false,
  "final_tracked_preflight_required": true,
  "final_tracked_preflight_status_required": "PRE_EXECUTION_AUTHORIZED",
  "final_tracked_preflight_branch_identity_required": true,
  "final_tracked_preflight_self_referential_head_claim_forbidden": true,
  "superseded_pr_close_attempt_limit": 1,
  "superseded_pr_number": 377,
  "superseded_pr_expected_head_sha": "f4bd0ed525467b8f0d75a462b9d2c205476d00a4",
  "superseded_pr_expected_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "superseded_pr_must_remain_draft_until_replacement_acceptance": true,
  "superseded_pr_branch_deletion_allowed": false,
  "replay_source_commit": "befced4b916890467eec710adc52d0510db0bccc",
  "replay_test_commit": "f4bd0ed525467b8f0d75a462b9d2c205476d00a4",
  "cherry_pick_no_commit_limit": 2,
  "authorized_cherry_pick_no_commit_commits": [
    "befced4b916890467eec710adc52d0510db0bccc",
    "f4bd0ed525467b8f0d75a462b9d2c205476d00a4"
  ],
  "write_result_false_must_be_fully_side_effect_free": true,
  "bootstrap_expiry_must_be_idempotent_for_same_decision_round": true,
  "bootstrap_expiry_must_rebind_for_different_decision_or_round": true
}
```

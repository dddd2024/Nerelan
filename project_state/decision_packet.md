# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260825_issue367_engineering_landing_boundary_r2_v1",
  "round_id": "round_20260825_issue367_engineering_landing_boundary_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260825_issue364_path_a_lifecycle_coherence_r2_v1",
  "follows_last_round_id": "round_20260825_issue364_path_a_lifecycle_coherence_r2_v1",
  "previous_audit_outcome": "ISSUE365_ENGINEERING_LANDING_BOUNDARY_R2_OWNER_AUDIT_COMPLETE",
  "workstream_id": "issue367-engineering-landing-boundary-r2-v1",
  "source_issue": 367,
  "parent_issue": 365,
  "integration_base_ref": "main",
  "base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "activation_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "starting_head": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "required_branch": "owner/issue367-engineering-landing-boundary-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 1,
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
      "command_id": "issue367_r2v1.bootstrap",
      "command": "verify locked base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf and fresh branch; commit Decision first; generate startup snapshot, command plan, transition lint, transition preflight, and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["code_read", "local_static_check", "commit"],
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
      "command_id": "issue367_r2v1.landing_authority_gate",
      "command": "extend transition_preflight in reverse_agent/project_gate.py with an optional --event-path argument; when the event action is ready_for_review and the Decision contract declares mainline_merge_intent_required=false, return BLOCKED with a deterministic engineering_pr_not_landing_authorized reason; when mainline_merge_intent_required=true and ready_for_review, load the active mainline merge intent and verify it binds the exact current PR number, Decision ID/digest, Command Plan digest, locked base, workflow profile, and expiry; any mismatch returns BLOCKED with landing_authority_mismatch or landing_authority_required; all other event actions (opened, edited, synchronize, converted_to_draft, labeled, unlabeled, auto_merge_enabled, auto_merge_disabled) proceed through the existing transition-preflight path without change; update .github/workflows/state-gate.yml transition-preflight step to pass --event-path so the gate receives the event action at ready_for_review time",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/project_gate.py",
        ".github/workflows/state-gate.yml"
      ]
    },
    {
      "command_id": "issue367_r2v1.landing_authority_tests",
      "command": "extend tests/test_project_gate.py with CLI-level regressions for transition-preflight event-path parsing and landing authority enforcement; extend tests/test_control_plane_transition.py with unit-test coverage for engineering_pr_not_landing_authorized, landing_authority_required, landing_authority_mismatch, and the pass-through case for non-ready_for_review events; extend tests/platform_v1/test_merge_intent.py with intent-binding regressions proving G2 engineering PR blocks on ready_for_review, G3 stale inherited intent blocks, G4 current bound intent passes, G5 wrong PR blocks, G6 wrong base blocks, G7 wrong head blocks, G8 wrong Decision digest blocks, G9 wrong Command Plan digest blocks, G10 wrong workflow profile blocks, G11 missing/expired intent blocks, G12 drift blocks, G13 post-merge validation remains fail-closed, G14 historical PR347 schema-v3 remains valid, G15 #364 Path-A lifecycle remains green, G16 direct repeat of #365 sequence blocks before merge",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_project_gate.py",
        "tests/test_control_plane_transition.py",
        "tests/platform_v1/test_merge_intent.py"
      ]
    },
    {
      "command_id": "issue367_r2v1.validate_and_publish",
      "command": "run the focused test suites for project_gate, control_plane_transition, merge_intent, mainline_landing, path_a_gate, and ci_responsibility; run git diff --check; run transition-lint, transition-preflight, and worktree-publication-readiness; commit implementation; push exact branch and create one Draft PR to main",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "lint", "local_static_check", "commit", "push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_r2v1.post_publication_binding",
      "command": "after Draft PR creation obtains the actual GitHub PR number, archive the inherited PR347 active intent byte-for-byte to project_state/mainline_merge_intents/archive/pr347_v2.json, then bind project_state/mainline_merge_intents/active.json to the actual new PR number with the current Decision digest, Command Plan digest, locked base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf, workflow_profile=baseline, required workflows for baseline, allowed_merge_method=merge, and bounded expiry; run final local validation; perform the final normal branch push",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit", "push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true,
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr347_v2.json"
      ]
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
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/platform_v1/test_merge_intent.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr347_v2.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/mainline_landing.py",
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
    "tests/test_ci_responsibility.py",
    "tests/test_mainline_landing.py",
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
    "tests/test_mainline_landing.py",
    "tests/test_path_a_gate.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_ci_responsibility.py",
    "tests/test_execution_evidence.py",
    "tests/test_decision_preflight.py",
    "tests/test_trusted_command_runner.py"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete", "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_comment", "pull_request_close",
    "dependency_install", "browser_execution", "snapshot_update", "arbitrary_remote_browsing", "external_url_navigation", "offensive_security_or_network_attack_work",
    "second_decision_commit", "make_state_gate_push_pre_merge", "broad_dependency_change",
    "new_gate_family", "new_decision_artifact_family", "new_receipt_artifact_family",
    "modify_issue345_decision", "modify_issue360_branch_or_pr", "modify_issue363_branch_or_pr", "modify_issue364_decision",
    "revisit_issue283_protection", "revisit_github_ruleset",
    "mark_ready_pr360", "merge_pr360", "close_pr360", "rebase_pr360",
    "start_issue358", "start_issue363",
    "delete_or_rotate_inherited_active_intent"
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
    "github_pr_close_allowed": false,
    "publication_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "push exact branch and create one Draft PR after all validation suites pass",
      "push post-publication binding commit after Draft PR number obtained"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "reverse_agent/project_gate.py",
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/platform_v1/test_merge_intent.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr347_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE367_ENGINEERING_LANDING_BOUNDARY_R2_V1_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE367_BLOCKED_WITH_EXACT_EVIDENCE",
  "second_gate_family_forbidden": true
}
```

## Goal

Enforce a fail-closed boundary between engineering and landing authority for transition-mode R2 pull requests. When a PR is marked `ready_for_review`, the State Gate must distinguish between:

1. **ENGINEERING_DRAFT**: `mainline_merge_intent_required=false` — the Decision is engineering-only; `ready_for_review` must BLOCK with `engineering_pr_not_landing_authorized` because the Decision opted out of landing-intent binding.
2. **LANDING_CAPABLE_DRAFT**: `mainline_merge_intent_required=true` but the active mainline merge intent is inherited from a prior PR or otherwise does not bind the current PR/Decision/base — must BLOCK with `landing_authority_required` or `landing_authority_mismatch`.
3. **LANDING_READY**: `mainline_merge_intent_required=true` and the active intent exactly binds the current PR number, Decision ID/digest, Command Plan digest, locked base, workflow profile, and expiry — may proceed to the normal transition-preflight path.

The immediate incident (#365) was an engineering-only Decision (`mainline_merge_intent_required=false`) that reached Owner merge without a current active intent or attestation. The post-merge mainline-merge-validation correctly BLOCKED. The systemic gap: no pre-merge governance layer stopped the engineering-only Decision from becoming merge-eligible.

## Acceptance

1. `transition_preflight` accepts an optional `--event-path` argument and parses the GitHub event action.
2. When the event action is `ready_for_review` and `mainline_merge_intent_required=false`, the gate returns `BLOCKED` with `engineering_pr_not_landing_authorized` in `blocking_reasons`.
3. When the event action is `ready_for_review` and `mainline_merge_intent_required=true` but no valid active intent exists, the gate returns `BLOCKED` with `landing_authority_required`.
4. When the event action is `ready_for_review` and `mainline_merge_intent_required=true` and the active intent exists but does not match the current PR/Decision/base/profile, the gate returns `BLOCKED` with `landing_authority_mismatch`.
5. When the event action is `ready_for_review` and `mainline_merge_intent_required=true` and the active intent exactly matches, the gate proceeds through the normal transition-preflight path.
6. All non-`ready_for_review` event actions (`opened`, `edited`, `synchronize`, `converted_to_draft`, `labeled`, `unlabeled`, `auto_merge_enabled`, `auto_merge_disabled`) proceed through the existing transition-preflight path without change.
7. The `.github/workflows/state-gate.yml` `transition-preflight` step passes `--event-path "$GITHUB_EVENT_PATH"` so the gate receives the event action.
8. The post-merge mainline-merge-validation remains unchanged and fail-closed.
9. Historical PR347 schema-v3 intent binding behavior remains unchanged and valid.
10. #364 Path-A lifecycle (`ACTIVATION_DRAFT`, `IMPLEMENTATION_DRAFT`, `READY_FINAL_READINESS`) remains green.
11. A direct repeat of the #365 sequence (engineering-only Decision -> `ready_for_review` -> merge) now fails a server-visible required check BEFORE merge.
12. `project_state/decision_packet.md` is never edited after the Decision commit.
13. One Draft PR is created against `main`; it remains Draft. The post-publication binding commit archives the inherited PR347 intent and binds the new active intent to the actual PR number.
14. No mark-ready, merge, auto-merge, tag, release, or deploy occurs by the Agent.

## Execution policy

- Stage only the exact `allowed_mutated_paths`; never reset, clean, stash, restore, amend, rebase, squash, or force push.
- All validation is local and deterministic except for the bounded publication and post-publication binding network exceptions.
- Keep the PR Draft. Agent comment, ready, merge, tag, release, and deploy remain prohibited.
- Do not touch #358, #363, #364's Decision, desktop-app code, Connection product code, or any non-#367 governance surface.
- The inherited PR347 active intent is archived byte-for-byte before being replaced; it is never deleted or cleared.
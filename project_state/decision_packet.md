# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260825_issue364_path_a_lifecycle_coherence_r2_v1",
  "round_id": "round_20260825_issue364_path_a_lifecycle_coherence_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue345_scope_aware_workflow_policy_r2_v2",
  "follows_last_round_id": "round_20260824_issue345_scope_aware_workflow_policy_r2_v2",
  "previous_audit_outcome": "ISSUE345_R2V2_SCOPE_AWARE_WORKFLOW_PROFILE_POLICY_DRAFT_ACCEPTED_FOR_OWNER_LANDING",
  "workstream_id": "issue364-path-a-lifecycle-coherence-r2-v1",
  "source_issue": 364,
  "parent_issue": 353,
  "integration_base_ref": "main",
  "base_sha": "435907ad132dc1080b111ac6372c179e5cda429c",
  "activation_base_sha": "435907ad132dc1080b111ac6372c179e5cda429c",
  "starting_head": "435907ad132dc1080b111ac6372c179e5cda429c",
  "required_branch": "owner/issue353-path-a-lifecycle-coherence-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
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
    "verify exact main base 435907ad132dc1080b111ac6372c179e5cda429c and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue364_r2v1.bootstrap",
      "command": "verify locked base 435907ad132dc1080b111ac6372c179e5cda429c and fresh branch; commit Decision first; generate startup snapshot, command plan, transition lint, transition preflight, and worktree publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY",
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
      "command_id": "issue364_r2v1.lifecycle_stage_core",
      "command": "extend reverse_agent/control_plane/path_a.py with three stage-aware Path-A lifecycle outcomes (ACTIVATION_DRAFT, IMPLEMENTATION_DRAFT, READY_FINAL_READINESS): add DeltaObservation dataclass plus empty_delta flag, refactor changed_paths_for_event to return a DeltaObservation tuple, add a classify_stage helper, and restructure verify_path_a_r1 so ACTIVATION_DRAFT with a proven empty delta returns a PASS that explicitly carries implementation_authority=false and product_accepted=false without executing task checks; IMPLEMENTATION_DRAFT keeps all current path, risk, snapshot, digest, head/base/merge-base, auto-merge, and authority-revision checks; READY_FINAL_READINESS revalidates live Issue, r1-approved, approval transition, digest, snapshot, exact head/base, merge base, changed paths, risk classification, Allowed paths, and auto-merge on a freshly computed live authority revision and returns READY_FINAL_READINESS while still forbidding implementation authority; converted_to_draft events recompute the delta from live git truth rather than trusting the previous workflow stage",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/path_a.py"
      ]
    },
    {
      "command_id": "issue364_r2v1.lifecycle_regressions",
      "command": "extend tests/test_path_a_gate.py with focused stage-aware regressions covering A1 approved activation draft + zero delta -> ACTIVATION_DRAFT PASS; A2 activation draft approval/snapshot invalid -> BLOCK; A3 activation draft cannot count as completed implementation -> BLOCK; I1 valid implementation draft -> existing implementation PASS; I2 invalid implementation draft -> existing fail-closed behavior preserved; R1 Ready unchanged accepted exact implementation head -> READY_FINAL_READINESS PASS; R2 Ready head/base drift -> BLOCK; R3 Ready Issue digest/approval drift -> BLOCK; R4 Ready cannot bypass missing snapshot/approval -> BLOCK; D1 converted_to_draft + empty delta -> ACTIVATION_DRAFT; D2 converted_to_draft + implementation delta -> IMPLEMENTATION_DRAFT; L1 labeled/unlabeled/edited/synchronize re-evaluates live authority; M1 auto_merge_enabled BLOCK; plus an explicit ACTIVATION_DRAFT PASS != PRODUCT_ACCEPTED regression",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_path_a_gate.py"
      ]
    },
    {
      "command_id": "issue364_r2v1.validate_and_publish",
      "command": "run the Path-A gate focused suite, CI responsibility suite, project gate suite, and control-plane/planning-adapter suites; run git diff --check; run transition-lint and transition-preflight and worktree-publication-readiness; commit implementation; push exact branch and create one Draft PR to main",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "lint", "local_static_check", "commit", "push", "draft_pr", "network_access"],
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
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/decision_preflight.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
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
    ".github/workflows/**",
    ".codex-skills/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/github_adapter.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_ci.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/architecture/**",
    "reverse_agent/base_platform/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/worktree_state.py",
    "frontend/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "tests/platform_v1/**",
    "tests/base_platform/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_ci_responsibility.py",
    "tests/test_mainline_landing.py"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete", "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_comment", "pull_request_close",
    "dependency_install", "browser_execution", "snapshot_update", "arbitrary_remote_browsing", "external_url_navigation", "offensive_security_or_network_attack_work",
    "second_decision_commit", "make_state_gate_push_pre_merge", "modify_workflows_or_ci", "broad_dependency_change",
    "new_gate_family", "new_decision_artifact_family", "new_receipt_artifact_family",
    "modify_issue345_decision", "modify_issue360_branch_or_pr", "modify_issue363_branch_or_pr",
    "revisit_issue283_protection", "revisit_github_ruleset",
    "mark_ready_pr360", "merge_pr360", "close_pr360",
    "rebase_pr360"
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
      "push exact branch and create one Draft PR after all validation suites pass"
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
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE364_PATH_A_LIFECYCLE_R2_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE364_BLOCKED_WITH_EXACT_EVIDENCE",
  "activation_stage": "ACTIVATION_DRAFT",
  "implementation_stage": "IMPLEMENTATION_DRAFT",
  "ready_stage": "READY_FINAL_READINESS",
  "second_gate_family_forbidden": true
}
```

## Goal

Reconcile the Path-A State Gate ready-for-review semantics with the Path-A lifecycle so that a Draft PR can be created at activation (zero delta), can be validated during implementation (non-empty implementation delta), and can be revalidated at Ready (draft=false) without granting implementation authority. Parent defect #353 required that draft=false + READY_FINAL_READINESS not be conflated with PATH_A_R1_AUTHORIZED implementation-authority.

## Acceptance

1. This Decision is the unique immutable first commit from `main@435907ad132dc1080b111ac6372c179e5cda429c`; all later implementation descends from it.
2. `changed_paths_for_event` returns a `DeltaObservation` carrying `changed_paths`, `base_sha`, `head_sha`, and `empty_delta`; the legacy `(changed, base, head)` shape is preserved for internal callers.
3. `verify_path_a_r1` accepts a stage argument and dispatches to three mutually exclusive stage-validated paths:
   - `ACTIVATION_DRAFT`: PASS only when `changed_paths` is empty and the PR is open/draft with an approved r1-approved snapshot; result carries `implementation_authority=false`, `product_accepted=false`, `no_task_checks=true`, and `authority_revalidation_required=true`.
   - `IMPLEMENTATION_DRAFT`: keeps every current Path-A R1 check (labels, digest, approval, head/base/merge-base, auto-merge, Allowed paths, risk floor, changed_paths non-empty) and emits `PATH_A_R1_AUTHORIZED` with `implementation_authority=true`.
   - `READY_FINAL_READINESS`: revalidates live Issue, r1-approved, approval transition, digest, snapshot, exact head/base, merge base, changed paths (if any), risk classification, Allowed paths, and auto-merge against a freshly computed live authority revision; emits `READY_FINAL_READINESS` with `implementation_authority=false`, `product_accepted=false`, `no_task_checks=true`, `read_only_final_readiness=true`.
4. `converted_to_draft` events recompute the delta from live git truth and classify as `ACTIVATION_DRAFT` when the delta is empty and `IMPLEMENTATION_DRAFT` when the delta is non-empty; previous workflow stage is not trusted.
5. `authority_revision` always reflects current live PR state including `pr_draft_state`, so Draft->Ready mutation invalidates any prior expected authority revision; Ready never inherits a prior Draft digest.
6. A regression test proves `ACTIVATION_DRAFT PASS != PRODUCT_ACCEPTED` (i.e., an activation draft's PASS result cannot satisfy an implementation-completed predicate).
7. Existing fail-closed Path-A R1 behavior is preserved: any missing/invalid snapshot, approval removal/change, Issue body edit after approval, head/base/merge-base drift, risk-escalation path, unauthorized path, or auto-merge state blocks the gate in every stage except the corresponding activation-empty-Delta case.
8. No `.github/workflows/state-gate.yml` change is required: the workflow already triggers on `converted_to_draft`, `ready_for_review`, `labeled`, `unlabeled`, `synchronize`, `opened`, `edited`, `reopened`, `auto_merge_enabled`, `auto_merge_disabled`; the new stage-aware gate reuses the existing `path-a-r1` step.
9. `project_state/decision_packet.md` is never edited after the Decision commit; the transition-lint, transition-preflight, and worktree-publication-readiness gates all pass before implementation commits land.
10. `tests/test_path_a_gate.py` gains the mandatory regression matrix (A1/A2/A3, I1/I2, R1/R2/R3/R4, D1/D2, L1, M1, G1) and remains green together with `tests/test_ci_responsibility.py`, `tests/test_project_gate.py`, `tests/test_control_plane_transition.py`, and `tests/test_planning_and_github_adapters.py`.
11. #360 is untouched; #363 is untouched; #283 is not revisited.
12. One Draft PR is created against `main`; it remains Draft; no mark-ready, merge, auto-merge, tag, release, or deploy occurs.

## Execution policy

- Stage only the exact `allowed_mutated_paths`; never reset, clean, stash, restore, amend, rebase, squash, or force push.
- All validation is local and deterministic: no network access except the one bounded publication exception.
- Keep the PR Draft. Agent comment, ready, merge, tag, release, and deploy remain prohibited; owner landing follows independent audit under this Decision's bounded scope.
- Do not touch #360, #363, desktop-app code, Connection product code, or any non-#353/#364 governance surface.

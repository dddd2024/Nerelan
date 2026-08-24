# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue325_path_b_decision_immutability_r2_v4",
  "round_id": "round_20260824_issue325_path_b_decision_immutability_r2_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue330_trusted_remote_merge_boundary_r2_v3",
  "follows_last_round_id": "round_20260824_issue330_trusted_remote_merge_boundary_r2_v3",
  "previous_audit_outcome": "ISSUE325_R2_V3_BLOCKED_PLATFORM_V1_NONLANDING_INTENT_TEST_CONTRACT",
  "superseded_local_attempt_v3_decision_id": "decision_20260824_issue325_path_b_decision_immutability_r2_v3",
  "superseded_local_attempt_v3_round_id": "round_20260824_issue325_path_b_decision_immutability_r2_v3",
  "superseded_local_attempt_v3_commit": "470a5c18b0a420ef18adfb8b3fb525abb2e08442",
  "superseded_local_attempt_v3_failure": "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_exact_pr_not_issue_number",
  "superseded_local_attempt_v3_result": "1 failed/1156 passed/12 skipped/4 deselected",
  "superseded_local_attempt_decision_id": "decision_20260824_issue325_path_b_decision_immutability_r2_v2",
  "superseded_local_attempt_round_id": "round_20260824_issue325_path_b_decision_immutability_r2_v2",
  "superseded_local_attempt_commit": "55c602045c868f534696ee71ef6c23e274972a43",
  "superseded_local_attempt_failure": "PLATFORM_V1_ACTIVE_INTENT_DEFAULTED_TRUE_WITHOUT_EXPLICIT_OPT_OUT_7_FAILURES",
  "workstream_id": "issue325-path-b-decision-immutability-r2-v4",
  "source_issue": 325,
  "parent_issue": 321,
  "historical_predecessor_pr": 331,
  "historical_predecessor_head": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e",
  "historical_predecessor_base": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "historical_main_push_run": 32682663868,
  "historical_state_gate_push_run": 32682663872,
  "historical_v1_base_and_branch": "superseded and read-only; not an active authority",
  "integration_base_ref": "main",
  "base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "activation_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "starting_head": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "required_branch": "owner/issue325-path-b-decision-immutability-r2-v4",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "product_replay_commit_limit": 0,
  "implementation_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 1,
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
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_immutability_required": true,
  "retroactive_scope_expansion_allowed": false,
  "second_decision_commit_allowed": false,
  "decision_after_implementation_allowed": false,
  "stale_preflight_then_decision_change_allowed": false,
  "clean_decision_first_history_required": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base, branch, clean worktree, merge-base and no remote collision without mutating remote state",
    "create this immutable Decision as the unique first commit after the locked base before implementation or generated governance mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue325.bootstrap_gate_sequence",
      "command": "verify exact base, branch, clean worktree, merge-base and no remote collision; run startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre after Decision activation; require PRE_EXECUTION_AUTHORIZED with zero blockers",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
      "allowed_mutated_paths": []
    },
    {
      "command_id": "issue325.implementation_decision_immutability",
      "command": "freshly reimplement from the locked base without importing v2 or v3 dirty implementation or gate delta; extend the existing project_gate path only: enforce decision_content_immutable_after_activation=true with live git history and committed blob evidence in transition_preflight, transition_reconcile and worktree_publication_readiness; remove only the three DecisionImmutability CI deselections; add fail-closed regression tests; add only the adjacent-class skipif to tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_exact_pr_not_issue_number, preserving strict historical/landing behavior; create exactly one implementation commit",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "workflow_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["reverse_agent/project_gate.py", "tests/test_project_gate.py", "tests/test_control_plane_transition.py", ".github/workflows/ci.yml", "tests/test_ci_responsibility.py", "tests/platform_v1/test_contracts.py"]
    },
    {
      "command_id": "issue325.generated_governance_artifacts",
      "command": "generate only the five existing governance gate artifacts after implementation validation and create exactly one generated-governance commit; do not alter Decision, source, tests or workflows in this commit",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
      "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "issue325.local_validation_and_immutability_proof",
      "command": "run focused gate, transition, CI responsibility, platform merge-intent, Path-A and planning-adapter tests; run the exact Platform V1 blocking command after removing only the three DecisionImmutability deselections; run transition-lint, transition-preflight --mode pre, transition-reconcile when evidence exists, worktree-publication-readiness when preflight is current, and git diff --check; prove clean Decision-first history and all named negative cases fail closed",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "issue325.initial_push_and_draft_pr",
      "command": "after complete deterministic validation, perform exactly one normal fast-forward push of owner/issue325-path-b-decision-immutability-r2-v4, create exactly one Draft PR against main at 122f91ff451929f34cd71e918d88f1512d020d1d, observe exact-head CI State Gate and Decision Preflight checks read-only, then stop at independent audit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true,
      "allowed_mutated_paths": []
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_contracts.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": ["AGENTS.md", "reverse_agent/control_plane/models.py", "reverse_agent/control_plane/transition.py", "reverse_agent/mainline_landing.py", "tests/platform_v1/test_merge_intent.py", ".github/workflows/state-gate.yml", ".github/workflows/decision-preflight.yml", "tests/test_mainline_landing.py", "tests/test_path_a_gate.py", "tests/test_planning_and_github_adapters.py"],
  "generated_artifact_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": [
    "frontend/**", "docs/**", "reverse_agent/control_plane/models.py", "reverse_agent/control_plane/transition.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/mainline_landing.py", "reverse_agent/platform_v1/**", ".github/workflows/decision-preflight.yml", ".github/workflows/freshness.yml", ".github/workflows/model-access.yml", ".github/workflows/state-gate.yml", "project_state/schemas/**", "project_state/mainline_merge_intents/**", "project_state/mainline_recoveries/**", "project_state/rounds/**", "project_state/audits/**", "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements*.txt", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile*", "AGENTS.md"
  ],
  "forbidden_operations": ["direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite", "dependency_install", "live_model_call", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read", "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_close", "browser", "playwright", "offensive_security", "modify_pr327", "modify_pr329", "retroactive_authorization", "second_decision_commit", "decision_after_implementation", "import_or_copy_v2_dirty_worktree_delta", "import_or_copy_v3_dirty_worktree_delta"],
  "capability_policy": {
    "runner_dispatch_allowed": false, "model_api_invocation_allowed": false, "opencode_invocation_allowed": false, "live_provider_access_allowed": false, "credential_access_allowed": false, "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false, "destructive_operations_allowed": false, "dependency_install_allowed": false, "network_access_default_allowed": false, "direct_push_to_main_allowed": false, "merge_allowed": false, "mark_ready_allowed": false, "force_push_allowed": false, "rebase_during_execution_allowed": false, "tag_or_release_allowed": false, "deployment_allowed": false, "github_issue_comment_allowed": false, "github_issue_close_allowed": false, "github_pr_creation_allowed": true, "github_pr_close_allowed": false, "publication_allowed": true, "remote_observation_read_only_allowed": true,
    "local_network_exceptions": ["after complete deterministic validation, perform exactly one normal fast-forward push of owner/issue325-path-b-decision-immutability-r2-v4, create exactly one Draft PR against main at 122f91ff451929f34cd71e918d88f1512d020d1d, observe exact-head CI State Gate and Decision Preflight checks read-only, then stop at independent audit"],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [{"pattern": ".github/workflows/**", "minimum_risk": "R2"}, {"pattern": "**/secrets/**", "minimum_risk": "R3"}],
  "authorized_risk_paths": ["reverse_agent/project_gate.py", "tests/test_project_gate.py", "tests/test_control_plane_transition.py", ".github/workflows/ci.yml", "tests/test_ci_responsibility.py", "tests/platform_v1/test_contracts.py"],
  "authorized_risk_tier": "R2",
  "goal": "Make the existing project_gate machine-enforce immutable Path-B Decision content after activation while restoring only the three DecisionImmutability tests to the CI blocking gate.",
  "success_terminal": "ISSUE325_DECISION_IMMUTABILITY_R2_V4_DRAFT_PR_READY_FOR_INDEPENDENT_AUDIT",
  "blocked_terminal": "ISSUE325_DECISION_IMMUTABILITY_BLOCKED_WITH_EXACT_NAMED_EVIDENCE"
}
```

## Goal

Implement the smallest fail-closed extension of the existing `project_gate` path for Issue #325. Enforce `decision_content_immutable_after_activation=true` in transition preflight, transition reconcile and worktree publication readiness using live git history and committed blob evidence, restore only the three exact DecisionImmutability tests to the Platform V1 CI blocking command, and add only the adjacent-class skipif to the named V6 contract test. No second gate, schema, dependency, execution store, frontend, provider or model surface is allowed.

PR331 recovery is read-only historical evidence: candidate head `6d37e3ec7ca35da95c83b0bc03f1e6be2321950e` was based on `0beac2f57c1ae9caa1b11dc02dfc027c9b19e496`; main push run `32682663868` and State Gate push run `32682663872` are not current authority. The old v1 base/branch is historicalized and cannot authorize this round.

## Acceptance

1. HEAD, merge-base and locked base are all `122f91ff451929f34cd71e918d88f1512d020d1d`; branch is exact and clean before mutation.
2. This Decision is the unique first commit after the locked base, changes only its own file and remains byte-identical through final head.
3. Existing `project_gate` rechecks immutability in preflight, reconcile and publication readiness without a second gate or schema.
4. The check requires a true flag, valid starting head, exactly one Decision-modifying commit in `starting_head..HEAD`, ancestor and oldest-new-commit ordering, Decision-only activation scope, equal activation/HEAD blobs, and clean Decision worktree/index.
5. Missing/invalid flag or start head, missing/multiple commit, non-ancestor/late commit, scope drift, missing/changed blob, worktree/index dirtiness, retroactive scope expansion, second Decision commit, Decision-after-implementation and stale-preflight-then-Decision-change fail closed with named blockers.
6. CI removes only the three exact DecisionImmutability deselections; the four fake-provider deselections remain exact and unchanged.
7. Focused suites, `tests/platform_v1/test_merge_intent.py`, `tests/test_ci_responsibility.py`, Path-A/planning adapters, transition lint/preflight/reconcile/publication readiness and `git diff --check` pass before publication.
8. Exactly one implementation commit, one generated-governance commit, one normal fast-forward push and one Draft PR occur; no product commit, binding commit, rerun, dependency/model/provider/runner operation, comment, mark-ready or merge.
9. After exact-head CI, State Gate and Decision Preflight succeed, the Draft PR remains Draft and execution stops for independent audit.

## Execution policy

- This approved Decision is the sole Path-B authority; Issue #325 is context only.
- Use `apply_patch`; stage only exact allowed paths. Never reset, clean, stash, restore, amend, force push, rebase or rewrite history.
- Reuse existing `project_gate` and committed-blob helpers; referenced `models.py` and `transition.py` are read-only in this round.
- The implementation commit touches only the six source/test/CI paths, including the one adjacent test skipif; generated governance touches only the five gate artifacts.
- This v4 round must be freshly reimplemented from the locked base and must not inherit, copy, cherry-pick or apply any v2 or v3 worktree delta, including uncommitted dirty implementation or gate artifacts.
- Do not import, cherry-pick, copy or use authority from PR327 or PR329, and do not import or copy either failed v2 or v3 worktree delta. Do not access credentials, invoke models/providers, run browser/Playwright or perform offensive-security work.
- After the single push and Draft PR, observe exact-head checks read-only and stop at the independent audit boundary. Owner audit, mark-ready and merge are outside this round.

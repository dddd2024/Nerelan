# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260823_issue326_mainline_attestation_recovery_r2_v1",
  "round_id": "round_20260823_issue326_mainline_attestation_recovery_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "follows_last_round_id": "round_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "previous_audit_outcome": "ISSUE320_R2_V2_LANDING_PR324_MERGED_WITH_STATE_GATE_PUSH_FAILURE_32639335287_EXPOSED",
  "source_issue": 326,
  "validated_implementation_issue": 324,
  "validated_implementation_pr": 324,
  "validated_implementation_branch": "owner/issue320-state-gate-reachability-r2-v2-landing",
  "validated_implementation_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "state_gate_push_failure_run_id_observed": 32639335287,
  "state_gate_push_failure_observed": true,
  "non_retroactive_recovery": true,
  "workstream_id": "issue326-mainline-attestation-recovery-r2-v1",
  "required_branch": "owner/issue326-mainline-attestation-recovery-r2-v1",
  "starting_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "activation_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "integration_base_ref": "main",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "mark_ready_allowed": false,
  "merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "workflow_rerun_allowed": false,
  "rerun_state_gate_push_32639335287_allowed": false,
  "add_attestation_to_pr324_allowed": false,
  "rewrite_pr324_history_allowed": false,
  "modify_pr324_decision_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue326-mainline-attestation-recovery-r2-v1 from locked base 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 in an isolated detached worktree",
    "commit this immutable Decision as the unique first new commit after 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 before any generated governance artifact or semantic mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue326.bootstrap_and_gate",
      "command": "verify origin/main remains 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496; verify worktree merge-base equals base_sha; run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before any mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks", "generate_governance_artifact"],
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
      "command_id": "issue326.chronology_invariant_implementation",
      "command": "implement machine-verifiable attestation-chronology invariant: (1) github_remote_verifier.load_merge_attestation must surface _remote_comment_created_at from live GitHub remote comment.created_at (never trusting attestation self-declared timestamps); (2) mainline_landing._validate_attestation must add a new named check attestation_created_before_merge that rejects when _remote_comment_created_at >= merge_commit_author_date, using authoritative merge boundary derived from git log of the merge commit; (3) validate_future_merge and validate_historical_recovery must produce named blocking_reasons for late_attestation, missing_attestation, and attestation_not_before_merge rather than an undifferentiated BLOCKED",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/github_remote_verifier.py",
        "reverse_agent/mainline_landing.py",
        "reverse_agent/project_gate.py"
      ]
    },
    {
      "command_id": "issue326.schema_evolution",
      "command": "extend merge_approval_attestation_v2.schema.json with _remote_comment_created_at property (ISO-8601, remote-observed only); keep v1 four-run policy frozen and untouched",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/schemas/merge_approval_attestation_v2.schema.json"
      ]
    },
    {
      "command_id": "issue326.test_suite",
      "command": "add regression tests for: (A) merge-without-attestation-then-late-attestation-rerun -> BLOCKED with reason 'attestation_created_not_before_merge' or 'late_attestation'; (B) comment.created_at >= merge boundary -> BLOCKED; (C) missing attestation -> named blocking_reason; (D) preserve all existing fail-closed checks (wrong PR/head/base/method/intent-digest/workflow-event/workflow-SHA/failed-workflow/wrong-author/wrong-body-digest); (E) positive case: valid schema-v2 intent + three pre-merge workflows + Owner attestation created strictly BEFORE merge -> PASSED",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_test_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_mainline_landing.py",
        "tests/test_ci_responsibility.py",
        "tests/platform_v1/test_merge_intent.py",
        "tests/platform_v1/test_contracts.py"
      ]
    },
    {
      "command_id": "issue326.non_retroactive_recovery_record",
      "command": "create project_state/mainline_recoveries/pr324.json as a non-retroactive FAILURE recovery record: records source_pr=324, state_gate_push_run_id=32639335287 with conclusion=failure, semantic_tree_landed=true, authority_lifecycle_failed=true because required pre-merge attestation was absent, non_retroactive=true; never asserts 32639335287 success; never redefines PR324 as historically authorized",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_recoveries/pr324.json"
      ]
    },
    {
      "command_id": "issue326.mainline_intent_rebind",
      "command": "archive current active mainline merge intent byte-for-byte to archive/pr324_v2.json; replace active.json with new schema-v2 intent binding issue326 PR number, locked base, allowed merge method, immutable issue326 Decision digest, generated Command Plan digest, required workflows (CI, Decision Preflight, State Gate pull_request), chronology_invariant_required=true, bounded expiry; one governance-only binding commit",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr324_v2.json"
      ]
    },
    {
      "command_id": "issue326.final_prepublication_validation",
      "command": "run python -m pytest tests/test_mainline_landing.py -q; python -m pytest tests/test_ci_responsibility.py -q; python -m pytest tests/test_project_gate.py -q; python -m pytest tests/test_control_plane_transition.py -q; python -m pytest tests/test_planning_and_github_adapters.py -q; python -m pytest tests/platform_v1/test_merge_intent.py tests/platform_v1/test_contracts.py -q; python -m reverse_agent.project_gate transition-lint --state-dir project_state; python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre; python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state; git diff --check; prove Decision commit is first after 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496, touches only project_state/decision_packet.md, and its blob is unchanged between activation and final HEAD; prove late-attestation negative case fails for chronology reason",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue326.initial_push_and_pr",
      "command": "normal push owner/issue326-mainline-attestation-recovery-r2-v1 once; create exactly one Draft PR with base=main; observe actual PR number; do not mark-ready; do not merge; do not create Owner attestation; do not rerun workflows",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue326.intent_binding_push",
      "command": "normal fast-forward push binding commit as second and final push; observe final exact head CI, State Gate, and Decision Preflight; STOP at DRAFT_PR_READY_FOR_EXACT_HEAD_OWNER_AUDIT",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "repository_observation", "network_access"],
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
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json",
    "project_state/mainline_recoveries/pr324.json",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
    "AGENTS.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/mainline_recoveries/pr60.json",
    "requirements*.txt",
    "pyproject.toml",
    "frontend/**",
    "docs/**",
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "dependency_install",
    "live_model_call",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "runner_dispatch",
    "history_rewrite",
    "archive_historical_intent_mutation",
    "pr_body_mutation_before_acceptance",
    "rerun_state_gate_push_32639335287",
    "add_attestation_to_pr324",
    "rewrite_pr324_history",
    "modify_pr324_decision",
    "workflow_rerun",
    "owner_attestation_creation",
    "mark_ready",
    "merge",
    "issue_comment_on_pr324"
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
    "local_network_exceptions": [
      "normal push owner/issue326-mainline-attestation-recovery-r2-v1 once for initial publication",
      "create exactly one Draft PR with base=main",
      "observe fresh exact-head CI, State Gate pull_request, and Decision Preflight runs without rerun or runner dispatch",
      "normal fast-forward push binding commit as second and final push",
      "observe final exact-head CI, State Gate pull_request, and Decision Preflight runs"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "github_mark_ready_allowed": false,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json",
    "project_state/mainline_recoveries/pr324.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE326_NON_RETROACTIVE_MAINLINE_ATTESTATION_RECOVERY_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "HARD_STOP_ISSUE326"
}
```

## Goal

Non-retroactively recover the mainline attestation lifecycle failure exposed by #324, and machine-block the "merge then add attestation then rerun validation to whitewash history" attack vector. Specifically: (1) machine-prove that any accepted attestation's trusted GitHub `comment.created_at` strictly precedes the authoritative merge boundary, using remote-observed GitHub metadata rather than self-declared attestation timestamps; (2) preserve the historical record that PR #324's State Gate push run 32639335287 concluded FAILURE without ever rewriting it as SUCCESS; (3) represent #324 as a non-retroactive FAILURE recovery so that its successor (issue326) does not redefine #324 as historically authorized.

## Acceptance

1. `origin/main` remains locked at `0beac2f57c1ae9caa1b11dc02dfc027c9b19e496`. The issue326 Decision commit is the unique first new commit after this base, touches only `project_state/decision_packet.md`, and its blob is unchanged between activation and final HEAD.
2. `github_remote_verifier.load_merge_attestation` surfaces `_remote_comment_created_at` from the live GitHub Issues-Comments API response for the attestation-carrying comment. `_validate_attestation` rejects any attestation where `_remote_comment_created_at >= merge_commit.author_date` (the authoritative merge boundary), via a new named check `attestation_created_before_merge` producing a distinct `blocking_reason`.
3. Regression A: valid intent + exact three pre-merge workflows + merge WITHOUT attestation + add otherwise-valid attestation AFTER merge + rerun validation => BLOCKED with reason explicitly indicating late/retroactive attestation chronology, not a fixture error.
4. Regression B: trusted remote `comment.created_at >=` authoritative merge boundary => BLOCKED with reason `attestation_created_not_before_merge`.
5. Regression C: missing attestation => named `blocking_reason` (not a generic BLOCKED).
6. Regression D: all existing fail-closed behaviors (wrong PR / wrong head / wrong base / wrong merge method / wrong intent digest / wrong workflow event / wrong workflow SHA / failed workflow / wrong comment author / wrong body digest) remain enforced and are not weakened.
7. Positive: valid schema-v2 intent + exact three pre-merge workflow runs + Owner structured attestation with `comment.created_at` strictly before the merge + correct two-parent merge/tree => PASSED.
8. The v1 historical/frozen four-run policy (`CI`, `Decision Preflight`, `State Gate (pull_request)`, `State Gate (push)`) is preserved byte-for-byte in archived v1 intents and unchanged in the v1 path of `_validate_intent` / `_validate_attestation`.
9. `project_state/mainline_recoveries/pr324.json` exists and faithfully records `source_pr=324`, `state_gate_push_run_id=32639335287`, `state_gate_push_conclusion=failure`, `semantic_tree_landed=true`, `authority_lifecycle_failed=true`, `non_retroactive=true`. It does NOT claim 32639335287 succeeded and does NOT redefine #324 as historically authorized.
10. The State Gate push run `32639335287` is NEVER rerun. No attestation is added to PR #324. No #324 Decision is modified. No #324 history is rewritten.
11. `merge_allowed=false`, `mark_ready_allowed=false`, `direct_push_to_main_allowed=false`, `force_push_allowed=false`, `rebase_during_execution_allowed=false`. Agent does not create Owner attestation, mark-ready, merge, auto-merge, direct-push main, force-push, rebase, squash/reset, rerun workflow, invoke provider/model, scrape credentials, dispatch runner, tag, or release.
12. Issue #325 is not executed; its worktree is left untouched. Issues #301, #295, #297, #304, #283 are not touched.
13. All required tests pass locally (`test_mainline_landing`, `test_ci_responsibility`, `test_project_gate`, `test_control_plane_transition`, `test_planning_and_github_adapters`, `test_merge_intent`, `test_contracts`); `transition-lint`, `transition-preflight --mode pre`, `worktree-publication-readiness`, and `git diff --check` all PASS.
14. Exactly one Draft PR is created against `main`. Final exact head has CI, State Gate, and Decision Preflight observed. Execution stops at `DRAFT_PR_READY_FOR_EXACT_HEAD_OWNER_AUDIT`.

## Execution policy

- Issue #324 remains a frozen FAILURE observation. Never mutate #324 state, add attestation to #324, rerun the State Gate push 32639335287, modify the #324 Decision, or rewrite #324 history.
- Treat `32639335287 = FAILURE` as negative evidence preserved in perpetuity.
- The attestation-chronology invariant is the sole new source-level invariant added; extend existing `GitHubRemoteAcceptanceVerifier`, `mainline_landing`, and `mainline-merge-validation` rather than creating a second governance gate.
- Use exactly one Draft PR and exactly two normal pushes (initial push + binding push). No mark-ready, merge, issue close, PR close, or post-merge mutation is performed by the Agent.
- Preserve unrelated worktree content in the parent F:\reverse-agent worktree; do not use reset, clean, stash, restore, deletion, force push, or history rewrite.

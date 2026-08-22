# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260822_issue285_home_goal_truth_r2_v2_landing",
  "round_id": "round_20260822_issue285_home_goal_truth_r2_v2_landing",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "follows_last_round_id": "round_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "previous_audit_outcome": "V1_PREPUBLICATION_REWORK_REQUIRED_HEAD_84995E46310874B2AA98955AD3378A6ACEAE8336_PLATFORM_V1_1107_PASSED_1_SKIPPED_11_DESELECTED_ONLY_MAINLINE_ACTIVE_INTENT_PREBIND_SCHEMA_V2_ASSERTION_FAILED_ZERO_PUSH_ZERO_PR",
  "rejected_landing_decision_id": "decision_20260822_issue285_home_goal_truth_r2_v1_landing",
  "rejected_landing_round_id": "round_20260822_issue285_home_goal_truth_r2_v1_landing",
  "rejected_landing_head": "84995e46310874b2aa98955ad3378a6aceae8336",
  "rejected_landing_blocked_test": "tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority",
  "rejected_landing_normal_push_count": 0,
  "rejected_landing_pr_creation_count": 0,
  "workstream_id": "issue285-home-goal-truth-r2-v2-landing",
  "source_issue": 285,
  "validated_product_pr": 286,
  "validated_product_head": "8310a25ae3c2e88e21207434e7d3647a971f8b0f",
  "validated_product_tree": "95b93ad9455a015d41a58b285d5232d7e430ebb0",
  "validated_product_audit_review_id": 4998754580,
  "validated_product_audit_time": "2026-08-22T02:59:19Z",
  "validated_ci_run_id": 32547032914,
  "validated_model_access_run_id": 32547032884,
  "validated_issue_digest": "c40d700ce3a4ebb1a902a8a7207ef4c36ae8eeb0b89f3d5713bca905db5d4e66",
  "required_branch": "owner/issue285-home-goal-truth-r2-v2-landing",
  "starting_head": "8310a25ae3c2e88e21207434e7d3647a971f8b0f",
  "activation_base_sha": "ecacfd94e5140151a97fb1d3d486cd992769271b",
  "integration_base_ref": "main",
  "base_sha": "ecacfd94e5140151a97fb1d3d486cd992769271b",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "pre_pr_intent_assertions_deferred": [
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_id",
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_locked_base_sha",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_id",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_locked_base_sha",
    "tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority"
  ],
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 2,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "original_pr_close_attempt_limit": 1,
  "superseded_pr_comment_create_limit": 1,
  "attestation_comment_create_limit": 1,
  "attestation_comment_update_limit": 2,
  "mark_ready_attempt_limit": 1,
  "convert_to_draft_rollback_limit": 1,
  "merge_attempt_limit": 1,
  "issue_close_attempt_limit": 1,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "runner_dispatch_limit": 0,
  "tag_or_release_limit": 0,
  "deployment_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_close_allowed": true,
  "pr_close_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue285-home-goal-truth-r2-v2-landing from accepted product head 8310a25ae3c2e88e21207434e7d3647a971f8b0f in an isolated canonical-LF checkout whose merge-base with main is ecacfd94e5140151a97fb1d3d486cd992769271b",
    "commit this immutable Decision as the unique first new commit after 8310a25ae3c2e88e21207434e7d3647a971f8b0f before any generated governance artifact publication intent mutation mark-ready or merge",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue285landing.verify_candidate_and_remote",
      "command": "verify origin/main remains ecacfd94e5140151a97fb1d3d486cd992769271b; verify Issue 285 remains approved with normalized body digest c40d700ce3a4ebb1a902a8a7207ef4c36ae8eeb0b89f3d5713bca905db5d4e66; verify PR 286 remains Draft at head 8310a25ae3c2e88e21207434e7d3647a971f8b0f and base ecacfd94e5140151a97fb1d3d486cd992769271b with accepted review 4998754580, CI run 32547032914, Model Access run 32547032884, zero unresolved review threads and no head or base drift; verify the remote landing branch ref refs/heads/owner/issue285-home-goal-truth-r2-v2-landing does not yet exist and no GitHub landing PR exists for that head branch",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue285landing.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before publication or merge-intent mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
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
      "command_id": "issue285landing.prepublication_validation",
      "command": "before the landing PR number exists prove the eight product blobs equal accepted PR 286 head 8310a25ae3c2e88e21207434e7d3647a971f8b0f; prove origin/main and merge-base remain ecacfd94e5140151a97fb1d3d486cd992769271b and 8310a25ae3c2e88e21207434e7d3647a971f8b0f is an ancestor of HEAD; run focused Home Goal tests, the Platform V1 blocking gate with only its ordinary deselections plus exactly the five declared pre-PR intent-binding deferrals, and run mainline landing and merge-intent tests with the additional exact deselection tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority; run CI responsibility, frontend tests typecheck lint production and mock builds, transition lint and preflight, publication readiness and git diff --check; accept no product mutation or other failure",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue285landing.publish_initial_draft",
      "command": "after prepublication validation passes push owner/issue285-home-goal-truth-r2-v2-landing once and create exactly one Draft PR with base main; read the actual GitHub-assigned PR number without guessing; transient checks against inherited PR 277 active intent are not acceptance evidence",
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
      "command_id": "issue285landing.bind_actual_pr",
      "command": "using only the observed GitHub-assigned Draft PR number copy the committed schema-v2 PR 277 active intent byte-for-byte to project_state/mainline_merge_intents/archive/pr277_v2.json and replace active.json with schema version 2 bound to the actual landing PR, locked base ecacfd94e5140151a97fb1d3d486cd992769271b, this immutable Decision raw digest, the committed Command Plan raw digest, merge method merge, exact workflows CI Decision Preflight and State Gate pull_request, and expiry 2026-08-24T23:59:59Z; commit exactly once without editing the Decision or product paths",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr277_v2.json"
      ]
    },
    {
      "command_id": "issue285landing.final_bound_validation",
      "command": "on the final PR-bound head prove the archived PR 277 bytes, schema-v2 active intent fields and raw Decision and Command Plan digests are exact; prove all eight validated product blobs remain identical and 8310a25ae3c2e88e21207434e7d3647a971f8b0f through HEAD changes only the eight allowed governance paths; run the focused Home Goal tests, exact Platform V1 blocking gate with only its ordinary deselections and all five formerly deferred assertions enabled, mainline landing and merge-intent tests, CI responsibility, frontend tests typecheck lint production and mock builds, transition lint and preflight, publication readiness and git diff --check; any failure stops publication",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue285landing.publish_bound_head",
      "command": "after full bound validation push the single post-publication binding commit as the second and final normal push; verify the remote branch equals the local final head; observe fresh exact-final-head CI, Decision Preflight, State Gate pull_request and Model Access runs without rerun or runner dispatch",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "push", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue285landing.audit_attest_and_land",
      "command": "after fresh exact-final-head CI Decision Preflight State Gate pull_request and Model Access runs succeed obtain an independent clean detached exact-head ACCEPTED audit for the landing PR; reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; create one non-active placeholder comment, observe its numeric ID and PATCH that same comment into the unique active schema-v2 MAINLINE_MERGE_APPROVAL_ATTESTATION bound to its own ID, exact three pre-merge workflow run IDs, canonical intent digest, exact accepted head and locked base; immediately reobserve no drift and then owner-controlled mark-ready once and merge once with method merge and expected-head protection; if merge is blocked after mark-ready and before merge success use the reserved second attestation update to remove the active marker and convert the same landing PR back to Draft at most once; do not retry merge in this Decision",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "convert_to_draft", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue285landing.post_merge_verify_and_close",
      "command": "verify the landing PR is merged; verify merge commit M has exactly parents ecacfd94e5140151a97fb1d3d486cd992769271b and the accepted landing head, tree M equals the accepted landing tree and origin/main equals M; require exact-M CI push, State Gate push and Model Access push SUCCESS and mainline-merge-validation PASSED; only then comment that PR 286 is superseded, close PR 286 and close Issue 285 completed; if post-merge evidence fails leave Issue 285 open and require a new bounded recovery Decision without revert force push reset or history rewrite",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "pull_request_close", "issue_close", "network_access"],
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr277_v2.json"
  ],
  "reference_paths": [
    "frontend/src/hooks/use-platform.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/routes/home.tsx",
    "frontend/tests/platform-home.test.tsx",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_task_service.py",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
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
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "product_mutation",
    "source_edit",
    "test_edit",
    "documentation_edit",
    "workflow_change",
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "dependency_install",
    "live_model_call",
    "model_api_invocation",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work"
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
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "verify origin/main remains ecacfd94e5140151a97fb1d3d486cd992769271b; verify Issue 285 remains approved with normalized body digest c40d700ce3a4ebb1a902a8a7207ef4c36ae8eeb0b89f3d5713bca905db5d4e66; verify PR 286 remains Draft at head 8310a25ae3c2e88e21207434e7d3647a971f8b0f and base ecacfd94e5140151a97fb1d3d486cd992769271b with accepted review 4998754580, CI run 32547032914, Model Access run 32547032884, zero unresolved review threads and no head or base drift; verify the remote landing branch ref refs/heads/owner/issue285-home-goal-truth-r2-v2-landing does not yet exist and no GitHub landing PR exists for that head branch",
      "after prepublication validation passes push owner/issue285-home-goal-truth-r2-v2-landing once and create exactly one Draft PR with base main; read the actual GitHub-assigned PR number without guessing; transient checks against inherited PR 277 active intent are not acceptance evidence",
      "after full bound validation push the single post-publication binding commit as the second and final normal push; verify the remote branch equals the local final head; observe fresh exact-final-head CI, Decision Preflight, State Gate pull_request and Model Access runs without rerun or runner dispatch",
      "after fresh exact-final-head CI Decision Preflight State Gate pull_request and Model Access runs succeed obtain an independent clean detached exact-head ACCEPTED audit for the landing PR; reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; create one non-active placeholder comment, observe its numeric ID and PATCH that same comment into the unique active schema-v2 MAINLINE_MERGE_APPROVAL_ATTESTATION bound to its own ID, exact three pre-merge workflow run IDs, canonical intent digest, exact accepted head and locked base; immediately reobserve no drift and then owner-controlled mark-ready once and merge once with method merge and expected-head protection; if merge is blocked after mark-ready and before merge success use the reserved second attestation update to remove the active marker and convert the same landing PR back to Draft at most once; do not retry merge in this Decision",
      "verify the landing PR is merged; verify merge commit M has exactly parents ecacfd94e5140151a97fb1d3d486cd992769271b and the accepted landing head, tree M equals the accepted landing tree and origin/main equals M; require exact-M CI push, State Gate push and Model Access push SUCCESS and mainline-merge-validation PASSED; only then comment that PR 286 is superseded, close PR 286 and close Issue 285 completed; if post-merge evidence fails leave Issue 285 open and require a new bounded recovery Decision without revert force push reset or history rewrite"
    ],
    "ci_network_exceptions": ["provider-free fake HTTP and SSE fixtures bound only to 127.0.0.1"],
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": true,
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE285_HOME_GOAL_TRUTH_R2_V2_LANDING_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE285_HOME_GOAL_TRUTH_R2_V2_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the already validated Issue #285 Home and authoritative Goal-truth product tree through one governance-only Path-B candidate whose immutable Decision, generated Command Plan, actual-PR schema-v2 merge intent, exact product objects, independent audit, owner attestation, expected-head merge, and post-merge evidence remain valid on merged `main`.

## Acceptance

1. This Decision is the unique first new commit after accepted product head `8310a25ae3c2e88e21207434e7d3647a971f8b0f`; the branch merge-base and locked integration base remain exact `main@ecacfd94e5140151a97fb1d3d486cd992769271b`.
2. PR #286, review `4998754580`, exact product tree `95b93ad9455a015d41a58b285d5232d7e430ebb0`, CI run `32547032914`, Model Access run `32547032884`, and normalized Issue #285 digest `c40d700ce3a4ebb1a902a8a7207ef4c36ae8eeb0b89f3d5713bca905db5d4e66` remain immutable candidate evidence.
3. The eight referenced product and test blobs remain byte-identical to PR #286. No product, source, test, documentation, workflow, dependency, credential, provider, model, OpenCode, binary, or attack-related mutation occurs.
4. The gate sequence produces only the five authorized artifacts and returns `PRE_EXECUTION_AUTHORIZED` before publication or merge-intent mutation. The Decision is never edited after its activation commit.
5. Before the landing PR number exists, only the five exact declared active-intent binding assertions may be additionally deselected. After actual PR binding, all five pass and no other failure is accepted.
6. The actual GitHub-assigned landing PR number is observed after the initial Draft publication. The committed PR #277 schema-v2 intent is archived byte-for-byte, and final `active.json` binds the actual landing PR, locked base, raw Decision and Command Plan digests, merge method `merge`, exact three pre-merge workflows, equal-tree policy, and bounded expiry.
7. The final bound head passes focused Home and Goal tests, the exact Platform V1 blocking gate, mainline landing and merge-intent tests, CI responsibility, frontend tests/typecheck/lint/builds, transition gates, publication readiness, blob equality, path checks, and `git diff --check` with zero live provider calls.
8. Fresh final-head CI, Decision Preflight, State Gate pull_request, and Model Access runs are SUCCESS. A separate clean detached reviewer accepts the exact final head and records zero blockers and zero unresolved review threads.
9. Owner `dddd2024` publishes one self-bound schema-v2 merge attestation, immediately proves no base/head/check/audit/thread/mergeability drift, then performs at most one mark-ready and one expected-head merge using merge method `merge`; auto-merge, squash, rebase, direct-main push, force push, and history rewrite remain forbidden.
10. Post-merge verification proves merge parents `[ecacfd94e5140151a97fb1d3d486cd992769271b, H_land]`, tree equality with `H_land`, `origin/main == M`, exact-M CI/State Gate/Model Access push success, and `mainline-merge-validation == PASSED` before PR #286 and Issue #285 close. A post-merge failure leaves Issue #285 open for a new bounded recovery Decision and never authorizes revert or history rewrite.

## Execution policy

- Preserve V1 landing head `84995e46310874b2aa98955ad3378a6aceae8336` as immutable negative evidence with zero push and zero PR; do not reuse or publish its branch.
- Treat PR #286 and its exact-head acceptance as immutable product evidence; never edit its branch, head, or body during this landing.
- TaskStore remains the sole product execution truth. This landing adds no second authority store, task store, budget database, scheduler, queue, executor mode, or plugin manager.
- Bind the schema-v2 merge intent only after observing the new Draft landing PR number; never substitute Issue #285 or PR #286 for that number.
- Keep this Decision byte-identical after activation and preserve `project_state/mainline_merge_intents/archive/pr277_v2.json` byte-for-byte.
- If merge is blocked after mark-ready, revoke the active attestation with the one reserved update and convert the PR back to Draft at most once. Do not retry merge in this Decision.
- Stop on any base, head, branch, digest, path, product blob, audit, workflow, thread, mergeability, expiry, or attestation mismatch. Preserve unrelated worktree content and do not use reset, clean, stash, restore, deletion, force push, or history rewrite.

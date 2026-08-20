# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260820_issue268_product_ux2a_usage_budgets_r2_v5_landing",
  "round_id": "round_20260820_issue268_product_ux2a_usage_budgets_r2_v5_landing",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue259_state_gate_attestation_lifecycle_r2_v3",
  "follows_last_round_id": "round_20260819_issue259_state_gate_attestation_lifecycle_r2_v3",
  "previous_audit_outcome": "ISSUE268_V4_LANDING_BLOCKED_PREBINDING_PLATFORM_GATE_INCOMPATIBLE_WITH_SCHEMA_V2_ACTIVE_INTENT",
  "superseded_local_landing_decision_id": "decision_20260820_issue268_product_ux2a_usage_budgets_r2_v4_landing",
  "superseded_local_landing_round_id": "round_20260820_issue268_product_ux2a_usage_budgets_r2_v4_landing",
  "superseded_local_landing_branch": "owner/issue268-product-ux2a-usage-budgets-r2-v4-landing",
  "superseded_local_landing_decision_commit": "8a099adf03cc42f5ae4acc279fa924dde08b2b3d",
  "superseded_local_landing_published": false,
  "workstream_id": "issue268-product-ux2a-usage-budgets-r2-v5-landing",
  "source_issue": 268,
  "accepted_product_pr": 270,
  "accepted_product_head": "7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040",
  "accepted_product_tree": "99dbc76681ea00547a5166fbebc095743e7db700",
  "accepted_audit_comment_id": 5356762115,
  "accepted_ci_run_id": 32375246606,
  "accepted_decision_preflight_run_id": 32375246626,
  "accepted_state_gate_run_id": 32375246840,
  "superseded_implementation_pr": 269,
  "required_branch": "owner/issue268-product-ux2a-usage-budgets-r2-v5-landing",
  "starting_head": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "activation_base_sha": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "integration_base_ref": "main",
  "base_sha": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_close_allowed": true,
  "pr_close_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue268-product-ux2a-usage-budgets-r2-v5-landing from exact main aa5972a2c216a775089fbb52a5efa160f4884eb8 in an isolated canonical-LF checkout",
    "commit this immutable landing Decision as the first new commit after aa5972a2c216a775089fbb52a5efa160f4884eb8 before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue268v5landing.verify_accepted_product",
      "command": "verify origin/main remains aa5972a2c216a775089fbb52a5efa160f4884eb8; verify PR 270 remains Draft at accepted head 7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040 and base aa5972a2c216a775089fbb52a5efa160f4884eb8; verify exact-head CI, Decision Preflight and State Gate run IDs 32375246606, 32375246626 and 32375246840 are SUCCESS; verify accepted audit comment 5356762115 and zero unresolved review threads; verify the landing target branch and Draft PR do not yet exist",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue268v5landing.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before product or merge-intent mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v5landing.replay_accepted_product",
      "command": "git cherry-pick c5f30ee6b8869160c89e937eaee233415b01aaf6 7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040; prove all 15 product/test/frontend path objects equal accepted PR 270 and make no source edit",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit_replay", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue268v5landing.prepublication_validation",
      "command": "before the landing PR number exists run only the Issue 268 focused backend set, frontend Agent Runs test, frontend typecheck, frontend mock build, transition-lint, transition-preflight --mode pre, and git diff --check; prove accepted product object identity; defer the exact Platform V1 blocking gate and all active-intent binding tests until after the actual Draft PR number is committed",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v5landing.publish_initial_draft",
      "command": "push owner/issue268-product-ux2a-usage-budgets-r2-v5-landing once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing; transient checks against the inherited PR 264 active intent are not acceptance evidence",
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
      "command_id": "issue268v5landing.bind_actual_pr",
      "command": "using only the observed GitHub-assigned Draft PR number, copy the committed schema-v2 PR 264 active intent byte-for-byte to project_state/mainline_merge_intents/archive/pr264_v2.json and replace active.json with schema version 2 bound to the actual landing PR, locked base, this immutable Decision, committed Command Plan, merge method merge, exact three pre-merge workflows and a bounded future expiry; commit exactly once without editing the Decision",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v5landing.final_bound_validation",
      "command": "on the final PR-bound head prove all 15 accepted product objects remain identical; prove archived PR 264 bytes and schema-v2 active intent fields/digests; run focused backend, exact Platform V1 blocking gate, mainline landing and merge-intent tests, CI responsibility, transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; any failure stops publication",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v5landing.publish_bound_head",
      "command": "push the single post-publication binding commit once; verify remote branch equals local final head; close PR 270 as superseded by the landing PR; observe fresh exact-final-head CI, Decision Preflight and State Gate pull_request runs without rerun",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_close", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue268v5landing.attest_and_land",
      "command": "after fresh exact-final-head workflows succeed, perform a clean-worktree exact-head audit and record ACCEPTED; immediately reobserve base/head/checks/MERGEABLE/CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation comment bound to the actual comment ID, exact three workflow run IDs, intent digest, head and base; then owner-controlled mark-ready and merge exactly once with merge method merge and expected-head protection",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue268v5landing.post_merge_verify",
      "command": "verify the landing PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 268 completed only after all post-merge evidence is green",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "issue_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_service.py",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/runs.test.tsx",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr264_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
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
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/decision_preflight.py",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/pnpm-lock.yaml",
    "frontend/yarn.lock",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
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
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "history_rewrite",
    "source_edit",
    "raw_event_persistence",
    "secret_redaction_weakening",
    "second_taskstore_or_budget_database"
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
      "verify origin/main remains aa5972a2c216a775089fbb52a5efa160f4884eb8; verify PR 270 remains Draft at accepted head 7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040 and base aa5972a2c216a775089fbb52a5efa160f4884eb8; verify exact-head CI, Decision Preflight and State Gate run IDs 32375246606, 32375246626 and 32375246840 are SUCCESS; verify accepted audit comment 5356762115 and zero unresolved review threads; verify the landing target branch and Draft PR do not yet exist",
      "push owner/issue268-product-ux2a-usage-budgets-r2-v5-landing once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing; transient checks against the inherited PR 264 active intent are not acceptance evidence",
      "push the single post-publication binding commit once; verify remote branch equals local final head; close PR 270 as superseded by the landing PR; observe fresh exact-final-head CI, Decision Preflight and State Gate pull_request runs without rerun",
      "after fresh exact-final-head workflows succeed, perform a clean-worktree exact-head audit and record ACCEPTED; immediately reobserve base/head/checks/MERGEABLE/CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation comment bound to the actual comment ID, exact three workflow run IDs, intent digest, head and base; then owner-controlled mark-ready and merge exactly once with merge method merge and expected-head protection",
      "verify the landing PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 268 completed only after all post-merge evidence is green"
    ],
    "ci_network_exceptions": [],
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
  "success_terminal": "ISSUE268_PRODUCT_UX2A_USAGE_BUDGETS_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE268_PRODUCT_UX2A_R2_V5_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the independently accepted Issue #268 PRODUCT-UX-2A product through a self-contained Path-B candidate whose immutable Decision, generated Command Plan, schema-v2 active merge intent, exact product objects, owner approval attestation and post-merge evidence remain valid on merged `main`.

## Acceptance

1. This owner landing Decision is the first new commit after exact `main@aa5972a2c216a775089fbb52a5efa160f4884eb8`; no mutation or publication occurs before a generated Command Plan and `PRE_EXECUTION_AUTHORIZED` preflight.
2. The 15 accepted product/test/frontend path objects exactly equal PR #270 head `7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040`; there is no source edit, dependency, workflow, package, lockfile, secret, provider, model, OpenCode or second-store change.
3. The actual GitHub-assigned landing PR number is observed after the first Draft publication. The committed PR #264 schema-v2 active intent is archived byte-for-byte, and the final schema-v2 `active.json` binds the actual landing PR, exact base, this Decision digest, committed Command Plan digest, merge method `merge`, exact three pre-merge workflows and a live expiry.
4. The final bound head passes focused backend, exact Platform V1 blocking gate, mainline landing/merge-intent regressions, CI-responsibility, frontend checks, transition lint/preflight, publication readiness and diff checks. Fresh exact-head CI, Decision Preflight and State Gate pull_request runs are `SUCCESS`.
5. A clean detached exact-head audit accepts the final bound head and is recorded as a PR comment. There are no unresolved review threads, head/base drift, or non-clean merge state.
6. Owner `dddd2024` publishes exactly one schema-v2 merge approval attestation comment whose self-referential approval object ID, canonical digests, exact three workflow observations, accepted head and locked base validate against remote truth.
7. Owner-controlled mark-ready and merge occur once using merge method `merge` and expected-head protection. There is no auto-merge, direct-main push, force push, rebase, history rewrite, squash or deployment.
8. Post-merge verification proves the PR merge commit, new `origin/main`, State Gate push and required main checks. `mainline-merge-validation` passes against the committed intent and remote attestation before Issue #268 is closed completed.

## Execution policy

- Treat PR #270 and audit comment `5356762115` as immutable accepted product evidence. PR #269 remains immutable negative evidence.
- Do not edit this Decision after activation and do not guess the landing PR number.
- Replay only commits `c5f30ee6b8869160c89e937eaee233415b01aaf6` and `7c8335a80a8eb5fe5e7cd42d59b7d2004dd36040`; compare all 15 accepted product objects before each publication.
- First publish the single Draft PR, observe its actual number, then make exactly one PR-binding governance commit and one final push.
- Treat checks on the unbound first Draft head as transient, never as landing acceptance. Use only fresh runs on the final bound head.
- Publish the owner attestation only after exact-head audit acceptance and immediate remote re-observation. Mark-ready and merge immediately afterward with expected-head protection.
- Preserve all unrelated runtime/untracked content. Stop on any base/head/check/digest/thread/mergeability mismatch or exhausted publication limit.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue272_product_ux2b_opencode_server_r2_v4_landing",
  "round_id": "round_20260821_issue272_product_ux2b_opencode_server_r2_v4_landing",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260820_issue268_product_ux2a_usage_budgets_r2_v5_landing",
  "follows_last_round_id": "round_20260820_issue268_product_ux2a_usage_budgets_r2_v5_landing",
  "previous_audit_outcome": "PR274_EXACT_HEAD_EC1835F7_CLEAN_LOCAL_AUDIT_NO_FINDINGS_REMOTE_THREE_RUNS_SUCCESS_PENDING_SEPARATE_LANDING_AUTHORITY",
  "workstream_id": "issue272-product-ux2b-opencode-server-r2-v4-landing",
  "source_issue": 272,
  "validated_product_pr": 274,
  "validated_product_head": "ec1835f7644c36f4fd69f3ffbd2c61432520126f",
  "validated_product_tree": "5138e0188d339cb90b1bc7ba5416ba3ed2239069",
  "validated_ci_run_id": 32394440620,
  "validated_decision_preflight_run_id": 32394440688,
  "validated_state_gate_run_id": 32394440627,
  "rejected_product_pr": 273,
  "rejected_product_head": "0e33f3d143a6122f0a20580911caed7c88b48342",
  "rejected_audit_comment_id": 5358486097,
  "required_branch": "owner/issue272-product-ux2b-opencode-server-r2-v4-landing",
  "starting_head": "29faccd89a86b4313df66151652e2bd5724f141b",
  "activation_base_sha": "29faccd89a86b4313df66151652e2bd5724f141b",
  "integration_base_ref": "main",
  "base_sha": "29faccd89a86b4313df66151652e2bd5724f141b",
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
    "create owner/issue272-product-ux2b-opencode-server-r2-v4-landing from exact main 29faccd89a86b4313df66151652e2bd5724f141b in an isolated canonical-LF checkout",
    "commit this immutable landing Decision as the first new commit after 29faccd89a86b4313df66151652e2bd5724f141b before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue272v4landing.verify_validated_product",
      "command": "verify origin/main remains 29faccd89a86b4313df66151652e2bd5724f141b; verify PR 274 remains Draft at head ec1835f7644c36f4fd69f3ffbd2c61432520126f and base 29faccd89a86b4313df66151652e2bd5724f141b; verify exact-head CI, Decision Preflight and State Gate run IDs 32394440620, 32394440688 and 32394440627 are SUCCESS; verify PR 273 and rejection comment 5358486097 remain immutable negative evidence; verify zero unresolved review threads and that the landing target branch and Draft PR do not yet exist",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue272v4landing.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before product or merge-intent mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v4landing.replay_validated_product",
      "command": "git cherry-pick 6664d53c9603794c7e04bd0c338fd0db80331b23 ec1835f7644c36f4fd69f3ffbd2c61432520126f; prove all nine product and test path objects equal validated PR 274 and make no source edit",
      "phase": "implementation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["commit_replay", "repository_observation"],
      "network_access": false, "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue272v4landing.prepublication_validation",
      "command": "before the landing PR number exists run the four-file PRODUCT-UX-2B focused test set, CI responsibility, unchanged frontend test typecheck and mock build, transition-lint, transition-preflight --mode pre, worktree-publication-readiness and git diff --check; prove all nine product objects equal PR 274; defer active-intent binding tests until the actual Draft PR number is committed",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v4landing.publish_initial_draft",
      "command": "push owner/issue272-product-ux2b-opencode-server-r2-v4-landing once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing; transient checks against inherited PR 271 active intent are not acceptance evidence",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue272v4landing.bind_actual_pr",
      "command": "using only the observed GitHub-assigned Draft PR number, copy the committed schema-v2 PR 271 active intent byte-for-byte to project_state/mainline_merge_intents/archive/pr271_v2.json and replace active.json with schema version 2 bound to the actual landing PR, locked base, this immutable Decision, committed Command Plan, merge method merge, exact three pre-merge workflows and expiry 2026-08-28T23:59:59Z; commit exactly once without editing the Decision",
      "phase": "implementation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v4landing.final_bound_validation",
      "command": "on the final PR-bound head prove all nine validated product objects remain identical and archived PR 271 bytes plus schema-v2 active intent fields and digests are exact; run the four-file focused set, exact Platform V1 blocking gate, mainline landing and merge-intent tests, CI responsibility, unchanged frontend checks, transition-lint, transition-preflight --mode pre, worktree-publication-readiness and git diff --check; any failure stops publication",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false, "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v4landing.publish_bound_head",
      "command": "push the single post-publication binding commit once; verify remote branch equals local final head; close PR 274 as superseded by the landing PR; observe fresh exact-final-head CI, Decision Preflight and State Gate pull_request runs without rerun",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["push", "pull_request_close", "repository_observation", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue272v4landing.attest_and_land",
      "command": "after fresh exact-final-head workflows succeed, perform a clean detached exact-head audit including both PR 273 blockers and record ACCEPTED on the landing PR; immediately reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation comment bound to its actual comment ID, exact three workflow run IDs, intent digest, head and base; then owner-controlled mark-ready and merge exactly once with merge method merge and expected-head protection",
      "phase": "publication", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue272v4landing.post_merge_verify",
      "command": "verify the landing PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 272 completed only after all post-merge evidence is green",
      "phase": "validation", "required": true, "expected_exit_codes": [0],
      "execution_surface": "local", "operations": ["repository_observation", "issue_close", "network_access"],
      "network_access": true, "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_task_execution.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr271_v2.json",
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
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/rounds/**", "project_state/audits/**", "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**", "project_state/schemas/**", "requirements*.txt", "pyproject.toml", ".github/**",
    "reverse_agent/project_gate.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/mainline_landing.py",
    "reverse_agent/decision_preflight.py", "frontend/**", "docs/**", "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "live_model_call", "opencode_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "tag_or_release", "deployment", "worktree_deletion", "history_rewrite", "source_edit",
    "non_loopback_transport", "remote_endpoint_from_untrusted_payload", "raw_event_persistence", "prompt_or_response_persistence",
    "secret_redaction_weakening", "second_taskstore_or_budget_database", "network_attack_or_offensive_security_work"
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
      "verify origin/main remains 29faccd89a86b4313df66151652e2bd5724f141b; verify PR 274 remains Draft at head ec1835f7644c36f4fd69f3ffbd2c61432520126f and base 29faccd89a86b4313df66151652e2bd5724f141b; verify exact-head CI Decision Preflight and State Gate run IDs 32394440620 32394440688 and 32394440627 are SUCCESS; verify PR 273 and rejection comment 5358486097 remain immutable negative evidence; verify zero unresolved review threads and that the landing target branch and Draft PR do not yet exist",
      "push owner/issue272-product-ux2b-opencode-server-r2-v4-landing once and create exactly one Draft PR with base=main; read the actual GitHub-assigned PR number without guessing; transient checks against inherited PR 271 active intent are not acceptance evidence",
      "push the single post-publication binding commit once; verify remote branch equals local final head; close PR 274 as superseded by the landing PR; observe fresh exact-final-head CI Decision Preflight and State Gate pull_request runs without rerun",
      "after fresh exact-final-head workflows succeed perform a clean detached exact-head audit including both PR 273 blockers and record ACCEPTED on the landing PR; immediately reobserve base head checks MERGEABLE CLEAN and zero unresolved threads; publish one schema-v2 mainline merge approval attestation comment bound to its actual comment ID exact three workflow run IDs intent digest head and base; then owner-controlled mark-ready and merge exactly once with merge method merge and expected-head protection",
      "verify the landing PR is merged and origin/main equals mergeCommit.oid; wait for State Gate push and required main checks; run mainline-merge-validation against the merge and remote attestation; close Issue 272 completed only after all post-merge evidence is green"
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
  "success_terminal": "ISSUE272_PRODUCT_UX2B_OPENCODE_SERVER_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE272_PRODUCT_UX2B_R2_V4_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the validated Issue #272 PRODUCT-UX-2B OpenCode Server/SSE transport through a self-contained Path-B candidate whose immutable Decision, generated Command Plan, schema-v2 active merge intent, exact product objects, independent audit, owner approval attestation and post-merge evidence remain valid on merged `main`.

## Acceptance

1. This owner landing Decision is the first new commit after exact `main@29faccd89a86b4313df66151652e2bd5724f141b`; no product, merge-intent mutation or publication occurs before generated authority and `PRE_EXECUTION_AUTHORIZED`.
2. The nine product/test path objects exactly equal PR #274 head `ec1835f7644c36f4fd69f3ffbd2c61432520126f`; replay commits `6664d53c` and `ec1835f7` without source edits, dependencies, workflows, frontend, credential, provider, live model, OpenCode or second-store changes.
3. The final code retains authenticated loopback-only OpenCode Server/SSE transport, exact session filtering, sanitized usage persistence, cumulative task/window budget enforcement across roles and claim epochs, pre-dispatch UNKNOWN/exhausted stops, stale lease fencing, provider-qualified model confinement, bounded abort and deterministic disposal.
4. The actual GitHub-assigned landing PR number is observed after first Draft publication. The committed PR #271 schema-v2 active intent is archived byte-for-byte, and final `active.json` binds the actual landing PR, locked base, Decision digest, Command Plan digest, merge method `merge`, exact three pre-merge workflows and expiry.
5. The final bound head passes focused tests, exact Platform V1 blocking gate, mainline landing and merge-intent tests, CI responsibility, unchanged frontend checks, transition lint/preflight, publication readiness and diff checks. Fresh exact-head CI, Decision Preflight and State Gate pull_request runs are SUCCESS.
6. A clean detached exact-head audit reproduces both PR #273 blockers as fixed, finds no new blocker and records ACCEPTED on the landing PR. There are no unresolved review threads, head/base drift or non-clean merge state.
7. Owner `dddd2024` publishes exactly one schema-v2 merge approval attestation whose self-referential approval object ID, canonical digests, exact three workflow observations, accepted head and locked base validate against remote truth.
8. Owner-controlled mark-ready and merge occur once using merge method `merge` and expected-head protection. There is no auto-merge, direct-main push, force push, rebase, history rewrite, squash or deployment.
9. Post-merge verification proves the PR merge commit, new `origin/main`, State Gate push and required main checks. `mainline-merge-validation` passes against committed intent and remote attestation before Issue #272 is closed completed.
10. No live OpenCode/model/provider call, credential/auth-store read, dependency install, runner dispatch, non-loopback request, network attack, tag, release or deployment occurs.

## Execution policy

- Treat PR #273 and rejection comment `5358486097` as immutable negative evidence. PR #274 is validated candidate evidence but receives no acceptance mutation under its exhausted V3 authority.
- Do not edit this Decision after activation and do not guess the landing PR number.
- Replay only commits `6664d53c9603794c7e04bd0c338fd0db80331b23` and `ec1835f7644c36f4fd69f3ffbd2c61432520126f`; compare all nine product objects before each publication.
- First publish one Draft PR, observe its actual number, then make exactly one PR-binding governance commit and one final push.
- Treat checks on the unbound first Draft head as transient. Use only fresh runs on the final PR-bound head for audit, attestation and merge.
- Publish owner attestation only after exact-head audit acceptance and immediate remote re-observation. Mark-ready and merge immediately afterward with expected-head protection.
- Preserve all unrelated runtime/untracked content. Stop on any base/head/check/digest/thread/mergeability mismatch or exhausted publication limit.

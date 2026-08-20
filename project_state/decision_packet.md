# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260820_issue268_product_ux2a_usage_budgets_r2_v3",
  "round_id": "round_20260820_issue268_product_ux2a_usage_budgets_r2_v3",
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
  "previous_audit_outcome": "PR269_EXACT_HEAD_REWORK_REQUIRED_CRASH_RETRY_BLOCKED_BY_MAX_TASKS",
  "superseded_decision_id": "decision_20260820_issue268_product_ux2a_usage_budgets_r2_v2",
  "superseded_round_id": "round_20260820_issue268_product_ux2a_usage_budgets_r2_v2",
  "superseded_owner_branch": "owner/issue260-product-ux2a-usage-budgets-r2-v2",
  "superseded_owner_decision_commit": "7585480244ff265546f4006019c80c65f719ce32",
  "superseded_generated_authority_commit": "334c0dcabda93e92d742f034bcdd964aa74a1463",
  "superseded_candidate_head": "28fe5d7e4cdf668f2a8e7a260ec6d5a911f1ff43",
  "superseded_pull_request": 269,
  "workstream_id": "issue268-product-ux2a-usage-budgets-r2-v3",
  "source_issue": 268,
  "required_branch": "owner/issue260-product-ux2a-usage-budgets-r2-v3",
  "starting_head": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "activation_base_sha": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "integration_base_ref": "main",
  "base_sha": "aa5972a2c216a775089fbb52a5efa160f4884eb8",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
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
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue260-product-ux2a-usage-budgets-r2-v3 from exact main aa5972a2c216a775089fbb52a5efa160f4884eb8 in an isolated canonical-LF checkout",
    "commit this immutable Decision as the first new commit after aa5972a2c216a775089fbb52a5efa160f4884eb8 before product mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue268v3.verify_owner_authority",
      "command": "verify GitHub Issue 268 remains unchanged and open; verify PR 269 exact head 28fe5d7e4cdf668f2a8e7a260ec6d5a911f1ff43 has an independent REWORK_REQUIRED comment for the max_tasks=1 crash-recovery boundary; verify origin/main equals aa5972a2c216a775089fbb52a5efa160f4884eb8; verify the exact target branch is created from that base and no remote target branch or open pull request already exists",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue268v3.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before any product source or test mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.recover_and_repair_usage_budget_contract",
      "command": "reuse only the exact allowlisted product delta from audited PR 269 head 28fe5d7e4cdf668f2a8e7a260ec6d5a911f1ff43; distinguish first task starts from INTERRUPTED retries so max_tasks=1 with max_retries=1 can reclaim the retained reservation; keep retry and WIP fencing, reservation re-keying, exact-once charging, honest usage states, API and Agent Runs UI contracts unchanged; add the exact boundary regression test",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_schema_mutation", "bounded_test_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.focused_validation",
      "command": "python -m pytest tests/platform_v1/test_autonomy.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_run_read_model.py tests/platform_v1/test_task_service.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.platform_regression",
      "command": "run the exact Platform V1 blocking gate command committed in .github/workflows/ci.yml, including only its seven exact-node deselections for Decision immutability and installed-OpenCode fake-provider probes; also run tests/test_ci_responsibility.py to prove the deselection set is exact and not broadened",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.frontend_validation",
      "command": "run npm --prefix frontend test -- runs.test.tsx, npm --prefix frontend run typecheck, and npm --prefix frontend run build:mock using the repository's existing installed dependencies only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.final_local_validation",
      "command": "run repository blocking CI-equivalent tests that are compatible with a pre-publication head, transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; require all checks green without model, provider, credential, runner, package-install, or network execution",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue268v3.publish_single_draft",
      "command": "push owner/issue260-product-ux2a-usage-budgets-r2-v3 exactly once and create exactly one Draft PR with base=main; record the immutable Decision, superseded PR 269, exact checks, exact head, corrected crash boundary, and honest enforcement boundary in the PR body",
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
      "command_id": "issue268v3.observe_exact_head_checks",
      "command": "observe the fresh GitHub Actions results for the exact replacement Draft PR head without rerun or mutation; stop for independent exact-head audit and separate R2 landing authority",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "project_state/mainline_recoveries/**",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
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
    "mark_ready",
    "merge",
    "history_rewrite",
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
      "verify GitHub Issue 268 remains unchanged and open; verify PR 269 exact head 28fe5d7e4cdf668f2a8e7a260ec6d5a911f1ff43 has an independent REWORK_REQUIRED comment for the max_tasks=1 crash-recovery boundary; verify origin/main equals aa5972a2c216a775089fbb52a5efa160f4884eb8; verify the exact target branch is created from that base and no remote target branch or open pull request already exists",
      "push owner/issue260-product-ux2a-usage-budgets-r2-v3 exactly once and create exactly one Draft PR with base=main; record the immutable Decision, superseded PR 269, exact checks, exact head, corrected crash boundary, and honest enforcement boundary in the PR body",
      "observe the fresh GitHub Actions results for the exact replacement Draft PR head without rerun or mutation; stop for independent exact-head audit and separate R2 landing authority"
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
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE268_PRODUCT_UX2A_USAGE_BUDGETS_R2_V3_DRAFT_READY_FOR_INDEPENDENT_AUDIT",
  "blocked_terminal": "ISSUE268_PRODUCT_UX2A_R2_V3_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Recover the accepted portions of PRODUCT-UX-2A from audited PR #269 and correct its exact crash-retry boundary without broadening the architecture: append-only numeric OpenCode usage observations in the existing TaskStore, server-owned atomic token/cost admission reservations, exact-once reconciliation, honest enforcement classifications, and observable API/UI summaries without another orchestrator, database, telemetry backend, dependency, or provider integration.

## Acceptance

1. This immutable owner Decision is the first new commit after exact `main@aa5972a2c216a775089fbb52a5efa160f4884eb8`; all product mutation follows a generated Command Plan and `PRE_EXECUTION_AUTHORIZED` preflight.
2. Only the exact 15 product/test/frontend paths from audited PR #269 are recovered. No stale v2 gate artifact, Decision, branch binding, commit, or publication authority is reused.
3. A valid window with `max_tasks=1`, `max_retries=1`, and one retained ACTIVE reservation can reclaim its sole `INTERRUPTED` task: claim epoch advances, the reservation is re-keyed rather than duplicated or released, `tasks_started` remains the count of distinct first starts, `retries_used` increments once, and completion charges once.
4. First starts still fail closed when `tasks_started >= max_tasks`; interrupted retries still fail closed when `retries_used >= max_retries`; WIP and token/cost admission remain atomic in the same `BEGIN IMMEDIATE` transaction.
5. Allowlisted documented OpenCode-shaped numeric usage remains extracted before generic evidence redaction and persisted without prompts, responses, tool payloads, headers, credentials, raw event JSON, or adjacent secret sentinels; generic secret/token redaction is not weakened.
6. Existing TaskStore databases migrate in place and idempotently; no second database, budget service, orchestration runtime, policy engine, dependency, workflow, package, or lockfile is introduced.
7. Reservation completion, retry, crash and reconciliation are exact-once. Admission denial dispatches no executor. Overrun or unavailable usage stops future dispatch with explicit evidence and never claims a mid-call provider cutoff unsupported by the current `subprocess.run` transport.
8. API and Agent Runs UI expose limits, reserved, observed, remaining, unknown counts and task/role provenance, and distinguish `HARD_ADMISSION_ENFORCED`, `POST_RUN_OBSERVED`, and `USAGE_UNKNOWN` without overstating enforcement.
9. Focused backend tests, the exact committed Platform V1 blocking CI-equivalent suite, `tests/test_ci_responsibility.py`, the Agent Runs frontend test, frontend typecheck, mock build, repository blocking CI-equivalent checks, transition lint/preflight, publication readiness, and `git diff --check` pass on the exact candidate head using provider-free fixtures and existing installed dependencies.
10. Execution performs no model/provider/OpenCode invocation, credential/auth-store read, runner dispatch, package install, dependency/workflow/governance implementation change, direct-main push, force push, rebase, history rewrite, auto-merge, mark-ready, merge, tag, release, or deployment.
11. The exact validated candidate is pushed once and published as one replacement Draft PR. Fresh exact-head CI is observed; independent exact-head audit and any R2 landing require separate authority.

## Execution policy

- Treat Issue #268, the PR #269 exact-head REWORK_REQUIRED evidence, and this v3 Decision together as the bounded owner-approved recovery authority. Issue comments and later Issue edits do not expand it.
- Do not edit this Decision after its activation commit.
- Generate and commit only the listed gate artifacts before product mutation; require `PRE_EXECUTION_AUTHORIZED` with zero blockers.
- Recover only the product commit delta from `28fe5d7e4cdf668f2a8e7a260ec6d5a911f1ff43`; never recover its Decision or generated gate artifacts.
- Extract only allowlisted numeric usage from parsed OpenCode JSON before sanitized executor evidence is produced; never persist or expose the raw source event.
- Preserve legacy rows and classify their enforcement honestly. `UNKNOWN` is a state, never numeric zero.
- Stage only exact authorized paths and compare the staged raw manifest before every commit. Preserve unrelated source-worktree runtime and untracked content.
- Stop after one replacement Draft PR and fresh exact-head CI observation. This Decision grants no independent audit acceptance, attestation, mark-ready, merge, Issue close, old-PR close, or mainline landing.

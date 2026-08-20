# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260820_issue272_product_ux2b_opencode_server_r2_v2",
  "round_id": "round_20260820_issue272_product_ux2b_opencode_server_r2_v2",
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
  "previous_audit_outcome": "ISSUE272_V1_STOPPED_BEFORE_PUBLICATION_REQUIRED_BARE_FULL_SUITE_CONFLICTED_WITH_OPENCODE_INVOCATION_PROHIBITION",
  "workstream_id": "issue272-product-ux2b-opencode-server-r2-v2",
  "source_issue": 272,
  "required_branch": "owner/issue272-product-ux2b-opencode-server-r2-v2",
  "starting_head": "29faccd89a86b4313df66151652e2bd5724f141b",
  "activation_base_sha": "29faccd89a86b4313df66151652e2bd5724f141b",
  "integration_base_ref": "main",
  "base_sha": "29faccd89a86b4313df66151652e2bd5724f141b",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 1,
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
    "create owner/issue272-product-ux2b-opencode-server-r2-v2 from exact main 29faccd89a86b4313df66151652e2bd5724f141b in an isolated canonical-LF checkout",
    "commit this immutable Decision as the first new commit after 29faccd89a86b4313df66151652e2bd5724f141b before product mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue272v2.verify_recovery_authority",
      "command": "verify GitHub Issue 272 remains planning-only and unchanged; verify origin/main equals 29faccd89a86b4313df66151652e2bd5724f141b and PR 271 post-merge State Gate remains green; verify v1 Decision c0312e952e3fa0b747f0b4ae2bd8aa9e03383e98, gate commit e1667963 and product commit 4a4e7e38 exist only as local stopped evidence; verify the v1 branch has no remote publication; verify the exact v2 branch was created from that base and no remote v2 branch or open pull request exists",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue272v2.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before recovering any product source or test object",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.recover_exact_v1_product",
      "command": "after PRE_EXECUTION_AUTHORIZED, cherry-pick exact local product commit 4a4e7e38 and require the canonical Git delta for the nine authorized product/test paths to be object-identical to the v1 stopped candidate; no v1 Decision or generated gate artifact may be recovered",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "cherry_pick", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.focused_validation",
      "command": "python -m pytest tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task_execution.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.platform_regression",
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
      "command_id": "issue272v2.repository_diagnostic",
      "command": "run repository-wide pytest with exactly the same seven exact-node deselections used by the Platform V1 blocking gate so installed OpenCode is never launched; require the only failures to be the exact ten parameter cases of tests/test_path_a_gate.py::test_state_gate_pull_request_trigger_reaches_every_risk_only_change caused by the unchanged main State Gate paths filter, with every other node passing; treat this known baseline debt as diagnostic rather than a product success",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [1],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.frontend_regression",
      "command": "run npm test, typecheck and build:mock for the exact unchanged frontend tree using only already-installed local dependencies through a repository-external temporary validation copy; do not install dependencies and do not mutate frontend or package artifacts",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.final_local_validation",
      "command": "run transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; inspect the exact staged raw path manifest, canonical v1-v2 product-delta identity, and secret-sentinel assertions; require all blocking checks green without model, provider, credential, runner, package-install, OpenCode, or non-loopback network execution",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v2.publish_single_draft",
      "command": "push owner/issue272-product-ux2b-opencode-server-r2-v2 exactly once and create exactly one Draft PR with base=main; record the immutable Decision, v1 stop evidence, exact checks, exact head, official OpenCode contracts, loopback/secret boundary, abort semantics, known unrelated repository diagnostic debt, and CLI compatibility in the PR body",
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
      "command_id": "issue272v2.observe_exact_head_checks",
      "command": "observe the fresh GitHub Actions results for the exact Draft PR head without rerun or mutation; stop for independent exact-head audit and separate R2 landing authority",
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
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_execution.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task_execution.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": ["project_state/decision_packet.md", "AGENTS.md"],
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
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "live_model_call", "opencode_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "tag_or_release", "deployment", "worktree_deletion", "mark_ready", "merge", "history_rewrite",
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
      "verify GitHub Issue 272 remains planning-only and unchanged; verify origin/main equals 29faccd89a86b4313df66151652e2bd5724f141b and PR 271 post-merge State Gate remains green; verify v1 Decision c0312e952e3fa0b747f0b4ae2bd8aa9e03383e98, gate commit e1667963 and product commit 4a4e7e38 exist only as local stopped evidence; verify the v1 branch has no remote publication; verify the exact v2 branch was created from that base and no remote v2 branch or open pull request exists",
      "provider-free fake HTTP and SSE fixtures bound only to 127.0.0.1 during deterministic tests",
      "push owner/issue272-product-ux2b-opencode-server-r2-v2 exactly once and create exactly one Draft PR with base=main; record the immutable Decision, v1 stop evidence, exact checks, exact head, official OpenCode contracts, loopback/secret boundary, abort semantics, known unrelated repository diagnostic debt, and CLI compatibility in the PR body",
      "observe the fresh GitHub Actions results for the exact Draft PR head without rerun or mutation; stop for independent exact-head audit and separate R2 landing authority"
    ],
    "ci_network_exceptions": ["provider-free fake HTTP and SSE fixtures bound only to 127.0.0.1"],
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
  "success_terminal": "ISSUE272_PRODUCT_UX2B_OPENCODE_SERVER_R2_V2_DRAFT_READY_FOR_INDEPENDENT_AUDIT",
  "blocked_terminal": "ISSUE272_PRODUCT_UX2B_R2_V2_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Recover the exact validated PRODUCT-UX-2B candidate from stopped local v1 evidence under a corrected immutable authority. Add an optional trusted OpenCode Server transport behind the existing executor contract: per-role loopback-only authenticated server lifecycle, official HTTP/SSE session control, bounded event parsing, completed-assistant numeric usage, reservation-aware abort, and durable owner-epoch-fenced persistence. Preserve the CLI transport as the compatibility fallback and reuse the existing TaskStore, executor permissions, binding relay, authority envelope, durable runs, evidence and validation rather than adding another runtime or database.

## Acceptance

1. This immutable owner Decision is the first new commit after exact `main@29faccd89a86b4313df66151652e2bd5724f141b`; every product mutation follows a generated Command Plan and `PRE_EXECUTION_AUTHORIZED` preflight.
2. V1 commits `c0312e952e3fa0b747f0b4ae2bd8aa9e03383e98`, `e1667963` and `4a4e7e38` remain local negative/recovery evidence. V1 is not pushed because its required bare full-suite command could collect four installed-OpenCode tests while the same Decision prohibited any OpenCode invocation.
3. Only the exact nine product/test paths listed by this Decision may be recovered. The canonical v2 product delta must be object-identical to v1 product commit `4a4e7e38`; no v1 Decision or gate artifact may cross into v2.
4. There is no frontend, dependency, package, lockfile, workflow, schema, governance implementation, model-control, credential-relay, trusted-host, coordinator, documentation or second-store mutation.
5. Server mode is optional and selected only by trusted process configuration. The default CLI execution path, its JSON-line parsing, role permissions, prompt envelope, binding behavior, lease release, evidence, timeout and validation contracts remain compatible.
6. Production server mode creates exactly one per-role child bound to `127.0.0.1`, generates a transient Basic-auth password, preserves the existing restricted child environment and role config, uses only the official health/session/event/prompt_async/abort/dispose endpoints, and shuts down only the exact child it created within bounded time.
7. Endpoint and protocol handling reject non-loopback, URL-userinfo, redirects, wrong content type, oversized JSON/SSE, malformed events, foreign-session completion/error/usage, disconnect-before-idle, timeout and unexpected child exit. None can be treated as successful execution.
8. Only completed assistant-message numeric usage for the exact session is accepted. Child IDs are hashed; duplicate/progressive events are idempotent; prompts, responses, reasoning, tool payloads, raw events, headers, passwords, URL credentials and secret sentinels never reach TaskStore, events, evidence, API output, logs or exceptions.
9. Durable usage appends validate the active run owner and epoch in the same SQLite transaction as insertion. A stale worker cannot append after lease movement; exact-epoch replay remains idempotent.
10. The existing active TaskStore reservation is the only streaming threshold source. On the first observed cumulative token/cost crossing, one abort request is sent. `STREAM_ABORT_CONFIRMED` requires the documented boolean true; false, error or disconnect is `STREAM_ABORT_UNKNOWN`. Neither state is called a provider hard cutoff because a completed model step precedes observation.
11. Exact-session `session.idle` without an abort proves transport completion; `session.error` fails. A confirmed threshold abort returns a distinct non-success classification so existing claim reconciliation can classify overrun and block future dispatch honestly.
12. Provider-free fake loopback tests, focused suites, the exact Platform V1 blocking gate, CI responsibility, frontend regression/typecheck/mock build, transition lint/preflight, publication readiness and `git diff --check` pass on the exact candidate head using existing dependencies only.
13. Repository-wide pytest is diagnostic because main currently has ten known `test_path_a_gate.py` failures against its unchanged path-filtered State Gate. With the exact seven CI deselections, the candidate must reproduce exactly those ten failures and pass every other node; any additional or missing failure is a stop.
14. Execution performs no live model/provider/OpenCode invocation, credential/auth-store read, runner dispatch, dependency install, non-loopback test, network attack, direct-main push, force push, rebase, history rewrite, auto-merge, mark-ready, merge, tag, release or deployment.
15. The exact validated candidate is pushed once and published as one Draft PR. Fresh exact-head CI is observed; independent audit and any R2 mainline landing require separate authority.

## Execution policy

- Treat Issue #272 and this Decision as the complete bounded owner authority. The Issue cannot authorize execution and later comments or edits do not expand this Decision.
- Do not edit this Decision after its activation commit.
- Generate and commit only the listed gate artifacts before product recovery; require `PRE_EXECUTION_AUTHORIZED` with zero blockers.
- Recover only product commit `4a4e7e38`, then prove the nine-path canonical delta is identical to v1. Do not recover v1 governance.
- Use fake loopback servers for deterministic validation. Do not start OpenCode, query auth/models, read credentials, or contact a provider.
- Parse usage through a closed numeric allowlist before sanitized evidence. Hash child identifiers and discard all raw event and content fields.
- Stage only exact authorized paths and inspect the staged raw manifest before every commit. Preserve unrelated worktrees and runtime/untracked content.
- Stop after one Draft PR and fresh exact-head CI observation. This Decision grants no audit acceptance, attestation, mark-ready, merge, Issue close, old-PR close or mainline landing.

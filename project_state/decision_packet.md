# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue272_product_ux2b_opencode_server_r2_v3",
  "round_id": "round_20260821_issue272_product_ux2b_opencode_server_r2_v3",
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
  "previous_audit_outcome": "PR273_EXACT_HEAD_0E33F3D1_REJECTED_CUMULATIVE_TASK_BUDGET_RESET_AND_UNQUALIFIED_MODEL_OMISSION",
  "workstream_id": "issue272-product-ux2b-opencode-server-r2-v3",
  "source_issue": 272,
  "required_branch": "owner/issue272-product-ux2b-opencode-server-r2-v3",
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
    "create owner/issue272-product-ux2b-opencode-server-r2-v3 from exact main 29faccd89a86b4313df66151652e2bd5724f141b in an isolated canonical-LF checkout",
    "commit this immutable Decision as the first new commit after 29faccd89a86b4313df66151652e2bd5724f141b before product mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue272v3.verify_repair_authority",
      "command": "verify Issue 272 remains planning-only; verify origin/main equals 29faccd89a86b4313df66151652e2bd5724f141b; verify Draft PR 273 remains at rejected exact head 0e33f3d143a6122f0a20580911caed7c88b48342 with CI, Decision Preflight and State Gate success plus independent REJECT comment 5358486097; verify no remote v3 branch or open v3 pull request exists",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue272v3.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before recovering product objects",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.recover_rejected_product",
      "command": "after PRE_EXECUTION_AUTHORIZED, cherry-pick exact rejected product commit 0e33f3d143a6122f0a20580911caed7c88b48342 and require the canonical Git delta for the nine authorized product/test paths to be object-identical; recover no v2 Decision or gate artifact",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "cherry_pick", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.repair_audit_findings",
      "command": "add an owner-epoch-fenced active task/window usage budget snapshot in the existing TaskStore; compare every completed assistant observation against cumulative already-accepted plus new task usage; make prior UNKNOWN or already-exhausted enforced usage fail before server dispatch; retain idempotent replay; require exact provider/model form in server mode without changing CLI compatibility; add deterministic regressions for planner 60 plus coder 50 against reservation 100, unknown and exhausted pre-dispatch stops, replay, stale epoch, qualified model success and unqualified model fail-closed",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.focused_validation",
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
      "command_id": "issue272v3.platform_regression",
      "command": "run the exact Platform V1 blocking gate committed in .github/workflows/ci.yml with only its seven exact-node deselections; also run tests/test_ci_responsibility.py",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.repository_diagnostic",
      "command": "run repository-wide pytest with exactly the same seven exact-node deselections; require exit 1 with only the exact ten unchanged tests/test_path_a_gate.py path-filter parameter failures and every other node passing",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [1],
      "execution_surface": "local",
      "operations": ["run_checks", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.frontend_regression",
      "command": "run frontend test, typecheck and build:mock for the exact unchanged frontend tree using only existing local dependencies through a repository-external temporary validation copy; install nothing and mutate no frontend or package artifact",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.final_local_validation",
      "command": "run transition-lint, transition-preflight --mode pre, worktree-publication-readiness and git diff --check; inspect exact raw paths, v2 recovery object identity, repair-only second product commit and secret sentinels; require all blocking checks green without OpenCode, provider, model, credential, runner, package-install or non-loopback execution",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue272v3.publish_single_draft",
      "command": "push owner/issue272-product-ux2b-opencode-server-r2-v3 exactly once and create exactly one Draft PR against main; bind rejected PR 273 evidence, immutable v3 authority, exact tests, cumulative budget and model-selection corrections, known unrelated diagnostic debt and exact head in the body",
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
      "command_id": "issue272v3.observe_exact_head_checks",
      "command": "observe fresh GitHub Actions for the exact v3 Draft PR head without rerun or mutation; stop for a new independent exact-head audit and separate R2 landing authority",
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
    "project_state/current_state.json", "project_state/state_manifest.json", "project_state/artifact_index.json",
    "project_state/rounds/**", "project_state/audits/**", "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**", "project_state/mainline_merge_intents/**", "project_state/schemas/**",
    "requirements*.txt", "pyproject.toml", ".github/**", "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py", "reverse_agent/decision_preflight.py",
    "reverse_agent/platform_v1/trusted_host.py", "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/**", "frontend/**", "docs/**", "AGENTS.md"
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
      "verify Issue 272 remains planning-only; verify origin/main equals 29faccd89a86b4313df66151652e2bd5724f141b; verify Draft PR 273 remains at rejected exact head 0e33f3d143a6122f0a20580911caed7c88b48342 with CI, Decision Preflight and State Gate success plus independent REJECT comment 5358486097; verify no remote v3 branch or open v3 pull request exists",
      "provider-free fake HTTP and SSE fixtures bound only to 127.0.0.1 during deterministic tests",
      "push owner/issue272-product-ux2b-opencode-server-r2-v3 exactly once and create exactly one Draft PR against main; bind rejected PR 273 evidence, immutable v3 authority, exact tests, cumulative budget and model-selection corrections, known unrelated diagnostic debt and exact head in the body",
      "observe fresh GitHub Actions for the exact v3 Draft PR head without rerun or mutation; stop for a new independent exact-head audit and separate R2 landing authority"
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
  "success_terminal": "ISSUE272_PRODUCT_UX2B_OPENCODE_SERVER_R2_V3_DRAFT_READY_FOR_INDEPENDENT_AUDIT",
  "blocked_terminal": "ISSUE272_PRODUCT_UX2B_R2_V3_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Recover the exact rejected PRODUCT-UX-2B product objects from PR #273 under a fresh authority, then repair both independent-audit findings without widening the product: enforce the existing active reservation against cumulative task/window usage across planner, coder, reviewer and retries, and never silently drop a trusted configured model in Server mode. Preserve the official OpenCode Server/SSE adapter, CLI fallback, existing TaskStore and provider-free validation boundary.

## Acceptance

1. This Decision is the first new commit after exact `main@29faccd89a86b4313df66151652e2bd5724f141b`; generated Command Plan and `PRE_EXECUTION_AUTHORIZED` precede all recovered product objects.
2. PR #273 head `0e33f3d1` and REJECT comment `5358486097` remain immutable negative evidence. V3 first recovers only its nine product/test path objects and proves object identity, then adds exactly one bounded repair commit.
3. The active TaskStore reservation remains the only threshold. The enforcement snapshot uses the exact active task/window and totals every already accepted OBSERVED observation across prior roles and retained retry epochs; replay cannot double count.
4. Under an enforced reservation, any prior UNKNOWN observation or already-exhausted cumulative total stops before server/session/prompt dispatch. A newly persisted observation re-reads authoritative cumulative totals before deciding whether one abort is required.
5. Planner 60 plus coder 50 against reservation 100 requests exactly one coder abort and returns non-success. Stale durable owner/epoch cannot write or read the enforcement snapshot.
6. Server mode requires a trusted provider-qualified model selection and sends both official `providerID` and `modelID`; an unqualified configured model fails before child launch. CLI continues to accept its existing compatible identifier forms.
7. No prompt, response, reasoning, tool body, raw event, header, password, model secret or adjacent sentinel reaches TaskStore, evidence, events, API output, logs or exceptions.
8. Only the exact nine product/test paths plus Decision and five generated gates may differ. No frontend, dependency, package, lockfile, workflow, trusted-host, coordinator, model-control, credential relay, documentation or second-store mutation.
9. Focused tests, exact Platform V1 blocking gate, CI responsibility, unchanged frontend tests/typecheck/build, transition gates, publication readiness and diff check pass. Repository diagnostic reproduces only the exact ten unchanged path-filter failures.
10. No live OpenCode/model/provider call, credential/auth-store read, package install, runner dispatch, non-loopback request, network attack, mark-ready, merge, tag, release or deployment occurs.
11. Publish the exact validated v3 head once as one Draft PR. Independent audit and mainline landing require subsequent separate authority.

## Execution policy

- Do not edit this Decision after its activation commit.
- Generate and commit only the five listed gate artifacts before recovery.
- Cherry-pick only product commit `0e33f3d1`, never its v2 Decision or generated gates; verify canonical object identity.
- Implement cumulative enforcement by querying the existing TaskStore ledger, not a second counter/database or process-local approximation.
- Use only provider-free fake loopback fixtures; never start OpenCode or read credentials during validation.
- Stage exact authorized paths and inspect raw manifests. Preserve all unrelated worktrees and scratch content.
- Stop after one Draft PR and exact-head check observation. This authority grants no audit acceptance, old-PR mutation, mark-ready, merge or Issue close.

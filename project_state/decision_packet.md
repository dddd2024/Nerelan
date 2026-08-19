# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue259_state_gate_attestation_lifecycle_r2_v2",
  "round_id": "round_20260819_issue259_state_gate_attestation_lifecycle_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue250_platform_v2_landing_r2_v9",
  "follows_last_round_id": "round_20260819_issue250_platform_v2_landing_r2_v9",
  "previous_audit_outcome": "ISSUE259_STATE_GATE_ATTESTATION_LIFECYCLE_R2_V1_OWNER_AUDIT_BLOCKED",
  "superseded_pr": 261,
  "superseded_audit_comment_id": 5341050328,
  "workstream_id": "issue259-state-gate-attestation-lifecycle-r2-v2",
  "source_issue": 259,
  "required_branch": "owner/issue259-state-gate-attestation-lifecycle-r2-v2",
  "starting_head": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "activation_base_sha": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "integration_base_ref": "main",
  "base_sha": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 3,
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
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git worktree add F:/reverse-agent-issue259-state-gate-attestation-lifecycle-r2-v2 origin/owner/issue259-state-gate-attestation-lifecycle-r2-v2",
    "verify the owner-published immutable Decision activation commit is the first new commit after 4b95cf719244f25f095a0936c7a97e44c57a0482 and do not edit project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue259v2.verify_owner_authority",
      "command": "fetch and verify origin/main remains 4b95cf719244f25f095a0936c7a97e44c57a0482; verify the successor branch contains exactly the owner activation Decision as its first new commit; verify PR 261 is closed unmerged and audit comment 5341050328 exists",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue259v2.run_transition_gates",
      "command": "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before source mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v2.implement_lifecycle_contract",
      "command": "implement the lifecycle-scoped mainline landing contract: preserve historical schema-v1 four-run semantics; add schema-v2 current three-run pre-merge intent/attestation semantics; keep State Gate(push) post-merge only; migrate the active Platform V1 contract tests to dispatch by schema version without weakening historical v1 checks",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_schema_mutation", "bounded_test_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v2.prepublication_validation",
      "command": "run Issue 259 focused regression suites, historical integration-baseline checks, CI-responsibility/decision-preflight/architecture contracts, and all blocking tests that do not require the future GitHub-assigned PR number; run transition-lint and git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v2.publish_single_draft",
      "command": "push the successor candidate once and create exactly one Draft PR with base=main; read the PR number assigned by GitHub; do not guess or precompute the PR number and do not use Issue 259 as source_pr",
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
      "command_id": "issue259v2.bind_exact_pr_number",
      "command": "after GitHub assigns the Draft PR number, create exactly one bounded post-publication binding commit: archive the committed PR 257 v1 active intent byte-for-byte into archive/pr257_v1.json, create schema-v2 active intent bound to the actual Draft PR number/base/current Decision/current Command Plan, and add regression coverage proving Issue-number substitution fails closed; never edit the immutable Decision",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "bounded_test_mutation", "stage_authorized_paths", "commit", "repository_observation"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue259v2.final_blocking_validation",
      "command": "on the final PR-bound local head run tests/platform_v1/test_contracts.py and tests/platform_v1/test_merge_intent.py plus all Issue 259 focused suites and the repository blocking CI-equivalent command; require all blocking tests green; run transition-lint, transition-preflight --mode pre, and git diff --check; any failure stops publication",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v2.publish_final_bound_head",
      "command": "push the single final PR-binding commit once, verify remote branch equals local final head, then observe the fresh exact-head CI, Decision Preflight, and State Gate(pull_request) run IDs; do not rerun stale runs as approval evidence",
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
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py",
    "tests/test_ci_responsibility.py",
    "tests/test_decision_preflight.py",
    "tests/test_project_gate_baseline_lifecycle.py",
    "tests/test_architecture_contracts.py",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr257_v1.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/active.json",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/merge_approval_attestation.schema.json",
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
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/merge_approval_attestation.schema.json",
    "requirements*.txt",
    "pyproject.toml",
    ".github/workflows/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/decision_preflight.py",
    "frontend/**",
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
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "mark_ready",
    "merge",
    "history_rewrite",
    "archive_historical_intent_mutation"
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
  "success_terminal": "ISSUE259_STATE_GATE_ATTESTATION_LIFECYCLE_R2_V2_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE259_V2_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Repair Issue #259 as a lifecycle-correct, fail-closed v2 contract: preserve immutable historical four-run v1 evidence, use exactly three feasible exact-feature-head workflows for new pre-merge approval, and bind the new active intent to the real GitHub-assigned Draft PR number without predicting it.

## Acceptance

1. The owner activation Decision is the first new commit after exact `main@4b95cf719244f25f095a0936c7a97e44c57a0482`; PR #261 remains closed/unmerged and is cited only as superseded audit evidence.
2. Historical schema-version-1 intent/attestation/baseline/recovery semantics remain four-run and are not rewritten.
3. New schema-version-2 intent/attestation semantics require exactly CI, Decision Preflight, and State Gate(pull_request); State Gate(push) cannot substitute pre-merge and remains post-merge evidence.
4. The Decision has no allowed/forbidden overlap for `archive/pr257_v1.json`; transition preflight is `PRE_EXECUTION_AUTHORIZED` before source mutation and remains non-blocking on final head.
5. The actual GitHub-assigned successor Draft PR number, not Issue #259 and not a predicted number, is committed into the final v2 active merge intent in exactly one post-publication binding commit.
6. Platform V1 blocking contract tests are schema-aware: historical v1 keeps four-run expectations; current v2 keeps three-run pre-merge expectations. Missing/wrong PR binding fails closed.
7. The final PR-bound local head passes the real blocking CI-equivalent suite plus Issue #259 focused regression suites, transition lint/preflight, and `git diff --check` before the final push.
8. Fresh exact-head CI, Decision Preflight, and State Gate(pull_request) runs are all `SUCCESS` before owner attestation is possible.
9. No owner attestation, mark-ready, merge, direct-main push, force-push, rebase, auto-merge, deployment, release, credential access, provider/model/OpenCode invocation, or historical evidence rewrite occurs in agent execution.

## Execution policy

- Treat PR #261 and comment `5341050328` as immutable negative evidence; do not reopen or reuse its workflow runs.
- Do not copy PR #261 governance artifacts or its incorrect `source_pr: 259` active intent. Source/schema/test ideas may be reimplemented only after the new transition gate authorizes mutation.
- Do not edit this Decision after the owner activation commit.
- GitHub PR number allocation is an external fact: create one Draft PR first, read its assigned number, then make exactly one bounded binding commit and one final push.
- Stop after the three fresh exact-head pre-merge workflows have been observed; owner performs attestation and landing separately.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue259_state_gate_attestation_lifecycle_r2_v1",
  "round_id": "round_20260819_issue259_state_gate_attestation_lifecycle_r2_v1",
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
  "previous_audit_outcome": "ISSUE250_STATE_GATE_RECOVERY_V1_SUPERSEDED_CIRCULAR_PREMERGE_PUSH_REQUIREMENT",
  "superseded_pr": 258,
  "superseded_branch": "owner/issue250-state-gate-recovery-v1",
  "workstream_id": "issue259-state-gate-attestation-lifecycle-r2-v1",
  "source_issue": 259,
  "required_branch": "owner/issue259-state-gate-attestation-lifecycle-r2-v1",
  "starting_head": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "activation_base_sha": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "integration_base_ref": "main",
  "base_sha": "4b95cf719244f25f095a0936c7a97e44c57a0482",
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
    "git worktree add F:/reverse-agent-issue259-state-gate-attestation-lifecycle-r2-v1 origin/owner/issue259-state-gate-attestation-lifecycle-r2-v1",
    "edit and commit only project_state/decision_packet.md as the immutable activation commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue259v1.verify_authority",
      "command": "verify origin/main == 4b95cf71, successor branch == 4b95cf71, worktree clean",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v1.run_transition_gates",
      "command": "run transition-command-plan, transition-lint, transition-preflight in order",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v1.implement_policy_separation",
      "command": "split CANONICAL_WORKFLOW_POLICY into historical 4-run and current 3-run pre-merge policies; add v2 schemas; update validation to be polymorphic on schema_version; update tests",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "bounded_schema_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v1.run_focused_tests",
      "command": "run focused test suites: test_mainline_landing, test_integration_baseline, test_decision_preflight, test_project_gate_baseline_lifecycle, test_ci_responsibility, and other directly affected tests",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v1.final_gates",
      "command": "run transition lint, transition preflight, git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue259v1.publish_draft_pr",
      "command": "push branch once to origin/owner/issue259-state-gate-attestation-lifecycle-r2-v1, create exactly one Draft PR base=main, do not mark ready, do not merge",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/merge_approval_attestation.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py",
    "tests/test_ci_responsibility.py",
    "tests/test_decision_preflight.py",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr257_v1.json"
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
    "project_state/mainline_merge_intents/archive/**",
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
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE259_STATE_GATE_ATTESTATION_LIFECYCLE_V1_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE259_V1_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Fix the circular dependency in pre-merge State Gate(push) attestation by splitting workflow evidence into lifecycle-specific policies. The current pre-merge attestation requires only three exact-head runs (CI, Decision Preflight, State Gate pull_request). State Gate(push) becomes post-merge landing evidence only. Historical 4-run semantics are preserved verbatim for frozen baselines, archived intents, and PR #60 recovery.

## Acceptance

1. New `CURRENT_PREMERGE_WORKFLOW_POLICY` defines exactly three runs (CI, Decision Preflight, State Gate pull_request) for current pre-merge attestation.
2. `CANONICAL_WORKFLOW_POLICY` remains the four-run historical policy, used by `integration_baseline()` and `validate_pr60_recovery()` unchanged.
3. Schema-version-1 intents/attestations continue to validate against the four-run policy (backward compatible).
4. Schema-version-2 intents/attestations validate against the three-run current pre-merge policy.
5. Regression tests prove: current 3-run happy path passes; missing any of the 3 runs blocks; wrong head SHA blocks; wrong event blocks; workflow failure blocks; duplicate run IDs block; push State Gate cannot substitute as pre-merge evidence; frozen baseline still requires 4 runs; historical archived intents preserve 4-run semantics; owner approval checks still fail-closed; merge topology checks still fail-closed.
6. No historical artifact is modified.
7. Draft PR published, no mark-ready, no merge.

## Execution policy

- Immutable Decision first; source/schema/tests mutate only after PRE_EXECUTION_AUTHORIZED.
- No dependency installs, model calls, provider access, credentials, deployment, release, or main push.
- Commit only the authorized path set; generated governance artifacts limited to gate files.
- Push once, one Draft PR, no mark-ready, no merge.
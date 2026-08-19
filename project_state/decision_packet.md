# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue250_state_gate_recovery_r2_v1",
  "round_id": "round_20260819_issue250_state_gate_recovery_r2_v1",
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
  "previous_audit_outcome": "ISSUE250_V9_PRODUCT_MERGED_MAIN_CI_GREEN_STATE_GATE_BLOCKED_MISSING_PREMERGE_ATTESTATION",
  "workstream_id": "issue250-state-gate-recovery-r2-v1",
  "source_issue": 250,
  "recovery_for_pr": 257,
  "active_pr": 258,
  "required_branch": "owner/issue250-state-gate-recovery-v1",
  "starting_head": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "activation_base_sha": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "integration_base_ref": "main",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "accepted_product_head": "64a58dab5a3a51b57b09af284bcf7887c9ac2262",
  "accepted_product_merge_commit": "4b95cf719244f25f095a0936c7a97e44c57a0482",
  "accepted_product_tree": "a9ef8a376faf5d286b60a0ecb1a2014958becece",
  "accepted_audit_pr": 257,
  "accepted_audit_comment_id": 5340144601,
  "failed_main_state_gate_run": 32237446072,
  "authority_worktree": "F:/reverse-agent-issue250-state-gate-recovery-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "attestation_placeholder_comment_limit": 1,
  "attestation_comment_update_limit": 1,
  "audit_comment_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "expected_pr_number": 258,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_comment_update_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "runner_dispatch_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git worktree add -b owner/issue250-state-gate-recovery-v1 F:/reverse-agent-issue250-state-gate-recovery-v1 4b95cf719244f25f095a0936c7a97e44c57a0482",
    "edit and commit only project_state/decision_packet.md as the immutable activation commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue250recovery.observe_failure",
      "command": "verify exact merged main, PR 257 evidence, green main CI and Model Access, and State Gate run 32237446072 blocked because the structured pre-merge attestation was absent",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250recovery.bind_landing_authority",
      "command": "generate and commit the active Command Plan, archive PR 257 intent, and create PR 258 active merge intent bound to this immutable Decision and plan",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["generate_governance_artifact", "bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250recovery.validate_governance_only_candidate",
      "command": "prove there are no product changes, run active merge-intent and mainline landing tests, final transition lint/preflight, and git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250recovery.publish_exact_draft_pr",
      "command": "push branch once, create exactly one Draft PR expected as 258, and stop if GitHub assigns another number",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250recovery.attest_exact_head",
      "command": "after required PR 258 exact-head workflows and independent audit succeed, post one audit comment, create one inert attestation placeholder, then update that exact comment once to the canonical active MAINLINE_MERGE_APPROVAL_ATTESTATION bound to workflow run IDs and its own remote object ID",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "issue_comment_update", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250recovery.land_once",
      "command": "reobserve attestation, base, head, checks, mergeable state and review threads, then owner-controlled mark-ready and merge once with merge method merge and expected-head protection",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "mark_ready", "merge", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250recovery.post_merge_verify",
      "command": "verify PR 258 merged, origin/main equals mergeCommit.oid, and wait for exact main push CI, Model Access and State Gate SUCCESS without retroactively claiming PR 257 State Gate passed",
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr257_v1.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": ["project_state/decision_packet.md"],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/**"
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
    "runner_dispatch",
    "worktree_deletion"
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
    "github_issue_comment_allowed": true,
    "github_issue_comment_update_allowed": true,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".github/CODEOWNERS", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE250_MAIN_STATE_GATE_RECOVERED_GREEN_NO_RETROACTIVE_CLAIM",
  "blocked_terminal": "ISSUE250_STATE_GATE_RECOVERY_V1_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Restore a green main State Gate with a governance-only, correctly pre-attested landing. Preserve the historical truth that PR 257 merged with green CI but its push State Gate failed because the required structured pre-merge attestation was absent.

## Acceptance

1. Immutable Decision first locks exact main base `4b95cf719244f25f095a0936c7a97e44c57a0482`, PR 258 and merge method `merge`.
2. The PR 257 intent is archived and the PR 258 intent is bound to this Decision and committed Command Plan; no product/source/test/workflow content changes.
3. All PR 258 exact-head required workflows and a fresh independent audit succeed.
4. Before mark-ready or merge, one owner-authored structured active attestation comment binds exact workflow run IDs, base, head, intent digest, approval payload and its own remote comment ID.
5. Owner-controlled mark-ready and merge occur once with expected-head protection; exact merged-main CI, Model Access and State Gate succeed.
6. No result claims that PR 257's failed State Gate later passed, and no workflow rerun is dispatched.

## Execution policy

- Governance-only recovery; do not edit source, tests, workflows, frontend, docs or dependencies.
- Commit only the active Command Plan among generated gate artifacts.
- No provider/model/OpenCode/credential call, deployment, release, runner dispatch, direct-main push, history rewrite, auto-merge or cleanup.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue250_platform_v2_landing_r2_v9",
  "round_id": "round_20260819_issue250_platform_v2_landing_r2_v9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue250_platform_v2_landing_r2_v8",
  "follows_last_round_id": "round_20260819_issue250_platform_v2_landing_r2_v8",
  "previous_audit_outcome": "ISSUE250_V8_LANDING_NOT_PUBLISHED_MISSING_EXPLICIT_ALLOWED_MERGE_METHOD",
  "workstream_id": "issue250-platform-v2-landing-r2-v9",
  "source_issue": 250,
  "superseded_pr": 256,
  "active_pr": 257,
  "required_branch": "owner/issue250-platform-completion-v9-landing",
  "starting_head": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "activation_base_sha": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "integration_base_ref": "main",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "accepted_product_head": "58c1b0ec0be88ede995bddab1edca8051e126e64",
  "accepted_product_tree": "f81301b061c85f7f1b4fc605a2b59ee2629fe509",
  "accepted_audit_pr": 256,
  "accepted_audit_comment_id": 5339864239,
  "authority_and_product_worktree": "F:/reverse-agent-issue250-platform-completion-v9-landing",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "expected_pr_number": 257,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
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
    "git worktree add -b owner/issue250-platform-completion-v9-landing F:/reverse-agent-issue250-platform-completion-v9-landing 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
    "edit and commit only project_state/decision_packet.md as the immutable activation commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue250v9.verify_accepted_exact_head",
      "command": "verify PR 256 exact head/base, all required workflow SUCCESS, MERGEABLE/CLEAN, no review threads, and accepted audit comment 5339864239",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v9.bind_landing_authority",
      "command": "generate and commit the active Command Plan, archive PR 134 intent, and create PR 257 active merge intent bound to this immutable Decision and plan",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["generate_governance_artifact", "bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v9.reuse_exact_v7_product_commits",
      "command": "git cherry-pick 52eaf44c 9d1ef3ba 58c1b0ec",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit_replay"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v9.final_validation",
      "command": "prove product equivalence, run active merge-intent and landing tests, final transition lint/preflight, freshness and git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v9.publish_exact_draft_pr",
      "command": "push branch once, close PR 256, create exactly one Draft PR expected as 257, and stop if GitHub assigns another number",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_close", "pull_request_create", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250v9.accept_and_land",
      "command": "wait for all required PR 257 exact-head workflows, audit/comment exact head, reobserve base/head/checks/mergeable state, then owner-controlled mark-ready and merge once with merge method merge and expected-head protection",
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
      "command_id": "issue250v9.post_merge_verify",
      "command": "verify PR 257 merged, origin/main equals mergeCommit.oid, wait for main push checks, and close Issue 250 completed",
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
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/**",
    "reverse_agent/model_access/**",
    "reverse_agent/freshness.py",
    "tests/platform_v1/**",
    "tests/test_team_graph.py",
    "tests/test_freshness.py",
    "tests/test_mainline_landing.py",
    "tests/test_dev_up_contract.py",
    "frontend/**",
    "docs/architecture/**",
    "docs/roadmap/**",
    "README.md",
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1",
    "launch_reverse_agent.bat",
    "create_desktop_shortcut.ps1",
    "renovate.json",
    "governance/freshness-registry.json",
    ".github/CODEOWNERS",
    ".github/workflows/freshness.yml",
    ".gitignore",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
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
    "requirements*.txt",
    "pyproject.toml",
    ".github/workflows/state-gate.yml"
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
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".github/CODEOWNERS", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [".github/workflows/freshness.yml", ".github/CODEOWNERS"],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE250_PLATFORM_V2_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "blocked_terminal": "ISSUE250_V9_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the accepted Issue 250 Platform V2 product through a self-contained Path-B candidate whose Decision, Command Plan and active merge intent remain valid on merged `main`.

## Acceptance

1. Immutable Decision first after exact main base binds PR 257, accepted product head/tree, `allowed_merge_method=merge`, base, workflows and owner-controlled landing.
2. Prior PR 134 intent is archived; active intent matches this Decision and Command Plan before product replay.
3. Product blobs outside landing governance equal accepted v7.
4. PR 257 exact-head required workflows succeed and audit accepts with no review threads.
5. Owner-controlled mark-ready and merge occur once with expected-head protection; post-merge main checks succeed and Issue 250 closes.

## Execution policy

- No new source/test edits or dependency installs; replay accepted product commits exactly.
- Commit only the active Command Plan among generated gate artifacts.
- No provider/model/OpenCode/credential call, deployment, release, direct-main push, history rewrite, auto-merge or cleanup.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue250_ci_repair_r2_v7",
  "round_id": "round_20260819_issue250_ci_repair_r2_v7",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue250_ci_repair_r2_v6",
  "follows_last_round_id": "round_20260819_issue250_ci_repair_r2_v6",
  "previous_audit_outcome": "ISSUE250_V6_REMOTE_PREFLIGHT_BLOCKED_BY_REFERENCE_PATH_SCOPE_AND_ONE_MISSING_ALLOWED_TEST_PATH",
  "workstream_id": "issue250-ci-repair-r2-v7",
  "source_issue": 250,
  "superseded_pr": 255,
  "required_branch": "owner/issue250-platform-completion-v7",
  "starting_head": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "activation_base_sha": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "integration_base_ref": "main",
  "mainline_merge_intent_required": false,
  "authority_and_product_worktree": "F:/reverse-agent-issue250-platform-completion-v7",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "replacement_draft_pr_creation_limit": 1,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git worktree add -b owner/issue250-platform-completion-v7 F:/reverse-agent-issue250-platform-completion-v7 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
    "edit and commit only project_state/decision_packet.md as the immutable activation commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue250v7.verify_exact_state",
      "command": "verify origin/main equals 706991ad0cb826d7c963a8ddfb7e770e97cdf60b and record every PR 255 exact-head workflow conclusion and failed preflight path",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v7.bind_active_command_plan",
      "command": "generate the deterministic active command plan, stage only project_state/gates/command_plan.json, and commit it before product replay",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["generate_governance_artifact", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v7.reuse_exact_v6_product_commits",
      "command": "git cherry-pick ed81f24d 3de9730a 95bc4103",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit_replay"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v7.verify_product_tree_equivalence",
      "command": "prove every v7 product blob equals exact v6 head 95bc41037ced9fa4e86827c3aff4b5542d6cc076 outside the new Decision and Command Plan",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v7.affected_validation",
      "command": "run merge-intent, architecture-contract, mainline-landing and transition-preflight tests, then run final transition-lint and transition-preflight after product replay",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v7.repository_validation",
      "command": "reuse the tree-identical v6 full product evidence and run freshness, git diff --check, Decision immutability and exact final scope inspection",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v7.push_once",
      "command": "git push origin HEAD:refs/heads/owner/issue250-platform-completion-v7",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250v7.replace_draft_pr",
      "command": "close PR 255 as superseded, create one Draft PR from owner/issue250-platform-completion-v7 to main, and comment Issue 250",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_close", "pull_request_create", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "project_state/decision_packet.md"
  ],
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
    "merge",
    "mark_ready",
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
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "github_mark_ready_allowed": false,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".github/CODEOWNERS", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    ".github/workflows/freshness.yml",
    ".github/CODEOWNERS"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE250_V7_REPLACEMENT_DRAFT_PR_EXACT_HEAD_CI_READY",
  "blocked_terminal": "ISSUE250_V7_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Publish the exact already-verified Issue 250 v6 product tree under a corrected transition scope contract: mutable product paths are allowed paths, `reference_paths` remain read-only, and final preflight validates the fully replayed product rather than only the activation state.

## Acceptance

1. The Decision commit is first after the exact approved main base and remains immutable.
2. The matching active Command Plan is committed before the three exact v6 product commits are replayed.
3. Every product blob outside the new Decision and Command Plan is identical to exact v6 head `95bc41037ced9fa4e86827c3aff4b5542d6cc076`.
4. Final transition preflight after product replay reports `PRE_EXECUTION_AUTHORIZED` with no outside or reference-path violations.
5. One normal push publishes the branch; PR #255 is closed as superseded and exactly one replacement Draft PR is created.
6. Replacement exact-head GitHub Actions reach SUCCESS with no ready, merge, provider/model call, deployment, release, dependency install or cleanup.

## Execution policy

- No source or test edits are permitted; replay the exact v6 product commits only.
- The active Command Plan is the only generated gate artifact authorized for commit.
- Preserve unrelated worktrees and runtime directories until final cleanup after all goals land.

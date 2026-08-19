# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue250_ci_repair_r2_v6",
  "round_id": "round_20260819_issue250_ci_repair_r2_v6",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue250_ci_repair_r2_v5",
  "follows_last_round_id": "round_20260819_issue250_ci_repair_r2_v5",
  "previous_audit_outcome": "ISSUE250_V5_SUPERSEDED_BEFORE_PRODUCT_REPLAY_AFTER_V4_CI_REVEALED_TRUSTED_HOST_SOCKET_LEAK",
  "workstream_id": "issue250-ci-repair-r2-v6",
  "source_issue": 250,
  "superseded_pr": 254,
  "required_branch": "owner/issue250-platform-completion-v6",
  "starting_head": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "activation_base_sha": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "integration_base_ref": "main",
  "mainline_merge_intent_required": false,
  "authority_and_product_worktree": "F:/reverse-agent-issue250-platform-completion-v6",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "replacement_draft_pr_creation_limit": 1,
  "dependency_install_limit": 1,
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
    "git worktree add -b owner/issue250-platform-completion-v6 F:/reverse-agent-issue250-platform-completion-v6 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
    "edit and commit only project_state/decision_packet.md as the immutable activation commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue250v6.verify_exact_state",
      "command": "verify origin/main equals 706991ad0cb826d7c963a8ddfb7e770e97cdf60b and record every PR 254 exact-head workflow conclusion and failed assertion",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v6.bind_active_command_plan",
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
      "command_id": "issue250v6.reuse_exact_product_commits",
      "command": "git cherry-pick b80372c74fc3b5eea0cfd8bdb3491b638e2a2feb 58f1d2388b1d6393213a3640b10e91f4d95440fd",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit_replay"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250v6.close_trusted_host_sockets",
      "command": "use apply_patch to make CombinedTrustedHost.stop close every HTTP server socket after shutdown and add a deterministic same-port reuse regression test",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_edit", "bounded_test_contract_edit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.install_frontend_lockfile",
      "command": "npm ci --prefix frontend",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["dependency_install", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.frontend_validation",
      "command": "npm --prefix frontend run lint && npm --prefix frontend test -- --run && npm --prefix frontend run typecheck && npm --prefix frontend run build",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.backend_validation",
      "command": "python -m pytest tests/platform_v1/test_goal_service.py tests/platform_v1/test_autonomy.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_publication_controller.py tests/platform_v1/test_capability_registry.py tests/platform_v1/test_task_service.py tests/test_freshness.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.platform_validation",
      "command": "run the Issue 250 Platform blocking suite with the seven provider or historical-decision tests deselected exactly as CI",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.repository_validation",
      "command": "run the Issue 250 repository baseline suite, freshness check, transition-lint, git diff --check, and exact scope inspection",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250v6.commit_socket_repair",
      "command": "git add only reverse_agent/platform_v1/trusted_host.py tests/platform_v1/test_trusted_host.py and commit the verified socket lifecycle repair",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue250v6.push_once",
      "command": "git push origin HEAD:refs/heads/owner/issue250-platform-completion-v6",
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
      "command_id": "issue250v6.replace_draft_pr",
      "command": "close PR 254 as superseded, create one Draft PR from owner/issue250-platform-completion-v6 to main, and comment Issue 250",
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
    "project_state/decision_packet.md",
    "docs/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    ".github/**"
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
    "dependency_install_allowed": true,
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
  "success_terminal": "ISSUE250_V6_REPLACEMENT_DRAFT_PR_EXACT_HEAD_CI_READY",
  "blocked_terminal": "ISSUE250_V6_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Publish the verified Issue 250 Platform V2 product with a committed active Command Plan and a cross-platform Trusted Host shutdown contract that releases every bound server socket deterministically.

## Acceptance

1. The Decision commit is first after the exact approved main base and remains immutable.
2. The matching generated `project_state/gates/command_plan.json` is committed before the exact v4 product and CI-repair commits are replayed.
3. `CombinedTrustedHost.stop()` releases all model-control, task-API, and relay server sockets; a stopped host's exact ports can be rebound by a new host.
4. Local frontend, backend, Platform, repository, freshness, transition and diff checks pass on the final exact head.
5. One normal push publishes the branch; PR #254 is closed as superseded and exactly one replacement Draft PR is created.
6. Replacement exact-head GitHub Actions reach SUCCESS with no ready, merge, provider/model call, deployment, release or cleanup.

## Execution policy

- Use `apply_patch` for the Trusted Host source and regression-test edit.
- The active Command Plan is the only generated gate artifact authorized for commit in this round.
- No credentials or auth stores are read and no live provider/model/OpenCode call occurs.
- Preserve every unrelated worktree and runtime directory until the final cleanup authority after all goals land.

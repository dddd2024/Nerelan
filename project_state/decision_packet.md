# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue250_platform_completion_r2_v1",
  "round_id": "round_20260819_issue250_platform_completion_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue232_sprint_c_cutover_landing_r2_v2",
  "follows_last_round_id": "round_20260819_issue232_sprint_c_cutover_landing_r2_v2",
  "previous_audit_outcome": "ISSUE232_SPRINT_C_CUTOVER_LANDED_ON_MAIN_AND_REMOTE_VERIFIED",
  "workstream_id": "issue250-platform-completion-r2-v1",
  "source_issue": 250,
  "parent_issue": 148,
  "required_branch": "owner/issue250-platform-completion-r2-v1",
  "starting_head": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "activation_base_sha": "706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
  "integration_base_ref": "main",
  "authority_worktree": "F:/reverse-agent-issue250-platform-completion-r2-v1",
  "product_branch": "owner/issue250-platform-completion-v1",
  "product_worktree": "F:/reverse-agent-issue250-platform-completion-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 2,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "dependency_install_limit": 1,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-issue250-authority-publication-v1 fetch origin owner/issue250-platform-completion-r2-v1",
    "git -C F:/reverse-agent-issue250-authority-publication-v1 rev-parse origin/owner/issue250-platform-completion-r2-v1",
    "$b=(git -C F:/reverse-agent-issue250-authority-publication-v1 branch --list owner/issue250-platform-completion-r2-v1);if($b){'ISSUE250_AUTH_BRANCH_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue250-platform-completion-r2-v1'){'ISSUE250_AUTH_WORKTREE_EXISTS';exit 24};'ISSUE250_AUTH_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue250-authority-publication-v1 worktree add --track -b owner/issue250-platform-completion-r2-v1 F:/reverse-agent-issue250-platform-completion-r2-v1 origin/owner/issue250-platform-completion-r2-v1",
    "git -C F:/reverse-agent-issue250-platform-completion-r2-v1 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue250-platform-completion-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue250.verify_base",
      "command": "git fetch origin main; if((git rev-parse origin/main) -ne '706991ad0cb826d7c963a8ddfb7e770e97cdf60b'){exit 51};'ISSUE250_EXACT_BASE_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue250.create_clean_product_worktree",
      "command": "$b=(git branch --list owner/issue250-platform-completion-v1);if($b){exit 52};if(Test-Path -LiteralPath 'F:/reverse-agent-issue250-platform-completion-v1'){exit 53};git worktree add -b owner/issue250-platform-completion-v1 F:/reverse-agent-issue250-platform-completion-v1 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["branch_create", "worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.disable_product_sparse_checkout",
      "command": "git -C F:/reverse-agent-issue250-platform-completion-v1 sparse-checkout disable",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_prepare"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.install_frontend_lockfile",
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
      "command_id": "issue250.capture_current_frontend",
      "command": "build current mock frontend, start hidden loopback preview, capture current-run Chrome screenshots for home/tasks/settings, then stop only the exact owned process tree",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["visual_validation", "local_service_start", "local_service_stop"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.backend_focused_tests",
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
      "command_id": "issue250.frontend_tests",
      "command": "npm --prefix frontend test -- --run && npm --prefix frontend run typecheck && npm --prefix frontend run build",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.platform_blocking_tests",
      "command": "python -m pytest tests/platform_v1 -q --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_bytes_unchanged_since_commit --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_commit_precedes_implementation --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_single_decision_commit_in_range --deselect=tests/platform_v1/test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end --deselect=tests/platform_v1/test_task3c_v4_repairs.py::TestInstalledOpenCodeFakeProviderSmoke::test_installed_opencode_fake_provider_end_to_end --deselect=tests/platform_v1/test_task3c_v5_opencode_probe.py::TestDirectFakeProviderControl::test_opencode_direct_fake_provider --deselect=tests/platform_v1/test_task3c_v5_opencode_probe.py::TestRelayFakeProviderRun::test_opencode_relay_fake_provider",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.repository_baseline_tests",
      "command": "python -m pytest tests/test_project_gate.py tests/test_ci_responsibility.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_control_plane_transition.py tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py tests/test_supervisor_validate.py tests/test_repository_hygiene.py tests/test_codex_skills.py tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.final_scope_and_diff_check",
      "command": "git diff --check; git status --short; git diff --name-only 706991ad0cb826d7c963a8ddfb7e770e97cdf60b",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue250.commit_product",
      "command": "git add only Issue #250 authorized paths; git commit -m 'feat: complete unattended multi-agent platform'",
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
      "command_id": "issue250.push_product_once",
      "command": "git push origin HEAD:refs/heads/owner/issue250-platform-completion-v1",
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
      "command_id": "issue250.create_draft_pr",
      "command": "github connector create one Draft PR owner/issue250-platform-completion-v1 to main and comment issue 250",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_create", "issue_comment", "network_access"],
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
    "pyproject.toml"
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
    "github_issue_comment_allowed": true,
    "github_pr_creation_allowed": true,
    "github_mark_ready_allowed": false,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "success_terminal": "ISSUE250_PLATFORM_COMPLETION_DRAFT_PR_EXACT_HEAD_CI_READY",
  "blocked_terminal": "ISSUE250_PLATFORM_COMPLETION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Complete the provider-free product and UX implementation for a local-first unattended multi-Agent platform on a clean product branch, reusing the landed mature components and publishing one Draft PR for exact-head CI.

## Acceptance

1. Natural-language Goal -> Spec -> Plan -> Tasks artifacts are durable, inspectable, revisioned and launched through existing TaskStore/LangGraph/Binding paths.
2. Owner-activated autonomous windows enforce repository, capability, time, WIP and operation budgets outside model text; scheduler restart cannot duplicate accepted work.
3. Capability discovery, trusted Draft publication, sanitized telemetry/receipts and morning summaries are provider-free tested.
4. The frontend presents one simple GPT/OpenHands-style workspace backed by real APIs; typecheck/tests/build and current-run browser captures pass.
5. Renovate/freshness, launcher and architecture truth are current without introducing another control plane or database.
6. Existing Platform V1 and repository blocking suites pass; only authorized paths enter the clean product commit.
7. Exactly one normal product-branch push and one Draft PR occur; no merge, ready, live model/provider call, release, deploy or cleanup occurs.

## Execution policy

- Use `apply_patch` for repository edits and preserve all unrelated worktrees/runtime scratch.
- Frontend dependency installation follows the checked-in lockfile exactly and is limited to one `npm ci`.
- Product Design capture happens before frontend mutation; post-build visual verification happens after implementation.
- A fresh real-provider dogfood and final landing each require their own later exact authority.

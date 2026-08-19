# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue246_durable_resume_repair_r2_v1",
  "round_id": "round_20260819_issue246_durable_resume_repair_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue245_sprint_c_sequential_recovery_r3_v1",
  "follows_last_round_id": "round_20260819_issue245_sprint_c_sequential_recovery_r3_v1",
  "previous_audit_outcome": "ISSUE245_LIVE_ONCE_BLOCKED_BEFORE_REVIEWER_LAUNCH_PREPARED_CONTEXT_INCOMPLETE_NO_RETRY",
  "workstream_id": "issue246-durable-resume-repair-r2-v1",
  "source_issue": 246,
  "parent_issue": 245,
  "required_branch": "owner/issue246-durable-resume-repair-r2-v1",
  "starting_head": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "activation_base_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "integration_base_ref": "owner/repository-modernization-v2-planning",
  "canonical_planning_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "authority_worktree": "F:/reverse-agent-issue246-durable-resume-repair-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
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
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 fetch origin owner/issue246-durable-resume-repair-r2-v1",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 rev-parse origin/owner/issue246-durable-resume-repair-r2-v1",
    "$b=(git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 branch --list owner/issue246-durable-resume-repair-r2-v1);if($b){'ISSUE246_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue246-durable-resume-repair-r2-v1'){'ISSUE246_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE246_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 worktree add --track -b owner/issue246-durable-resume-repair-r2-v1 F:/reverse-agent-issue246-durable-resume-repair-r2-v1 origin/owner/issue246-durable-resume-repair-r2-v1",
    "git -C F:/reverse-agent-issue246-durable-resume-repair-r2-v1 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue246-durable-resume-repair-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue246.verify_exact_base",
      "command": "$local=(git rev-parse 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd);$merge=(git merge-base HEAD 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd);if($local -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd' -or $merge -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd'){exit 51};'ISSUE246_EXACT_BASE_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246.provider_free_regression",
      "command": "python -m pytest tests/test_team_graph.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task_service.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue246.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue246.verify_scope",
      "command": "$expected=@('reverse_agent/platform_v1/durable_execution.py','tests/platform_v1/test_durable_execution.py','tests/platform_v1/test_task_service.py');$actual=@(git diff --name-only 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd)|Sort-Object;if(Compare-Object ($expected|Sort-Object) $actual){exit 52};'ISSUE246_EXACT_SCOPE_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246.commit_exact",
      "command": "git add -- reverse_agent/platform_v1/durable_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task_service.py; git commit -m \"fix: reconstruct durable reviewer context\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_exact_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246.push_once",
      "command": "git push origin HEAD:refs/heads/owner/issue246-durable-resume-repair-r2-v1",
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
      "command_id": "issue246.create_draft_pr",
      "command": "github_connector create draft PR from owner/issue246-durable-resume-repair-r2-v1 to owner/repository-modernization-v2-planning",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_connector",
      "operations": ["pull_request_create", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246.final_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task_service.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/workflows/team_graph.py",
    "tests/test_team_graph.py",
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
    ".github/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/decision_packet.md",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
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
    "direct_push_main",
    "direct_push_integration_base",
    "second_product_commit",
    "second_push_attempt",
    "live_model_call",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "dependency_install",
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
    "github_issue_comment_allowed": true,
    "github_pr_creation_allowed": true,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "success_terminal": "ISSUE246_DURABLE_RESUME_REPAIR_CANDIDATE_PUBLISHED_FOR_EXACT_HEAD_CI",
  "blocked_terminal": "ISSUE246_DURABLE_RESUME_REPAIR_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Repair the `POST_CODER` durable resume path so a restarted host reconstructs the complete persisted OpenCode prepared context and launches only Reviewer.

## Acceptance

1. The complete prepared context is reconstructed from persisted run identity before Reviewer dispatch.
2. Planner and Coder are not replayed; Reviewer is invoked exactly once in provider-free regression.
3. Worktree, base SHA, execution ID, CLI identity, binding/policy, Coder snapshot and lease fencing remain fail-closed.
4. Pre-launch executor exceptions retain a bounded actionable classification/detail without raw provider output.
5. Required provider-free tests and `git diff --check` pass.
6. Exactly one product commit is pushed to the exact feature branch and one Draft PR is created.

## Execution policy

- No live model, OpenCode, provider, auth-store or credential access is permitted.
- Generated gate files are evidence only and must not be included in the product commit.
- Landing/merge requires a separate exact-head Decision after CI succeeds.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue246_durable_resume_clean_candidate_r2_v3",
  "round_id": "round_20260819_issue246_durable_resume_clean_candidate_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue246_durable_resume_repair_r2_v2",
  "follows_last_round_id": "round_20260819_issue246_durable_resume_repair_r2_v2",
  "previous_audit_outcome": "ISSUE246_V2_PRODUCT_TESTS_PASS_PR247_GOVERNANCE_CONTAMINATION_REQUIRES_CLEAN_CANDIDATE",
  "workstream_id": "issue246-durable-resume-clean-candidate-r2-v3",
  "source_issue": 246,
  "parent_issue": 245,
  "required_branch": "owner/issue246-durable-resume-clean-candidate-r2-v3",
  "starting_head": "75b3a842b4ff43d257331da133f7040e1c6810bf",
  "activation_base_sha": "75b3a842b4ff43d257331da133f7040e1c6810bf",
  "integration_base_ref": "owner/repository-modernization-v2-planning",
  "canonical_planning_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "authority_worktree": "F:/reverse-agent-issue246-durable-resume-clean-candidate-r2-v3",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "accepted_source_commit": "93fde56beb8c65b062d9ca3e373e2ea09b2b23b4",
  "accepted_source_parent": "75b3a842b4ff43d257331da133f7040e1c6810bf",
  "clean_candidate_branch": "owner/issue246-durable-resume-clean-candidate-v3",
  "clean_candidate_base_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "clean_candidate_commit_limit": 1,
  "superseded_pr": 247,
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
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 fetch origin owner/issue246-durable-resume-clean-candidate-r2-v3",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 rev-parse origin/owner/issue246-durable-resume-clean-candidate-r2-v3",
    "$b=(git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 branch --list owner/issue246-durable-resume-clean-candidate-r2-v3);if($b){'ISSUE246_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue246-durable-resume-clean-candidate-r2-v3'){'ISSUE246_V3_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE246_V3_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 worktree add --track -b owner/issue246-durable-resume-clean-candidate-r2-v3 F:/reverse-agent-issue246-durable-resume-clean-candidate-r2-v3 origin/owner/issue246-durable-resume-clean-candidate-r2-v3",
    "git -C F:/reverse-agent-issue246-durable-resume-clean-candidate-r2-v3 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue246-durable-resume-clean-candidate-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD 75b3a842b4ff43d257331da133f7040e1c6810bf",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue246v3.verify_inputs",
      "command": "$authority=(git rev-parse HEAD);$source=(git rev-parse 93fde56beb8c65b062d9ca3e373e2ea09b2b23b4);$base=(git rev-parse 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd);if($authority -eq '' -or $source -ne '93fde56beb8c65b062d9ca3e373e2ea09b2b23b4' -or $base -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd'){exit 51};'ISSUE246_V3_INPUTS_VERIFIED'",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v3.create_clean_candidate",
      "command": "$branch='owner/issue246-durable-resume-clean-candidate-v3';$path='F:/reverse-agent-issue246-durable-resume-clean-candidate-v3';if(git branch --list $branch){exit 52};if(Test-Path -LiteralPath $path){exit 53};git worktree add -b $branch $path 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync", "worktree_create"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v3.replay_exact_product_commit",
      "command": "git -C F:/reverse-agent-issue246-durable-resume-clean-candidate-v3 cherry-pick 93fde56beb8c65b062d9ca3e373e2ea09b2b23b4",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["exact_commit_replay", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v3.verify_clean_candidate",
      "command": "$p='F:/reverse-agent-issue246-durable-resume-clean-candidate-v3';$head=(git -C $p rev-parse HEAD);$parent=(git -C $p rev-parse HEAD^);$expected=@('reverse_agent/platform_v1/durable_execution.py','tests/platform_v1/test_durable_execution.py','tests/platform_v1/test_task_service.py');$actual=@(git -C $p diff --name-only 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd..HEAD)|Sort-Object;if($parent -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd' -or (Compare-Object ($expected|Sort-Object) $actual)){exit 54};foreach($x in $expected){$a=(git -C $p rev-parse ('HEAD:'+$x));$b=(git rev-parse ('93fde56beb8c65b062d9ca3e373e2ea09b2b23b4:'+$x));if($a -ne $b){exit 55}};Write-Output ('ISSUE246_V3_CLEAN_CANDIDATE='+$head)",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v3.provider_free_regression",
      "command": "Set-Location F:/reverse-agent-issue246-durable-resume-clean-candidate-v3; python -m pytest tests/test_team_graph.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task_service.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue246v3.ci_baseline_regression",
      "command": "Set-Location F:/reverse-agent-issue246-durable-resume-clean-candidate-v3; python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue246v3.diff_check",
      "command": "git -C F:/reverse-agent-issue246-durable-resume-clean-candidate-v3 diff --check 7d04395b0a67b86f6512b44c5cd3bc6009ca56fd..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue246v3.push_clean_candidate_once",
      "command": "git -C F:/reverse-agent-issue246-durable-resume-clean-candidate-v3 push origin HEAD:refs/heads/owner/issue246-durable-resume-clean-candidate-v3",
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
      "command_id": "issue246v3.create_clean_draft_pr",
      "command": "github connector create draft PR from owner/issue246-durable-resume-clean-candidate-v3 to owner/repository-modernization-v2-planning",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_create", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246v3.close_superseded_pr247",
      "command": "github connector close PR 247 after clean Draft PR creation",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
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
  "success_terminal": "ISSUE246_DURABLE_RESUME_CLEAN_CANDIDATE_PUBLISHED_FOR_EXACT_HEAD_CI",
  "blocked_terminal": "ISSUE246_DURABLE_RESUME_CLEAN_CANDIDATE_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Publish an exact clean candidate for the accepted `POST_CODER` durable resume repair without carrying transition-governance commits into the product PR.

## Acceptance

1. Clean candidate parent is the exact planning SHA `7d04395b...`.
2. Its only changed paths are the three accepted source/test paths, and each resulting blob equals source commit `93fde56b...`.
3. Provider-free recovery tests, HTTP routing test, CI governance baseline tests, and `git diff --check` pass in the clean candidate.
4. Exactly one clean candidate commit and one normal push are made; one replacement Draft PR is created.
5. PR #247 is closed only after the replacement Draft PR exists; it is never merged.

## Execution policy

- No live model, OpenCode, provider, auth-store or credential access is permitted.
- Generated gate files and the Decision remain on the separate authority branch and must not enter the clean candidate.
- Landing/merge requires a separate exact-head Decision after CI succeeds.

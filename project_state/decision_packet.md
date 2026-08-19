# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue246_clean_candidate_landing_r2_v5",
  "round_id": "round_20260819_issue246_clean_candidate_landing_r2_v5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue246_clean_candidate_publication_r2_v4",
  "follows_last_round_id": "round_20260819_issue246_clean_candidate_publication_r2_v4",
  "previous_audit_outcome": "ISSUE246_PR248_EXACT_HEAD_BASELINE_SUCCESS_CLEAN_CANDIDATE_READY_TO_LAND",
  "workstream_id": "issue246-clean-candidate-landing-r2-v5",
  "source_issue": 246,
  "parent_issue": 245,
  "required_branch": "owner/issue246-clean-candidate-landing-r2-v5",
  "starting_head": "4bd4bac4e7621c3b22b847432aab4fc2a8f11d73",
  "activation_base_sha": "4bd4bac4e7621c3b22b847432aab4fc2a8f11d73",
  "integration_base_ref": "owner/repository-modernization-v2-planning",
  "canonical_planning_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "authority_worktree": "F:/reverse-agent-issue246-clean-candidate-landing-r2-v5",
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
  "accepted_clean_candidate_sha": "221a5f7feb59441e84378edff4ae4d9619b24726",
  "bounded_history_deepen": 256,
  "superseded_pr": 247,
  "landing_pr": 248,
  "github_ci_run_id": 32217605241,
  "github_ci_job_id": 95961935888,
  "allowed_merge_method": "merge",
  "expected_pr_head": "221a5f7feb59441e84378edff4ae4d9619b24726",
  "expected_pr_base": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
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
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 fetch origin owner/issue246-clean-candidate-landing-r2-v5",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 rev-parse origin/owner/issue246-clean-candidate-landing-r2-v5",
    "$b=(git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 branch --list owner/issue246-clean-candidate-landing-r2-v5);if($b){'ISSUE246_V5_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue246-clean-candidate-landing-r2-v5'){'ISSUE246_V5_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE246_V5_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v1 worktree add --track -b owner/issue246-clean-candidate-landing-r2-v5 F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 origin/owner/issue246-clean-candidate-landing-r2-v5",
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue246-clean-candidate-landing-r2-v5",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD 4bd4bac4e7621c3b22b847432aab4fc2a8f11d73",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue246v5.fetch_landing_inputs",
      "command": "git fetch origin owner/repository-modernization-v2-planning owner/issue246-durable-resume-clean-candidate-v3",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v5.verify_candidate_and_pr",
      "command": "$base=(git rev-parse origin/owner/repository-modernization-v2-planning);$candidate=(git rev-parse origin/owner/issue246-durable-resume-clean-candidate-v3);$parent=(git rev-parse ($candidate+'^'));$j=(gh pr view 248 --repo dddd2024/reverse-agent --json state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid,mergeable,mergeStateStatus,statusCheckRollup|ConvertFrom-Json);$checks=@($j.statusCheckRollup);$baseline=@($checks|Where-Object{$_.workflowName -eq 'CI' -and $_.name -eq 'baseline' -and $_.conclusion -eq 'SUCCESS'});if($base -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd' -or $candidate -ne '221a5f7feb59441e84378edff4ae4d9619b24726' -or $parent -ne $base -or $j.state -ne 'OPEN' -or -not $j.isDraft -or $j.baseRefName -ne 'owner/repository-modernization-v2-planning' -or $j.baseRefOid -ne $base -or $j.headRefOid -ne $candidate -or $j.mergeable -ne 'MERGEABLE' -or $baseline.Count -ne 1){exit 51};'ISSUE246_V5_PR248_EXACT_HEAD_ACCEPTED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v5.verify_ci_run",
      "command": "$r=(gh run view 32217605241 --repo dddd2024/reverse-agent --json status,conclusion,headSha,jobs|ConvertFrom-Json);$job=@($r.jobs|Where-Object{$_.databaseId -eq 95961935888 -and $_.name -eq 'baseline' -and $_.conclusion -eq 'success'});if($r.status -ne 'completed' -or $r.conclusion -ne 'success' -or $r.headSha -ne '221a5f7feb59441e84378edff4ae4d9619b24726' -or $job.Count -ne 1){exit 52};'ISSUE246_V5_EXACT_CI_SUCCESS_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue246v5.remote_cas_reobserve",
      "command": "git fetch origin owner/repository-modernization-v2-planning; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};$remote=(git rev-parse origin/owner/repository-modernization-v2-planning);if($remote -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd'){exit 53};'ISSUE246_V5_REMOTE_CAS_MATCH'",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246v5.mark_ready",
      "command": "github connector mark PR 248 ready for review",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["mark_ready", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246v5.merge_expected_head",
      "command": "github connector merge PR 248 method merge expected_head 221a5f7feb59441e84378edff4ae4d9619b24726",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["merge", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246v5.post_merge_readback",
      "command": "$j=(gh pr view 248 --repo dddd2024/reverse-agent --json state,mergedAt,mergeCommit,headRefOid,baseRefName|ConvertFrom-Json);git fetch origin owner/repository-modernization-v2-planning;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};$remote=(git rev-parse origin/owner/repository-modernization-v2-planning);if($j.state -ne 'MERGED' -or $j.headRefOid -ne '221a5f7feb59441e84378edff4ae4d9619b24726' -or $j.mergeCommit.oid -ne $remote){exit 54};Write-Output ('ISSUE246_V5_MERGED='+$remote)",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue246v5.close_source_issue",
      "command": "github connector comment and close issue 246 as completed",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["issue_comment", "issue_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
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
    "reverse_agent/**",
    "tests/**",
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
    "github_pr_creation_allowed": false,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "success_terminal": "ISSUE246_DURABLE_RESUME_REPAIR_LANDED_AND_REMOTE_VERIFIED",
  "blocked_terminal": "ISSUE246_DURABLE_RESUME_REPAIR_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land PR #248 by exact-head protected merge after re-observing the clean candidate, successful baseline, and unchanged planning base.

## Acceptance

1. PR #248 remains Draft, MERGEABLE, based on exact planning SHA `7d04395b...`, with exact head `221a5f7f...`.
2. GitHub CI run `32217605241`, job `95961935888`, is successful on that exact head.
3. Remote planning CAS is re-observed immediately before publication and remains `7d04395b...`.
4. The PR is marked ready and merged with method `merge` and expected-head protection.
5. Post-merge PR and remote planning readback agree on the merge commit; issue #246 is then closed completed.

## Execution policy

- No live model, OpenCode, provider, auth-store or credential access is permitted.
- No repository product, test, workflow, documentation, package, candidate branch, or planning branch direct-push mutation is permitted.
- Only PR #248 mark-ready/merge, post-merge readback, and issue #246 bookkeeping are authorized publication actions.

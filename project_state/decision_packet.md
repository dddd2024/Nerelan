# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue232_sprint_c_cutover_landing_r2_v2",
  "round_id": "round_20260819_issue232_sprint_c_cutover_landing_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue232_sprint_c_cutover_r2_v1",
  "follows_last_round_id": "round_20260819_issue232_sprint_c_cutover_r2_v1",
  "previous_audit_outcome": "ISSUE232_SPRINT_C_CUTOVER_PR249_EXACT_HEAD_CI_SUCCESS",
  "workstream_id": "issue232-sprint-c-cutover-landing-r2-v2",
  "source_issue": 232,
  "parent_issue": 148,
  "related_issue": 245,
  "required_branch": "owner/issue232-sprint-c-cutover-landing-r2-v2",
  "starting_head": "b93daf9743f30028e98c38891edcca134772a541",
  "activation_base_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "integration_base_ref": "main",
  "canonical_planning_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "main_before_sha": "d0bae01eec2f9c20bad4c4beb46de9791e42cbcb",
  "authority_worktree": "F:/reverse-agent-issue232-sprint-c-cutover-landing-r2-v2",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_publication": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "landing_pr": 249,
  "github_ci_run_id": 32219501000,
  "github_ci_job_id": 95967212406,
  "known_nonrequired_state_gate_run_id": 32219500946,
  "known_nonrequired_state_gate_failure": "snapshot_missing",
  "allowed_merge_method": "merge",
  "expected_pr_head": "b93daf9743f30028e98c38891edcca134772a541",
  "expected_pr_base": "d0bae01eec2f9c20bad4c4beb46de9791e42cbcb",
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
    "git -C F:/reverse-agent-issue232-cutover-landing-authority-publication-v2 fetch origin owner/issue232-sprint-c-cutover-landing-r2-v2",
    "git -C F:/reverse-agent-issue232-cutover-landing-authority-publication-v2 rev-parse origin/owner/issue232-sprint-c-cutover-landing-r2-v2",
    "$b=(git -C F:/reverse-agent-issue232-cutover-landing-authority-publication-v2 branch --list owner/issue232-sprint-c-cutover-landing-r2-v2);if($b){'ISSUE232_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue232-sprint-c-cutover-landing-r2-v2'){'ISSUE232_V2_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE232_V2_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue232-cutover-landing-authority-publication-v2 worktree add --track -b owner/issue232-sprint-c-cutover-landing-r2-v2 F:/reverse-agent-issue232-sprint-c-cutover-landing-r2-v2 origin/owner/issue232-sprint-c-cutover-landing-r2-v2",
    "git -C F:/reverse-agent-issue232-sprint-c-cutover-landing-r2-v2 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue232-sprint-c-cutover-landing-r2-v2",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD b93daf9743f30028e98c38891edcca134772a541",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue232v2.fetch_landing_inputs",
      "command": "git fetch origin main owner/repository-modernization-v2-planning",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue232v2.verify_pr_and_required_checks",
      "command": "$main=(git rev-parse origin/main);$planning=(git rev-parse origin/owner/repository-modernization-v2-planning);$j=(gh pr view 249 --repo dddd2024/reverse-agent --json state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid,mergeable,mergeStateStatus,statusCheckRollup|ConvertFrom-Json);$checks=@($j.statusCheckRollup);$baseline=@($checks|Where-Object{$_.workflowName -eq 'CI' -and $_.name -eq 'baseline' -and $_.conclusion -eq 'SUCCESS'});$preflight=@($checks|Where-Object{$_.workflowName -eq 'Decision Preflight' -and $_.name -eq 'decision-preflight' -and $_.conclusion -eq 'SUCCESS'});$model=@($checks|Where-Object{$_.workflowName -eq 'Model Access' -and $_.name -eq 'verify' -and $_.conclusion -eq 'SUCCESS'});if($main -ne 'd0bae01eec2f9c20bad4c4beb46de9791e42cbcb' -or $planning -ne 'b93daf9743f30028e98c38891edcca134772a541' -or $j.state -ne 'OPEN' -or -not $j.isDraft -or $j.baseRefName -ne 'main' -or $j.baseRefOid -ne $main -or $j.headRefName -ne 'owner/repository-modernization-v2-planning' -or $j.headRefOid -ne $planning -or $j.mergeable -ne 'MERGEABLE' -or $baseline.Count -ne 1 -or $preflight.Count -ne 1 -or $model.Count -ne 1){exit 51};'ISSUE232_V2_PR249_EXACT_HEAD_ACCEPTED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue232v2.verify_baseline_run",
      "command": "$r=(gh run view 32219501000 --repo dddd2024/reverse-agent --json status,conclusion,headSha,jobs|ConvertFrom-Json);$job=@($r.jobs|Where-Object{$_.databaseId -eq 95967212406 -and $_.name -eq 'baseline' -and $_.conclusion -eq 'success'});if($r.status -ne 'completed' -or $r.conclusion -ne 'success' -or $r.headSha -ne 'b93daf9743f30028e98c38891edcca134772a541' -or $job.Count -ne 1){exit 52};'ISSUE232_V2_EXACT_CI_SUCCESS_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue232v2.verify_nonrequired_state_gate_diagnosis",
      "command": "$r=(gh run view 32219500946 --repo dddd2024/reverse-agent --json status,conclusion,headSha,jobs|ConvertFrom-Json);$log=(gh run view 32219500946 --repo dddd2024/reverse-agent --log-failed|Out-String);$job=@($r.jobs|Where-Object{$_.name -eq 'state-gate' -and $_.conclusion -eq 'failure'});if($r.status -ne 'completed' -or $r.conclusion -ne 'failure' -or $r.headSha -ne 'b93daf9743f30028e98c38891edcca134772a541' -or $job.Count -ne 1 -or $log -notmatch 'snapshot_missing'){exit 53};'ISSUE232_V2_NONREQUIRED_PATH_A_ROUTING_FAILURE_CONFIRMED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue232v2.remote_cas_reobserve",
      "command": "git fetch origin main owner/repository-modernization-v2-planning;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};$main=(git rev-parse origin/main);$planning=(git rev-parse origin/owner/repository-modernization-v2-planning);if($main -ne 'd0bae01eec2f9c20bad4c4beb46de9791e42cbcb' -or $planning -ne 'b93daf9743f30028e98c38891edcca134772a541'){exit 54};'ISSUE232_V2_REMOTE_CAS_MATCH'",
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
      "command_id": "issue232v2.mark_ready",
      "command": "github connector mark PR 249 ready for review",
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
      "command_id": "issue232v2.merge_expected_head",
      "command": "github connector merge PR 249 method merge expected_head b93daf9743f30028e98c38891edcca134772a541",
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
      "command_id": "issue232v2.post_merge_readback",
      "command": "$j=(gh pr view 249 --repo dddd2024/reverse-agent --json state,mergedAt,mergeCommit,headRefOid,baseRefName|ConvertFrom-Json);git fetch origin main;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};$remote=(git rev-parse origin/main);if($j.state -ne 'MERGED' -or $j.headRefOid -ne 'b93daf9743f30028e98c38891edcca134772a541' -or $j.baseRefName -ne 'main' -or $j.mergeCommit.oid -ne $remote){exit 55};Write-Output ('ISSUE232_V2_MAIN_MERGED='+$remote)",
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
      "command_id": "issue232v2.close_source_issue",
      "command": "github connector comment and close issue 232 as completed",
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
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "docs/**",
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
    "direct_push_planning",
    "product_or_test_mutation",
    "second_merge_attempt",
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
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": false,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "success_terminal": "ISSUE232_SPRINT_C_CUTOVER_LANDED_ON_MAIN_AND_REMOTE_VERIFIED",
  "blocked_terminal": "ISSUE232_SPRINT_C_CUTOVER_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land PR #249 by exact-head protected merge after re-observing successful required CI and unchanged `main` / planning refs.

## Acceptance

1. PR #249 remains Draft and MERGEABLE with exact head `b93daf97...` and exact base `d0bae01e...`.
2. Required `baseline` run `32219501000`, job `95967212406`, is successful on the exact head; Decision Preflight and Model Access verification are also successful.
3. The non-required State Gate failure is independently confirmed as the known Path-A routing mismatch `snapshot_missing`, not a product/test failure.
4. Remote `main` and planning CAS values are re-observed unchanged immediately before publication.
5. The PR is marked ready and merged with method `merge` and expected-head protection.
6. Post-merge PR and remote `main` readback agree on the merge commit; issue #232 is then closed completed.

## Execution policy

- No product, test, workflow, documentation, package, planning branch, or `main` direct-push mutation is permitted.
- No live model, OpenCode, provider, credential, dependency, release, deployment, or worktree-cleanup action is permitted.
- Only PR #249 mark-ready/merge, exact post-merge readback, and issue #232 bookkeeping are authorized publication actions.

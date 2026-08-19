# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue232_sprint_c_cutover_r2_v1",
  "round_id": "round_20260819_issue232_sprint_c_cutover_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue245_sprint_c_sequential_recovery_r3_v2",
  "follows_last_round_id": "round_20260819_issue245_sprint_c_sequential_recovery_r3_v2",
  "previous_audit_outcome": "SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_ACCEPTED_ONE_TASK_THREE_ROLE_CALLS",
  "workstream_id": "issue232-sprint-c-cutover-r2-v1",
  "source_issue": 232,
  "related_issue": 245,
  "parent_issue": 233,
  "required_branch": "owner/issue232-sprint-c-cutover-r2-v1",
  "starting_head": "b93daf9743f30028e98c38891edcca134772a541",
  "activation_base_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "authority_worktree": "F:/reverse-agent-issue232-sprint-c-cutover-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_publication": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "canonical_planning_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "main_before_sha": "d0bae01eec2f9c20bad4c4beb46de9791e42cbcb",
  "main_only_commit_count": 2,
  "planning_only_commit_count": 60,
  "cutover_pr_creation_limit": 1,
  "cutover_pr_head": "owner/repository-modernization-v2-planning",
  "cutover_pr_base": "main",
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 fetch origin owner/issue232-sprint-c-cutover-r2-v1",
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 rev-parse origin/owner/issue232-sprint-c-cutover-r2-v1",
    "$b=(git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 branch --list owner/issue232-sprint-c-cutover-r2-v1);if($b){'ISSUE232_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue232-sprint-c-cutover-r2-v1'){'ISSUE232_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE232_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 worktree add --track -b owner/issue232-sprint-c-cutover-r2-v1 F:/reverse-agent-issue232-sprint-c-cutover-r2-v1 origin/owner/issue232-sprint-c-cutover-r2-v1",
    "git -C F:/reverse-agent-issue232-sprint-c-cutover-r2-v1 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue232-sprint-c-cutover-r2-v1",
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
      "command_id": "issue232.verify_sprint_c_evidence",
      "command": "python -c \"import json,pathlib;d=json.loads(pathlib.Path(r'F:\\\\reverse-agent-issue245-sequential-team-live-v2\\\\evidence.json').read_text(encoding='utf-8'));assert d.get('accepted') is True and d.get('status')=='SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_ACCEPTED';assert d.get('checkpoint_before')=='POST_CODER' and d.get('checkpoint_after')=='POST_VALIDATION';assert d.get('model_invocations_before_interrupt')==2 and d.get('startup_model_invocations')==0 and d.get('model_invocations_after_resume')==3;assert d.get('reviewer_only_on_resume') is True and d.get('identity_preserved') is True and d.get('stale_epoch_write_rejected') is True;assert d.get('terminal_status')=='READY_FOR_REVIEW' and d.get('validation_exit_code')==0 and d.get('semantic_validation_exit_code')==0;assert d.get('product_setup_stat_before')==d.get('product_setup_stat_after') and d.get('forbidden_task_store_stat_before')==d.get('forbidden_task_store_stat_after');print('ISSUE232_SPRINT_C_LIVE_EVIDENCE_ACCEPTED')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue232.fetch_cutover_refs",
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
      "command_id": "issue232.verify_cutover_shape",
      "command": "$main=(git rev-parse origin/main);$planning=(git rev-parse origin/owner/repository-modernization-v2-planning);$base=(git merge-base $main $planning);$ahead=(git rev-list --count ($main+'..'+$planning));$behind=(git rev-list --count ($planning+'..'+$main));$preview=(git merge-tree $base $main $planning|Out-String);if($main -ne 'd0bae01eec2f9c20bad4c4beb46de9791e42cbcb' -or $planning -ne 'b93daf9743f30028e98c38891edcca134772a541' -or [int]$ahead -ne 60 -or [int]$behind -ne 2 -or $preview -match '<<<<<<<' -or $preview -match 'changed in both' -or $preview -match 'added in both'){exit 51};'ISSUE232_CUTOVER_SHAPE_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue232.close_issue245",
      "command": "github connector comment accepted live evidence and close issue 245 completed",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["issue_comment", "issue_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue232.create_cutover_draft_pr",
      "command": "github connector create Draft PR owner/repository-modernization-v2-planning to main",
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
      "command_id": "issue232.comment_cutover",
      "command": "github connector comment issue 232 with live evidence and cutover Draft PR",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["issue_comment", "network_access"],
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
    "README.md",
    "docs/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
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
    ".github/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "docs/**",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "product_or_test_mutation",
    "merge",
    "mark_ready",
    "auto_merge",
    "push",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "model_api_invocation",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "dependency_install",
    "tag_or_release",
    "deployment",
    "worktree_deletion"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "github_issue_comment_allowed": true,
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": true,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "success_terminal": "ISSUE232_SPRINT_C_CUTOVER_DRAFT_PR_CREATED_FOR_EXACT_HEAD_CI",
  "blocked_terminal": "ISSUE232_SPRINT_C_CUTOVER_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Close the successful live recovery Work Item and create the explicit planning-to-main cutover Draft PR without mutating either protected branch.

## Acceptance

1. The one-shot Sprint C evidence proves three roles, POST_CODER interruption, Reviewer-only recovery, fencing and validation success, with real runtime files unchanged.
2. Remote main is exactly `d0bae01e...`; planning is exactly `b93daf97...`, 60 commits ahead and 2 behind.
3. Deterministic merge preview reports no content conflict.
4. Issue #245 is commented and closed completed.
5. One Draft PR is created from the exact planning branch to `main`; issue #232 records it.
6. No branch push, product/test/docs/workflow/package mutation, mark-ready, or merge occurs.

## Execution policy

- This Decision creates the cutover PR only. Exact-head CI and a separate landing Decision are required before merge.
- No new model/provider call is allowed.

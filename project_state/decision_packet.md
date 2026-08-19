# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue233_sprint_b4_github_ruleset_r2_v1",
  "round_id": "round_20260819_issue233_sprint_b4_github_ruleset_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue240_sprint_b1_owner_clean_landing_r2_v2",
  "follows_last_round_id": "round_20260819_issue240_sprint_b1_owner_clean_landing_r2_v2",
  "previous_audit_outcome": "ISSUE240_SPRINT_B1_OWNER_CLEAN_LANDED_AND_REMOTE_VERIFIED",
  "workstream_id": "issue233-sprint-b4-github-ruleset-r2-v1",
  "source_issue": 233,
  "parent_issue": 148,
  "required_branch": "owner/issue233-sprint-b4-github-ruleset-r2-v1",
  "starting_head": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "activation_base_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "authority_worktree": "F:/reverse-agent-issue233-sprint-b4-github-ruleset-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_external_mutation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "repository": "dddd2024/reverse-agent",
  "canonical_planning_ref": "refs/heads/owner/repository-modernization-v2-planning",
  "canonical_expected_sha": "7d04395b0a67b86f6512b44c5cd3bc6009ca56fd",
  "ruleset_name": "reverse-agent protected integration v1",
  "ruleset_target_refs": ["refs/heads/main", "refs/heads/owner/repository-modernization-v2-planning"],
  "required_status_check": "baseline",
  "github_owner_login": "dddd2024",
  "github_owner_actor_id": 206685950,
  "github_owner_bypass_mode": "always",
  "ruleset_create_attempt_limit": 1,
  "ruleset_update_or_delete_forbidden": true,
  "raw_credential_read_forbidden": true,
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v7 status --short",
    "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v7 fetch origin owner/issue233-sprint-b4-github-ruleset-r2-v1",
    "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v7 rev-parse origin/owner/issue233-sprint-b4-github-ruleset-r2-v1",
    "$b=(git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v7 branch --list owner/issue233-sprint-b4-github-ruleset-r2-v1);if($b){'ISSUE233_B4_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue233-sprint-b4-github-ruleset-r2-v1'){'ISSUE233_B4_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE233_B4_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v7 worktree add --track -b owner/issue233-sprint-b4-github-ruleset-r2-v1 F:/reverse-agent-issue233-sprint-b4-github-ruleset-r2-v1 origin/owner/issue233-sprint-b4-github-ruleset-r2-v1",
    "git -C F:/reverse-agent-issue233-sprint-b4-github-ruleset-r2-v1 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue233-sprint-b4-github-ruleset-r2-v1",
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
      "command_id": "issue233b4.fetch_canonical",
      "command": "git fetch origin owner/repository-modernization-v2-planning",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue233b4.verify_preconditions",
      "command": "$canonical=(git rev-parse origin/owner/repository-modernization-v2-planning);if($canonical -ne '7d04395b0a67b86f6512b44c5cd3bc6009ca56fd'){Write-Output ('CANONICAL_DRIFT='+$canonical);exit 51};$sets=@(gh api repos/dddd2024/reverse-agent/rulesets --paginate|ConvertFrom-Json);if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};if($sets.Count -ne 0){$sets|ConvertTo-Json -Depth 8;exit 52};$checks=(gh api repos/dddd2024/reverse-agent/commits/7d04395b0a67b86f6512b44c5cd3bc6009ca56fd/check-runs|ConvertFrom-Json).check_runs;$baseline=@($checks|Where-Object{$_.name -eq 'baseline' -and $_.conclusion -eq 'success' -and $_.app.slug -eq 'github-actions'});if($baseline.Count -ne 1){exit 53};'ISSUE233_B4_PRECONDITIONS_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue233b4.create_ruleset_once",
      "command": "$payload=@{name='reverse-agent protected integration v1';target='branch';enforcement='active';bypass_actors=@(@{actor_id=206685950;actor_type='User';bypass_mode='always'});conditions=@{ref_name=@{include=@('refs/heads/main','refs/heads/owner/repository-modernization-v2-planning');exclude=@()}};rules=@(@{type='deletion'},@{type='non_fast_forward'},@{type='pull_request';parameters=@{dismiss_stale_reviews_on_push=$true;require_code_owner_review=$false;require_last_push_approval=$false;required_approving_review_count=0;required_review_thread_resolution=$true;allowed_merge_methods=@('merge')}},@{type='required_status_checks';parameters=@{strict_required_status_checks_policy=$false;do_not_enforce_on_create=$true;required_status_checks=@(@{context='baseline'})}})};$json=$payload|ConvertTo-Json -Depth 12 -Compress;$response=$json|gh api --method POST repos/dddd2024/reverse-agent/rulesets -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2026-03-10' --input -;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};$created=$response|ConvertFrom-Json;if($created.name -ne 'reverse-agent protected integration v1' -or $created.enforcement -ne 'active' -or $created.target -ne 'branch'){exit 54};Write-Output ('ISSUE233_B4_RULESET_CREATED_ID='+$created.id)",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["github_ruleset_mutation", "authenticated_github_admin", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue233b4.verify_ruleset_exact",
      "command": "$sets=@(gh api repos/dddd2024/reverse-agent/rulesets --paginate|ConvertFrom-Json);$match=@($sets|Where-Object{$_.name -eq 'reverse-agent protected integration v1'});if($match.Count -ne 1){exit 55};$full=gh api ('repos/dddd2024/reverse-agent/rulesets/'+$match[0].id) -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2026-03-10'|ConvertFrom-Json;$expectedRefs=@('refs/heads/main','refs/heads/owner/repository-modernization-v2-planning')|Sort-Object;$actualRefs=@($full.conditions.ref_name.include)|Sort-Object;$expectedTypes=@('deletion','non_fast_forward','pull_request','required_status_checks')|Sort-Object;$actualTypes=@($full.rules.type)|Sort-Object;$bypass=@($full.bypass_actors);$pr=@($full.rules|Where-Object{$_.type -eq 'pull_request'})[0];$status=@($full.rules|Where-Object{$_.type -eq 'required_status_checks'})[0];$contexts=@($status.parameters.required_status_checks.context);if($full.enforcement -ne 'active' -or $full.target -ne 'branch' -or (Compare-Object $expectedRefs $actualRefs) -or $full.conditions.ref_name.exclude.Count -ne 0 -or (Compare-Object $expectedTypes $actualTypes) -or $bypass.Count -ne 1 -or [int64]$bypass[0].actor_id -ne 206685950 -or $bypass[0].actor_type -ne 'User' -or $bypass[0].bypass_mode -ne 'always' -or $pr.parameters.dismiss_stale_reviews_on_push -ne $true -or $pr.parameters.require_code_owner_review -ne $false -or $pr.parameters.require_last_push_approval -ne $false -or [int]$pr.parameters.required_approving_review_count -ne 0 -or $pr.parameters.required_review_thread_resolution -ne $true -or @($pr.parameters.allowed_merge_methods).Count -ne 1 -or $pr.parameters.allowed_merge_methods[0] -ne 'merge' -or $status.parameters.strict_required_status_checks_policy -ne $false -or $status.parameters.do_not_enforce_on_create -ne $true -or $contexts.Count -ne 1 -or $contexts[0] -ne 'baseline'){exit 56};Write-Output ('ISSUE233_B4_RULESET_EXACT_ID='+$full.id)",
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
      "command_id": "issue233b4.verify_effective_branch_rules",
      "command": "$main=@(gh api repos/dddd2024/reverse-agent/rules/branches/main|ConvertFrom-Json);$planning=@(gh api repos/dddd2024/reverse-agent/rules/branches/owner%2Frepository-modernization-v2-planning|ConvertFrom-Json);$expected=@('deletion','non_fast_forward','pull_request','required_status_checks')|Sort-Object;$mainTypes=@($main.type)|Sort-Object;$planningTypes=@($planning.type)|Sort-Object;if(Compare-Object $expected $mainTypes){exit 57};if(Compare-Object $expected $planningTypes){exit 58};'ISSUE233_B4_EFFECTIVE_BRANCH_RULES_VERIFIED'",
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
      "command_id": "issue233b4.final_status",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "docs/roadmap/modernization_v2/SPRINT_B_GOVERNANCE_CI_PLAN.md",
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
    "product_or_test_mutation",
    "ruleset_update",
    "ruleset_delete",
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
    "tag_or_release",
    "deployment",
    "opencode_invocation",
    "model_api_invocation",
    "provider_network_call",
    "raw_credential_read",
    "credential_publication",
    "dependency_install"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "credential_value_access_allowed": false,
    "live_provider_access_allowed": false,
    "github_authenticated_admin_session_allowed": true,
    "github_ruleset_create_allowed": true,
    "github_ruleset_update_allowed": false,
    "github_ruleset_delete_allowed": false,
    "github_merge_allowed": false
  },
  "success_terminal": "ISSUE233_SPRINT_B4_GITHUB_RULESET_ACTIVE_AND_VERIFIED",
  "blocked_terminal": "ISSUE233_SPRINT_B4_GITHUB_RULESET_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Apply the smallest GitHub-native branch ruleset that protects both the current effective integration branch and `main` while preserving a single-Owner emergency path with audit visibility.

```text
refs/heads/main
refs/heads/owner/repository-modernization-v2-planning
  -> deletion blocked
  -> force push blocked
  -> changes require an associated pull request
  -> allowed merge method: merge
  -> required review thread resolution
  -> required GitHub Actions check: baseline
  -> Owner user 206685950 may bypass with bypass_mode=always
```

Zero required approvals is intentional for this personal, single-Owner repository. It still requires a PR and deterministic CI without creating an impossible second-human approval dependency. The named Owner bypass is the explicit emergency exception and remains visible in GitHub's ruleset/audit surface.

## Acceptance

1. The Decision commit is the only committed file change on the authority branch and precedes every external mutation.
2. Standard transition gates return `PRE_EXECUTION_AUTHORIZED` with no blocking reason.
3. Immediately before mutation, canonical planning is the exact expected SHA, repository rulesets are empty, and that SHA has one successful GitHub Actions `baseline` check.
4. Exactly one ruleset create request is attempted; update, delete, and retry are forbidden.
5. Exact ruleset and effective-rule readback succeeds for both target branches.
6. No product/test/docs/workflow/package mutation; no model/provider/OpenCode/Codex/OpenHands/API experiment; no raw credential read.

```text
ISSUE233_SPRINT_B4_GITHUB_RULESET_ACTIVE_AND_VERIFIED
```

## Execution policy

- Use the authenticated Owner-controlled `gh` session only for the exact REST calls in the generated plan; never display or read its raw token.
- Any precondition, API, or readback mismatch is a hard stop. Do not repair a partially created ruleset in this authority.
- No branch, PR, merge, release, deployment, product, provider, or dependency mutation is authorized.

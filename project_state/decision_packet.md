# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_pr146_stale_local_candidate_reconcile_v26",
  "round_id": "round_20260809_pr146_stale_local_candidate_reconcile_v26",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_pr146_stale_local_candidate_reconcile_v25",
  "follows_last_round_id": "round_20260809_pr146_stale_local_candidate_reconcile_v25",
  "previous_audit_outcome": "V25_OWNER_PREDELEGATION_SUPERSEDED_BEFORE_EXECUTION_DUE_TO_DECISION_CONTENT_DRIFT",
  "source_issue": 136,
  "parent_issue": 127,
  "active_pr": 146,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_remote_head": "9c6d6987d5e13c8a0ed92aef8bd9dcd4caf191b6",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "accepted_stage_b_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "stale_candidate_reconciliation_contract": {
    "expected_local_head": "0befedf8b4b912c9cd29a11e2717abe8795aa9ca",
    "expected_local_parent": "cd8cc3e3e10e961fc22fe0400a262760507ada57",
    "expected_subject": "landing: bind PR146 v24 intent",
    "expected_commit_paths": [
      "project_state/mainline_merge_intents/active.json",
      "project_state/mainline_merge_intents/archive/pr134_v1.json",
      "project_state/gates/bootstrap_state.json",
      "project_state/gates/command_plan.json",
      "project_state/gates/startup_snapshot.json",
      "project_state/gates/transition_command_plan_preview.json",
      "project_state/gates/transition_preflight_result.json"
    ],
    "tracked_worktree_must_be_clean_before_reset": true,
    "index_must_be_clean_before_reset": true,
    "reset_target_must_equal_current_remote_authority_head": true,
    "single_reset_allowed": true,
    "reset_command": "git reset --hard origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "post_reset_stop_required": true
  },
  "preexisting_carryover_contract": {
    "kernel_followup_issue": 147,
    "paths": [".frontend_stage/**", ".platform_v1_runtime/**"],
    "decision_scope_only": true,
    "must_not_be_staged": true,
    "must_not_be_cleaned_or_stashed": true,
    "must_not_be_deleted": true
  },
  "owner_landing_contract": {
    "pr": 146,
    "base_branch": "main",
    "expected_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "head_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
    "draft_until_final_audit": true,
    "owner_only_ready_and_merge": true,
    "merge_method": "merge",
    "auto_merge_forbidden": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin main",
    "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git show -s --format=%s HEAD",
    "git diff-tree --no-commit-id --name-only -r HEAD",
    "git diff --exit-code",
    "git diff --cached --exit-code",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "git show origin/owner/issue136-agent-canvas-reuse-spike-v2:project_state/decision_packet.md",
    "git reset --hard origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "validation.reconciled_head",
      "command": "git rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "exact_head_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "validation.reconciled_tracked_clean",
      "command": "git diff --exit-code",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.reconciled_index_clean",
      "command": "git diff --cached --exit-code",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.final_status",
      "command": "git status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".frontend_stage/**",
    ".platform_v1_runtime/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/schemas/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "cherry_pick",
    "stash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": ".github/**", "minimum_risk": "R3"},
    {"pattern": "reverse_agent/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R2"}
  ],
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "runner_managed_artifact_paths": [
    "project_state/gates/evidence/**",
    "project_state/gates/execution_log.json"
  ]
}
```

## Owner audit and execution policy

v26 supersedes v25 before any local delegation. v25 was never executed. During Owner predelegation self-audit, the first v25 commit contained an unsupported explanatory capability-policy field and a follow-up commit changed the same Decision ID's content; even though the parser would ignore the extra field, that content drift violates the project's immutable-Decision discipline. v26 re-establishes one immutable authority object.

v26 exists only to reconcile one known unpublished local v24 candidate commit after the local Agent correctly stopped because local HEAD was one commit ahead of the canonical remote authority.

The unpublished commit `0befedf8b4b912c9cd29a11e2717abe8795aa9ca` is not present on GitHub. Before reset, the local Agent must prove all of the following: local HEAD is exactly that SHA; its parent is exactly v24 `cd8cc3e3e10e961fc22fe0400a262760507ada57`; its subject is exactly `landing: bind PR146 v24 intent`; its committed paths are exactly the seven governance paths listed in the reconciliation contract; tracked worktree and index are clean; remote `main` remains `dd4cb074ab5b9baacf300706878b29bd745f12c3`; and the target remote branch equals the v26 authority fetched from GitHub.

Only after every precondition passes is exactly one destructive operation authorized: `git reset --hard origin/owner/issue136-agent-canvas-reuse-spike-v2`. This reset intentionally discards only the verified unpublished stale candidate and advances the local checkout onto v26. It does not authorize `git clean`, stash, rebase, amend, cherry-pick, force push, or deletion of the pre-existing untracked `.frontend_stage/**` / `.platform_v1_runtime/**` carryover.

After reset, regenerate the standard transition artifacts, require transition lint PASS and `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, run the four read-only reconciliation validations, then STOP. Do not perform PR146 landing preparation under v26. Owner will issue a fresh landing Decision after successful reconciliation.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260823_issue320_state_gate_reachability_r2_v2",
  "round_id": "round_20260823_issue320_state_gate_reachability_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260822_issue285_home_goal_truth_r2_v2_landing",
  "follows_last_round_id": "round_20260822_issue285_home_goal_truth_r2_v2_landing",
  "previous_audit_outcome": "ISSUE320_R2_V1_REJECTED_PR319_REPLAY_REQUIRED_FOR_STATE_GATE_REACHABILITY",
  "superseded_pr": 319,
  "superseded_owner_branch": "owner/issue318-state-gate-reachability-r2-v1",
  "superseded_head": "d837891f582a9ed30088fea8f7465a5cc97ce153",
  "workstream_id": "issue320-state-gate-reachability-r2-v2",
  "source_issue": 320,
  "required_branch": "owner/issue320-state-gate-reachability-r2-v2",
  "starting_head": "772de2662949d2a454b611806a36b52f75cace9f",
  "activation_base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "integration_base_ref": "main",
  "base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "post_publication_binding_commit_limit": 0,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 1,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "mark_ready_allowed": false,
  "merge_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue320-state-gate-reachability-r2-v2 from locked origin/main 772de2662949d2a454b611806a36b52f75cace9f in an isolated detached worktree whose merge-base with main is 772de2662949d2a454b611806a36b52f75cace9f",
    "commit this immutable Decision as the unique first new commit after 772de2662949d2a454b611806a36b52f75cace9f before any generated governance artifact or semantic replay",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue320v2.bootstrap_and_gate",
      "command": "verify origin/main remains 772de2662949d2a454b611806a36b52f75cace9f; verify PR 319 remains frozen Draft at head d837891f582a9ed30088fea8f7465a5cc97ce153; run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before semantic replay",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue320v2.semantic_replay",
      "command": "restore the four semantic replay files as an exact Git-blob replay from superseded v1 head d837891f582a9ed30088fea8f7465a5cc97ce153 in a single commit; verify each blob SHA equals the approved target: .github/workflows/state-gate.yml=73b44ca43b293a9481b026be801f119c77f68514, .github/workflows/ci.yml=2dc26892325e12fe22fd472d587a324f1ebc76e7, tests/test_ci_responsibility.py=d01aebfac31ba85be93b259e49edf26967ae0066, tests/test_project_gate.py=7063553ba79bd8a37e00f69679e300c3b6c7e63b",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "bounded_test_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        ".github/workflows/state-gate.yml",
        ".github/workflows/ci.yml",
        "tests/test_ci_responsibility.py",
        "tests/test_project_gate.py"
      ]
    },
    {
      "command_id": "issue320v2.post_replay_validation",
      "command": "run tests/test_path_a_gate.py, tests/test_ci_responsibility.py, tests/test_project_gate.py, tests/test_control_plane_transition.py plus tests/test_planning_and_github_adapters.py; run transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; assert test_state_gate_pull_request_trigger_reaches_every_risk_only_change 10 cases ALL PASS; assert State Gate ordinary pull_request block contains no paths: key; any failure stops publication",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue320v2.publish_single_draft",
      "command": "push owner/issue320-state-gate-reachability-r2-v2 once and create exactly one Draft PR with base=main; observe fresh exact-head CI, State Gate pull_request, and Decision Preflight runs without rerun or runner dispatch; stop at READY_FOR_OWNER_AUDIT",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py"
  ],
  "reference_paths": [
    "project_state/decision_packet.md",
    "AGENTS.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "direct_push_main",
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
    "worktree_deletion",
    "mark_ready",
    "merge",
    "history_rewrite",
    "archive_historical_intent_mutation",
    "cherry_pick_rejected_head"
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
    "local_network_exceptions": [
      "push owner/issue320-state-gate-reachability-r2-v2 once and create exactly one Draft PR with base=main; observe fresh exact-head CI, State Gate pull_request, and Decision Preflight runs without rerun or runner dispatch"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "github_mark_ready_allowed": false,
    "github_merge_allowed": false,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE320_STATE_GATE_REACHABILITY_R2_V2_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE320_V2_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Rework Issue #320 as an authority-chronology-clean R2 v2 replay of the State Gate reachability fix: from locked `main@772de2662949d2a454b611806a36b52f75cace9f`, record the immutable Decision as the unique first new commit, generate Path-B authority to `PRE_EXECUTION_AUTHORIZED`, then replay the four final semantic files from superseded PR #319 head `d837891f582a9ed30088fea8f7465a5cc97ce153` as exact Git blobs in a single semantic commit, without cherry-picking or modifying the Decision.

## Acceptance

1. This Decision is the unique first new commit after exact `main@772de2662949d2a454b611806a36b52f75cace9f`; PR #319 remains frozen Draft and its v1 branch `owner/issue318-state-gate-reachability-r2-v1` remains superseded evidence only.
2. The branch `owner/issue320-state-gate-reachability-r2-v2` merge-base equals `772de2662949d2a454b611806a36b52f75cace9f`; the four semantic replay files are the only non-bootstrap mutation and each equals its target blob SHA.
3. The Path-B authority chain (startup-snapshot -> transition-command-plan -> transition-lint -> transition-preflight --mode pre) yields `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]` before semantic replay begins.
4. `test_state_gate_pull_request_trigger_reaches_every_risk_only_change` passes all 10 cases; the State Gate ordinary `pull_request` block contains no `paths:` key; CI, State Gate, and Decision Preflight fresh exact-head runs are `SUCCESS`.
5. No PR #319 commit is cherry-picked; no generated v1 gate artifact is restored; no `reverse_agent/**`, `frontend/**`, `model_access/**`, or `test_path_a_gate.py` mutation occurs. The Decision is never edited after activation.

## Execution policy

- Preserve PR #319 as frozen Draft negative evidence with zero push and zero PR body mutation.
- Treat the four target blob SHAs as immutable semantic replay targets; any SHA mismatch fails closed.
- Do not cherry-pick v1 commits or restore v1 gate artifacts; only the four final file blobs are reused, via `git show <v1-head>:<path>`.
- TaskStore remains the sole product execution truth; this replay adds no second authority store, merge intent, attestation, or scheduler.
- Stop on any base, head, branch, blob, path, scope, gate, test, or chronology mismatch. Preserve unrelated worktree content and do not use reset, clean, stash, restore, deletion, force push, or history rewrite.
- No mark-ready, merge, auto-merge, direct-main push, tag, release, deployment, credential access, provider/model invocation, or runner dispatch occurs.
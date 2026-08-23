# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260823_issue325_decision_immutability_r2_v1",
  "round_id": "round_20260823_issue325_decision_immutability_r2_v1",
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
  "previous_audit_outcome": "ISSUE285_HOME_GOAL_TRUTH_R2_V2_LANDING_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "workstream_id": "issue325-decision-immutability-r2-v1",
  "source_issue": 325,
  "parent_issue": 321,
  "integration_base_ref": "main",
  "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "activation_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "starting_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "required_branch": "owner/issue325-path-b-decision-immutability-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "runner_dispatch_limit": 0,
  "tag_or_release_limit": 0,
  "deployment_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue325.bootstrap_gate_sequence",
      "command": "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre immediately after the Decision activation commit; require PRE_EXECUTION_AUTHORIZED with zero blockers before any implementation mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue325.implement_transition_immutability",
      "command": "extend TransitionAuthority with the immutable-Decision evidence fields (defaults for backward compatibility); add decision_single_commit_in_range, decision_commit_precedes_implementation, decision_content_unchanged, decision_commit_descends_from_activation_base, and scope_contract_consistent checks to validate_transition; wire immutable-evidence computation into transition_preflight and transition_reconcile; add an immutability check to transition_lint; add an explicit immutability re-check to worktree_publication_readiness",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "source_edit", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/models.py",
        "reverse_agent/control_plane/transition.py",
        "reverse_agent/project_gate.py"
      ]
    },
    {
      "command_id": "issue325.implement_regression_tests",
      "command": "add focused current-round deterministic Git-history regression tests for Cases A/B/C/D and the positive case to test_control_plane_transition.py using the existing _transition_git stub mechanism; update test_ci_responsibility.py deselection-set assertions from 7 to 4 after restoring the three TestDecisionImmutability nodes; make only the minimal edit to test_merge_intent.py needed for the restored nodes to parse the current-round starting_head contract correctly",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["test_edit", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/platform_v1/test_merge_intent.py",
        "tests/test_control_plane_transition.py",
        "tests/test_ci_responsibility.py"
      ]
    },
    {
      "command_id": "issue325.update_blocking_ci",
      "command": "remove the three TestDecisionImmutability --deselect tokens from the Platform V1 blocking pytest command in .github/workflows/ci.yml so the restored nodes become blocking; keep the four unrelated task3c deselections intact; do not touch state-gate.yml or any other workflow",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["workflow_change", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        ".github/workflows/ci.yml"
      ]
    },
    {
      "command_id": "issue325.final_validation",
      "command": "run the six focused pytest suites (test_merge_intent, test_control_plane_transition, test_project_gate, test_ci_responsibility, test_path_a_gate, test_planning_and_github_adapters), the Platform V1 blocking pytest command exactly as it appears in ci.yml, transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; prove the Git chronology: exactly one decision_packet.md-modifying commit in starting_head..HEAD, it is the first new commit, its blob equals HEAD blob, and every mutated path is within the allowed scope",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue325.publish_draft_pr",
      "command": "after full local validation push the exact branch once and create exactly one Draft PR against main; observe the exact remote head, fresh CI, State Gate, and Decision Preflight pull_request runs; do not mark ready, merge, tag, release, or dispatch runners",
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
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/project_gate.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/test_control_plane_transition.py",
    "tests/test_ci_responsibility.py",
    ".github/workflows/ci.yml"
  ],
  "reference_paths": [
    "reverse_agent/decision_preflight.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/evidence_source.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/local_seal.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/report_binding.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/__init__.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/test_project_gate.py",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
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
    "project_state/schemas/**",
    "project_state/context/**",
    "project_state/evidence/**",
    "project_state/proposed_state/**",
    "project_state/domains/**",
    "project_state/jobs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/roadmap/**",
    "project_state/solve_tasks/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/control_plane/evidence_source.py",
    "reverse_agent/control_plane/execution_reconciliation.py",
    "reverse_agent/control_plane/local_seal.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/report_binding.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/control_plane/__init__.py",
    "reverse_agent/platform_v1/**",
    "tests/test_project_gate.py",
    "tests/platform_v1/test_contracts.py",
    "frontend/**",
    "docs/**",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
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
    "model_api_invocation",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "tag_or_release",
    "deployment",
    "worktree_deletion",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work",
    "mark_ready",
    "merge",
    "issue_close",
    "pull_request_close"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": ["provider-free fake HTTP and SSE fixtures bound only to 127.0.0.1"],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [".github/workflows/ci.yml"],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE325_PATH_B_DECISION_IMMUTABILITY_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE325_PATH_B_DECISION_IMMUTABILITY_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Upgrade the Path-B `decision_content_immutable_after_activation=true` flag from an audit-only convention into a repository-owned, machine-enforced, fail-closed governance constraint. After activation, any mutation of the original Decision, retroactive scope expansion, or second Decision-mutating commit must be caught by transition-lint, transition-preflight (pre and post), worktree-publication-readiness, and blocking CI.

## Acceptance

1. `origin/main == 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496` at activation; the branch `owner/issue325-path-b-decision-immutability-r2-v1` is rooted exactly at that SHA with merge-base equal to `base_sha`.
2. This Decision commit is the unique first new commit after `starting_head`; it is the only commit in `starting_head..HEAD` that modifies `project_state/decision_packet.md`; `HEAD:project_state/decision_packet.md` equals the activation-commit blob byte-for-byte for the lifetime of the branch.
3. `validate_transition` gains fail-closed checks for: exactly-one Decision commit in range (`decision_activation_commit_limit`), Decision commit precedes all implementation commits, Decision blob unchanged since its commit (including no working/staged diff on `decision_packet.md`), Decision commit descends from `activation_base_sha`, and allowed/forbidden scope non-contradiction. Every violation lands in `blocking_reasons`, never only a warning.
4. `transition_lint` and `worktree_publication_readiness` independently re-verify Decision immutability so a regenerated or stale downstream artifact cannot whitewash a prior unauthorized mutation.
5. Deterministic negative Git-history fixtures prove Cases A (retroactive scope expansion), B (post-hoc field addition), C (allowed_paths expansion), D (second Decision commit) all BLOCK; the positive case (single activation Decision then implementation then evidence) PASSES.
6. The three `TestDecisionImmutability` nodes previously deselected from blocking CI are restored (they are sound for current-round semantics), and `test_ci_responsibility.py` is updated so the Platform V1 blocking gate has exactly four deselections (the three unrelated task3c nodes).
7. Focused tests in `tests/platform_v1/test_merge_intent.py -q`, `tests/test_control_plane_transition.py -q`, `tests/test_project_gate.py -q`, `tests/test_ci_responsibility.py -q`, `tests/test_path_a_gate.py -q`, `tests/test_planning_and_github_adapters.py -q`, the Platform V1 blocking pytest command as written in `ci.yml`, `transition-lint`, `transition-preflight --mode pre`, `worktree-publication-readiness`, and `git diff --check` all pass.
8. Exactly one normal push of the exact branch and exactly one Draft PR against `main`; no mark-ready, merge, tag, release, runner dispatch, dependency install, live model/provider call, credential access, force push, rebase, or history rewrite.
9. Fresh exact-head CI, State Gate, and Decision Preflight `pull_request` runs are observed; the round stops at `DRAFT_PR_READY_FOR_EXACT_HEAD_OWNER_AUDIT`.

## Execution policy

- This Decision is byte-immutable after its activation commit; any later edit to `project_state/decision_packet.md` fails closed and requires a new issue/round/branch/Decision rather than an in-place amendment.
- Do not create a second governance gate; strengthen the existing transition, preflight, authority-collection, and publication-readiness surfaces.
- Do not execute issues #301, #295, #297, #304, #302, #305, #317, #287, or #283 (Owner GitHub-Settings control-plane task, out of local coding scope).
- Pre-existing dirty worktree state observed at bootstrap (prior interrupted run) is preserved to `C:\Users\wjc27\AppData\Local\Temp\opencode\issue325_preserved_dirty\` for audit; the four in-scope files that blocked branch checkout were restored to the authoritative `origin/main` versions so the fresh branch is rooted at the locked SHA. Out-of-scope dirty files (`frontend/**`, `reverse_agent/platform_v1/task_service.py`) remain unstaged and are never committed or pushed.
- Fail closed on any main drift, Decision mutation, scope contradiction, or unexplained test failure; stop and request a revised Work Item rather than widening this Decision.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "round_id": "round_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260823_issue320_state_gate_reachability_r2_v2",
  "follows_last_round_id": "round_20260823_issue320_state_gate_reachability_r2_v2",
  "previous_audit_outcome": "ISSUE320_R2_V2_IMPLEMENTATION_ACCEPTED_EXACT_HEAD_663FC157_TREE_7B5D3AB9_PR322",
  "source_issue": 320,
  "landing_planning_issue": 323,
  "validated_implementation_pr": 322,
  "validated_implementation_branch": "owner/issue320-state-gate-reachability-r2-v2",
  "validated_implementation_head": "663fc157a0dafc8002511921bc2b0411f26ee020",
  "validated_implementation_tree": "7b5d3ab9b591380745ecd8c663cf7042acd05fc4",
  "validated_implementation_decision": "decision_20260823_issue320_state_gate_reachability_r2_v2",
  "validated_implementation_decision_blob": "f00dd1d8c1056262ba8e8312211dbf07e10bfd26",
  "accepted_implementation_pr_state": "OPEN",
  "accepted_implementation_pr_draft": true,
  "workstream_id": "issue320-state-gate-reachability-r2-v2-landing",
  "required_branch": "owner/issue320-state-gate-reachability-r2-v2-landing",
  "starting_head": "663fc157a0dafc8002511921bc2b0411f26ee020",
  "activation_base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "integration_base_ref": "main",
  "base_sha": "772de2662949d2a454b611806a36b52f75cace9f",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
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
    "create owner/issue320-state-gate-reachability-r2-v2-landing from accepted head 663fc157a0dafc8002511921bc2b0411f26ee020 in an isolated detached worktree whose merge-base with main is 772de2662949d2a454b611806a36b52f75cace9f",
    "commit this immutable Decision as the unique first new commit after 663fc157a0dafc8002511921bc2b0411f26ee020 before any generated governance artifact or semantic mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue320v2landing.bootstrap_and_gate",
      "command": "verify origin/main remains 772de2662949d2a454b611806a36b52f75cace9f; verify PR 322 remains OPEN Draft at head 663fc157a0dafc8002511921bc2b0411f26ee020; verify four accepted semantic blobs unchanged; run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED with zero blockers before any mutation",
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
      "command_id": "issue320v2landing.prepublic_validation",
      "command": "run test_path_a_gate, test_ci_responsibility, test_project_gate, test_mainline_landing + test_merge_intent, test_control_plane_transition + test_planning_and_github_adapters; run transition-lint, transition-preflight --mode pre, worktree-publication-readiness, git diff --check; assert all PASS; do not modify any accepted semantic blob",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue320v2landing.decision_history_proof",
      "command": "prove Decision commit is first after 663fc157; prove Decision commit touches only project_state/decision_packet.md; prove Decision blob unchanged between activation and final HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue320v2landing.initial_push_and_pr",
      "command": "normal push owner/issue320-state-gate-reachability-r2-v2-landing once; create exactly one Draft PR with base=main; observe actual PR number; do not mark-ready; do not merge",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue320v2landing.mainline_intent_binding",
      "command": "archive current active mainline merge intent byte-for-byte to archive/pr288_v2.json; replace active.json with new schema-v2 intent binding actual landing PR number, locked base, allowed merge method, immutable landing Decision digest, generated Command Plan digest, required workflows, bounded expiry; one governance-only binding commit; do not modify Decision",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr288_v2.json"
      ]
    },
    {
      "command_id": "issue320v2landing.final_validation",
      "command": "prove Decision blob unchanged; prove accepted semantic blobs unchanged; prove archive byte-for-byte; prove active intent binding exact; rerun all prepublication validation; require all PASS before second push",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue320v2landing.final_push",
      "command": "normal fast-forward push binding commit as second and final push; observe final exact head CI, State Gate, and Decision Preflight; verify all SUCCESS; verify PR still Draft, main still locked base, head exact, mergeable, zero unresolved threads",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "repository_observation", "network_access"],
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr288_v2.json"
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
  "accepted_immutable_semantic_blobs": [
    {
      "path": ".github/workflows/state-gate.yml",
      "blob_sha": "73b44ca43b293a9481b026be801f119c77f68514"
    },
    {
      "path": ".github/workflows/ci.yml",
      "blob_sha": "2dc26892325e12fe22fd472d587a324f1ebc76e7"
    },
    {
      "path": "tests/test_ci_responsibility.py",
      "blob_sha": "d01aebfac31ba85be93b259e49edf26967ae0066"
    },
    {
      "path": "tests/test_project_gate.py",
      "blob_sha": "7063553ba79bd8a37e00f69679e300c3b6c7e63b"
    }
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/schemas/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md"
  ],
  "forbidden_operations": [
    "product_semantic_mutation",
    "workflow_semantic_mutation",
    "test_semantic_mutation",
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
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
    "runner_dispatch",
    "history_rewrite",
    "archive_historical_intent_mutation",
    "pr_body_mutation_before_acceptance"
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
      "normal push owner/issue320-state-gate-reachability-r2-v2-landing once for initial publication",
      "create exactly one Draft PR with base=main",
      "observe fresh exact-head CI, State Gate pull_request, and Decision Preflight runs without rerun or runner dispatch",
      "normal fast-forward push binding commit as second and final push",
      "observe final exact-head CI, State Gate pull_request, and Decision Preflight runs"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": true,
    "github_issue_close_allowed": true,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": true,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "publication_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr288_v2.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE320_R2_V2_LANDING_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE320_V2_LANDING_EXECUTION_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the independently accepted PR #322 exact tree `7b5d3ab9b591380745ecd8c663cf7042acd05fc4` via a fresh Decision-first Path-B landing round: from accepted head `663fc157a0dafc8002511921bc2b0411f26ee020`, record this immutable landing Decision as the unique first new commit, generate Path-B authority to `PRE_EXECUTION_AUTHORIZED`, prove the accepted semantic blobs unchanged, publish exactly one Draft landing PR with an initial push, bind the schema-v2 mainline merge intent to the actual PR number via one governance-only binding commit, publish the binding with a second push, and stop at `READY_FOR_OWNER_AUDIT` for the owner to perform mark-ready and merge from a fresh audit of the final exact head.

## Acceptance

1. This landing Decision is the unique first new commit after accepted head `663fc157a0dafc8002511921bc2b0411f26ee020`; PR #322 remains OPEN Draft at the same head; `origin/main` remains locked at `772de2662949d2a454b611806a36b52f75cace9f`.
2. The landing branch `owner/issue320-state-gate-reachability-r2-v2-landing` merge-base with `main` equals `772de2662949d2a454b611806a36b52f75cace9f`; the four accepted semantic blobs are byte-for-byte unchanged; no product, workflow, or test semantic mutation occurs.
3. The Path-B authority chain (startup-snapshot -> transition-command-plan -> transition-lint -> transition-preflight --mode pre) yields `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]` before any mutation.
4. All prepublication tests pass; Decision history proof confirms the Decision commit is first, touches only `project_state/decision_packet.md`, and its blob is unchanged between activation and final HEAD.
5. Exactly two normal pushes: initial push creates the Draft PR with the accepted semantic tree plus Decision and generated artifacts; the second push fast-forwards the mainline-intent binding commit. Exactly one Draft PR is created. The PR remains Draft; no mark-ready or merge is performed by the Agent.
6. The active mainline merge intent is byte-for-byte archived to `archive/pr288_v2.json`, then replaced with a new schema-v2 intent binding the actual landing PR number, locked base SHA, `merge` method, immutable landing Decision digest, generated Command Plan digest, required workflows (CI, Decision Preflight, State Gate pull_request), and a bounded expiry.
7. Final exact head has CI, State Gate, and Decision Preflight all `SUCCESS`; PR remains Draft; `main` still at locked base; `mergeable == MERGEABLE`; zero unresolved blocking review threads.
8. No force push, rebase, squash, history rewrite, direct main push, auto-merge, dependency installation, live model/provider call, credential access, runner dispatch, tag, release, or deployment occurs.

## Execution policy

- Treat PR #322 and its four accepted semantic blobs as immutable evidence; never modify them.
- Treat the landing Decision as immutable after activation; never edit it post-commit.
- Use exactly one Draft PR and exactly two normal pushes; no additional pushes or PRs.
- The mainline merge intent binding is a single governance-only commit touching only `project_state/mainline_merge_intents/active.json` and `project_state/mainline_merge_intents/archive/pr288_v2.json`.
- Stop at `READY_FOR_OWNER_AUDIT` after the second push and exact-head workflow observation; the owner performs mark-ready and merge from a fresh re-audit.
- No mark-ready, merge, issue close, PR close, or post-merge mutation is performed by the Agent.
- Preserve unrelated worktree content; do not use reset, clean, stash, restore, deletion, force push, or history rewrite.

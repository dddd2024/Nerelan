# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue330_trusted_remote_merge_boundary_r2_v3",
  "round_id": "round_20260824_issue330_trusted_remote_merge_boundary_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue328_trusted_remote_merge_boundary_r2_v2",
  "follows_last_round_id": "round_20260824_issue328_trusted_remote_merge_boundary_r2_v2",
  "previous_audit_outcome": "PR329_FINAL_BINDING_PRODUCTION_PRE_MERGE_SIMULATION_FIXTURE_FAILURE",
  "workstream_id": "issue330-trusted-remote-merge-boundary-r2-v3",
  "source_issue": 330,
  "parent_issue": 328,
  "superseded_pr": 329,
  "superseded_pr_head": "9e77707cb3905d1b8ab72790f749fc5bfe97b3fa",
  "superseded_terminal": "PR329_R2_V2_BLOCKED_PRODUCTION_PRE_MERGE_SIMULATION_FIXTURE",
  "historical_failed_landing_pr": 324,
  "historical_failed_state_gate_push_run": 32639335287,
  "integration_base_ref": "main",
  "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "activation_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "starting_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "required_branch": "owner/issue330-mainline-attestation-recovery-r2-v3",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
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
  "workflow_rerun_allowed": false,
  "add_attestation_to_pr324_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "trusted_merge_boundary": "github_pull_request_merged_at",
  "trusted_attestation_body_window": "github_comment_created_at_and_updated_at_strictly_before_merged_at",
  "trusted_remote_metadata_is_runtime_enriched_evidence": true,
  "local_git_timestamp_authority_allowed": false,
  "attestation_self_declared_timestamp_authority_allowed": false,
  "missing_or_invalid_remote_timestamp_fails_closed": true,
  "timestamp_equality_fails_closed": true,
  "clean_replay_from_locked_main_required": true,
  "closed_pr327_and_failed_pr329_authority_import_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify origin/main remains 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 and the target remote branch and PR do not exist",
    "create the fresh branch from the locked base and commit this immutable Decision as the unique first new commit before any generated governance, source, test, recovery, or intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue330.bootstrap_gate_sequence",
      "command": "verify exact base, branch, clean worktree, merge-base and no remote collision; run startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre immediately after Decision activation; require PRE_EXECUTION_AUTHORIZED with zero blockers before any non-Decision mutation",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks", "generate_governance_artifact"],
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
      "command_id": "issue330.replay_trusted_remote_chronology",
      "command": "replay the accepted trusted remote chronology implementation from the locked main tree: runtime-enrich the exact carrying comment with remote id, author, created_at and updated_at; validate schema-v2 using exact merged PR, exact merge commit and remote merged_at; require created_at < merged_at and updated_at < merged_at; never use local Git timestamps or payload-declared timestamps; keep schema-v1 unchanged",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_source_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/github_remote_verifier.py",
        "reverse_agent/mainline_landing.py"
      ]
    },
    {
      "command_id": "issue330.replay_regressions_fixture_and_recovery",
      "command": "replay deterministic regressions and recovery truth: fix production pre-merge simulation to supply both runtime-only v2 comment timestamps before content-digest calculation; cover crafted future local history, post-merge edit, equality, later, missing and invalid remote timestamps, valid created_at <= updated_at < merged_at, exact PR and merge binding, named fail-closed reasons and frozen v1 behavior; preserve PR324 as negative evidence",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_test_mutation", "bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_mainline_landing.py",
        "tests/platform_v1/test_merge_intent.py",
        "tests/platform_v1/test_contracts.py",
        "project_state/mainline_recoveries/pr324.json"
      ]
    },
    {
      "command_id": "issue330.prepublication_validation",
      "command": "run the mandatory focused pytest commands, the exact Platform V1 blocking command represented by CI, transition-lint, transition-preflight --mode pre, worktree-publication-readiness and git diff --check; prove production pre-merge simulation passes after the fixture correction, chronology cases fail closed with named reasons, schema-v1 remains unchanged and all cumulative paths are authorized",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation", "generate_governance_artifact"],
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
      "command_id": "issue330.history_and_replay_proof",
      "command": "prove Decision is the unique first commit after the locked base and remains byte-identical; prove the implementation is a clean replay from locked main with no PR327 or PR329 ancestor, cherry-pick, patch import or authority import; prove PR324 State Gate push run 32639335287 remains FAILURE and was not rerun",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue330.initial_push_and_draft_pr",
      "command": "after full deterministic validation perform the first normal fast-forward push of owner/issue330-mainline-attestation-recovery-r2-v3; create exactly one Draft PR against locked main; observe the actual PR number; keep it Draft and perform no attestation, comment, mark-ready, merge or workflow rerun",
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
      "command_id": "issue330.mainline_intent_binding",
      "command": "after the actual successor PR number is known, archive the current PR324 active schema-v2 intent byte-for-byte, replace active.json with the exact successor PR binding, create one governance-only binding commit, and do not add any chronology field or modify the Decision",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr324_v2.json"
      ]
    },
    {
      "command_id": "issue330.final_validation",
      "command": "prove Decision immutability, exact path set, archive byte identity, exact active intent binding, one implementation commit, one generated-governance commit and one binding commit; rerun the complete validation suite and require PASS before the second push",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue330.final_push_and_owner_audit_boundary",
      "command": "perform the second and final normal fast-forward push containing only the binding commit; observe exact-head CI, State Gate pull_request and Decision Preflight SUCCESS, Draft state, locked main, exact head and no blocking review threads; stop for independent Owner audit",
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
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py",
    "project_state/mainline_recoveries/pr324.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "project_state/decision_packet.md",
    "reverse_agent/project_gate.py",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_path_a_gate.py",
    "tests/test_planning_and_github_adapters.py"
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
    "requirements*.txt",
    "pyproject.toml",
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/context/**",
    "project_state/evidence/**",
    "project_state/proposed_state/**",
    "project_state/domains/**",
    "project_state/jobs/**",
    "project_state/roadmap/**",
    "project_state/solve_tasks/**",
    "project_state/mainline_recoveries/pr60.json",
    "project_state/mainline_merge_intents/archive/pr108_v1.json",
    "project_state/mainline_merge_intents/archive/pr110_v1.json",
    "project_state/mainline_merge_intents/archive/pr112_v1.json",
    "project_state/mainline_merge_intents/archive/pr112_v2.json",
    "project_state/mainline_merge_intents/archive/pr112_v3.json",
    "project_state/mainline_merge_intents/archive/pr112_v4.json",
    "project_state/mainline_merge_intents/archive/pr112_v5.json",
    "project_state/mainline_merge_intents/archive/pr112_v6.json",
    "project_state/mainline_merge_intents/archive/pr119_v1.json",
    "project_state/mainline_merge_intents/archive/pr121_v2.json",
    "project_state/mainline_merge_intents/archive/pr121_v3.json",
    "project_state/mainline_merge_intents/archive/pr121_v4.json",
    "project_state/mainline_merge_intents/archive/pr129_v5.json",
    "project_state/mainline_merge_intents/archive/pr132_v7.json",
    "project_state/mainline_merge_intents/archive/pr134_v1.json",
    "project_state/mainline_merge_intents/archive/pr257_v1.json",
    "project_state/mainline_merge_intents/archive/pr264_v2.json",
    "project_state/mainline_merge_intents/archive/pr271_v2.json",
    "project_state/mainline_merge_intents/archive/pr275_v2.json",
    "project_state/mainline_merge_intents/archive/pr277_v2.json",
    "project_state/mainline_merge_intents/archive/pr288_v2.json",
    "project_state/mainline_merge_intents/archive/pr67_v5.json",
    "project_state/mainline_merge_intents/archive/pr93_v10.json",
    "project_state/mainline_merge_intents/archive/pr93_v11.json",
    "project_state/mainline_merge_intents/archive/pr97_v1.json",
    "project_state/mainline_merge_intents/archive/pr97_v2.json",
    "project_state/mainline_merge_intents/archive/pr97_v3.json",
    "project_state/mainline_merge_intents/archive/pr97_v4.json"
  ],
  "forbidden_operations": [
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
    "model_api_invocation",
    "opencode_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work",
    "mark_ready",
    "merge",
    "issue_comment",
    "issue_close",
    "pull_request_close",
    "create_or_edit_pr324_attestation",
    "modify_pr327",
    "modify_pr329",
    "execute_issue325",
    "import_pr327_or_pr329_commit_or_authority"
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
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "publication_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "perform the first normal fast-forward push only after deterministic local validation",
      "create exactly one Draft PR against locked main",
      "observe exact-head CI, State Gate pull_request and Decision Preflight without rerun or runner dispatch",
      "perform the second and final normal fast-forward push containing only the intent-binding commit",
      "observe final Draft state, exact head, locked main, mergeability and review-thread status"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_recoveries/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py",
    "project_state/mainline_recoveries/pr324.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE328_V3_CLEAN_REPLAY_COMPLETE_PRODUCTION_PREMERGE_SIMULATION_PASSES_DRAFT_PR_READY_FOR_EXACT_HEAD_OWNER_AUDIT",
  "blocked_terminal": "ISSUE330_TRUSTED_REMOTE_MERGE_BOUNDARY_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Perform a clean, owner-approved replay of the trusted remote merge-boundary implementation from the locked main tree. Correct the schema-v2 production pre-merge simulation fixture before the single implementation commit, preserve PR #324 as negative evidence, and stop at the exact-head Owner audit boundary without importing any commit or authority from closed PR #327 or failed PR #329.

## Acceptance

1. Before mutation, `origin/main` is exactly `0beac2f57c1ae9caa1b11dc02dfc027c9b19e496`, the target remote branch and PR do not exist, and the fresh branch/worktree is clean with starting head and merge-base equal to the locked base.
2. This Decision is the unique first new commit after the locked base, changes only `project_state/decision_packet.md`, is byte-identical through the final head, and is immutable after activation.
3. `startup-snapshot`, `transition-command-plan`, `transition-lint`, and `transition-preflight --mode pre` return `PRE_EXECUTION_AUTHORIZED` with no blockers before any source, test, recovery, intent, or generated artifact mutation.
4. The replayed production verifier overwrites runtime comment id, author, created_at and updated_at from the exact carrying GitHub comment; payload-declared runtime metadata is never authority.
5. Schema-v2 validation binds the exact merged PR and exact merge commit, uses remote PR `merged_at`, and requires remote comment `created_at < merged_at` and `updated_at < merged_at`; missing, invalid, equal and later values fail closed with named reasons. Local Git timestamps remain non-authoritative.
6. `test_production_pre_merge_simulation` supplies both runtime-only comment timestamps before digest calculation and passes only for valid pre-merge chronology. Crafted future-dated local history, post-merge edits, equality, later, missing and invalid cases remain covered.
7. Exact PR, head, base, merge method, intent digest, workflow, comment author and body bindings remain fail closed; schema-v1 four-run behavior remains unchanged.
8. `project_state/mainline_recoveries/pr324.json` preserves semantic-tree-landed but authority-lifecycle-failed truth, State Gate push run `32639335287` remains FAILURE, and no historical or retroactive authorization is asserted.
9. The mandatory focused pytest commands, the exact Platform V1 blocking command, transition gates, worktree publication readiness and `git diff --check` pass on the exact cumulative head.
10. The round has exactly one Decision activation commit, one implementation/test/recovery commit, one generated-governance commit, one post-publication intent-binding commit, two normal fast-forward pushes and one Draft PR against locked main.
11. After binding, final exact-head CI, State Gate pull_request and Decision Preflight are SUCCESS; the Draft PR remains Draft, main remains locked, and no blocking review threads remain.
12. No attestation, PR comment, mark-ready, merge, workflow rerun, direct main push, force push, rebase, history rewrite, provider/model call, dependency installation, credential access, runner dispatch, tag, release, deployment, offensive-security work, PR #327 mutation, PR #329 mutation or Issue #325 execution occurs.

## Execution policy

- This approved Decision is the sole Path-B authority for the round; the Issue is an owner plan and is not mutation authority by itself.
- The implementation is a clean replay from the locked main tree. Do not cherry-pick, copy, import, or rely on commits, patches, Decision content, or authority from PR #327 or PR #329.
- Extend only the existing `github_remote_verifier -> mainline_landing -> project_gate` path. Do not add a second gate, execution store, orchestration runtime, authority schema, workflow or dependency.
- Use exactly one implementation commit for source, tests and PR324 recovery evidence; exactly one generated-governance commit; and exactly one post-publication active-intent binding commit.
- Preserve PR324 State Gate push failure as negative evidence. Never rerun it, add an attestation to PR324, rewrite history, or claim retroactive authorization.
- Keep the successor PR Draft and stop after final exact-head observation at the Owner audit boundary. Owner attestation, mark-ready and merge require a fresh owner action outside this round.
- Preserve unrelated worktree content and use explicit path staging only. Never reset, clean, stash, restore, amend, force push, rebase or rewrite history.

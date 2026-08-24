# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue328_trusted_remote_merge_boundary_r2_v2",
  "round_id": "round_20260824_issue328_trusted_remote_merge_boundary_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "follows_last_round_id": "round_20260823_issue320_state_gate_reachability_r2_v2_landing",
  "previous_audit_outcome": "PR324_SEMANTIC_TREE_LANDED_BUT_STATE_GATE_PUSH_FAILED_WITHOUT_REQUIRED_PREMERGE_ATTESTATION",
  "workstream_id": "issue328-trusted-remote-merge-boundary-r2-v2",
  "source_issue": 328,
  "parent_issue": 326,
  "superseded_pr": 327,
  "superseded_pr_head": "22b21ce9b9816862f15b1e19a4b800251fe220bf",
  "superseded_terminal": "PR327_R2_V1_REJECTED_WRONG_AUTHORITY_BOUNDARY",
  "historical_failed_landing_pr": 324,
  "historical_failed_state_gate_push_run": 32639335287,
  "integration_base_ref": "main",
  "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "activation_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "starting_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "required_branch": "owner/issue328-mainline-attestation-recovery-r2-v2",
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
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify origin/main and origin/owner/issue328-mainline-attestation-recovery-r2-v2 both remain exactly 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
    "commit this immutable Decision as the unique first new commit after 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 and before any generated governance artifact or implementation mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue328.bootstrap_gate_sequence",
      "command": "verify exact base and branch bindings; prove PR 327 remains closed and unmerged at head 22b21ce9b9816862f15b1e19a4b800251fe220bf; run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre immediately after the Decision activation commit; require PRE_EXECUTION_AUTHORIZED with zero blockers before any implementation mutation",
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
      "command_id": "issue328.implement_trusted_remote_chronology",
      "command": "extend the existing GitHub verifier and mainline landing validator only: enrich the exact carrying comment with trusted remote created_at and updated_at; require schema-v2 validation to obtain trusted PR merged_at from the exact merged PR and exact merge commit; parse all three remote timestamps fail closed; require comment created_at and updated_at each strictly earlier than PR merged_at; never use local Git author or committer time and never accept payload-declared timestamps as authority; keep schema-v1 semantics unchanged",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "source_edit", "stage_authorized_paths", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/github_remote_verifier.py",
        "reverse_agent/mainline_landing.py"
      ]
    },
    {
      "command_id": "issue328.implement_regressions_and_recovery_record",
      "command": "add deterministic regressions for crafted future-dated local history, post-merge comment edit, equality at each remote boundary, later timestamps, missing or invalid merged_at created_at and updated_at, valid created_at less-than-or-equal-to updated_at strictly before merged_at, exact PR and merge-commit binding, and frozen schema-v1 behavior; minimally update the current schema-v2 intent contract fixtures; add durable PR 324 negative recovery evidence that never claims retroactive authorization",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "test_edit", "stage_authorized_paths", "commit"],
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
      "command_id": "issue328.prepublication_validation",
      "command": "run test_mainline_landing, test_ci_responsibility, test_project_gate, test_control_plane_transition, test_planning_and_github_adapters, test_merge_intent and test_contracts; run transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check; prove both decisive remote chronology regressions BLOCK for named remote reasons, the positive current schema-v2 case PASSES, schema-v1 remains unchanged, and all cumulative changed paths are authorized",
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
      "command_id": "issue328.decision_and_history_proof",
      "command": "prove the Decision commit is the unique first commit after starting_head; prove it touches only project_state/decision_packet.md; prove the activation Decision blob equals the final Decision blob; prove no PR 327 commit is an ancestor or patch import of this branch; prove local Git timestamps are absent from the schema-v2 authority path; prove the PR 324 State Gate push run 32639335287 remains FAILURE and was not rerun",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue328.initial_push_and_pr",
      "command": "after full deterministic local validation perform the first normal fast-forward push of owner/issue328-mainline-attestation-recovery-r2-v2; create exactly one Draft PR with base=main; observe the actual remote PR number; keep the PR Draft; do not create an attestation, mark ready, merge, comment, or rerun workflows",
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
      "command_id": "issue328.mainline_intent_binding",
      "command": "archive the current active schema-v2 PR 324 intent byte-for-byte to project_state/mainline_merge_intents/archive/pr324_v2.json; replace active.json with a schema-v2 intent binding the actual successor PR number, locked base, merge method, immutable Issue 328 Decision digest, generated Command Plan digest, required workflows, and bounded expiry; create exactly one governance-only post-publication binding commit; do not encode a self-declared chronology flag and do not modify the Decision",
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
      "command_id": "issue328.final_validation",
      "command": "prove Decision immutability, archive byte identity, exact active intent binding, one implementation commit, one generated-governance commit, one binding commit, and all authorized paths; rerun all prepublication validation and require all PASS before the second push",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue328.final_push_and_observation",
      "command": "perform the second and final normal fast-forward push of the governance-only binding commit; observe final exact-head CI, State Gate pull_request, and Decision Preflight without rerun or runner dispatch; require all SUCCESS; verify PR remains Draft, main remains locked base, head is exact, no unresolved blocking review threads exist, and stop for exact-head Owner audit",
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
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py",
    "project_state/mainline_recoveries/pr324.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json"
  ],
  "reference_paths": [
    "reverse_agent/project_gate.py",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/mainline_merge_intents/archive/pr264_v2.json",
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
    ".github/**",
    "frontend/**",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    "AGENTS.md",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/schemas/**",
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
    "project_state/mainline_merge_intents/archive/pr97_v4.json",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/**",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_path_a_gate.py"
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
    "worktree_deletion",
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
    "execute_issue325"
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
      "perform the first normal fast-forward push of owner/issue328-mainline-attestation-recovery-r2-v2 only after deterministic local validation",
      "create exactly one Draft PR with base=main",
      "observe the actual Draft PR number and fresh exact-head CI, State Gate pull_request, and Decision Preflight runs without rerun or runner dispatch",
      "perform the second and final normal fast-forward push containing only the authorized intent-binding commit",
      "observe final exact-head CI, State Gate pull_request, Decision Preflight, PR Draft state, exact head, locked main, mergeability, and unresolved review-thread count"
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
    "project_state/mainline_recoveries/pr324.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr324_v2.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE328_TRUSTED_REMOTE_MERGE_BOUNDARY_READY_FOR_OWNER_AUDIT",
  "blocked_terminal": "ISSUE328_TRUSTED_REMOTE_MERGE_BOUNDARY_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Replace the rejected local-Git-time chronology boundary with one repository-owned, fail-closed validator path that uses only trusted GitHub remote evidence for current schema-v2 approval: the exact carrying comment's remote created_at and updated_at must both be strictly earlier than the exact merged PR's remote merged_at. Preserve schema-v1 history, preserve PR #324 as negative evidence, publish one Draft successor PR through a bounded post-publication intent binding, and stop at exact-head Owner audit without attestation, mark-ready, merge, or workflow rerun.

## Acceptance

1. At activation, origin/main and origin/owner/issue328-mainline-attestation-recovery-r2-v2 both equal 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496, and the branch merge-base with main equals that SHA.
2. This Decision is the unique first new commit after starting_head; it touches only project_state/decision_packet.md, precedes all implementation, and remains byte-for-byte unchanged through the final exact head. No PR #327 commit or Decision authority is imported.
3. The Path-B sequence startup-snapshot -> transition-command-plan -> transition-lint -> transition-preflight --mode pre returns PRE_EXECUTION_AUTHORIZED with blocking_reasons=[] before source, test, recovery, or intent mutation.
4. The live GitHub verifier runtime-enriches the exact structured attestation with the carrying comment's trusted remote created_at and updated_at, and schema-v2 mainline validation obtains trusted merged_at from the exact merged PR bound to the expected merge commit.
5. Current schema-v2 validation requires remote comment created_at < remote PR merged_at and remote comment updated_at < remote PR merged_at. Equality, later values, missing values, and invalid values fail closed with named material reasons. Local Git author/committer times and payload-declared timestamps are never authority.
6. Decisive regression A proves remote merged_at=T1 and comment created_at=T2 with T1 <= T2 blocks even when T2 is earlier than a crafted local author time T3. Decisive regression B proves a comment created at T0 before merge but updated at T2 with T0 < T1 <= T2 blocks. Equality at each boundary and missing/invalid timestamp cases also block; a valid created_at less-than-or-equal-to updated_at with both strictly before merged_at passes.
7. Existing wrong PR, head, base, merge method, intent digest, workflow SHA, event, conclusion, comment author, and body digest bindings remain fail closed; frozen schema-v1 four-run behavior remains unchanged.
8. project_state/mainline_recoveries/pr324.json records that PR #324's semantic tree landed but its authority lifecycle failed because required pre-merge attestation was absent; State Gate push run 32639335287 remains FAILURE, is never rerun, and no record claims historical or retroactive authorization.
9. Focused tests in tests/test_mainline_landing.py, tests/test_ci_responsibility.py, tests/test_project_gate.py, tests/test_control_plane_transition.py, tests/test_planning_and_github_adapters.py, tests/platform_v1/test_merge_intent.py, and tests/platform_v1/test_contracts.py pass. transition-lint, transition-preflight --mode pre, worktree-publication-readiness, and git diff --check pass on the exact cumulative head.
10. Exactly one implementation commit, one generated-governance commit, one post-publication binding commit, two normal fast-forward pushes, and one Draft PR against main. The active PR #324 intent is archived byte-for-byte to archive/pr324_v2.json, and active.json is replaced by an exact schema-v2 successor PR binding. No chronology policy is self-declared in the intent.
11. Final exact-head CI, State Gate pull_request, and Decision Preflight are SUCCESS; the PR remains Draft; main remains locked at base_sha; the PR head is exact; no unresolved blocking review threads remain.
12. No Owner attestation, mark-ready, merge, workflow rerun, direct main push, force push, rebase, history rewrite, provider/model call, dependency install, credential access, runner dispatch, tag, release, deployment, offensive-security work, PR #327 mutation, or Issue #325 execution occurs in this round.

## Execution policy

- The GitHub PR object and exact carrying GitHub comment are the only chronology sources. Remote metadata is injected at runtime and is never trusted when declared in the attestation payload.
- Extend the existing github_remote_verifier -> mainline_landing -> project_gate path. Do not add a parallel gate, execution store, orchestration runtime, or authority schema.
- Treat this Decision as immutable after activation. Missing scope requires a new Issue, branch, round, and Decision; never amend or widen this activated file.
- Use one implementation commit for source, tests, and the PR #324 recovery record; use one generated-governance commit before publication; use one governance-only intent-binding commit after the Draft PR reveals its actual number.
- Preserve the current PR #324 State Gate push failure as negative evidence. Do not add or edit an attestation, rerun the workflow, or claim the historical merge was authorized.
- Stop at ISSUE328_TRUSTED_REMOTE_MERGE_BOUNDARY_READY_FOR_OWNER_AUDIT after the second push and final exact-head workflow observation. Owner attestation and any subsequent expected-head landing require a fresh owner action outside this Agent execution round.
- Preserve unrelated worktree content and use only explicit path staging. Never reset, clean, stash, restore, delete, amend, force push, rebase, or rewrite history.

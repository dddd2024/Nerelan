# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue333_pr331_attested_landing_r2_v2",
  "round_id": "round_20260824_issue333_pr331_attested_landing_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue332_pr331_attested_landing_r2_v1",
  "follows_last_round_id": "round_20260824_issue332_pr331_attested_landing_r2_v1",
  "previous_audit_outcome": "ISSUE332_BLOCKED_BEFORE_REMOTE_MUTATION_UNSUPPORTED_REMOTE_EXECUTION_SURFACE_AND_GATES_RISK_PROJECTION",
  "source_issue": 333,
  "predecessor_issue": 332,
  "candidate_pr": 331,
  "candidate_head_sha": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e",
  "candidate_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "validated_candidate_pr_state": "OPEN",
  "validated_candidate_pr_draft": true,
  "validated_candidate_pr_mergeable": "MERGEABLE",
  "validated_candidate_pr_merge_state": "CLEAN",
  "workstream_id": "issue333-pr331-attested-landing-r2-v2",
  "required_branch": "owner/issue333-pr331-landing-r2-v2",
  "starting_head": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "activation_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "integration_base_ref": "main",
  "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "no_binding_commit_authority_branch",
  "issue_number_must_not_substitute_for_pr_number": true,
  "historical_failed_landing_pr": 324,
  "historical_failed_state_gate_push_run": "32639335287",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "product_replay_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "authority_branch_push_attempt_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "placeholder_comment_create_limit": 1,
  "carrying_comment_update_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "workflow_rerun_limit": 0,
  "dependency_install_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "pr_creation_allowed": false,
  "issue_comment_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "publication_allowed": true,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "rerun_allowed": false,
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
    "reobserve origin/main at 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 and PR331 at head 6d37e3ec7ca35da95c83b0bc03f1e6be2321950e; verify the target authority branch is absent",
    "create owner/issue333-pr331-landing-r2-v2 from 0beac2f57c1ae9caa1b11dc02dfc027c9b19e496 in an isolated worktree and commit this immutable Decision as the unique first new commit",
    "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre only after the Decision commit; generated artifacts are limited to the five listed gate paths"
  ],
  "premerge_remote_run_observations": [
    {
      "workflow": "CI",
      "workflow_path": ".github/workflows/ci.yml",
      "run_id": "32680416619",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e"
    },
    {
      "workflow": "Decision Preflight",
      "workflow_path": ".github/workflows/decision-preflight.yml",
      "run_id": "32680416560",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e"
    },
    {
      "workflow": "State Gate (pull_request)",
      "workflow_path": ".github/workflows/state-gate.yml",
      "run_id": "32680416585",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e"
    }
  ],
  "active_intent_binding_evidence": {
    "active_blob_sha256": "dfb46422678db38e53cadd94c0f4b9dc43676dc78a547e246b4cbebea82f1145",
    "source_pr": 331,
    "locked_base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
    "decision_id": "decision_20260824_issue330_trusted_remote_merge_boundary_r2_v3",
    "decision_content_sha256": "110e4c2523c08b0c53cec60a8853a9c496e37e9099ee038f0426cbf603271267",
    "command_plan_sha256": "cf6aa01247df6255520db7ef8e9220edd7e30b1740498a405984ca79bb3ca282",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "expiry": "2026-08-25T23:59:59Z"
  },
  "premerge_attestation_policy": {
    "repository": "dddd2024/reverse-agent",
    "pull_request": 331,
    "base_sha": "0beac2f57c1ae9caa1b11dc02dfc027c9b19e496",
    "head_sha": "6d37e3ec7ca35da95c83b0bc03f1e6be2321950e",
    "merge_method": "merge",
    "required_runs": [
      "CI:32680416619:attempt1",
      "Decision Preflight:32680416560:attempt1",
      "State Gate (pull_request):32680416585:attempt1"
    ],
    "comment_scope": "PR331 only",
    "placeholder_create_count": 1,
    "same_comment_update_count": 1,
    "remote_timestamps_are_runtime_authority": true,
    "chronology": "comment.created_at <= comment.updated_at < pr.merged_at",
    "local_git_timestamps_and_payload_timestamps_are_not_authority": true
  },
  "remote_landing_policy": {
    "placeholder_comment_create": "exactly_once_on_PR331",
    "carrying_comment_update": "exactly_once_on_same_comment",
    "comment_readback_required": true,
    "mark_ready": "exactly_once_on_PR331",
    "expected_head_merge": "exactly_once_with_head_6d37e3ec7ca35da95c83b0bc03f1e6be2321950e",
    "merge_tree_must_equal_candidate_head_tree": true,
    "auto_merge": false,
    "direct_main_push": false,
    "post_merge_observation_only": true,
    "workflow_rerun": false
  },
  "allowed_commands": [
    {
      "command_id": "issue333.bootstrap_and_preflight",
      "command": "observe the exact base, branch, and Decision; run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre; generate only the five named gate artifacts; require PRE_EXECUTION_AUTHORIZED with zero blockers",
      "phase": "bootstrap",
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
      "command_id": "issue333.premerge_exact_head_observation",
      "command": "observe PR331, origin/main, branch absence, exact base/head, Draft/CLEAN/MERGEABLE state, zero blocking reviews/comments, active intent, Decision and three named attempt-1 successful checks; stop on any drift",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue333.placeholder_and_attestation",
      "command": "on PR331 only, create exactly one placeholder comment, update that same comment exactly once to the schema-v2 carrying attestation, then read back the exact remote comment id/author/created_at/updated_at; create no other comment and stop on drift",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue333.mark_ready_and_expected_head_merge",
      "command": "after fresh readback and strict chronology validation, mark PR331 ready exactly once and merge exactly once with expected head 6d37e3ec7ca35da95c83b0bc03f1e6be2321950e using merge method merge; no auto-merge or direct main push",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue333.post_merge_observation",
      "command": "observe the merge commit, exact new mainline, merge tree equality, and natural CI(push) and State Gate(push) attempt-1 results; run only bounded local checks and stop without rerun or further mutation",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access", "run_checks"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/**",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml"
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
    "reverse_agent/**",
    "tests/**",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
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
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "history_rewrite",
    "extra_comment",
    "second_comment_update",
    "unbounded_pr_or_issue_mutation",
    "pr331_head_mutation",
    "retroactive_pr324_authorization",
    "post_merge_repository_mutation",
    "offensive_security_or_network_attack_work"
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
    "remote_observation_read_only_allowed": true,
    "github_issue_comment_allowed": true,
    "github_pr_comment_allowed": true,
    "github_mark_ready_allowed": true,
    "github_merge_allowed": true,
    "github_pr_creation_allowed": false,
    "authority_branch_push_allowed": false,
    "publication_allowed": true,
    "local_network_exceptions": [
      "observe PR331 and exact checks before each authorized mutation",
      "create one placeholder comment and update the same comment once on PR331",
      "read back the carrying comment and execute one mark-ready and one expected-head merge on PR331",
      "observe post-merge CI(push), State Gate(push), mainline, and merge tree only"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE333_PR331_ATTESTED_LANDING_READY_WITH_POST_MERGE_EXACT_HEAD_EVIDENCE",
  "blocked_terminal": "ISSUE333_PR331_ATTESTED_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Execute the owner-approved Issue #333 Path-B landing round for the already accepted PR #331 head `6d37e3ec7ca35da95c83b0bc03f1e6be2321950e`, using a fresh immutable Decision-first branch from `main@0beac2f57c1ae9caa1b11dc02dfc027c9b19e496`. Generate only the bounded governance artifacts, then stop at the exact remote landing boundary until every remote observation, comment timestamp, expected-head, and post-merge check is independently satisfied.

## Acceptance

1. This Decision is the unique first commit on `owner/issue333-pr331-landing-r2-v2`, the worktree starts at and remains based on `main@0beac2f57c1ae9caa1b11dc02dfc027c9b19e496`, and the Decision blob is immutable after activation.
2. PR #331 remains the sole candidate: its exact accepted head is `6d37e3ec7ca35da95c83b0bc03f1e6be2321950e`, base is the locked main SHA, it is Draft/CLEAN/MERGEABLE, and the three named attempt-1 checks remain successful.
3. Only the Decision and five generated gate paths may be changed. There are zero product, source, test, workflow, dependency, intent, authority-branch-push, or PR-creation operations.
4. Before any remote mutation, fresh readback proves the candidate, active intent, Decision, checks, and review/comment state are unchanged. Any drift stops the round.
5. The only allowed comment lifecycle is one placeholder comment on PR331, one update of that same comment to the carrying schema-v2 attestation, and one readback of runtime remote identity and timestamps. The invariant is `created_at <= updated_at < merged_at`; local Git dates and payload-declared runtime values are never authority.
6. After fresh chronology and exact-head validation, exactly one mark-ready and one expected-head merge using method `merge` may occur. No automatic merge, direct main push, rerun, extra comment, or post-merge mutation is allowed.
7. The merge tree equals the accepted PR331 head tree, and natural post-merge CI(push) and State Gate(push) evidence succeeds on the resulting exact mainline.

## Execution policy

- Treat the Issue #333 owner plan, PR331, its accepted head, the locked base, and the active intent evidence as immutable authority snapshots.
- Treat this Decision as immutable after the unique first commit. Gate generation, when separately authorized by the same Decision, is limited to the five named files; do not create gates during bootstrap unless the parent explicitly invokes that phase.
- All command records use `execution_surface: local`; remote actions are represented only by the recognized generic operations `repository_observation` and `network_access` (with `run_checks` for bounded local/post-merge checks).
- Keep generated governance risk separate from path-risk floor: gate files are governed by `governance_artifact_risk_tier: R2` and `generated_artifact_paths`; the path-risk floor covers only workflow R2 and secrets R3.
- No product or UI work, model/provider call, credentials, dependency, workflow, attack, binary, destructive operation, or history rewrite is in scope.
- Stop with exact evidence on any base/head/branch/PR/check/comment/intent/Decision drift, missing or invalid remote timestamps, chronology failure, tree mismatch, failed check, or unexpected local path.

# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue325_pr338_attested_landing_r2_v4",
  "round_id": "round_20260824_issue325_pr338_attested_landing_r2_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue325_pr338_attested_landing_r2_v1",
  "follows_last_round_id": "round_20260824_issue325_pr338_attested_landing_r2_v1",
  "previous_audit_outcome": "PR338_LANDING_V2_BLOCKED_BEFORE_REMOTE_MUTATION_STALE_PR\u0033\u0033\u0031_TEXTUAL_BINDING",
  "source_issue": 325,
  "predecessor_issue": 325,
  "candidate_pr": 338,
  "candidate_head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c",
  "candidate_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "validated_candidate_pr_state": "OPEN",
  "validated_candidate_pr_draft": true,
  "validated_candidate_pr_mergeable": "MERGEABLE",
  "validated_candidate_pr_merge_state": "CLEAN",
  "validated_candidate_nonblocking_owner_audit_review_allowed": true,
  "validated_candidate_issue_comment_count": 1,
  "validated_candidate_review_thread_count": 0,
  "workstream_id": "issue325-pr338-attested-landing-r2-v4",
  "required_branch": "owner/issue325-pr338-attested-landing-r2-v4",
  "starting_head": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "activation_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "integration_base_ref": "main",
  "base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
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
  "placeholder_comment_create_limit": 0,
  "carrying_comment_update_limit": 0,
  "corrective_comment_update_limit": 1,
  "historical_comment_id": 5391853597,
  "historical_comment_created_at": "2026-08-24T07:08:13Z",
  "historical_comment_updated_at": "2026-08-24T07:08:51Z",
  "historical_comment_body_sha256": "a4c4b5f4286938d7c2045fa15fae067b7c527f520405c1afbcd46ae5b2152b61",
  "historical_comment_body_length": 2150,
  "historical_comment_parser_found": false,
  "historical_v3_comment_lifecycle": "v3 one create and one update are immutable negative chronology evidence; v4 performs only one corrective update of this existing comment id",
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
    "reobserve origin/main at 122f91ff451929f34cd71e918d88f1512d020d1d and PR338 at head 2c3cf5a52853b2504b908f621613f0ac5003319c; verify the target authority branch is absent",
    "create owner/issue325-pr338-attested-landing-r2-v4 from 122f91ff451929f34cd71e918d88f1512d020d1d in an isolated worktree and commit this immutable Decision as the unique first new commit",
    "run startup-snapshot, transition-command-plan, transition-lint, and transition-preflight --mode pre only after the Decision commit; generated artifacts are limited to the five listed gate paths"
  ],
  "premerge_remote_run_observations": [
    {
      "workflow": "CI",
      "workflow_path": ".github/workflows/ci.yml",
      "run_id": "32698170396",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"
    },
    {
      "workflow": "Decision Preflight",
      "workflow_path": ".github/workflows/decision-preflight.yml",
      "run_id": "32698170395",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"
    },
    {
      "workflow": "State Gate (pull_request)",
      "workflow_path": ".github/workflows/state-gate.yml",
      "run_id": "32698170393",
      "attempt": 1,
      "status": "SUCCESS",
      "event": "pull_request",
      "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"
    }
  ],
  "active_intent_binding_evidence": {
    "active_blob_sha256": "f06bc6b062604e0f5089fd04058bfc255d3b977d43b7598cc72a1a91ec807712",
    "active_canonical_digest": "sha256:f15b4804d30ee9b5a11f98d03fb030902088fa97ebc099e8f67368d75824b1f4",
    "source_pr": 338,
    "locked_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
    "decision_id": "decision_20260824_issue325_landing_candidate_r2_v8",
    "decision_content_sha256": "a683acb8a89b0e335174089d05711421f9573dcc777b7a343ff09ab30b567ecf",
    "command_plan_sha256": "5f93d2aa4617024f1f90741f8fd5af4acee72a748f09ab3f445e8e7c5c4dae7b",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "expiry": "2026-08-26T23:59:59Z"
  },
  "premerge_attestation_policy": {
    "repository": "dddd2024/reverse-agent",
    "pull_request": 338,
    "base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
    "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c",
    "merge_method": "merge",
    "required_runs": [
      "CI:32698170396:attempt1",
      "Decision Preflight:32698170395:attempt1",
      "State Gate (pull_request):32698170393:attempt1"
    ],
    "comment_scope": "existing PR338 comment id 5391853597 only",
    "placeholder_create_count": 0,
    "corrective_update_existing_comment_count": 1,
    "historical_v3_create_update_immutable_negative_evidence": true,
    "remote_timestamps_are_runtime_authority": true,
    "chronology": "historical v3 created_at <= updated_at; v4 preserves created_at and requires parseable corrected body before merge",
    "local_git_timestamps_and_payload_timestamps_are_not_authority": true
  },
  "remote_landing_policy": {
    "placeholder_comment_create": false,
    "corrective_comment_update_existing_id": "exactly_once_on_PR338_comment_5391853597",
    "new_comment_allowed": false,
    "historical_v3_create_update_immutable": true,
    "comment_readback_required": true,
    "mark_ready": "exactly_once_on_PR338",
    "expected_head_merge": "exactly_once_with_head_2c3cf5a52853b2504b908f621613f0ac5003319c",
    "merge_tree_must_equal_candidate_head_tree": true,
    "auto_merge": false,
    "direct_main_push": false,
    "post_merge_observation_only": true,
    "workflow_rerun": false
  },
  "allowed_commands": [
    {
      "command_id": "issue325.bootstrap_and_preflight",
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
      "command_id": "issue325.premerge_exact_head_observation",
      "command": "observe PR338, origin/main, branch absence, exact base/head, Draft/CLEAN/MERGEABLE state, one nonblocking exact-head OWNER COMMENTED audit review permitted; zero blocking reviews, zero issue comments, zero review threads, active intent, Decision and three named attempt-1 successful checks; stop on any drift",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue325.corrective_attestation_update",
      "command": "on PR338 only, update existing issue comment id 5391853597 exactly once with a parseable schema-v2 carrying attestation; preserve id author created_at and existing chronology, then read back the corrected body; create no new comment and stop on drift",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue325.mark_ready_and_expected_head_merge",
      "command": "after fresh readback and strict chronology validation, mark PR338 ready exactly once and merge exactly once with expected head 2c3cf5a52853b2504b908f621613f0ac5003319c using merge method merge; no auto-merge or direct main push",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue325.post_merge_observation",
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
    "new_comment",
    "delete_comment",
    "second_corrective_comment_update",
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
    "pr338_head_mutation",
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
      "observe PR338 and exact checks before each authorized mutation",
      "perform one corrective update of existing PR338 comment 5391853597 and read it back; never create a new comment or update twice",
      "read back the carrying comment and execute one mark-ready and one expected-head merge on PR338",
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
  "success_terminal": "PR338_PREMERGE_REMOTE_ATTESTATION_VALID_EXPECTED_HEAD_MERGE_COMPLETE_EXACT_NEW_MAIN_CI_AND_STATE_GATE_SUCCESS",
  "blocked_terminal": "PR338_LANDING_V2_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Repair the already-created PR338 carrying comment without creating any new comment, then perform the one authorized exact-head landing sequence after the corrected schema-v2 body is read back. Historical v3 comment creation and update remain immutable negative evidence; v4 only authorizes one corrective update of comment id 5391853597.

## Acceptance

1. This Decision is the unique first commit on `owner/issue325-pr338-attested-landing-r2-v4`, the worktree starts at and remains based on `main@122f91ff451929f34cd71e918d88f1512d020d1d`, and the Decision blob is immutable after activation.
2. PR #338 remains the sole candidate: its exact accepted head is `2c3cf5a52853b2504b908f621613f0ac5003319c`, base is the locked main SHA, it is Draft/CLEAN/MERGEABLE, and the three named attempt-1 checks remain successful.
3. Only the Decision and five generated gate paths may be changed. There are zero product, source, test, workflow, dependency, intent, authority-branch-push, or PR-creation operations.
4. Before any remote mutation, fresh readback proves the candidate, active intent, Decision, checks, and review/comment state are unchanged. Any drift stops the round.
5. Historical v3 comment creation and update are immutable negative chronology evidence. V4 permits only one corrective update of existing PR338 comment `5391853597`, preserving its author and created_at, followed by readback of runtime identity and a parseable schema-v2 body. The invariant is `created_at <= updated_at < merged_at`; local Git dates and payload-declared values are never authority.
6. After fresh chronology and exact-head validation, exactly one mark-ready and one expected-head merge using method `merge` may occur. No automatic merge, direct main push, rerun, extra comment, or post-merge mutation is allowed.
7. The merge tree equals the accepted PR338 head tree, and natural post-merge CI(push) and State Gate(push) evidence succeeds on the resulting exact mainline.

## Execution policy

- This immutable v4 Decision is the only Path-B authority for the PR338 repair landing; v3 comment creation and update are historical immutable negative evidence and grant no additional mutation.
- The first local commit is this Decision and the only subsequent local commit is the generated governance commit. No source, test, workflow, dependency, intent, or product path may change.
- Do not create, delete, or update any comment except the one corrective update of existing PR338 comment 5391853597 authorized exactly once. Preserve its author and created_at; read back the corrected parseable schema-v2 body.
- Any drift in PR338 head/base/Draft/CLEAN/MERGEABLE state, review/thread/comment counts, active intent, Decision, checks, or comment identity is a hard stop. The existing one nonblocking exact-head OWNER COMMENTED review is permitted; blocking reviews, issue comments beyond the existing carrying comment, and review threads are forbidden.
- Mark-ready and merge are authorized exactly once for PR338 only after corrected attestation readback and chronology validation. Auto-merge, direct main push, rerun, extra comment, and unrelated mutation remain forbidden.
- After merge, observe naturally triggered push workflows and run read-only deterministic validation. Stop at the exact-new-main success boundary.

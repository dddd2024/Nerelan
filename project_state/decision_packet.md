# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue325_pr338_attested_landing_r2_v1",
  "round_id": "round_20260824_issue325_pr338_attested_landing_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue325_landing_candidate_r2_v8",
  "follows_last_round_id": "round_20260824_issue325_landing_candidate_r2_v8",
  "previous_audit_outcome": "PR338_EXACT_HEAD_ACCEPTED_FOR_PRE_ATTESTED_EXPECTED_HEAD_LANDING",
  "workstream_id": "issue325-pr338-attested-landing-r2-v1",
  "source_issue": 325,
  "parent_issue": 330,
  "candidate_pr": 338,
  "candidate_head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c",
  "candidate_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "historical_failed_landing_pr": 324,
  "historical_failed_state_gate_push_run": 32639335287,
  "integration_base_ref": "main",
  "base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "activation_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "starting_head": "122f91ff451929f34cd71e918d88f1512d020d1d",
  "required_branch": "owner/issue325-pr338-attested-landing-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_generated_governance": true,
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
  "runner_dispatch_limit": 0,
  "tag_or_release_limit": 0,
  "deployment_limit": 0,
  "accepted_exact_head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c",
  "required_premerge_runs": [
    {"name": "CI", "run_id": 32698170396, "run_attempt": 1, "conclusion": "success", "event": "pull_request", "workflow_file": ".github/workflows/ci.yml", "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"},
    {"name": "Decision Preflight", "run_id": 32698170395, "run_attempt": 1, "conclusion": "success", "event": "pull_request", "workflow_file": ".github/workflows/decision-preflight.yml", "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"},
    {"name": "State Gate (pull_request)", "run_id": 32698170393, "run_attempt": 1, "conclusion": "success", "event": "pull_request", "workflow_file": ".github/workflows/state-gate.yml", "head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c"}
  ],
  "active_intent_blob_sha256": "f06bc6b062604e0f5089fd04058bfc255d3b977d43b7598cc72a1a91ec807712",
  "active_intent_canonical_digest": "sha256:f15b4804d30ee9b5a11f98d03fb030902088fa97ebc099e8f67368d75824b1f4",
  "active_intent_binding": {
    "source_pr": 338,
    "locked_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
    "decision_id": "decision_20260824_issue325_landing_candidate_r2_v8",
    "decision_content_sha256": "a683acb8a89b0e335174089d05711421f9573dcc777b7a343ff09ab30b567ecf",
    "command_plan_sha256": "5f93d2aa4617024f1f90741f8fd5af4acee72a748f09ab3f445e8e7c5c4dae7b",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "expires_at": "2026-08-26T23:59:59Z"
  },
  "premerge_attestation_policy": {
    "repository": "dddd2024/reverse-agent",
    "source_pr": 338,
    "locked_base_sha": "122f91ff451929f34cd71e918d88f1512d020d1d",
    "accepted_exact_head_sha": "2c3cf5a52853b2504b908f621613f0ac5003319c",
    "allowed_merge_method": "merge",
    "required_workflows": ["CI", "Decision Preflight", "State Gate (pull_request)"],
    "required_run_attempt": 1,
    "comment_scope": "PR338 carrying comment only",
    "comment_lifecycle": "one placeholder create followed by exactly one update of the same comment id",
    "remote_timestamp_rule": "comment created_at <= comment updated_at < GitHub PR merged_at, with both comment timestamps strictly before merge",
    "local_git_timestamp_authority_allowed": false,
    "payload_declared_timestamp_authority_allowed": false
  },
  "remote_landing_policy": {
    "placeholder_comment_create": true,
    "placeholder_comment_update_same_id": true,
    "readback_required": true,
    "mark_ready_allowed": true,
    "merge_allowed": true,
    "merge_method": "merge",
    "expected_head_protection_required": true,
    "auto_merge_allowed": false,
    "direct_main_push_allowed": false,
    "force_push_allowed": false,
    "post_merge_push_observation_only": true,
    "post_merge_workflow_rerun_allowed": false
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "reobserve origin/main, PR338 exact base/head, Draft/CLEAN/MERGEABLE state, three attempt-1 successful runs, zero comments/reviews/threads and no target branch collision",
    "create this immutable Decision as the unique first commit from the locked main base before any generated governance or remote mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue325.bootstrap_and_preflight",
      "command": "verify the locked main/base/head/branch bindings and all preconditions; generate the five governance artifacts; require PRE_EXECUTION_AUTHORIZED with zero blockers before any remote mutation",
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
      "command_id": "issue325.premerge_remote_attestation",
      "command": "after fresh exact-head observation and independent audit, create exactly one placeholder comment on PR338, update that same comment exactly once with the final schema-v2 attestation, read back its immutable id/body/created_at/updated_at, and require exact PR/base/head/active intent/run bindings and timestamps strictly before merge",
      "phase": "remote_landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote",
      "operations": ["create_one_pr338_placeholder_comment", "update_same_pr338_comment_once", "readback_remote_comment"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_remote_scope": "PR338 carrying attestation comment only"
    },
    {
      "command_id": "issue325.expected_head_merge",
      "command": "after successful attestation readback and immediate re-observation, mark PR338 ready exactly once and immediately merge with merge method and exact expected-head protection; verify merged=true, first parent=locked base, second parent=accepted head, merge tree=accepted-head tree and new main equals returned merge commit",
      "phase": "remote_landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote",
      "operations": ["mark_ready_once", "expected_head_merge_once", "post_merge_read_only_observation"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_remote_scope": "PR338 only"
    },
    {
      "command_id": "issue325.post_merge_observation",
      "command": "observe naturally triggered exact-new-main CI(push) and State Gate(push) attempt 1 without rerun or dispatch; run current mainline merge validation and provider-free deterministic checks on the exact merge commit; require all PASS and stop",
      "phase": "post_merge_validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_and_local_read_only",
      "operations": ["repository_observation", "run_provider_free_checks"],
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
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
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
    "project_state/solve_tasks/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "reset",
    "clean",
    "stash",
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
    "extra_comment",
    "second_comment_update",
    "attestation_edit_after_merge",
    "modify_pr338_head",
    "modify_unrelated_issue_or_pr",
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
    "authority_branch_push_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "mark_ready_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "github_issue_comment_allowed": false,
    "github_pr_comment_allowed": true,
    "github_pr_comment_scope": "PR338 carrying attestation only",
    "github_pr_creation_allowed": false,
    "github_pr_close_allowed": false,
    "publication_allowed": false,
    "remote_observation_read_only_allowed": true,
    "post_merge_push_observation_allowed": true,
    "ci_network_exceptions": [
      "observe naturally triggered exact-new-main CI(push) and State Gate(push) attempt 1 without rerun or dispatch"
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [],
  "authorized_risk_tier": "R2",
  "success_terminal": "PR338_PREMERGE_REMOTE_ATTESTATION_VALID_EXPECTED_HEAD_MERGE_COMPLETE_EXACT_NEW_MAIN_CI_AND_STATE_GATE_SUCCESS",
  "blocked_terminal": "ISSUE325_PR338_ATTESTED_LANDING_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Perform one non-retroactive, pre-attested, expected-head-protected landing of PR #338. The accepted candidate is exactly PR338 head `2c3cf5a52853b2504b908f621613f0ac5003319c` against `main@122f91ff451929f34cd71e918d88f1512d020d1d`. The landing authority branch changes only Decision and generated governance artifacts; the product branch and PR head are immutable.

## Acceptance

1. Immediately before remote mutation, PR338 is OPEN, Draft, CLEAN and MERGEABLE; base is exact locked main; head is exact accepted head; target landing branch has no collision; no comments, reviews, unresolved threads or blocking review decision exist.
2. The exact pre-merge runs are attempt 1 SUCCESS: CI `32698170396`, Decision Preflight `32698170395`, State Gate (pull_request) `32698170393`, all bound to accepted head `2c3cf5a52853b2504b908f621613f0ac5003319c`.
3. Active schema-v2 intent is read back and binds PR338, exact base, the Issue330 Decision/Command Plan digests, three required workflows and bounded expiry; its raw active blob SHA-256 is `f06bc6b062604e0f5089fd04058bfc255d3b977d43b7598cc72a1a91ec807712` and canonical digest is `sha256:f15b4804d30ee9b5a11f98d03fb030902088fa97ebc099e8f67368d75824b1f4`.
4. The carrying comment lifecycle consists of exactly one placeholder creation and exactly one update of that same comment. The final attestation binds PR338, exact base/head, merge method, active-intent digest, exact successful runs, owner `dddd2024`, approval object id equal to the comment id and canonical digests.
5. Remote comment `created_at` and `updated_at` are timezone-aware, ordered with `created_at <= updated_at`, and both strictly precede GitHub PR `merged_at`; missing, invalid, equal or late timestamps fail closed. Payload-declared and local Git timestamps are never authority.
6. Before merge, fresh readback proves the PR remains exact and the final carrying comment is the only authorized comment. Mark-ready occurs exactly once, followed immediately by one merge-method merge with expected-head protection; auto-merge is never enabled.
7. Merge evidence proves `merged=true`, first parent equals locked base, second parent equals accepted head, merge tree equals accepted-head tree and `origin/main` advances exactly to the returned merge commit.
8. Naturally triggered exact-new-main CI(push) and State Gate(push) are observed without rerun or dispatch and both are attempt 1 SUCCESS. Current mainline merge validation and provider-free deterministic checks pass on the exact merge commit.
9. PR324 State Gate(push) run `32639335287` remains FAILURE negative evidence and is never rerun or reclassified as authorized.
10. No product/source/test/workflow/intent mutation, authority branch push, extra comment, unrelated issue/PR mutation, provider/model call, credential access, dependency install, offensive-security work, tag, release, deployment, force push, rebase, reset, amend, mark-ready outside PR338 or merge outside PR338 occurs.

## Execution policy

- This immutable Decision is the only Path-B authority for the landing round; Issue #325 is the source work item but does not itself authorize mutation.
- The first local commit is this Decision and the only subsequent local commit is the generated governance commit. If the machine requires an authority branch push, stop and report instead of expanding scope.
- The PR338 comment is the only permitted remote comment. Create one placeholder, update the same object once, read it back, and never edit it after merge.
- Any drift in base, head, mergeability, Draft state, checks, intent, comment count, review state, audit, timestamps or expected merge topology is a hard stop. Do not rerun checks to manufacture evidence.
- Mark-ready and merge are explicitly authorized only for PR338 in this exact expected-head sequence. Owner attestation, automatic merge, direct main push and all unrelated publication remain forbidden.
- After merge, observe naturally triggered push workflows and run read-only deterministic validation. Stop at the exact-new-main success boundary; no further mutation is authorized by this Decision.

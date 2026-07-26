# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260726_governance_migration_pr44_merge_v1","round_id":"round_20260726_governance_migration_pr44_merge_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260726_governance_migration_owner_manual_merge_rework_v3",
  "follows_last_round_id": "round_20260726_governance_migration_owner_manual_merge_rework_v3",
  "previous_audit_outcome": "ACCEPTED_PR44_HEAD_7c19e741_AUDIT_PASSED",
  "workstream_id": "governance-migration-pr44-merge-v1",
  "source_issue": 43,
  "program_issue": 26,
  "required_branch": "codex/governance-migration-owner-manual-merge-v1",
  "starting_head": "7c19e74194ec0befb34edca6a88c5c668bd2d968",
  "activation_base_sha": "964cd647afc3d51a7fdf855080351da53c5e79ef",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "stop_after_preflight_authorized": true,
  "one_time_merge_authorization": true,
  "merge_authorization_scope": {
    "repository": "dddd2024/reverse-agent",
    "pr_number": 44,
    "source_issue": 43,
    "accepted_exact_head_sha": "7c19e74194ec0befb34edca6a88c5c668bd2d968",
    "activation_base_sha": "964cd647afc3d51a7fdf855080351da53c5e79ef",
    "required_branch": "codex/governance-migration-owner-manual-merge-v1",
    "merge_method": "merge",
    "expected_head_protection": "required",
    "independent_audit_result": "ACCEPTED",
    "merge_allowed_for_agent": false,
    "mark_ready_allowed_for_agent": false,
    "owner_manual_mark_ready_allowed_after_preflight": true,
    "owner_manual_merge_allowed_after_preflight": true
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md", "project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot", "status.git_status", "status.pr_observation", "gate.command_plan", "gate.transition_lint", "gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.git_rev_parse_head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.git_rev_parse_origin_main","command":"git rev-parse origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.git_merge_base","command":"git merge-base HEAD origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.pr_observation","command":"gh pr view 44 --json number,isDraft,state,headRefOid,baseRefOid,mergeable,mergeStateStatus","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.pr_checks","command":"gh pr checks 44","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"status.pr_reviews","command":"gh api repos/dddd2024/reverse-agent/pulls/44/reviews --jq length","phase":"status","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]}
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
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "tests/test_minimal_integration_baseline_docs.py",
    "docs/run_closeout.md",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "tests/test_minimal_integration_baseline_docs.py",
    "reverse_agent/**",
    ".github/workflows/**",
    ".codex-skills/**",
    "docs/run_closeout.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    "tests/test_project_gate.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifactindex.json"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "agent_initiated_merge",
    "agent_initiated_mark_ready",
    "automation_initiated_merge",
    "automation_initiated_mark_ready",
    "GitHub auto-merge",
    "automatic merge",
    "tag or release",
    "cross-repository publication",
    "unbounded network access",
    "credentials or secrets access",
    "unknown-binary execution",
    "model API invocation from repository code",
    "external reverse-tool invocation",
    "runner dispatch",
    "workflow dispatch",
    "history rewrite",
    "product source changes",
    "dependency changes",
    "workflow changes",
    "Gate runtime changes",
    "LangGraph runtime changes",
    "new Gate implementation",
    "new receipt schema",
    "new verifier implementation",
    "modifying AGENTS.md",
    "modifying docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "modifying docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "modifying docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "modifying .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "modifying tests/test_minimal_integration_baseline_docs.py",
    "modifying docs/run_closeout.md",
    "modifying .codex-skills/**",
    "creating new implementation commit",
    "creating new PR",
    "modifying PR #44 head",
    "pushing new code",
    "mark-ready or merge before PRE_EXECUTION_AUTHORIZED",
    "using new R1 carve-out to self-authorize this migration PR",
    "R2/R3 PR using the new lightweight merge path"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "agent_initiated_merge_allowed": false,
    "agent_initiated_mark_ready_allowed": false,
    "owner_manual_mark_ready_allowed_after_preflight": true,
    "owner_manual_merge_allowed_after_preflight": true,
    "merge_method": "merge",
    "expected_head_sha": "7c19e74194ec0befb34edca6a88c5c668bd2d968",
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "gh pr view 44",
      "gh pr checks 44",
      "gh api repos/dddd2024/reverse-agent/pulls/44/reviews"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": "docs/architecture/**", "minimum_risk": "R2"},
    {"pattern": "docs/roadmap/**", "minimum_risk": "R2"},
    {"pattern": ".github/ISSUE_TEMPLATE/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R1"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ],
  "scope_policy": {
    "scope": "governance_migration_pr44_merge_authorization",
    "one_time_merge_authorization": true,
    "merge_authorization_only": true,
    "no_implementation_commits": true,
    "no_source_changes": true,
    "no_governance_doc_changes": true,
    "no_test_changes": true,
    "no_template_changes": true,
    "no_workflow_changes": true,
    "no_pr_body_changes": true,
    "no_new_pr": true,
    "allowed_activities": [
      "read_and_re_observe_github_git_pr_ci_review_state",
      "write_decision_packet_md",
      "generate_compiler_owned_gate_evidence",
      "run_startup_snapshot",
      "run_transition_command_plan",
      "run_transition_lint",
      "run_transition_preflight_pre",
      "after_pre_execution_authorized_prepare_owner_manual_mark_ready_and_merge_steps",
      "after_owner_merge_read_only_post_merge_verification",
      "after_successful_verification_close_issue_43"
    ]
  },
  "merge_semantics": {
    "merge_target": "PR #44",
    "merge_method": "merge",
    "expected_head_sha": "7c19e74194ec0befb34edca6a88c5c668bd2d968",
    "expected_base_sha": "964cd647afc3d51a7fdf855080351da53c5e79ef",
    "expected_head_protection": "required (--match-head-commit or equivalent)",
    "independent_audit_result": "ACCEPTED",
    "audit_accepted_head": "7c19e74194ec0befb34edca6a88c5c668bd2d968",
    "audit_comments_are_evidence_not_authority": true,
    "merge_actor_must_be_owner_maintainer": true,
    "agent_must_not_mark_ready_or_merge": true,
    "carve_out_self_authorization_forbidden": "The new R1 carve-out cannot be used to self-authorize this migration PR. This Decision is the sole Path-B authority for the merge.",
    "pre_merge_re_observation_required": true,
    "pre_merge_re_observation_conditions": [
      {"id": "C1", "description": "origin/main == 964cd647afc3d51a7fdf855080351da53c5e79ef", "expected_value": "964cd647afc3d51a7fdf855080351da53c5e79ef"},
      {"id": "C2", "description": "PR #44 headRefOid == 7c19e74194ec0befb34edca6a88c5c668bd2d968", "expected_value": "7c19e74194ec0befb34edca6a88c5c668bd2d968"},
      {"id": "C3", "description": "independent audit accepted head == 7c19e74194ec0befb34edca6a88c5c668bd2d968", "expected_value": "7c19e74194ec0befb34edca6a88c5c668bd2d968"},
      {"id": "C4", "description": "PR baseRefOid == 964cd647afc3d51a7fdf855080351da53c5e79ef", "expected_value": "964cd647afc3d51a7fdf855080351da53c5e79ef"},
      {"id": "C5", "description": "exact-head CI all SUCCESS", "expected_value": "all_pass"},
      {"id": "C6", "description": "Decision Preflight SUCCESS", "expected_value": "PRE_EXECUTION_AUTHORIZED"},
      {"id": "C7", "description": "State Gate SUCCESS", "expected_value": "PASS"},
      {"id": "C8", "description": "PR mergeable == MERGEABLE", "expected_value": "MERGEABLE"},
      {"id": "C9", "description": "mergeStateStatus == CLEAN", "expected_value": "CLEAN"},
      {"id": "C10", "description": "unresolved blocking review threads == 0", "expected_value": 0},
      {"id": "C11", "description": "PR still Draft and not merged", "expected_value": "isDraft=true, merged=false"},
      {"id": "C12", "description": "no concurrent Agent modifying or publishing that branch", "expected_value": "no_concurrent_activity"}
    ],
    "any_condition_failed_action": "STOP immediately and do not proceed to mark-ready or merge",
    "post_merge_verification_required_after_owner_merge": [
      "PR merged == true",
      "merge commit SHA recorded",
      "new origin/main == merge commit SHA",
      "merged PR head == accepted exact head 7c19e74194ec0befb34edca6a88c5c668bd2d968",
      "close Issue #43",
      "output final closeout report"
    ]
  },
  "stop_conditions": [
    "transition_lint_failure",
    "preflight_not_authorized",
    "any_pre_merge_re_observation_condition_failed",
    "scope_violation_detected",
    "independent_audit_withdrawn_or_overturned",
    "pr_head_changed_from_accepted_exact_head",
    "origin_main_drifted_from_activation_base_sha",
    "ci_failure_on_exact_head",
    "blocking_review_thread_present",
    "pr_no_longer_draft_or_already_merged",
    "concurrent_agent_activity_detected",
    "agent_attempted_mark_ready_or_merge",
    "attempted_force_push_rebase_squash_or_history_rewrite",
    "attempted_github_auto_merge",
    "attempted_to_use_new_r1_carve_out_for_self_authorization",
    "implementation_commit_created",
    "source_or_governance_or_test_or_template_or_workflow_file_modified",
    "pr_body_modified",
    "new_pr_created"
  ]
}
```

## DECISION_PACKET

### Goal

One-time bounded Path-B merge authorization for PR #44 (governance migration: R1 owner manual merge carve-out). This Decision authorizes the repository owner/maintainer to personally perform `mark-ready` and `merge` (method = `merge`, with `--match-head-commit` or equivalent expected-head protection) of PR #44 at exact head `7c19e74194ec0befb34edca6a88c5c668bd2d968`, after all twelve pre-merge re-observation conditions hold and only after `PRE_EXECUTION_AUTHORIZED` from transition-preflight.

This Decision does NOT authorize the Agent to mark-ready or merge. It does NOT modify any product source, governance docs, issue templates, tests, workflows, or PR #44 head. It does NOT create a new implementation commit. It does NOT use the new R1 carve-out to self-authorize (the new carve-out has not reached `main` yet; this Decision is the sole Path-B authority for the merge).

### Authority and evidence boundary

- This is a Path-B (R2) Decision. Authority is this approved Decision + generated command_plan.json + PRE_EXECUTION_AUTHORIZED.
- The independent audit result on PR #44 head `7c19e74194ec0befb34edca6a88c5c668bd2d968` is ACCEPTED evidence, recorded as audit comments on Issue #43. Audit comments are evidence, not execution authority. They inform the Decision shape but do not themselves authorize the merge.
- The accepted exact head is `7c19e74194ec0befb34edca6a88c5c668bd2d968`. Any head movement invalidates this merge authorization.

### Pre-merge re-observation (all 12 must hold immediately before owner merge)

1. `origin/main` == `964cd647afc3d51a7fdf855080351da53c5e79ef` (no main drift)
2. PR #44 `headRefOid` == `7c19e74194ec0befb34edca6a88c5c668bd2d968` (no head movement)
3. independent audit accepted head == `7c19e74194ec0befb34edca6a88c5c668bd2d968`
4. PR `baseRefOid` == `964cd647afc3d51a7fdf855080351da53c5e79ef`
5. exact-head CI == all SUCCESS
6. Decision Preflight == PRE_EXECUTION_AUTHORIZED
7. State Gate == SUCCESS
8. PR `mergeable` == MERGEABLE
9. `mergeStateStatus` == CLEAN
10. unresolved blocking review threads == 0
11. PR still Draft and not merged
12. no concurrent Agent modifying or publishing that branch

Any condition failed: STOP immediately. Do not proceed to mark-ready or merge.

### Owner manual merge sequence (after PRE_EXECUTION_AUTHORIZED and re-observation PASS)

```text
owner/maintainer manual mark-ready (personally via GitHub UI or owner-controlled CLI)
-> immediate owner/maintainer manual merge (merge method = merge,
   with --match-head-commit or equivalent expected-head protection)
-> post-merge verification (merged == true, mergeCommit.oid recorded,
   new origin/main == mergeCommit.oid, merged PR head == 7c19e74194ec0befb34edca6a88c5c668bd2d968)
-> close Issue #43
-> output final closeout report
```

The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used. `gh pr ready 44` and `gh pr merge 44 --merge` run personally by an owner/maintainer are permitted under this Decision.

### Stop Conditions

Stop immediately when:
- transition-lint fails;
- transition-preflight does not return PRE_EXECUTION_AUTHORIZED;
- any of the 12 pre-merge re-observation conditions fails;
- independent audit is withdrawn or overturned;
- PR head changes from `7c19e74194ec0befb34edca6a88c5c668bd2d968`;
- `origin/main` drifts from `964cd647afc3d51a7fdf855080351da53c5e79ef`;
- CI fails on exact head;
- blocking review thread present;
- PR no longer Draft or already merged;
- concurrent Agent activity detected on the branch;
- Agent attempts mark-ready or merge (forbidden — only owner/maintainer may perform these);
- attempted force push, rebase, squash, or history rewrite;
- attempted GitHub auto-merge;
- attempted to use the new R1 carve-out for self-authorization;
- implementation commit is created;
- any source, governance, test, template, or workflow file is modified;
- PR #44 body is modified;
- a new PR is created.

# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260725_merge_run_closeout_legacy_doc_pilot_v1","round_id":"round_20260725_merge_run_closeout_legacy_doc_pilot_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260725_merge_readme_alignment_pilot_v1",
  "follows_last_round_id": "round_20260725_merge_readme_alignment_pilot_v1",
  "previous_audit_outcome": "R1_RUN_CLOSEOUT_LEGACY_DOC_PILOT_EXACT_HEAD_ACCEPTED",
  "workstream_id": "merge-run-closeout-legacy-doc-pilot-v1",
  "source_issue": 42,
  "program_issue": 26,
  "source_work_item": 40,
  "source_pull_request": 41,
  "required_branch": "plan/merge-run-closeout-legacy-doc-pilot-v1",
  "starting_head": "649667a731ff5657197f2a21dd760e0631aa61a9",
  "activation_base_sha": "649667a731ff5657197f2a21dd760e0631aa61a9",
  "accepted_pr_head_sha": "16a32acc35e1c3839a8002c42fee77b7c7565f02",
  "audited_pr_base_sha": "649667a731ff5657197f2a21dd760e0631aa61a9",
  "expected_current_main_sha": "649667a731ff5657197f2a21dd760e0631aa61a9",
  "main_tree_equivalence_required": false,
  "merge_method": "merge",
  "close_source_work_item_after_merge": true,
  "source_work_item_to_close": 40,
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "auto_merge_allowed": false,
  "stop_after_exact_head_ci": false,
  "stop_immediately_after_merge_verification": true,
  "bootstrap_exception_files": ["project_state/decision_packet.md","project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot","status.git_status","gate.command_plan","gate.transition_lint","gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"observe.current_main","command":"git fetch origin main && test \"$(git rev-parse origin/main)\" = \"649667a731ff5657197f2a21dd760e0631aa61a9\"","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observe.pr41","command":"gh pr view 41 --repo dddd2024/reverse-agent --json state,isDraft,mergeable,mergeStateStatus,headRefOid,baseRefOid,statusCheckRollup,reviewDecision","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.mark_ready","command":"gh pr ready 41 --repo dddd2024/reverse-agent","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["mark_pr_ready_for_review","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.merge_pr41","command":"gh pr merge 41 --repo dddd2024/reverse-agent --merge --match-head-commit 16a32acc35e1c3839a8002c42fee77b7c7565f02","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["merge","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"verify.pr41_merged","command":"gh pr view 41 --repo dddd2024/reverse-agent --json state,isDraft,mergedAt,mergeCommit,headRefOid,baseRefOid","phase":"verification","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"verify.main_after_merge","command":"git fetch origin main && git rev-parse origin/main","phase":"verification","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.close_issue_40","command":"gh issue close 40 --repo dddd2024/reverse-agent --reason completed","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_close","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": ["project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md","README.md","docs/run_closeout.md","docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md","docs/architecture/SOURCE_OF_TRUTH_MATRIX.md"],
  "generated_artifact_paths": ["project_state/gates/startup_snapshot.json","project_state/gates/command_plan.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": ["reverse_agent/**",".github/**",".codex-skills/**","AGENTS.md","README.md","docs/**","tests/**","pyproject.toml","pytest.ini","setup.cfg"],
  "forbidden_operations": ["direct push to main","force push","rebase","squash","tag","release","unknown_binary_execution","model_api_invocation","external_reverse_tool_invocation","runner_dispatch","workflow_dispatch","automatic_merge","branch_creation","pull_request_creation","git_config_modification","history_rewrite","secret_access","destructive_operations","product_source_changes","dependency_changes","workflow_changes","documentation_changes","test_changes","new_gate_implementation","new_receipt_schema","new_verifier_implementation","langgraph_runtime_expansion","agent_registry","web_console","spec_kit_installation","open_swe_installation","openhands_installation","trust_layer_implementation","binary_evidence_firewall_implementation","hostile_binary_analysis_implementation","governance_simplification_changes","phase_b_governance_simplification","append_commit_to_pr41","modify_pr41_branch"],
  "capability_policy": {"git_push_from_local_executor":false,"branch_creation_from_local_executor":false,"pull_request_creation_from_local_executor":false,"merge_from_local_executor":true,"mark_pr_ready_for_review":true,"local_network_exceptions":["git fetch origin main","gh pr view 41 --repo dddd2024/reverse-agent","gh pr ready 41 --repo dddd2024/reverse-agent","gh pr merge 41 --repo dddd2024/reverse-agent --merge --match-head-commit 16a32acc35e1c3839a8002c42fee77b7c7565f02","gh issue close 40 --repo dddd2024/reverse-agent --reason completed"]},
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/decision_packet.md","project_state/gates/**"],
  "path_risk_floor": [{"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},{"pattern":"project_state/gates/**","minimum_risk":"R2"}],
  "scope_policy": {"scope":"protected_merge_of_accepted_run_closeout_legacy_doc_pilot","allow_product_source":false,"allow_dependency_changes":false,"allow_workflow_changes":false,"allow_test_additions":false,"allow_documentation_changes":false,"allow_template_changes":false,"allow_governance_simplification":false},
  "stop_conditions": ["transition_lint_failure","preflight_not_authorized","working_tree_not_clean","current_main_sha_mismatch","pr41_not_open","pr41_not_draft_before_mark_ready","pr41_head_sha_mismatch","pr41_base_sha_mismatch","pr41_checks_not_successful","pr41_not_mergeable_or_clean","unresolved_review_thread","mark_ready_failure","merge_failure","merged_head_mismatch","issue40_close_failure","scope_violation_detected","phase_b_governance_simplification_attempted"]
}
```

## DECISION_PACKET

### Goal

Perform exactly one protected Path-B merge of accepted `docs/run_closeout.md` legacy-compatibility pilot PR #41 without changing its accepted head, then close source Work Item Issue #40 as completed. This Decision does not authorize Phase B governance simplification work.

### Authority and bindings

This Decision is activated by the repository owner/planning authority on branch `plan/merge-run-closeout-legacy-doc-pilot-v1`. It binds:

- `source_issue`: #42 (PLANNING_REFERENCE_ONLY handoff Issue)
- `source_work_item`: #40 (the approved R1 Work Item, `r1-approved` by `dddd2024` at `2026-07-25T09:58:59Z`)
- `source_pull_request`: #41 (Draft PR, exact accepted head `16a32acc35e1c3839a8002c42fee77b7c7565f02`)
- `expected_current_main_sha`: `649667a731ff5657197f2a21dd760e0631aa61a9` (must not have moved)
- `audited_pr_base_sha`: `649667a731ff5657197f2a21dd760e0631aa61a9` (PR base equals current main; no tree-equivalence drift to reconcile)
- `accepted_pr_head_sha`: `16a32acc35e1c3839a8002c42fee77b7c7565f02`
- `merge_method`: `merge` (no rebase, no squash)
- `close_source_work_item_after_merge`: close Issue #40 as completed after merge verification succeeds

### Authorized sequence

1. Generate and validate the Decision-bound Command Plan and require `PRE_EXECUTION_AUTHORIZED`.
2. Verify current `origin/main` is exactly `649667a731ff5657197f2a21dd760e0631aa61a9`.
3. Verify PR #41 is open, Draft, clean/mergeable, exact head `16a32acc35e1c3839a8002c42fee77b7c7565f02`, exact base `649667a731ff5657197f2a21dd760e0631aa61a9`, and its exact-head CI succeeded.
4. Mark PR #41 ready only as the immediate precondition for this merge.
5. Merge with merge-commit method and `--match-head-commit 16a32acc35e1c3839a8002c42fee77b7c7565f02` protection.
6. Verify `merged=true`, record `mergeCommit` and new `origin/main` SHA.
7. Close Issue #40 as completed.
8. Stop immediately. Do not begin Phase B governance simplification.

### Explicit prohibitions

This Decision does **not** authorize any of the following:

- Modifying the PR #41 branch (`codex/run-closeout-legacy-doc-pilot-v1`) or appending commits to it.
- Modifying any product source, documentation, test, workflow, dependency, template, or governance file.
- Rebase, squash, force-push, auto-merge, or direct push to `main`.
- Tag or release operations.
- Starting Phase B governance simplification (e.g. evaluating or implementing lightweight owner-manual-merge for ordinary R1). That work requires a separate R0 planning task and a separate approved Work Item/Decision.
- Any operation outside the exact command sequence listed in `allowed_commands`.

### Stop conditions

Stop immediately and do not proceed to merge if any of the following is true:

- `transition-lint` or `transition-preflight` fails, or `PRE_EXECUTION_AUTHORIZED` is not achieved.
- The working tree is not clean.
- `origin/main` has moved away from `649667a731ff5657197f2a21dd760e0631aa61a9`.
- PR #41 is not open, not Draft (before mark-ready), not mergeable/clean, or has unresolved blocking review threads.
- PR #41 `headRefOid` != `16a32acc35e1c3839a8002c42fee77b7c7565f02` or `baseRefOid` != `649667a731ff5657197f2a21dd760e0631aa61a9`.
- PR #41 exact-head CI is not successful.
- Mark-ready or merge command fails.
- Merged head does not match the accepted head.
- Issue #40 close command fails.
- Any scope violation or attempt to begin Phase B governance simplification.

### Completion

Completion requires: PR #41 merged with merge-commit method using `--match-head-commit` protection; `merged=true` verified; new `origin/main` SHA recorded; Issue #40 closed as completed. No other action is authorized by this Decision.

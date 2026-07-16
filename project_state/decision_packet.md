```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260716_closeout_order_provenance_rework_v1",
  "round_id": "round_20260716_closeout_order_provenance_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260710_post_closeout_required_audit_truth_rework_v1",
  "follows_last_round_id": "round_20260710_post_closeout_required_audit_truth_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "canonical_closeout_order_required": true,
  "execution_log_chronology_required": true,
  "report_finalization_runtime_provenance_required": true,
  "final_archive_refresh_after_report_finalization_required": true,
  "round_manifest_provenance_fields_required": true,
  "report_alias_parity_required": true,
  "state_manifest_freshness_regression_preservation_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260716_closeout_order_provenance_rework_v1/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/execution_report.md",
    "project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/pytest_result.txt",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "reverse_agent/project_runner_contract.py",
    "docs/roadmap/closeout_order_provenance_rework_plan.md"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/project_agent_runner.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/user_solve_*.py",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/jobs/*",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite",
    "docs/roadmap/*"
  ],
  "publication_authorization": {
    "granted_by_user": true,
    "applies_to": "manually_invoked_execution_agent_after_required_validation",
    "branch_strategy": "one_short_lived_branch_per_decision_or_pull_request",
    "allowed_branch": "agent/closeout-order-provenance-rework-v1",
    "base_branch": "main",
    "multiple_commits_on_same_branch_allowed": true,
    "reuse_same_branch_for_review_fixes_allowed": true,
    "new_branch_per_commit_required": false,
    "commit_allowed": true,
    "push_allowed": true,
    "draft_pr_allowed": true,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "merge_allowed": false,
    "rebase_allowed": false,
    "tag_mutation_allowed": false,
    "remote_branch_deletion_allowed": false,
    "workflow_mutation_allowed": false,
    "secrets_mutation_allowed": false,
    "git_add_all_allowed": false,
    "stage_only_explicit_allowed_paths": true,
    "publish_only_after_required_validation": true,
    "command_plan_must_explicitly_authorize_publication_commands": true,
    "publication_blocked_when_credentials_or_command_authority_missing": true,
    "delete_branch_after_merge_recommended": true
  }
}
```

# DECISION_PACKET

## 1. Goal

Complete one bounded `project_governance` rework round that repairs the closeout-order and provenance defects identified by the independent audit of `round_20260710_post_closeout_required_audit_truth_rework_v1`.

Establish one observable lifecycle:

```text
implementation and tests
→ preliminary report generation
→ run-closeout evidence generation
→ report finalization from observed run-closeout evidence
→ report-summary / execution-log / final-check refresh
→ final close-round archive refresh
→ archived/live parity verification
```

The system must not claim that `close-round` was the final lifecycle action when the raw transcript proves that a later lifecycle-mutating command occurred. Runtime evidence must prove that report finalization occurred before the final archive refresh.

The user also grants controlled publication permission. The manually invoked execution Agent may use one short-lived branch, `agent/closeout-order-provenance-rework-v1`, for this complete decision and its review fixes. The branch may contain multiple commits. A new branch must not be created for each commit. After required validation, the Agent may push that branch and may open a Draft PR to `main` only when publication commands are explicitly authorized by the current command-plan and credentials are available.

## 2. Current Evidence

Current task authority is `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only.

Current mainline is `project_governance`. The previous independent audit outcome is `REWORK_REQUIRED` because:

1. The raw `pytest_result.txt` and synthesized `execution_log.json` recorded an outer sequence in which `close-round` was followed by `run-closeout`.
2. The previous final gate nevertheless reported `close_round_is_last_command_block=PASS`.
3. The previous round manifest archive timestamp preceded the final `run_closeout_result.json` timestamp referenced by report finalization.
4. Required Audit items 25 and 26 relied mainly on implementation descriptions rather than observed runtime provenance proving report finalization followed by final archive refresh.

Current evidence also shows that `reverse_agent/project_runner_contract.py` is a non-dispatching foundation, sets `dispatch_enabled=false`, `executable=false`, and `external_invocations.remote_mutation=false`. This round must not claim that the existing automated Runner can publish. The publication permission applies only to a manually invoked execution Agent operating under this Decision and an explicit command-plan.

Existing foundations that must be reused rather than duplicated include:

- project_gate hard gates;
- command-plan authority;
- execution-log synthesis;
- report-summary synthesis;
- run-closeout and close-round archive;
- final-check;
- policy-lint and prompt-consistency;
- state-manifest freshness;
- post-final context synchronization;
- Job and Runner Contract foundations;
- manual-mode orchestrator foundations.

Missing reverse-solving artifacts and legacy `negative_results.json` scope metadata are non-blocking because this is not a sample-solving round. No runtime reverse tool, model API, Web service, database, scheduler, cleanup-apply, or automated Runner dispatch is authorized.

## 3. Do Not Do

Do not:

- implement Goal, Plan, Task, Scheduler, multi-workstream namespace, Code Review Plane, frontend scheduling, LangGraph, databases, queues, or real Runner dispatch;
- modify `reverse_agent/project_runner_contract.py` or claim that it supports remote mutation;
- modify `.github/workflows`, `.codex-skills`, frontend, User Solve, solver, harness, sample, or reverse-tool code;
- alter `task_packet.json`, `current_state.json`, `artifact_index.json`, `negative_results.json`, or `workstreams.json`;
- run dynamic reverse probes, debuggers, emulators, hooks, or model APIs;
- read the full `solve_reports/` tree or `PROJECT_PROGRESS_LOG.txt`;
- push directly to `main`;
- force-push, merge, rebase, tag, edit secrets, delete remote branches, or edit workflows;
- create a new branch for each commit;
- use `git add -A` or stage unrelated files;
- publish before required validation passes;
- execute publication commands that are absent from the current command-plan;
- treat user publication authorization as proof that credentials, Runner dispatch, or command authority exist.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260710_post_closeout_required_audit_truth_rework_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

Read-only context:

- `reverse_agent/project_runner_contract.py`
- `docs/roadmap/closeout_order_provenance_rework_plan.md`

## 5. Required Audit

The final report must answer each item using current observed artifact fields, timestamps, digests, command blocks, or test outputs:

1. Is `decision_meta` valid, APPROVED, and bound to `project_governance`?
2. Is `reverse-agent-iteration@v2` active in the current skill registry?
3. Is the previous independent audit outcome recorded as `REWORK_REQUIRED`?
4. Is task_packet treated as background only?
5. What exact raw command ordering defect existed in the previous round?
6. Does the new execution log preserve actual chronological order without reordering?
7. Is `close-round` the final lifecycle-mutating project gate action?
8. Are any later publication commands classified separately and prevented from mutating tracked file content?
9. Does report finalization contain current observed run-closeout evidence?
10. Is `report_finalized_at` recorded from an actual runtime event?
11. Is `archive_refreshed_at` recorded from an actual runtime event?
12. Is `archive_refreshed_at` later than or equal to `report_finalized_at`?
13. Does the round manifest record the final archive refresh basis?
14. Do archived reports and pytest results match final live files?
15. Do both report aliases agree on summary and finalization data?
16. Does final-check fail on intentionally inverted closeout ordering?
17. Does final-check fail when archive refresh predates report finalization?
18. Does final-check fail when the final archive refresh is missing?
19. Does command-plan cover every required engineering command and expected exit code?
20. Were omitted or unauthorized commands absent?
21. Were all modified source and test paths within scope?
22. Were all forbidden paths left untouched?
23. Did the focused pytest command pass with exit code 0?
24. Did state-manifest freshness and post-final context sync remain current?
25. Is publication authorization limited to `agent/closeout-order-provenance-rework-v1`?
26. Were multiple commits, if any, kept on the same decision branch rather than separate per-commit branches?
27. Was direct push to `main`, force push, merge, rebase, tag mutation, workflow mutation, and secret mutation absent?
28. Were only explicitly allowed files staged?
29. If publication occurred, was it authorized by command-plan and performed only after required validation?
30. If publication could not occur, was it reported as blocked rather than bypassing command authority or credential requirements?

## 6. Implementation Scope

Implement the smallest compatible correction in `reverse_agent/project_gate.py` and, only where unavoidable, `reverse_agent/project_state.py`.

Required engineering behavior:

1. Define a canonical closeout lifecycle and make its runtime phases observable.
2. Preserve raw transcript chronology in `pytest_result.txt`, `run_closeout_execution_log.json`, and `execution_log.json`.
3. Replace any check that infers the final command from a planned or synthesized order with a check against the raw observed transcript.
4. Distinguish the last lifecycle-mutating project-gate action from optional post-validation publication delivery actions.
5. Record `report_finalized_at`, `archive_refreshed_at`, and `archive_refresh_basis` in current round evidence.
6. Require `archive_refreshed_at >= report_finalized_at`.
7. Require a final archive refresh after report finalization.
8. Verify archived/live report and pytest parity after the final archive refresh.
9. Reject Required Audit answers that use only code-path descriptions when runtime provenance is required.
10. Preserve backward compatibility for older round manifests that lack the new fields; legacy manifests remain readable but cannot satisfy this round's acceptance contract.
11. Preserve existing state-manifest freshness, report alias parity, command-plan, execution-log, policy-lint, prompt-consistency, and post-final context behavior.

Publication policy for the manually invoked execution Agent:

- use or create only `agent/closeout-order-provenance-rework-v1` for this decision;
- allow multiple focused commits on that same branch, including implementation, tests, and review fixes;
- stage only explicit allowed paths;
- push only the dedicated branch;
- optionally open a Draft PR targeting `main`;
- do not merge the PR;
- do not delete the branch; branch deletion is recommended after merge by the maintainer;
- execute publication only when the current command-plan explicitly authorizes the publication commands;
- when authorization or credentials are missing, stop publication and report `PUBLICATION_BLOCKED` without weakening engineering acceptance evidence.

Generated artifacts may include current-round gate JSON, reports, pytest result, state manifest, context packet, and the new round archive. Do not generate unrelated artifacts.

## 7. Tests

Run the exact focused suite:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py tests/test_project_state.py -q
```

Add focused regression coverage for:

1. raw transcript containing `close-round` followed by a lifecycle-mutating `run-closeout` fails;
2. execution-log order differing from raw transcript fails;
3. final gate claiming the wrong last lifecycle command fails;
4. `archive_refreshed_at < report_finalized_at` fails;
5. missing final archive refresh fails;
6. archived/live report mismatch fails;
7. archived/live pytest mismatch fails;
8. Required Audit items 25 and 26 without runtime provenance fail;
9. correct lifecycle order passes;
10. legacy round manifests remain readable but cannot satisfy the new current-round provenance requirement;
11. publication commands, when present, are recognized as a separate delivery phase and do not broaden engineering file scope;
12. direct-main, force-push, merge, rebase, workflow, secret, tag, remote-delete, or wrong-branch publication policy is rejected;
13. multiple commits on the same authorized branch are permitted;
14. branch-per-commit behavior is not required or generated.

Then run the current gate sequence authorized by the generated command-plan, including decision-lint, preflight, gate-profile, command-plan, report-summary, execution-log, final-check, run-closeout, final close-round, archive parity, and post-final context sync as applicable.

Publication is not an excuse to skip or weaken any test or gate. If publication commands are not present in command-plan, do not execute them.

Write the exact commands, stdout/stderr, exit codes, and final summary to `project_state/pytest_result.txt`, `project_state/codex_execution_report.md`, `project_state/execution_report.md`, and current gate artifacts.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` when:

- decision-lint, preflight, command-plan, pytest, report-summary, execution-log, final-check, run-closeout, close-round, archive parity, state-manifest freshness, or context sync fails;
- raw and synthesized command chronology disagree;
- report finalization cannot be tied to observed run-closeout evidence;
- final archive refresh cannot be proven to occur after report finalization;
- archived and live reports or pytest results differ;
- the fix requires modifying a forbidden file or widening into another mainline;
- the fix requires redesigning Jobs, Runner Contract, orchestrator, frontend, database, scheduler, workflow, User Solve, or reverse-solving code;
- unrelated working-tree changes cannot be isolated safely;
- publication would require direct push to `main`, force push, merge, rebase, tag mutation, workflow mutation, secret mutation, remote branch deletion, or staging unrelated files;
- the active branch is not `agent/closeout-order-provenance-rework-v1`;
- publication commands are absent from command-plan;
- GitHub credentials or remote access are unavailable;
- publication fails; do not rewrite history or broaden permission to recover.

A publication blocker does not authorize bypassing command-plan or remote safety. Preserve all validated local artifacts and report the exact blocker.

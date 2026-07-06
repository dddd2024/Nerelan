```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_closeout_final_check_consistency_rework_v1",
  "round_id": "round_20260706_closeout_final_check_consistency_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_prework_provenance_closeout_rework_v1",
  "follows_last_round_id": "round_20260706_prework_provenance_closeout_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_48_closeout_final_check_consistency_rework_v1",
  "primary_goal": "Repair final-check-after-close, run-closeout top-level status, report-summary synthesis, and source-scope consistency after the prework provenance rework. Do not add new feature scope.",
  "command_plan_authority_required": true,
  "accepted_requires_final_gate_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_final_check_after_close_passed": true,
  "accepted_requires_status_policy_consistency": true,
  "accepted_requires_no_unauthorized_source_changes": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [
    "reverse_agent/project_state.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_state_manifest.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state_manifest.py"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260706_closeout_final_check_consistency_rework_v1/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/jobs/*",
    "project_state/roadmap/workstreams.json",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/index.sqlite",
    "project_state/*.db"
  ],
  "forbidden_capabilities_this_round": [
    "real_cleanup_apply",
    "cleanup_apply_execute",
    "file_delete",
    "file_move",
    "archive_compaction_apply",
    "archive_apply",
    "real_tombstone_write",
    "real_deletion_manifest_write",
    "sqlite_database_creation",
    "database_migration",
    "web_runtime",
    "frontend_runtime",
    "production_http_service",
    "scheduler_or_service",
    "database_or_queue",
    "real_user_upload_ingestion",
    "real_sample_analysis_execution",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "remote_runner_dispatch",
    "workflow_dispatch_trigger",
    "github_actions_dispatch_or_polling",
    "model_api_invocation",
    "git_push_from_local_executor",
    "branch_creation_from_local_executor",
    "pull_request_creation_from_local_executor",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Closeout Final-Check Consistency Rework v1**.

This is a narrow `engineering_branch` rework round after `decision_20260706_prework_provenance_closeout_rework_v1` was audited as `REWORK_REQUIRED`.

The previous rework fixed the original stale prework-provenance problem and generated a current round manifest, but it still failed hard acceptance because final-check and run-closeout remained inconsistent. This round must finish the closeout/status-consistency repair without adding new feature work.

Accepted target:

- `project_state/gates/final_gate_result.json.gate_status` is `PASSED`.
- `project_state/gates/run_closeout_result.json.closeout_status` is `PASSED`.
- `final-check-after-close` passes or is represented without active nested failure state.
- `codex_execution_report.md`, `execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `execution_log.json`, `final_gate_result.json`, and `run_closeout_result.json` agree on the same current decision/round/report state.
- `report-summary` no longer reports a mismatch between synthesized status and report status.
- The prior unauthorized-source-scope issue around `reverse_agent/project_state.py` is resolved by either keeping the change within this decision's explicit allowed scope or reverting it safely.
- All command-plan required commands are recorded in execution-log.
- No forbidden paths or forbidden capabilities are used.
- The execution report may recommend `ACCEPTED` only if pytest, report-summary, execution-log, final-check, and run-closeout all support it.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and contains older sample-solving context; it must not control this engineering round.

Previous audited state:

- Previous decision: `decision_20260706_prework_provenance_closeout_rework_v1`.
- Previous round: `round_20260706_prework_provenance_closeout_rework_v1`.
- Previous manual audit outcome: `REWORK_REQUIRED`.
- Previous `prework_provenance_result.json` was current and `PASSED`.
- Previous `pytest_result.txt` had `status=FAILED` because final-check, report-summary, execution-log, or run-closeout command blocks failed.
- Previous `final_gate_result.json` had `gate_status=FAILED`.
- Previous `run_closeout_result.json` had `closeout_status=FAILED` even though close-round internally produced a round manifest.
- Previous `final-check-after-close` exited 1.
- Previous report status and final-gate status disagreed: report claimed `ACCEPTED_WITH_LIMITATIONS`, while final-gate/status-policy evidence still indicated `FAILED/REWORK_REQUIRED`.
- Previous audit identified `reverse_agent/project_state.py` as a source file changed outside the prior decision's allowed source list. This round explicitly allows that file only for status/pytest-result semantics repair.

Existing capabilities that must be reused, not duplicated:

- `project_gate` hard gates;
- command-plan authority;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and close-round;
- round manifest archive;
- prework-provenance gate;
- startup snapshot and round baseline;
- status-policy reconciliation;
- generated artifact coverage checks;
- forbidden-path checks;
- report auto-summary and neutral execution report alias;
- context packet builder;
- post-final evidence sync gate.

This round must repair the existing gate/report/closeout chain. It must not create a parallel status system, a parallel closeout system, a second execution log format, or a new provenance mechanism.

Artifact freshness policy:

- Current evidence must use this decision ID and this round ID.
- Historical sample artifacts and missing sample artifacts are nonblocking for this engineering round.
- Stale governance artifacts may be referenced only as historical/nonblocking, not as current proof.

Tool and execution policy:

- Local deterministic Python and pytest are allowed only through command-plan.
- No model API invocation is allowed.
- No GitHub Actions dispatch or polling is allowed.
- No runner dispatch is allowed.
- No Web/frontend runtime is allowed.
- No sample solving or external reverse tool invocation is allowed.
- No cleanup apply, deletion, archive compaction apply, tombstone write, database creation, or database migration is allowed.

## 3. Do Not Do

Do not add new product features.

Do not rework timestamp precision hardening unless a regression test fails. The existing `context_sync_basis` and `timestamp_precision_policy` behavior should remain intact.

Do not rework prework provenance unless required for current closeout consistency. The prior stale-prework issue was already fixed.

Do not modify `.codex-skills/*`.

Do not modify `.github/workflows/*`.

Do not modify `frontend/*`.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not modify `project_state/jobs/*` or `project_state/roadmap/workstreams.json`.

Do not read or commit full `solve_reports/*`.

Do not run sample solving, binary parsing, unpacking, candidate search, runtime validation, IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools.

Do not implement Web/API runtime, frontend runtime, scheduler, service, queue, database, GitHub App, ChatGPT Action, or remote runner.

Do not run workflow dispatch, agent dispatch, runner dispatch, or auto-iteration.

Do not perform cleanup apply, file deletion, file moving, archive compaction apply, real deletion manifest write, or real tombstone write.

Do not mark the round `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` if final-check or run-closeout still fails.

Do not suppress failing gate statuses to pass. Fix the consistency problem or stop with `REWORK_REQUIRED`.

## 4. Files To Inspect

Must inspect:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/prework_provenance_result.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_reports.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`
- `tests/test_project_state_manifest.py`

May inspect if needed:

- `reverse_agent/project_state_manifest.py`
- `project_state/context/current_context_packet.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `reverse_agent/post_final_evidence_sync.py`
- `tests/test_post_final_evidence_sync.py`
- `tests/test_project_context_builder.py`

Do not inspect by default:

- full `solve_reports/*`
- full `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/*`
- archived/cold historical artifacts unless a failing gate explicitly requires them.

## 5. Required Audit

Audit must answer all of the following:

1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `engineering_branch`?
2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?
3. Does `codex_execution_report.md` match this decision ID and round ID?
4. Does `execution_report.md` semantically match `codex_execution_report.md`?
5. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
6. Does `pytest_result.txt` status agree with command block exit codes and final-check/run-closeout evidence?
7. Does `command_plan.json` carry current decision and round IDs?
8. Does command-plan authorize every executed command?
9. Were any omitted or unauthorized commands executed?
10. Does execution-log record every command-plan required command?
11. Does execution-log provenance match live pytest_result, command_plan, and run_closeout evidence?
12. Does `prework_provenance_result.json` remain current and pass?
13. Does final-check pass before closeout?
14. Does close-round archive the current round if closeout is permitted?
15. Does final-check after closeout pass?
16. Does `run_closeout_result.json.closeout_status` pass?
17. Does final gate contain no active blocking reasons?
18. Does report-summary match the execution report status, files_changed, generated_artifacts, and required audit coverage?
19. Are all changed source/test files explicitly allowed by this decision?
20. Does the round avoid forbidden paths?
21. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?
22. Did this round preserve existing timestamp precision hardening and prework provenance behavior without reimplementing them unnecessarily?
23. Did this round reuse existing project_gate/report/final-check/closeout foundations instead of adding a parallel mechanism?
24. Does the final conclusion avoid claiming `ACCEPTED` unless all hard gates and closeout support it?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is limited to closeout/final-check/report-summary/status consistency.

1. Repair final-check-after-close semantics.
   - Identify why `run_closeout_result.json` keeps active nested failures after close-round has archived the round.
   - Ensure final-check-after-close is executed against coherent post-close artifacts.
   - Do not suppress failures; resolve the stale or contradictory evidence source.

2. Repair run-closeout top-level status.
   - `run_closeout_result.json.closeout_status` must be `PASSED` only when all required closeout checks pass.
   - If any nested failure remains, the execution report must remain `FAILED/REWORK_REQUIRED`.
   - If close-round succeeds but final-check-after-close fails, preserve the failure and do not recommend acceptance.

3. Repair report-summary/final-gate consistency.
   - Ensure report summary, synthesized summary, final gate status, and run-closeout status use one canonical current-round status model.
   - Avoid mixed states where report claims `ACCEPTED_WITH_LIMITATIONS` while final-gate says `FAILED/REWORK_REQUIRED`.

4. Repair files-changed and allowed-source consistency.
   - `reverse_agent/project_state.py` is allowed this round only for status/pytest-result semantics repair.
   - If its change is no longer needed, revert or minimize it safely within command-plan authority.
   - Ensure final gate no longer flags allowed current-round source changes as unauthorized.

5. Repair pytest_result acceptance semantics.
   - Keep the previous useful behavior: if required command blocks fail, top-level status must not be `PASSED`.
   - Ensure a fully successful run records no failing required command blocks.

6. Preserve previous fixes.
   - Keep current prework provenance behavior passing.
   - Keep digest-backed post-final timestamp precision behavior passing.
   - Do not weaken stale artifact detection to make closeout pass.

7. Add or update tests.
   - Test final-check-after-close pass path.
   - Test run-closeout top-level status is `PASSED` only when nested closeout steps pass.
   - Test report-summary and execution-report status consistency.
   - Test allowed-source handling for `reverse_agent/project_state.py` when explicitly permitted.
   - Test that failed required commands still downgrade pytest_result/report status.

Allowed source/test changes are limited to the files listed in `decision_contract`.

## 7. Tests

Run only command-plan authorized commands. If this Tests section conflicts with `project_state/gates/command_plan.json`, command-plan wins.

Expected minimum validation set:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate prework-provenance --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state_manifest.py -q
python -m pytest tests/test_post_final_evidence_sync.py tests/test_project_context_builder.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_closeout_final_check_consistency_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required result artifacts:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/prework_provenance_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/rounds/round_20260706_closeout_final_check_consistency_rework_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- all required pytest commands pass;
- prework provenance remains current;
- report-summary passes;
- execution-log passes;
- final-check passes before closeout;
- run-closeout passes;
- final-check passes after closeout;
- round manifest exists if closeout is permitted;
- no unauthorized source/test files are changed;
- no forbidden paths are modified;
- execution report recommends `ACCEPTED` only with supporting artifacts.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- repository root is not `F:\reverse-agent` or equivalent;
- `project_state/decision_packet.md` cannot be read;
- `.codex-skills/registry.json` does not mark `reverse-agent-iteration` active;
- command-plan cannot be generated or is inconsistent with this decision;
- command-plan omits required testing and no approved fallback exists;
- repairing final-check/closeout requires modifying forbidden paths;
- repairing closeout requires changing workflows, frontend, jobs, roadmap, database files, cleanup artifacts, sample artifacts, or `.codex-skills`;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, or archive apply becomes necessary;
- pytest or final-check fails and cannot be fixed within allowed files;
- the only apparent way to pass is to suppress final-check or run-closeout failures instead of resolving them.

Stop with `REWORK_REQUIRED` if:

- final-check still fails;
- final-check-after-close still fails;
- run-closeout top-level status remains failed;
- pytest_result header status contradicts failed required commands;
- execution-log provenance remains inconsistent with live evidence;
- report-summary does not match execution-report/final-gate evidence;
- source/test changes include files outside this decision's allowed list;
- current round is not archived even though closeout is permitted;
- the report claims `SUCCESS/ACCEPTED` without passing final-check and closeout.

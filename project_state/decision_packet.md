```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_prework_provenance_closeout_rework_v1",
  "round_id": "round_20260706_prework_provenance_closeout_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_post_final_timestamp_precision_hardening_v1",
  "follows_last_round_id": "round_20260706_post_final_timestamp_precision_hardening_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_47_prework_provenance_closeout_rework_v1",
  "primary_goal": "Repair the failed timestamp-precision hardening closeout by making prework provenance current-round aligned and restoring pytest/result/final-check/run-closeout status consistency. Do not re-expand the timestamp hardening feature scope.",
  "command_plan_authority_required": true,
  "accepted_requires_current_prework_provenance_artifact": true,
  "accepted_requires_final_gate_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_round_manifest_current": true,
  "accepted_requires_status_policy_consistency": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_state_manifest.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state_manifest.py"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/gates/prework_provenance_result.json",
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
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/*"
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

Implement **Prework Provenance Closeout Rework v1**.

This is a narrow `engineering_branch` rework round after the previous round `decision_20260706_post_final_timestamp_precision_hardening_v1` was audited as `REWORK_REQUIRED`.

The previous round achieved the timestamp-hardening feature objective in substance: post-final sync used digest-backed timestamp precision, produced `timestamp_precision_policy=precise_parsed_with_digest_fallback`, removed the active timestamp warning, and pytest passed. However, it failed hard acceptance because final-check and run-closeout did not pass.

Accepted target for this rework:

- `project_state/gates/prework_provenance_result.json` is regenerated or repaired for the current decision/round/report IDs.
- final-check no longer fails on stale `prework_provenance_gate_artifact`.
- `pytest_result.txt` summary status is consistent with command block failures and final-check evidence.
- `execution_log.json` provenance is consistent with live pytest, command-plan, and closeout evidence.
- `run_closeout_result.json.closeout_status` is `PASSED`.
- `project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json` exists if closeout is permitted by command-plan.
- `final_gate_result.json.gate_status` is `PASSED`.
- `codex_execution_report.md` recommends `ACCEPTED` only if pytest, report-summary, execution-log, final-check, and run-closeout all support it.

This round is not a new feature round. It must not reopen or expand Web, Runner, database, CI workflow, sample solving, IDA/Ghidra/MCP, or frontend work.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` is background only and contains older sample-solving context; it must not control this engineering round.

Previous audited state:

- Previous decision: `decision_20260706_post_final_timestamp_precision_hardening_v1`.
- Previous round: `round_20260706_post_final_timestamp_precision_hardening_v1`.
- Previous execution report status: `FAILED`.
- Previous execution report acceptance recommendation: `REWORK_REQUIRED`.
- Manual audit outcome: `REWORK_REQUIRED`.

Evidence from the failed previous round:

- `project_state/codex_execution_report.md` reported `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`.
- `project_state/pytest_result.txt` reported `status=PASSED`, but also recorded non-zero final-check and run-closeout command blocks.
- `project_state/gates/final_gate_result.json` reported `gate_status=FAILED`.
- `project_state/gates/run_closeout_result.json` reported `closeout_status=FAILED`.
- The primary closeout blocker was `prework_provenance_gate_artifact`.
- `project_state/gates/prework_provenance_result.json` carried the previous decision/round IDs, not the timestamp-hardening round IDs.
- Post-final timestamp hardening itself was not the blocker: digest-backed sync fields were present and the active timestamp warning was removed.

Existing capabilities that must not be duplicated:

- `project_gate` hard gates;
- command-plan authority;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and round archive;
- prework provenance gate foundation;
- startup snapshot and round baseline;
- context packet builder;
- post-final evidence sync gate;
- status-policy reconciliation;
- generated artifact coverage checks;
- forbidden-path checks;
- policy-lint and prompt-consistency foundations;
- CI workflow coverage/readiness foundations.

This round must reuse those existing mechanisms. It must not create a parallel closeout system, a second execution-log format, or a new provenance framework.

Artifact freshness policy:

- Current evidence must use this decision ID and this round ID.
- Historical sample artifacts and missing sample artifacts are nonblocking for this engineering round.
- Stale governance artifacts may be referenced only as historical/nonblocking, never as current proof.

Tool and execution policy:

- Local deterministic Python and pytest are allowed only through command-plan.
- No model API invocation is allowed.
- No GitHub Actions dispatch or polling is allowed.
- No runner dispatch is allowed.
- No Web/frontend runtime is allowed.
- No sample solving or external reverse tool invocation is allowed.
- No cleanup apply, deletion, archive compaction apply, tombstone write, database creation, or database migration is allowed.

## 3. Do Not Do

Do not reimplement timestamp precision hardening from scratch. The previous round's digest-backed post-final sync behavior should be preserved unless a failing test proves a regression.

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

Do not mark the round `ACCEPTED` if final-check or run-closeout fails.

Do not mark `pytest_result.txt` status as `PASSED` if command blocks required for acceptance fail.

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
- `project_state/gates/prework_provenance_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/startup_snapshot.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_reports.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

May inspect if needed:

- `reverse_agent/project_state_manifest.py`
- `tests/test_project_state_manifest.py`
- `project_state/context/current_context_packet.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `reverse_agent/post_final_evidence_sync.py`
- `tests/test_post_final_evidence_sync.py`

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
4. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
5. Does `pytest_result.txt` status agree with command block exit codes and final-check/run-closeout evidence?
6. Does `command_plan.json` carry current decision and round IDs?
7. Does command-plan authorize every executed command?
8. Were any omitted or unauthorized commands executed?
9. Does `prework_provenance_result.json` carry current decision, round, and report IDs?
10. Is prework provenance generated after or consistent with the current startup snapshot/baseline evidence?
11. Does final-check no longer fail on stale or invalid `prework_provenance_gate_artifact`?
12. Does execution-log provenance match live pytest_result, command_plan, and run_closeout evidence?
13. Does `run_closeout_result.json.closeout_status` pass if command-plan permits closeout?
14. Does the current round manifest exist and match the current report if closeout is permitted?
15. Does report-summary match the execution report?
16. Did the implementation avoid forbidden paths?
17. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?
18. Did this round preserve the existing timestamp precision hardening behavior without reimplementing it unnecessarily?
19. Did this round reuse existing project_gate/report/final-check/closeout foundations instead of adding a parallel mechanism?
20. Does final-check pass?
21. Does the final conclusion avoid claiming `ACCEPTED` unless all hard gates and closeout support it?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is limited to closeout/provenance/status consistency.

1. Repair current-round prework provenance.
   - Ensure `prework_provenance_result.json` can be regenerated for the current decision, round, and report IDs.
   - Ensure it references current startup snapshot/baseline evidence rather than a previous round.
   - If the gate already exists, strengthen it; do not introduce a parallel provenance artifact.

2. Repair final-check integration.
   - final-check must treat stale prework provenance as a blocker.
   - final-check must pass when current prework provenance is present and valid.
   - Avoid hardcoding a specific historical round or artifact SHA.

3. Repair execution-log provenance consistency.
   - Ensure execution-log provenance matches live pytest_result, command_plan, and closeout evidence.
   - If hybrid provenance is used, record the evidence sources and digests consistently.
   - Do not silently ignore failed required commands.

4. Repair pytest_result status semantics.
   - Header status must not claim `PASSED` if required acceptance commands fail.
   - If pytest commands pass but final-check or run-closeout fails, distinguish test success from round acceptance failure.
   - Preserve existing parsers and backward compatibility.

5. Repair run-closeout path.
   - If command-plan permits closeout, closeout must run only after final-check can pass.
   - closeout must archive the current round and write a current round manifest.
   - If closeout cannot pass, the execution report must remain `FAILED/REWORK_REQUIRED`.

6. Add or update tests.
   - Test stale prework provenance blocks final-check.
   - Test current prework provenance allows final-check to pass.
   - Test run-closeout fails before final-check and passes after valid provenance.
   - Test pytest_result status does not contradict failed required commands.
   - Test execution-log provenance detects stale/mismatched live evidence.

7. Preserve prior timestamp-hardening behavior.
   - Keep digest-backed timestamp precision fields working.
   - Do not remove `context_sync_basis` or `timestamp_precision_policy` support.
   - Only touch post-final sync code if required to keep existing tests green; otherwise leave it unchanged.

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_prework_provenance_closeout_rework_v1
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
- `project_state/rounds/round_20260706_prework_provenance_closeout_rework_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- all required pytest commands pass;
- prework provenance is current;
- final-check passes;
- run-closeout passes if command-plan permits closeout;
- round manifest exists if closeout is permitted;
- report-summary and execution-log match the execution report;
- no forbidden paths are modified;
- execution report recommends `ACCEPTED` only with supporting artifacts.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- repository root is not `F:\reverse-agent` or equivalent;
- `project_state/decision_packet.md` cannot be read;
- `.codex-skills/registry.json` does not mark `reverse-agent-iteration` active;
- command-plan cannot be generated or is inconsistent with this decision;
- command-plan omits required testing and no approved fallback exists;
- repairing closeout requires modifying forbidden paths;
- repairing closeout requires changing workflows, frontend, jobs, roadmap, database files, cleanup artifacts, sample artifacts, or `.codex-skills`;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, or archive apply becomes necessary;
- pytest or final-check fails and cannot be fixed within allowed files;
- the only apparent way to pass is to suppress `prework_provenance_gate_artifact` without generating current provenance.

Stop with `REWORK_REQUIRED` if:

- prework provenance remains stale after implementation;
- final-check still fails;
- run-closeout still fails when command-plan expects success;
- pytest_result header status contradicts failed required commands;
- execution-log provenance remains inconsistent with live evidence;
- current round is not archived even though closeout is permitted;
- report-summary or execution-log does not match pytest/final-check evidence;
- the report claims `SUCCESS/ACCEPTED` without passing final-check and closeout.

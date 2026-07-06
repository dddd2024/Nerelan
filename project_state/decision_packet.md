```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_required_audit_status_truth_rework_v1",
  "round_id": "round_20260706_required_audit_status_truth_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_closeout_final_check_consistency_rework_v1",
  "follows_last_round_id": "round_20260706_closeout_final_check_consistency_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_49_required_audit_status_truth_rework_v1",
  "primary_goal": "Repair Required Audit coverage and status truthfulness so reports cannot claim accepted states while final-check or run-closeout evidence is failed.",
  "command_plan_authority_required": true,
  "accepted_requires_required_audit_coverage_passed": true,
  "accepted_requires_truthful_failed_status_when_gates_fail": true,
  "accepted_requires_pytest_result_status_consistent_with_required_command_exit_codes": true,
  "accepted_requires_report_summary_consistency": true,
  "accepted_requires_final_gate_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_round_manifest_current_if_closeout_allowed": true,
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
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/rounds/round_20260706_required_audit_status_truth_rework_v1/*"
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

Implement **Required Audit Status Truth Rework v1**.

This is a narrow `engineering_branch` rework round after `decision_20260706_closeout_final_check_consistency_rework_v1` was audited as `REWORK_REQUIRED`.

The previous round improved parts of closeout consistency, but it still failed hard acceptance because the execution report claimed `ACCEPTED_WITH_LIMITATIONS` while final-check and run-closeout evidence remained failed. The immediate defect is no longer broad closeout design; it is truthfulness and alignment of reports, Required Audit answers, pytest-result status semantics, report-summary synthesis, and final gate status.

Accepted target:

- Required Audit coverage passes with substantive, question-aligned answers for every audit item.
- If final-check or run-closeout fails, both `codex_execution_report.md` and `execution_report.md` must state `FAILED / REWORK_REQUIRED`, not `ACCEPTED_WITH_LIMITATIONS`.
- If any required command exits outside command-plan expected exit codes, `pytest_result.txt` summary must not be `PASSED`.
- `report_summary_synthesis.json` must match the execution report status, recommendation, tests, and generated artifacts.
- `final_gate_result.json.gate_status` must be `PASSED` before any accepted recommendation is used.
- `run_closeout_result.json.closeout_status` must be `PASSED` if command-plan permits closeout.
- Current round manifest must exist and match current report if closeout is permitted.
- No forbidden paths or forbidden capabilities are used.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` is background only and must not control this engineering round.

Previous audited state:

- Previous decision: `decision_20260706_closeout_final_check_consistency_rework_v1`.
- Previous round: `round_20260706_closeout_final_check_consistency_rework_v1`.
- Previous manual audit outcome: `REWORK_REQUIRED`.
- `prework_provenance_result.json` was current and `PASSED`.
- Unit tests passed: `1124 passed` and `16 passed`.
- `command_plan.json` was present, current, and had no omitted commands.
- `final_gate_result.json.gate_status` was `FAILED`.
- `run_closeout_result.json.closeout_status` was `FAILED`.
- `close-round` failed because `final_check_before_archive` failed on `required_audit_coverage`.
- `pytest_result.txt` summary claimed `PASSED` while body recorded final-check and run-closeout failures.
- `report_summary_fields_match_synthesis` failed because synthesized status expected `FAILED / REWORK_REQUIRED`, but the report claimed `ACCEPTED_WITH_LIMITATIONS`.
- `status_policy_valid` failed because status evidence was contradictory.
- `required_audit_coverage` failed because Required Audit answers did not align with audit questions.

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

This round must repair the existing report/status/audit truth chain. It must not add a parallel report format, a new closeout system, a new execution log format, or a new provenance framework.

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

Do not change workflow files, frontend files, jobs, roadmap, sample artifacts, database files, cleanup artifacts, or `.codex-skills/*`.

Do not rework timestamp precision hardening unless a regression test fails. Existing `context_sync_basis` and `timestamp_precision_policy` behavior must remain intact.

Do not rework prework provenance unless required for current report/status consistency. The prior stale-prework issue was already fixed.

Do not suppress final-check, Required Audit, report-summary, status-policy, or closeout failures merely to pass. The report must truthfully reflect failed evidence.

Do not mark the round `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` if final-check or run-closeout fails.

Do not let `pytest_result.txt` claim `PASSED` when required acceptance commands fail.

Do not read full `solve_reports/*`, run sample solving, run IDA/Ghidra/OllyDbg/MCP, invoke external reverse tools, start Web/frontend runtime, trigger runner/workflow dispatch, call model APIs, create databases, or perform cleanup apply/deletion/archive apply.

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

Audit must answer all of the following with substantive answers:

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
13. Does report-summary match the execution report status, files_changed, tests_ran, generated_artifacts, and required audit coverage?
14. Does Required Audit coverage pass without placeholder or question-misaligned answers?
15. Does status-policy reject accepted claims when final-check or run-closeout evidence is failed?
16. Does final-check pass before closeout?
17. Does close-round archive the current round if closeout is permitted?
18. Does final-check after closeout pass or is there no active post-close nested failure?
19. Does `run_closeout_result.json.closeout_status` pass if command-plan permits closeout?
20. Does the current round manifest exist and match the current report if closeout is permitted?
21. Does final gate contain no active blocking reasons?
22. Are all changed source/test files explicitly allowed by this decision?
23. Does the round avoid forbidden paths?
24. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?
25. Did this round preserve existing timestamp precision hardening and prework provenance behavior without reimplementing them unnecessarily?
26. Did this round reuse existing project_gate/report/final-check/closeout foundations instead of adding a parallel mechanism?
27. Does the final conclusion avoid claiming `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` unless all hard gates and closeout support it?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is limited to Required Audit coverage, truthful report status, pytest-result status semantics, report-summary consistency, final-check, and run-closeout status consistency.

1. Repair Required Audit answer alignment.
   - Ensure generated reports answer every Required Audit item directly and substantively.
   - Avoid placeholder answers such as only naming the conclusion token.
   - Ensure the final audit-conclusion options are handled as conclusion choices, not treated as malformed audit questions.

2. Repair report status truthfulness.
   - If final-check or run-closeout fails, the report must be `FAILED / REWORK_REQUIRED`.
   - `ACCEPTED_WITH_LIMITATIONS` may be used only for nonblocking limitations after hard gates pass.
   - Do not claim core success while hard gate evidence says failed.

3. Repair pytest_result status semantics.
   - If any required command exits outside command-plan expected exit codes, top-level `pytest_result_summary.status` must not be `PASSED`.
   - Distinguish unit-test success from round acceptance success.
   - Preserve backwards-compatible parsing of existing command blocks.

4. Repair report-summary and auto-summary consistency.
   - `report_summary_synthesis.json`, `codex_report_auto_summary.json`, and `execution_report_auto_summary.json` must agree with the live reports.
   - The status and acceptance recommendation must derive from current evidence, not optimistic prose.

5. Repair closeout path only as needed.
   - Run-closeout should fail truthfully if Required Audit or final-check fails.
   - Run-closeout should pass only after final-check and close-round conditions are satisfied.
   - Do not weaken stale artifact or nested-failure detection.

6. Preserve previous fixes.
   - Keep prework provenance current and passing.
   - Keep digest-backed post-final timestamp precision behavior intact.
   - Keep allowed-source handling for explicitly permitted source files.

7. Add or update tests.
   - Test Required Audit coverage for substantive aligned answers.
   - Test that reports with failed final-check/run-closeout cannot claim accepted status.
   - Test pytest_result summary downgrades when a required command exits outside expected codes.
   - Test report-summary detects and rejects report/final-gate status mismatches.
   - Test final successful closeout path if the implementation supports it within scope.

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_required_audit_status_truth_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required result artifacts:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/prework_provenance_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/rounds/round_20260706_required_audit_status_truth_rework_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- all required pytest commands pass;
- Required Audit coverage passes;
- report-summary passes;
- execution-log passes;
- final-check passes before closeout;
- run-closeout passes if command-plan permits closeout;
- final-check passes after closeout or no active post-close nested failure remains;
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
- repairing report/status/audit consistency requires modifying forbidden paths;
- repairing the issue requires changing workflows, frontend, jobs, roadmap, database files, cleanup artifacts, sample artifacts, or `.codex-skills`;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, or archive apply becomes necessary;
- pytest or final-check fails and cannot be fixed within allowed files;
- the only apparent way to pass is to suppress final-check, Required Audit, report-summary, or run-closeout failures instead of resolving the evidence mismatch.

Stop with `REWORK_REQUIRED` if:

- Required Audit coverage still fails;
- report status still claims accepted while final-check or run-closeout evidence is failed;
- pytest_result header status contradicts failed required commands;
- report-summary does not match live reports and final-gate evidence;
- final-check still fails;
- run-closeout top-level status remains failed when acceptance is claimed;
- execution-log provenance remains inconsistent with live evidence;
- source/test changes include files outside this decision's allowed list;
- current round is not archived even though closeout is permitted and acceptance is claimed.

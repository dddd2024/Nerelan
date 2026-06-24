```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260624_closeout_final_state_sync_rework_v1",
  "round_id": "round_20260624_closeout_final_state_sync_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260624_closeout_transient_warning_normalization_v1",
  "previous_round_id": "round_20260624_closeout_transient_warning_normalization_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair final-state synchronization after closeout transient warning normalization: live report, pytest_result, execution_log, report-summary, final-check, run-closeout, and round archive must all agree before SUCCESS/ACCEPTED is allowed.",
  "command_plan_authority_required": true,
  "accepted_requires_report_status_success": true,
  "accepted_requires_report_acceptance_accepted": true,
  "accepted_requires_pytest_result_passed": true,
  "accepted_requires_execution_log_passed": true,
  "accepted_requires_report_summary_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_round_manifest_present": true,
  "accepted_requires_archive_status_archived": true,
  "accepted_requires_archived_report_matches_live_report": true,
  "accepted_requires_archived_pytest_result_matches_live_pytest_result": true,
  "accepted_requires_report_summary_fields_match_synthesis_passed": true,
  "accepted_requires_generated_artifacts_cover_round_archive": true,
  "accepted_requires_run_closeout_executed_steps_nonempty": true,
  "accepted_requires_no_active_closeout_warnings": true,
  "accepted_requires_required_audit_complete": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_state_hygiene_inventory_scope_complete": true,
  "accepted_requires_no_rename": true,
  "accepted_requires_no_delete": true,
  "accepted_requires_no_phase2_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/naming_migration_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/state_hygiene_inventory.json",
    "project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md",
    "project_state/execution_report.md",
    "project_state/gates/execution_report_auto_summary.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Closeout Final-State Sync Rework v1.

The previous round attempted to normalize closeout transient warnings. It filled the report and generated some apparently successful artifacts, but audit found that the live final state was not synchronized:

- `codex_execution_report.md` claimed `SUCCESS / ACCEPTED`.
- `pytest_result.txt` claimed `PASSED` and recorded `run-closeout: PASSED`.
- But live `project_state/gates/final_gate_result.json` had `gate_status: FAILED`.
- Live `project_state/gates/report_summary_synthesis.json` had `synthesis_status: FAILED` and expected `FAILED / REWORK_REQUIRED` while the report claimed `SUCCESS / ACCEPTED`.
- Live final-check reported a missing round manifest, archived report mismatch, archived pytest mismatch, generated artifacts missing the round archive manifest, and a blocking `report_summary_fields_match_synthesis` reason.
- `project_state/gates/run_closeout_result.json` was a minimal closeout stub with `executed_steps: []`, so it was not sufficient proof of a real closeout run.

This round must repair only that final-state synchronization problem. A report may be `SUCCESS / ACCEPTED` only when the live final gate artifacts support it mechanically. The final accepted state must have:

1. `codex_execution_report.md` top summary `SUCCESS / ACCEPTED`.
2. `pytest_result.txt` summary `PASSED`.
3. `execution_log.json.gate_status: PASSED`.
4. `report_summary_synthesis.json.synthesis_status: PASSED` with no diffs, errors, or warnings.
5. `final_gate_result.json.gate_status: PASSED` with no warnings or blocking reasons.
6. `run_closeout_result.json.closeout_status: PASSED` with non-empty real `executed_steps` evidence.
7. current round manifest present under `project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/round_manifest.json`.
8. archived report and archived pytest result matching live files.
9. generated artifacts covering the current round archive files.
10. no active closeout warnings.

This is still Phase 1.5 engineering hardening. Do not perform naming migration, file deletion, neutral report path creation, Phase 2 CI/Web/AgentRunner/database work, or sample solving.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains background-only `samplereverse` sample state and is not authoritative. The current task is controlled by this `decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260624_closeout_transient_warning_normalization_v1`.

Accepted prior-round facts:

- The decision was valid and used active `reverse-agent-iteration@v2`.
- Required Audit answers were filled and not placeholder-like.
- Core tests passed in `pytest_result.txt`: `tests/test_project_gate.py` and `tests/test_project_gate.py tests/test_project_state.py`.
- `execution-log`, `report-auto-summary`, and the recorded `run-closeout` command exited successfully in the command transcript.
- `run_closeout_result.json` represented the intended closeout warning normalization shape: `warnings: []`, `resolved_pre_archive_warnings: []`, `pre_archive_diagnostics: []`, and `final_check_after_archive` with `status: PASSED`, `gate_status: PASSED`.

Blocking prior-round facts:

- Live `final_gate_result.json` had `gate_status: FAILED`.
- Live `report_summary_synthesis.json` had `synthesis_status: FAILED`.
- Live report summary said `SUCCESS / ACCEPTED`, but report-summary expected `FAILED / REWORK_REQUIRED`.
- final-check reported the current round manifest missing.
- final-check reported archived report and archived pytest result differed from live files.
- final-check reported generated artifacts omitted the current round archive manifest.
- final-check blocking reason included `report_summary_fields_match_synthesis: codex_report_summary differs from synthesized summary`.
- `run_closeout_result.json.executed_steps` was empty, which is not sufficient proof of the required closeout command sequence.

Artifact freshness:

- All proof for this rework must be regenerated under `decision_20260624_closeout_final_state_sync_rework_v1` and `round_20260624_closeout_final_state_sync_rework_v1`.
- Prior-round artifacts are diagnostic context only.
- Historical/backlog `samplereverse` artifacts remain external notices only and must not be claimed as current evidence.

Existing capabilities to preserve:

- command-plan authority and omitted-command enforcement.
- required-command recording enforcement.
- `execution_log_required_commands_recorded`.
- report-auto-summary no synthetic missing command insertion.
- report-summary synthesis and final-check strictness.
- Required Audit placeholder blocking.
- Phase 1 completion evidence-path checks.
- `state_hygiene_inventory_scope_complete` archive-scope check.
- closeout transient warning normalization without hiding real failures.
- naming-hygiene inventory-only behavior with no rename/delete/neutral live path creation.

Gate/command-plan strategy:

- Use only valid profiles: `fast`, `standard`, `full`.
- Because this round repairs final accepted-state synchronization and closeout evidence, command-plan should select or require `full` validation.
- Tests are subordinate to command-plan. If this Tests section conflicts with command-plan, command-plan is authoritative.
- Closeout may run only if command-plan authorizes it and the selected profile allows closeout.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not rename any live artifact in this round.

Do not create `project_state/execution_report.md` in this round.

Do not create `project_state/gates/execution_report_auto_summary.json` in this round.

Do not delete files in this round.

Do not remove legacy Codex-named files in this round.

Do not modify `project_state/artifact_index.json` in this round.

Do not write dynamic findings into `.codex-skills/`.

Do not write `SUCCESS / ACCEPTED` into `codex_execution_report.md` unless live `report_summary_synthesis.json`, `final_gate_result.json`, `execution_log.json`, `pytest_result.txt`, and `run_closeout_result.json` all support that status.

Do not accept `run_closeout_result.json` with `executed_steps: []` as sufficient proof of closeout.

Do not accept final output if the current round manifest is missing.

Do not accept final output if archived report or archived pytest result differs from live files.

Do not accept final output if generated artifacts omit current round archive files.

Do not accept final output if `report_summary_fields_match_synthesis` is WARN/FAILED or is listed as a blocking reason.

Do not hide real closeout/final-check/report-summary failures by relabeling them as transient.

Do not use `COMPLETED_WITH_LIMITATIONS` as a report status. Supported report status values remain `SUCCESS`, `PARTIAL`, `FAILED`, and `BLOCKED`.

Do not broaden this round into naming migration, compatibility dual-write, Phase 2 GitHub CI, `ci.yml`, `state-gate.yml`, PR automation, branch protection, Web UI, AgentRunner, Codex adapter, Trae adapter, Job Manager, database, queue, scheduler, daemon, API Planner, API Auditor, self-hosted runner, or background worker work.

Do not continue `samplereverse` solving or any sample-solving task.

Do not read the full `solve_reports/` directory or full `PROJECT_PROGRESS_LOG.txt`.

Do not treat old sample artifacts or prior-round gate artifacts as current evidence.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`
- `project_state/execution_report.md`
- `project_state/gates/execution_report_auto_summary.json`

Do not introduce a `medium` profile.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only relevant implementation and gate evidence files:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/gate_profile_plan.json`
9. `project_state/gates/naming_migration_plan.json`
10. `project_state/gates/state_hygiene_inventory.json`
11. `project_state/gates/preflight_result.json`
12. `project_state/gates/policy_lint_result.json`
13. `project_state/gates/policy_impact_audit.json`
14. `project_state/gates/run_round_result.json`
15. `project_state/gates/run_closeout_result.json`
16. `project_state/gates/run_closeout_execution_log.json`
17. `project_state/gates/round_delta_summary.json`
18. `project_state/gates/round_close_snapshot.json` if present
19. `project_state/rounds/round_20260624_closeout_transient_warning_normalization_v1/round_manifest.json` only as bounded prior-round diagnostic evidence, if present
20. `project_state/rounds/round_20260624_closeout_transient_warning_normalization_v1/codex_execution_report.md` only as bounded prior-round diagnostic evidence, if present
21. `project_state/rounds/round_20260624_closeout_transient_warning_normalization_v1/pytest_result.txt` only as bounded prior-round diagnostic evidence, if present

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What final-state drift caused the previous round to fail despite a `SUCCESS / ACCEPTED` report, and which live artifacts proved the drift?
2. How does the implementation prevent `codex_execution_report.md` from claiming `SUCCESS / ACCEPTED` when live `report_summary_synthesis.json` or `final_gate_result.json` is FAILED?
3. How does `run_closeout_result.json` now prove a real closeout sequence with non-empty `executed_steps`, instead of a minimal stub?
4. How does final-check prove the current round manifest exists, archive status is archived, and archived report/pytest files match live files?
5. How does report-summary prove `report_summary_fields_match_synthesis` is PASS and that status/acceptance fields match the live report?
6. Which regression tests cover final-state drift, missing round manifest, archive mismatch, generated-artifacts archive coverage, empty closeout executed steps, and false SUCCESS reports?
7. How were `execution_log_required_commands_recorded: PASS`, `state_hygiene_inventory_scope_complete: PASS`, Required Audit completeness, and closeout transient warning normalization preserved?
8. How does this round preserve no sample-solving behavior, no prompt/skill mutation, no heavy artifact scan, no rename/delete/neutral live path creation, no evidence weakening, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Primary scope: repair live final-state synchronization and prevent false accepted reports when final gate artifacts disagree.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/naming_migration_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/rounds/round_20260624_closeout_final_state_sync_rework_v1/*`

Required behavior:

1. Establish a current-round baseline before modifications.
2. Preserve closeout transient warning normalization, but do not allow it to mask final-state failures.
3. Ensure report-summary, final-check, report-auto-summary, execution-log, pytest_result, run-closeout, and round manifest are regenerated in an order that produces a coherent final live state.
4. Ensure `run_closeout_result.json.executed_steps` is non-empty and contains the real closeout command sequence.
5. Ensure final-check fails if `run_closeout_result.json.executed_steps` is empty in an accepted report.
6. Ensure final-check fails if round manifest is missing after closeout.
7. Ensure final-check fails if archived report or archived pytest result differs from live files after closeout.
8. Ensure final-check fails if generated_artifacts omit current round archive files.
9. Ensure report-summary fails if synthesized status/acceptance diverges from the live report summary, and prevent the live report from claiming SUCCESS while synthesis is FAILED.
10. Ensure `report_summary_fields_match_synthesis` is PASS in final accepted output.
11. Ensure `codex_execution_report.md` is written as `SUCCESS / ACCEPTED` only after the live final-check and report-summary are both PASSED.
12. Preserve `execution_log_required_commands_recorded: PASS` and `state_hygiene_inventory_scope_complete: PASS`.
13. Preserve naming-hygiene inventory-only behavior: no rename, no delete, no neutral live report path creation.
14. Add focused tests for false SUCCESS blocking, empty closeout executed steps, missing archive manifest, archive mismatch, generated-artifacts archive coverage, report-summary/final-check divergence, and success path.
15. Regenerate current-round `pytest_result.txt`, `execution_log.json`, `codex_report_auto_summary.json`, `report_summary_synthesis.json`, `final_gate_result.json`, `run_closeout_result.json`, `run_closeout_execution_log.json`, `state_hygiene_inventory.json`, and `codex_execution_report.md`.
16. Run closeout if and only if command-plan authorizes it.
17. Final accepted report must be `SUCCESS / ACCEPTED` with final-check `PASSED`, report-summary `PASSED`, execution-log `PASSED`, report-auto-summary `PASSED`, run-closeout `PASSED`, non-empty closeout executed steps, current round manifest present, archive status archived, complete Required Audit, no active closeout warnings, and no blocking reasons.

Do not implement actual naming migration, rename, deletion, compatibility dual-write, schema migration, Phase 2, Web, CI, database, or multi-executor adapter in this round.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Generate and obey command-plan:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate naming-hygiene --state-dir project_state
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_closeout_final_state_sync_rework_v1 --dry-run --json
python -m reverse_agent.project_gate run-round --state-dir project_state --round-id round_20260624_closeout_final_state_sync_rework_v1 --execute
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260624_closeout_final_state_sync_rework_v1
python -m reverse_agent.project_gate naming-hygiene --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`. Do not include nested closeout-internal command blocks in the top-level command stream. Record nested closeout command evidence in `project_state/gates/run_closeout_execution_log.json` or the existing scoped closeout evidence artifact.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- implementation requires modifying files outside allowed source scope;
- state updates require forbidden paths;
- implementation requires renaming live report paths;
- implementation requires deleting files;
- implementation requires creating new neutral live report paths;
- implementation requires modifying prompt/skill files;
- implementation requires weakening command-plan authority, required-command recording, report-summary strictness, final-check strictness, closeout strictness, or Required Audit strictness;
- implementation requires accepting a false SUCCESS report while report-summary/final-check is FAILED;
- implementation requires accepting `run_closeout_result.json.executed_steps=[]` as closeout proof;
- implementation requires accepting `COMPLETED_WITH_LIMITATIONS` as a report status;
- implementation requires scanning full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`;
- Required Audit remains incomplete or placeholder-like.

Stop with `REWORK_REQUIRED` if tests fail, command-plan authority regresses, required command recording regresses, `codex_execution_report.md` is not `SUCCESS / ACCEPTED`, `pytest_result_summary.status` is not `PASSED`, Required Audit contains PENDING/placeholders, `execution_log.json.gate_status` is not `PASSED`, report-summary is not `PASSED`, final-check is not `PASSED`, run-closeout is not `PASSED`, `run_closeout_result.json.executed_steps` is empty, current round manifest is missing, archive status is not archived, archived report/pytest mismatch live files, generated artifacts omit current round archive files, `report_summary_fields_match_synthesis` is not PASS, policy-lint fails, policy-impact fails, `state_hygiene_inventory_scope_complete` is missing or not PASS, `execution_log_required_commands_recorded` is missing or not PASS, any file is renamed, any file is deleted, any neutral live report path is created, any forbidden path is mutated, final-check has warnings or blocking reasons, or the final report remains non-success for reasons other than a clearly documented real blocker.

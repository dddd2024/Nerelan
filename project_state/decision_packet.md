```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_source_fix_closeout_record_rework_v1",
  "round_id": "round_20260618_source_fix_closeout_record_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the source-fix closeout record mismatch left by the previous stale-snapshot synthesis source-fix round.

The previous round appears to have completed the intended source fix: `report-summary` no longer requires stale `round_close_snapshot.json`, current regression tests passed, and generated-artifact synthesis now uses current command/artifact identity. However, the live report overstates completion: it claims `SUCCESS/ACCEPTED` and lists archive files, while the current final gate still reports archive/manifest warnings and `archive_status=not_archived` / `report_status=PARTIAL` / `report_acceptance_recommendation=NEEDS_REVIEW`.

This round must reconcile report, pytest result, final-check, and close-round evidence. Prefer artifact/report repair and rerun of closeout commands. Do not change the stale-snapshot synthesis source code again unless inspection proves the closeout tool itself has a bounded bug.

Target behavior:

- Current report summary and final gate agree.
- If close-round succeeds, current round archive files exist and are recorded consistently.
- If close-round does not succeed, report must use `PARTIAL` or `FAILED` with `REWORK_REQUIRED`, not `SUCCESS/ACCEPTED`.
- Live `round_close_snapshot.json`, if claimed as current, must carry the current decision and round IDs.
- No old snapshot or old archive file may be reused as current closeout evidence.
- The already implemented stale-snapshot synthesis behavior must remain intact.
- No reverse-solving or mature reverse-engineering tool work is allowed.

## 2. Current Evidence

Current execution authority is this live `project_state/decision_packet.md`. `task_packet.json` remains advisory only and must not override this decision.

State summary:

- `task_packet.json` still says `execution_scope=decision_packet_controls_current_round`; therefore this decision controls Codex execution.
- `current_state.json` still describes old `samplereverse` reverse-solving state with missing candidate/runtime evidence. That state is not current evidence for this engineering closeout-record task.
- `artifact_index.json` still shows most historical `samplereverse` artifacts as missing. Those reverse artifacts must not be used as current evidence.
- `negative_results.json` still blocks old reverse-solving directions, including blind old solver search, budget-only expansion, compare-semantics-disagree candidates as primary frontier, committing full solve report outputs, and repeated failed `samplereverse` branches. This round must not touch those directions.
- `.codex-skills/registry.json` contains active `reverse-agent-iteration` version 2, so `reverse-agent-iteration@v2` is valid.

Relevant prior evidence:

- `decision_20260618_fast_report_summary_stale_snapshot_source_fix_v1` implemented the stale snapshot synthesis source fix in `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- Its report says focused regression subset passed and the full gate/state suite passed.
- Its `report-summary` artifact passed and no longer required stale `round_close_snapshot.json` in the expected generated artifacts.
- Its current `final_gate_result.json` still reports archive warnings and status summary values inconsistent with `SUCCESS/ACCEPTED`.
- Its live `round_close_snapshot.json` still carries an older `decision_20260618_fast_non_closeout_prose_precision_rework_v1` decision/round ID, so it is not current closeout evidence for the last source-fix round.
- The last report listed round archive files as generated artifacts, but the current GitHub state did not prove those archive files existed as live repository contents during audit.

Existing implementation status:

- The source fix in `build_report_summary_synthesis` should not be reopened unless fresh evidence shows a bounded implementation defect.
- The present problem is evidence/record consistency around final-check and close-round, not reverse-solving.

## 3. Do Not Do

Do not run reverse-solving.

Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger hooks, emulators, runtime probes, sample runners, GUI/frontend workflows, or raw sample analysis.

Do not modify solver code, harness code, strategy code, transform code, debugger/tool-runner integrations, sample runner code, GUI/frontend code, raw sample files, skill files, or solve report outputs.

Do not hide archive inconsistency by only editing report prose.

Do not claim `SUCCESS/ACCEPTED` unless final-check and closeout evidence support it.

Do not reuse old `round_close_snapshot.json` as current closeout evidence.

Do not claim archive files that do not exist.

Do not weaken full-profile close-round or archive requirements.

Do not remove generated-artifact checking from report-summary or final-check.

Do not update this decision file during Codex execution. If this decision file is dirty at startup, stop.

## 4. Files To Inspect

Read default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Inspect evidence and closeout artifacts:

- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- current round archive files for this round after close-round, if generated

Inspect source/tests only if needed to determine whether close-round itself has a bounded implementation bug:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not inspect unrelated reverse-solving or tool-integration modules unless a gate command explicitly reports a forbidden-path blocker that names them.

## 5. Required Audit

Before modifying files, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded after path confirmation and before any file modification.
3. This decision file is not dirty at startup.
4. No source or test files are dirty at startup.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. `task_packet.json` is non-authoritative and this decision controls execution.
7. This is an engineering closeout-record rework, not reverse-solving.

During execution, verify:

1. Whether the previous source fix already satisfies stale-snapshot synthesis behavior.
2. Whether live `round_close_snapshot.json` carries current or stale IDs.
3. Whether current round archive files exist after close-round.
4. Whether final-check status summary agrees with report summary.
5. Whether close-round has a complete command block and exit code in `pytest_result.txt`.
6. Whether `report_summary_synthesis.json` and `final_gate_result.json` agree with `codex_report_summary`.
7. Whether the final report should be `SUCCESS/ACCEPTED` or must be downgraded to `PARTIAL`/`REWORK_REQUIRED`.

## 6. Implementation Scope

Prefer updating only project-state/report artifacts:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` only if close-round produces it with current IDs
- `project_state/rounds/round_20260618_source_fix_closeout_record_rework_v1/codex_execution_report.md` if close-round succeeds
- `project_state/rounds/round_20260618_source_fix_closeout_record_rework_v1/decision_packet.md` if close-round succeeds
- `project_state/rounds/round_20260618_source_fix_closeout_record_rework_v1/pytest_result.txt` if close-round succeeds
- `project_state/rounds/round_20260618_source_fix_closeout_record_rework_v1/round_manifest.json` if close-round succeeds

Only if close-round/final-check implementation is demonstrably defective may Codex modify:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

If source/test changes are made, rerun the full gate/state suite and treat this as a full validation round.

Required report shape:

- Use `SUCCESS/ACCEPTED` only if final-check has no FAIL checks and closeout/archive evidence is consistent.
- Use `PARTIAL` or `FAILED` with `REWORK_REQUIRED` if close-round does not generate current archive evidence.
- `files_changed` and `generated_artifacts` must not list missing archive files.
- If `round_close_snapshot.json` is listed, it must carry current decision/round IDs.
- Report body must explicitly state whether close-round was run, its exit status, and whether archive files were generated.

## 7. Tests

Run and record the following in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If source/test files are modified, also run and record:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check has no FAIL checks and closeout is allowed, run and record:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_source_fix_closeout_record_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The result record must include:

- `decision_id=decision_20260618_source_fix_closeout_record_rework_v1`
- `round_id=round_20260618_source_fix_closeout_record_rework_v1`
- final `report_id`
- every command actually run
- exact pytest outcome if pytest is run
- close-round command block and exit code if close-round is run
- explicit statement whether archive files exist and match live report/pytest result

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- startup path is not `F:\reverse-agent`;
- this decision file is dirty at startup;
- source/test files are dirty at startup before this round's changes;
- `decision_meta` is missing or not `APPROVED`;
- `reverse-agent-iteration@v2` is not active;
- archive files cannot be generated but report would need them for `SUCCESS/ACCEPTED`;
- close-round after a no-FAIL final-check still does not produce a current round manifest;
- `round_close_snapshot.json` still carries old IDs after a claimed close-round;
- report-summary and final-check still disagree after artifact refresh;
- fixing the issue requires modifying outside the allowed source/test files;
- source/test changes are made but pytest is not run;
- final-check has FAIL after the final report is written;
- reverse-solving, solver, harness, debugger/tool-runner, sample, GUI/frontend, skill-file, or solve-report-output modification becomes necessary.

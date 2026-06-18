```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_report_summary_stale_snapshot_source_fix_v1",
  "round_id": "round_20260618_fast_report_summary_stale_snapshot_source_fix_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair `report-summary` and `final-check` synthesis for fast non-closeout artifact-only rounds so stale closeout snapshots are not required as current generated artifacts.

The previous v5 fast validation proved that parser-safe scope, preflight, fast profile classification, pytest omission, close-round omission, and startup ordering all worked. It still failed because `report-summary` synthesized `generated_artifacts` with an old `round_close_snapshot.json` even though the v5 decision correctly excluded that stale file from current evidence.

This round is a bounded source-fix round. It may modify the project gate implementation and regression tests only as needed to fix report-summary/final-check expected artifact synthesis. It must not perform reverse-solving.

Target behavior:

- For fast profile with `closeout_allowed=false` and no active close-round command, `report-summary` must not require `round_close_snapshot.json` in expected `generated_artifacts`.
- If a stale `round_close_snapshot.json` exists with an older decision or round ID, it must not be treated as current generated evidence for the fast round.
- If a stale `run_round_result.json` exists and dry-run was omitted by fast profile, it must not be treated as current generated evidence.
- For full profile source-fix rounds where close-round is run, closeout snapshot/archive expectations must remain strict.
- `report-summary` and `final-check` must agree on generated artifact expectations.
- Command ordering diagnostics should not obscure the main fix: actual startup command blocks must remain before preflight. If command-plan ordering is touched, keep it small and covered by tests.

## 2. Current Evidence

Current execution authority is this live `project_state/decision_packet.md`. `task_packet.json` remains advisory only and must not override this decision.

State summary:

- `task_packet.json` still says `execution_scope=decision_packet_controls_current_round`; therefore this decision controls Codex execution.
- `current_state.json` still describes old `samplereverse` reverse-solving state with missing candidate/runtime evidence. That state is not current evidence for this engineering source fix.
- `artifact_index.json` still shows most historical `samplereverse` artifacts as missing. Those reverse artifacts must not be used as current evidence.
- `negative_results.json` still blocks old reverse-solving directions, including blind old solver search, budget-only expansion, compare-semantics-disagree candidates as primary frontier, committing full solve report outputs, and repeated failed `samplereverse` branches. This round must not touch those directions.
- `.codex-skills/registry.json` contains active `reverse-agent-iteration` version 2, so `reverse-agent-iteration@v2` is valid.

Relevant prior evidence:

- `decision_20260618_fast_non_closeout_prose_precision_rework_v1` was audited as `ACCEPTED_WITH_LIMITATIONS` and fixed over-broad close-round prose matching.
- `decision_20260618_fast_artifact_only_validation_v3` proved core fast behavior but failed audit because stale closeout snapshot data was claimed as generated/current.
- `decision_20260618_fast_artifact_only_validation_v4_stale_gate_artifact_rework` failed preflight because path-like forbidden entries in Implementation Scope were parsed as allowed scope.
- `decision_20260618_fast_artifact_only_validation_v5_parser_safe_scope` fixed the preflight/parser-safe scope issue. Preflight passed, gate-profile was fast, closeout was disallowed, pytest and close-round were omitted, and source/test files were not modified.
- v5 failed only because `report-summary` and `final-check` still synthesized expected `generated_artifacts` containing stale `project_state/gates/round_close_snapshot.json`.

Existing capability boundary:

- This round is not reverse-solving.
- Do not run reverse-engineering tools, debugger hooks, emulators, sample runners, runtime probes, GUI/frontend workflows, or raw sample analysis.
- Do not inspect or modify mature reverse-engineering tool integrations.

Artifact freshness rule:

- Gate artifacts may be current evidence only if they carry the current decision/round/report IDs where applicable.
- Any gate artifact carrying an older decision or round ID is stale and must not be synthesized as a current generated artifact for a fast non-closeout validation.
- A stale closeout snapshot may exist on disk from a previous full closeout round. Its existence must not force fast non-closeout reports to list it.

## 3. Do Not Do

Do not modify solver code, harness code, strategy code, transform code, debugger/tool-runner integrations, sample runner code, GUI/frontend code, raw sample files, skill files, or solve report outputs.

Do not run reverse-solving.

Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger hooks, emulators, runtime probes, or sample runners.

Do not treat stale closeout snapshot data as current evidence.

Do not make fast non-closeout rounds run close-round.

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

Inspect implementation and tests:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if existing project-state report/final-check compatibility tests require a bounded update

Inspect generated evidence:

- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/round_close_snapshot.json` only to confirm stale IDs
- `project_state/gates/run_round_result.json` only to confirm whether it is current or stale

Do not inspect unrelated reverse-solving or tool-integration modules unless a gate command explicitly reports a forbidden-path blocker that names them.

## 5. Required Audit

Before modifying files, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded after path confirmation and before any file modification.
3. This decision file is not dirty at startup.
4. No source or test files are dirty at startup.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. `task_packet.json` is non-authoritative and this decision controls execution.
7. This is an engineering source-fix round, not reverse-solving.
8. Because `reverse_agent/project_gate.py` is in scope, gate-profile should classify this as full validation and closeout should be allowed after successful final-check.

After implementation, verify:

1. Fast non-closeout report-summary does not require stale `round_close_snapshot.json`.
2. Fast non-closeout final-check accepts the report-summary generated-artifact set when it excludes stale closeout snapshot data.
3. Fast non-closeout does not require stale `run_round_result.json` if dry-run was omitted by fast profile.
4. Full profile close-round/archive expectations remain strict.
5. Generated-artifact checking is still active and still catches missing current artifacts.
6. Existing fast closeout-consistency behavior remains intact.
7. Actual startup command blocks in `pytest_result.txt` remain before preflight.
8. No reverse-solving direction in `negative_results.json` is repeated.

## 6. Implementation Scope

Allowed source and test files for this source-fix round are only:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project-state and gate artifacts for this source-fix round are only:

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
- `project_state/gates/round_close_snapshot.json` if produced by close-round in this full validation round
- `project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/codex_execution_report.md` if close-round succeeds
- `project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/decision_packet.md` if close-round succeeds
- `project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/pytest_result.txt` if close-round succeeds
- `project_state/rounds/round_20260618_fast_report_summary_stale_snapshot_source_fix_v1/round_manifest.json` if close-round succeeds

Required implementation shape:

- Prefer a narrowly scoped helper or predicate used by report-summary/final-check synthesis to decide whether closeout snapshot artifacts are expected for the current round.
- The predicate must account for current profile, `closeout_allowed`, active close-round command presence, and current decision/round ID freshness.
- For fast profile with closeout disallowed and close-round omitted, do not synthesize stale closeout snapshot as expected generated artifact.
- For full profile after close-round, keep snapshot/archive expectations strict.
- Do not solve the problem by deleting generated-artifact comparison wholesale.

Required tests to add or update:

1. Fast non-closeout with a stale `round_close_snapshot.json` on disk: report-summary must not expect it in generated_artifacts.
2. Fast non-closeout with an omitted dry-run and stale `run_round_result.json` on disk: report-summary must not expect it in generated_artifacts.
3. Full profile close-round path still expects closeout snapshot/archive artifacts.
4. Generated-artifact checking still detects missing current required artifacts.
5. Existing fast-profile closeout-consistency tests still pass.
6. Optional if touched: command-plan order keeps startup/preflight semantics consistent or has explicit tests documenting diagnostic order.

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If `final-check` has no FAIL checks and the worktree state is acceptable, run:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_report_summary_stale_snapshot_source_fix_v1
```

The result record must include:

- `decision_id=decision_20260618_fast_report_summary_stale_snapshot_source_fix_v1`
- `round_id=round_20260618_fast_report_summary_stale_snapshot_source_fix_v1`
- final `report_id`
- every command actually run
- exact pytest outcome
- explicit note whether close-round was run or skipped

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- startup path is not `F:\reverse-agent`;
- this decision file is dirty at startup;
- source/test files are dirty at startup before this round's changes;
- `decision_meta` is missing or not `APPROVED`;
- `reverse-agent-iteration@v2` is not active;
- implementing the fix requires modifying outside the allowed source/test files;
- fixing the issue requires deleting generated-artifact checking entirely;
- fast non-closeout still expects stale closeout snapshot as generated/current evidence;
- fast non-closeout still expects stale dry-run artifact when dry-run was omitted;
- full profile closeout/archive requirements are weakened;
- pytest fails and cannot be explained with a bounded decision-scoped action;
- final-check still has FAIL after the report is written;
- reverse-solving, solver, harness, debugger/tool-runner, sample, GUI/frontend, skill-file, or solve-report-output modification becomes necessary.

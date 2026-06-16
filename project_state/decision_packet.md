```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_gate_baseline_lifecycle_closeout_rework_v1",
  "round_id": "round_20260616_gate_baseline_lifecycle_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out `round_20260616_cpp1_success_reanchor_closeout_rework_v1` by repairing the remaining gate baseline lifecycle and close snapshot inconsistency.

This is an `engineering_branch` gate repair round. Do not continue CPP1 solving work. Do not rerun the CPP1 local sample. Do not regenerate CPP1 evidence artifacts.

Required end state:

- live `final_gate_result.json` is not FAILED;
- `report_summary_synthesis.json` is PASSED;
- `baseline_lifecycle_guard` no longer treats explicitly authorized source/test changes as unauthorized inherited dirty files;
- `report_summary_fields_match_synthesis` passes;
- close-round exits 0;
- round archive exists for `round_20260616_gate_baseline_lifecycle_closeout_rework_v1`;
- `local_reverse_cpp1_2f6fcb63_success_target_reanchor` remains current and unchanged.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Previous round:

- `decision_20260616_cpp1_success_reanchor_closeout_rework_v1`
- `round_20260616_cpp1_success_reanchor_closeout_rework_v1`
- mainline: `engineering_branch`

Known facts from audit:

- `command-plan` now passes.
- The generic project CLI classification works.
- `pytest` passes with 570 tests.
- `close-round` reported CLOSED and created an archive.
- live `final_gate_result.json` still reports FAILED.
- blockers are `baseline_lifecycle_guard` and `report_summary_fields_match_synthesis`.
- `project_state/gates/round_close_snapshot.json` records dirty source/test files: `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- These two files were explicitly allowed by the previous decision implementation scope.
- Current CPP1 reanchor artifact is already current and must not be changed.

Historical missing artifacts remain external state notices. Missing/stale current artifacts must still block.

## 3. Do Not Do

Do not rerun the CPP1 local sample.

Do not continue reverse-solving work or produce candidate material.

Do not modify CPP1 evidence artifacts, except read-only verification.

Do not analyze `samplereverse`.

Do not modify solver logic, sample runners, IDA runner semantics, `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not manually patch gate result files to hide failures.

Do not weaken decision/report/pytest/round id matching.

Do not weaken current artifact freshness policy.

Do not remove historical missing artifact entries just to pass gates.

## 4. Files To Inspect

Read the default project_state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260616_cpp1_success_reanchor_closeout_rework_v1/round_manifest.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, read-only verification only
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. `project_gate.py` and `tests/test_project_gate.py` were authorized in the previous decision's Implementation Scope.
4. The close snapshot correctly records they were dirty at close.
5. The gate incorrectly classifies them as unauthorized inherited source/test dirty files.
6. The fix must be limited to baseline lifecycle / close snapshot authorization semantics.
7. Current CPP1 artifacts remain current and are not downgraded.
8. Historical 50 missing sample artifacts remain external state notices, not blockers.

Required result:

- `baseline_lifecycle_guard` must pass or become non-blocking only for source/test files that are authorized by decision scope and covered by report/tests.
- Unauthorized source/test dirty files must still block.
- `report_summary_fields_match_synthesis` must pass.
- Gate result files must be generated by gate commands, not manually edited.
- close-round must exit 0 before reporting SUCCESS/ACCEPTED.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- directly related tests, preferably `tests/test_project_gate.py`

Allowed state updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_gate_baseline_lifecycle_closeout_rework_v1/*`

Do not modify:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`;
- `project_state/artifact_index.json`, unless needed only to preserve existing current registration without changing meaning;
- solver/sample-runner/IDA/harness modules;
- `.codex-skills/`.

Implementation must distinguish:

- unauthorized inherited source/test dirty files;
- source/test files explicitly authorized by the current decision and listed in report/tests;
- generated state files expected during closeout.

Do not make all dirty source/test files non-blocking. The exception must be constrained by current decision scope, report coverage, and tests.

## 7. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_gate_baseline_lifecycle_closeout_rework_v1
```

Focused tests must cover:

- authorized source/test files in Implementation Scope are not reported as unauthorized inherited dirty files at close;
- unauthorized source/test dirty files still block;
- close snapshot dirty source/test files must be either authorized or blocking;
- report-summary includes all files required by synthesis, including `round_close_snapshot.json` when generated;
- current artifact freshness and id matching checks remain strict.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if live `final_gate_result.json` remains FAILED.

Stop with `REWORK_REQUIRED` if `baseline_lifecycle_guard` still fails.

Stop with `REWORK_REQUIRED` if `report_summary_fields_match_synthesis` still fails.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if the fix weakens artifact freshness, id matching, forbidden path checks, or unauthorized source/test dirty detection.

Stop with `REWORK_REQUIRED` if CPP1 evidence artifacts are modified.

Stop with `BLOCKED` if this requires broad project_state schema changes outside baseline lifecycle / close snapshot semantics.

Do not write SUCCESS or ACCEPTED if final gate or close-round fails.

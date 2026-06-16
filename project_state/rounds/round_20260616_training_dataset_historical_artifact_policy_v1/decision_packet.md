```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_training_dataset_historical_artifact_policy_v1",
  "round_id": "round_20260616_training_dataset_historical_artifact_policy_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the gate/status policy that incorrectly blocks `training_dataset` rounds when the only artifact freshness issue is historical sample artifact missing/stale state unrelated to the current training round.

The previous `training_dataset` round produced the requested resume plan and type coverage matrix, but `close-round` failed because `status_policy_valid` treated historical `samplereverse` missing artifacts as blocking under `training_dataset`.

This is an `engineering_branch` gate-policy repair round. Do not continue sample solving. Do not regenerate the training inventory. Do not rerun local samples.

Required end state:

- `training_dataset` mainline can treat historical sample artifact freshness issues as non-blocking when the current report does not claim those artifacts as current evidence;
- `status_policy_valid` passes for the previous training resume scenario when the only blocking issue is historical sample artifact freshness;
- real current-round missing/stale artifacts remain blocking;
- `engineering_branch` behavior remains unchanged;
- `reverse_solving` behavior remains strict and does not silently downgrade current evidence failures;
- `report-summary` passes;
- `final-check` passes;
- `close-round` exits 0 and archives `round_20260616_training_dataset_historical_artifact_policy_v1`.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

The previous round:

- `decision_20260616_local_reverse_training_resume_plan_v1`
- `round_20260616_local_reverse_training_resume_plan_v1`
- mainline: `training_dataset`
- audit conclusion: `REWORK_REQUIRED`

Evidence from the previous round:

- `project_state/local_reverse_training_resume_plan.json` exists and contains the expected resume plan.
- `project_state/local_reverse_type_coverage_matrix.json` exists and contains type coverage.
- `pytest` passed with 645 tests.
- `command-plan` passed.
- No sample execution was reported.
- No source/test code was modified.
- `final-check` failed because `status_policy_valid` failed.
- `close-round` failed after archive due to `final_check_after_archive: ['status_policy_valid']`.
- `report_summary_synthesis.json` expected `FAILED / REWORK_REQUIRED`, while Codex report claimed `SUCCESS / ACCEPTED`.

Known likely root cause:

- `reverse_agent/project_state.py` has `_historical_artifact_freshness_is_non_blocking()`.
- `reverse_agent/project_gate.py` has `_status_policy_failure_is_historical_artifacts_only()`.
- The current logic appears to downgrade historical missing/stale artifacts for `engineering_branch` but not for `training_dataset`.
- For training resume planning, historical `samplereverse` missing artifacts are external state notices, not current-round blockers, provided the report does not claim them as current evidence.

Existing mature tool interfaces and sample evidence mechanisms must remain untouched. This round is only about gate/status policy classification.

Existing relevant capabilities to check before implementation:

- project_state doctor/lint/report status policy code;
- project_gate final-check/close-round status policy code;
- report-summary synthesis behavior;
- artifact freshness classification;
- mainline-specific policy handling;
- tests for project_state, project_gate, and local_reverse_training_status;
- existing IDA/Ghidra/debugger/solver/harness interfaces, read-only only.

## 3. Do Not Do

Do not modify solver logic.

Do not modify sample runners.

Do not modify IDA/Ghidra/debugger/emulator/probe/harness behavior.

Do not rerun local reverse samples.

Do not generate candidates.

Do not rebuild or rescan the training inventory.

Do not modify `.codex-skills/`.

Do not modify raw samples.

Do not modify GUI/frontend.

Do not commit full `solve_reports/`.

Do not weaken artifact freshness policy globally.

Do not allow `training_dataset` to treat current-round missing/stale evidence as non-blocking.

Do not downgrade `reverse_solving` current evidence failures.

Do not hide real `report-summary` diffs or errors.

Do not patch generated JSON files manually to hide failure.

Do not treat `task_packet.task` as the current execution authority.

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
- `project_state/gates/round_delta_summary.json`
- `project_state/local_reverse_training_resume_plan.json`
- `project_state/local_reverse_type_coverage_matrix.json`
- `project_state/rounds/round_20260616_local_reverse_training_resume_plan_v1/round_manifest.json`, if present
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`
- `tests/test_local_reverse_training_status.py`

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded as baseline.
3. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
4. Current decision controls execution; `task_packet.json` is only state input.
5. Previous round failed only because of `status_policy_valid` after training resume artifacts were produced.
6. The artifact freshness blocker is historical sample artifact missing/stale state, not current-round generated training artifacts.
7. The previous training report did not claim historical `samplereverse` artifacts as current evidence.
8. Existing logic already distinguishes historical artifact freshness for `engineering_branch`.
9. The fix can be narrow and mainline-aware.
10. The fix will not change `reverse_solving` current evidence strictness.
11. The fix will not permit missing artifacts that are directly referenced by current training resume outputs.
12. Existing IDA/Ghidra/debugger/solver/harness capabilities are noted read-only; do not assume they do not exist.
13. `negative_results.json` is checked and no prohibited failed direction is repeated.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`

Allowed test changes:

- `tests/test_project_state.py`
- `tests/test_project_gate.py`

Allowed generated state/report updates:

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
- `project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/*`

Expected implementation:

1. In `reverse_agent/project_state.py`, update `_historical_artifact_freshness_is_non_blocking()` so its allowed non-blocking mainlines include both:
   - `engineering_branch`
   - `training_dataset`

2. In `reverse_agent/project_gate.py`, update `_status_policy_failure_is_historical_artifacts_only()` so the historical-artifact-only downgrade also applies to `training_dataset`.

3. Add focused tests proving:
   - `training_dataset` plus only historical missing/stale artifacts is non-blocking;
   - `engineering_branch` behavior remains unchanged;
   - `reverse_solving` with current missing/stale evidence still blocks;
   - `training_dataset` with current-round claimed missing artifact still blocks;
   - `status_policy_valid` passes when only historical sample artifact freshness exists;
   - `report_summary_synthesis` still fails on real status/report mismatch.

Do not modify:

- solver/sample-runner/IDA/debugger/emulator/harness modules;
- `.codex-skills/`;
- raw samples;
- GUI/frontend files;
- full `solve_reports/`;
- existing local_reverse resume plan artifacts, except generated state refresh if gates require it;
- `artifact_index.json`, unless using an existing tested mechanism and documenting provenance.

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
python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_local_reverse_training_status.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_training_dataset_historical_artifact_policy_v1
```

Validation expectations:

- pytest passes;
- `training_dataset` historical artifact freshness is non-blocking only when historical and not claimed as current evidence;
- `reverse_solving` freshness strictness remains intact;
- current-round training artifacts cannot be missing while report claims success;
- `report-summary` passes;
- `final-check` passes;
- `close-round` exits 0;
- archive is created.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if `training_dataset` still fails only because of historical sample artifact freshness.

Stop with `REWORK_REQUIRED` if `reverse_solving` missing/stale current evidence becomes non-blocking.

Stop with `REWORK_REQUIRED` if current-round training artifacts can be missing while report claims success.

Stop with `REWORK_REQUIRED` if `report-summary` fails.

Stop with `REWORK_REQUIRED` if `final-check` fails.

Stop with `REWORK_REQUIRED` if `close-round` exits nonzero.

Stop with `REWORK_REQUIRED` if solver/sample-runner/IDA/debugger/emulator/harness code is modified.

Stop with `REWORK_REQUIRED` if `.codex-skills/`, raw samples, GUI/frontend, or full `solve_reports/` are modified.

Stop with `REWORK_REQUIRED` if old sample_solver blind search, beam/budget expansion, or a negative_results failed direction is repeated.

Stop with `REWORK_REQUIRED` if stale/missing artifacts are treated as current evidence.

Stop with `BLOCKED` if the required fix needs broad project_state schema migration rather than a narrow mainline-aware policy update.

Do not write SUCCESS or ACCEPTED if final-check or close-round fails.

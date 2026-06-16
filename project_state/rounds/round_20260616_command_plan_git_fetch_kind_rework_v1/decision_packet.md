```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_command_plan_git_fetch_kind_rework_v1",
  "round_id": "round_20260616_command_plan_git_fetch_kind_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the command-plan classification gap that blocked `round_20260616_clean_baseline_handoff_v1`.

The previous round proved the clean baseline handoff, but `close-round` failed because `git fetch origin` was classified as `unknown`, causing `command_plan.plan_status=WARN` and `command_plan_ids_match=FAIL`.

This is an `engineering_branch` gate-command classification rework. Do not continue reverse solving. Do not rerun CPP1 or any local reverse sample.

Required end state:

- `git fetch origin` is recognized as a valid status command by command-plan;
- command-plan returns `PASSED` for the clean-baseline required command set;
- `command_plan_ids_match` passes;
- `report-summary` passes;
- `final-check` passes;
- `close-round` exits 0 and archives `round_20260616_command_plan_git_fetch_kind_rework_v1`;
- no solver, sample runner, IDA/debugger/probe, `.codex-skills/`, raw sample, GUI/frontend, training, or full `solve_reports/` files are modified.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round:

- `decision_20260616_clean_baseline_handoff_v1`
- `round_20260616_clean_baseline_handoff_v1`
- mainline: `engineering_branch`
- audit conclusion: `REWORK_REQUIRED`

Known facts from the audit:

- The previous round proved clean startup baseline: startup `git status --short` was empty after path confirmation.
- The previous round proved local `HEAD` matched `origin/main` at `de49b3e290de35c52f5b137eb236704669a67aeb`.
- `round_delta_summary.json` showed `baseline_dirty_files=[]` and `inherited_dirty_files=[]`.
- `pytest` passed with 583 tests.
- `report-summary` initially passed and `baseline_lifecycle_guard` passed.
- `close-round` failed with exit code 1 because `command_plan_ids_match` failed.
- `command_plan_ids_match` failed because `command_plan.json` had the correct `decision_id` and `round_id`, but `plan_status=WARN` instead of `PASSED`.
- `plan_status=WARN` was caused by `git fetch origin` being classified as `kind=unknown`, `phase=unknown`.
- This is a command classification gap in existing gate logic, not a reverse-solving issue and not a sample artifact issue.
- `negative_results.json` remains applicable: do not return to old sample_solver blind search, do not merely increase beam/budget, do not use compare_semantics_agree=false candidates as primary frontier, do not commit full `solve_reports/`, and do not repeat failed sample-search directions.
- Existing gate capabilities include `preflight`, `command-plan`, `run-round`, `report-summary`, `final-check`, `close-round`, baseline lifecycle checks, close snapshots, archive checks, and report synthesis.
- This round does not need IDA, Ghidra, debugger, emulator, solver, harness execution, GUI/frontend work, training dataset updates, or sample metadata changes.

## 3. Do Not Do

Do not rerun CPP1 or any local reverse sample.

Do not generate candidate material.

Do not modify solver logic, sample runners, IDA runner semantics, debugger/emulator/probe code, `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not weaken decision/report/pytest/round id matching.

Do not change `command_plan_ids_match` to accept arbitrary `WARN`.

Do not globally allow unknown command kinds.

Do not suppress real command-plan warnings.

Do not manually patch gate JSON files to hide failures.

Do not remove historical missing artifact entries just to pass gates.

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

- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_baseline.json`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if needed to confirm no unrelated test changes are required
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, read-only verification only

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. The previous failure is specifically `git fetch origin` classified as `unknown`.
4. `command_plan.json` had the correct `decision_id` and `round_id`; the only relevant mismatch was `plan_status=WARN`.
5. The previous round did not have source/test inherited dirty files.
6. Existing `_command_kind()` / `_command_phase()` mechanisms can be extended rather than replaced.
7. Current CPP1 artifacts remain current and are not modified.

Required result:

- Add narrow support for `git fetch` as a recognized command kind.
- Classify `git fetch` as status-phase command.
- Keep unknown unrelated commands as WARN.
- Keep `command_plan_ids_match` strict; prefer command classification over relaxing acceptance.
- Regenerate gate outputs through CLI commands, not by manual JSON editing.
- Close and archive `round_20260616_command_plan_git_fetch_kind_rework_v1`.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`

Allowed test changes:

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
- `project_state/rounds/round_20260616_command_plan_git_fetch_kind_rework_v1/*`

Expected implementation:

- Extend `_command_kind()` so `git fetch`, including `git fetch origin`, returns a recognized kind such as `git fetch`.
- Extend or confirm `_command_phase()` treats `git fetch` as `status`.
- Add focused tests proving command-plan with `git fetch origin` returns `plan_status=PASSED` when no other warnings exist.
- Add focused tests proving unrelated unknown commands still produce WARN.

Do not modify:

- solver/sample-runner/IDA/debugger/harness modules
- `.codex-skills/`
- raw samples
- GUI/frontend files
- full `solve_reports/`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`
- `project_state/artifact_index.json`, except read-only verification

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_command_plan_git_fetch_kind_rework_v1
```

Focused tests must cover:

- `_command_kind("git fetch origin") == "git fetch"` or an equivalent recognized kind;
- `_command_phase("git fetch", archive_seen=False) == "status"` or equivalent status-phase classification;
- command-plan with `git fetch origin` returns `plan_status=PASSED` when no other warnings exist;
- unknown unrelated commands still produce WARN;
- close-round still fails on real command-plan id mismatch;
- clean baseline behavior remains intact;
- no current CPP1 artifact changes.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if `git fetch origin` still becomes `unknown`.

Stop with `REWORK_REQUIRED` if command-plan remains `WARN` only because of `git fetch`.

Stop with `REWORK_REQUIRED` if `command_plan_ids_match` still fails.

Stop with `REWORK_REQUIRED` if `report-summary` fails.

Stop with `REWORK_REQUIRED` if `final-check` fails.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if source/test dirty baseline reappears unexpectedly and is not explained by this round's actual source/test edits.

Stop with `REWORK_REQUIRED` if any forbidden path is modified.

Stop with `REWORK_REQUIRED` if any CPP1 evidence artifact is modified.

Stop with `BLOCKED` if this requires broad command planner redesign instead of a narrow command classification fix.

Do not write SUCCESS or ACCEPTED if close-round fails.

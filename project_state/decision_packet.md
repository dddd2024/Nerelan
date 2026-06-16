```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_clean_baseline_handoff_v1",
  "round_id": "round_20260616_clean_baseline_handoff_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close the dirty-baseline handoff risk left by `round_20260616_report_summary_status_semantics_v1`.

This is an `engineering_branch` verification and state-hygiene round. Do not change gate semantics. Do not continue reverse solving. Do not rerun CPP1 or any local reverse sample.

Required end state:

- the local repository has consumed the latest GitHub/main commit containing the accepted report-summary status semantics work;
- startup evidence proves whether the worktree begins clean after path and repository confirmation;
- if startup `git status --short` contains source/test dirty files, stop and report `BLOCKED` or `REWORK_REQUIRED` without modifying source/test files;
- if startup is clean, run the normal gate/report/close sequence and produce a new archived round proving a clean baseline handoff;
- `round_baseline.json` / `round_delta_summary.json` for this round must not classify `reverse_agent/project_gate.py` or `tests/test_project_gate.py` as inherited dirty files;
- no source/test files are modified in this round;
- current CPP1 artifacts remain unchanged.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Previous accepted round:

- `decision_20260616_report_summary_status_semantics_v1`
- `round_20260616_report_summary_status_semantics_v1`
- mainline: `engineering_branch`
- audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known facts from the audit:

- The previous round fixed the core report-summary status semantics issue: `project_state/gates/report_summary_synthesis.json` now uses `synthesis_status=PASSED` when there are no `errors`, no `diffs`, and no blocking warnings.
- The previous round recorded `583 passed` for `tests/test_project_state.py` and `tests/test_project_gate.py`.
- The previous round passed `report-summary`, `final-check`, and `close-round`.
- The limitation was process-level: startup `git status --short` already showed `reverse_agent/project_gate.py` and `tests/test_project_gate.py` as dirty, so the round closed with inherited source/test dirty warnings even though the files were within allowed scope and startup evidence was trusted.
- The next useful step is not more gate logic. The next useful step is proving that, after the accepted commit is pulled from GitHub, a new round can start from a clean source/test baseline.
- Historical `samplereverse` task/current_state contents are not the execution authority for this round.
- Historical missing sample artifacts are external notices for this engineering branch round, not current evidence to solve a sample.
- `negative_results.json` still forbids returning to old sample solver blind search, merely increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full `solve_reports/`, and repeating failed sample-search directions.
- Existing gate capabilities include `preflight`, `command-plan`, `run-round`, `report-summary`, `final-check`, `close-round`, baseline lifecycle checks, close snapshots, archive checks, and report synthesis.
- This round does not need IDA, Ghidra, debugger, emulator, solver, harness execution, GUI/frontend work, training dataset updates, or sample metadata changes.

## 3. Do Not Do

Do not modify `reverse_agent/project_gate.py`.

Do not modify `tests/test_project_gate.py` or any other test file.

Do not modify solver logic, sample runners, IDA runner semantics, debugger/emulator/probe code, `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not rerun CPP1 or any local reverse sample.

Do not generate candidate material.

Do not manually patch gate JSON files to hide startup dirty files.

Do not weaken decision/report/pytest/round id matching.

Do not weaken artifact freshness policy.

Do not remove historical missing artifact entries just to pass gates.

Do not treat `task_packet.task` as the current execution authority.

Do not proceed past startup verification if source/test files are already dirty after syncing the accepted GitHub commit.

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

- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260616_report_summary_status_semantics_v1/round_manifest.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, read-only verification only
- `reverse_agent/project_gate.py`, read-only verification only
- `tests/test_project_gate.py`, read-only verification only

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before any generated state update, confirm:

1. `Set-Location F:\reverse-agent`, `Get-Location`, `Test-Path F:\reverse-agent`, and `git rev-parse --show-toplevel` prove the correct repository.
2. Fetch remote metadata and confirm the local checkout is not behind `origin/main`. If it is behind and the worktree is clean, fast-forward to `origin/main`; if it is behind and dirty, stop and report the dirty files.
3. Run `git status --short` after path confirmation and after any fast-forward sync.
4. If startup `git status --short` includes `reverse_agent/` or `tests/` source/test paths, stop. This round is specifically to prove clean source/test baseline; inherited source/test dirty files are not acceptable for this round.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. The previous round's `codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, and `final_gate_result.json` all refer to `decision_20260616_report_summary_status_semantics_v1` or the current round as appropriate before they are regenerated.
7. Current CPP1 artifact remains present and is only read for verification.

Required result if startup is clean:

- create a normal `codex_execution_report.md` for this round;
- record all commands and outputs in `project_state/pytest_result.txt`;
- regenerate gate outputs through the project gate commands, not by manual editing;
- close and archive `round_20260616_clean_baseline_handoff_v1`;
- final `round_delta_summary.json` may include generated gate/report/archive files, but must not include source/test files as inherited dirty or new dirty;
- final `final_gate_result.json` must not contain `baseline_capture_order` or `files_changed_excludes_inherited_dirty_files` warnings caused by source/test inherited dirty files.

## 6. Implementation Scope

No source changes are allowed.

No test changes are allowed.

Allowed generated state/report updates only:

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
- `project_state/rounds/round_20260616_clean_baseline_handoff_v1/*`

Read-only source/test verification is allowed for:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Do not modify:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`
- `project_state/artifact_index.json`
- solver/sample-runner/IDA/debugger/harness modules
- `.codex-skills/`

If any source/test modification appears necessary, stop and report `BLOCKED`; do not make the modification in this round.

## 7. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git fetch origin
git status -sb
git rev-parse HEAD
git rev-parse origin/main
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_clean_baseline_handoff_v1
```

If `git rev-parse HEAD` and `git rev-parse origin/main` differ after fetch:

- if `git status --short` is empty, run `git pull --ff-only` and record it before continuing;
- if `git status --short` is not empty, stop and report `BLOCKED` with the dirty file list.

Validation expectations:

- `git status --short` startup block after path confirmation must not contain source/test dirty files;
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q` must pass;
- `report-summary` must pass;
- `final-check` must pass;
- `close-round` must exit 0;
- `round_delta_summary.json` must show no inherited source/test dirty files for this round;
- no current CPP1 artifact should change.

## 8. Stop Conditions

Stop with `BLOCKED` if local checkout cannot be synced to the current GitHub/main commit without overwriting local dirty files.

Stop with `REWORK_REQUIRED` if startup `git status --short` contains source/test dirty files after sync.

Stop with `REWORK_REQUIRED` if `round_baseline.json` or `round_delta_summary.json` records `reverse_agent/project_gate.py`, `tests/test_project_gate.py`, or other source/test files as inherited dirty in this round.

Stop with `REWORK_REQUIRED` if `final_gate_result.json` is FAILED.

Stop with `REWORK_REQUIRED` if `report-summary` fails or `report_summary_synthesis.json` has `errors` or `diffs`.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if any source/test file is modified.

Stop with `REWORK_REQUIRED` if CPP1 evidence artifacts are modified.

Stop with `REWORK_REQUIRED` if the round weakens id matching, artifact freshness checks, forbidden path checks, or unauthorized dirty detection.

Do not write SUCCESS or ACCEPTED if this round starts with source/test inherited dirty files.

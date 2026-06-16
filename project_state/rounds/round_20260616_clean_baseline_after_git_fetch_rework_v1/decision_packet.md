```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_clean_baseline_after_git_fetch_rework_v1",
  "round_id": "round_20260616_clean_baseline_after_git_fetch_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Verify a clean source/test baseline after the accepted `git fetch` command-plan classification rework.

This is an `engineering_branch` state-hygiene verification round. Do not change source code. Do not change tests. Do not continue reverse solving. Do not rerun CPP1 or any local reverse sample.

Required end state:

- the local checkout has consumed the current GitHub/main commit that contains `round_20260616_command_plan_git_fetch_kind_rework_v1`;
- startup evidence proves whether the source/test worktree begins clean;
- `git fetch` remains recognized by command-plan as `kind=git fetch`, `phase=status`;
- `command-plan` returns `PASSED` without unknown-command warnings;
- `round_baseline.json` and `round_delta_summary.json` for this round must not record `reverse_agent/project_gate.py`, `tests/test_project_gate.py`, or any other source/test path as inherited dirty;
- no source/test files are modified in this round;
- `report-summary` passes;
- `final-check` passes;
- `close-round` exits 0 and archives `round_20260616_clean_baseline_after_git_fetch_rework_v1`;
- current CPP1 evidence artifacts remain unchanged.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Previous accepted round:

- `decision_20260616_command_plan_git_fetch_kind_rework_v1`
- `round_20260616_command_plan_git_fetch_kind_rework_v1`
- mainline: `engineering_branch`
- audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known facts from the audit:

- The previous round fixed the immediate command-plan blocker: `git fetch` is now classified as `kind=git fetch`, `phase=status`.
- The previous round's `command_plan.json` had `plan_status=PASSED`, `warnings=[]`, and `blocking_reasons=[]`.
- The previous round recorded `589 passed` for `tests/test_project_state.py` and `tests/test_project_gate.py`.
- The previous round passed `report-summary`, `final-check`, and `close-round`, and archived `round_20260616_command_plan_git_fetch_kind_rework_v1`.
- The limitation was process-level: `reverse_agent/project_gate.py` and `tests/test_project_gate.py` were still dirty at startup/baseline because they were the authorized implementation files for that round.
- The next useful step is not more gate logic. The next useful step is proving that, after the accepted rework is committed and synced, a fresh round starts with no source/test dirty baseline.
- Historical `samplereverse` task/current_state contents are not the execution authority for this round.
- Historical missing sample artifacts are external notices for this engineering branch round, not current evidence to solve a sample.
- `negative_results.json` still forbids returning to old sample_solver blind search, merely increasing beam/budget, using compare_semantics_agree=false candidates as primary frontier, committing full `solve_reports/`, and repeating failed sample-search directions.
- Existing gate capabilities include `preflight`, `command-plan`, `run-round`, `report-summary`, `final-check`, `close-round`, baseline lifecycle checks, close snapshots, archive checks, report synthesis, and recognized `git fetch` command classification.
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

Do not weaken command-plan unknown-command detection.

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

- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260616_command_plan_git_fetch_kind_rework_v1/round_manifest.json`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, read-only verification only
- `reverse_agent/project_gate.py`, read-only verification only
- `tests/test_project_gate.py`, read-only verification only

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before any generated state update, confirm:

1. `Set-Location F:\reverse-agent`, `Get-Location`, `Test-Path F:\reverse-agent`, and `git rev-parse --show-toplevel` prove the correct repository.
2. Run `git fetch` and confirm it exits 0.
3. Run `git status -sb`, `git rev-parse HEAD`, and `git rev-parse origin/main`.
4. If `HEAD` and `origin/main` differ after fetch, stop and report `BLOCKED` with the two commit hashes. Do not attempt broad sync or reset inside this round.
5. Run `git status --short` after path confirmation and fetch.
6. If startup `git status --short` includes any `reverse_agent/` or `tests/` source/test path, stop and report `REWORK_REQUIRED` without modifying source/test files. This round is specifically to prove clean source/test baseline after the prior rework commit is consumed.
7. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
8. The previous round's report, pytest result, command_plan, final gate result, and round manifest all refer to `decision_20260616_command_plan_git_fetch_kind_rework_v1` before this round regenerates live gate files.
9. Current CPP1 artifact remains present and is only read for verification.

Required result if startup is clean:

- create a normal `codex_execution_report.md` for this round;
- record all commands and outputs in `project_state/pytest_result.txt`;
- regenerate gate outputs through project gate commands, not by manual JSON editing;
- close and archive `round_20260616_clean_baseline_after_git_fetch_rework_v1`;
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
- `project_state/rounds/round_20260616_clean_baseline_after_git_fetch_rework_v1/*`

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
git fetch
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_clean_baseline_after_git_fetch_rework_v1
```

Validation expectations:

- startup `git status --short` after path confirmation and fetch must not contain source/test dirty files;
- `git rev-parse HEAD` must equal `git rev-parse origin/main` after fetch;
- `command-plan` must classify `git fetch` as status / git fetch and return `PASSED`;
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q` must pass;
- `report-summary` must pass;
- `final-check` must pass;
- `close-round` must exit 0;
- `round_delta_summary.json` must show no inherited source/test dirty files for this round;
- no current CPP1 artifact should change.

## 8. Stop Conditions

Stop with `BLOCKED` if local `HEAD` does not match `origin/main` after `git fetch`.

Stop with `REWORK_REQUIRED` if startup `git status --short` contains any source/test dirty files after path confirmation and fetch.

Stop with `REWORK_REQUIRED` if `round_baseline.json` or `round_delta_summary.json` records `reverse_agent/project_gate.py`, `tests/test_project_gate.py`, or any other source/test file as inherited dirty in this round.

Stop with `REWORK_REQUIRED` if `git fetch` is not recognized by command-plan or command-plan returns `WARN` because of `git fetch`.

Stop with `REWORK_REQUIRED` if `command_plan_ids_match` fails.

Stop with `REWORK_REQUIRED` if `report-summary` fails.

Stop with `REWORK_REQUIRED` if `final-check` fails.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if any source/test file is modified.

Stop with `REWORK_REQUIRED` if CPP1 evidence artifacts are modified.

Stop with `REWORK_REQUIRED` if the round weakens id matching, artifact freshness checks, forbidden path checks, command-plan unknown-command detection, or unauthorized dirty detection.

Do not write SUCCESS or ACCEPTED if this round starts with source/test inherited dirty files.

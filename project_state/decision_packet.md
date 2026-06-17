```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_artifact_only_validation_v2",
  "round_id": "round_20260618_fast_artifact_only_validation_v2",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Run a real `fast` artifact-only validation v2 round after the fast non-closeout source fix.

This round must not modify source or test code. Its purpose is to validate the live low-risk behavior after `decision_20260617_fast_non_closeout_semantics_source_fix_v1`:

- `gate-profile` auto-selects `profile=fast` for artifact/report-only scope;
- `closeout_allowed=false` is preserved;
- `command-plan --json` includes `profile_meta.profile=fast`;
- `command-plan --json` includes `omitted_commands` entries for both pytest and close-round;
- the close-round omitted entry must exist even though close-round is absent from this decision's Tests section;
- `final-check` accepts the fast non-closeout state without requiring normal archive files;
- the report must not claim normal archive/close-round success;
- no `project_state/rounds/round_20260618_fast_artifact_only_validation_v2/*` normal archive should be created unless final-check explicitly proves close-round is allowed, which is not expected for this round;
- full-profile and standard-profile behavior must not be changed in this round.

This is an engineering-branch validation task. It must not turn into reverse-solving, tool-integration, training-dataset work, or another source implementation round.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous accepted-with-limitations source-fix round:

- `decision_20260617_fast_non_closeout_semantics_source_fix_v1`
- `round_20260617_fast_non_closeout_semantics_source_fix_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known state from the previous audit:

- The source-fix round was a valid `full` round because it changed `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- It reported `SUCCESS/ACCEPTED`.
- pytest passed with 741 tests.
- final-check passed.
- close-round succeeded under `profile=full`.
- The source-fix report claimed the intended fixes were implemented:
  - fast non-closeout command-plan now explicitly records close-round omission;
  - `fast_profile_closeout_consistency` detects implicit close-round omission;
  - `report_summary_synthesis` / final-check no longer require normal archive paths for fast non-closeout.
- Because the previous real round was `full`, a real artifact-only fast validation is still required.

Meaning:

- Do not implement more source changes in this round.
- Validate the repaired behavior only through project_state/gate artifact regeneration.
- If fast non-closeout still cannot be validated without source changes, report `REWORK_REQUIRED` and stop.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- command-plan expected-exit semantics;
- report-body consistency check;
- gate-profile metadata and consistency checks;
- `gate_profile_closeout_safety` check;
- fast profile scope checks;
- fast pytest omitted-command metadata;
- fast close-round omitted-command metadata;
- fast non-closeout archive exemption;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check;
- full-profile close-round and archive behavior.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this validation.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Existing tool capability boundary:

- This round is not reverse-solving.
- This round does not require IDA/Ghidra/debugger/solver/harness execution.
- Mature reverse tools must not be modified or reimplemented.

## 3. Do Not Do

Do not modify `reverse_agent/*.py`.

Do not modify `tests/*.py`.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` files.

Do not implement new gate logic in this round.

Do not expand `standard` behavior.

Do not run pytest.

Do not run close-round.

Do not create a normal round archive for this fast non-closeout validation unless final-check explicitly proves `closeout_allowed=true`; expected behavior is `closeout_allowed=false` and no normal archive.

Do not claim `SUCCESS/ACCEPTED` if:

- `gate-profile` does not auto-select fast;
- `command-plan` lacks a close-round omitted entry;
- `final-check` still requires normal archive files;
- any source/test file becomes dirty;
- close-round is run despite `closeout_allowed=false`.

Do not treat `task_packet.task` as current execution authority.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

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

Also inspect:

- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a gate command directly reports them as a blocking forbidden path.

## 5. Required Audit

Before any artifact update, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` is clean, later project_state dirty files are this-round artifact changes, not inherited baseline dirty.
4. If startup `git status --short` already shows any `reverse_agent/*.py` or `tests/*.py` dirty file, stop immediately and write `status=BLOCKED` or `FAILED` with `acceptance_recommendation=REWORK_REQUIRED`; do not continue.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not continue.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm no mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

No source/test implementation is allowed in this round.

Forbidden files:

- `reverse_agent/*.py`
- `tests/*.py`
- `.codex-skills/*`
- solver/harness/tool-runner/debugger/sample/GUI/frontend/raw sample files

Allowed project-state/report files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` only if produced by an allowed command and explicitly marked as non-archive evidence; expected behavior is no new normal close snapshot

Do not write a normal `project_state/rounds/round_20260618_fast_artifact_only_validation_v2/*` archive unless final-check proves `closeout_allowed=true`. Current expected behavior is fast non-closeout, so no normal archive should be produced.

Required validation behavior:

- Run startup and preflight first.
- Run `gate-profile` and `command-plan` in artifact-only state.
- Auto-selected `gate-profile` must be `profile=fast`.
- `gate_profile_plan.json` must carry current decision_id/round_id and `profile=fast`.
- `command_plan.json` must carry current decision_id/round_id and `profile_meta.profile=fast`.
- `profile_meta.closeout_allowed` must be false.
- `command_plan.json` must include an omitted pytest entry.
- `command_plan.json` must include an omitted close-round entry with reason indicating closeout is not allowed.
- `command_plan.json` must not include pytest or close-round in active commands.
- `report-summary` and `final-check` must be run after the report/pytest_result artifacts are written.
- `final-check` must not require normal archive files for this fast non-closeout round.
- `final-check` must not report stale current decision/round/report IDs.
- `codex_execution_report.md` must clearly state that close-round was intentionally omitted because fast `closeout_allowed=false`.
- `codex_execution_report.md` must not claim normal archive success.
- If final-check can pass without archive and with fast non-closeout metadata, report may use `SUCCESS/ACCEPTED` for the validation result only, with explicit non-archived/non-closeout status.
- If final-check still fails because archive files are expected or close-round omission is not recognized, report must use `PARTIAL` or `FAILED` with `acceptance_recommendation=REWORK_REQUIRED`.

Required evidence in final artifacts:

- `gate_profile_plan.json`: current IDs, `profile=fast`, `closeout_allowed=false`.
- `command_plan.json`: current IDs, `profile_meta.profile=fast`, omitted pytest entry, omitted close-round entry.
- `final_gate_result.json`: fast profile checks PASS and no normal archive requirement for fast non-closeout.
- `codex_execution_report.md`: no source/test changes claimed; no normal archive success claimed.
- `files_changed` and `generated_artifacts`: no `reverse_agent/*.py` or `tests/*.py` paths.

## 7. Tests

Run and record only the following commands in `project_state/pytest_result.txt` unless stopped by startup/preflight rules:

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
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Do not run pytest.

Do not run close-round.

The pytest_result header must include:

- `decision_id=decision_20260618_fast_artifact_only_validation_v2`
- `round_id=round_20260618_fast_artifact_only_validation_v2`
- the final `report_id`
- all commands actually run
- explicit notation that pytest and close-round were intentionally omitted by fast non-closeout

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- any source/test file becomes dirty;
- fast cannot be auto-selected;
- command-plan does not include omitted close-round metadata;
- final-check still expects normal archive files for fast non-closeout;
- final-check cannot distinguish fast non-closeout from normal archived closeout;
- making this pass requires source/test modification;
- making this pass requires changing solver/harness/tool-runner/debugger/sample code.

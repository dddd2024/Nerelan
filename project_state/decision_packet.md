```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_fast_artifact_only_validation_rework_v1",
  "round_id": "round_20260617_fast_artifact_only_validation_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Rework the `fast` artifact-only validation semantics from `decision_20260617_fast_artifact_only_validation_v1`.

The previous round was reported as `COMPLETED_WITH_LIMITATIONS`, but the limitations show a real validation inconsistency: fast profile selected correctly and source/test files were not changed, yet the report/synthesis/archive semantics still do not cleanly represent `closeout_allowed=false` and omitted close-round behavior.

Required end state:

- no `reverse_agent/*.py`, `tests/*.py`, solver, harness, reverse-tool, sample, GUI, or `.codex-skills/` file is modified;
- startup status is clean before any artifact update;
- fast auto-selection remains `profile=fast` for the artifact-only validation scope;
- `command_plan.json` must clearly prove whether pytest and close-round were omitted by fast trimming;
- if `omitted_commands` cannot prove pytest/close-round omission because these commands were absent from the decision Tests section, the report must state validation is incomplete and use `PARTIAL` or `FAILED`, not `SUCCESS/ACCEPTED`;
- `fast_profile_closeout_consistency` must not claim `close_round_omitted=false` when `command_plan.json` contains no close-round command;
- if `closeout_allowed=false`, report/synthesis/final gate must not imply normal archive closeout success;
- if a manual archive directory is created for recordkeeping, it must be labeled as manual/non-closeout evidence and must not be used as proof of normal close-round success;
- full and standard behavior must not be changed in this round.

This is an engineering-branch artifact/report semantics rework. It must not become a source/test implementation round.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous round under review:

- `decision_20260617_fast_artifact_only_validation_v1`
- `round_20260617_fast_artifact_only_validation_v1`
- Codex self-reported: `COMPLETED_WITH_LIMITATIONS`
- GPT audit conclusion: `REWORK_REQUIRED`

Evidence from the previous round:

- `gate-profile` auto-selected `profile=fast`.
- `closeout_allowed=false`.
- `required_command_kinds=[startup, preflight, command-plan, report-summary, final-check]`.
- Explicit `gate-profile --profile fast --json` matched auto fast.
- `command-plan` contained 13 commands, all within fast required command kinds.
- `command-plan` did not include pytest, run-round, doctor, lint-report, or close-round.
- No `reverse_agent/*.py` or `tests/*.py` files were modified.
- `final-check` passed with fast-profile checks shown as PASS.
- Report claimed `SUCCESS/ACCEPTED`.

Blocking inconsistencies:

- The decision required `omitted_commands` to record pytest and close-round omission reasons, but `command_plan.json` had `omitted_commands=[]`.
- The command plan had no close-round command, but `fast_profile_closeout_consistency` reported `close_round_omitted=false` while `closeout_allowed=false`.
- The report claimed `SUCCESS/ACCEPTED` although normal close-round was not run and closeout was not allowed.
- Archive/synthesis paths existed from manual recordkeeping, while fast profile was explicitly `closeout_allowed=false`, causing archive semantics to be ambiguous.
- The round manifest was non-minimal / manually archived rather than a normal close-round archive.

Meaning:

- The fast classifier worked.
- The no-source/no-test constraint worked.
- The command-plan and final-check semantic reporting around omitted close-round and closeout_allowed=false is not yet trustworthy.
- This rework should repair state/report evidence, not implement a new gate engine.

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
- fast omitted-command metadata where representable;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this fast validation rework.
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

Do not implement new gate logic in this round unless the existing artifact/report commands already expose a safe flag for this exact semantic correction.

Do not expand `standard` behavior.

Do not run pytest.

Do not run close-round.

Do not create or rely on a normal close-round archive when `fast.closeout_allowed=false`.

Do not claim `SUCCESS/ACCEPTED` if omitted pytest/close-round evidence is incomplete or closeout semantics are ambiguous.

Do not hide the `omitted_commands=[]` limitation.

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
3. If startup `git status --short` is clean, later artifact dirty files are this-round changes, not inherited baseline dirty.
4. If startup `git status --short` already shows any `reverse_agent/*.py` or `tests/*.py` dirty file, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not continue.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not continue.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm fast profile auto-selects `fast`.
9. Confirm whether command-plan lacks close-round and pytest.
10. Confirm whether `omitted_commands` records those omissions.
11. Confirm no mature reverse-engineering tool integration needs to be modified.

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
- `project_state/gates/round_close_snapshot.json` only if explicitly marked as manual/non-closeout; otherwise do not generate it

Do not write a normal `project_state/rounds/round_20260617_fast_artifact_only_validation_rework_v1/*` archive unless an existing final-check result explicitly proves fast closeout is safe. Current expected behavior is that fast closeout is not safe and no normal archive should be produced.

Required rework behavior:

- Run startup and preflight first.
- Run `gate-profile` and `command-plan` in artifact-only state.
- Preserve auto-selected `fast` if it still applies.
- If `omitted_commands=[]` while pytest/close-round are absent, report validation as incomplete: `status=PARTIAL` or `FAILED`; `acceptance_recommendation=REWORK_REQUIRED`.
- If final-check reports `close_round_omitted=false` while command-plan contains no close-round command, explicitly record this as the rework blocker.
- If `closeout_allowed=false`, do not claim normal archive closeout.
- The final report must distinguish:
  - fast classifier success;
  - command-plan trim evidence incomplete/complete;
  - closeout not allowed;
  - no source/test changes.
- Final report must not claim `SUCCESS/ACCEPTED` unless all above inconsistencies are resolved by existing artifact/report evidence only.

Required evidence in final artifacts:

- `gate_profile_plan.json` carries current decision_id/round_id and `profile=fast`.
- `command_plan.json` carries current decision_id/round_id and `profile_meta.profile=fast`.
- `codex_execution_report.md` does not claim source/test changes.
- `files_changed` and `generated_artifacts` do not include any `reverse_agent/*.py` or `tests/*.py` path.
- If rework remains incomplete, report must explicitly recommend a future source-code fix in a separate engineering round, not silently accept.

## 7. Tests

Run only:

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

- `decision_id=decision_20260617_fast_artifact_only_validation_rework_v1`
- `round_id=round_20260617_fast_artifact_only_validation_rework_v1`
- the final `report_id`
- all commands actually run
- explicit notation that pytest and close-round were intentionally omitted

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

- any source/test file becomes dirty;
- fast cannot be auto-selected;
- omitted_commands cannot prove pytest/close-round omission;
- final-check cannot correctly identify omitted close-round;
- report would need to claim archived/accepted closeout while `closeout_allowed=false`;
- implementing the fix requires changing `reverse_agent/*.py` or `tests/*.py`;
- implementing the fix requires changing solver/harness/tool-runner/debugger/sample code;
- the validation requires replacing or rewriting the existing gate system.

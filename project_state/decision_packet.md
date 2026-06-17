```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_fast_artifact_only_validation_v1",
  "round_id": "round_20260617_fast_artifact_only_validation_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Run a real `fast` artifact-only validation round.

This round must not change source or test code. Its purpose is to validate the fast-profile command trimming behavior in the actual low-risk condition it was designed for: project-state/report/gate artifact updates only.

Required end state:

- no `reverse_agent/*.py`, `tests/*.py`, solver, harness, reverse-tool, sample, GUI, or `.codex-skills/` file is modified;
- startup status is clean before any artifact update;
- `gate-profile` selects or can explicitly run `fast` for an artifact/report-only scope;
- `command-plan --json` for fast contains `profile_meta.profile=fast`;
- fast `command-plan --json` contains `omitted_commands` for heavy commands such as pytest and close-round, with reasons;
- fast command-plan still includes startup/status, preflight, gate-profile, command-plan, report-summary, final-check, and required currentness/artifact checks;
- fast must not claim archived closeout if close-round is omitted;
- fast must not write `SUCCESS/ACCEPTED` if final-check is not compatible with omitted close-round;
- final-check must verify fast scope is artifact-only and must reject any source/test logic delta under fast;
- close-round must not be run as a normal closeout command if `fast.closeout_allowed=false`;
- full path behavior is not changed in this round;
- standard profile behavior is not changed in this round.

This is an engineering-branch gate validation task. It must not turn into reverse-solving, tool-integration, or training-dataset work.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous accepted-with-limitations round:

- `decision_20260617_fast_profile_command_trimming_pilot_v1`
- `round_20260617_fast_profile_command_trimming_pilot_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known state from the previous audit:

- Fast profile command trimming was implemented in code.
- The previous real execution round still ran as `full`, because it modified `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- `command-plan --json` in that previous full round had `omitted_commands=[]`, which was correct for full.
- Fast-specific final-check checks existed and passed as not-applicable for the full round.
- pytest passed with 731 tests.
- final-check passed.
- close-round archived the round.
- Remaining limitation: fast trimming has not yet been validated in a real artifact-only round.

Meaning:

- The code-level fast pilot is implemented.
- The next required evidence is a no-source/no-test fast artifact-only validation round.
- This round should produce artifact evidence, not new source logic.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- command-plan expected-exit semantics;
- conditional close-round behavior;
- report-body consistency check;
- gate-profile metadata and consistency checks;
- `gate_profile_closeout_safety` check;
- fast profile scope checks;
- fast omitted-command metadata;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this fast validation.
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

Allowed execution:

- Read repository source/tests and compact `project_state/` metadata only as context.
- Run only the gate/status commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not modify `reverse_agent/*.py`.

Do not modify `tests/*.py`.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` files.

Do not implement new gate logic in this round.

Do not expand `standard` behavior.

Do not use fast to bypass source/test/gate/project_state logic changes.

Do not run pytest as part of the fast validation path unless fast incorrectly selected a source/test scope; if that happens, stop and report REWORK_REQUIRED instead of normalizing the result.

Do not run close-round as normal closeout if fast profile reports `closeout_allowed=false`.

Do not claim `SUCCESS/ACCEPTED` if close-round was omitted but the report claims archive/closeout success.

Do not weaken final-check, close-round, preflight, decision immutability, startup/baseline, stale artifact, generated-artifact, command-plan, report-body, or profile consistency checks.

Do not globally allow reduced checks for all rounds.

Do not implement LLM-based profile selection.

Do not add another independent gate engine.

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
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a gate command directly reports them as a blocking forbidden path.

## 5. Required Audit

Before any artifact update, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` is clean, later artifact dirty files are this-round changes, not inherited baseline dirty.
4. If startup `git status --short` already shows any `reverse_agent/*.py` or `tests/*.py` dirty file, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not continue.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not continue.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm existing fast profile command trimming exists before running the validation.
9. Confirm no mature reverse-engineering tool integration needs to be modified.

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
- `project_state/gates/run_round_result.json` only if generated by allowed command and not used to force full/pytest
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` only if a safe non-archive snapshot is produced; do not create archive if fast closeout is disallowed
- `project_state/rounds/round_20260617_fast_artifact_only_validation_v1/*` only if closeout is explicitly allowed by final-check; otherwise do not archive

Required validation behavior:

- Run startup and preflight first.
- Run `gate-profile` and `command-plan` in the artifact-only state.
- Prefer auto-selection of `fast`; if auto-selection does not select fast for a clean artifact-only scope, record this as REWORK_REQUIRED rather than forcing source/test changes.
- It is acceptable to additionally run an explicit `gate-profile --profile fast --json` inspection if the CLI supports it, but the validation result must state whether auto-selected fast or only explicit fast worked.
- The fast command-plan must include `omitted_commands` for pytest and close-round if fast closeout is not allowed.
- The fast command-plan must not include pytest when no source/test files changed.
- The fast command-plan must not include close-round when `closeout_allowed=false`.
- Run report-summary and final-check after the report and pytest_result artifacts are written.
- If final-check says the fast validation is not closeout-safe, write `status=PARTIAL` or `FAILED` with `acceptance_recommendation=REWORK_REQUIRED`; do not run close-round.
- If final-check proves fast artifact-only closeout is explicitly safe, close-round may be run; otherwise it must be omitted.
- The final report must state clearly whether fast was auto-selected, whether pytest was omitted, whether close-round was omitted, and why.

Required evidence in final artifacts:

- `gate_profile_plan.json` must carry current decision_id/round_id and `profile=fast` for a successful fast validation.
- `command_plan.json` must carry current decision_id/round_id and `profile_meta.profile=fast` for a successful fast validation.
- `command_plan.json` must include `omitted_commands` with reasons.
- `final_gate_result.json` must include fast-profile validation checks.
- `codex_execution_report.md` must not claim source/test changes.
- `files_changed` and `generated_artifacts` must not include any `reverse_agent/*.py` or `tests/*.py` path.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt` unless stopped by preflight/startup rules:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate gate-profile --state-dir project_state --profile fast --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Do not run pytest or close-round in the normal fast validation path unless final-check explicitly proves that fast closeout is safe and the command-plan requires it.

The pytest_result header must include:

- `decision_id=decision_20260617_fast_artifact_only_validation_v1`
- `round_id=round_20260617_fast_artifact_only_validation_v1`
- the final `report_id`
- all commands actually run
- explicit notation that pytest and close-round were omitted if fast trimmed them

If fast auto-selection fails and the system selects `full`, record that as `REWORK_REQUIRED` for this validation round unless the reason is a real source/test dirty state detected at startup, in which case report `BLOCKED`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- any source/test file modification is required;
- pytest becomes necessary to make this round pass;
- close-round must be run despite fast `closeout_allowed=false`;
- fast auto-selection cannot select fast for artifact/report-only scope;
- final-check cannot validate fast omitted pytest/close-round safely;
- implementing this would require changing solver/harness/tool-runner/debugger/sample code;
- the validation requires replacing or rewriting the existing gate system.

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_gate_profile_tier_integration_v1",
  "round_id": "round_20260617_gate_profile_tier_integration_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Formally integrate the gate tier design around the existing `gate-profile` mechanism.

The goal is to turn the current advisory fast/standard/full profile idea into a small, testable execution-policy layer without weakening the default full gate path.

Required end state:

- define explicit semantics for `fast`, `standard`, and `full` profiles;
- preserve `full` as the default profile for close-round and archive safety;
- allow `gate-profile` and `command-plan` to expose the selected profile, profile reason, allowed command set, and whether close-round is permitted;
- support explicit profile selection for inspection/dry-run, while preventing accidental archive/close-round under an insufficient profile;
- add final-check validation that profile metadata is current and compatible with the current decision/report/round;
- keep profile behavior deterministic and rule-based, not LLM-based;
- keep all prior clean-start, decision immutability, stale artifact ID, generated-artifact existence, command-plan expected-exit, report-body consistency, report-summary, and close-round checks intact;
- do not touch solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

This is an engineering-branch gate architecture task. It must not turn into reverse-solving, tool-integration, or training-dataset work.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are advisory inputs only and must not override this decision.

Previous accepted-with-limitations round:

- `decision_20260617_report_body_status_consistency_cleanup_v1`
- `round_20260617_report_body_status_consistency_cleanup_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known current state from the previous audit:

- `codex_report_summary.status` was `SUCCESS` and `acceptance_recommendation` was `ACCEPTED`.
- startup status was clean.
- preflight passed.
- pytest passed with 707 tests.
- final-check passed.
- close-round closed and archived the round.
- `report_body_consistency` passed.
- Prior report-body inconsistency was resolved enough to proceed.
- Remaining limitations were non-blocking: report prose contained a generic diagnostic caveat, and `tests/test_project_gate.py` had a large diff.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- command-plan expected-exit semantics;
- conditional close-round behavior;
- report-body consistency check;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` mismatch detection;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check;
- existing advisory `gate-profile` classifier.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this gate-profile integration.
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

- Read repository source/tests and compact `project_state/` metadata.
- Run only the gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not make `fast` or `standard` silently replace `full` for close-round.

Do not weaken final-check, close-round, preflight, decision immutability, startup/baseline, stale artifact, generated-artifact, command-plan, or report-body checks.

Do not globally allow reduced checks for all rounds.

Do not implement LLM-based profile selection.

Do not add another independent gate engine.

Do not rewrite command-plan, final-check, or close-round from scratch.

Do not expand this into frontend, GUI, solver, harness, sample runner, reverse tools, IDA/Ghidra/debugger, or training dataset work.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not modify `.codex-skills/`.

Do not add a database, queue, Kubernetes, workflow engine, or new external service.

Do not treat `task_packet.task` as current execution authority.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

Do not use this profile work to bypass close-round failures.

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
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if command-plan/report validation plumbing strictly requires it
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` is clean, later source/test dirty files must be treated as this-round changes, not inherited baseline dirty.
4. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not implement changes.
5. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not implement changes.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm existing `gate-profile` behavior before changing it.
9. Confirm command-plan currently records expected exits and close-round semantics correctly.
10. Confirm final-check currently sees report-body consistency as PASS before adding profile validation.
11. Confirm no mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if command-plan/report validation plumbing strictly requires it

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed project-state/report files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_gate_profile_tier_integration_v1/*`

Required profile semantics:

- `fast`: for report-only, artifact-only, documentation-only, or project_state-only cleanup where no source/test logic changes are present. It may generate a reduced advisory command list, but must not silently close/archive unless final-check says the selected profile is explicitly closeout-safe.
- `standard`: for ordinary non-gate Python/test changes where project_gate/project_state/close-round semantics are not modified. It may include targeted pytest plus full state/gate validation.
- `full`: for gate/project_state/command-plan/final-check/close-round changes, harness/solver/tool-runner-adjacent changes, any source/test dirty at startup, any unknown-risk profile, or any profile ambiguity. This remains the default safe path.

Required implementation behavior:

- Add a deterministic profile policy function if one does not already exist; otherwise refactor the existing classifier minimally.
- `gate-profile --json` must output at least: `profile`, `profile_reason`, `risk_reasons`, `closeout_allowed`, `required_command_kinds`, `decision_id`, `round_id`, `mainline`, and `generated_at`.
- `command-plan` must include selected profile metadata and show which commands are included because of that profile.
- If explicit profile selection is supported, invalid profile names must fail with a clear error.
- If no explicit profile is supplied, use auto-selection but default to `full` for ambiguity or any gate/project_state source change.
- `final-check` must validate that `gate_profile_plan.json` is current for the active decision/round and consistent with `command_plan.json`.
- `final-check` must fail if a non-full profile attempts close-round while `closeout_allowed` is false.
- `close-round` must keep full safety semantics by default; reduced profiles must be explicitly marked safe before archive can be created.
- Do not reduce current test coverage for the full path.
- Keep the profile implementation small and table/rule-driven.
- Preserve command-plan expected-exit semantics from prior rounds.
- Preserve report-body consistency behavior.
- Preserve startup/baseline consistency behavior.
- Preserve stale artifact ID behavior.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. auto profile defaults to `full` for `reverse_agent/project_gate.py` changes.
2. auto profile defaults to `full` for `reverse_agent/project_state.py` changes.
3. auto profile uses `fast` only for report/project_state artifact-only cleanup when no source/test logic changes are present.
4. `standard` profile is selected or allowed for ordinary non-gate Python/test changes when risk rules permit it.
5. ambiguous or unknown file changes default to `full`.
6. `gate-profile --json` includes profile metadata, reasons, command kinds, and closeout permission.
7. `command-plan --json` includes profile metadata and remains compatible with expected-exit semantics.
8. stale `gate_profile_plan.json` decision_id/round_id causes final-check FAIL.
9. mismatch between `gate_profile_plan.json` profile and `command_plan.json` profile causes final-check FAIL.
10. non-full profile with `closeout_allowed=false` cannot close/archive.
11. full profile can close/archive when all other gates pass.
12. invalid explicit profile name fails clearly.
13. existing command-plan expected-exit tests continue to pass.
14. existing report-body consistency tests continue to pass.
15. existing startup/baseline consistency tests continue to pass.
16. existing stale artifact ID tests continue to pass.
17. existing generated-artifact live-path tests continue to pass.
18. existing tmp-path dirty-state tests continue to pass.
19. existing preflight handoff and decision immutability tests continue to pass.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_gate_profile_tier_integration_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_gate_profile_tier_integration_v1`
- `round_id=round_20260617_gate_profile_tier_integration_v1`
- the final `report_id`
- all commands actually run

If preflight fails due to actual startup source/test dirty, Codex must stop after recording startup/preflight evidence and write a BLOCKED/REWORK report instead of running the remaining commands.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires replacing the existing gate system;
- implementing this requires changing solver/harness/tool-runner/debugger/sample code;
- profile semantics cannot be expressed with a small deterministic rule table;
- close-round safety would need to be weakened to make fast/standard pass;
- tests fail for reasons outside the narrow gate-profile tier integration scope.

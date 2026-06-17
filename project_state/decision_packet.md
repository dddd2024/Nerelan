```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_command_plan_expected_exit_semantics_v1",
  "round_id": "round_20260617_command_plan_expected_exit_semantics_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair command-plan expected-exit semantics so diagnostic commands, ordinary required commands, and closeout commands are modeled differently.

This is a narrow engineering rework after `decision_20260617_current_report_gate_regeneration_rework_v1`. The previous round largely fixed current report/gate artifact ID consistency. The remaining blocker is `pytest_result_exit_codes_match_command_plan`: diagnostic commands returned non-zero while command-plan still expected exit code 0 for every required command.

Required end state:

- command-plan must distinguish ordinary required commands, diagnostic gate/status commands, and closeout commands;
- diagnostic commands may allow non-zero exit codes when their purpose is to detect and report gate problems, but their findings must still be reflected in report-summary/final-check;
- ordinary required commands must still fail when they return unexpected non-zero exit codes;
- `close-round` must remain a real closeout command and must not be treated as a harmless diagnostic failure in the normal closeout path;
- `close-round` should be skipped or treated as a diagnostic failure-path fixture when final-check is already failed, rather than being included as an unconditional expected-success command;
- `pytest_result_exit_codes_match_command_plan` must use command kind/phase semantics instead of treating all command-plan entries as expected `[0]`;
- preserve startup/baseline consistency checks, stale artifact ID checks, preflight-failure handoff, decision immutability, generated-artifact existence, report-prose claim coverage, tmp-path checks, gate-profile behavior, and current-report gate regeneration behavior;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_current_report_gate_regeneration_rework_v1`
- `round_20260617_current_report_gate_regeneration_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- The current report, pytest_result, report-summary, final-check, and close-round mostly referenced the current decision/report/round.
- Startup `git status --short` was clean.
- Preflight passed.
- Pytest passed: 684 tests.
- `decision_report_match` passed.
- `report_summary_fields_match_synthesis` passed.
- `stale_artifact_ids` passed.
- `startup_baseline_consistency` passed.
- `files_changed_covers_git_diff` passed.
- `files_changed_excludes_inherited_dirty_files` passed.
- The remaining hard blocker was `pytest_result_exit_codes_match_command_plan`.
- The mismatch came from commands such as `doctor`, `lint-report`, `report-summary`, and `close-round` returning exit code 1 while command-plan expected `[0]` for every command.

Meaning:

- Startup/baseline/stale artifact/current-report ID issues are mostly resolved and should not be expanded further.
- The remaining defect is command-plan expected-exit modeling.
- Diagnostic commands that intentionally detect gate/report problems need different expected-exit semantics from ordinary commands.
- `close-round` needs conditional execution semantics: it should not be run as a successful closeout command after final-check has already failed.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` structural mismatch FAIL behavior;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check;
- gate-profile classifier behavior.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this engineering rework.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not continue expanding startup/baseline/stale artifact/current-report ID functionality beyond preserving existing checks.

Do not add another new gate subsystem.

Do not rewrite command-plan, report-summary, final-check, or close-round from scratch.

Do not weaken ordinary required command failures.

Do not make all commands globally accept `[0, 1]`.

Do not treat `close-round` exit code 1 as acceptable in the normal closeout path.

Do not call a round complete if final-check or close-round is failed/invalid.

Do not use diagnostic command failures as an excuse to write accepted/completed status.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, runtime probe, GUI/frontend, sample runner, raw sample, or `.codex-skills/` files.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not change training sample statuses.

Do not add a database, queue system, workflow engine, or new external dependency.

Do not treat `task_packet.task` as current execution authority.

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

- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if pytest_result/status validation plumbing strictly requires it
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
8. Confirm the previous `pytest_result_exit_codes_match_command_plan` blocker before changing code.
9. Confirm which command categories are ordinary required, diagnostic, and closeout.
10. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if pytest_result/status validation strictly requires it

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_command_plan_expected_exit_semantics_v1/*`

Required implementation behavior:

- Extend command-plan entries with clear command semantics, such as `kind` / `phase` values for ordinary status commands, preflight, tests, diagnostic commands, gate checks, and closeout commands.
- Keep ordinary required commands expected to exit `[0]`.
- Treat `doctor`, `lint-report`, `report-summary`, and `final-check` as diagnostic or gate-diagnostic commands when they are used to inspect/report state. These commands may allow `[0, 1]` only when non-zero output is expected to be captured in report/final gate rather than treated as an execution mismatch.
- Do not silently ignore diagnostic command failures: their failures must remain visible in pytest_result/report/final gate, and the report must remain `PARTIAL`/`FAILED` with `REWORK_REQUIRED` unless final-check and closeout pass.
- Treat `close-round` as a closeout command. In normal closeout path it must expect exit `[0]`.
- Add conditional close-round semantics: `close-round` should be executed only if final-check has passed, unless the command is explicitly part of a test fixture validating failure behavior.
- If final-check fails, close-round should be skipped in the normal manual command plan and the report should remain `REWORK_REQUIRED` or `BLOCKED`.
- Update `pytest_result_exit_codes_match_command_plan` so it validates exit codes according to command kind and conditional execution semantics.
- Ensure command-plan JSON records enough metadata for final-check to decide whether a non-zero command exit is allowed, diagnostic, or blocking.
- Ensure ordinary command exit 1 still fails the check.
- Ensure close-round exit 1 still fails in closeout mode.
- Preserve startup/baseline consistency behavior from prior rounds.
- Preserve stale artifact ID behavior from prior rounds.
- Preserve current-report gate regeneration behavior from prior rounds.
- Preserve preflight-failure handoff behavior.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve gate-profile classifier behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. diagnostic command exit 1 does not trigger `pytest_result_exit_codes_match_command_plan` mismatch when command-plan explicitly allows diagnostic `[0, 1]`.
2. diagnostic command exit 1 remains visible in report/final gate and does not produce accepted/completed status.
3. ordinary required command exit 1 still triggers `pytest_result_exit_codes_match_command_plan` FAIL.
4. final-check failed causes normal close-round command to be skipped or marked not applicable, not executed as expected-success closeout.
5. final-check passed allows close-round expected exit `[0]`.
6. close-round exit 1 in closeout mode still blocks.
7. command-plan JSON records command kind/phase/expected_exit_codes sufficient for final-check validation.
8. current round final-check/close-round no longer fails solely because diagnostic commands returned exit 1.
9. Existing startup/baseline consistency tests continue to pass.
10. Existing stale artifact ID tests continue to pass.
11. Existing current-report regeneration tests continue to pass.
12. Existing preflight-failure handoff tests continue to pass.
13. Existing execution-authority hard-stop tests continue to pass.
14. Existing generated-artifact live-path tests continue to pass.
15. Existing report prose claim coverage tests continue to pass.
16. Existing tmp-path dirty-state tests continue to pass.
17. Existing gate-profile tests continue to pass.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_command_plan_expected_exit_semantics_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_command_plan_expected_exit_semantics_v1`
- `round_id=round_20260617_command_plan_expected_exit_semantics_v1`
- the final `report_id`
- all commands actually run

If final-check fails, Codex should not run `close-round` as a normal expected-success closeout command. Record the skip or diagnostic reason instead and report `REWORK_REQUIRED`.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- command kind/phase semantics cannot distinguish diagnostic commands from closeout commands without broad refactoring;
- tests fail for reasons outside the narrow command-plan expected-exit semantics scope.

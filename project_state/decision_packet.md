```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_current_report_gate_regeneration_rework_v1",
  "round_id": "round_20260617_current_report_gate_regeneration_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the current-report gate regeneration order so `codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `final_gate_result.json`, `round_delta_summary.json`, and close-round all refer to the same current decision/report/round.

This is a narrow engineering rework after `decision_20260617_preflight_startup_status_consistency_rework_v1`. Do not add new broad gate features. The immediate failure is that live `codex_execution_report.md` was updated to the current round, but later gate artifacts and command outputs still used or reported stale prior-round report IDs.

Required end state:

- report-summary must read the current live `project_state/codex_execution_report.md`, not a stale archived or cached report;
- final-check output must contain the current `decision_id`, current live `report_id`, and current `round_id`;
- close-round must compare the requested round_id against the current decision/report, not against stale prior-round artifacts;
- stale `report_summary_synthesis.json`, `final_gate_result.json`, `command_plan.json`, and `round_delta_summary.json` must be regenerated or rejected before they are used as current evidence;
- if close-round fails, the report must remain `PARTIAL`/`FAILED` with `REWORK_REQUIRED` or `BLOCKED`; do not package close-round failure as completion;
- preserve startup/baseline consistency checks, stale artifact ID checks, preflight-failure handoff, decision immutability, generated-artifact existence, report-prose claim coverage, tmp-path checks, and gate-profile behavior;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_preflight_startup_status_consistency_rework_v1`
- `round_20260617_preflight_startup_status_consistency_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- The live `codex_execution_report.md` was updated to the current round and used `status=PARTIAL` plus `acceptance_recommendation=REWORK_REQUIRED`.
- The startup `git status --short` in `pytest_result.txt` was clean, and preflight passed.
- The implementation added useful checks for startup/baseline consistency and stale artifact IDs.
- However, `doctor`, `lint-report`, `report-summary`, `final-check`, and `close-round` output still referenced `codex_report_20260617_preflight_failure_handoff_rework_v1` / `round_20260617_preflight_failure_handoff_rework_v1` while the live report was `codex_report_20260617_preflight_startup_status_consistency_rework_v1`.
- `final_gate_result.json` and close-round were therefore not current evidence for the active report.
- close-round failed with report/decision mismatch, command-plan mismatch, pytest exit-code mismatch, files_changed coverage mismatch, startup/baseline consistency mismatch, and report-summary mismatch.
- The screenshot claim that close-round failed only because diagnostic commands naturally return non-zero is insufficient; the actual failure includes stale/mismatched report and gate artifacts.

Meaning:

- The code checks are moving in the right direction.
- The remaining defect is regeneration/order-of-operations: after the live report is written, report-summary/final-check/close-round must be regenerated against that live report and current round.
- Stale gate artifacts must not be used to claim completion or limitation.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
- startup/baseline consistency check;
- stale artifact ID check;
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

Do not continue expanding generated-artifact functionality beyond preserving existing checks.

Do not add another new gate subsystem.

Do not rewrite clean-start guard, report-summary, final-check, or close-round from scratch.

Do not weaken existing hard-stop gates.

Do not use stale `final_gate_result.json`, stale `report_summary_synthesis.json`, stale `command_plan.json`, stale `round_delta_summary.json`, or stale `preflight_result.json` as current evidence.

Do not use archived prior-round reports as the live report for current report-summary/final-check/close-round.

Do not call a round complete if final-check or close-round is failed/invalid.

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

- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` if present
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/status plumbing strictly requires it
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
8. Confirm the previous stale live-report/gate-artifact regeneration defect before changing code.
9. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/status plumbing strictly requires it

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
- `project_state/rounds/round_20260617_current_report_gate_regeneration_rework_v1/*`

Required implementation behavior:

- Ensure report-summary reads the current live `project_state/codex_execution_report.md` after it is written.
- Ensure final-check reads the current live report and emits the current `report_id`, `decision_id`, and `round_id`.
- Ensure close-round uses the current live report for report/decision/round comparisons.
- Ensure stale gate artifacts are regenerated or rejected before they can influence current final-check/close-round output.
- Ensure `report_summary_synthesis.json` generated for current round contains current `report_id`, current `round_id`, and current `based_on_decision_id`.
- Ensure `final_gate_result.json` generated for current round contains current `decision_id`, current live `report_id`, and current `round_id`.
- Ensure `command_plan.json` generated for current round contains current `decision_id` and current `round_id`.
- Ensure `round_delta_summary.json` and `round_baseline.json` are current-round artifacts or are clearly rejected as stale.
- If close-round fails, report status/recommendation must remain non-success and non-accepted.
- If diagnostic commands are expected to fail during a blocked/diagnostic path, command-plan must model expected exit codes explicitly; otherwise final-check must treat non-zero exit codes as real failures.
- Preserve startup/baseline consistency behavior from the previous round.
- Preserve stale artifact ID check behavior from the previous round.
- Preserve preflight-failure handoff behavior.
- Preserve `pytest_result_summary.status` exit-code consistency behavior.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve gate-profile classifier behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. After current live report is written, report-summary reads that current report, not a prior report.
2. final-check output `report_id` and `round_id` match the current live report.
3. close-round requested round_id compares against the current decision/report/round.
4. stale `report_summary_synthesis.json` cannot satisfy current final-check.
5. stale `final_gate_result.json` cannot be treated as current success evidence.
6. stale `command_plan.json` cannot satisfy current command-plan checks.
7. close-round failed/invalid prevents accepted/completed report status.
8. command-plan expected exit code mismatch remains a blocking failure unless explicitly modeled by the current command-plan.
9. Current report `PARTIAL/REWORK_REQUIRED` is not misread as accepted completion.
10. Existing startup/baseline consistency tests continue to pass.
11. Existing stale artifact ID tests continue to pass.
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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_current_report_gate_regeneration_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_current_report_gate_regeneration_rework_v1`
- `round_id=round_20260617_current_report_gate_regeneration_rework_v1`
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
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- current report and current gate artifacts cannot be made to reference the same decision/report/round without broad refactoring;
- tests fail for reasons outside the narrow current-report gate regeneration scope.

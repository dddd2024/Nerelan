```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_report_body_status_consistency_cleanup_v1",
  "round_id": "round_20260617_report_body_status_consistency_cleanup_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Clean up report body/status consistency after the accepted-with-limitations `decision_20260617_command_plan_expected_exit_semantics_v1` round.

This is a narrow engineering/documentation cleanup. Do not continue expanding command-plan, gate-profile, startup/baseline, stale artifact, generated-artifact, solver, harness, or reverse-tool functionality.

Required end state:

- `project_state/codex_execution_report.md` body status text must not contradict `codex_report_summary.status` or `codex_report_summary.acceptance_recommendation`;
- if `codex_report_summary.status=SUCCESS` and `acceptance_recommendation=ACCEPTED`, the body must not say `PARTIAL`, `REWORK_REQUIRED`, `close-round still fails`, or `previous round's report is still the live report`;
- if final gate and close-round are archived/passed, the report body must reflect that state;
- add or harden a lightweight report-body consistency check so obvious status contradictions are caught by `report-summary` or `final-check` in future rounds;
- keep all prior gate-tiering, command-plan expected-exit, startup/baseline, stale artifact ID, generated-artifact existence, report-prose claim, tmp-path, and gate-profile behavior intact;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round accepted with limitations:

- `decision_20260617_command_plan_expected_exit_semantics_v1`
- `round_20260617_command_plan_expected_exit_semantics_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Observed facts from the previous audit:

- `command-plan` expected-exit semantics were implemented.
- Diagnostic commands such as `doctor`, `lint-report`, `report-summary`, and `final-check` are now modeled with diagnostic expected-exit semantics.
- `pytest_result_exit_codes_match_command_plan` passed.
- startup/preflight/baseline checks passed.
- stale artifact ID checks passed.
- final gate passed.
- close-round ultimately archived the round successfully.
- However, the report body still contained stale text saying `PARTIAL` and claiming previous-round report/close-round failures even though the structured JSON summary said `SUCCESS`/`ACCEPTED` and the final gate/close-round had passed.

Meaning:

- This is no longer a gate architecture defect.
- The remaining defect is report readability/trust: prose status must not contradict structured status.
- The next step should be a small cleanup, not another broad gate redesign.

Existing useful behavior to preserve:

- fast/standard/full advisory `gate-profile` classifier;
- command-plan expected-exit semantics;
- conditional close-round behavior;
- startup/baseline consistency check;
- stale artifact ID check;
- current-report gate regeneration behavior;
- preflight-failure handoff check;
- `decision_immutability` FAIL behavior;
- inherited source/test dirty FAIL behavior;
- `report_summary_fields_match_synthesis` structural mismatch FAIL behavior;
- generated-artifact live-path existence behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state check.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this cleanup.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run only the gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not continue expanding command-plan expected-exit semantics.

Do not continue expanding startup/baseline/stale artifact/current-report ID functionality.

Do not add another new gate subsystem.

Do not rewrite command-plan, report-summary, final-check, or close-round from scratch.

Do not weaken ordinary required command failures.

Do not change close-round semantics except where needed to test report-body consistency.

Do not call a round complete if final-check or close-round is failed/invalid.

Do not use report-body cleanup as an excuse to change solver, harness, reverse-tool, sample, or GUI behavior.

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

- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report-body validation plumbing strictly requires it
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
8. Confirm the previous report-body/status contradiction before changing code or report text.
9. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report-body consistency validation strictly requires it

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
- `project_state/rounds/round_20260617_report_body_status_consistency_cleanup_v1/*`

Required implementation behavior:

- Correct the live `project_state/codex_execution_report.md` body so its `## Status`, `Remaining Limitations`, and key verification text agree with `codex_report_summary`.
- If structured summary says `SUCCESS` and `ACCEPTED`, body text must not claim partial completion, rework required, stale live report, or close-round failure.
- Add or harden a report body consistency check that detects obvious contradictions between body status prose and JSON summary status/recommendation.
- The check should flag examples such as:
  - JSON `SUCCESS` but body status begins with `PARTIAL` or `FAILED`;
  - JSON `ACCEPTED` but body says `REWORK_REQUIRED`, `BLOCKED`, or `close-round still fails`;
  - JSON success plus body claims previous-round report is still live.
- Keep the check narrow and heuristic; do not build an NLP subsystem.
- Ensure report-summary/final-check include the new check or equivalent validation.
- Preserve command-plan expected-exit semantics from the previous round.
- Preserve startup/baseline consistency behavior from prior rounds.
- Preserve stale artifact ID behavior from prior rounds.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve gate-profile classifier behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. JSON summary `SUCCESS` plus body `PARTIAL` causes report-body consistency FAIL.
2. JSON summary `ACCEPTED` plus body `REWORK_REQUIRED` or `BLOCKED` causes FAIL.
3. JSON success plus body `close-round still fails` causes FAIL.
4. JSON success plus body `previous round's report is still the live report` causes FAIL.
5. Matching JSON success and body success passes.
6. Matching JSON partial/rework body passes when the summary is genuinely `PARTIAL` / `REWORK_REQUIRED`.
7. Existing command-plan expected-exit tests continue to pass.
8. Existing startup/baseline consistency tests continue to pass.
9. Existing stale artifact ID tests continue to pass.
10. Existing current-report regeneration tests continue to pass.
11. Existing preflight-failure handoff tests continue to pass.
12. Existing generated-artifact live-path tests continue to pass.
13. Existing report prose claim coverage tests continue to pass.
14. Existing tmp-path dirty-state tests continue to pass.
15. Existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_report_body_status_consistency_cleanup_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_report_body_status_consistency_cleanup_v1`
- `round_id=round_20260617_report_body_status_consistency_cleanup_v1`
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
- implementing this requires rewriting command-plan, close-round, or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- report-body consistency cannot be checked without broad refactoring or NLP-style analysis;
- tests fail for reasons outside the narrow report-body status consistency cleanup scope.

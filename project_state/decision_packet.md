```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_preflight_failure_handoff_rework_v1",
  "round_id": "round_20260617_preflight_failure_handoff_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair preflight-failure handoff and report-status handling so a hard-stop preflight failure cannot be packaged as `COMPLETED_WITH_LIMITATIONS` or `ACCEPTED_WITH_LIMITATIONS`.

This is a narrow engineering rework after `decision_20260617_execution_authority_hard_stop_rework_v1`. The previous round successfully made `source_test_clean_start` fail when startup source/test files were dirty, but Codex continued running later commands and wrote an acceptance recommendation even though the round was blocked.

Required end state:

- if preflight exits non-zero, Codex must stop the implementation flow and write a BLOCKED/REWORK report;
- preflight hard-stop failures must not be represented as completed or accepted with limitations;
- `pytest_result_summary.status` must not be `PASSED` when any required command block exits non-zero;
- command-plan/run-round/final-check/close-round consistency checks must treat preflight failure as a blocking handoff state, not a successful closeout path;
- `codex_report_summary.status` must use accepted status vocabulary already supported by lint/final-check;
- do not continue expanding generated-artifact behavior;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_execution_authority_hard_stop_rework_v1`
- `round_20260617_execution_authority_hard_stop_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- Startup `git status --short` showed source/test dirty files:
  - `reverse_agent/project_gate.py`
  - `tests/test_project_gate.py`
- `preflight` correctly returned FAILED with `source_test_clean_start` FAIL.
- `run-round --dry-run --json` correctly returned FAILED because preflight failed.
- doctor, lint-report, report-summary, final-check, and close-round also failed or reported blocking findings.
- `final_gate_result.json` had `gate_status=FAILED` and multiple blocking reasons.
- Despite that, `codex_report_summary.status` was `COMPLETED_WITH_LIMITATIONS` and `acceptance_recommendation` was `ACCEPTED_WITH_LIMITATIONS`.
- `pytest_result_summary.status` was `PASSED` even though recorded command blocks included exit code 1.
- final gate caught `pytest_result_match`, `pytest_result_exit_codes_match_command_plan`, `report_summary_fields_match_synthesis`, and `status_policy_valid` failures.

Meaning:

- The hard-stop checks started working.
- The remaining defect is handoff/reporting semantics after a hard-stop: a blocked round must stop and report BLOCKED/REWORK, not continue to a pseudo-success state.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
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

Do not continue expanding generated-artifact functionality.

Do not rewrite clean-start guard, report-summary, final-check, or close-round from scratch.

Do not weaken existing hard-stop gates.

Do not convert preflight failure into `COMPLETED_WITH_LIMITATIONS`.

Do not set `acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS` when preflight failed.

Do not set `pytest_result_summary.status=PASSED` when any required command block exits non-zero.

Do not run close-round after preflight hard-stop except in a test fixture that explicitly validates failure behavior.

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
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
3. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not implement changes.
4. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not implement changes.
5. If startup `git status --short` shows `tmp*/` or other temporary files/directories, remove them if safe; otherwise stop and report BLOCKED.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm the previous preflight-failure handoff defect before changing code.
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
- `project_state/rounds/round_20260617_preflight_failure_handoff_rework_v1/*`

Required implementation behavior:

- Add or harden a preflight-failure handoff policy: after preflight exits non-zero, the round must be marked BLOCKED/FAILED/REWORK_REQUIRED and no success/accepted recommendation may be emitted.
- Ensure `codex_report_summary.status` uses a valid supported status such as `BLOCKED`, `FAILED`, or another already-accepted non-success status; do not use unsupported `COMPLETED_WITH_LIMITATIONS`.
- Ensure `acceptance_recommendation` is `REWORK_REQUIRED` or `BLOCKED`, not accepted, when preflight failed.
- Ensure `pytest_result_summary.status` reflects command-block failures; if any required command block exits non-zero, status must not be `PASSED`.
- Ensure final-check fails if `pytest_result_summary.status=PASSED` but required command blocks contain non-zero exit codes.
- Ensure final-check fails if report status/recommendation claims accepted while preflight or run-round has failed.
- Ensure command-plan expected exit-code comparisons remain strict for normal closeout, while test fixtures can explicitly validate failed preflight paths.
- Preserve `source_test_clean_start`, `decision_immutability`, inherited source/test dirty, `report_summary_fields_match_synthesis`, generated-artifact existence, report-prose claim, tmp-path, and gate-profile behavior from prior rounds.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. preflight failed -> report summary status cannot be accepted/completed.
2. preflight failed -> acceptance recommendation must be `REWORK_REQUIRED` or `BLOCKED`.
3. command block exit 1 -> `pytest_result_summary.status` cannot be `PASSED`.
4. `pytest_result_summary.status=PASSED` plus command block exit 1 -> final-check FAIL.
5. preflight failed plus close-round attempted -> final-check or close-round FAIL.
6. unsupported report status such as `COMPLETED_WITH_LIMITATIONS` causes lint/final-check FAIL.
7. existing execution-authority hard-stop tests continue to pass.
8. existing generated-artifact live-path tests continue to pass.
9. existing report prose claim coverage tests continue to pass.
10. existing tmp-path dirty-state tests continue to pass.
11. existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_preflight_failure_handoff_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_preflight_failure_handoff_rework_v1`
- `round_id=round_20260617_preflight_failure_handoff_rework_v1`
- the final `report_id`
- all commands actually run

If preflight fails due to existing source/test dirty, Codex must stop after recording startup/preflight evidence and write a BLOCKED/REWORK report instead of running the remaining commands.

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- preflight failure cannot be represented as BLOCKED/REWORK without broad refactoring;
- tests fail for reasons outside the narrow preflight-failure handoff scope.

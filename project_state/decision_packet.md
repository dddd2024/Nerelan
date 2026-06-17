```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_preflight_startup_status_consistency_rework_v1",
  "round_id": "round_20260617_preflight_startup_status_consistency_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair startup-status, preflight-baseline, and current-round final-gate consistency so a clean startup cannot later be misreported as inherited source/test dirty, and stale gate artifacts cannot be used as current evidence.

This is the actual engineering rework after `decision_20260617_preflight_failure_handoff_rework_v1`. Do not change the external Codex prompt in this round; use the corrected prompt externally, but this decision is for repository behavior and state consistency.

Required end state:

- if the trusted startup `git status --short` shows source/test dirty, preflight and final-check must treat it as hard-stop evidence;
- if trusted startup `git status --short` is clean, later source/test dirty files must be treated as this-round modifications, not inherited baseline dirty;
- preflight must not report `source_test_clean_start: PASS` when trusted startup evidence shows source/test dirty;
- final-check must fail if `preflight_result.json`, `report_summary_synthesis.json`, or `final_gate_result.json` references a stale report_id / round_id rather than the current decision/report;
- final-check must fail if live `final_gate_result.json` is stale or mismatched and must not use it as current success evidence;
- keep preflight-failure handoff, decision immutability, generated-artifact existence, report-prose claim coverage, and tmp-path checks intact;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_preflight_failure_handoff_rework_v1`
- `round_20260617_preflight_failure_handoff_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- The current report improved status semantics by using `status=PARTIAL` and `acceptance_recommendation=REWORK_REQUIRED`, instead of `COMPLETED_WITH_LIMITATIONS` / accepted.
- The user also showed a clean startup example where `git status --short` was empty at the true beginning of execution.
- However, later recorded `pytest_result.txt` showed source/test files dirty in the startup command block, while preflight still reported `source_test_clean_start: PASS`.
- This means startup evidence and preflight baseline were inconsistent.
- `final_gate_result.json` also referenced stale IDs from `round_20260617_execution_authority_hard_stop_rework_v1` while the live report was for `round_20260617_preflight_failure_handoff_rework_v1`.
- Therefore final-check evidence was not current for the active report/round.
- Gate output still had report/decision mismatch, pytest_result mismatch, command-plan mismatch, report-summary mismatch, and stale final gate evidence.

Meaning:

- The report-status vocabulary issue moved in the right direction.
- The remaining defect is state provenance: startup `git status`, baseline capture/reuse, preflight_result, report_summary_synthesis, and final_gate_result must all agree on the current decision/report/round.
- A stale final gate or stale report-summary artifact must never be treated as current evidence.

Existing useful behavior to preserve:

- `source_test_clean_start` hard stop;
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

Do not modify the external Codex prompt in this repository during this round.

Do not continue expanding generated-artifact functionality.

Do not rewrite clean-start guard, report-summary, final-check, or close-round from scratch.

Do not weaken existing hard-stop gates.

Do not convert preflight failure into accepted/completed status.

Do not use stale `final_gate_result.json`, stale `report_summary_synthesis.json`, or stale `preflight_result.json` as current evidence.

Do not run close-round after a hard-stop except in a test fixture explicitly validating failure behavior.

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
- `reverse_agent/project_state.py` only if status/baseline parsing support strictly requires it
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. Record whether startup status is truly clean or has baseline dirty files.
4. If startup `git status --short` is clean, later source/test dirty files must be treated as this-round changes, not inherited baseline dirty.
5. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED` or `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`; do not implement changes.
6. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write a BLOCKED report; do not implement changes.
7. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
8. Current decision controls execution; `task_packet.json` is not authoritative.
9. Confirm the previous startup/preflight/final-gate ID mismatch before changing code.
10. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if startup-status parsing or pytest_result validation strictly requires it

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
- `project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/*`

Required implementation behavior:

- Parse trusted startup `git status --short` from `pytest_result.txt` command blocks when available.
- If trusted startup status shows source/test dirty, preflight/final-check must not report clean-start PASS unless there is an explicit pre-existing decision allowlist and no live decision mutation.
- If trusted startup status is clean, baseline summaries must not later classify implementation source/test changes as inherited dirty.
- If startup status and `round_baseline.json` disagree on source/test dirty state, final-check must FAIL with a clear startup/baseline consistency error.
- Ensure `preflight_result.json`, `report_summary_synthesis.json`, `command_plan.json`, and `final_gate_result.json` carry current `decision_id`, `report_id` where applicable, and `round_id`.
- Ensure final-check fails if any of those artifacts are stale or reference another round/report.
- Ensure report-summary/final-check regenerate current-round synthesis/final result rather than using stale previous-round IDs.
- Ensure final gate cannot use a stale `final_gate_result.json` as current success evidence.
- Preserve preflight-failure handoff behavior from the previous round.
- Preserve `pytest_result_summary.status` exit-code consistency behavior.
- Preserve generated-artifact live-path existence behavior.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve gate-profile classifier behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. startup `git status --short` clean, later source/test files dirty: final-check treats them as this-round changes, not inherited dirty.
2. startup `git status --short` shows source/test dirty, baseline missing or clean: preflight/final-check FAIL.
3. startup status and `round_baseline.json` conflict on source/test dirty: final-check FAIL.
4. `preflight_result.json` with stale `round_id`: final-check FAIL.
5. `report_summary_synthesis.json` with stale `report_id` or `round_id`: final-check FAIL.
6. `final_gate_result.json` with stale `report_id` or `round_id`: final-check FAIL.
7. final-check generated for current round must contain current `decision_id`, current `report_id`, and current `round_id`.
8. Current report `PARTIAL/REWORK_REQUIRED` must not be misread as accepted completion.
9. Existing preflight-failure handoff tests continue to pass.
10. Existing execution-authority hard-stop tests continue to pass.
11. Existing generated-artifact live-path tests continue to pass.
12. Existing report prose claim coverage tests continue to pass.
13. Existing tmp-path dirty-state tests continue to pass.
14. Existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_preflight_startup_status_consistency_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_preflight_startup_status_consistency_rework_v1`
- `round_id=round_20260617_preflight_startup_status_consistency_rework_v1`
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
- startup status, baseline state, and current-round gate artifact IDs cannot be reconciled without broad refactoring;
- tests fail for reasons outside the narrow startup/preflight/final-gate consistency scope.

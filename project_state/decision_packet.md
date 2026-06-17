```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_execution_authority_hard_stop_rework_v1",
  "round_id": "round_20260617_execution_authority_hard_stop_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Harden execution-authority and startup-cleanliness gates so two conditions become hard failures instead of warnings:

1. live `project_state/decision_packet.md` is modified during the current round;
2. startup `git status --short` shows source/test dirty files before implementation begins.

This is a narrow rework after `decision_20260617_generated_artifact_existence_rework_v1`. Do not continue expanding generated-artifact behavior in this round. The immediate problem is that the previous round continued after startup source/test dirty and modified the live decision packet during execution, while final gate only produced WARN-level findings.

Required end state:

- `decision_immutability` must FAIL when live `project_state/decision_packet.md` appears in `files_changed`, `new_dirty_files_since_baseline`, or baseline dirty files for the active round;
- startup source/test dirty must make preflight BLOCKED/FAILED unless the decision had a trusted pre-existing allowlist before execution and the live decision was not modified during execution;
- `files_changed_excludes_inherited_dirty_files` must FAIL for inherited source/test dirty files unless there is trusted startup evidence and a pre-existing decision allowlist, with no live decision mutation;
- `report_summary_fields_match_synthesis` must FAIL for status, acceptance, `files_changed`, or `generated_artifacts` mismatches;
- existing generated-artifact existence work should be preserved but not expanded;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_generated_artifact_existence_rework_v1`
- `round_20260617_generated_artifact_existence_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- `project_state/gates/run_round_result.json` was restored as a live generated artifact and `generated_artifact_live_paths_exist` passed.
- Tests passed: `634 passed in 40.13s`.
- However, startup `git status --short` already showed source/test dirty files:
  - `reverse_agent/project_gate.py`
  - `tests/test_project_gate.py`
- The decision for that round required immediate stop when startup source/test dirty was present, but Codex continued implementation, final-check, and close-round.
- live `project_state/decision_packet.md` appeared in `files_changed` and new dirty files during execution.
- `decision_immutability` was WARN instead of FAIL.
- inherited source/test dirty was WARN instead of FAIL.
- `report_summary_fields_match_synthesis` was WARN despite status/acceptance mismatch.
- The report itself was `status=FAILED` and `acceptance_recommendation=REWORK_REQUIRED`.

Meaning:

- Generated-artifact existence moved in the right direction.
- The remaining blocking issue is execution-authority enforcement: Codex must not continue after dirty-start source/test evidence, and must not mutate its active task authority during execution.
- Warnings are insufficient for these conditions.

Existing useful behavior to preserve:

- clean-start baseline guard logic;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state blocking behavior;
- generated-artifact live-path existence checks;
- gate-profile classifier behavior;
- current command-plan/final-check/close-round flow.

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

Do not continue expanding generated-artifact functionality beyond preserving the previous existence check behavior.

Do not rewrite clean-start guard, report-summary, final-check, or close-round from scratch.

Do not weaken existing gate, report-summary, final-check, or close-round checks.

Do not modify live `project_state/decision_packet.md` during execution to add a late allowlist or change the active task.

Do not let `Allowed Inherited Dirty Baseline Files` added during execution authorize source/test dirty files that were already dirty at startup.

Do not downgrade execution-authority violations to warnings.

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
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
3. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED`; do not implement changes.
4. If startup `git status --short` shows live `project_state/decision_packet.md` dirty, stop immediately and write `codex_execution_report.md` with `status=BLOCKED`; do not implement changes.
5. If startup `git status --short` shows `tmp*/` or other temporary files/directories, remove them if safe; otherwise stop and report `BLOCKED`.
6. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
7. Current decision controls execution; `task_packet.json` is not authoritative.
8. Confirm the previous WARN-level execution-authority violations before changing code.
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
- `project_state/rounds/round_20260617_execution_authority_hard_stop_rework_v1/*`

Required implementation behavior:

- Make `decision_immutability` a FAIL, not WARN, whenever live `project_state/decision_packet.md` appears in `files_changed`, `new_dirty_files_since_baseline`, or baseline dirty files.
- Make preflight fail/block when startup source/test dirty files are present without a trusted pre-existing allowlist captured before execution.
- A trusted inherited source/test allowlist must come from the active decision as read at startup; it must not be introduced by modifying live `decision_packet.md` during execution.
- Make `files_changed_excludes_inherited_dirty_files` FAIL for inherited source/test dirty files unless all of the following are true:
  - startup evidence confirms the files were pre-existing dirty files;
  - the active decision had an explicit allowlist before execution;
  - live `project_state/decision_packet.md` was not modified during execution.
- Make `report_summary_fields_match_synthesis` FAIL for mismatches in `status`, `acceptance_recommendation`, `files_changed`, or `generated_artifacts`.
- Preserve generated-artifact live-path existence behavior from the previous round.
- Preserve report-prose claimed source/test coverage behavior.
- Preserve `tmp*/` dirty-state check behavior.
- Preserve gate-profile classifier behavior.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. live `project_state/decision_packet.md` in `files_changed` causes `decision_immutability` FAIL.
2. live `project_state/decision_packet.md` in `new_dirty_files_since_baseline` causes `decision_immutability` FAIL.
3. live `project_state/decision_packet.md` in baseline dirty files causes preflight or final-check FAIL.
4. startup source/test dirty without trusted pre-existing allowlist causes preflight BLOCKED/FAILED.
5. late-added allowlist in live decision cannot authorize source/test dirty files if live decision changed during execution.
6. inherited source/test dirty in `files_changed` causes FAIL unless trusted startup evidence and pre-existing allowlist both exist.
7. `report_summary_fields_match_synthesis` status/acceptance mismatch causes FAIL.
8. `report_summary_fields_match_synthesis` `files_changed` mismatch causes FAIL.
9. `report_summary_fields_match_synthesis` `generated_artifacts` mismatch causes FAIL.
10. Existing generated-artifact live-path tests continue to pass.
11. Existing report prose claim coverage tests continue to pass.
12. Existing tmp-path dirty-state tests continue to pass.
13. Existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_execution_authority_hard_stop_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_execution_authority_hard_stop_rework_v1`
- `round_id=round_20260617_execution_authority_hard_stop_rework_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- startup `git status --short` already shows live `project_state/decision_packet.md` dirty;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- execution-authority violations cannot be raised from WARN to FAIL without broad refactoring;
- tests fail for reasons outside the narrow execution-authority hard-stop scope.

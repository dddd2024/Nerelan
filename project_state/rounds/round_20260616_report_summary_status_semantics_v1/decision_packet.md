```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_report_summary_status_semantics_v1",
  "round_id": "round_20260616_report_summary_status_semantics_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the report-summary status semantics ambiguity found during audit of `round_20260616_gate_baseline_lifecycle_closeout_rework_v1`.

This is an `engineering_branch` gate semantics round. Do not continue reverse solving, do not rerun CPP1, and do not regenerate sample evidence.

Required end state:

- `python -m reverse_agent.project_gate report-summary --state-dir project_state` has CLI output and JSON status semantics that agree;
- `project_state/gates/report_summary_synthesis.json` no longer reports `synthesis_status=WARN` when there are no `errors` and no `diffs` and the only warnings are explicitly non-blocking inherited-dirty / external-state notices;
- `report_summary_fields_match_synthesis` remains PASS;
- `baseline_lifecycle_guard` remains strict for unauthorized source/test dirty files;
- `final-check` exits 0;
- `close-round` exits 0 and archives `round_20260616_report_summary_status_semantics_v1`;
- current CPP1 artifacts, especially `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, remain unchanged.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous reviewed round:

- `decision_20260616_gate_baseline_lifecycle_closeout_rework_v1`
- `round_20260616_gate_baseline_lifecycle_closeout_rework_v1`
- mainline: `engineering_branch`
- audit conclusion: `ACCEPTED_WITH_LIMITATIONS`

Known facts from audit:

- `codex_execution_report.md` reports `SUCCESS` and `acceptance_recommendation=ACCEPTED` for the previous round.
- `pytest_result.txt` recorded all required commands and `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q` passed with 578 tests.
- `report-summary` CLI output was `PASSED`.
- `final-check` was `PASSED`.
- `close-round` was `CLOSED` with exit 0 and archive created.
- `project_state/gates/report_summary_synthesis.json` still recorded `synthesis_status=WARN` because of an inherited dirty warning even though `diffs=[]` and `errors=[]`.
- This creates a status-language mismatch: the gate behavior is acceptable, but the artifact field is ambiguous for future audit.
- Historical missing sample artifacts remain external state notices, not blockers for this engineering gate round.
- `project_state/artifact_index.json` still contains current CPP1 evidence, including `local_reverse_cpp1_2f6fcb63_success_target_reanchor` with freshness `current`; this round must not alter its meaning.

Existing relevant capabilities:

- `reverse_agent/project_gate.py` already implements `report-summary`, `final-check`, `close-round`, `command-plan`, baseline lifecycle checks, close snapshot checks, round archive checks, and report synthesis.
- `tests/test_project_gate.py` already contains focused tests for report synthesis, baseline lifecycle, close snapshot behavior, command-plan extraction, and close-round behavior.
- This round does not require IDA, Ghidra, debugger, runtime probe, solver, harness execution, GUI/frontend work, or sample metadata changes.

## 3. Do Not Do

Do not rerun CPP1 or any local reverse sample.

Do not generate candidate material.

Do not modify solver logic, sample runners, IDA runner semantics, debugger/emulator/probe code, `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not manually patch `report_summary_synthesis.json`, `final_gate_result.json`, or other gate files to hide failures.

Do not weaken decision/report/pytest/round id matching.

Do not weaken artifact freshness policy.

Do not make all report-summary warnings non-blocking.

Do not suppress real `errors`, real `diffs`, missing command-plan, missing round baseline, report/decision mismatch, pytest mismatch, unauthorized dirty source/test files, or forbidden path violations.

Do not remove historical missing artifact entries just to pass gates.

## 4. Files To Inspect

Read the default project_state files in order:

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
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`, read-only verification only

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. The previous round passed final-check and close-round but left `report_summary_synthesis.json` with `synthesis_status=WARN` and no `errors` / `diffs`.
4. The warning source is non-blocking inherited-dirty or external-state notice, not a real report-summary mismatch.
5. `report_summary_fields_match_synthesis` currently passes and must continue to pass.
6. `baseline_lifecycle_guard` currently passes and must continue to block unauthorized source/test dirty files.
7. Current CPP1 artifacts remain current and are not modified.

Required result:

- Define a precise status policy for report-summary synthesis artifacts.
- If `errors` or `diffs` are present, `synthesis_status` must remain `FAILED` or equivalent blocking status.
- If warnings are only recognized non-blocking warnings, choose one consistent representation and test it. Preferred representation: `synthesis_status=PASSED` plus a separate `warnings` list and/or `non_blocking_warnings` / `external_state_notices` field.
- If warnings are not recognized as non-blocking, status must remain `WARN` and final-check must not silently turn it into full acceptance.
- CLI output, JSON artifact, final-check interpretation, and tests must agree.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- directly related tests, preferably `tests/test_project_gate.py`

Allowed state updates generated by commands:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_report_summary_status_semantics_v1/*`

Do not modify:

- `project_state/local_reverse_cpp1_2f6fcb63_success_target_reanchor.json`
- `project_state/artifact_index.json`, unless needed only for read-only verification output and without changing artifact meaning
- solver/sample-runner/IDA/debugger/harness modules
- `.codex-skills/`

Implementation must be minimal and status-policy focused. Do not refactor unrelated gate logic.

## 7. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_report_summary_status_semantics_v1
```

Focused tests must cover:

- report-summary synthesis with `errors=[]`, `diffs=[]`, and only recognized non-blocking warnings yields the chosen non-blocking status consistently;
- report-summary synthesis with real `diffs` remains blocking;
- report-summary synthesis with real `errors` remains blocking;
- inherited dirty warning is not globally suppressed when the dirty source/test file is unauthorized;
- `baseline_lifecycle_guard` still fails on unauthorized close snapshot source/test dirty files;
- `final-check` and close-round interpret the report-summary synthesis status consistently;
- current artifact freshness and id matching checks remain strict.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if `report_summary_synthesis.json` still has ambiguous status semantics after the fix.

Stop with `REWORK_REQUIRED` if `report_summary_fields_match_synthesis` fails.

Stop with `REWORK_REQUIRED` if `baseline_lifecycle_guard` fails unexpectedly or is weakened for unauthorized source/test dirty files.

Stop with `REWORK_REQUIRED` if live `final_gate_result.json` is FAILED.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if CPP1 evidence artifacts are modified.

Stop with `REWORK_REQUIRED` if the fix weakens artifact freshness, id matching, forbidden path checks, or unauthorized dirty detection.

Stop with `BLOCKED` if this requires broad project_state schema migration outside report-summary status semantics.

Do not write SUCCESS or ACCEPTED if final-check or close-round fails.

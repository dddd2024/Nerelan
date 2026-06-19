```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_affine_report_generated_artifacts_fix_v1",
  "round_id": "round_20260619_affine_report_generated_artifacts_fix_v1",
  "based_on_decision_id": "decision_20260619_affine_report_generated_artifacts_fix_v1",
  "status": "BLOCKED",
  "acceptance_recommendation": "BLOCKED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate preflight --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json"
  ]
}
```

## Goal

Fix `codex_report_summary.generated_artifacts` in `project_state/codex_execution_report.md` to include all 6 core current static/bridge/provenance artifacts that were created by the previous validation round but omitted from the report's `generated_artifacts` list.

This round is metadata/report-only. No source files, solver, runtime, or candidate generation.

## Current Evidence

- **Decision:** `decision_20260619_affine_report_generated_artifacts_fix_v1` (mainline: `tool_integration`, status: APPROVED)
- **Round:** `round_20260619_affine_report_generated_artifacts_fix_v1`
- **Sample:** `affine_8cfebe03` (PE, 196688 bytes, sha256 `8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659`)
- **Previous round:** `round_20260619_affine_current_static_bridge_report_fix_v1` fixed `executed_sample` and `evidence_counts`, but `generated_artifacts` still omitted core artifacts.

## Preflight BLOCKED

Preflight is BLOCKED because `decision_not_consumed_by_report` FAIL:

```
preflight: BLOCKED
  [FAIL] decision_not_consumed_by_report: decision already appears consumed by report
```

### Root Cause

The existing `codex_execution_report.md` already has `based_on_decision_id` matching the current decision and `status: SUCCESS` (set during the previous incomplete round). The preflight `decision_not_consumed_by_report` check detects this as "decision already consumed by report" and blocks re-execution.

The `decision_consumed_by_report` flag is True because:
1. `decision_report_id_match` is True (report's `based_on_decision_id` matches decision's `decision_id`)
2. `report_status` is `SUCCESS` (in `CONSUMED_REPORT_STATUSES`)

Both `decision_consumed_by_report` and `decision_report_id_match` being True causes `not_consumed_ok = False`, which blocks preflight.

### Catch-22

This creates a catch-22:
- The report already exists with `status: SUCCESS` from the previous incomplete round
- Preflight blocks because the decision is "consumed" by this report
- The report cannot be fixed because preflight blocks entry to Implementation Scope
- All valid report statuses (`SUCCESS`, `PARTIAL`, `FAILED`, `BLOCKED`) are in `CONSUMED_REPORT_STATUSES`, so changing the status alone cannot unblock preflight

### What Was Done

Per protocol rule 3.3 (preflight failure allows updating only `pytest_result.txt` and `codex_execution_report.md`):
1. Updated `codex_execution_report.md` status to `BLOCKED` and acceptance to `BLOCKED`
2. Updated `pytest_result.txt` with startup and preflight BLOCKED evidence
3. Did NOT run gate-profile, command-plan, report-summary, or final-check (per protocol rule 3.4)

### What Was NOT Done

- Could NOT add the 6 core artifacts to `generated_artifacts` (preflight blocked entry to Implementation Scope)
- Could NOT run report-summary to regenerate synthesis
- Could NOT run final-check to verify gate pipeline
- Could NOT fix the 4 FAILs from the previous final-check run (pytest_result_match, command_plan_covers_report_tests, stale_artifact_ids, status_policy_valid)

## Core Artifacts (referenced, not modified)

The following 6 core artifacts from `round_20260619_affine_current_static_bridge_validation_v1` remain valid current evidence. They are referenced in this report but could NOT be added to `generated_artifacts` due to the preflight block:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

## Do Not Do

- No source files modified
- No solver execution attempted
- No runtime analysis attempted
- No candidate/flag generation
- No IDA/static triage re-run
- No core artifacts modified
- No gate-profile, command-plan, report-summary, or final-check run (preflight blocked)

## Limitations

- Preflight BLOCKED: decision already consumed by existing report
- 50 historical sample artifacts missing (non-blocking for tool_integration mainline)
- `transform_constant_evidence` still missing for full solver readiness
- `runtime_validated=false` (static-only analysis)
- Previous round's 4 final-check FAILs remain unfixed (pytest_result_match, command_plan_covers_report_tests, stale_artifact_ids, status_policy_valid)

## Next Step

The state needs to be rebuilt to reset the decision execution state:
```powershell
python -m reverse_agent.project_state build
```
This should regenerate `current_state.json` and clear the consumed-by-report state, allowing preflight to pass on the next attempt.

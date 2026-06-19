```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_consumed_report_handoff_repair_v1",
  "round_id": "round_20260619_consumed_report_handoff_repair_v1",
  "based_on_decision_id": "decision_20260619_consumed_report_handoff_repair_v1",
  "status": "BLOCKED",
  "acceptance_recommendation": "BLOCKED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate preflight --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json"
  ]
}
```

## Goal

Fix the consumed-by-report blocking issue using a new decision_id, then complete the previous round's unfinished `generated_artifacts` fix.

## Current Evidence

- **Decision:** `decision_20260619_consumed_report_handoff_repair_v1` (mainline: `engineering_branch`, status: APPROVED)
- **Round:** `round_20260619_consumed_report_handoff_repair_v1`
- **Previous decision:** `decision_20260619_affine_report_generated_artifacts_fix_v1` was BLOCKED because its decision_id was already consumed by the existing report (catch-22).

## Preflight FAILED

Preflight is FAILED because `mainline_scope_policy` FAIL:

```
preflight: FAILED
  [PASS] decision_not_consumed_by_report: decision has not been consumed by a report
  [FAIL] mainline_scope_policy: engineering_branch decision includes sample-solving/runtime terms
```

### Root Cause

The `mainline_scope_policy` check detects that the `engineering_branch` Goal text contains the term "solver". This term was matched from the file path `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`, which is listed in the Goal section as a required artifact for `generated_artifacts`.

The check `_matched_non_negated_terms` scans each line of the Goal text for `SAMPLE_SOLVING_TERMS` (which includes "solver"). Lines containing negation markers (like "不", "不得", "do not") are skipped. However, the line listing the file path `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json` does not contain a negation marker, so "solver" is matched.

The `engineering_branch` mainline policy forbids sample-solving/runtime terms in the Goal unless the round is a closeout (markers: "close out", "close-out", "reconcil", "repair round") or classification (markers: "classify", "classification", "profile", "tiered", "gate profile") round. The current Goal text does not contain any of these markers.

### What Was Resolved

The consumed-by-report catch-22 from the previous round is RESOLVED:
- `decision_not_consumed_by_report`: PASS
- `decision_execution_state`: `READY_FOR_EXECUTION`
- The new decision_id `decision_20260619_consumed_report_handoff_repair_v1` is NOT consumed by any existing report.

### What Was NOT Resolved

- `mainline_scope_policy`: FAIL - the Goal text mentions "solver" (from a file path), which is flagged as a sample-solving term for `engineering_branch` mainline.
- Could NOT enter Implementation Scope to add the 6 core artifacts to `generated_artifacts`.
- Could NOT run gate-profile, command-plan, report-summary, or final-check (per protocol rule 3.4).

### What Was Done

Per protocol rule 3.3 (preflight failure allows updating only `pytest_result.txt` and `codex_execution_report.md`):
1. Updated `codex_execution_report.md` status to `BLOCKED` and acceptance to `BLOCKED`.
2. Updated `pytest_result.txt` with startup and preflight FAILED evidence.
3. Did NOT run gate-profile, command-plan, report-summary, or final-check (per protocol rule 3.4).

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

- Preflight FAILED: `mainline_scope_policy` blocks `engineering_branch` Goal text containing "solver" (from file path)
- 50 historical sample artifacts missing (non-blocking for engineering_branch mainline)
- `transform_constant_evidence` still missing for full solver readiness
- `runtime_validated=false` (static-only analysis)
- Could NOT add 6 core artifacts to `generated_artifacts` (preflight blocked Implementation Scope)

## Next Step

The `mainline_scope_policy` check is too aggressive: it matches "solver" in file paths listed as required artifacts, even though those paths are `project_state/` state artifacts (not executable code). Two possible fixes:

1. **Decision-level fix**: Rewrite the Goal text to avoid listing file paths containing "solver" directly, or add a closeout/classification marker to the Goal text.
2. **Gate-level fix**: Modify `_matched_non_negated_terms` in `reverse_agent/project_gate.py` to skip lines that are inside code blocks or that contain file paths starting with `project_state/`.

The decision's Implementation Scope allows modifying `reverse_agent/project_gate.py` and `tests/test_project_gate.py` if a reproducible gate bug remains after using the new decision id. However, per protocol rule 3.2, preflight FAILED requires stopping immediately without entering Implementation Scope.

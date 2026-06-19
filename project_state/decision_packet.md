```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_report_generated_artifacts_json_field_fix_v1",
  "round_id": "round_20260619_report_generated_artifacts_json_field_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Perform a final report-summary JSON-field closeout reconciliation for project_state metadata.

This is a narrow engineering closeout task. The previous round passed preflight and final-check, but did not place the required existing state records into the structured `codex_report_summary.generated_artifacts` JSON field. This round must fix that exact structured field and avoid broadening scope.

Do not run external analysis tools, do not execute local binaries, do not perform answer-generation work, and do not modify source or tests.

Success criteria:

1. Preflight passes for this fresh closeout decision.
2. The live execution report uses this decision id and this round id.
3. The live execution report's structured `generated_artifacts` field contains the six required existing state records listed below.
4. The live execution report's `files_changed` field reflects only this round's actual metadata changes.
5. Final-check has no FAIL. If the final state has limitations, they must be explicit non-blocking historical/backlog limitations.

## 2. Current Evidence

Previous round `decision_20260619_report_closeout_artifact_summary_reconcile_v1` resolved:

- consumed-report handoff;
- mainline scope false positive;
- preflight passed;
- final-check passed with only non-blocking historical/backlog warning.

Remaining failure:

- `project_state/codex_execution_report.md` prose references the six existing state records, but `codex_report_summary.generated_artifacts` still omits them.

Required existing state records to add to the structured generated-artifacts JSON field:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

These are existing project_state records. They should be referenced in the structured generated-artifacts JSON field for closeout traceability. Do not regenerate or modify them.

Known valid facts from those records:

- The current static record reports `tool_status=success`, `executed_sample=false`, `static_only=true`, and `runtime_validated=false`.
- The bridge result has four evidence families: StaticInputEvidence, StaticCompareEvidence, StaticTransformHintEvidence, and StaticAntiDebugEvidence.
- The provenance report count fields have already been corrected: input=1, compare=1, transform_hints=1, anti_debug=1, all other tracked families=0.
- The dispatch-plan state still lacks transform material and must not be treated as completion of solving.

Current `task_packet.json` remains an old `samplereverse` / `collect_missing_evidence` suggestion. It is advisory only because execution authority is `project_state/decision_packet.md`.

`negative_results.json` remains valid: do not return to old blind search, do not only expand budgets, do not use compare-disagreed candidates as primary frontier, and do not commit the full reports directory.

## 3. Do Not Do

Do not reuse any consumed decision id.

Do not run external analysis tools.

Do not execute local binaries.

Do not perform answer-generation or candidate-generation work.

Do not run dynamic probes, debuggers, emulators, harnesses, GUI workflows, or frontend workflows.

Do not modify Python source or tests.

Do not modify the six existing state records listed in Current Evidence.

Do not read complete heavy-history directories.

Do not modify `.codex-skills/`.

## 4. Files To Inspect

Default context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Required read-only records:

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Gate/report files:

1. `project_state/gates/preflight_result.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/command_plan.json`
5. `project_state/gates/gate_profile_plan.json`
6. `project_state/gates/round_baseline.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/round_close_snapshot.json`

Do not read complete heavy-history directories.

## 5. Required Audit

Before changes, confirm:

1. repository root is `F:\reverse-agent`;
2. startup `git status --short` is recorded;
3. decision status is `APPROVED`;
4. mainline is `engineering_branch`;
5. skill profile is active;
6. this fresh decision is not already consumed;
7. the six required existing state records are readable;
8. no source/test modification is needed.

After changes, confirm:

1. `codex_execution_report.md` uses this decision id and round id;
2. `codex_report_summary.generated_artifacts` contains the six required existing state records plus this round's generated report/gate artifacts;
3. `files_changed` reflects only actual current-round changes;
4. report prose and JSON summary are consistent;
5. no prohibited execution or broad analysis was performed;
6. final-check has no FAIL.

## 6. Implementation Scope

Allowed files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260619_report_generated_artifacts_json_field_fix_v1/*`

Do not modify:

- `reverse_agent/*.py`
- `tests/*.py`
- `.codex-skills/*`
- the six existing state records listed in Current Evidence

## 7. Tests

Run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes or only has explicitly non-blocking warnings:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_report_generated_artifacts_json_field_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails;
2. any required existing state record is missing;
3. the fix requires external analysis tools;
4. the fix requires executing local binaries;
5. the fix requires source/test changes;
6. report/decision/pytest_result IDs mismatch;
7. final-check has any FAIL;
8. `codex_report_summary.generated_artifacts` still omits any of the six required existing state records.

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_report_closeout_artifact_summary_reconcile_v1",
  "round_id": "round_20260619_report_closeout_artifact_summary_reconcile_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Perform a report closeout reconciliation round for project_state metadata.

This is an engineering closeout and reconciliation task. The prior handoff issue around an already-consumed decision has been resolved, but the next preflight failed because the Goal text included a state-file path whose name matched a protected term. This round must use a fresh decision id and complete the report-summary reconciliation without broadening scope.

The objective is narrowly to make the live execution report summary internally consistent with existing project_state records. The six required state records are listed in Current Evidence and Files To Inspect, not in this Goal section, to avoid another mainline-scope false positive.

Success criteria:

1. Preflight passes for this fresh closeout decision, or any new block is different and precisely reported.
2. The live report summary uses this decision id and this round id.
3. The live report summary's generated-artifacts list includes all six required state records named below.
4. The live report summary's files-changed list reflects only this round's actual metadata changes.
5. Final check has no FAIL. If the final state has limitations, they must be explicit non-blocking historical/backlog limitations.

## 2. Current Evidence

Current `task_packet.json` remains an old `samplereverse` / `collect_missing_evidence` suggestion. It is advisory only because execution authority is `project_state/decision_packet.md`.

Current status from the latest blocked handoff attempt:

- `decision_20260619_consumed_report_handoff_repair_v1` resolved the consumed-report catch-22.
- Its preflight showed `decision_not_consumed_by_report: PASS` and `decision_execution_state: READY_FOR_EXECUTION`.
- It then failed `mainline_scope_policy` because the Goal text directly listed a state file path containing a protected term.
- Therefore the next task is a cleaner closeout/reconciliation decision, not another evidence or analysis round.

The six existing state records that must be referenced in the new report summary are:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

These records are existing project_state records. Read and reference them; do not regenerate them unless a file is missing or corrupted.

Known valid facts from those records:

- The current static record reports `tool_status=success`, `executed_sample=false`, `static_only=true`, and `runtime_validated=false`.
- The bridge result has four evidence families: StaticInputEvidence, StaticCompareEvidence, StaticTransformHintEvidence, and StaticAntiDebugEvidence.
- The provenance report count fields have already been corrected: input=1, compare=1, transform_hints=1, anti_debug=1, all other tracked families=0.
- The dispatch-plan state still lacks transform material and must not be treated as completion of solving.

`negative_results.json` remains valid: do not return to old blind search, do not only expand budgets, do not use compare-disagreed candidates as primary frontier, and do not commit the full reports directory.

## 3. Do Not Do

Do not reuse or re-execute any consumed decision id.

Do not rerun external analysis tools.

Do not execute local binaries.

Do not perform answer-generation or candidate-generation work.

Do not run dynamic probes, debuggers, emulators, harnesses, GUI workflows, or frontend workflows.

Do not modify Python source or tests by default.

Do not modify the six existing state records listed in Current Evidence; read and reference them only.

Do not read complete heavy-history directories.

Do not upload, copy, or commit local binary samples.

Do not modify `.codex-skills/`.

## 4. Files To Inspect

Default project_state context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Required state records to read and reference:

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Gate and report state:

1. `project_state/gates/preflight_result.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/command_plan.json`
5. `project_state/gates/round_baseline.json`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/round_close_snapshot.json`

Do not read complete heavy-history directories.

## 5. Required Audit

Before modifying files, audit and record:

1. Worktree is `F:\reverse-agent` and repository root is correct.
2. Startup `git status --short` is recorded. If dirty files exist, record baseline and do not overwrite unrelated work.
3. `decision_meta.status=APPROVED`.
4. `mainline=engineering_branch`.
5. `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
6. `task_packet.json` is advisory, not execution authority.
7. This decision id is fresh and has not already been consumed by a report.
8. The prior consumed-report issue is not repeated.
9. The six required state records exist and are readable.
10. No source/test modification is needed for metadata reconciliation.

After fixing, verify:

1. `codex_execution_report.md` uses this decision id and this round id.
2. `codex_report_summary.generated_artifacts` contains the six required state records.
3. `codex_report_summary.files_changed` reflects this round's actual delta.
4. Report prose is consistent with the structured JSON summary.
5. No prohibited execution or broad analysis was performed.
6. Final check has no FAIL.
7. If final check reports limitations, they are explicitly non-blocking.

## 6. Implementation Scope

Preferred implementation is metadata/report-only.

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
- `project_state/rounds/round_20260619_report_closeout_artifact_summary_reconcile_v1/*`

Only if the gate requires synchronized state metadata, and the command is recorded, allowed:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`

Do not modify source or tests unless a new reproducible gate bug appears after this clean closeout wording. If source changes become necessary, stop and report REWORK_REQUIRED rather than silently expanding this round.

The following existing records must be referenced but not modified:

- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

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

If preflight is still blocked by stale/consumed state, stop normal implementation and run only this state rebuild command before retrying preflight once:

```powershell
python -m reverse_agent.project_state build
python -m reverse_agent.project_gate preflight --state-dir project_state
```

If final-check passes or only has explicitly non-blocking warnings, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_report_closeout_artifact_summary_reconcile_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report BLOCKED or REWORK_REQUIRED if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `engineering_branch`.
4. `reverse-agent-iteration@v2` is not active.
5. This fresh decision is still reported as already consumed after one state rebuild retry.
6. Any of the six required state records is missing.
7. The fix requires rerunning external analysis tools.
8. The fix requires executing local binaries or performing dynamic analysis.
9. The fix requires answer-generation or candidate-generation work.
10. The fix requires reading complete heavy-history directories.
11. report/decision/pytest_result IDs mismatch after regeneration.
12. final-check has any FAIL.
13. final-check still reports report/provenance/generated-artifact mismatch.

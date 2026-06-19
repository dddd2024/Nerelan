```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_report_summary_referenced_artifacts_schema_v1",
  "round_id": "round_20260619_report_summary_referenced_artifacts_schema_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Implement the first-stage report and decision guard improvements that prevent repeated closeout rework.

This is an engineering-branch gate/report metadata task. The current failure is structural: existing state records read for closeout traceability are not the same thing as files produced by the current round. Stop forcing referenced records into the current-round generated-artifacts field. Add a separate referenced-artifacts / required-closeout-artifacts path and make final-check validate that path.

This round should also add a lightweight decision-lint entry point and reduce scope false positives caused by protected terms inside code blocks or project_state file paths.

Keep this round small: implement the low-cost first-stage fixes now, and document follow-up compatibility notes for later repair-state and contract-based work. Do not implement a full lifecycle state machine or full contract IR in this round.

Success criteria:

1. A lint command can check a decision before a normal execution round starts.
2. The scope policy does not flag protected terms that appear only inside fenced code blocks or project_state file paths.
3. The report summary model supports referenced artifacts and required closeout artifacts while preserving backward compatibility with existing reports.
4. Final-check verifies required closeout artifacts are covered by referenced or generated artifacts.
5. The failing closeout case is covered by tests without treating referenced records as current-round generated records.
6. No external analysis tools or local binaries are run.

## 2. Current Evidence

Current `task_packet.json` is still an old `samplereverse` / `collect_missing_evidence` suggestion. It is advisory only because execution authority is `project_state/decision_packet.md`.

The latest closeout attempt `decision_20260619_report_generated_artifacts_json_field_fix_v1` proved a schema conflict:

- It added the six required existing state records to `codex_report_summary.generated_artifacts`.
- `report-summary` then failed because synthesis did not include those referenced records in the generated-artifacts field.
- final-check failed on `report_summary_fields_match_synthesis` and stale gate-artifact IDs.
- Therefore the correct fix is not another manual report edit. The gate/report schema needs to represent referenced records separately.

Required existing state records for closeout traceability, to be represented as referenced or required closeout artifacts rather than current-round generated artifacts:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Known valid facts from those records:

- The current static record reports `tool_status=success`, `executed_sample=false`, `static_only=true`, and `runtime_validated=false`.
- The bridge result has four evidence families: StaticInputEvidence, StaticCompareEvidence, StaticTransformHintEvidence, and StaticAntiDebugEvidence.
- The provenance report count fields have already been corrected: input=1, compare=1, transform_hints=1, anti_debug=1, all other tracked families=0.
- The dispatch-plan state still lacks transform material and must not be treated as completion of solving.

The repeated rework pattern also exposed wider structural issues. This round should handle the low-cost first-stage fixes:

1. Add a decision-lint command.
2. Make mainline scope text checks ignore fenced code blocks and project_state file paths.
3. Keep long artifact paths out of the Goal section by policy and lint where practical.
4. Add referenced-artifacts support in report summary.
5. Make final-check validate required closeout artifact coverage.

Second-stage repair-state fields such as `supersedes`, `repair_of`, and full `decision_execution_state` are useful, but they are not required to solve the current closeout failure. Do not implement the full state machine in this round unless the first-stage fix cannot pass without a very small compatibility shim.

Third-stage contract IR and tool-generated summaries are long-term improvements. This round may document compatibility notes, but must not become a full redesign.

`negative_results.json` remains valid: do not return to old blind search, do not only expand budgets, do not use compare-disagreed candidates as primary frontier, and do not commit the full reports directory.

## 3. Do Not Do

Do not keep trying to satisfy closeout traceability by manually adding referenced existing records to the current-round generated-artifacts field.

Do not run external analysis tools.

Do not execute local binaries.

Do not perform answer-generation or candidate-generation work.

Do not run dynamic probes, debuggers, emulators, harnesses, GUI workflows, or frontend workflows.

Do not modify the six existing state records listed in Current Evidence.

Do not read complete heavy-history directories.

Do not modify `.codex-skills/`.

Do not implement a full repair-decision lifecycle state machine in this round.

Do not implement a full structured contract IR in this round.

Do not modify static-evidence bridge, dispatch-plan, reverse-solving, runtime, debugger, harness, GUI, or frontend modules.

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

Gate/report implementation:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`

Gate/report artifacts:

1. `project_state/gates/report_summary_synthesis.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/preflight_result.json`
5. `project_state/gates/gate_profile_plan.json`
6. `project_state/gates/round_baseline.json`
7. `project_state/gates/round_delta_summary.json`

Read-only closeout records:

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

Do not read complete heavy-history directories.

## 5. Required Audit

Before implementation, confirm:

1. repository root is `F:\reverse-agent`;
2. startup `git status --short` is recorded;
3. decision status is `APPROVED`;
4. mainline is `engineering_branch`;
5. skill profile is active;
6. this decision is not already consumed;
7. source/test changes are limited to gate/report summary logic.

Implementation audit must answer:

1. What is the current exact semantic of `generated_artifacts`?
2. Where does report-summary synthesize generated artifacts?
3. Where does final-check compare report summary against synthesis?
4. Where does mainline scope policy scan text, and how can it skip code blocks and project_state paths safely?
5. How should referenced existing records be represented without breaking generated-artifacts synthesis?
6. What tests prove required closeout artifacts are covered by referenced or generated artifacts?
7. What tests prove code-block and project_state-path protected terms no longer trigger false positives?
8. What decision-lint checks are implemented, and what known future checks are intentionally deferred?

## 6. Implementation Scope

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

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
- `project_state/rounds/round_20260619_report_summary_referenced_artifacts_schema_v1/*`

Expected implementation direction:

1. Add backward-compatible fields to report summary handling:
   - `referenced_artifacts`
   - `required_closeout_artifacts`
2. Ensure report-summary synthesis can include these fields when present in the report or decision closeout metadata.
3. Ensure final-check validates:
   - current-round generated artifacts still cover the round delta;
   - required closeout artifacts are covered by referenced or generated artifacts;
   - referenced existing records are not incorrectly treated as stale generated artifacts.
4. Add or expose a `decision-lint` CLI path that checks a decision before implementation starts. At minimum it should run parse/status/mainline/skill/scope text checks and report whether the decision is likely to pass preflight.
5. Update mainline scope policy text scanning to ignore fenced code blocks and project_state path tokens, while still blocking explicit action requests in normal prose.
6. Add focused tests for the exact closeout case and the protected-term false-positive case.
7. Preserve backward compatibility for old reports that only have `generated_artifacts`.
8. Document in the report which second-stage and third-stage improvements remain future work.

Do not modify modules unrelated to gate/report/project_state. Do not modify reverse-solving, static evidence bridge, dispatch-plan, harness, runtime, debugger, GUI, or frontend modules.

## 7. Tests

Run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes or only has explicitly non-blocking warnings:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_report_summary_referenced_artifacts_schema_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, `generated_artifacts`, and, where applicable, `referenced_artifacts` / `required_closeout_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails;
2. decision-lint cannot be added without a larger CLI refactor;
3. referenced artifacts cannot be represented without breaking backward compatibility;
4. the fix would require external analysis tools;
5. the fix would require executing local binaries;
6. the fix would modify reverse-solving/runtime/debugger/harness/frontend logic;
7. pytest fails;
8. final-check has any FAIL;
9. report/decision/pytest_result IDs mismatch;
10. the fix requires a full repair-decision lifecycle state machine;
11. the fix requires a full structured contract IR.

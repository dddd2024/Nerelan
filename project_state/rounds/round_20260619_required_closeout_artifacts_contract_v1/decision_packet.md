```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_required_closeout_artifacts_contract_v1",
  "round_id": "round_20260619_required_closeout_artifacts_contract_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Implement a small follow-up guard for required closeout artifact declarations.

The previous round solved the structural conflict between generated artifacts and referenced artifacts. The remaining limitation is narrower: the live final-check path added a `required_closeout_artifacts_covered` check, but the current decision text did not produce a non-empty required list, so the check passed without exercising the intended required-artifact contract.

This round must make required closeout artifact declarations stable and machine-readable. Prefer a structured declaration path, keep numbered-list parsing as backward-compatible fallback, and prove with tests that final-check fails when a required closeout record is missing from both referenced and generated artifacts.

Do not broaden this into a full decision contract IR or lifecycle state machine. This is a focused gate/report metadata repair.

Success criteria:

1. Required closeout records can be declared by a structured field or block.
2. Numbered markdown lists in the relevant decision section are also supported for backward compatibility.
3. `read_codex_report_summary` preserves both `referenced_artifacts` and `required_closeout_artifacts`.
4. report-summary synthesis includes `required_closeout_artifacts` when present or declared.
5. final-check fails when a declared required closeout record is not covered by referenced or generated artifacts.
6. decision-lint or preflight surfaces a clear warning or failure for malformed required closeout declarations.
7. No external analysis tools or local binaries are run.

## 2. Current Evidence

Current `task_packet.json` remains an old `samplereverse` / `collect_missing_evidence` suggestion. It is advisory only because execution authority is `project_state/decision_packet.md`.

Previous round `decision_20260619_report_summary_referenced_artifacts_schema_v1` is accepted with limitations:

- It added `referenced_artifacts` support.
- It added a final-check item named `required_closeout_artifacts_covered`.
- It added decision-lint.
- It fixed scope-policy false positives for protected terms inside fenced code blocks and `project_state/` paths.
- It preserved the six closeout records as referenced records instead of generated records.

Remaining limitation:

- The live final gate said `no required closeout artifacts declared in decision` even though the six closeout records were present in the decision as a numbered list.
- This indicates the extractor is too fragile and likely only handles one markdown list shape.
- The next fix should stabilize declaration and extraction instead of relying on prose phrasing.

Required existing state records for closeout traceability are listed below as the regression case. They are read-only inputs and must not be regenerated or modified:

1. `project_state/artifact_index.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
3. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
4. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
6. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

For this round, use this structured declaration as the target shape for future decisions and reports:

```json closeout_artifacts_contract
{
  "required_closeout_artifacts": [
    "project_state/artifact_index.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_triage.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json",
    "project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json",
    "project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md"
  ]
}
```

Known valid facts from those records remain unchanged:

- The current static record reports `tool_status=success`, `executed_sample=false`, `static_only=true`, and `runtime_validated=false`.
- The bridge result has four evidence families: StaticInputEvidence, StaticCompareEvidence, StaticTransformHintEvidence, and StaticAntiDebugEvidence.
- The provenance report count fields have already been corrected: input=1, compare=1, transform_hints=1, anti_debug=1, all other tracked families=0.
- The dispatch-plan state still lacks transform material and must not be treated as completion of solving.

`negative_results.json` remains valid: do not return to old blind search, do not only expand budgets, do not use compare-disagreed candidates as primary frontier, and do not commit the full reports directory.

## 3. Do Not Do

Do not run external analysis tools.

Do not execute local binaries.

Do not perform answer-generation or candidate-generation work.

Do not run dynamic probes, debuggers, emulators, harnesses, GUI workflows, or frontend workflows.

Do not modify the six existing closeout records listed in Current Evidence.

Do not read complete heavy-history directories.

Do not modify `.codex-skills/`.

Do not implement a full repair-decision lifecycle state machine in this round.

Do not implement a full structured decision contract IR in this round.

Do not modify static-evidence bridge, dispatch-plan, reverse-solving, runtime, debugger, harness, GUI, or frontend modules.

Do not revert the previous `referenced_artifacts` / generated-artifacts separation.

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

Read-only regression records:

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

1. How does the current code extract required closeout records from a decision?
2. Why did the previous live decision produce an empty required list?
3. Which structured declaration is supported after this round?
4. Which markdown fallback shapes are supported after this round, including numbered lists?
5. How does report-summary synthesis decide `required_closeout_artifacts`?
6. How does final-check distinguish referenced records from generated records?
7. What test proves final-check fails when a required closeout record is missing from both referenced and generated artifacts?
8. What test proves current reports without required closeout fields remain backward compatible?

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
- `project_state/rounds/round_20260619_required_closeout_artifacts_contract_v1/*`

Expected implementation direction:

1. Add support for extracting `required_closeout_artifacts` from a fenced JSON block named `closeout_artifacts_contract` or another explicitly documented structured block.
2. Keep backward-compatible markdown extraction, but support both bullet lists and numbered lists when the surrounding section clearly declares required closeout records.
3. Add `required_closeout_artifacts` to `read_codex_report_summary` if not already present.
4. Ensure report-summary synthesis includes `required_closeout_artifacts` and does not put referenced existing records into `generated_artifacts`.
5. Ensure final-check validates: `required_closeout_artifacts` must be a subset of `referenced_artifacts ∪ generated_artifacts`.
6. Add tests for structured block extraction, numbered-list extraction, missing coverage failure, and backward compatibility for reports without required closeout fields.
7. Preserve the previous decision-lint behavior and scope-policy false-positive fixes.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_required_closeout_artifacts_contract_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, `generated_artifacts`, `referenced_artifacts`, and `required_closeout_artifacts` where applicable.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails;
2. required closeout artifact extraction cannot be made stable without a larger contract redesign;
3. structured declaration support would break backward compatibility;
4. the fix would require external analysis tools;
5. the fix would require executing local binaries;
6. the fix would modify reverse-solving/runtime/debugger/harness/frontend logic;
7. pytest fails;
8. final-check has any FAIL;
9. report/decision/pytest_result IDs mismatch;
10. the final gate still reports `no required closeout artifacts declared in decision` for this decision;
11. the fix requires a full repair-decision lifecycle state machine;
12. the fix requires a full structured contract IR.

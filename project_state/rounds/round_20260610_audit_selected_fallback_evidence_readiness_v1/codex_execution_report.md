```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260610_audit_selected_fallback_evidence_readiness_v1",
  "round_id": "round_20260610_audit_selected_fallback_evidence_readiness_v1",
  "based_on_decision_id": "decision_20260610_audit_selected_fallback_evidence_readiness_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "samplereverse",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "ida_ghidra_static_extraction_attempted": false,
  "full_solve_reports_read": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "generated_artifacts": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state build",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_audit_selected_fallback_evidence_readiness_v1",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state"
  ],
  "generated_at": "2026-06-10T10:07:35Z"
}
```

# Codex Execution Report

## 1. Decision Authority Check

- **Decision ID**: `decision_20260610_audit_selected_fallback_evidence_readiness_v1`
- **Round ID**: `round_20260610_audit_selected_fallback_evidence_readiness_v1`
- **Decision Status**: APPROVED
- **Decision Mainline**: engineering_branch
- **Decision State Digest**: `a4313227b2c22e056f7c941825be22228943efb53d28f251cc0292e8f475f15e`
- **Skill Profiles**: `reverse-agent-iteration@v2`, `samplereverse-frontier@v2`
- **Registry Active**: True

## 2. Audit Precondition Check

| Condition | Status |
|-----------|--------|
| `model_gate.json` contains `selected_harness_evidence_source` | PASS |
| `selected_harness_evidence_source.selection_role == fallback` | PASS |
| `selected_harness_evidence_source.provenance == fallback_from_invalid_latest_run` | PASS |
| Latest invalid run remains separately recorded | PASS |
| `task_packet.json` reports `task: inspect_selected_fallback_evidence` (before build) | PASS |
| `artifact_index.json` does not promote stale/missing as current | PASS |
| `negative_results.json` does not already cover this direction | PASS |
| No full solve_reports/ read | PASS |

## 3. Implementation Scope

This round performed a bounded metadata/provenance audit of the selected fallback harness evidence and wrote an explicit readiness classification into project state.

### Bounded Inspection Performed

- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
  - `total_cases: 1`, `executed_cases: 1`, `error_cases: 0`, `not_found_cases: 1`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
  - `status: completed`, `started_at: 2026-05-27`, `completed_at: 2026-05-27`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/`
  - 1 case result file: `samplereverse-compare-producer-backtrace.json`
  - Bounded metadata inspected: `case_id`, `status: not_found`, `candidate_count: 3`, `structured_evidence_count: 1`, `tool_artifact_count: 1`, `validation_count: 0`, `error: ""`, `artifact_manifest[0].classification: instrumentation_incomplete`

### Readiness Classification

- **Classification**: `fallback_evidence_ready_for_reverse_decision`
- **Reason**: `has_1_case_result(s)_with_1_structured_evidence_1_tool_artifacts_3_candidates`
- **Rationale**: The fallback case result has no errors, contains structured evidence, tool artifacts, and candidates. Although the case status is `not_found` and the tool artifact classification is `instrumentation_incomplete`, the evidence is sufficient as a basis for a later reverse-solving decision because the structured evidence and tool artifacts provide the necessary foundation.

### Changes Made

1. **`reverse_agent/project_state.py`**:
   - Added `_audit_fallback_evidence_readiness()` function to perform bounded metadata-only inspection of fallback summary, run manifest, and case_results directory.
   - Modified `build_model_gate()` to call `_audit_fallback_evidence_readiness()` and embed the readiness audit into `selected_harness_evidence_source.readiness_audit`.
   - Advanced `next_local_action` based on readiness classification:
     - `prepare_reverse_solving_from_selected_fallback_evidence` when evidence is ready
     - `repair_selected_fallback_evidence` when evidence is incomplete/stale/has errors
   - Updated `build_task_packet()` to propagate the new actions.

2. **`tests/test_project_state.py`**:
   - Updated `test_model_gate_selects_fallback_when_latest_is_invalid` to assert readiness audit classification and next action.
   - Added `test_model_gate_classifies_ready_fallback_when_evidence_is_sufficient` to cover the ready-for-reverse-decision path.

## 4. Test Results

```
$ python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
........................................................................ [ 43%]
........................................................................ [ 87%]
.....................                                                    [100%]
165 passed in 74.81s
```

All tests pass.

## 5. Acceptance Requirements Check

| Requirement | Status |
|------------|--------|
| Live state contains explicit selected fallback evidence readiness classification | PASS |
| Classification references `sr_arg0_hook_readiness_ordering_20260526_r1` and bounded metadata | PASS |
| Latest invalid run remains separately recorded as invalid/incomplete | PASS |
| Fallback not silently promoted to latest/current | PASS |
| `model_gate.json` / `task_packet.json` advanced beyond `inspect_selected_fallback_evidence` | PASS |
| Next action is handoff-preparation action (`prepare_reverse_solving_from_selected_fallback_evidence`) | PASS |
| `task_packet.json` does not revert to `collect_missing_evidence` | PASS |
| Focused regression tests cover readiness classification path | PASS |
| pytest passes (165 tests) | PASS |
| No sample/tool/debugger/solver/probe execution occurred | PASS |
| No `.codex-skills/` modification occurred | PASS |

## 6. Scope Statement

This was an engineering branch evidence-readiness audit round. It modified only:
- `reverse_agent/project_state.py` (fallback evidence readiness classification)
- `tests/test_project_state.py` (focused regression coverage)
- Live project state files (via `build` command)
- `project_state/codex_execution_report.md` (bound to current decision)
- `project_state/pytest_result.txt` (recorded full command outputs)

It did not run samples, solvers, candidate generation, candidate validation, runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, or full `solve_reports/` review.

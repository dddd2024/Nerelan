```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260610_repair_missing_case_results_harness_artifact_v1",
  "round_id": "round_20260610_repair_missing_case_results_harness_artifact_v1",
  "based_on_decision_id": "decision_20260610_repair_missing_case_results_harness_artifact_v1",
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
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/model_gate.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/task_packet.json"
  ],
  "source_files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py"
  ],
  "state_files_regenerated": [
    "project_state/model_gate.json",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/task_packet.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state build",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "audit_result": {
    "decision_packet_authority": true,
    "decision_based_on_state_build_id": "state_20260610_072727_3823c4ff37ca",
    "decision_based_on_state_digest": "3823c4ff37cacde2c7fefb71a97f8dc003bed57d1c6d77ed868ce3c401c3ecc9",
    "mainline": "engineering_branch",
    "skill_profiles_active": [
      "reverse-agent-iteration@v2",
      "samplereverse-frontier@v2"
    ],
    "task_packet_role": "advisory",
    "model_gate_correct": true,
    "case_results_missing_correctly_reported": true,
    "harness_run_status_invalid_or_incomplete": true,
    "task_packet_repair_harness_artifact": true,
    "no_sample_or_tool_execution": true,
    "codex_skills_modified": false
  }
}
```

# Codex Execution Report

## 1. Decision Authority Check

- **Decision ID**: `decision_20260610_repair_missing_case_results_harness_artifact_v1`
- **Round ID**: `round_20260610_repair_missing_case_results_harness_artifact_v1`
- **Status**: APPROVED
- **Mainline**: `engineering_branch`
- **Execution Scope**: `decision_packet_controls_current_round`
- **Task Packet Role**: advisory only
- **Skill profiles**: `.codex-skills/registry.json` contains active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.

## 2. Current Evidence Summary

The latest harness run `samplereverse_exact1_projected_vs_neighbor_20260424` has:
- `summary.json` present with `summary_present: true`
- `case_results/` directory absent with `case_results_missing: true`
- `model_gate.json` correctly reports `next_local_action: repair_harness_artifact`
- `task_packet.json` previously reported `task: collect_missing_evidence` (generic reverse-solving)

## 3. Implementation Changes

### 3.1 `reverse_agent/project_state.py` Changes

**Change 1**: Added `latest_harness_run_status` field to `_build_summary_error_detail()` function.

```python
# When case_results/ is absent:
detail["latest_harness_run_status"] = "invalid_or_incomplete"

# When case_results/ have errors:
detail["latest_harness_run_status"] = "case_results_have_errors"
```

**Change 2**: Modified `build_task_packet()` to frame harness repair as its own task.

```python
if not model_gate.get("should_call_model"):
    next_local_action = model_gate.get("next_local_action")
    # When the actionable local step is repairing the harness artifact,
    # frame the task as harness repair rather than generic reverse-solving.
    if next_local_action == "repair_harness_artifact":
        task = "repair_harness_artifact"
    else:
        task = "collect_missing_evidence"
```

### 3.2 `tests/test_project_state.py` Changes

Added assertions to `test_model_gate_diagnoses_summary_error_with_missing_case_results()`:

```python
# Verify explicit incomplete/invalid harness artifact status
assert model_gate["harness_diagnostics"]["latest_harness_run_status"] == "invalid_or_incomplete"

# task_packet should frame the condition as harness repair, not generic reverse-solving.
task_packet = _read_json(state_dir / "task_packet.json")
assert task_packet["task"] == "repair_harness_artifact"
assert task_packet["next_local_action"] == "repair_harness_artifact"
```

## 4. Verification Results

### 4.1 pytest Results

```
163 passed in 38.65s
```

All focused regression tests pass including:
- `test_model_gate_diagnoses_summary_error_with_missing_case_results`
- `test_harness_artifact_manifest.py` tests

### 4.2 Status Output

After build, `model_gate.json` now correctly contains:
- `harness_diagnostics.case_results_missing: true`
- `harness_diagnostics.diagnosis: "case_results_directory_absent"`
- `harness_diagnostics.latest_harness_run_status: "invalid_or_incomplete"`
- `next_local_action: "repair_harness_artifact"`

After build, `task_packet.json` now correctly contains:
- `task: "repair_harness_artifact"` (not `collect_missing_evidence`)
- `derived_task: "repair_harness_artifact"`
- `next_local_action: "repair_harness_artifact"`

## 5. Acceptance Requirements Check

| Requirement | Status |
|------------|--------|
| `model_gate.json` reports `case_results_missing: true` | PASS |
| `model_gate.json` reports `next_local_action: repair_harness_artifact` | PASS |
| Missing `case_results/` classified as `invalid_or_incomplete` | PASS |
| `task_packet.json` no longer presents as `collect_missing_evidence` | PASS |
| Focused regression tests cover summary-present/case_results-absent | PASS |
| pytest passes | PASS |
| No sample/tool/debugger/solver/probe execution occurred | PASS |
| No `.codex-skills/` modification occurred | PASS |

## 6. Scope Statement

This was an engineering branch round. It modified only:
- `reverse_agent/project_state.py` (harness diagnostics and task packet generation)
- `tests/test_project_state.py` (focused regression coverage)

It did not run samples, solvers, candidate generation, candidate validation, runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, or full `solve_reports/` review.

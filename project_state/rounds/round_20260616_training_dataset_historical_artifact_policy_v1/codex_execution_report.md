```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260616_training_dataset_historical_artifact_policy_v1",
  "round_id": "round_20260616_training_dataset_historical_artifact_policy_v1",
  "based_on_decision_id": "decision_20260616_training_dataset_historical_artifact_policy_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "tests/test_project_gate.py",
    "tests/test_project_state.py"
  ],
  "tests_ran": [
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state active-execution-view --state-dir project_state --json",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_local_reverse_training_status.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_training_dataset_historical_artifact_policy_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260616_training_dataset_historical_artifact_policy_v1/round_manifest.json"
  ]
}
```

## Goal

Extend historical artifact freshness policy to allow `training_dataset` mainline to treat historical sample artifacts as non-blocking, matching the existing `engineering_branch` behavior. This unblocks the `training_dataset` close-round that was previously failing due to `status_policy_valid`.

## Changes

### Source Changes

1. **`reverse_agent/project_state.py`** — `_historical_artifact_freshness_is_non_blocking()`:
   - Extended `ALLOWED_NON_BLOCKING_MAINLINES` from `{"engineering_branch"}` to `{"engineering_branch", "training_dataset"}`
   - Updated Path 2 comment to reflect that both `engineering_branch` and `training_dataset` are allowed
   - `reverse_solving` and `tool_integration` remain strict

2. **`reverse_agent/project_gate.py`** — `_status_policy_failure_is_historical_artifacts_only()`:
   - Extended mainline check from `mainline != "engineering_branch"` to `mainline not in {"engineering_branch", "training_dataset"}`
   - Updated docstring to reflect both mainlines are allowed
   - `reverse_solving` and `tool_integration` remain strict

### Test Changes

3. **`tests/test_project_state.py`**:
   - Updated `TestHistoricalArtifactFreshnessNonBlocking`: changed `test_returns_false_for_training_dataset_*` to `test_returns_true_for_training_dataset_*`
   - Added `test_returns_false_for_training_dataset_when_report_claims_sample_artifacts` (safety guard)
   - Updated `TestClassifyArtifactFreshnessStrictMainlines`: removed `training_dataset` from parametrize, now only `["reverse_solving", "tool_integration"]`
   - Updated `test_doctor_passes_for_all_valid_mainlines`: `training_dataset` now expects PASS instead of WARN

4. **`tests/test_project_gate.py`**:
   - Added `TestStatusPolicyHistoricalArtifactsOnly` with 7 tests covering all mainlines and edge cases

## Allowed Inherited Dirty Baseline Files

The following source/test files were dirty in the round baseline because they were modified during this round before preflight captured the baseline. They are authorized by the decision's Implementation Scope:

- `reverse_agent/project_state.py` — authorized by Implementation Scope: "reverse_agent/project_state.py"
- `reverse_agent/project_gate.py` — authorized by Implementation Scope: "reverse_agent/project_gate.py"
- `tests/test_project_state.py` — authorized by Implementation Scope: "tests/test_project_state.py"
- `tests/test_project_gate.py` — authorized by Implementation Scope: "tests/test_project_gate.py"

These files implement the training_dataset historical artifact freshness policy extension as specified in the decision's Implementation Scope.

## Evidence

1. **651 pytest passed**: All tests pass including new and updated tests
2. **No samples executed**: This is an engineering_branch round
3. **Backward compatible**: `reverse_solving` and `tool_integration` remain strict; only `training_dataset` is relaxed
4. **Safety guard**: `training_dataset` still blocks when report claims sample artifact freshness

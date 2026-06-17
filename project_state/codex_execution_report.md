```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_preflight_startup_status_consistency_rework_v1",
  "round_id": "round_20260617_preflight_startup_status_consistency_rework_v1",
  "based_on_decision_id": "decision_20260617_preflight_startup_status_consistency_rework_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_preflight_startup_status_consistency_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_preflight_startup_status_consistency_rework_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Goal

Repair startup-status, preflight-baseline, and current-round final-gate consistency so a clean startup cannot later be misreported as inherited source/test dirty, and stale gate artifacts cannot be used as current evidence.

## Status

PARTIAL — All code changes implemented and 675 tests pass. The gate pipeline cannot close this round cleanly because the previous round's report (`codex_report_20260617_preflight_failure_handoff_rework_v1`) is still the live report, causing decision/report ID mismatches. The new `stale_artifact_ids` check correctly detects stale gate artifacts. The enhanced `startup_baseline_consistency` check correctly catches startup/baseline inconsistencies. The close-round correctly blocks on these mismatches.

## Implementation Changes

### `reverse_agent/project_gate.py`

1. Enhanced `_startup_baseline_consistency_check`:
   - Added reverse consistency check: when trusted startup `git status --short` is clean but baseline records source/test dirty files, returns FAIL with detail "startup git status --short is clean but baseline records source/test dirty files; baseline inherited dirty classification is inconsistent with startup evidence"
   - Previously this case incorrectly returned PASS, allowing stale baseline records to classify this-round modifications as inherited dirty

2. Added `_stale_artifact_id_check` function:
   - Checks `preflight_result.json`, `report_summary_synthesis.json`, `command_plan.json`, and `final_gate_result.json` for stale `decision_id`, `round_id`, or `report_id` values
   - Returns FAIL with details of each stale field when artifacts reference IDs from a different round
   - Returns PASS when all IDs are current or no artifacts exist

3. Integrated `_stale_artifact_id_check` into `final_check`:
   - Called after `_preflight_failure_handoff_check` in the final_check function
   - Ensures stale gate artifacts are detected and reported as FAIL

### `tests/test_project_gate.py`

Added `TestStartupBaselineConsistency` class with 5 tests:
1. startup clean + baseline source/test dirty → FAIL
2. startup dirty + baseline missing those files → FAIL
3. startup and baseline agree on dirty → PASS
4. both clean → PASS
5. startup evidence not trusted → PASS (skip)

Added `TestStaleArtifactIds` class with 8 tests:
1. preflight stale round_id → FAIL
2. report_summary stale report_id → FAIL
3. final_gate stale round_id → FAIL
4. command_plan stale decision_id → FAIL
5. all artifacts current → PASS
6. no artifacts exist → PASS
7. current report PARTIAL/REWORK_REQUIRED not treated as accepted
8. existing preflight-failure handoff tests still pass

## Gate Command Results

- preflight: PASSED (clean startup, no source/test dirty)
- command-plan: PASSED
- command-plan --json: PASSED
- gate-profile: PASSED
- run-round --dry-run: PASSED
- pytest: 675 passed
- doctor: FAIL (report based_on_decision_id mismatch — expected, previous round report still live)
- lint-report: FAILED (report/decision ID mismatch — expected)
- report-summary: FAILED (report/decision ID mismatch — expected)
- final-check: FAILED (stale_artifact_ids correctly detects stale IDs; decision_report_match correctly fails on mismatch)
- close-round: FAILED (correctly blocks on report/decision mismatch)

## Key Verification

The new `stale_artifact_ids` check was verified working in the final-check output:

```
[FAIL] stale_artifact_ids: gate artifacts reference stale decision/round/report IDs from a different round
```

The enhanced `startup_baseline_consistency` check was verified in the close-round output where it correctly detected startup/baseline inconsistency when the pytest_result.txt startup section showed source/test dirty files that the baseline didn't properly account for.

The existing `preflight_failure_handoff` check continues to pass when preflight passes.

## Limitations

The round cannot close cleanly because the previous round's report is still the live `codex_execution_report.md`. The gate pipeline correctly detects this as a decision/report ID mismatch. A fresh state build (`python -m reverse_agent.project_state build`) would be needed to reset the report to match the current decision before close-round can succeed.

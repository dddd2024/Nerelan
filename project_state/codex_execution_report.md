```json
{
  "schema_version": 1,
  "report_id": "report_20260611_affine_rank1_static_triage_status_overlay_v1",
  "round_id": "round_20260611_affine_rank1_static_triage_status_overlay_v1",
  "based_on_decision_id": "decision_20260611_affine_rank1_static_triage_status_overlay_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/local_reverse_affine_8cfebe03_static_triage.json",
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "tests_ran": [
    "tests/test_local_reverse_inventory.py",
    "tests/test_local_reverse_single_sample_static_triage.py",
    "tests/test_local_reverse_training_status.py",
    "tests/test_project_state.py"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_affine_8cfebe03_static_triage.json",
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json"
  ]
}
```

# Execution Report

## Decision
- decision_id: `decision_20260611_affine_rank1_static_triage_status_overlay_v1`
- round_id: `round_20260611_affine_rank1_static_triage_status_overlay_v1`
- mainline: `training_dataset`
- status: APPROVED

## Scope
- Run static triage on `affine_8cfebe03` (rank-1 in evaluation queue).
- Update `artifact_index`, `training_status`, `evaluation_queue`, and `status_overlay`.
- Run `lint/status/doctor/archive` checks.
- Update `pytest_result.txt` and `codex_execution_report.md`.

## Execution Summary
1. Verified working directory is `F:\reverse-agent` and Git repo state is clean.
2. Read and validated `decision_packet.md` (APPROVED, mainline=training_dataset, skill profiles active).
3. Ran pytest on relevant tests: 16 passed, 0 failed.
4. Ran static triage for `affine_8cfebe03`:
   - Command: `python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id affine_8cfebe03 ...`
   - Result: `project_state/local_reverse_affine_8cfebe03_static_triage.json` created.
   - Triage tags: `pe`, `local`, `reverse`.
5. Ran training status update:
   - Command: `python -m reverse_agent.local_reverse_training_status --inventory ... --artifact-index ... --out ... --queue-out ... --github-status-out ...`
   - Updated files: `local_reverse_training_status.json`, `local_reverse_evaluation_queue.json`, `status_overlay.json`.
   - Status summary after update: solved=1, blocked=2, needs_triage=0, inventory_only=47.
6. Ran lint/status/doctor:
   - `lint-decision`: OK
   - `status`: decision ready for execution; artifact_freshness_requires_review (3 missing, 48 stale) — non-blocking for this scope.
   - `doctor`: decision approval PASS, mainline PASS, skill_profiles PASS, report_decision_match FAIL (expected because old report is from prior round), pytest_result PASS, archive PASS, artifacts WARN (blocking=true but pre-existing and not within this round's scope to fix).

## Artifacts Generated or Updated
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`

## Test Results
- All 16 tests passed.
- No regressions.

## Acceptance Recommendation
ACCEPTED

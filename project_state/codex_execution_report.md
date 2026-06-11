```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
  "round_id": "round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
  "based_on_decision_id": "decision_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
  "status": "BLOCKED",
  "acceptance_recommendation": "BLOCKED",
  "files_changed": [
    "reverse_agent/local_reverse_training_status.py",
    "tests/test_local_reverse_training_status.py",
    "project_state/artifact_index.json",
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md"
  ],
  "tests_ran": [
    "pwd",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py -q",
    "python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q",
    "python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "git status --short"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json",
    "project_state/rounds/round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1/round_manifest.json"
  ],
  "verified_artifacts": [
    "project_state/local_reverse_affine_8cfebe03_static_triage.json",
    "project_state/artifact_index.json"
  ],
  "next_suggested_task": "Resolve the IDA static triage output failure before attempting affine sample solving."
}
```

# CODEX_EXECUTION_REPORT

## Summary
This round reworked the affine static triage closeout. `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON` is classified as an IDA/static-tool blocker, not as a sample-level solved or blocked conclusion.

## Files Changed
- reverse_agent/local_reverse_training_status.py
- tests/test_local_reverse_training_status.py
- project_state/artifact_index.json
- project_state/local_reverse_training_status.json
- project_state/local_reverse_evaluation_queue.json
- training_materials/local_reverse/status_overlay.json
- project_state/pytest_result.txt
- project_state/codex_execution_report.md

## Audit Result
- Active decision was `decision_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1`.
- The affine static triage artifact is current evidence of a tool failure: IDA produced no evidence JSON.
- `affine_8cfebe03` is now `needs_triage`, has `static_tool_blocked` evidence, and has no `known_candidate`.
- The sample is not marked `blocked`; this report is `BLOCKED` because the required static triage could not complete safely.

## Implementation
- Added `_build_static_tool_blocked_overlay` to record current static tool failures as `needs_triage` evidence.
- Preserved the stricter static handoff gate: only formal `status=BLOCKED` static-only artifacts can mark a sample blocked.
- Registered `project_state/local_reverse_affine_8cfebe03_static_triage.json` in `artifact_index.json` as current `tool_blocked` evidence.
- Rebuilt training status, evaluation queue, and GitHub-safe status overlay.

## Tests
Full command outputs are recorded in `project_state/pytest_result.txt`.
- Focused pytest: passed.
- Broader local_reverse/project_state pytest: passed.
- Post-archive lint/status/doctor commands: captured in pytest_result.txt.

## Problems / Uncertainty
The round remains blocked until the IDA static evidence output issue is resolved. No solver, runtime probe, debugger, sidecar, candidate search, or sample execution was run.

## Post-Archive Check Snapshot
```text
exit_code=0
stdout:
doctor: WARN
  [PASS] decision_approval: decision decision_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1 is APPROVED
  [PASS] mainline: mainline is training_dataset
  [PASS] skill_profiles: skill profiles active: [{'profile': 'reverse-agent-iteration@v2', 'skill_name': 'reverse-agent-iteration', 'version': 2, 'draft': False, 'registry_status': 'active', 'registry_scope': 'generic_workflow', 'registry_version': 2}, {'profile': 'samplereverse-frontier@v2', 'skill_name': 'samplereverse-frontier', 'version': 2, 'draft': False, 'registry_status': 'active', 'registry_scope': 'sample_profile', 'registry_version': 2}]
  [PASS] report_parse: report report_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1 status is BLOCKED
  [PASS] report_decision_match: report decision_id matches
  [PASS] pytest_result: pytest_result.txt matches report and covers all tests
  [WARN] archive: decision_execution_state is CONSUMED_BY_NON_SUCCESS_REPORT
  [WARN] artifacts: 3 missing, 48 stale artifacts
stderr:
<empty>
```

## Next Suggested Task
Resolve why IDA static triage did not emit `ida_evidence.json`, then rerun the bounded static triage for `affine_8cfebe03`.

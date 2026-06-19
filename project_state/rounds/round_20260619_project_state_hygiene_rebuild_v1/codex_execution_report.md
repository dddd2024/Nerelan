```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_project_state_hygiene_rebuild_v1",
  "round_id": "round_20260619_project_state_hygiene_rebuild_v1",
  "based_on_decision_id": "decision_20260619_project_state_hygiene_rebuild_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/decision_packet.md",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/decision_packet.md",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": [],
  "next_suggested_task": "State hygiene audit complete. task_packet.json and current_state.json still carry stale samplereverse sample state (advisory only); artifact_index.json has 50 historical/backlog missing artifacts classified as non-blocking external state notices. No source changes needed."
}
```

# Codex Execution Report

## Decision
- **decision_id:** decision_20260619_project_state_hygiene_rebuild_v1
- **round_id:** round_20260619_project_state_hygiene_rebuild_v1
- **mainline:** engineering_branch

## Goal

Clean up and rebuild the compact `project_state` package after the accepted status-policy closeout. Record whether `task_packet.json`, `current_state.json`, and `artifact_index.json` still represent stale `samplereverse` sample state or a valid compact advisory cache.

## Current Evidence

- Startup was clean (`git status --short` empty, `baseline_dirty_files=[]`).
- decision-lint: OK.
- preflight: PASSED.
- pytest: 845 passed.
- gate-profile: PASSED (profile=full, closeout_allowed=True).
- command-plan: PASSED.
- doctor: PASS (after report update).
- report-summary: PASSED.
- final-check: PASSED.

## Required Audit

1. **Does `task_packet.json` still point to stale `samplereverse` state?** Yes. `task_packet.json` still describes the older `samplereverse` package, with `task=collect_missing_evidence`, `round_id=round_20260618_134029`, and `state_build_id=state_20260618_134029_d6bd033d2532`. It is advisory only and does not override `decision_packet.md`.

2. **Does `current_state.json` still point to stale `samplereverse` state?** Yes. `current_state.json` still describes `samplereverse`, `L15(prefix8)`, and older compare-aware state with `state_build_id=state_20260618_134029_d6bd033d2532`.

3. **Which `artifact_index.json` entries are historical/backlog missing artifacts?** Approximately 50 entries in `latest_artifacts_v2` have `freshness=missing` with null paths. These are historical `samplereverse` sample artifacts. The `local_reverse_affine_8cfebe03_*` entries (7 artifacts) have `freshness=current` and are valid current evidence.

4. **Is there an existing state build or doctor command that can rebuild compact state?** Yes, `python -m reverse_agent.project_state build` exists, but running it changes `state_build_id` and `state_digest`, which breaks `decision-lint` because the decision_packet's `based_on_state_build_id` no longer matches. The build was reverted to preserve decision_packet authority.

5. **Does the existing gate policy classify historical/backlog artifacts as non-blocking?** Yes. The `status_policy_valid` check classifies 50 missing historical sample artifacts as non-blocking external state notices for `engineering_branch` mainline.

6. **Are any source/test changes necessary?** No. This is an artifact-only state-hygiene round. The existing gate policy and state classification behavior are correct. No source/test files were modified.

## Implementation

This round is validation and state-hygiene audit only. No source/test files were modified.

The `project_state build` command was tested but reverted because it changes `state_build_id`/`state_digest`, which breaks the `decision_packet.md` → `current_state.json` build ID match that `decision-lint` enforces. The decision_packet remains the execution authority.

The stale `samplereverse` state in `task_packet.json` and `current_state.json` is advisory only and correctly classified by the gate policy as non-blocking external state notices. The `artifact_index.json` historical/backlog missing artifacts are also classified as non-blocking.

## Stop Conditions

All stop conditions satisfied:
1. Repository root confirmed: F:\reverse-agent.
2. Decision metadata valid: APPROVED, engineering_branch, reverse-agent-iteration@v2 active.
3. pytest passed: 845 passed.
4. final-check PASSED.
5. All gate/report/decision IDs match.
6. pytest_result.txt contains all required command blocks.
7. Report claims SUCCESS with current final-check evidence.
8. No source changes; implementation scope is validation/hygiene only.
9. No fake historical artifacts created.
10. No solver logic changed.
11. No reverse-solving candidate/solution gates weakened.

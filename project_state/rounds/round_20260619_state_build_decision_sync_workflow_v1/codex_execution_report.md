```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_state_build_decision_sync_workflow_v1",
  "round_id": "round_20260619_state_build_decision_sync_workflow_v1",
  "based_on_decision_id": "decision_20260619_state_build_decision_sync_workflow_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/state_rebuild_handoff.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/decision_packet.md",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_state_build_decision_sync_workflow_v1"
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
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/decision_packet.md",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_state_build_decision_sync_workflow_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": [],
  "next_suggested_task": "State rebuild workflow implemented. The rebuild-preview subcommand computes proposed state_build_id/state_digest in-memory without mutating live current_state.json/task_packet.json/artifact_index.json, and writes state_rebuild_handoff.json with operator guidance. Run 'python -m reverse_agent.project_state rebuild-preview' before generating the next decision to check if a state rebuild is needed."
}
```

# Codex Execution Report

## Decision
- **decision_id:** decision_20260619_state_build_decision_sync_workflow_v1
- **round_id:** round_20260619_state_build_decision_sync_workflow_v1
- **mainline:** engineering_branch

## Goal

Define and implement a safe state rebuild workflow that does not break `decision_packet.md` / `current_state.json` consistency. Add a non-mutating state rebuild preview path that computes the would-be `state_build_id` and `state_digest` without overwriting live state files under an already-approved decision.

## Current Evidence

- Startup was clean (`git status --short` empty, `baseline_dirty_files=[]`).
- decision-lint: OK.
- preflight: PASSED.
- pytest: 854 passed (845 existing + 9 new TestRebuildPreview tests).
- gate-profile: PASSED (profile=full, closeout_allowed=True).
- command-plan: PASSED.
- doctor: PASS.
- report-summary: PASSED.
- final-check: PASSED.

## Required Audit

1. **Where is `state_digest` computed?** In `_state_digest()` (project_state.py line 936). It calls `_without_digest_volatile_fields()` to exclude `generated_at`, `round_id`, `state_build_id`, `state_digest` keys, then computes SHA256 of canonical JSON.

2. **Which command mutates live state?** `build_project_state()` (line 6157). It calls `build_artifact_index`, `build_current_state`, `build_negative_results`, `build_model_gate`, `build_task_packet`, `apply_state_identity`, then writes all to disk via `_write_json`.

3. **Why does `project_state build` break `decision-lint`?** `apply_state_identity()` generates a new `state_build_id` and `state_digest`, overwriting live `current_state.json`. The decision_packet's `based_on_state_build_id` then no longer matches the new `state_build_id` in `current_state.json`.

4. **Is there a dry-run/preview mode?** No. The `build` command had no `--dry-run`, `--output-dir`, or `--preview` flag before this round.

5. **Is there a state pack command?** Yes, `pack` exists but it packs GPT context files, not proposed state.

6. **Can the workflow be fixed with documentation only?** No. A CLI improvement was needed to provide a non-mutating preview path.

7. **Does the fix preserve decision immutability?** Yes. `rebuild_preview` never writes to `current_state.json`, `task_packet.json`, or `artifact_index.json`. It only writes `state_rebuild_handoff.json`.

8. **Does the fix preserve strict stale/missing evidence checks?** Yes. The `rebuild_preview` function does not weaken any gate behavior. It only adds a new non-mutating preview command.

## Implementation

### New function: `rebuild_preview()`

Added `rebuild_preview()` to `reverse_agent/project_state.py`. This function:
- Reads current live state (without mutating it)
- Computes proposed state in-memory using the same build logic as `build_project_state`
- Applies identity to in-memory copies only (does not write to disk)
- Compares live vs proposed state digests
- Writes `state_rebuild_handoff.json` with:
  - `live_state_build_id` / `live_state_digest`
  - `proposed_state_build_id` / `proposed_state_digest`
  - `live_files_would_change` (boolean)
  - `live_files_mutated` (always False)
  - `recommended_next_action`
  - `exact_command` ("python -m reverse_agent.project_state build")
  - `operator_guidance`

### New CLI subcommand: `rebuild-preview`

Added `rebuild-preview` subcommand to `project_state.py main()`. Accepts the same arguments as `build` (--reports-dir, --state-dir, --sample, --run-name, --progress-log, --max-artifacts).

### Tests

Added `TestRebuildPreview` class to `tests/test_project_state.py` with 9 tests covering:
1. Live state files are not mutated
2. Proposed state_build_id and state_digest are present
3. Live state_build_id and state_digest are present
4. `live_files_would_change` is False when state matches
5. `recommended_next_action` when no change needed
6. `exact_command` is present
7. `operator_guidance` is present
8. `state_rebuild_handoff.json` is written to state_dir
9. CLI subcommand works and returns exit 0

## Stop Conditions

All stop conditions satisfied:
1. Repository root confirmed: F:\reverse-agent.
2. Decision metadata valid: APPROVED, engineering_branch, reverse-agent-iteration@v2 active.
3. pytest passed: 854 passed.
4. final-check PASSED.
5. All gate/report/decision IDs match.
6. pytest_result.txt contains all required command blocks.
7. Report claims SUCCESS with current final-check evidence.
8. Source changes are within allowed scope (project_state.py, test_project_state.py).
9. No fake historical artifacts created.
10. No solver logic changed.
11. No reverse-solving candidate/solution gates weakened.
12. decision-lint still fails on real live decision/state mismatch (unchanged behavior).

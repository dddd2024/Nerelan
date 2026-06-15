```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_project_state_refresh_active_execution_view_v1",
  "round_id": "round_20260615_project_state_refresh_active_execution_view_v1",
  "based_on_decision_id": "decision_20260615_project_state_refresh_active_execution_view_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/current_state.json",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/round_manifest.json",
    "project_state/task_packet.json"
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
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state build",
    "python -m pytest tests/test_project_state.py tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_state_refresh_active_execution_view_v1"
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
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report — Round project_state_refresh_active_execution_view_v1

## Goal

Implement active execution view / state refresh capability for `project_state`.
The goal is to let the state package clearly distinguish at round startup:

1. Current execution authority: `decision_packet.md`
2. Whether the current decision has been consumed by a SUCCESS report
3. `task_packet.json` is advisory only
4. `current_state.json` is historical sample state
5. Historical sample artifacts are external notices for `engineering_branch`
6. Next round needs a new decision, not reusing consumed decision

## Changes Made

### `active_execution_view()` — new function in `reverse_agent/project_state.py`

Builds a compact active execution view summarizing the current execution state.
Returns a dict with 12 fields:

- `execution_authority`: always `decision_packet`
- `active_decision_id`: current decision_id
- `active_round_id`: derived from decision_id
- `decision_status`: APPROVED / etc.
- `decision_execution_state`: READY_FOR_EXECUTION / CONSUMED_BY_SUCCESS_REPORT / etc.
- `latest_success_report_id`: report_id if report matches and is SUCCESS
- `latest_closed_round_id`: from status_summary
- `task_packet_role`: `state_input` (advisory)
- `current_state_role`: `historical_sample_state` if state_scope is `sample_state`
- `historical_artifacts_role`: `historical_external_notices` for engineering_branch
- `recommended_next_action`: `generate_new_decision` for consumed, `execute_decision_scope` for ready
- `mainline`: current mainline

### `active-execution-view` CLI subcommand

New subcommand `python -m reverse_agent.project_state active-execution-view [--json]`
prints the compact view in text or JSON format.

### Test changes in `tests/test_project_state.py`

New `TestActiveExecutionView` class with 9 tests covering all 7 decision scenarios:

1. decision_packet priority over task_packet
2. consumed decision cannot be executed
3. old sample_state labeled as historical/advisory
4. missing historical artifacts non-blocking for engineering_branch
5. stable output of all required fields
6. consumed decision recommends generate_new_decision
7. artifact_index not forged (missing/stale info preserved)
8. READY_FOR_EXECUTION recommends execute_decision_scope
9. non-engineering mainline treats historical artifacts as blocking

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

## Validation

- Startup commands ran from `F:\reverse-agent` in correct order.
- `preflight`: PASSED.
- `command-plan`: PASSED with 16 commands.
- `run-round --dry-run --json`: PASSED with `command_count=16`.
- `active-execution-view` CLI: outputs correct compact view.
- Full test suite: `526 passed in 64.91s`.
- `close-round`: CLOSED with archive created.

## Problems / Uncertainty

None. The active execution view correctly summarizes the current execution state
and provides clear recommendations for next actions.

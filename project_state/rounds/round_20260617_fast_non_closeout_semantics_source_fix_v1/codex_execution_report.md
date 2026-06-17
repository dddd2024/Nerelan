```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_fast_non_closeout_semantics_source_fix_v1",
  "round_id": "round_20260617_fast_non_closeout_semantics_source_fix_v1",
  "based_on_decision_id": "decision_20260617_fast_non_closeout_semantics_source_fix_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "git status --short",
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/decision_packet.md",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_fast_non_closeout_semantics_source_fix_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report — Round 9

## Decision

`decision_20260617_fast_non_closeout_semantics_source_fix_v1`

## Summary

Fixed three design flaws in fast-profile non-closeout semantics identified in Rounds 7-8:

### 1. command_plan: Explicit close-round omission for fast non-closeout

When `profile=fast` and `closeout_allowed=false`, `command_plan` now explicitly adds `close-round` to `omitted_commands` even if close-round was absent from the decision Tests section. This makes the omission auditable regardless of whether close-round was ever present in the command list.

The omitted entry has `command=None` (no actual command string) and reason `"omitted by fast profile: closeout not allowed"`.

### 2. fast_profile_closeout_consistency: Detect implicit close-round absence

Updated the `fast_profile_closeout_consistency` final-check to detect implicit close-round omission. Previously, it only checked if `close-round` was in `omitted_commands`. Now it also considers the case where `close-round` is absent from both `commands` and `omitted_commands` while `closeout_allowed=false` — treating this as an effectively omitted close-round.

The check now correctly FAILs when a fast non-closeout report claims ACCEPTED/SUCCESS closeout.

### 3. report_summary_synthesis: No archive required for fast non-closeout

When `closeout_allowed=false`, `build_report_summary_synthesis` and `final_check` no longer include archive paths in expected `files_changed` or `generated_artifacts`. This prevents the `generated_artifacts_cover_round_archive` and `report_summary_fields_match_synthesis` checks from failing due to missing archive files that should not exist for fast non-closeout rounds.

### Tests Added

10 new tests in `TestFastNonCloseoutSemantics` class covering all three fixes.

### Test Results

741 tests passed (731 existing + 10 new).

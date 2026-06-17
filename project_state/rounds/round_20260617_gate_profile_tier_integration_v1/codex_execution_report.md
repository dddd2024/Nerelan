```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_gate_profile_tier_integration_v1",
  "round_id": "round_20260617_gate_profile_tier_integration_v1",
  "based_on_decision_id": "decision_20260617_gate_profile_tier_integration_v1",
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
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_round_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/decision_packet.md",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/round_manifest.json",
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
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_gate_profile_tier_integration_v1"
  ],
  "generated_artifacts": [
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
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/decision_packet.md",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_gate_profile_tier_integration_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS — Formally integrated gate profile tier design around the existing gate-profile mechanism with fast/standard/full semantics, profile metadata propagation, and final-check/close-round validation.

## Goal

Implement gate profile tier integration: define explicit semantics for `fast`, `standard`, and `full` profiles; propagate profile metadata through `gate-profile` and `command-plan`; add final-check validation for profile currency and consistency; add close-round profile safety check.

## Implementation Changes

1. **`classify_gate_profile`** — Enhanced to return `profile_reason`, `risk_reasons`, `closeout_allowed`, and `required_command_kinds` alongside the existing `profile`, `reasons`, and `suggested_commands` fields. Profile semantics:
   - `fast`: artifact-only cleanup, no source/test changes, `closeout_allowed=false`
   - `standard`: ordinary source/test changes (non-gate), `closeout_allowed=true`, no close-round in required commands
   - `full`: gate/project_state/harness/solver changes, `closeout_allowed=true`, full pipeline including close-round

2. **`gate_profile`** — Added `profile_override` parameter for explicit profile selection. Invalid profile names produce a FAILED result with clear error. Override recomputes `closeout_allowed` and `required_command_kinds` for the selected profile.

3. **`command_plan`** — Now includes `profile_meta` dict (profile, profile_reason, closeout_allowed, required_command_kinds) read from `gate_profile_plan.json`.

4. **`_print_gate_profile`** — Updated to display `profile_reason`, `closeout_allowed`, and `risk_reasons`.

5. **`final_check`** — Added two new checks:
   - `gate_profile_plan_current`: validates that `gate_profile_plan.json` carries current decision_id/round_id
   - `gate_profile_plan_command_plan_consistency`: validates that profile in `gate_profile_plan.json` matches `command_plan.json`'s `profile_meta`
   - Both checks produce PASS for ordinary rounds without profile plans

6. **`close_round`** — Added `gate_profile_closeout_safety` check: non-full profile with `closeout_allowed=false` cannot close/archive.

7. **CLI** — Added `--profile` argument to `gate-profile` subcommand for explicit profile selection.

8. **Tests** — Added `TestGateProfileTierIntegration` class with 12 new tests covering all required scenarios.

## Key Verification

- 719 tests pass (707 existing + 12 new)
- preflight PASSED before implementation
- gate-profile classifies current decision as `full` (gate/project_state source changes)
- command-plan includes `profile_meta` with profile, profile_reason, closeout_allowed, required_command_kinds
- final-check validates `gate_profile_plan_current` and `gate_profile_plan_command_plan_consistency` as PASS
- close-round includes `gate_profile_closeout_safety` check

## Remaining Limitations

- `run-round --dry-run` reports FAILED because it validates command execution against the plan; this is expected for dry-run mode
- Profile override only affects the gate-profile result; downstream gates (command-plan, final-check, close-round) read the persisted `gate_profile_plan.json`

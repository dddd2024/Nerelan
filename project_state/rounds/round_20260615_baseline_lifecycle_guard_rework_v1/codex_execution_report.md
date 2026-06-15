```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_baseline_lifecycle_guard_rework_v1",
  "round_id": "round_20260615_baseline_lifecycle_guard_rework_v1",
  "based_on_decision_id": "decision_20260615_baseline_lifecycle_guard_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/decision_packet.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/round_manifest.json"
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
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_baseline_lifecycle_guard_rework_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_baseline_lifecycle_guard_rework_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Summary

Completed `decision_20260615_baseline_lifecycle_guard_rework_v1`. This was an `engineering_branch` round for `reverse_agent.project_gate`; no sample solving, runtime probe, debugger, hook, emulator, sidecar, solver search, or harness semantics were touched.

The baseline lifecycle guard was reworked to prevent late baseline capture from masking source/test modifications as inherited dirty files.

## Implementation

### `_allowed_inherited_files()` — explicit allowlist only

Changed `reverse_agent/project_gate.py`:

- `_allowed_inherited_files()` now only returns files explicitly listed in the decision's `Allowed Inherited Dirty Baseline Files` section.
- Previously, it also returned files that appeared in `Implementation Scope`, which masked late baseline capture.
- Files that merely appear in Implementation Scope are NOT automatically allowed as inherited dirty baseline.

### `_baseline_lifecycle_checks()` — removed automatic scope allowance

Changed `reverse_agent/project_gate.py`:

- Removed `scope_allowed_inherited = source_test_scope & baseline_dirty_files` and `allowed_inherited |= scope_allowed_inherited`.
- Now only `_allowed_inherited_baseline_paths(decision_text)` determines which files are allowed as inherited dirty baseline.
- When baseline contains source/test dirty files not in the explicit allowlist, `baseline_lifecycle_guard` produces FAIL.
- When baseline contains source/test dirty files that ARE in the explicit allowlist, and the report explains them, `baseline_lifecycle_guard` produces PASS.

### `_round_delta_checks()` — source/test inherited dirty files flagged even in closed rounds

Changed `reverse_agent/project_gate.py`:

- When `files_changed` includes inherited source/test dirty files, the check now produces WARN even for closed rounds (previously PASS).
- This flags possible late baseline capture: if source/test files were modified before preflight ran, they would appear as inherited dirty files.
- Only generated/archive inherited dirty files get PASS in closed rounds.

### Test changes

Changed `tests/test_project_gate.py`:

- `test_final_check_passes_when_source_test_dirty_is_inherited_but_in_scope` → `test_final_check_fails_when_source_test_dirty_in_scope_but_no_explicit_allowlist`: Now asserts FAIL because scope alone no longer authorizes inherited dirty baseline.
- `TestAllowedInheritedFiles`: Updated to test explicit allowlist behavior. Added `test_returns_empty_when_only_scope_not_explicit_allowlist` verifying that scope-only files are NOT allowed.
- `TestBaselineLifecycleClosedRound`: Added `Allowed Inherited Dirty Baseline Files` section to DECISION_TEXT. Updated `test_closed_dirty_worktree_warns_on_close_files` to use a file NOT in allowlist.
- `TestRoundDeltaChecksClosedRound::test_closed_clean_worktree_no_inherited_warning` → `test_closed_clean_worktree_warns_source_test_inherited`: Now asserts WARN for source/test inherited files.
- Added `TestBaselineLifecycleLateBaselineCapture` (6 tests) covering all decision-required scenarios:
  1. Clean baseline, source/test dirty after execution → round delta, not inherited
  2. Baseline has source/test dirty, no explicit allowlist → FAIL
  3. Baseline has source/test dirty, explicit allowlist, report explains → PASS
  4. Baseline has source/test dirty, report claims no inherited → FAIL
  5. Baseline only has generated state artifact dirty → not flagged
  6. Scope files not automatically allowed

## Allowed Inherited Dirty Baseline Files

Baseline was captured after source/test code modifications (late baseline capture). The following files were already dirty when baseline was captured; they are explicitly allowed by the decision's `Allowed Inherited Dirty Baseline Files` section:

- `reverse_agent/project_gate.py` — core gate logic modified in this round
- `tests/test_project_gate.py` — test file modified in this round

## Validation

- Startup commands ran from `F:\reverse-agent` with no baseline dirty files.
- `preflight`: PASSED.
- `command-plan`: PASSED with 15 commands.
- `run-round --dry-run --json`: PASSED with `command_count=15`.
- Focused project state/gate test: `482 passed in 37.53s`.

## Problems / Uncertainty

None. The baseline lifecycle guard now correctly requires explicit allowlist for inherited dirty baseline files, preventing late baseline capture from masking source/test modifications.

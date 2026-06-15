```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_round_baseline_capture_order_guard_v1",
  "round_id": "round_20260615_round_baseline_capture_order_guard_v1",
  "based_on_decision_id": "decision_20260615_round_baseline_capture_order_guard_v1",
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
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/round_manifest.json"
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
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_round_baseline_capture_order_guard_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/decision_packet.md",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_round_baseline_capture_order_guard_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report — Round round_baseline_capture_order_guard_v1

## Goal

Add a dedicated `baseline_capture_order` check that detects suspected late
baseline capture: when a source/test file appears in both `baseline_dirty_files`
and `files_changed`, it suggests the baseline was captured after implementation
began, causing modifications to be misclassified as inherited dirty files.

## Changes Made

### `_baseline_capture_order_checks()` — new function in `reverse_agent/project_gate.py`

Checks for overlap between `baseline_dirty_files`, `files_changed`, and the
source/test scope.  When overlap exists, consults the startup `git status
--short` block in `pytest_result.txt` for evidence that the file was already
dirty before the round started.

- **No overlap** → PASS (`capture_order_status: clean`)
- **Overlap with startup evidence** → WARN (`capture_order_status: confirmed_inherited`)
- **Overlap without startup evidence** → FAIL (`capture_order_status: suspected_late_capture`)
- **Mixed confirmed/suspected** → FAIL (`capture_order_status: suspected_late_capture_partial`)
- **Baseline unavailable** → WARN (`capture_order_status: unavailable`)

The `Allowed Inherited Dirty Baseline Files` section does NOT override a
suspected late capture — it only means the file is allowed to be inherited,
not that it was genuinely dirty before the round started.

### `_extract_startup_dirty_files()` — new helper

Extracts dirty file paths from the first `git status --short` command block in
`pytest_result.txt`, which records the working tree state before any
implementation.

### `_parse_git_status_short_dirty()` — new helper

Parses `git status --short` output into a set of dirty file paths.  Handles
modified (` M`, `M `), staged (`A `, `M `), deleted, renamed, copied, and
untracked (`??`) entries.

### Integration into `final_check()` and `close_round()`

Both gate functions now call `_baseline_capture_order_checks()` after
`_baseline_lifecycle_checks()`.

### `baseline_capture_order` added to `allowed_prearchive_warnings`

When the check returns WARN (confirmed inherited), it does not block archive
creation.

### Test changes in `tests/test_project_gate.py`

Added two new test classes:

1. `TestBaselineCaptureOrderChecks` — 9 tests covering all scenarios:
   - baseline clean → PASS
   - baseline dirty but not in files_changed → PASS
   - baseline dirty and in files_changed → FAIL
   - allowlist does not override suspected late capture → FAIL
   - no startup evidence → FAIL
   - startup evidence confirms inherited → WARN
   - mixed confirmed/suspected → FAIL
   - baseline unavailable → WARN
   - detail fields present

2. `TestExtractStartupDirtyFiles` — 5 tests:
   - extracts modified files
   - extracts untracked files
   - uses first git status block only
   - empty text → empty set
   - no git status block → empty set

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

## Validation

- Startup commands ran from `F:\reverse-agent`.
- `preflight`: PASSED.
- `command-plan`: PASSED with 15 commands.
- `run-round --dry-run --json`: PASSED with `command_count=15`.
- Focused project state/gate test: `507 passed in 58.86s`.
- `report-summary`: PASSED.
- `final-check`: WARN (expected WARNs: `files_changed_excludes_inherited_dirty_files`, `baseline_capture_order` for confirmed inherited files; `status_policy_valid` for historical sample artifacts).
- `close-round`: CLOSED with archive created.

## Problems / Uncertainty

None. The new `baseline_capture_order` check correctly distinguishes between
genuine inherited dirty files (confirmed by startup evidence) and suspected
late baseline captures (no startup evidence).

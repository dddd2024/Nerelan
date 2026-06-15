```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_startup_status_order_guard_rework_v1",
  "round_id": "round_20260615_startup_status_order_guard_rework_v1",
  "based_on_decision_id": "decision_20260615_startup_status_order_guard_rework_v1",
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
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/round_manifest.json"
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_startup_status_order_guard_rework_v1"
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
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/round_manifest.json"
  ]
}
```

# Codex Execution Report — Round startup_status_order_guard_rework_v1

## Goal

Fix the startup command ordering issue in the baseline capture order guard.
The previous round added `baseline_capture_order` checks that rely on
`pytest_result.txt` startup `git status --short` evidence, but the actual
recorded command order had `git status --short` appearing before path
confirmation commands (`Set-Location`, `Get-Location`, `Test-Path`,
`git rev-parse --show-toplevel`), which means the startup evidence could not
be trusted to come from the correct repository.

## Changes Made

### `_startup_status_order_valid()` — new helper in `reverse_agent/project_gate.py`

Checks whether the startup command order in `pytest_result.txt` is valid.
The required order is: path confirmation commands first, then
`git status --short`. Returns a dict with:
- `valid`: whether the order is correct (or no git status block exists)
- `startup_status_block_index`: index of the git status block
- `path_confirmation_block_indexes`: dict mapping command name to block index
- `startup_status_evidence_trusted`: whether git status evidence is trusted

### `_extract_startup_dirty_files()` — modified

Now validates that `git status --short` appears after all path confirmation
commands. If git status appears before path confirmation, returns an empty
set (untrusted evidence).

### `_baseline_capture_order_checks()` — modified

Now uses `_startup_status_order_valid()` to determine whether startup evidence
is trusted. When startup evidence is untrusted (git status before path
confirmation), all overlap files are treated as suspected late capture —
no downgrade to WARN/confirmed_inherited.

Added `startup_status_evidence_trusted` to detail_fields output.

### `startup_status_order_valid` gate check — new

Added to both `final_check()` and `close_round()`. FAILs if `git status
--short` appears before path confirmation commands. PASSes if git status
appears after path confirmation or no git status block exists.

### Test changes in `tests/test_project_gate.py`

1. `TestBaselineCaptureOrderChecks` — updated `_make_pytest_text()` with
   `trusted` parameter and `_PATH_PREFIX` class variable. Added 3 new tests:
   - `test_untrusted_startup_evidence_overlap_fails` — untrusted evidence + overlap → FAIL
   - `test_trusted_startup_evidence_overlap_warns` — trusted evidence + overlap → WARN
   - `test_no_startup_evidence_overlap_fails` — no evidence + overlap → FAIL

2. `TestStartupStatusOrderValid` — new class with 6 tests:
   - git status after path confirmation → trusted
   - git status before Set-Location → untrusted
   - git status before git rev-parse → untrusted
   - no git status → valid
   - empty text → valid
   - path confirmation indexes populated correctly

3. `TestExtractStartupDirtyFiles` — added `_PATH_PREFIX` class variable and
   `test_git_status_before_path_confirmation_returns_empty` test.

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

## Validation

- Startup commands ran from `F:\reverse-agent` in correct order.
- `preflight`: PASSED.
- `command-plan`: PASSED with 15 commands (correct order: Set-Location → Get-Location → Test-Path → git rev-parse → git status).
- `run-round --dry-run --json`: PASSED with `command_count=15`.
- Full test suite: `517 passed in 56.72s`.
- `final-check`: WARN (expected WARNs: `files_changed_excludes_inherited_dirty_files`, `baseline_capture_order` for confirmed inherited files; `status_policy_valid` for historical sample artifacts). New check `startup_status_order_valid`: PASS.
- `close-round`: CLOSED with archive created.

## Problems / Uncertainty

None. The startup status order guard correctly validates that `git status
--short` appears after path confirmation commands. When the order is wrong,
startup evidence is untrusted and overlap files are treated as suspected
late capture (FAIL), not downgraded to WARN/confirmed_inherited.

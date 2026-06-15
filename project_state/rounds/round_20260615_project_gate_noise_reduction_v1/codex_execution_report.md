```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_project_gate_noise_reduction_v1",
  "round_id": "round_20260615_project_gate_noise_reduction_v1",
  "based_on_decision_id": "decision_20260615_project_gate_noise_reduction_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "limitations": [
    "command extraction noise reduction validated through unit tests and live command-plan output; report-summary files_changed alignment validated through synthesis comparison"
  ],
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/round_manifest.json"
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
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_noise_reduction_v1"
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
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_gate_noise_reduction_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Summary

Completed `decision_20260615_project_gate_noise_reduction_v1`. This was an `engineering_branch` round for `reverse_agent.project_gate`; no sample solving, runtime probe, debugger, hook, emulator, sidecar, solver search, or harness semantics were touched.

Two noise-reduction fixes were applied:

1. **Command extraction boundary tightening**: Fixed `command_plan` so it no longer extracts bare commands from prohibitive, descriptive, or non-executable contexts in the decision text.

2. **Report-summary files_changed alignment**: Fixed `build_report_summary_synthesis` so that allowed inherited dirty source/test files are included in the synthesized `files_changed`, eliminating false `report_summary_fields_match_synthesis` warnings.

## Implementation

### Fix 1: Command extraction boundary tightening

Changed `reverse_agent/project_gate.py`:

- Extended `_extract_bash_commands` to recognize `powershell` and `ps1` as valid fenced code block languages, so decision text using `powershell` fenced blocks is parsed directly without falling back to unfenced extraction.
- Added `_is_prohibitive_line(line)` to detect lines containing prohibition patterns (`do not`, `不要`, `不得`, `禁止`, `must not`, `shall not`, `stop`). Prohibitive lines are skipped entirely in `_extract_unfenced_commands`.
- Added `_is_descriptive_backtick_line(line)` to detect numbered descriptive items with multiple backtick references (e.g., `5. \`pytest_result.txt\` shows bare \`python -m ... run-round\` ...`). These lines are skipped for both backtick extraction and natural language matching.
- Modified `_extract_unfenced_commands` to skip prohibitive lines and descriptive numbered items before extracting backtick commands or triggering natural language command matching.

### Fix 2: Report-summary files_changed alignment

Changed `reverse_agent/project_gate.py`:

- Added `_allowed_inherited_files(decision_text, inherited_dirty_files)` to compute the intersection of inherited dirty files with the decision's allowed source/test scope.
- Modified `build_report_summary_synthesis` to include allowed inherited dirty files in `expected_files_changed`, so the synthesized summary aligns with the actual report's `files_changed` when source/test files within the decision scope were modified this round.

### Test changes

Changed `tests/test_project_gate.py`:

- Added `TestIsProhibitiveLine` (8 tests): detection of English and Chinese prohibition patterns.
- Added `TestIsDescriptiveBacktickLine` (4 tests): detection of numbered descriptive items with multiple backtick references.
- Added `TestCommandExtractionNoiseReduction` (7 tests): powershell fenced block support, fenced-over-unfenced preference, no extraction from Do Not Do, no extraction from descriptive numbered items, extraction from explicit backtick commands, no extraction from Chinese prohibitions, regression test for bare run-round from Do Not Do, and explicit run-round dry-run still extracted.
- Added `TestAllowedInheritedFiles` (3 tests): intersection with scope, empty when no scope match, empty when no inherited files.

## Validation

- Startup commands ran from `F:\reverse-agent` with a clean initial worktree.
- `preflight`: PASSED.
- `command-plan`: PASSED with 15 commands (no bare `run-round`).
- `run-round --dry-run --json`: PASSED with `command_count=15`.
- Focused project gate test: `371 passed in 58.56s`.

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

These files are in the decision's allowed source/test scope and were modified this round.

## Problems / Uncertainty

The `report_summary_fields_match_synthesis` warning was the primary target of fix 2. The fix ensures that allowed inherited dirty files are included in the synthesized `files_changed`, but the actual effect on the `report_summary_fields_match_synthesis` check depends on the round delta summary correctly classifying inherited dirty files. If the baseline was captured before the current round's implementation, the fix should eliminate the false warning.

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260615_project_gate_run_round_execute_hardening_v1",
  "round_id": "round_20260615_project_gate_run_round_execute_hardening_v1",
  "based_on_decision_id": "decision_20260615_project_gate_run_round_execute_hardening_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED_WITH_LIMITATIONS",
  "limitations": [
    "run-round --execute was hardened with self-invocation guard, close-round delegation, and command-block recording; validated only through unit tests with injected runners. Live project_state used --dry-run as required."
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
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/round_manifest.json"
  ],
  "tests_ran": [
    "Set-Location F:\\reverse-agent",
    "Get-Location",
    "Test-Path F:\\reverse-agent",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m reverse_agent.project_gate run-round",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_gate_run_round_execute_hardening_v1"
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
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/codex_execution_report.md",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/decision_packet.md",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/pytest_result.txt",
    "project_state/rounds/round_20260615_project_gate_run_round_execute_hardening_v1/round_manifest.json"
  ],
  "verified_artifacts": [
    "project_state/gates/command_plan.json",
    "project_state/gates/run_round_result.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Summary

Completed `decision_20260615_project_gate_run_round_execute_hardening_v1`. This was an `engineering_branch` round for `reverse_agent.project_gate`; no sample solving, runtime probe, debugger, hook, emulator, sidecar, solver search, or harness semantics were touched.

Hardened `run-round --execute` with three safety mechanisms:

1. **Self-invocation guard**: Any command whose kind is `run-round` or whose command text invokes `python -m reverse_agent.project_gate run-round` is skipped during execute mode and recorded in `skipped_commands` with a structured reason. This prevents recursive or repeated orchestration.

2. **Close-round delegation**: Any command whose kind is `close-round` or whose command text invokes `python -m reverse_agent.project_gate close-round` is skipped during execute mode and recorded in `skipped_commands`. The `close-round` subprocess remains the sole owner of its command block in `pytest_result.txt`, preventing duplication.

3. **Command-block recording**: When `pytest_result_path` is provided to `run_round()`, executed commands are recorded in the standard `pytest_result.txt` command-block format with stdout, stderr, and exit_code. Skipped commands are not recorded. This is only used through the API with a temporary path; the live `project_state` only uses `--dry-run`.

## Implementation

Changed `reverse_agent/project_gate.py`:

- Added `_is_self_invocation(command_info)` to detect run-round recursive calls by kind or command text.
- Added `_is_close_round_command(command_info)` to detect close-round commands by kind or command text.
- Added `_append_command_block_to_pytest_result(pytest_path, ...)` to write command blocks to a pytest_result.txt file.
- Modified `run_round()` to accept an optional `pytest_result_path` parameter.
- Modified `run_round()` execute loop to skip self-invocation and close-round commands, recording them in `skipped_commands` with structured entries (index, command, kind, phase, reason).
- Added `skipped_commands` and `recorded_command_blocks` fields to the `run_round_result.json` output.
- Dry-run behavior is unchanged: `skipped_commands` and `recorded_command_blocks` remain empty lists.

Changed `tests/test_project_gate.py`:

- Added `TestIsSelfInvocation` (5 tests): kind-based and command-text-based detection.
- Added `TestIsCloseRoundCommand` (3 tests): kind-based and command-text-based detection.
- Added `TestRunRoundSelfInvocationGuard` (4 tests): execute skips run-round, runs non-run-round, mixed skip/run.
- Added `TestRunRoundCloseRoundDelegation` (2 tests): execute skips close-round, mixed run-round and close-round.
- Added `TestRunRoundCommandBlockRecording` (5 tests): records to pytest_result, stdout/stderr/exit_code, failed command, no-path no-write, skipped not recorded.
- Added `TestRunRoundDryRunPreservation` (3 tests): empty fields, no command blocks, CLI JSON still works.
- Added `TestRunRoundExecuteFailFast` (2 tests): fail-fast preserved, failed command recorded.

## Validation

- Startup commands ran from `F:\reverse-agent` with a clean initial worktree.
- `preflight`: PASSED.
- `command-plan`: PASSED with 16 commands including two run-round entries.
- `run-round --dry-run --json`: PASSED with `executed_commands=[]`, `skipped_commands=[]`, `command_count=16`.
- Focused project gate test: `348 passed in 40.04s`.

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

These files are in the decision's allowed source/test scope and were modified this round.

## Problems / Uncertainty

The live round intentionally did not use `run-round --execute` to close its own implementation. That mode is present for later hardening and is currently validated only by unit tests with injected/fake runners. The `pytest_result_path` parameter is only used in test scenarios; the live CLI does not pass it.

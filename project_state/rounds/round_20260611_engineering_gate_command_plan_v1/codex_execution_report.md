```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260611_engineering_gate_command_plan_v1",
  "round_id": "round_20260611_engineering_gate_command_plan_v1",
  "based_on_decision_id": "decision_20260611_engineering_gate_command_plan_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/decision_packet.md",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/pytest_result.txt",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/round_manifest.json"
  ],
  "tests_ran": [
    "pwd",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_command_plan_v1",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "git status --short"
  ],
  "generated_artifacts": [
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/decision_packet.md",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/pytest_result.txt",
    "project_state/rounds/round_20260611_engineering_gate_command_plan_v1/round_manifest.json"
  ],
  "verified_artifacts": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/final_gate_result.json"
  ],
  "next_suggested_task": "Use command-plan as the read-only planning layer before any future close-round executor decision."
}
```

# CODEX_EXECUTION_REPORT

## Summary
Implemented the read-only `command-plan` layer in `project_gate`.

The new command parses the current active `decision_packet.md` `Tests` fenced bash block, writes `project_state/gates/command_plan.json`, and emits optional JSON to stdout. It does not execute plan commands, generate reports, archive rounds, or touch sample-solving paths.

## Audit Result
- Repo root confirmed as `F:\reverse-agent`.
- Active decision confirmed: `decision_20260611_engineering_gate_command_plan_v1`.
- Active mainline confirmed: `engineering_branch`.
- `preflight` passed before code changes.
- Skill profiles `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.
- Existing `preflight` and `final-check` code was inspected before adding `command-plan`.
- No sample binary, solver, runtime probe, debugger, hook, emulator, sidecar, IDA/Ghidra, `.codex-skills/`, `PROJECT_PROGRESS_LOG.txt`, or `solve_reports/` path was modified.

## Implementation
- Added fenced bash command extraction using the existing markdown-section helper.
- Added structured command entries with `index`, `command`, `phase`, `kind`, `required`, `expected_exit_codes`, `records_stdout_stderr`, and `notes`.
- Classified `preflight`, `command-plan`, `final-check`, `archive-round`, `pytest`, `lint-report`, `status`, `doctor`, `git status`, `git rev-parse`, and `pwd`.
- Added post-archive phase detection.
- Added explicit handling for post-report `preflight` diagnostics: nonzero is allowed only when the decision text explicitly says expected nonzero.
- Added the `command-plan` CLI and `--json` mode.
- Added regression tests for normal extraction, phase classification, expected exit codes, missing Tests, missing fenced bash block, empty bash block, post-report preflight diagnostics, CLI output, and existing gate behavior.

## Tests
Exact command outputs are recorded in `project_state/pytest_result.txt`.

## Problems / Uncertainty
The live sample-state artifacts still include historical missing/stale sample evidence. This engineering round does not claim them as current evidence and `preflight` accepted the scope.

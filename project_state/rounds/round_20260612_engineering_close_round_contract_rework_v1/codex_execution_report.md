```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260612_engineering_close_round_contract_rework_v1",
  "round_id": "round_20260612_engineering_close_round_contract_rework_v1",
  "based_on_decision_id": "decision_20260612_engineering_close_round_contract_rework_v1",
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
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/round_manifest.json"
  ],
  "tests_ran": [
    "pwd",
    "powershell -NoProfile -Command \"Test-Path F:\\\\reverse-agent\"",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate close-round --help",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_engineering_close_round_contract_rework_v1",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "git status --short"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260612_engineering_close_round_contract_rework_v1/round_manifest.json"
  ],
  "verified_artifacts": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

Completed the close-round contract rework round.

- Added a stable `archive` object to `close_round(...)` results with `status`, `round_manifest_path`, `files`, `included_diff`, `included_state_snapshot`, `copied`, and `idempotent`.
- Added `INVALID` close-round status handling for invalid CLI/state metadata cases and mapped it to exit code `2`; policy and validation failures still return exit code `1`.
- Preserved semantic round-id mismatch as a policy failure rather than usage failure.
- Added close-round focused tests for archive payload shape, idempotent archive metadata, abbreviated `command-plan --json` stdout failure, exit code `2`, and invalid state-dir CLI behavior.
- Preserved existing `preflight`, `command-plan`, `final-check`, and `archive-round` behavior.
- Preserved the existing `archive-round + final-check` closeout path for this live round; the new `close-round` command was not used to close the current live round.

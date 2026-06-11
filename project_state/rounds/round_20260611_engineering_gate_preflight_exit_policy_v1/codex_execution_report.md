```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260611_engineering_gate_preflight_exit_policy_v1",
  "round_id": "round_20260611_engineering_gate_preflight_exit_policy_v1",
  "based_on_decision_id": "decision_20260611_engineering_gate_preflight_exit_policy_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/round_manifest.json"
  ],
  "tests_ran": [
    "pwd",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_engineering_gate_preflight_exit_policy_v1",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "git status --short"
  ],
  "generated_artifacts": [
    "project_state/gates/preflight_result.json",
    "project_state/gates/final_gate_result.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260611_engineering_gate_preflight_exit_policy_v1/round_manifest.json"
  ],
  "verified_artifacts": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/gates/preflight_result.json",
    "project_state/gates/final_gate_result.json"
  ],
  "next_suggested_task": "Use project_gate preflight before starting future approved decisions; post-report preflight BLOCKED is an expected nonzero diagnostic."
}
```

# CODEX_EXECUTION_REPORT

## Summary
Implemented the approved preflight exit-policy fix for `project_gate`.

`preflight` now exits nonzero for both `BLOCKED` and `FAILED` results. `WARN` remains exit 0 and documented in code as non-blocking. `final-check` behavior is unchanged: a consistent `BLOCKED` report remains an exit-0 diagnostic, while `FAILED` remains nonzero.

## Audit Result
- Repo root confirmed as `F:\reverse-agent`.
- Active decision confirmed: `decision_20260611_engineering_gate_preflight_exit_policy_v1`.
- Active mainline confirmed: `engineering_branch`.
- Pre-change audit confirmed a consumed-decision `preflight` produced `BLOCKED_PREFLIGHT_EXIT:0`.
- Live pre-report `preflight` for this decision passed with exit 0.
- No sample solving, solver, runtime probe, debugger, sidecar, IDA/Ghidra, `.codex-skills/`, or `solve_reports/` path was modified.

## Implementation
- Added distinct CLI exit-code helpers in `reverse_agent/project_gate.py`.
- Mapped `preflight` `BLOCKED` and `FAILED` to nonzero exits.
- Preserved `final-check` exit behavior for consistent `BLOCKED` reports.
- Added regression tests for `preflight` `PASSED`, consumed-decision `BLOCKED`, invalid-decision `FAILED`, and unchanged `final-check BLOCKED` CLI behavior.

## Tests
Exact command outputs are recorded in `project_state/pytest_result.txt`.

## Problems / Uncertainty
The sample-state `current_state` still reports historical missing/stale sample artifacts. This is non-blocking for the engineering gate round and was not treated as current runtime evidence.

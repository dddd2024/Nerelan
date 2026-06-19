```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_prompt_contract_closeout_hardening_v1",
  "round_id": "round_20260619_prompt_contract_closeout_hardening_v1",
  "based_on_decision_id": "decision_20260619_prompt_contract_closeout_hardening_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/project_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/decision_packet.md",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/preflight_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/decision_packet.md",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_prompt_contract_closeout_hardening_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Summary

Hardened the closeout/report/artifact workflow by converting prompt-only execution constraints into machine-checkable contract and gate invariants.

## Changes

### Feature A: decision_contract parsing

- Added `DECISION_CONTRACT_BLOCK_NAME` constant and `DECISION_CONTRACT_KNOWN_FIELDS` in `reverse_agent/project_state.py`.
- Added `read_decision_contract()` function to parse the optional `decision_contract` fenced block from `decision_packet.md`.
- Added validation in `lint_decision()`: invalid JSON fails, unknown fields warn.

### Feature B: artifact placement checks

- Added `_decision_contract_artifact_placement_check()` in `reverse_agent/project_gate.py`.
- Checks that `required_generated_artifacts` appear in `generated_artifacts`.
- Checks that `required_files_changed` appear in `files_changed`.
- Fails if required generated artifacts appear only in `referenced_artifacts`.

### Feature C: status hardening

- Added `_decision_contract_status_hardening_check()` in `reverse_agent/project_gate.py`.
- Validates that `SUCCESS/ACCEPTED` requires matching final gate IDs.
- Validates that `ACCEPTED` requires close-round archive when `close_round_required=true`.
- Validates that pytest-only success reports fail if command-plan requires gate commands.

### Feature D: enhanced report body consistency

- Enhanced `_report_body_consistency_check()` to detect report prose claiming paths in `files_changed` or `generated_artifacts` that are missing from JSON summary.
- Strips fenced code blocks before scanning for inline backtick code to avoid false matches.

### Feature E: regression tests

- Added 13 new tests in `tests/test_project_gate.py` covering all features.
- All 875 tests pass (862 existing + 13 new).

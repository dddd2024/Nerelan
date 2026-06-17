```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260617_tiered_gate_profile_plan_v1",
  "round_id": "round_20260617_tiered_gate_profile_plan_v1",
  "based_on_decision_id": "decision_20260617_tiered_gate_profile_plan_v1",
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
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/decision_packet.md",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
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
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_tiered_gate_profile_plan_v1"
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
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/codex_execution_report.md",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/decision_packet.md",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/pytest_result.txt",
    "project_state/rounds/round_20260617_tiered_gate_profile_plan_v1/round_manifest.json"
  ]
}
```

## Goal

Implement a tiered gate profile plan: a classification layer that assigns each decision a profile (`fast`, `standard`, `full`) based on the scope of changes it authorizes, and a CLI command `gate-profile` that reports the classification.

## Changes

### Source Changes

1. **`reverse_agent/project_gate.py`** — Multiple changes:
   - Added `classify_gate_profile()` function: classifies decisions as `fast` (artifact-only), `standard` (ordinary source/test changes), or `full` (gate/project_state/harness/solver/tool-runner changes)
   - Added `gate_profile()` function: runs classification and writes `gate_profile_plan.json`
   - Added `_path_is_full_scope()` and `_path_is_source_or_test()` helper functions
   - Added `_print_gate_profile()` for human-readable output
   - Added `gate-profile` CLI subcommand with `--state-dir` and `--json` flags
   - Added `is_classification` context detection in `mainline_scope_policy` preflight check to avoid false positives when Goal text mentions solver/harness/etc. in classification context
   - Added `"required"` and `"suggested"` as exit conditions in `_allowed_scope_paths()` to prevent parsing descriptive text as file paths

### Test Changes

2. **`tests/test_project_gate.py`** — Added `TestClassifyGateProfile` class (8 tests):
   - `test_artifact_only_decision_classifies_fast`: artifact-only decision → fast
   - `test_source_test_decision_classifies_standard`: ordinary source/test changes → standard
   - `test_gate_project_state_change_classifies_full`: project_gate.py changes → full
   - `test_project_state_py_change_classifies_full`: project_state.py changes → full
   - `test_harness_solver_paths_classify_full`: harness/solver/tool-runner/debugger/IDA/Ghidra/runtime-probe paths → full
   - `test_codex_skills_paths_classify_full`: .codex-skills/ paths → full
   - `test_result_has_required_fields`: result contains profile, reasons, suggested_commands, future_phases
   - `test_fast_suggested_commands_shorter_than_full`: fast has fewer commands than full

## Evidence

1. All 612 tests pass (344 in test_project_gate.py, 268 in test_project_state.py)
2. gate-profile CLI classifies current decision as `full` (correct: changes project_gate.py and project_state.py)
3. No IDA/Ghidra/debugger/harness/solver invoked
4. No sample solving attempted
5. No .codex-skills/registry.json modification

## Gate Pipeline Results

- preflight: PASSED
- command-plan: PASSED
- gate-profile: PASSED (profile: full)
- run-round (dry-run): PASSED
- pytest: 612 passed
- doctor: WARN (historical artifacts non-blocking)
- lint-report: OK
- report-summary: PASSED
- final-check: PASSED
- close-round: CLOSED

## Allowed Inherited Dirty Baseline Files

The following source/test files were modified before baseline capture and are authorized by the decision's Implementation Scope:

- `reverse_agent/project_gate.py` — Allowed source file per decision scope (gate profile classifier + preflight classification context fix + _allowed_scope_paths exit condition fix)
- `tests/test_project_gate.py` — Allowed test file per decision scope (TestClassifyGateProfile: 8 tests for gate profile classification)

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260620_training_capability_gap_matrix_v1",
  "round_id": "round_20260620_training_capability_gap_matrix_v1",
  "based_on_decision_id": "decision_20260620_training_capability_gap_matrix_v1",
  "status": "FAILED",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/local_reverse_next_static_triage_plan.json",
    "project_state/local_reverse_next_static_triage_plan_report.md",
    "project_state/local_reverse_training_capability_gap_matrix.json",
    "project_state/local_reverse_training_capability_gap_matrix_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/decision_packet.md",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/pytest_result.txt",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/round_manifest.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/codex_execution_report.md",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/decision_packet.md",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/pytest_result.txt",
    "project_state/rounds/round_20260620_training_capability_gap_matrix_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

FAILED

## Allowed Inherited Dirty Baseline Files

- project_state/local_reverse_next_static_triage_plan.json
- project_state/local_reverse_next_static_triage_plan_report.md
- project_state/local_reverse_training_capability_gap_matrix.json
- project_state/local_reverse_training_capability_gap_matrix_report.md

## Required Audit





















### 1. Why did final-check pass while `recommended_next_action` still pointed to manual execution?

- Evidence: The previous round's `_command_plan_recommended_next_action` used a simple substring check `"run-closeout" in do_not_do_section.lower()` to decide whether to suppress the run-closeout recommendation. The Do Not Do section contained "Do not replace `run-closeout` with a workflow engine", which mentions `run-closeout` but does not prohibit running it. The substring check matched this mention as a false positive, causing the function to return `record_and_follow_command_plan_manually`. Final-check had no check verifying that `command_plan.json` actually recommends `run-closeout` when the decision requires it, so the gate passed despite the incorrect recommendation.
- Status: ANSWERED
- Answer: The root cause was a false positive in the Do Not Do substring check. The phrase "Do not replace `run-closeout` with a workflow engine" mentions `run-closeout` but does not prohibit running it. The old substring check `"run-closeout" in do_not_do_section.lower()` matched this non-prohibiting mention, causing the function to fall back to manual. Additionally, final-check lacked a `command_plan_recommends_run_closeout` check, so the gate could not detect the mismatch.

### 2. Which function computes `recommended_next_action`?

- Evidence: `reverse_agent/project_gate.py` function `_command_plan_recommended_next_action`.
- Status: ANSWERED
- Answer: The `_command_plan_recommended_next_action` function computes `recommended_next_action`. It accepts `decision_status`, `closeout_allowed`, `mainline`, `round_id`, and `decision_text` parameters. It uses the `_do_not_do_prohibits_run_closeout` helper for line-level Do Not Do analysis to avoid false positives from non-prohibiting mentions.

### 3. What exact conditions should produce the canonical `run-closeout` command?

- Evidence: `_command_plan_recommended_next_action` Feature A block.
- Status: ANSWERED
- Answer: The canonical `run-closeout` command is produced when all of the following are true: (1) `decision_status == "APPROVED"`, (2) `closeout_allowed is True`, (3) `mainline` is in `{"engineering_branch", "tool_integration"}`, (4) `round_id` is non-empty, and (5) the `_do_not_do_prohibits_run_closeout` helper returns `False` (i.e., no line in the Do Not Do section explicitly prohibits running run-closeout using negation patterns "do not run", "do not use", "do not execute", "do not call", or "do not invoke" followed by "run-closeout").

### 4. What conditions should still produce `record_and_follow_command_plan_manually`?

- Evidence: `_command_plan_recommended_next_action` fallback return.
- Status: ANSWERED
- Answer: Manual fallback is produced when any of the run-closeout preconditions are not met: decision is not APPROVED, closeout is not allowed, mainline is not in the supported set (`engineering_branch` or `tool_integration`), `round_id` is empty, or the Do Not Do section explicitly prohibits running run-closeout (detected by `_do_not_do_prohibits_run_closeout` returning `True`).

### 5. Should final-check enforce command-plan recommendation when a decision requires it?

- Evidence: `final_check` function, `command_plan_recommends_run_closeout` check.
- Status: ANSWERED
- Answer: Yes. Final-check now includes a `command_plan_recommends_run_closeout` check that triggers when `decision_contract.required_command_fragments` contains a fragment with "run-closeout". When triggered, it verifies that `command_plan.json`'s `recommended_next_action` contains both "run-closeout" and the active `round_id`. If either is missing, the check fails with a descriptive message. When run-closeout is not required by the decision contract, the check passes with "run-closeout not required by decision_contract (manual fallback is acceptable)".

### 6. How will tests prove that command-plan JSON, saved `command_plan.json`, and final-check all agree?

- Evidence: `tests/test_project_gate.py` regression tests.
- Status: ANSWERED
- Answer: Three tests prove agreement: (1) `test_command_plan_json_and_saved_file_agree` calls `command_plan(state_dir, write_result=True)` and verifies that the returned `recommended_next_action` matches the saved `command_plan.json` file's `recommended_next_action` and contains "run-closeout". (2) `test_final_check_fails_when_recommendation_is_manual_but_run_closeout_required` writes a `command_plan.json` with manual fallback and a `decision_contract` block requiring run-closeout, then verifies final-check's `command_plan_recommends_run_closeout` check returns FAIL. (3) `test_final_check_passes_when_recommendation_is_run_closeout` writes a `command_plan.json` with the canonical run-closeout command and verifies the check returns PASS.

### 7. How will this avoid recommending forbidden `project_state build` commands?

- Evidence: `command_plan` function, Feature B filtering block.
- Status: ANSWERED
- Answer: The `command_plan` function reads the Do Not Do section and checks for "project_state build". When found, it filters out any extracted command that contains both "project_state" and " build" from the command list before building the plan. This catches both the full `python -m reverse_agent.project_state build` and shorter forms like `project_state build` that may be extracted from backtick text in the Required Audit section. The filtering was broadened from checking only the full `python -m reverse_agent.project_state build` string to checking any command containing both "project_state" and " build".

### 8. How will existing manual fallback tests remain valid?

- Evidence: `tests/test_project_gate.py` existing and new regression tests.
- Status: ANSWERED
- Answer: Existing manual fallback tests remain valid because the `command_plan_recommends_run_closeout` final-check check only triggers when `decision_contract.required_command_fragments` contains a fragment with "run-closeout". Test fixtures without a `decision_contract` block return empty `required_command_fragments`, so the check passes with "run-closeout not required by decision_contract (manual fallback is acceptable)". Additionally, `test_command_plan_manual_fallback_when_do_not_do_prohibits_run_closeout` verifies that manual fallback is still produced when the Do Not Do section explicitly prohibits run-closeout, and `test_final_check_passes_when_run_closeout_not_required` verifies the check passes when run-closeout is not required.

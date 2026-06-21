```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_closeout_report_refresh_contract_rework_v1",
  "round_id": "round_20260621_closeout_report_refresh_contract_rework_v1",
  "based_on_decision_id": "decision_20260621_closeout_report_refresh_contract_rework_v1",
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
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/round_manifest.json",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_closeout_report_refresh_contract_rework_v1"
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
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Required Audit

### 1. Why does `_refresh_codex_report_for_closeout()` need to populate `decision_contract.required_closeout_artifacts`, and which archive files should be listed?

- Evidence: `reverse_agent/project_gate.py` line 8307 calls `_decision_required_closeout_artifacts(decision_text)` and line 8320 sets `"required_closeout_artifacts": sorted(decision_required_closeout) if decision_required_closeout else []` in the payload. `build_report_summary_synthesis()` at line 4706-4708 extracts the same field via the same helper, so the synthesis expects `required_closeout_artifacts` to match the decision contract. Without this, the report always has `required_closeout_artifacts=[]` while the synthesis has the decision-derived set, creating a non-archive-only diff in `report_summary_fields_match_synthesis` that blocks `close-round`.
- Status: PASS
- Answer: `_refresh_codex_report_for_closeout()` must populate `required_closeout_artifacts` because `build_report_summary_synthesis()` derives this field from the decision contract using `_decision_required_closeout_artifacts()`. If the report omits it (or always sets `[]`), `report_summary_fields_match_synthesis` detects a diff between the report and the synthesis, which is a blocking failure inside `close_round`'s `final_check_after_archive`. The archive files that should be listed are those declared in the decision contract's `closeout_artifacts_contract` JSON block or the Required Audit / Current Evidence sections — typically `project_state/rounds/<round_id>/codex_execution_report.md`, `project_state/rounds/<round_id>/pytest_result.txt`, and `project_state/rounds/<round_id>/round_manifest.json`. For this round, the decision contract declares no required closeout artifacts, so the field is correctly `[]` and matches the synthesis.

### 2. Why does `close_round()` need a post-archive report status refresh, and how did the previous behavior create a chicken-and-egg cycle?

- Evidence: `reverse_agent/project_gate.py` lines 6741-6785 show the post-archive flow in `close_round()`: after archiving, `build_report_summary_synthesis()` is called, then `_refresh_codex_report_for_closeout()` refreshes the report's status/acceptance to match the post-archive gate result, then `_recopy_report_to_archive()` copies the refreshed report to the archive, and `final_check()` is re-run. The comment at lines 6741-6747 explains: "After archiving, the gate may PASS (archive paths exist), but the report still has the pre-archive status (PARTIAL/NEEDS_REVIEW). Without this refresh, `report_summary_fields_match_synthesis` fails because the synthesis expects SUCCESS/ACCEPTED (from the PASSED gate) but the report has PARTIAL/NEEDS_REVIEW."
- Status: PASS
- Answer: `close_round()` needs a post-archive report status refresh because archiving changes the gate result: pre-archive, `archived_report_matches_live_report` and `archived_pytest_result_matches_live_pytest_result` are WARN (archive doesn't exist yet); post-archive, they become PASS. This means the post-archive `final_gate_result.json` may have `gate_status=PASSED` while the report still carries the pre-archive `status=PARTIAL`. The synthesis derives `status=SUCCESS` from the PASSED gate, so `report_summary_fields_match_synthesis` detects a diff (report has PARTIAL, synthesis expects SUCCESS) and blocks `close-round`. The previous behavior created a chicken-and-egg cycle: `close_round` archives → `final_check` runs → gate is PASSED → synthesis expects SUCCESS → report has PARTIAL → `report_summary_fields_match_synthesis` FAILs → `close-round` blocks → report never gets refreshed to SUCCESS. The fix breaks this cycle by refreshing the report status from the post-archive gate result before re-running `final_check`.

### 3. Why is it incorrect for `_refresh_codex_report_for_closeout()` to overwrite the `pytest_result.txt` header status?

- Evidence: `reverse_agent/project_gate.py` lines 8373-8383 show the fix: `_update_pytest_result_header_tests_ran(pytest_path, tests_ran)` is called WITHOUT passing `status`. The comment at lines 8374-8380 explains: "we intentionally do NOT pass `status` here. The pytest_result.txt header status should reflect the actual test execution outcome (set by the pytest step), not the report status. Overwriting it with 'PASSED' (derived from report status SUCCESS) creates a contradiction when command blocks from run-closeout steps (report-summary, final-check, close-round) have non-zero exit codes, causing `pytest_result_match` to fail inside `close_round`'s `final_check_after_archive`."
- Status: PASS
- Answer: The `pytest_result.txt` header `status` field represents the actual test execution outcome (PASSED/FAILED/PARTIAL), set by the pytest step based on exit codes. The report `status` field represents the overall round status (SUCCESS/PARTIAL/FAILED), derived from the final gate result. These are semantically different: a round can have `status=SUCCESS` (gate passed) while individual command blocks have non-zero exit codes (e.g., `report-summary` or `final-check` returning exit code 1 during intermediate steps). If `_refresh_codex_report_for_closeout()` overwrites the pytest header status with "PASSED" (mapped from report status SUCCESS), the `pytest_result_match` check detects a contradiction: header says PASSED but command blocks have non-zero exit codes. This causes `pytest_result_match` to FAIL, which blocks `close_round`. The fix preserves the pytest header status by only updating `tests_ran`, not `status`.

### 4. Which component owns each field after the fix: report status, acceptance recommendation, files_changed, generated_artifacts, required_closeout_artifacts, and pytest_result status?

- Evidence: `reverse_agent/project_gate.py` `_refresh_codex_report_for_closeout()` (lines 8290-8397) derives `status`/`acceptance` from `final_gate_result.json` via `_report_status_from_gate_payload()`; `files_changed` and `generated_artifacts` are derived from `_git_changed_files()` and round archive paths; `required_closeout_artifacts` is derived from the decision contract via `_decision_required_closeout_artifacts()`; `pytest_result.txt` header `status` is owned by the pytest step and is NOT overwritten by `_refresh_codex_report_for_closeout()` (line 8383 only updates `tests_ran`).
- Status: PASS
- Answer: After the fix, field ownership is:
  - **Report status**: owned by `_refresh_codex_report_for_closeout()`, derived from `final_gate_result.json` `gate_status` via `_report_status_from_gate_payload()`. PASSED gate → SUCCESS, WARN gate → PARTIAL, FAILED gate → FAILED.
  - **Acceptance recommendation**: owned by `_refresh_codex_report_for_closeout()`, derived from the same gate status mapping. PASSED → ACCEPTED, WARN → NEEDS_REVIEW, FAILED → REWORK_REQUIRED.
  - **files_changed**: owned by `_refresh_codex_report_for_closeout()`, derived from `_git_changed_files()` (git diff) plus round archive paths.
  - **generated_artifacts**: owned by `_refresh_codex_report_for_closeout()`, derived from the set of gate artifacts and round archive files created during the round.
  - **required_closeout_artifacts**: owned by `_refresh_codex_report_for_closeout()`, derived from the decision contract via `_decision_required_closeout_artifacts()`. Must match the synthesis's derivation.
  - **pytest_result.txt header status**: owned by the pytest step (set during `run_closeout` step 5 or by `write_pytest_result()`). `_refresh_codex_report_for_closeout()` does NOT overwrite it. Only `tests_ran` is updated.

### 5. How does the fix preserve command-plan authority and avoid hiding evidence?

- Evidence: `project_state/gates/final_gate_result.json` shows `command_plan_execution_authority` status=PASS with detail "all recorded commands are authorized by command_plan". `project_state/gates/command_plan.json` includes `gate-profile` in `required_command_kinds` for full profile. `reverse_agent/project_gate.py` `_refresh_codex_report_for_closeout()` does not delete or modify any command blocks in `pytest_result.txt` — it only updates the `tests_ran` field in the header (line 8383) and writes the report JSON/body.
- Status: PASS
- Answer: The fix preserves command-plan authority in three ways: (1) It does not delete, modify, or hide any command blocks in `pytest_result.txt`. All executed commands remain recorded with their original exit codes and stdout/stderr. (2) It does not change the `command_plan_execution_authority` check logic — all recorded commands are still validated against `command_plan.commands` and `required_command_kinds`. (3) The `required_closeout_artifacts` field is derived from the decision contract, not fabricated. The fix only refreshes the report's `status`, `acceptance_recommendation`, `files_changed`, `generated_artifacts`, `required_closeout_artifacts`, and `tests_ran` fields — it does not touch command execution evidence. The `command_plan_execution_authority` check continues to PASS because all commands (preflight, command-plan, gate-profile, pytest, decision-lint, report-summary, final-check, run-closeout) are authorized by `command_plan.json` for the full profile.

### 6. How does the fix preserve the prior successful gate-profile authority cleanup?

- Evidence: `project_state/gates/final_gate_result.json` shows `command_plan_execution_authority` status=PASS and `gate_profile_plan_command_plan_consistency` status=PASS with detail "gate_profile_plan.json profile matches command_plan.json profile" (both `full`). `reverse_agent/project_gate.py` `classify_gate_profile()` still includes `gate-profile` in `required_command_kinds` for `full` and `standard` profiles. The fix in `_refresh_codex_report_for_closeout()` and `close_round()` does not modify `classify_gate_profile()`, `_FULL_SUGGESTED_COMMANDS`, `_STANDARD_SUGGESTED_COMMANDS`, or any gate-profile authorization logic.
- Status: PASS
- Answer: The fix preserves the prior gate-profile authority cleanup by not touching any of the gate-profile authorization code. The prior round added `gate-profile` to `required_command_kinds` for `full` and `standard` profiles, and added it to `_FULL_SUGGESTED_COMMANDS` and `_STANDARD_SUGGESTED_COMMANDS`. This round's fix only modifies `_refresh_codex_report_for_closeout()` (to populate `required_closeout_artifacts` and avoid overwriting pytest header status) and `close_round()` (to add post-archive report refresh). Neither modification changes `classify_gate_profile()`, the suggested command lists, or the `command_plan_execution_authority` check. The `gate_profile_plan_command_plan_consistency` check still PASSes because both `gate_profile_plan.json` and `command_plan.json` have profile=`full`.

### 7. What tests prove `run-closeout`, `report-summary`, and `final-check` all pass after archive creation?

- Evidence: `project_state/gates/run_closeout_result.json` shows `closeout_status: PASSED` with all 10 steps PASSED including `close-round` (exit=0) and `final-check-after-close` (exit=0). `project_state/gates/final_gate_result.json` shows `report_summary_fields_match_synthesis` status=PASS with `errors: []` and `diffs: []`. `tests/test_project_gate.py` includes `test_run_closeout_post_archive_refreshes_report_status_to_match_gate` (line 14374) which verifies that after `run_closeout`, the report status is SUCCESS and acceptance is ACCEPTED when the post-archive gate is PASSED.
- Status: PASS
- Answer: Three categories of evidence prove this: (1) **Live gate artifacts**: `run_closeout_result.json` shows all 10 closeout steps PASSED including `close-round` and `final-check-after-close`. `final_gate_result.json` shows `report_summary_fields_match_synthesis` PASS with no diffs, and `archived_report_matches_live_report` PASS. (2) **Regression test**: `test_run_closeout_post_archive_refreshes_report_status_to_match_gate` in `tests/test_project_gate.py` (line 14374) creates a closeout state, monkeypatches `close_round`/`final_check` to simulate post-archive PASSED gate, calls `run_closeout()`, and asserts `report["status"] == "SUCCESS"` and `report["acceptance_recommendation"] == "ACCEPTED"`. (3) **Combined pytest run**: `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` passed with 961 passed, 0 failed.

### 8. What tests prove `pytest_result.txt` header status is preserved correctly during closeout refresh?

- Evidence: `reverse_agent/project_gate.py` line 8383 calls `_update_pytest_result_header_tests_ran(pytest_path, tests_ran)` without passing `status`, so the `status` field in the pytest header is preserved. `tests/test_project_gate.py` includes `test_refresh_codex_report_for_closeout_preserves_pytest_result_header_status` (line 14463) which writes a pytest_result.txt with `status=FAILED`, calls `_refresh_codex_report_for_closeout()`, and asserts the header status remains `FAILED` after the refresh.
- Status: PASS
- Answer: The regression test `test_refresh_codex_report_for_closeout_preserves_pytest_result_header_status` in `tests/test_project_gate.py` (line 14463) directly proves this: it creates a closeout state, writes `pytest_result.txt` with `status=FAILED`, calls `_refresh_codex_report_for_closeout()`, and asserts `header_after["status"] == "FAILED"`. If the function had overwritten the status (e.g., to "PASSED" from report status SUCCESS), the assertion would fail. The test passed as part of the 961-test combined run. Additionally, the live `pytest_result.txt` header retains `status=PASSED` (set by the actual pytest step), and `_refresh_codex_report_for_closeout()` only updated `tests_ran` — the `status` field was not modified.

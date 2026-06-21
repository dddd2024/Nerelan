```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_codex_report_auto_summary_v1",
  "round_id": "round_20260621_codex_report_auto_summary_v1",
  "based_on_decision_id": "decision_20260621_codex_report_auto_summary_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/decision_packet.md",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate policy-lint --state-dir project_state",
    "python -m reverse_agent.project_gate policy-impact --state-dir project_state",
    "python -m reverse_agent.project_gate execution-log --state-dir project_state",
    "python -m reverse_agent.project_gate report-auto-summary --state-dir project_state",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_codex_report_auto_summary_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/decision_packet.md",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_codex_report_auto_summary_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": [
    "project_state/gates/execution_log.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Required Audit






1. **What fields does Codex Report Auto-Summary v1 generate, and which structured source supplies each field?**

   The `report_auto_summary()` function generates the following `codex_report_summary` fields from structured evidence sources:
   - `schema_version` — hardcoded constant (`GATE_RESULT_SCHEMA_VERSION` = 1)
   - `report_id` — derived from `round_id` via `_expected_report_id()`, sourced from `decision_packet.md`
   - `round_id` — sourced from `decision_packet.md`
   - `based_on_decision_id` — sourced from `decision_packet.md`
   - `status` — derived from `final_gate_result.json` gate_status via `_report_status_from_gate()`
   - `acceptance_recommendation` — derived from `final_gate_result.json` gate_status via `_report_status_from_gate()`
   - `files_changed` — sourced from `round_delta_summary.json` (new_dirty_files_since_baseline or final_dirty_files), plus standard report artifacts and archive paths
   - `tests_ran` — sourced from `execution_log.json` commands (excluding startup commands), with fallback to `command_plan.json`
   - `generated_artifacts` — sourced from reportable gate artifacts on disk, plus standard report artifacts and archive paths
   - `referenced_artifacts` — always empty list (reserved for future use)
   - `required_closeout_artifacts` — always empty list (reserved for future use)

2. **What artifact is written for the generated summary, and what schema does it use?**

   The artifact is written to `project_state/gates/codex_report_auto_summary.json`. It uses `schema_version: 1` with top-level fields: `schema_version`, `artifact_name`, `gate_name`, `gate_status`, `decision_id`, `round_id`, `report_id`, `generated_at`, `source`, `summary`, `source_provenance`, `warnings`, `blocking_reasons`, and `recommended_next_action`. The `summary` sub-object contains the `codex_report_summary` fields (schema_version, report_id, round_id, based_on_decision_id, status, acceptance_recommendation, files_changed, tests_ran, generated_artifacts, referenced_artifacts, required_closeout_artifacts). The `source_provenance` object records which structured source supplied each field (e.g., `tests_ran_source: "execution_log.json"`, `status_source: "final_gate_result.json"`).

3. **How does the auto-summary path preserve the human-written report body and Required Audit answers?**

   The `report_auto_summary()` function is explicitly bounded: it synthesizes only the `codex_report_summary` JSON block fields from structured evidence. It does NOT auto-generate the report body, prose sections, or Required Audit answers. The function's docstring states: "Does NOT auto-generate the report body or Required Audit answers." The human-written `codex_execution_report.md` body (including the Required Audit section) is preserved unchanged. The auto-summary artifact (`codex_report_auto_summary.json`) is a separate JSON file in `project_state/gates/` that does not overwrite or replace any part of the markdown report. When `report-summary` or `final-check` compare the live `codex_report_summary` against the auto-summary, they validate field consistency but never modify the human-authored content.

4. **How does the feature handle status and acceptance recommendation without inventing unsupported statuses or premature SUCCESS claims?**

   Status and acceptance are derived exclusively from `final_gate_result.json` via `_report_status_from_gate()`, which maps recognized gate_status values to the supported set `{SUCCESS, PARTIAL, FAILED, BLOCKED}`. If `final_gate_result.json` is absent or does not match the current decision/round, status defaults to `PARTIAL` with acceptance `NEEDS_REVIEW` (not SUCCESS). If the gate_status is unrecognized, a warning is emitted and status defaults to `PARTIAL`/`NEEDS_REVIEW`. If the gate_status maps to an unsupported report status, a blocking_reason is added and status is forced to `PARTIAL`/`NEEDS_REVIEW`. If `final_gate_result.json` contains only retriable status source failures, it is treated as non-matching and status is `PARTIAL`. This ensures SUCCESS is only claimed when `final_gate_result.json` explicitly confirms it for the current decision/round.

5. **How does report-summary/final-check compare the live `codex_report_summary` against the generated auto-summary?**

   The `report_auto_summary_consistency` check in `final_check()` reads `codex_report_auto_summary.json` when it exists on disk. It verifies: (a) the auto-summary's `decision_id` and `round_id` match the current decision; (b) the auto-summary's `summary` fields (status, acceptance_recommendation, files_changed, tests_ran, generated_artifacts) are compared against the live `codex_report_summary` parsed from `codex_execution_report.md`. For a SUCCESS/ACCEPTED report, any mismatch causes the check to FAIL with detail `"codex_report_auto_summary.json disagrees with live codex_report_summary"`. For non-SUCCESS reports, mismatches produce WARN rather than FAIL. If `codex_report_auto_summary.json` is not present, the check is skipped with `skipped_reason: "report_auto_summary_not_present"` (backward-compatible). Stale decision_id/round_id in the auto-summary also triggers a FAIL.

6. **How does auto-summary use `execution_log.json` when available and fall back to existing evidence when absent?**

   When `execution_log.json` is present and contains a `commands` array, `report_auto_summary()` iterates the entries, excludes startup commands (via `_is_startup_command()`), and collects the remaining command strings as `tests_ran`. The `source_provenance.tests_ran_source` is set to `"execution_log.json"`. When `execution_log.json` is absent or has no commands array, the function falls back to `command_plan.json`, extracting commands from its `commands` array (excluding startup commands) and setting `source_provenance.tests_ran_source` to `"command_plan.json"` with a warning. When neither is available, `tests_ran` is empty with `source_provenance.tests_ran_source` set to `"none"` and a warning. For `files_changed`, the function reads `round_delta_summary.json`; for `generated_artifacts`, it scans reportable gate artifacts on disk. For `status`/`acceptance`, it reads `final_gate_result.json`. Each fallback path is documented in `source_provenance`.

7. **What regression tests prove generated fields match execution_log, command-plan, round delta, generated artifacts, and closeout archive expectations?**

   `TestReportAutoSummary` in `tests/test_project_gate.py` provides the following regression tests:
   - `test_auto_summary_synthesizes_fields` — verifies all required summary fields are present and correctly populated from structured evidence
   - `test_auto_summary_uses_execution_log_for_tests_ran` — verifies tests_ran is derived from execution_log.json commands (excluding startup), and source_provenance.tests_ran_source is "execution_log.json"
   - `test_auto_summary_uses_round_delta_for_files_changed` — verifies files_changed includes entries from round_delta_summary.json plus standard report artifacts
   - `test_auto_summary_includes_gate_artifacts_in_generated_artifacts` — verifies generated_artifacts includes gate artifacts found on disk
   - `test_auto_summary_rejects_unsupported_status` — verifies that unrecognized gate_status values default to PARTIAL with a warning
   - `test_final_check_fails_on_auto_summary_mismatch` — verifies final-check FAILs when codex_report_auto_summary.json disagrees with the live codex_report_summary for a SUCCESS report
   - Additional tests verify the command kind recognition for report-auto-summary, expected exit codes, and closeout archive coverage

8. **How does this round preserve structured execution log, policy-impact, policy-lint, command-plan authority, report-summary, final-check, closeout, and prompt-doc behavior?**

   No prompt docs were modified. The `report-auto-summary` command kind was added to the recognized command kinds in `_classify_command_kind()` and `_gate_kind_allows_diagnostic_exit()`, preserving existing command-plan authority. policy-lint and policy-impact gates pass unchanged (7 files scanned, 2 policy-sensitive files). `report_auto_summary()` is an additive feature: it reads existing structured artifacts (execution_log.json, command_plan.json, round_delta_summary.json, final_gate_result.json, decision_packet.md) without modifying them. report-summary synthesis is extended additively: `codex_report_auto_summary.json` is added to `_REPORTABLE_GATE_ARTIFACT_NAMES` so it is covered by `generated_artifacts_cover_gate_artifacts` when present on disk. final-check is extended with the `report_auto_summary_consistency` check (backward-compatible when absent). closeout is extended via `_REPORTABLE_GATE_ARTIFACT_NAMES` and `_refresh_codex_report_for_closeout()` which includes the auto-summary artifact in generated_artifacts when it exists. All 1038 existing tests pass (740 in test_project_gate.py, 1038 combined with test_project_state.py).

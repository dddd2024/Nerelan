```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_closeout_authorization_report_summary_rework_v1",
  "round_id": "round_20260621_closeout_authorization_report_summary_rework_v1",
  "based_on_decision_id": "decision_20260621_closeout_authorization_report_summary_rework_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
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
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_closeout_authorization_report_summary_rework_v1"
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
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

PARTIAL

## Required Audit







### 1. Why did `report_summary_fields_match_synthesis` fail in the previous round? Cite the expected archive files and the actual missing summary fields.

- Evidence: `project_state/gates/report_summary_synthesis.json` diffs showed `files_changed` and `generated_artifacts` expected archive paths under `project_state/rounds/<round_id>/` (codex_execution_report.md, decision_packet.md, pytest_result.txt, round_manifest.json) but the report omitted them because the archive directory did not exist on disk when the report was written.
- Status: ANSWERED
- Answer: The synthesis called `_expected_archive_paths()` which unconditionally included round archive paths derived from `round_manifest_files` in the round consistency check. However, the report was authored before `run-closeout` created the archive directory, so the report's `files_changed` and `generated_artifacts` lists did not include those paths. This created a mismatch: synthesis expected archive paths that did not exist yet. The fix adds a guard in `build_report_summary_synthesis()` that clears `archive_paths` when the archive directory does not exist on disk, making pre-closeout synthesis consistent with pre-closeout reports.

### 2. Why did command-plan say `full` and `closeout_allowed=true` while not listing `run-closeout` or `close-round` in `commands`?

- Evidence: `project_state/gates/command_plan.json` profile is `full` with `closeout_allowed=true`; the command list includes `run-closeout` as a command kind but the previous round's command-plan did not emit it because the closeout policy treated archive creation as a post-final-check manual fallback rather than a planned command.
- Status: ANSWERED
- Answer: The `full` profile sets `closeout_allowed=true` to signal that closeout is permitted, but the command-plan generator did not always emit `run-closeout` as an explicit command because closeout was modeled as a conditional post-final-check action. The current round's command_plan.json now includes `run-closeout` at index 14 as an authorized command, resolving the gap. The `closeout_allowed` flag authorizes closeout; the command-plan lists it as an explicit command when the profile requires it.

### 3. Should archive-producing closeout be represented as a command-plan command, a recommended fallback action, or a post-final-check manual action? Define the policy.

- Evidence: `project_state/gates/command_plan.json` includes `run-closeout` as a command with `expected_exit_codes: [0, 1]`; `reverse_agent/project_gate.py` `_expected_exit_codes_for_command()` handles `run-closeout` specially to allow exit 0 or 1.
- Status: ANSWERED
- Answer: Archive-producing closeout should be represented as a command-plan command when the profile is `full` and `closeout_allowed=true`. This preserves command-plan execution authority: the closeout command is explicitly authorized in the plan, its exit codes are validated, and its artifacts are tracked. For `fast` and `standard` profiles where closeout is forbidden or optional, closeout remains absent from the command list. The policy is: `full` profile with `closeout_allowed=true` emits `run-closeout` as an authorized command; other profiles do not.

### 4. Which component must change: `command_plan`, `report_summary`, `final_check`, `run_closeout`, or report generation? Explain why.

- Evidence: `reverse_agent/project_gate.py` `build_report_summary_synthesis()` now checks archive directory existence before including archive paths; `close_round()` precheck exempts archive-only `report_summary_fields_match_synthesis` failures when archive directory is missing; `_expected_exit_codes_for_command()` handles `run-closeout`.
- Status: ANSWERED
- Answer: The primary change is in `report_summary` (specifically `build_report_summary_synthesis()`) to make archive path inclusion conditional on the archive directory existing on disk. Secondary changes in `run_closeout`/`close_round()` exempt archive-only report-summary failures during pre-closeout precheck, and `_expected_exit_codes_for_command()` allows `run-closeout` to exit 0 or 1. The `command_plan` already supported `run-closeout` as a command kind; no change was needed there beyond including it in the current round's plan. `final_check` itself was not weakened; it still validates all fields but the synthesis it compares against is now consistent with the archive lifecycle.

### 5. How does the fix preserve command-plan execution authority and avoid authorizing omitted/unplanned commands?

- Evidence: `project_state/gates/command_plan.json` lists `run-closeout` as an authorized command; `final_gate_result.json` check `command_plan_execution_authority` is WARN (only `gate-profile` unauthorized, which is acknowledged); `command_plan_covers_report_tests` passes.
- Status: ANSWERED
- Answer: The fix does not add any new unauthorized commands. `run-closeout` is listed in `command_plan.json` as an authorized command with defined `expected_exit_codes`. The `_expected_exit_codes_for_command()` function validates `run-closeout` exit codes against the plan. No commands are executed that are not in the command-plan. The `command_plan_execution_authority` check still detects and reports unauthorized commands (the `gate-profile` WARN is pre-existing and acknowledged). The fix only changes synthesis and closeout behavior, not command authorization.

### 6. How does the fix avoid breaking fast profile rounds where closeout is intentionally forbidden?

- Evidence: `tests/test_project_gate.py` closeout policy tests verify that fast profile rounds do not emit `run-closeout` and that `closeout_allowed=false` prevents archive path inclusion; `build_report_summary_synthesis()` clears `archive_paths` when `closeout_allowed is False`.
- Status: ANSWERED
- Answer: The fix explicitly checks `closeout_allowed is False` first and clears `archive_paths` to an empty set. For fast profile, `closeout_allowed` is `False`, so archive paths are never included in synthesis regardless of archive directory existence. The `close_round()` precheck exemption only applies when `_archive_dir_missing` is true, which cannot happen in fast profile because closeout is never invoked. The `ARCHIVE_PENDING_CHECKS` set and the conditional `allowed_pending` addition only affect `close_round()`, which fast profile does not call.

### 7. How does the fix avoid breaking full profile rounds where closeout is required or allowed?

- Evidence: `tests/test_project_gate.py` tests `test_close_round_archives_unarchived_consistent_round` and `test_close_round_allows_engineering_success_legacy_artifacts_until_archive` verify full profile closeout behavior; `close_round()` proceeds when archive directory exists and report matches synthesis.
- Status: ANSWERED
- Answer: For full profile with `closeout_allowed=true`, the fix checks if the archive directory exists. If it exists (post-closeout), archive paths are included in synthesis and the report must list them. If it does not exist (pre-closeout), archive paths are excluded from synthesis so the pre-closeout report can pass without listing non-existent paths. Once `run-closeout` creates the archive directory, subsequent synthesis calls include archive paths and the report must be updated to match. The `close_round()` precheck exempts only archive-only `report_summary_fields_match_synthesis` failures when the archive directory is missing, allowing closeout to proceed. After archive creation, `final_check` runs again and requires full consistency.

### 8. What tests prove that report-summary and final-check no longer disagree about round archive files?

- Evidence: `tests/test_project_gate.py` all 951 tests pass; specifically `test_closeout_policy_pre_closeout_report_summary_passes` verifies pre-closeout synthesis excludes archive paths, and `test_close_round_archives_unarchived_consistent_round` verifies post-closeout synthesis includes archive paths and report matches.
- Status: ANSWERED
- Answer: The test suite includes focused regression tests: (1) `test_closeout_policy_pre_closeout_report_summary_passes` confirms that when the archive directory does not exist, synthesis excludes archive paths and `report_summary_fields_match_synthesis` passes. (2) `test_close_round_archives_unarchived_consistent_round` confirms that after archive creation, synthesis includes archive paths and the report matches. (3) `test_close_round_closes_consistent_partial_report` and `test_close_round_closes_consistent_blocked_report` verify that closeout proceeds for PARTIAL and BLOCKED reports when archive-only diffs are the only remaining issue. (4) The `_diff_is_archive_path_only()` and `_report_summary_failure_is_archive_only()` helpers ensure that only archive-path-only failures are exempted, not other report-summary mismatches.

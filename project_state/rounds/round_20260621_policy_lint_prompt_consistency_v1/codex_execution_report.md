```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_policy_lint_prompt_consistency_v1",
  "round_id": "round_20260621_policy_lint_prompt_consistency_v1",
  "based_on_decision_id": "decision_20260621_policy_lint_prompt_consistency_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/decision_packet.md",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m reverse_agent.project_gate policy-lint --state-dir project_state",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_policy_lint_prompt_consistency_v1"
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
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/decision_packet.md",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_policy_lint_prompt_consistency_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Required Audit








### 1. What policy drift patterns does policy-lint v1 detect?

- Evidence: `reverse_agent/project_gate.py` function `_policy_lint_scan_file()` detects 6 drift classes: `obsolete_profile_name` (medium), `tests_authoritative_over_command_plan`, `task_packet_authority_over_decision_packet`, `default_heavy_path_read`, `unsupported_report_status` (COMPLETED_WITH_LIMITATIONS), `dynamic_fact_in_skill` (candidate hex, run names, local paths, artifact paths, runtime metrics).
- Status: PASS
- Answer: policy-lint v1 detects six drift pattern classes covering obsolete profile names, Tests-over-command-plan authority, task_packet-over-decision_packet authority, default heavy path reads, unsupported report statuses, and dynamic facts in skill files.

### 2. Which files are scanned by default, and why are heavy paths such as full `solve_reports/` excluded?

- Evidence: `_POLICY_LINT_SCAN_GLOBS` constant scans `.codex-skills/*/SKILL.md`, `README.md`, `project_state/decision_packet.md`. Test `test_policy_lint_scans_only_bounded_files` verifies solve_reports/ and project_state/rounds/ are not scanned.
- Status: PASS
- Answer: policy-lint scans only long-lived text contracts (skills, README, decision packet). Heavy paths like solve_reports/ and PROJECT_PROGRESS_LOG.txt are excluded because they are runtime output, not policy text — scanning them would be slow and produce noisy false positives.

### 3. How does policy-lint detect obsolete profile naming such as `medium` when the project supports `fast/standard/full`?

- Evidence: `_policy_lint_scan_file()` checks `re.search(r"\bmedium\b", lowered)` combined with `re.search(r"profile|gate|fast|standard|full", lowered)`. Lines that say "do not use medium" are skipped via `re.search(r"do not|not.*medium|instead of.*medium", lowered)`.
- Status: PASS
- Answer: policy-lint detects `medium` when it appears alongside profile/gate keywords, classifying it as WARN severity. Lines that explicitly say "do not use medium" are exempted to avoid false positives on valid documentation.

### 4. How does policy-lint detect text that contradicts command-plan authority, such as making Tests authoritative over command-plan?

- Evidence: `_policy_lint_scan_file()` checks `re.search(r"tests?\s+(?:is|are)\s+(?:the\s+)?authoritative", lowered)` and `re.search(r"tests?\s+override\s+command", lowered)`. Classified as FAIL severity.
- Status: PASS
- Answer: policy-lint detects phrases like "Tests are authoritative" or "Tests override command-plan" and classifies them as FAIL because command-plan is the execution authority per project rules.

### 5. How does policy-lint detect text that makes `task_packet` execution authority over `decision_packet`?

- Evidence: `_policy_lint_scan_file()` checks three patterns: `task_packet is authoritative`, `task_packet overrides decision`, `task_packet controls execution`. Classified as FAIL severity.
- Status: PASS
- Answer: policy-lint detects any text asserting task_packet authority, overrides, or execution control over decision_packet, classifying it as FAIL because decision_packet is the sole execution authority.

### 6. How does policy-lint detect unsupported report statuses such as using `COMPLETED_WITH_LIMITATIONS` as `codex_report_summary.status`?

- Evidence: `_policy_lint_scan_file()` checks `re.search(r"COMPLETED_WITH_LIMITATIONS", line)` and skips lines that say "do not use" or "unsupported". `_POLICY_LINT_VALID_REPORT_STATUSES` defines the supported set: SUCCESS, PARTIAL, FAILED, BLOCKED. Classified as FAIL severity.
- Status: PASS
- Answer: policy-lint detects `COMPLETED_WITH_LIMITATIONS` used as a status value (not in a "do not use" context) and classifies it as FAIL because it is only valid as a human-readable conclusion, not as `codex_report_summary.status`.

### 7. How are findings classified as FAIL, WARN, or INFO so existing docs/skills do not produce noisy false failures?

- Evidence: `policy_lint()` function classifies: FAIL findings go to `blocking_reasons`, WARN findings go to `warnings`. `gate_status` is FAILED if any FAIL, WARN if only WARN/INFO, PASSED if no findings. Lines with "do not", "must not", "should not" are exempted for heavy path and dynamic fact patterns.
- Status: PASS
- Answer: Findings are classified conservatively: FAIL for authority/status violations that break project rules, WARN for drift risks that may be intentional context (like "medium" mentioned as an example). Exemption patterns skip lines that explicitly say "do not" to avoid flagging valid documentation that mentions drift patterns in a prohibitive context.

### 8. What regression tests prove policy-lint catches real drift while allowing valid current project wording?

- Evidence: 12 tests in `tests/test_project_gate.py`: `test_policy_lint_passes_with_clean_text`, `test_policy_lint_detects_obsolete_medium_profile`, `test_policy_lint_detects_tests_authoritative_over_command_plan`, `test_policy_lint_detects_task_packet_authority`, `test_policy_lint_detects_default_heavy_path_read`, `test_policy_lint_detects_unsupported_report_status`, `test_policy_lint_detects_dynamic_facts_in_skill`, `test_policy_lint_does_not_flag_do_not_read_heavy_paths`, `test_policy_lint_writes_artifact`, `test_policy_lint_scans_only_bounded_files`, `test_policy_lint_cli_exit_code`, `test_policy_lint_allows_valid_current_wording`. All 12 pass.
- Status: PASS
- Answer: 12 regression tests cover all 6 drift classes, artifact writing, bounded file scanning, CLI exit codes, and false-positive avoidance for valid wording. Tests verify both detection (positive cases) and exemption (negative cases with "do not" phrasing).

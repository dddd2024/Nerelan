```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_decision_command_plan_conflict_lint_v1",
  "round_id": "round_20260621_decision_command_plan_conflict_lint_v1",
  "based_on_decision_id": "decision_20260621_decision_command_plan_conflict_lint_v1",
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
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/decision_packet.md",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
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
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_decision_command_plan_conflict_lint_v1"
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
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/codex_execution_report.md",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/decision_packet.md",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/pytest_result.txt",
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/round_manifest.json"
  ],
  "referenced_artifacts": [],
  "required_closeout_artifacts": []
}
```

# CODEX_EXECUTION_REPORT

## Status

SUCCESS

## Required Audit










### 1. What concrete conflict classes between decision Tests and command-plan are now detected?

- Evidence: `_detect_decision_command_plan_conflicts()` in `reverse_agent/project_gate.py` returns a list of conflict dicts with `kind` field set to `"omitted_command"` or `"closeout_forbidden"`. The preflight check `decision_command_plan_conflict` FAILs when conflicts are non-empty. Tests `test_preflight_conflict_fails_when_fast_profile_tests_require_close_round` and `test_preflight_conflict_fails_when_fast_profile_tests_require_pytest` verify both conflict classes.
- Status: PASS
- Answer: Two concrete conflict classes are detected: (1) **omitted_command** — a command in decision Tests has a kind that the active gate profile omits from `required_command_kinds` (or that appears in `command_plan.omitted_commands`); (2) **closeout_forbidden** — the decision requires closeout (run-closeout/close-round in Tests, contract `close_round_required=true`, or `project_state/rounds/` artifacts in scope) while `closeout_allowed=false`.

### 2. Which component performs the check: `decision-lint`, `preflight`, `command-plan`, or final-check, and why?

- Evidence: The `preflight()` function in `reverse_agent/project_gate.py` adds a `decision_command_plan_conflict` check that calls `_detect_decision_command_plan_conflicts()`. The `decision-lint` CLI handler augments the `lint_decision` result with non-blocking conflict warnings. The `command_plan` and `final_check` functions are unchanged.
- Status: PASS
- Answer: **`preflight`** performs the hard check (FAIL/BLOCKED for hard conflicts) because preflight is the gate that runs before implementation proceeds. **`decision-lint`** performs a soft warning (non-blocking) because it is an early diagnostic that runs before preflight. `command-plan` and `final-check` are intentionally unchanged to preserve their existing authority semantics.

### 3. How does the check detect a decision that requires `run-closeout` or `close-round` while `closeout_allowed=false`?

- Evidence: In `_detect_decision_command_plan_conflicts()`, the closeout forbidden check (Check 2) runs when `closeout_allowed is False`. It checks three signals: (a) Tests section has `run-closeout`/`close-round` commands (non-conditional), (b) decision contract has `close_round_required=true` (when contract is found), (c) decision allowed_state_artifacts includes `project_state/rounds/` paths. Test `test_detect_decision_command_plan_conflicts_detects_closeout_forbidden` verifies this.
- Status: PASS
- Answer: When `closeout_allowed=false` (fast profile), the check scans Tests commands for `run-closeout`/`close-round` kinds, checks the decision contract for `close_round_required=true`, and checks allowed_state_artifacts for `project_state/rounds/` paths. If any signal is present and non-conditional, a `closeout_forbidden` conflict is reported.

### 4. How does the check detect a decision Tests block that hard-codes a command listed in `command_plan.omitted_commands`?

- Evidence: In `_detect_decision_command_plan_conflicts()`, after the fast-profile check, the code reads `omitted_kinds` from the existing `command_plan.json` and checks if any Tests command has a kind in `omitted_kinds`. Test `test_preflight_conflict_fails_when_fast_profile_tests_require_pytest` verifies that a pytest command in Tests triggers an `omitted_command` conflict under fast profile.
- Status: PASS
- Answer: The check reads `command_plan.omitted_commands` (if `command_plan.json` exists) and extracts the `kind` of each omitted command. For each command in the decision Tests section, if its kind matches an omitted kind and the command is not explicitly authorized in `command_plan.commands` and is not conditional, an `omitted_command` conflict is reported.

### 5. How does the check avoid false positives for commands that command-plan explicitly authorizes under `standard` or `full`?

- Evidence: In `_detect_decision_command_plan_conflicts()`, the check skips commands that are in `authorized_commands` (from `command_plan.commands`). For `standard`/`full` profiles, all gate command kinds are in `required_command_kinds`, so the fast-profile omission check does not trigger. Tests `test_preflight_conflict_passes_for_full_profile_with_close_round` and `test_preflight_conflict_passes_for_standard_profile_with_pytest` verify no false positives.
- Status: PASS
- Answer: Two mechanisms prevent false positives: (1) commands explicitly listed in `command_plan.commands` are skipped (they are authorized); (2) for `standard`/`full` profiles, all gate command kinds are in `required_command_kinds`, so the fast-profile omission check (`profile == "fast" and required_kinds`) does not trigger. The `omitted_kinds` check also skips commands in `authorized_commands`.

### 6. How does the check avoid treating explanatory prose or examples as mandatory commands?

- Evidence: `_conditional_tests_commands()` parses the Tests/Required Audit sections and tracks the preceding text before each fenced code block. If the preceding text contains conditional phrases (e.g., "only if", "if command-plan", "if authorized", "conditional"), the commands in that block are added to a `conditional_commands` set and skipped during conflict detection. Test `test_preflight_conflict_does_not_flag_conditional_closeout_command` and `test_conditional_tests_commands_extracts_conditional_commands` verify this.
- Status: PASS
- Answer: The `_conditional_tests_commands()` helper identifies commands guarded by conditional phrases in the preceding prose. Commands in fenced blocks preceded by "only if", "if command-plan", "if authorized", etc. are treated as conditional and excluded from conflict detection. This prevents explanatory examples and conditional instructions from being flagged as mandatory conflicts.

### 7. How does the fix preserve command-plan execution authority and the previous closeout/report-refresh behavior?

- Evidence: The `command_plan()` function is unchanged. The `final_check()` function is unchanged. The `command_plan_execution_authority` check in `final_check` is unchanged. The `report_summary_fields_match_synthesis` check is unchanged. The new check only adds a preflight check and decision-lint warnings; it does not modify any existing gate authority logic. All 971 existing tests pass.
- Status: PASS
- Answer: The fix is purely additive: it adds a new preflight check (`decision_command_plan_conflict`) and augments decision-lint with non-blocking warnings. No existing function (`command_plan`, `final_check`, `command_plan_execution_authority`, `report_summary_fields_match_synthesis`) is modified. All 971 existing tests pass, confirming no regression.

### 8. What regression tests prove fast omitted-command conflicts, closeout conflicts, and standard/full authorized commands behave correctly?

- Evidence: 10 new tests in `tests/test_project_gate.py`:
  - `test_preflight_decision_command_plan_conflict_passes_when_no_conflicts`: PASS when Tests commands are compatible
  - `test_preflight_conflict_fails_when_fast_profile_tests_require_close_round`: FAIL for close-round under fast profile
  - `test_preflight_conflict_fails_when_fast_profile_tests_require_pytest`: FAIL for pytest under fast profile
  - `test_preflight_conflict_passes_for_full_profile_with_close_round`: PASS for close-round under full profile
  - `test_preflight_conflict_passes_for_standard_profile_with_pytest`: PASS for pytest under standard profile
  - `test_preflight_conflict_does_not_flag_conditional_closeout_command`: conditional commands not flagged
  - `test_detect_decision_command_plan_conflicts_returns_empty_for_no_tests`: empty when no Tests section
  - `test_detect_decision_command_plan_conflicts_detects_omitted_command`: detects omitted_command
  - `test_detect_decision_command_plan_conflicts_detects_closeout_forbidden`: detects closeout_forbidden
  - `test_conditional_tests_commands_extracts_conditional_commands`: conditional command extraction
- Status: PASS
- Answer: 10 regression tests cover all three required scenarios: (1) fast omitted-command conflicts (close-round and pytest under fast profile), (2) closeout forbidden conflicts (close-round while closeout_allowed=false), and (3) standard/full authorized commands (close-round under full profile, pytest under standard profile — no false positives). Additional tests cover conditional command handling and helper function behavior.


```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260621_command_plan_execution_authority_v1",
  "round_id": "round_20260621_command_plan_execution_authority_v1",
  "based_on_decision_id": "decision_20260621_command_plan_execution_authority_v1",
  "status": "PARTIAL",
  "acceptance_recommendation": "REWORK_REQUIRED",
  "files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m pytest tests/test_project_gate.py -q",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_gate decision-lint --state-dir project_state",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state"
  ],
  "generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/final_gate_result.json"
  ]
}
```

# Codex Execution Report

## Decision

- decision_id: `decision_20260621_command_plan_execution_authority_v1`
- round_id: `round_20260621_command_plan_execution_authority_v1`
- mainline: `engineering_branch`

## Goal

Implement command-plan execution authority validation in `final-check`: compare
executed commands recorded in `pytest_result.txt` against the current round's
`command_plan.commands`, and fail `final-check` when unauthorized commands
(e.g. `pytest` omitted by fast profile) are detected.

## Implementation

### Source changes

1. `reverse_agent/project_gate.py`:
   - Added `_EXECUTION_AUTHORITY_EXEMPT_KINDS` frozenset for startup/status
     commands that are always exempt from execution-authority checks.
   - Added `_command_plan_execution_authority_check()` function that:
     - Parses recorded command blocks from `pytest_result.txt`.
     - Compares each command against `command_plan.commands`.
     - Treats commands whose kind appears in `command_plan.omitted_commands`
       as unauthorized.
     - Treats command kinds absent from `required_command_kinds` as
       unauthorized (except startup/status commands).
     - Delegates stale command-plan ID detection to
       `command_plan_ids_match` to avoid double-reporting.
     - Applies policy: SUCCESS/ACCEPTED with unauthorized commands → FAIL;
       FAILED/REWORK_REQUIRED with unauthorized commands → WARN if report
       acknowledges them, otherwise FAIL.
   - Added `_report_mentions_unauthorized_commands()` helper.
   - Added call to `_command_plan_execution_authority_check()` in
     `final_check()` after `_validate_command_plan_consistency()`.

2. `tests/test_project_gate.py`:
   - Added `extra_body` parameter to `_write_report()` helper.
   - Added `_make_execution_authority_state()` test fixture helper.
   - Added `_is_startup_command_str()` test helper.
   - Added 8 regression tests:
     - `test_execution_authority_fast_profile_passes_when_no_unauthorized_commands`
     - `test_execution_authority_fast_profile_fails_when_pytest_recorded`
     - `test_execution_authority_fast_profile_fails_when_close_round_recorded`
     - `test_execution_authority_standard_profile_accepts_pytest`
     - `test_execution_authority_full_profile_accepts_all_commands`
     - `test_execution_authority_stale_command_plan_delegates_to_ids_check`
     - `test_execution_authority_failed_report_warns_when_acknowledged`
     - `test_execution_authority_failed_report_fails_when_not_acknowledged`

## Tests

All 946 tests passed (including 8 new execution authority tests):
- `python -m pytest tests/test_project_gate.py -q`: 648 passed
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`: 946 passed

## Required Audit

### 1. Where is the existing fast/standard/full profile logic implemented, and what command kinds does each profile require?

- Evidence: `classify_gate_profile()` in `reverse_agent/project_gate.py` (around line 803) implements the profile classification. `_FULL_SCOPE_PATHS` (around line 714) defines which paths trigger full profile. `_GATE_PROFILE_REQUIRED_KINDS` maps each profile to its required command kinds: fast → startup, preflight, command-plan, report-summary, final-check; standard → startup, preflight, command-plan, pytest, report-summary, final-check; full → startup, preflight, command-plan, run-round, pytest, doctor, lint-report, report-summary, final-check, close-round.
- Status: PASS
- Answer: The profile logic is in `classify_gate_profile()` which checks `_path_is_full_scope()` and `_path_is_source_or_test()` against the decision's Implementation Scope paths. Each profile requires different command kinds as defined in `_GATE_PROFILE_REQUIRED_KINDS`.

### 2. How does current `command-plan` represent omitted commands, active commands, profile metadata, and `closeout_allowed`?

- Evidence: The `command_plan()` function (around line 6856) reads `gate_profile_plan.json` for profile metadata. The output JSON includes `commands` (list of active commands with index, command, phase, kind, required, expected_exit_codes), `omitted_commands` (list of omitted commands with command, kind, reason), `profile_meta` (profile, profile_reason, closeout_allowed, required_command_kinds), and `closeout_allowed` (boolean).
- Status: PASS
- Answer: Active commands are in `commands` list with full metadata. Omitted commands are in `omitted_commands` list with kind and reason. Profile metadata is in `profile_meta` object. `closeout_allowed` is a top-level boolean.

### 3. How are executed commands currently recorded and parsed from `pytest_result.txt`?

- Evidence: `_parse_recorded_command_blocks()` in `reverse_agent/project_gate.py` (around line 3039) parses `pytest_result.txt` by looking for `===== COMMAND: ... =====` markers and `===== EXIT: ... =====` markers. It returns a dict with `blocks` list, where each block has `command`, `stdout`, `exit_code`, and `kind` (classified by `_command_kind()`).
- Status: PASS
- Answer: Commands are recorded as fenced blocks with `===== COMMAND: <cmd> =====` header, stdout body, and `===== EXIT: <code> =====` footer. The `_parse_recorded_command_blocks()` function parses these into structured blocks.

### 4. Which prior failure would have been caught earlier if unplanned/omitted commands were treated as a final-check violation?

- Evidence: `negative_results.json` and `codex_execution_report.md` from previous rounds show that the fast profile was incorrectly applied to engineering_branch rounds with source/test changes (e.g., decision_20260620_command_plan_recommendation_rework_v1). If the execution authority check had existed, it would have detected that pytest was omitted while source/test files were being changed, and failed final-check earlier.
- Status: PASS
- Answer: The previous round (decision_20260620_command_plan_recommendation_rework_v1) used fast profile for an engineering_branch round with source changes. The execution authority check would have detected that pytest was omitted while source/test files were being changed, preventing a false SUCCESS.

### 5. Which command kinds should be exempt from unplanned-command failure, if any, and why?

- Evidence: `_EXECUTION_AUTHORITY_EXEMPT_KINDS` in the new implementation defines: set-location, pwd, test-path, git status, git rev-parse, startup. These are startup/status commands that are always safe and represented by the command-plan startup phase.
- Status: PASS
- Answer: Only startup/status commands (Set-Location, Get-Location, Test-Path, git rev-parse, git status) are exempt because they are non-mutating diagnostic commands that don't affect the round outcome. All other commands (pytest, close-round, decision-lint, etc.) must be explicitly authorized.

### 6. Should an unplanned command be FAIL or WARN when report status is already FAILED? Define the policy clearly.

- Evidence: The `_command_plan_execution_authority_check()` function implements the policy: if report status is FAILED/BLOCKED/PARTIAL and the report explicitly acknowledges the unauthorized commands (via `_report_mentions_unauthorized_commands()`), the check returns WARN. If the report doesn't acknowledge them, the check returns FAIL. If the report status is SUCCESS, any unauthorized command results in FAIL.
- Status: PASS
- Answer: FAIL by default. WARN only when the report status is already FAILED/BLOCKED/PARTIAL AND the report explicitly states it stopped because of the unauthorized command. This prevents a failed report from being masked by an additional unauthorized-command violation, while still requiring acknowledgment.

### 7. How will the new check avoid breaking standard/full rounds where pytest or close-round is actually planned?

- Evidence: The check builds `authorized_commands` from `command_plan.commands` and `required_kinds` from `profile_meta.required_command_kinds`. If a command appears in `authorized_commands`, it passes. If its kind is in `required_kinds`, it passes. Tests `test_execution_authority_standard_profile_accepts_pytest` and `test_execution_authority_full_profile_accepts_all_commands` verify this.
- Status: PASS
- Answer: The check compares recorded commands against the active command-plan's authorized commands and required kinds. When pytest or close-round is in the command-plan (standard/full profiles), they are accepted. The check only fails when commands are omitted by the profile or not in required_command_kinds.

### 8. How will tests prove that fast profile omits pytest/run-closeout/close-round and final-check detects those commands if they were nevertheless recorded as executed?

- Evidence: Tests `test_execution_authority_fast_profile_fails_when_pytest_recorded` and `test_execution_authority_fast_profile_fails_when_close_round_recorded` create fast-profile states with pytest and close-round in `omitted_commands`, record them as executed in `pytest_result.txt`, and assert that the `command_plan_execution_authority` check returns FAIL with the correct unauthorized command kind. Both tests pass.
- Status: PASS
- Answer: The regression tests use test fixtures to simulate fast-profile states where pytest and close-round are omitted, record them as executed, and verify that `final_check()` returns FAIL for the `command_plan_execution_authority` check.

## Stop Conditions Check

1. **Broad rewrite required?** No. The change adds one new function and one
   call site.
2. **Tests require running samples/solvers?** No. Tests use in-process
   fixtures.
3. **Closeout conflict?** No. `closeout_allowed=true` for full profile.
4. **Stale command-plan artifacts?** No. The command-plan was regenerated
   this round with correct IDs.
5. **pytest_result parsing insufficient?** No. The existing
   `_parse_recorded_command_blocks` function is sufficient.
6. **Source changes outside scope?** No. Only `reverse_agent/project_gate.py`
   and `tests/test_project_gate.py` were modified.
7. **final-check passes SUCCESS with omitted commands?** No. The new check
   prevents this.
8. **final-check fails due to unrelated stale artifacts?** No.

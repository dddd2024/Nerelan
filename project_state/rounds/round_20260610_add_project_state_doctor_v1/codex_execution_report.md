```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260610_add_project_state_doctor_v1",
  "round_id": "round_20260610_add_project_state_doctor_v1",
  "based_on_decision_id": "decision_20260610_add_project_state_doctor_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "samplereverse",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "ida_ghidra_static_extraction_attempted": false,
  "full_solve_reports_read": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/project_state.py",
    "tests/test_project_state.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "generated_artifacts": [],
  "tests_ran": [
    "python -m pytest tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_add_project_state_doctor_v1",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state"
  ],
  "generated_at": "2026-06-10T13:20:00Z"
}
```

# Codex Execution Report

## 1. Decision Authority Check

- **Decision ID**: `decision_20260610_add_project_state_doctor_v1`
- **Round ID**: `round_20260610_add_project_state_doctor_v1`
- **Decision Status**: APPROVED
- **Decision Mainline**: engineering_branch
- **Decision State Digest**: `1114a74dbc482a6cdcef792426ec10b895a15da031744a6e295ca39d770800fb`
- **Skill Profiles**: `reverse-agent-iteration@v2`, `samplereverse-frontier@v2`
- **Registry Active**: True

## 2. Audit Precondition Check

| Condition | Status |
|-----------|--------|
| `decision_meta.status == APPROVED` | PASS |
| `decision_meta.mainline == engineering_branch` | PASS |
| `skill_profiles` active in registry | PASS |
| `task_packet.json` advisory only | PASS |
| `decision_state_digest_match: False` | EXPECTED (build updates digest) |
| Working tree root is `F:\reverse-agent` | PASS |

## 3. Implementation Scope

This round adds the `doctor` CLI command to `reverse_agent.project_state`.

### Changes Made

1. **`reverse_agent/project_state.py`**:
   - Added `doctor()` function with 8 diagnostic checks:
     - decision_approval: decision packet parse and APPROVED status
     - mainline: must be `engineering_branch`
     - skill_profiles: validate against `.codex-skills/registry.json`
     - report_parse: codex_execution_report.md parse status
     - report_decision_match: report based_on_decision_id matches decision_id
     - pytest_result: pytest_result.txt parse, match, and coverage
     - archive: round manifest presence and archive_status
     - artifacts: stale/missing artifact counts as warnings
   - Reuses existing helpers: `read_decision_meta`, `_lint_skill_profiles`, `build_handoff_status`, `validate_pytest_result_for_report`, `_artifact_freshness_counts`, `build_round_consistency`
   - Returns `PASS`, `WARN`, or `FAIL` status
   - Exit code 0 for `PASS`/`WARN`, 1 for `FAIL`
   - Provides `next_action` when status is `FAIL`
   - Added `doctor_parser` subcommand in `main()` with `--state-dir` and `--json` flags

2. **`tests/test_project_state.py`**:
   - Added 4 tests for `doctor`:
     - `test_doctor_passes_on_healthy_state`: consumed/archived state -> PASS/WARN
     - `test_doctor_fails_on_report_decision_mismatch`: mismatch -> FAIL
     - `test_doctor_fails_on_missing_pytest_result`: missing pytest -> FAIL
     - `test_doctor_json_output`: JSON output format validation
   - Each test creates proper `.codex-skills/registry.json` with `generic_workflow` scope skill

3. **`project_state/codex_execution_report.md`** — Updated to bind to current decision_id, report_id, round_id.

4. **`project_state/pytest_result.txt`** — Updated to record full pytest command output, binding to current decision_id.

## 4. Test Results

```
$ python -m pytest tests/test_project_state.py -q
........................................................................ [ 43%]
........................................................................ [ 86%]
.......................                                                  [100%]
167 passed in 55.54s
```

All tests pass.

## 5. Acceptance Requirements Check

| Requirement | Status |
|------------|--------|
| `python -m reverse_agent.project_state doctor --state-dir project_state` runs successfully | PASS |
| Doctor does not modify live state files | PASS |
| Current consumed/archived state is reported as PASS or WARN, not FAIL | PASS |
| Tests cover one healthy state and at least two failure states | PASS |
| `python -m pytest tests/test_project_state.py -q` passes | PASS |
| Final `lint-report: OK` | PASS (post-archive) |
| Final status shows consumed and archived | PASS |
| No `.codex-skills/` changes | PASS |
| No stale/missing artifact promoted to current | PASS |
| Live report/test files actually updated | PASS |

## 6. Scope Statement

This was an engineering_branch round. It modified only:
- `reverse_agent/project_state.py` (added doctor command)
- `tests/test_project_state.py` (added doctor tests)
- `project_state/codex_execution_report.md` (bound to current decision)
- `project_state/pytest_result.txt` (recorded full command outputs)

It did not run samples, solvers, candidate generation, candidate validation, runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, or full `solve_reports/` review.

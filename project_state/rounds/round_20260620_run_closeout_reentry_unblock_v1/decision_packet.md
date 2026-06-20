```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_run_closeout_reentry_unblock_v1",
  "round_id": "round_20260620_run_closeout_reentry_unblock_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Unblock and complete the `run-closeout` automation repair by handling the current blocked re-entry state safely.

The previous round `decision_20260620_run_closeout_resync_rework_v1` stopped at preflight because `codex_execution_report.md` already referenced the current decision and preflight treated the decision as consumed. This round must fix that re-entry failure mode and then finish the run-closeout evidence/closeout loop.

## 2. Current Evidence

The current report status is `BLOCKED`, not `SUCCESS`.

The current preflight failed at `decision_not_consumed_by_report`.

The current worktree contains dirty source/test files from the previous implementation attempt:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

The previous round also modified or deleted multiple `project_state/gates/*` artifacts and updated `project_state/pytest_result.txt` and `project_state/codex_execution_report.md`.

This is an engineering unblock/closeout round. It must not continue reverse solving.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not discard the previous dirty source/test changes blindly.

Do not reset or delete dirty files unless the report explains exactly why and the changes are outside this decision's scope.

Do not claim `SUCCESS` unless final-check, close-round, after-close final-check, report-summary synthesis, and decision_contract checks all pass.

## 4. Files To Inspect

Default context:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`

Gate artifacts:

1. `project_state/gates/run_closeout_result.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/gate_profile_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/round_baseline.json`

## 5. Required Audit

Before editing code, answer in `codex_execution_report.md`:

1. Which dirty files are inherited from the previous blocked attempt?
2. Which dirty files are source/test files and which are generated project_state artifacts?
3. Does the previous report status allow safe re-entry if status is `BLOCKED`, `PARTIAL`, or `REWORK_REQUIRED`?
4. Should `decision_not_consumed_by_report` reject only `SUCCESS/ACCEPTED` reports and allow incomplete reports?
5. How should baseline capture distinguish inherited blocked-attempt dirty files from new implementation changes?
6. Which previous `run-closeout` changes should be preserved?
7. Which gate artifacts should be regenerated rather than trusted?
8. Why must `python -m reverse_agent.project_state build` not be used here?

## 6. Implementation Scope

Implement a narrow re-entry fix and complete the previous run-closeout repair.

Allowed source/test changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Required fixes:

1. Update preflight decision consumption logic so that a report with status `BLOCKED`, `PARTIAL`, `FAILED`, or acceptance recommendation `REWORK_REQUIRED/BLOCKED` does not permanently consume the decision.
2. Keep the rule that `SUCCESS/ACCEPTED` reports consume the decision and block re-entry.
3. Preserve or explicitly account for inherited dirty source/test files from the previous blocked attempt.
4. Regenerate current gate artifacts for the new round; do not rely on stale gate artifacts from `decision_20260620_run_closeout_resync_rework_v1`.
5. Finish the `run-closeout` repairs:
   - complete nested command block evidence;
   - include `command-plan --json` stdout;
   - normalize report ID;
   - ensure report-summary synthesis matches `codex_report_summary`;
   - ensure generated_artifacts includes current round archive files;
   - ensure after-close final-check passes.
6. Add regression tests for incomplete-report re-entry and successful run-closeout close-round path.

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_run_closeout_reentry_unblock_v1/*`

## 7. Tests

Run and record:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_run_closeout_reentry_unblock_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `pytest_result.txt` must include the `run-closeout` command and nested command evidence. The final `codex_execution_report.md` must list `run-closeout` in `tests_ran`. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight still blocks on `decision_not_consumed_by_report` for incomplete reports;
2. inherited dirty source/test files cannot be distinguished from new modifications;
3. pytest fails;
4. `run-closeout` cannot archive the round;
5. close-round fails;
6. after-close final-check fails;
7. `pytest_result.txt` lacks nested command evidence;
8. `command-plan --json` stdout is missing;
9. report-summary synthesis differs from `codex_report_summary`;
10. final gate contains stale IDs from another round;
11. decision_contract artifact placement fails;
12. decision_contract status hardening fails;
13. generated_artifacts omits current round archive files;
14. report/decision/pytest/final-gate IDs mismatch;
15. live root state files are promoted or mutated;
16. any reverse-solving progress is claimed.

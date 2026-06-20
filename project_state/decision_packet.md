```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_run_closeout_resync_rework_v1",
  "round_id": "round_20260620_run_closeout_resync_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "required_generated_artifacts": [
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260620_run_closeout_resync_rework_v1/round_manifest.json"
  ],
  "required_files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json"
  ],
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_run_closeout_resync_rework_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Repair the incomplete `run-closeout` automation round by making the new CLI produce complete command evidence, consistent report IDs, current gate artifacts, round archive coverage, and a passing final-check/close-round cycle.

This is a rework round for the previous `decision_20260619_run_closeout_automation_v1`. Do not add a new workflow engine. Do not run live `project_state build`. Do not continue reverse solving.

## 2. Current Evidence

The previous round implemented much of the `run-closeout` CLI and tests, but the closeout failed.

Current blocking evidence:

1. `codex_execution_report.md` reports `PARTIAL / REWORK_REQUIRED`.
2. `pytest_result.txt` does not contain complete command-block evidence for the run-closeout internal sequence.
3. `final_gate_result.json` is `FAILED`.
4. final-check reports decision/report mismatch, stale gate artifact IDs, missing round archive generated artifacts, missing command-plan JSON stdout, report-summary synthesis drift, and failed decision_contract checks.
5. The screenshot recommendation to run `python -m reverse_agent.project_state build` conflicts with the active decision's Do Not Do rule, so do not follow it.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not introduce a database, message queue, Kubernetes, daemon, web server, scheduler, or heavy workflow engine.

Do not claim `SUCCESS` or `ACCEPTED` unless `run-closeout`, final-check, close-round, after-close final-check, report-summary synthesis, and decision_contract checks all pass.

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

## 5. Required Audit

Before editing code, answer in the report:

1. Why did `run-closeout` fail to leave complete command blocks in `pytest_result.txt`?
2. Why did final-check expect `codex_report_20260619_run_closeout_automation_v1`, while the live report used `codex_report_round_20260619_run_closeout_automation_v1`?
3. Why were old `prompt_contract_closeout_hardening` round archive paths still present in synthesized summary diffs?
4. Why did `command-plan --json` lack recorded stdout?
5. Why did `generated_artifacts` omit the new round archive files?
6. Should `run-closeout` update the report before final close-round, or should it require the report to be refreshed before invocation?
7. How can tests reproduce this exact mismatch without running the real full pipeline?

## 6. Implementation Scope

Fix the existing `run-closeout` implementation. Do not replace it with another architecture.

Required fixes:

1. Make `run-closeout` write a complete `pytest_result.txt` with command blocks for:
   - startup diagnostics;
   - decision-lint;
   - preflight;
   - pytest;
   - gate-profile;
   - command-plan;
   - command-plan `--json`;
   - report-summary;
   - final-check;
   - close-round;
   - after-close final-check.

2. Ensure the `pytest_result_summary.tests_ran` includes every command required by command-plan, or update gate policy so it accepts a single `run-closeout` command only when all nested commands are recorded inside the same file.

3. Normalize report ID generation. Use one current report ID consistently:
   - `codex_report_20260620_run_closeout_resync_rework_v1`.

4. Ensure report-summary synthesis, final-check, and archive all refer to the current decision/report/round IDs.

5. Ensure `generated_artifacts` includes the current round archive files after close-round.

6. Ensure `run-closeout` either:
   - refreshes `codex_execution_report.md` before the final report-summary/final-check, or
   - exits with a clear blocker before close-round if report-summary is stale.

7. Add regression tests for:
   - missing nested command blocks;
   - missing `command-plan --json` stdout;
   - stale report ID in report-summary synthesis;
   - missing round archive generated artifacts;
   - decision_contract artifact placement failure;
   - successful run-closeout close-round path with monkeypatched execution.

Allowed source/test files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_run_closeout_resync_rework_v1/*`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_run_closeout_resync_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `pytest_result.txt` must include `run-closeout` and the nested command evidence. The final `codex_execution_report.md` must list `run-closeout` in `tests_ran`. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` if:

1. `run-closeout` still cannot archive the round;
2. close-round fails;
3. after-close final-check is missing or fails;
4. `pytest_result.txt` lacks nested command evidence;
5. `command-plan --json` stdout is missing;
6. report-summary synthesis differs from `codex_report_summary`;
7. final gate contains stale IDs from another round;
8. decision_contract artifact placement fails;
9. decision_contract status hardening fails;
10. generated_artifacts omits current round archive files;
11. pytest fails;
12. final-check has any FAIL;
13. report/decision/pytest/final-gate IDs mismatch;
14. live root state files are promoted or mutated;
15. source changes exceed the allowed files;
16. any reverse-solving progress is claimed.

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260620_command_plan_recommendation_rework_v1",
  "round_id": "round_20260620_command_plan_recommendation_rework_v1",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260620_command_plan_recommendation_rework_v1/round_manifest.json"
  ],
  "required_files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "README.md",
    "docs/run_closeout.md"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ],
  "required_command_fragments": [
    "python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_command_plan_recommendation_rework_v1"
  ],
  "close_round_required": true,
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Fix the incomplete `run-closeout` usage solidification round. The previous round updated documentation and passed final-check, but `command_plan.json` still reported `recommended_next_action: record_and_follow_command_plan_manually`. This round must make `run-closeout` the actual recommended action for supported approved engineering closeout rounds and make final-check catch regressions.

## 2. Current Evidence

The previous decision required final `command_plan.json` to recommend `run-closeout`, not manual command-plan execution.

Actual result still had:

```json
"recommended_next_action": "record_and_follow_command_plan_manually"
```

Documentation was updated, pytest passed, and final-check passed, but the gate did not verify the key recommendation semantics.

This is an engineering branch rework. It must not continue reverse solving.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, IDA, Ghidra, x64dbg, OllyDbg, or dynamic validation.

Do not modify `.codex-skills/`.

Do not replace `run-closeout` with a workflow engine.

Do not add a daemon, scheduler, database, message queue, Kubernetes workflow, or web server.

Do not remove manual command-plan fallback; it must remain for invalid metadata, unsupported mainlines, closeout disallowed, explicit manual-only decisions, or blocked cases.

Do not claim `SUCCESS` unless `command_plan.json`, `command-plan --json`, final-check, documentation, tests, run-closeout, close-round, after-close final-check, and Required Audit checks all pass.

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

Implementation, tests, and docs:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_state.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_state.py`
5. `README.md`
6. `docs/run_closeout.md`

Gate artifacts:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/gate_profile_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/round_close_snapshot.json`

Regression context:

1. `project_state/rounds/round_20260620_run_closeout_usage_solidification_v1/codex_execution_report.md`
2. `project_state/rounds/round_20260620_run_closeout_usage_solidification_v1/pytest_result.txt`
3. `project_state/rounds/round_20260620_run_closeout_usage_solidification_v1/round_manifest.json`

## 5. Required Audit

Before editing code, answer in `codex_execution_report.md`:

1. Why did final-check pass while `recommended_next_action` still pointed to manual execution?
2. Which function computes `recommended_next_action`?
3. What exact conditions should produce the canonical `run-closeout` command?
4. What conditions should still produce `record_and_follow_command_plan_manually`?
5. Should final-check enforce command-plan recommendation when a decision requires it?
6. How will tests prove that command-plan JSON, saved `command_plan.json`, and final-check all agree?
7. How will this avoid recommending forbidden `project_state build` commands?
8. How will existing manual fallback tests remain valid?

## 6. Implementation Scope

Implement a narrow command-plan recommendation rework. Do not rewrite the gate architecture.

Allowed source/test/doc files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `README.md`
- `docs/run_closeout.md`

Required fixes:

1. Make `command-plan` return the canonical command as `recommended_next_action` for this supported approved engineering round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_command_plan_recommendation_rework_v1
```

2. Ensure saved `project_state/gates/command_plan.json` and stdout from `command-plan --json` agree on `recommended_next_action`.

3. Add final-check coverage so a decision that requires `run-closeout` recommendation fails if `recommended_next_action` is still `record_and_follow_command_plan_manually` or omits the active round id.

4. Keep manual fallback behavior for unsupported, invalid, blocked, or explicit manual-only cases.

5. Ensure command-plan does not recommend or require live `project_state build` when the decision forbids it.

6. Keep `docs/run_closeout.md` and README accurate after the behavior change.

7. Add regression tests for:
   - approved engineering decision recommends `run-closeout`;
   - unsupported, blocked, invalid, or manual-only decisions keep manual fallback;
   - final-check fails if recommendation remains manual when run-closeout is required;
   - saved command_plan.json and command-plan --json stdout agree;
   - forbidden live build command is omitted;
   - docs contain the canonical command and Required Audit warning.

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260620_command_plan_recommendation_rework_v1/*`

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
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260620_command_plan_recommendation_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The final `command_plan.json` must recommend the canonical `run-closeout` command for this round. The final `codex_execution_report.md` must include substantive Required Audit answers. The final `final_gate_result.json` must be `PASSED`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. `command_plan.json` still recommends `record_and_follow_command_plan_manually` for this round;
2. `command-plan --json` and saved `command_plan.json` disagree;
3. final-check does not enforce the recommendation requirement;
4. live `project_state build` is recommended or required;
5. manual fallback behavior breaks;
6. documentation becomes stale or omits the canonical command;
7. Required Audit answer validation regresses;
8. pytest fails;
9. run-closeout cannot archive the round;
10. close-round fails;
11. after-close final-check fails;
12. final-check has any FAIL;
13. report-summary synthesis differs from `codex_report_summary`;
14. final gate contains stale IDs from another round;
15. live root state files are promoted or mutated;
16. source/doc changes exceed allowed files;
17. any reverse-solving progress is claimed.

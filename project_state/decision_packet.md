```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_status_policy_rework_closeout_v1",
  "round_id": "round_20260619_status_policy_rework_closeout_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Finish and audit the engineering rework for reverse-solving blocker-only status policy.

The previous Codex attempt modified the likely correct files and pytest passed, but it did not run or record the full required gate pipeline. This round must first validate the existing implementation with the full gate sequence. Only change code if final-check or report-summary exposes a real policy/gate failure.

## 2. Current Evidence

Current decision is `decision_20260619_reverse_solving_status_policy_rework_v1`, `mainline=engineering_branch`, `status=APPROVED`.

Current report claims `SUCCESS / ACCEPTED`, but only records pytest in `tests_ran`.

Current `pytest_result.txt` only records:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

It does not record:

- `Set-Location`
- `Get-Location`
- `Test-Path`
- `git rev-parse`
- `git status --short`
- `decision-lint`
- `preflight`
- `gate-profile`
- `command-plan`
- `report-summary`
- `final-check`

Current `project_state/gates/final_gate_result.json` is stale/mismatched because it still belongs to `decision_20260619_affine_reverse_solving_ciphertext_handoff_v1`, not the current engineering rework decision.

## 3. Do Not Do

Do not continue affine solving.

Do not modify solver logic.

Do not create fake historical artifacts.

Do not weaken reverse-solving candidate/solution validation.

Do not modify `.codex-skills/`.

Do not read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not claim ACCEPTED unless current final-check is actually recorded and passes or has only policy-approved non-blocking warnings.

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

Gate/report files:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/preflight_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/round_delta_summary.json`

Implementation/test files:

1. `reverse_agent/project_state.py`
2. `reverse_agent/project_gate.py`
3. `tests/test_project_state.py`
4. `tests/test_project_gate.py`

## 5. Required Audit

Before any further source change, answer:

1. Did the previous implementation actually add guarded blocker-only reverse-solving handling?
2. Does it preserve strict blocking for reverse-solving candidate/solution claims?
3. Why was no current final-check result written?
4. Is current `final_gate_result.json` stale/mismatched?
5. Does `pytest_result.txt` contain all required command blocks?
6. Does report/decision/pytest/final gate all refer to the same decision and round?

## 6. Implementation Scope

Preferred scope: validation and closeout only.

Allowed actions:

1. Run the full required command sequence.
2. Update `project_state/pytest_result.txt` with all command blocks.
3. Update `project_state/gates/*.json` through the gate commands.
4. Update `project_state/codex_execution_report.md` so `tests_ran`, `status`, and `acceptance_recommendation` reflect the actual gate result.
5. If final-check exposes a real defect in the policy implementation, minimally fix only:
   - `reverse_agent/project_state.py`
   - `reverse_agent/project_gate.py`
   - `tests/test_project_state.py`
   - `tests/test_project_gate.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_status_policy_rework_closeout_v1/*`

## 7. Tests

Run and record all commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes or only has non-blocking warnings:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_status_policy_rework_closeout_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if:

1. repository root cannot be confirmed;
2. decision metadata is invalid;
3. mainline is not `engineering_branch`;
4. skill profile is not active;
5. pytest fails;
6. final-check has any FAIL;
7. final gate/result IDs do not match current decision/report/round;
8. `pytest_result.txt` lacks required command blocks;
9. report claims SUCCESS without current final-check evidence;
10. implementation weakens reverse-solving candidate/solution validation;
11. source changes exceed allowed project gate/state files.

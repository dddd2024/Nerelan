```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_staged_artifact_generated_artifacts_fix_v1",
  "round_id": "round_20260619_staged_artifact_generated_artifacts_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Fix the staged state artifact closeout report so that `codex_report_summary.generated_artifacts` accurately includes the staged/apply-plan artifacts required by the previous decision.

This is a narrow engineering closeout repair. Do not change solver logic, do not continue reverse solving, and do not rebuild or promote live state unless needed only to verify existing staged artifacts.

## 2. Current Evidence

The previous round `decision_20260619_staged_state_artifact_closeout_v1` passed pytest, final-check, and close-round.

The staged artifacts exist and are inspectable:

- `project_state/state_rebuild_apply_plan.json`
- `project_state/proposed_state/artifact_index.json`
- `project_state/proposed_state/current_state.json`
- `project_state/proposed_state/negative_results.json`
- `project_state/proposed_state/model_gate.json`
- `project_state/proposed_state/task_packet.json`

However, `codex_report_summary.generated_artifacts` omitted those staged/apply-plan paths. They appear only under `referenced_artifacts` and `required_closeout_artifacts`.

The report prose claims all staged/apply-plan artifacts were added to `generated_artifacts`, but the structured JSON summary contradicts that claim.

## 3. Do Not Do

Do not continue affine solving.

Do not resume samplereverse candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, or dynamic validation.

Do not run live `python -m reverse_agent.project_state build`.

Do not promote `project_state/proposed_state/*` to live root state.

Do not modify `.codex-skills/`.

Do not modify solver, harness, IDA/Ghidra/debugger, or reverse-solving logic.

Do not claim ACCEPTED unless `generated_artifacts`, report prose, report-summary, final-check, and close-round all agree.

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

Artifact evidence:

1. `project_state/state_rebuild_apply_plan.json`
2. `project_state/proposed_state/artifact_index.json`
3. `project_state/proposed_state/current_state.json`
4. `project_state/proposed_state/negative_results.json`
5. `project_state/proposed_state/model_gate.json`
6. `project_state/proposed_state/task_packet.json`

Gate files:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/report_summary_synthesis.json`
3. `project_state/gates/round_delta_summary.json`
4. `project_state/gates/command_plan.json`
5. `project_state/gates/gate_profile_plan.json`

## 5. Required Audit

Before changing anything, answer:

1. Are all six staged/apply-plan artifacts present in GitHub?
2. Are they listed in `files_changed`?
3. Are they listed in `generated_artifacts`?
4. Are they listed only in `referenced_artifacts` / `required_closeout_artifacts`?
5. Does report prose claim something different from structured summary?
6. Does final-check currently catch this mismatch?
7. Is a source patch needed, or is this report-only closeout repair sufficient?

## 6. Implementation Scope

Preferred fix: report-only closeout repair.

Update `project_state/codex_execution_report.md` so that `codex_report_summary.generated_artifacts` includes:

- `project_state/state_rebuild_apply_plan.json`
- `project_state/proposed_state/artifact_index.json`
- `project_state/proposed_state/current_state.json`
- `project_state/proposed_state/negative_results.json`
- `project_state/proposed_state/model_gate.json`
- `project_state/proposed_state/task_packet.json`

Keep these paths in `files_changed`.

Keep them in `referenced_artifacts` and `required_closeout_artifacts` if the gate expects that, but do not use those fields as a substitute for `generated_artifacts`.

Only patch source/tests if report-summary or final-check cannot validate this consistency and a narrow gate/report-summary check is needed.

Allowed source/test changes only if necessary:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Allowed project_state outputs:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_staged_artifact_generated_artifacts_fix_v1/*`

## 7. Tests

Run and record all commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

Test-Path project_state/state_rebuild_apply_plan.json
Test-Path project_state/proposed_state/artifact_index.json
Test-Path project_state/proposed_state/current_state.json
Test-Path project_state/proposed_state/negative_results.json
Test-Path project_state/proposed_state/model_gate.json
Test-Path project_state/proposed_state/task_packet.json

python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_staged_artifact_generated_artifacts_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` if:

1. any staged/apply-plan artifact is missing;
2. `generated_artifacts` still omits staged/apply-plan artifacts;
3. report prose contradicts structured JSON summary;
4. report-summary does not match `codex_report_summary`;
5. final-check has any FAIL;
6. close-round fails;
7. report/decision/pytest/final-gate IDs mismatch;
8. live root state files are promoted or mutated;
9. source changes exceed the allowed gate/project-state scope;
10. any reverse-solving progress is claimed.
